"""Deterministic native-order materialization of reviewed fitting grids."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .joint_burst import K_DM_S_MHZ2, BandObservation
from .products import (
    load_band_observation_product,
    sha256_file,
    write_band_observation_product,
)

ALGORITHM = "native_order_inverse_variance_v1"
SMEARING_ALGORITHM = "residual_intra_bin_edge_delay_v1"


def arrays_sha256(*arrays: Any) -> str:
    """Hash array values with the workflow's exact dtype-and-shape convention."""

    digest = hashlib.sha256()
    for array in arrays:
        value = np.ascontiguousarray(array)
        digest.update(value.dtype.str.encode())
        digest.update(repr(value.shape).encode())
        digest.update(value.view(np.uint8))
    return digest.hexdigest()


def sample_time_axis_ns(
    *,
    time0_unix_ns: int,
    sample_interval_s: float,
    sample_count: int,
) -> NDArray[np.int64]:
    """Construct sample centers using the workflow's integer-nanosecond rule."""

    offsets_ns = np.rint(
        np.arange(sample_count, dtype=np.float64) * float(sample_interval_s) * 1.0e9
    ).astype(np.int64)
    return np.asarray(int(time0_unix_ns), dtype=np.int64) + offsets_ns


def residual_smearing_calculation(
    observation: BandObservation,
    *,
    absolute_dm_bounds_pc_cm3: tuple[float, float],
    frequency_bin_factor: int,
    frequency_contiguity_tolerance_mhz: float = 1.0e-9,
) -> dict[str, Any]:
    """Bound residual dispersion across every proposed averaged channel."""

    factor = _positive_factor(frequency_bin_factor, "frequency_bin_factor")
    dm_bounds = tuple(float(value) for value in absolute_dm_bounds_pc_cm3)
    if (
        len(dm_bounds) != 2
        or not np.all(np.isfinite(dm_bounds))
        or dm_bounds[0] >= dm_bounds[1]
    ):
        raise ValueError("absolute DM bounds must be finite and increasing")
    product_bounds = (
        observation.dispersion.product_dm_pc_cm3,
        observation.dispersion.product_dm_pc_cm3,
    )
    maximum_residual = max(
        abs(absolute_dm - product_dm)
        for absolute_dm in dm_bounds
        for product_dm in product_bounds
    )
    frequency, width = _group_frequencies(
        observation,
        factor,
        frequency_contiguity_tolerance_mhz,
    )
    lower = frequency - width / 2.0
    upper = frequency + width / 2.0
    smear = (
        K_DM_S_MHZ2
        * maximum_residual
        * np.abs(np.power(lower, -2.0) - np.power(upper, -2.0))
    )
    worst = int(np.argmax(smear))
    return {
        "algorithm": SMEARING_ALGORITHM,
        "dispersion_constant_s_mhz2": K_DM_S_MHZ2,
        "reference_frequency_mhz": 400.0,
        "absolute_dm_bounds_pc_cm3": list(dm_bounds),
        "product_dm_bounds_pc_cm3": list(product_bounds),
        "maximum_absolute_residual_dm_pc_cm3": float(maximum_residual),
        "frequency_bin_factor": factor,
        "maximum_smearing_s": float(smear[worst]),
        "worst_frequency_mhz": float(frequency[worst]),
        "worst_channel_width_mhz": float(width[worst]),
        "fit_sample_interval_s": float(observation.sample_interval_s),
        "output_frequency_count": int(frequency.size),
    }


@dataclass(frozen=True, slots=True)
class FitResolution:
    """One reviewed lower-resolution grid before baseline re-estimation."""

    waterfall: NDArray[np.float64]
    valid: NDArray[np.bool_]
    valid_fraction: NDArray[np.float64]
    propagated_noise_std: NDArray[np.float64]
    frequency_mhz: NDArray[np.float64]
    channel_width_mhz: NDArray[np.float64]
    sample_interval_s: float
    time0_unix_ns: int
    frequency_bin_factor: int
    time_bin_factor: int
    minimum_valid_fraction: float


def _positive_factor(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _group_frequencies(
    observation: BandObservation,
    factor: int,
    tolerance_mhz: float,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    frequency = observation.frequency_mhz
    width = observation.channel_width_mhz
    steps = np.diff(frequency)
    if steps.size and not (np.all(steps > 0) or np.all(steps < 0)):
        raise ValueError("frequency centers must be strictly ordered")
    ascending = steps.size == 0 or bool(steps[0] > 0)
    lower_all = frequency - 0.5 * width
    upper_all = frequency + 0.5 * width
    left_edges = upper_all[:-1] if ascending else lower_all[:-1]
    right_edges = lower_all[1:] if ascending else upper_all[1:]
    contiguous = np.abs(left_edges - right_edges) <= tolerance_mhz
    run_starts = np.concatenate(([0], np.flatnonzero(~contiguous) + 1))
    run_stops = np.concatenate((np.flatnonzero(~contiguous) + 1, [frequency.size]))
    run_lengths = run_stops - run_starts
    if np.any(run_lengths % factor):
        raise ValueError(
            "contiguous frequency run is not exactly divisible by bin factor"
        )

    output_frequency: list[float] = []
    output_width: list[float] = []
    for start in range(0, frequency.size, factor):
        stop = start + factor
        centers = frequency[start:stop]
        widths = width[start:stop]
        lower = centers - 0.5 * widths
        upper = centers + 0.5 * widths
        if factor > 1:
            left_edges = upper[:-1] if ascending else lower[:-1]
            right_edges = lower[1:] if ascending else upper[1:]
            if np.any(np.abs(left_edges - right_edges) > tolerance_mhz):
                raise ValueError("frequency bin would cross a channel gap")
        group_lower = float(np.min(lower))
        group_upper = float(np.max(upper))
        output_frequency.append(0.5 * (group_lower + group_upper))
        output_width.append(group_upper - group_lower)
    return (
        np.asarray(output_frequency, dtype=np.float64),
        np.asarray(output_width, dtype=np.float64),
    )


def _mean_first_group_time_ns(
    time0_unix_ns: int,
    sample_interval_s: float,
    factor: int,
) -> int:
    offset_ns = (
        Decimal(str(sample_interval_s))
        * Decimal("1000000000")
        * Decimal(factor - 1)
        / Decimal(2)
    )
    return int(time0_unix_ns) + int(
        offset_ns.to_integral_value(rounding=ROUND_HALF_EVEN)
    )


def resolve_fit_resolution(
    observation: BandObservation,
    *,
    frequency_bin_factor: int,
    time_bin_factor: int,
    minimum_valid_fraction: float,
    frequency_contiguity_tolerance_mhz: float = 1.0e-9,
) -> FitResolution:
    """Average one observation without reordering or circular placement."""

    frequency_factor = _positive_factor(
        frequency_bin_factor,
        "frequency_bin_factor",
    )
    time_factor = _positive_factor(time_bin_factor, "time_bin_factor")
    if time_factor != 1:
        raise ValueError(
            "time_bin_factor must remain one until the likelihood integrates bin duration"
        )
    if not np.isclose(minimum_valid_fraction, 1.0, rtol=0.0, atol=0.0):
        raise ValueError("minimum_valid_fraction must be exactly one for science fitting")
    if (
        not np.isfinite(frequency_contiguity_tolerance_mhz)
        or frequency_contiguity_tolerance_mhz < 0
    ):
        raise ValueError("frequency contiguity tolerance must be finite and non-negative")
    nfrequency, ntime = observation.waterfall.shape
    if nfrequency % frequency_factor:
        raise ValueError("frequency dimension is not exactly divisible by bin factor")
    if ntime % time_factor:
        raise ValueError("time dimension is not exactly divisible by bin factor")

    output_frequency, output_width = _group_frequencies(
        observation,
        frequency_factor,
        frequency_contiguity_tolerance_mhz,
    )
    output_shape = (
        nfrequency // frequency_factor,
        ntime // time_factor,
    )
    block_shape = (
        output_shape[0],
        frequency_factor,
        output_shape[1],
        time_factor,
    )
    values = observation.waterfall.reshape(block_shape)
    valid = observation.valid.reshape(block_shape)
    noise = observation.noise_std.reshape(block_shape)
    weights = np.zeros(block_shape, dtype=np.float64)
    np.divide(
        1.0,
        np.square(noise),
        out=weights,
        where=valid,
    )
    weight_sum = weights.sum(axis=(1, 3))
    weighted_sum = np.zeros(block_shape, dtype=np.float64)
    np.multiply(values, weights, out=weighted_sum, where=valid)
    weighted_sum = weighted_sum.sum(axis=(1, 3))
    valid_fraction = valid.sum(axis=(1, 3), dtype=np.int64) / float(
        frequency_factor * time_factor
    )
    output_valid = (
        (valid_fraction >= float(minimum_valid_fraction))
        & np.isfinite(weight_sum)
        & (weight_sum > 0)
    )
    output_values = np.full(output_shape, np.nan, dtype=np.float64)
    np.divide(
        weighted_sum,
        weight_sum,
        out=output_values,
        where=output_valid,
    )
    propagated_noise = np.full(output_shape, np.nan, dtype=np.float64)
    np.sqrt(
        np.divide(
            1.0,
            weight_sum,
            out=np.full(output_shape, np.nan, dtype=np.float64),
            where=output_valid,
        ),
        out=propagated_noise,
        where=output_valid,
    )
    return FitResolution(
        waterfall=output_values,
        valid=output_valid,
        valid_fraction=valid_fraction,
        propagated_noise_std=propagated_noise,
        frequency_mhz=output_frequency,
        channel_width_mhz=output_width,
        sample_interval_s=float(observation.sample_interval_s) * time_factor,
        time0_unix_ns=_mean_first_group_time_ns(
            observation.time0_unix_ns,
            observation.sample_interval_s,
            time_factor,
        ),
        frequency_bin_factor=frequency_factor,
        time_bin_factor=time_factor,
        minimum_valid_fraction=float(minimum_valid_fraction),
    )


def _product_array_identity(product_path: Path) -> dict[str, str]:
    """Hash the exact stored arrays, before loader dtype/broadcast conversion."""

    with np.load(product_path, allow_pickle=False) as archive:
        time_axis = sample_time_axis_ns(
            time0_unix_ns=int(archive["time0_unix_ns"]),
            sample_interval_s=float(archive["sample_interval_s"]),
            sample_count=int(archive["waterfall"].shape[1]),
        )
        return {
            "waterfall_sha256": arrays_sha256(archive["waterfall"]),
            "valid_mask_sha256": arrays_sha256(archive["pixel_valid"]),
            "frequency_grid_sha256": arrays_sha256(
                archive["frequency_mhz"],
                archive["channel_width_mhz"],
            ),
            "noise_sha256": arrays_sha256(archive["noise_std"]),
            "time_axis_sha256": arrays_sha256(time_axis),
        }


def materialize_fit_resolution(
    source_path: str | Path,
    output_path: str | Path,
    *,
    frequency_bin_factor: int,
    time_bin_factor: int,
    minimum_valid_fraction: float,
    frequency_contiguity_tolerance_mhz: float = 1.0e-9,
) -> dict[str, object]:
    """Write a strict fit product and return its hash-bound receipt."""

    source = Path(source_path)
    output = Path(output_path)
    if source.resolve() == output.resolve():
        raise ValueError("fit observation must not replace its high-resolution source")
    observation = load_band_observation_product(source)
    resolved = resolve_fit_resolution(
        observation,
        frequency_bin_factor=frequency_bin_factor,
        time_bin_factor=time_bin_factor,
        minimum_valid_fraction=minimum_valid_fraction,
        frequency_contiguity_tolerance_mhz=frequency_contiguity_tolerance_mhz,
    )
    source_identity = {
        "sha256": sha256_file(source),
        **_product_array_identity(source),
    }
    settings = {
        "frequency_bin_factor": resolved.frequency_bin_factor,
        "time_bin_factor": resolved.time_bin_factor,
        "minimum_valid_fraction": resolved.minimum_valid_fraction,
        "frequency_contiguity_tolerance_mhz": float(
            frequency_contiguity_tolerance_mhz
        ),
    }
    extra = {
        "frequency_bin_factor": np.asarray(
            resolved.frequency_bin_factor,
            dtype=np.int64,
        ),
        "time_bin_factor": np.asarray(resolved.time_bin_factor, dtype=np.int64),
        "minimum_valid_fraction": np.asarray(
            resolved.minimum_valid_fraction,
            dtype=np.float64,
        ),
        "frequency_contiguity_tolerance_mhz": np.asarray(
            frequency_contiguity_tolerance_mhz,
            dtype=np.float64,
        ),
        "source_observation_sha256": np.asarray(source_identity["sha256"]),
        "source_waterfall_sha256": np.asarray(
            source_identity["waterfall_sha256"]
        ),
        "source_valid_mask_sha256": np.asarray(
            source_identity["valid_mask_sha256"]
        ),
        "source_frequency_grid_sha256": np.asarray(
            source_identity["frequency_grid_sha256"]
        ),
        "source_noise_sha256": np.asarray(source_identity["noise_sha256"]),
        "source_time_axis_sha256": np.asarray(
            source_identity["time_axis_sha256"]
        ),
        "source_shape": np.asarray(observation.waterfall.shape, dtype=np.int64),
        "block_valid_fraction": resolved.valid_fraction.astype(np.float64),
        "propagated_noise_std": resolved.propagated_noise_std.astype(np.float64),
        "materialization_algorithm": np.asarray(ALGORITHM),
    }
    write_band_observation_product(
        output,
        instrument=observation.instrument,
        waterfall=resolved.waterfall,
        valid=resolved.valid,
        frequency_mhz=resolved.frequency_mhz,
        channel_width_mhz=resolved.channel_width_mhz,
        sample_interval_s=resolved.sample_interval_s,
        time0_unix_ns=resolved.time0_unix_ns,
        dispersion=observation.dispersion,
        input_sha256=dict(observation.input_sha256),
        extra=extra,
    )
    materialized = load_band_observation_product(output)
    output_identity = _product_array_identity(output)
    compare = materialized.valid & np.isfinite(resolved.propagated_noise_std)
    noise_ratio = (
        materialized.noise_std[compare] / resolved.propagated_noise_std[compare]
    )
    if noise_ratio.size == 0 or np.any(~np.isfinite(noise_ratio)):
        raise ValueError("cannot compare re-estimated and propagated fit noise")
    proposal = {
        "shape": list(materialized.waterfall.shape),
        "sample_interval_s": materialized.sample_interval_s,
        "time0_unix_ns": materialized.time0_unix_ns,
        "waterfall_sha256": output_identity["waterfall_sha256"],
        "valid_mask_sha256": output_identity["valid_mask_sha256"],
        "frequency_grid_sha256": output_identity["frequency_grid_sha256"],
        "noise_sha256": output_identity["noise_sha256"],
        "propagated_noise_sha256": arrays_sha256(
            resolved.propagated_noise_std
        ),
        "reestimated_to_propagated_noise_ratio_median": float(
            np.median(noise_ratio)
        ),
        "reestimated_to_propagated_noise_ratio_mad": float(
            np.median(np.abs(noise_ratio - np.median(noise_ratio)))
        ),
        "time_axis_sha256": output_identity["time_axis_sha256"],
    }
    proposal_binding = {
        "algorithm": ALGORITHM,
        "source": source_identity,
        "settings": settings,
        "proposal": proposal,
    }
    proposal["arrays_and_settings_sha256"] = hashlib.sha256(
        json.dumps(
            proposal_binding,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
    ).hexdigest()
    return {
        "schema_version": 1,
        "status": "candidate_fit_grid_pending_resolution_review",
        "instrument": observation.instrument,
        "source": {
            "path": str(source),
            **source_identity,
        },
        "settings": settings,
        "proposal": proposal,
        "output": {
            "path": str(output),
            "sha256": sha256_file(output),
        },
    }
