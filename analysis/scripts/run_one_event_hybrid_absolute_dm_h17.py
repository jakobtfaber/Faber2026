#!/usr/bin/env python3
"""Run one event's anchored-hybrid absolute-DM search from raw CHIME voltages."""

from __future__ import annotations

import argparse
import gc
import json
import warnings
from pathlib import Path
from typing import Any

import h5py
import numpy as np
from absolute_dm_voltage import (
    authoritative_fine_frequency_centres,
    package_dm_argument,
    physical_dm_from_package_coordinate,
    sha256,
    validate_frequency_map,
)
from baseband_analysis.core.bbdata import BBData
from baseband_analysis.core.dedispersion import (
    K_DM as PACKAGE_K_DM_S_MHZ2,
)
from baseband_analysis.core.dedispersion import (
    coherent_dedisp,
)
from baseband_analysis.core.sampling import _upchannel
from one_event_hybrid_dm import (
    K_DM_S_MHZ2,
    REFERENCE_FREQUENCY_MHZ,
    absolute_crop,
    apply_fractional_residual_dm,
    assert_exactly_once_identity,
    fit_grid,
    injected_absolute_dm_recovery,
    parabolic_peak,
    peak_time,
    residual_intra_channel_smearing_bound,
    residual_shift_samples,
    score_crop,
)
from one_event_workflow import legacy_stage_config, load_config

from radio_pipeline.fitting import DispersionState
from radio_pipeline.fitting.products import (
    unix_seconds_parts_to_ns,
    write_band_observation_product,
)


def _accepted_support(
    reference: np.ndarray,
    expected: dict[str, Any],
) -> dict[str, np.ndarray]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        standard_deviation = np.nanstd(reference, axis=1)
    all_nan = ~np.isfinite(reference).any(axis=1)
    finite_flat = ~all_nan & np.isfinite(standard_deviation) & (standard_deviation == 0)
    live = np.isfinite(standard_deviation) & (standard_deviation > 0)
    if (
        reference.shape[0] != int(expected["full_grid_rows"])
        or int(all_nan.sum()) != int(expected["all_nan_count"])
        or int(finite_flat.sum()) != int(expected["finite_flat_count"])
        or int(live.sum()) != int(expected["live_count"])
    ):
        raise RuntimeError("accepted CHIME support changed")
    return {"all_nan": all_nan, "finite_flat": finite_flat, "live": live}


def _upchannel_intensity(
    voltage: np.ndarray,
    *,
    frequency_id: np.ndarray,
    coarse_frequency_mhz: np.ndarray,
    accepted_live_h5: np.ndarray,
    upchannel_factor: int,
) -> dict[str, np.ndarray]:
    spectrum, _package_fine_frequency_mhz, fine_id = _upchannel(
        voltage,
        freq_id=frequency_id,
        fftsize=2 * upchannel_factor,
        downfreq=2,
    )
    expected_fine_id = (
        frequency_id[:, None] * upchannel_factor
        + np.arange(upchannel_factor, dtype=np.int64)[None, :]
    ).reshape(-1)
    fine_id = np.asarray(fine_id, dtype=np.int64)
    if not np.array_equal(fine_id, expected_fine_id):
        raise RuntimeError("upchannelized IDs do not map onto authoritative H5 IDs")
    fine_frequency_mhz = authoritative_fine_frequency_centres(
        frequency_id,
        coarse_frequency_mhz,
        upchannel_factor,
    )
    intensity = np.abs(spectrum[0]) ** 2 + np.abs(spectrum[1]) ** 2
    intensity = np.asarray(intensity.T, dtype=np.float32)
    result = {
        "waterfall": intensity,
        "fine_frequency_mhz": fine_frequency_mhz,
        "fine_id": fine_id,
        "coarse_frequency_mhz": np.repeat(
            np.asarray(coarse_frequency_mhz, dtype=float),
            upchannel_factor,
        ),
        "coarse_frequency_id": np.repeat(
            np.asarray(frequency_id, dtype=np.int64),
            upchannel_factor,
        ),
        "accepted_live": np.repeat(
            np.asarray(accepted_live_h5, dtype=bool),
            upchannel_factor,
        ),
    }
    del spectrum
    return result


def _align_upchannelized(
    waterfall: np.ndarray,
    *,
    residual_shift_frequency_mhz: np.ndarray,
    row_start_unix_ns: np.ndarray,
    accepted_live: np.ndarray,
    sample_time_s: float,
    total_dm_pc_cm3: float,
) -> tuple[np.ndarray, np.ndarray, int]:
    values = np.asarray(waterfall, dtype=float)
    frequency = np.asarray(residual_shift_frequency_mhz, dtype=float)
    start_ns = np.asarray(row_start_unix_ns, dtype=np.int64)
    time_base_unix_ns = int(np.min(start_ns[np.asarray(accepted_live, dtype=bool)]))
    start = (start_ns - time_base_unix_ns).astype(float) * 1.0e-9
    live = np.asarray(accepted_live, dtype=bool)
    referred_start = start - K_DM_S_MHZ2 * float(total_dm_pc_cm3) * (
        frequency**-2 - REFERENCE_FREQUENCY_MHZ**-2
    )
    origin = float(np.min(referred_start[live]))
    end = float(np.max(referred_start[live] + values.shape[1] * sample_time_s))
    sample_count = int(np.ceil((end - origin) / sample_time_s)) + 1
    time_s = origin + np.arange(sample_count, dtype=float) * sample_time_s
    aligned = np.full((values.shape[0], sample_count), np.nan, dtype=np.float32)
    source_sample = np.arange(values.shape[1], dtype=float)
    for row in np.flatnonzero(live):
        target_source_sample = (time_s - referred_start[row]) / sample_time_s
        aligned[row] = np.interp(
            target_source_sample,
            source_sample,
            values[row],
            left=np.nan,
            right=np.nan,
        ).astype(np.float32)
    return aligned, time_s, time_base_unix_ns


def _fixed_padded_source(
    waterfall: np.ndarray,
    time_s: np.ndarray,
    *,
    peak_time_s: float,
    sample_time_s: float,
    window_s: float,
    padding_samples: int,
) -> tuple[np.ndarray, int, float]:
    width = int(round(window_s / sample_time_s))
    center = int(round((peak_time_s - float(time_s[0])) / sample_time_s))
    start = center - width // 2 - padding_samples
    stop = start + width + 2 * padding_samples
    if start < 0 or stop > waterfall.shape[1]:
        raise RuntimeError("padded hybrid crop extends beyond anchor data")
    output_time0_s = float(time_s[start + padding_samples])
    return (
        np.asarray(waterfall[:, start:stop], dtype=float),
        width,
        output_time0_s,
    )


def _hybrid_trial(
    anchor_source: np.ndarray,
    *,
    target_dm_pc_cm3: float,
    anchor_dm_pc_cm3: float,
    input_dm_pc_cm3: float,
    residual_shift_frequency_mhz: np.ndarray,
    fine_id: np.ndarray,
    accepted_live: np.ndarray,
    sample_time_s: float,
    padding_samples: int,
    output_width_samples: int,
) -> tuple[dict[str, Any], np.ndarray]:
    identity = assert_exactly_once_identity(
        input_dm_pc_cm3,
        anchor_dm_pc_cm3,
        target_dm_pc_cm3,
    )
    shifted, shift_sample = apply_fractional_residual_dm(
        anchor_source,
        residual_shift_frequency_mhz,
        sample_time_s,
        identity["incoherent_residual_correction_pc_cm3"],
    )
    crop = shifted[
        :,
        padding_samples : padding_samples + output_width_samples,
    ]
    if not np.all(np.isfinite(crop[accepted_live])):
        raise RuntimeError("hybrid residual shift reached fixed-crop edge")
    result = score_crop(crop, sample_time_s, frequency_id=fine_id)
    result.update(
        {
            "target_total_dm_pc_cm3": float(target_dm_pc_cm3),
            "anchor_total_dm_pc_cm3": float(anchor_dm_pc_cm3),
            "applied_residual_dm_pc_cm3": identity["incoherent_residual_correction_pc_cm3"],
            "exactly_once_identity": identity,
            "minimum_shift_samples": float(np.min(shift_sample)),
            "maximum_shift_samples": float(np.max(shift_sample)),
        }
    )
    return result, crop


def _write_product(
    path: Path,
    *,
    waterfall: np.ndarray,
    upchannel: dict[str, np.ndarray],
    sample_time_s: float,
    target_dm_pc_cm3: float,
    anchor_dm_pc_cm3: float,
    input_dm_pc_cm3: float,
    time0_unix_ns: int,
    fine_channel_width_mhz: float,
    input_sha256: dict[str, str],
    role: str,
    upchannel_factor: int,
    fully_coherent: bool = False,
) -> dict:
    valid = np.asarray(upchannel["accepted_live"], dtype=bool)[:, None] & np.isfinite(waterfall)
    receipt = write_band_observation_product(
        path,
        instrument="chime",
        waterfall=waterfall,
        valid=valid,
        frequency_mhz=upchannel["fine_frequency_mhz"],
        channel_width_mhz=fine_channel_width_mhz,
        sample_interval_s=sample_time_s,
        time0_unix_ns=time0_unix_ns,
        dispersion=DispersionState(
            input_dm_pc_cm3=input_dm_pc_cm3,
            coherent_correction_pc_cm3=(
                target_dm_pc_cm3 - input_dm_pc_cm3
                if fully_coherent
                else anchor_dm_pc_cm3 - input_dm_pc_cm3
            ),
            incoherent_correction_pc_cm3=(
                0.0 if fully_coherent else target_dm_pc_cm3 - anchor_dm_pc_cm3
            ),
            product_dm_pc_cm3=target_dm_pc_cm3,
            mode=(
                "singlebeam_h5_fully_coherent"
                if fully_coherent
                else "singlebeam_h5_coherent_anchor_plus_fractional_residual"
            ),
        ),
        input_sha256=input_sha256,
        extra={
            "residual_shift_frequency_mhz": np.asarray(
                upchannel["coarse_frequency_mhz"], dtype=np.float64
            ),
            "fine_frequency_id": np.asarray(upchannel["fine_id"], dtype=np.int64),
            "coarse_frequency_id": np.asarray(upchannel["coarse_frequency_id"], dtype=np.int64),
            "accepted_live": np.asarray(upchannel["accepted_live"], dtype=bool),
            "sample_time_s": np.asarray(sample_time_s),
            "target_total_dm_pc_cm3": np.asarray(target_dm_pc_cm3),
            "anchor_total_dm_pc_cm3": np.asarray(anchor_dm_pc_cm3),
            "applied_residual_dm_pc_cm3": np.asarray(target_dm_pc_cm3 - anchor_dm_pc_cm3),
            "role": np.asarray(role),
            "frequency_bin_factor": np.asarray(upchannel_factor),
            "time_bin_factor": np.asarray(2 * upchannel_factor),
        },
    )
    receipt.update(
        {
            "target_total_dm_pc_cm3": target_dm_pc_cm3,
            "anchor_total_dm_pc_cm3": anchor_dm_pc_cm3,
            "applied_residual_dm_pc_cm3": target_dm_pc_cm3 - anchor_dm_pc_cm3,
            "role": role,
            "frequency_bin_factor": upchannel_factor,
            "time_bin_factor": 2 * upchannel_factor,
        }
    )
    return receipt


def run(
    config: dict,
    output_dir: Path,
    *,
    verification_dms_pc_cm3: np.ndarray | None = None,
    preparation_only: bool = False,
) -> dict:
    event = config["event"]
    h5_path = Path(config["h5_path"])
    reference_path = Path(config["accepted_chime_reference"])
    expected_h5_sha256 = config["expected_h5_sha256"]
    expected_reference_sha256 = config["expected_chime_reference_sha256"]
    if sha256(h5_path) != expected_h5_sha256:
        raise RuntimeError("raw CHIME H5 SHA-256 mismatch")
    if sha256(reference_path) != expected_reference_sha256:
        raise RuntimeError("accepted CHIME reference SHA-256 mismatch")
    reference = np.load(reference_path)
    expected_support = config["expected_chime_support"]
    support = _accepted_support(reference, expected_support)

    data = BBData.from_file(str(h5_path))
    raw_voltage = np.asarray(data["tiedbeam_baseband"][:])
    with h5py.File(h5_path, "r") as handle:
        frequency_id = np.asarray(handle["index_map/freq"]["id"], dtype=np.int64)
        frequency_mhz = np.asarray(handle["index_map/freq"]["centre"], dtype=float)
        row_start_unix_ns = unix_seconds_parts_to_ns(
            handle["time0"]["ctime"][:],
            handle["time0"]["ctime_offset"][:],
        )
        raw_sample_time_s = float(handle.attrs["delta_time"])
        baseband_dm_present = "DM" in handle["tiedbeam_baseband"].attrs
        package_input_dm = (
            float(handle["tiedbeam_baseband"].attrs["DM"]) if baseband_dm_present else 0.0
        )
        embedded_sha = str(handle.attrs["baseband-analysis_git_sha"])
    validate_frequency_map(frequency_id, frequency_mhz, raw_voltage.shape[0])
    input_coordinate_dm = physical_dm_from_package_coordinate(
        package_input_dm,
        package_dispersion_constant=PACKAGE_K_DM_S_MHZ2,
    )
    full_grid_rows = int(expected_support["full_grid_rows"])
    missing_id = np.setdiff1d(
        np.arange(full_grid_rows, dtype=np.int64),
        frequency_id,
    )
    present_dead_id = frequency_id[~support["live"][frequency_id]]
    live_absent_id = np.setdiff1d(np.flatnonzero(support["live"]), frequency_id)
    if (
        missing_id.size != int(expected_support["h5_missing_count"])
        or frequency_id.size != int(expected_support["h5_present_count"])
        or not np.all(~support["live"][missing_id])
    ):
        raise RuntimeError("CHIME source-missing support changed")
    expected_present_dead_ids = np.asarray(
        expected_support["h5_present_accepted_dead_ids"],
        dtype=np.int64,
    )
    if not np.array_equal(present_dead_id, expected_present_dead_ids):
        raise RuntimeError("CHIME H5-present accepted-dead IDs changed")
    if live_absent_id.size:
        raise RuntimeError("accepted-live CHIME row is absent from H5")
    accepted_live_h5 = support["live"][frequency_id]

    anchor_dm = float(config["anchor_dm_pc_cm3"])
    upchannel_factor = int(config["upchannel_factor"])
    # coherent_dedisp subtracts the H5 DM0 internally. Pass the package-scaled
    # absolute target; passing input_coordinate_dm here would subtract DM0 twice.
    package_argument = package_dm_argument(
        anchor_dm,
        0.0,
        package_dispersion_constant=PACKAGE_K_DM_S_MHZ2,
    )
    anchor_voltage = coherent_dedisp(
        data,
        package_argument,
        matrix_in=raw_voltage,
        time_shift=False,
    )
    upchannel = _upchannel_intensity(
        anchor_voltage,
        frequency_id=frequency_id,
        coarse_frequency_mhz=frequency_mhz,
        accepted_live_h5=accepted_live_h5,
        upchannel_factor=upchannel_factor,
    )
    del anchor_voltage
    gc.collect()
    upchannel_sample_time_s = raw_sample_time_s * 2.0 * upchannel_factor
    block_center_offset_ns = round((2.0 * upchannel_factor - 1.0) / 2.0 * raw_sample_time_s * 1.0e9)
    fine_row_start_unix_ns = np.repeat(
        row_start_unix_ns + block_center_offset_ns,
        upchannel_factor,
    )
    anchor_aligned, anchor_time_s, time_base_unix_ns = _align_upchannelized(
        upchannel["waterfall"],
        residual_shift_frequency_mhz=upchannel["coarse_frequency_mhz"],
        row_start_unix_ns=fine_row_start_unix_ns,
        accepted_live=upchannel["accepted_live"],
        sample_time_s=upchannel_sample_time_s,
        total_dm_pc_cm3=anchor_dm,
    )
    del upchannel["waterfall"]
    gc.collect()
    peak_time_s, _ = peak_time(
        anchor_aligned,
        anchor_time_s,
        upchannel_sample_time_s,
    )

    coarse_half_width = float(config["coarse_half_width_pc_cm3"])
    maximum_residual = coarse_half_width + float(config["fine_half_width_pc_cm3"])
    maximum_shift = np.max(
        np.abs(
            residual_shift_samples(
                upchannel["coarse_frequency_mhz"],
                upchannel_sample_time_s,
                maximum_residual,
            )
        )
    )
    padding_samples = int(np.ceil(maximum_shift)) + 4
    anchor_source, output_width_samples, product_time0_s = _fixed_padded_source(
        anchor_aligned,
        anchor_time_s,
        peak_time_s=peak_time_s,
        sample_time_s=upchannel_sample_time_s,
        window_s=float(config["window_s"]),
        padding_samples=padding_samples,
    )
    product_time0_unix_ns = time_base_unix_ns + round(product_time0_s * 1.0e9)
    coarse_width_mhz = abs(
        float(
            np.median(
                np.diff(frequency_mhz[np.argsort(frequency_id)])
                / np.diff(frequency_id[np.argsort(frequency_id)])
            )
        )
    )
    fine_channel_width_mhz = coarse_width_mhz / upchannel_factor
    input_hashes = {
        "raw_chime_h5": expected_h5_sha256,
        "accepted_chime_reference": expected_reference_sha256,
    }
    del anchor_aligned
    gc.collect()
    if not np.all(np.isfinite(anchor_source[upchannel["accepted_live"]])):
        raise RuntimeError("accepted-live anchor source has invalid fixed support")

    coarse = np.arange(
        anchor_dm - coarse_half_width,
        anchor_dm + coarse_half_width + 0.5 * float(config["coarse_step_pc_cm3"]),
        float(config["coarse_step_pc_cm3"]),
    )
    coarse_rows = [
        _hybrid_trial(
            anchor_source,
            target_dm_pc_cm3=dm,
            anchor_dm_pc_cm3=anchor_dm,
            input_dm_pc_cm3=input_coordinate_dm,
            residual_shift_frequency_mhz=upchannel["coarse_frequency_mhz"],
            fine_id=upchannel["fine_id"],
            accepted_live=upchannel["accepted_live"],
            sample_time_s=upchannel_sample_time_s,
            padding_samples=padding_samples,
            output_width_samples=output_width_samples,
        )[0]
        for dm in coarse
    ]
    coarse_fit = fit_grid(coarse_rows)
    if np.isclose(coarse_fit["dm_pc_cm3"], coarse[[0, -1]]).any():
        raise RuntimeError("hybrid coarse-grid maximum is on an edge")
    fine_half_width = float(config["fine_half_width_pc_cm3"])
    fine_step = float(config["fine_step_pc_cm3"])
    fine = np.arange(
        coarse_fit["dm_pc_cm3"] - fine_half_width,
        coarse_fit["dm_pc_cm3"] + fine_half_width + 0.5 * fine_step,
        fine_step,
    )
    fine_rows = [
        _hybrid_trial(
            anchor_source,
            target_dm_pc_cm3=dm,
            anchor_dm_pc_cm3=anchor_dm,
            input_dm_pc_cm3=input_coordinate_dm,
            residual_shift_frequency_mhz=upchannel["coarse_frequency_mhz"],
            fine_id=upchannel["fine_id"],
            accepted_live=upchannel["accepted_live"],
            sample_time_s=upchannel_sample_time_s,
            padding_samples=padding_samples,
            output_width_samples=output_width_samples,
        )[0]
        for dm in fine
    ]
    fit = fit_grid(fine_rows)
    if np.isclose(fit["dm_pc_cm3"], fine[[0, -1]]).any():
        raise RuntimeError("hybrid fine-grid maximum is on an edge")

    output_dir.mkdir(parents=True, exist_ok=True)
    products = {}
    anchor_row, anchor_crop = _hybrid_trial(
        anchor_source,
        target_dm_pc_cm3=anchor_dm,
        anchor_dm_pc_cm3=anchor_dm,
        input_dm_pc_cm3=input_coordinate_dm,
        residual_shift_frequency_mhz=upchannel["coarse_frequency_mhz"],
        fine_id=upchannel["fine_id"],
        accepted_live=upchannel["accepted_live"],
        sample_time_s=upchannel_sample_time_s,
        padding_samples=padding_samples,
        output_width_samples=output_width_samples,
    )
    products["anchor_before_residual"] = _write_product(
        output_dir / "chime_anchor_before_residual.npz",
        waterfall=anchor_crop,
        upchannel=upchannel,
        sample_time_s=upchannel_sample_time_s,
        target_dm_pc_cm3=anchor_dm,
        anchor_dm_pc_cm3=anchor_dm,
        input_dm_pc_cm3=input_coordinate_dm,
        time0_unix_ns=product_time0_unix_ns,
        fine_channel_width_mhz=fine_channel_width_mhz,
        input_sha256=input_hashes,
        role="one coherently dedispersed anchor before residual correction",
        upchannel_factor=upchannel_factor,
    )
    fit_row, fit_crop = _hybrid_trial(
        anchor_source,
        target_dm_pc_cm3=float(fit["dm_pc_cm3"]),
        anchor_dm_pc_cm3=anchor_dm,
        input_dm_pc_cm3=input_coordinate_dm,
        residual_shift_frequency_mhz=upchannel["coarse_frequency_mhz"],
        fine_id=upchannel["fine_id"],
        accepted_live=upchannel["accepted_live"],
        sample_time_s=upchannel_sample_time_s,
        padding_samples=padding_samples,
        output_width_samples=output_width_samples,
    )
    products["hybrid_fit_dm"] = _write_product(
        output_dir / "chime_hybrid_fit_dm.npz",
        waterfall=fit_crop,
        upchannel=upchannel,
        sample_time_s=upchannel_sample_time_s,
        target_dm_pc_cm3=float(fit["dm_pc_cm3"]),
        anchor_dm_pc_cm3=anchor_dm,
        input_dm_pc_cm3=input_coordinate_dm,
        time0_unix_ns=product_time0_unix_ns,
        fine_channel_width_mhz=fine_channel_width_mhz,
        input_sha256=input_hashes,
        role="anchor intensity shifted once by fit minus anchor",
        upchannel_factor=upchannel_factor,
    )
    geometry_dm = float(config["geometry_dm_pc_cm3"])
    geometry_row, geometry_crop = _hybrid_trial(
        anchor_source,
        target_dm_pc_cm3=geometry_dm,
        anchor_dm_pc_cm3=anchor_dm,
        input_dm_pc_cm3=input_coordinate_dm,
        residual_shift_frequency_mhz=upchannel["coarse_frequency_mhz"],
        fine_id=upchannel["fine_id"],
        accepted_live=upchannel["accepted_live"],
        sample_time_s=upchannel_sample_time_s,
        padding_samples=padding_samples,
        output_width_samples=output_width_samples,
    )
    products["geometry_dm"] = _write_product(
        output_dir / "chime_geometry_dm.npz",
        waterfall=geometry_crop,
        upchannel=upchannel,
        sample_time_s=upchannel_sample_time_s,
        target_dm_pc_cm3=geometry_dm,
        anchor_dm_pc_cm3=anchor_dm,
        input_dm_pc_cm3=input_coordinate_dm,
        time0_unix_ns=product_time0_unix_ns,
        fine_channel_width_mhz=fine_channel_width_mhz,
        input_sha256=input_hashes,
        role="anchor intensity shifted once by geometry minus anchor",
        upchannel_factor=upchannel_factor,
    )

    if preparation_only:
        result = {
            "schema_version": 1,
            "status": config["result_status"],
            "burst": event,
            "event_binding_sha256": config["event_binding_sha256"],
            "scope": f"{event} reviewed-input preparation only",
            "preparation_only": True,
            "source_h5": {"path": str(h5_path), "sha256": expected_h5_sha256},
            "accepted_reference": {
                "path": str(reference_path),
                "sha256": expected_reference_sha256,
                "dm_pc_cm3": float(config["accepted_chime_reference_dm_pc_cm3"]),
            },
            "support": {
                "full_grid_rows": full_grid_rows,
                "h5_present_count": int(frequency_id.size),
                "h5_missing_count": int(missing_id.size),
                "h5_missing_ids": missing_id.tolist(),
                "h5_present_accepted_dead_count": int(present_dead_id.size),
                "h5_present_accepted_dead_ids": present_dead_id.tolist(),
                "accepted_live_count": int(support["live"].sum()),
                "accepted_dead_count": int((~support["live"]).sum()),
                "accepted_live_absent_from_h5_count": int(live_absent_id.size),
                "proposed_extra_bad_rows": [],
                "manual_event_mask_applied": False,
                "historical_row_sum_replay_applied": False,
            },
            "hybrid_method": {
                "input_coordinate_dm_pc_cm3": input_coordinate_dm,
                "h5_package_dm_attribute_pc_cm3": package_input_dm,
                "anchor_dm_pc_cm3": anchor_dm,
                "coherent_anchor_package_argument_pc_cm3": package_argument,
                "coherent_anchor_count": 1,
                "oracle_only_fully_coherent_count": 0,
                "upchannel_factor": upchannel_factor,
                "raw_sample_time_s": raw_sample_time_s,
                "upchannel_sample_time_s": upchannel_sample_time_s,
                "reference_frequency_mhz": REFERENCE_FREQUENCY_MHZ,
                "residual_rule": "trial absolute DM minus anchor DM exactly once",
                "nonwrapping_fractional_sample_shifts": True,
            },
            "grid": {
                "coarse": coarse_rows,
                "coarse_fit": coarse_fit,
                "fine": fine_rows,
                "fit": fit,
            },
            "fit_trial": fit_row,
            "anchor_trial": anchor_row,
            "geometry_trial": geometry_row,
            "geometry_dm_pc_cm3": geometry_dm,
            "products": products,
        }
        result_path = output_dir / "chime_hybrid_result.json"
        result_path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
        return result

    selected_cutoff = str(fit["selected_cutoff_hz"])
    if verification_dms_pc_cm3 is None:
        oracle_half_width = float(config["oracle_half_width_pc_cm3"])
        oracle_dm = np.asarray(
            [
                float(fit["dm_pc_cm3"]) - oracle_half_width,
                float(fit["dm_pc_cm3"]),
                float(fit["dm_pc_cm3"]) + oracle_half_width,
            ]
        )
        oracle_role = "hybrid_power_maximum"
    else:
        oracle_dm = np.asarray(verification_dms_pc_cm3, dtype=float)
        if oracle_dm.shape != (3,) or not np.all(np.diff(oracle_dm) > 0):
            raise ValueError("posterior verification DMs must be ordered lower, median, upper")
        oracle_role = "joint_posterior_lower_median_upper"
    hybrid_oracle_rows = [
        _hybrid_trial(
            anchor_source,
            target_dm_pc_cm3=dm,
            anchor_dm_pc_cm3=anchor_dm,
            input_dm_pc_cm3=input_coordinate_dm,
            residual_shift_frequency_mhz=upchannel["coarse_frequency_mhz"],
            fine_id=upchannel["fine_id"],
            accepted_live=upchannel["accepted_live"],
            sample_time_s=upchannel_sample_time_s,
            padding_samples=padding_samples,
            output_width_samples=output_width_samples,
        )[0]
        for dm in oracle_dm
    ]
    fully_coherent_rows = []
    posterior_labels = ("lower", "median", "upper")
    for oracle_index, dm in enumerate(oracle_dm):
        direct_argument = package_dm_argument(
            dm,
            0.0,
            package_dispersion_constant=PACKAGE_K_DM_S_MHZ2,
        )
        direct_voltage = coherent_dedisp(
            data,
            direct_argument,
            matrix_in=raw_voltage,
            time_shift=False,
        )
        direct_upchannel = _upchannel_intensity(
            direct_voltage,
            frequency_id=frequency_id,
            coarse_frequency_mhz=frequency_mhz,
            accepted_live_h5=accepted_live_h5,
            upchannel_factor=upchannel_factor,
        )
        del direct_voltage
        direct_aligned, direct_time_s, direct_time_base_unix_ns = _align_upchannelized(
            direct_upchannel["waterfall"],
            residual_shift_frequency_mhz=direct_upchannel["coarse_frequency_mhz"],
            row_start_unix_ns=fine_row_start_unix_ns,
            accepted_live=direct_upchannel["accepted_live"],
            sample_time_s=upchannel_sample_time_s,
            total_dm_pc_cm3=dm,
        )
        if direct_time_base_unix_ns != time_base_unix_ns:
            raise RuntimeError("fully coherent oracle changed the time origin")
        direct_crop = absolute_crop(
            direct_aligned,
            direct_time_s,
            peak_time_s=peak_time_s,
            sample_time_s=upchannel_sample_time_s,
            window_s=float(config["window_s"]),
        )
        if not np.all(np.isfinite(direct_crop[direct_upchannel["accepted_live"]])):
            raise RuntimeError("fully coherent oracle reached the fixed-crop edge")
        direct_row = score_crop(
            direct_crop,
            upchannel_sample_time_s,
            frequency_id=direct_upchannel["fine_id"],
        )
        direct_row["target_total_dm_pc_cm3"] = float(dm)
        fully_coherent_rows.append(direct_row)
        if verification_dms_pc_cm3 is not None:
            width = int(round(float(config["window_s"]) / upchannel_sample_time_s))
            center = int(round((peak_time_s - float(direct_time_s[0])) / upchannel_sample_time_s))
            start = center - width // 2
            direct_time0_unix_ns = direct_time_base_unix_ns + round(
                float(direct_time_s[start]) * 1.0e9
            )
            label = posterior_labels[oracle_index]
            products[f"fully_coherent_posterior_{label}"] = _write_product(
                output_dir / f"chime_fully_coherent_posterior_{label}.npz",
                waterfall=direct_crop,
                upchannel=direct_upchannel,
                sample_time_s=upchannel_sample_time_s,
                target_dm_pc_cm3=float(dm),
                anchor_dm_pc_cm3=float(dm),
                input_dm_pc_cm3=input_coordinate_dm,
                time0_unix_ns=direct_time0_unix_ns,
                fine_channel_width_mhz=fine_channel_width_mhz,
                input_sha256=input_hashes,
                role=(f"fully coherent H5 posterior verification {label}"),
                upchannel_factor=upchannel_factor,
                fully_coherent=True,
            )
        del direct_upchannel, direct_aligned, direct_crop
        gc.collect()
    hybrid_oracle_score = np.asarray([row["score"][selected_cutoff] for row in hybrid_oracle_rows])
    direct_oracle_score = np.asarray([row["score"][selected_cutoff] for row in fully_coherent_rows])
    hybrid_oracle_peak = parabolic_peak(oracle_dm, hybrid_oracle_score)
    direct_oracle_peak = parabolic_peak(oracle_dm, direct_oracle_score)
    oracle_difference = abs(direct_oracle_peak - hybrid_oracle_peak)
    material_threshold = float(config["oracle_material_threshold_pc_cm3"])
    hybrid_normalised = hybrid_oracle_score / hybrid_oracle_score[1]
    direct_normalised = direct_oracle_score / direct_oracle_score[1]
    normalised_difference = np.abs(hybrid_normalised - direct_normalised)
    maximum_normalised_difference = float(np.max(normalised_difference))
    normalised_tolerance = float(config["oracle_normalised_curve_max_abs_difference"])
    center_score_ratio = float(hybrid_oracle_score[1] / direct_oracle_score[1])
    center_ratio_tolerance = float(config["oracle_center_score_ratio_tolerance"])
    oracle_center_is_maximum = (
        int(np.argmax(hybrid_oracle_score)) == 1 and int(np.argmax(direct_oracle_score)) == 1
    )
    center_requirement_applies = verification_dms_pc_cm3 is None
    oracle_curve_agreement = (
        maximum_normalised_difference <= normalised_tolerance
        and abs(center_score_ratio - 1.0) <= center_ratio_tolerance
    )
    if (
        (center_requirement_applies and not oracle_center_is_maximum)
        or oracle_difference > material_threshold
        or not oracle_curve_agreement
    ):
        raise RuntimeError("full-coherent bracket oracle disagrees with the hybrid objective")

    smearing = residual_intra_channel_smearing_bound(
        frequency_mhz[accepted_live_h5],
        coarse_channel_width_mhz=0.390625,
        maximum_absolute_residual_dm_pc_cm3=maximum_residual,
    )
    smearing["upchannel_sample_time_s"] = upchannel_sample_time_s
    smearing["fraction_of_upchannel_sample"] = (
        smearing["maximum_smearing_s"] / upchannel_sample_time_s
    )
    pulse_fwhm_s = float(config["reference_pulse_fwhm_s"])
    smearing["reference_pulse_fwhm_s"] = pulse_fwhm_s
    smearing["fraction_of_reference_pulse_fwhm"] = smearing["maximum_smearing_s"] / pulse_fwhm_s
    sample_fraction_threshold = float(config["smearing_max_fraction_of_upchannel_sample"])
    pulse_fraction_threshold = float(config["smearing_max_fraction_of_reference_pulse_fwhm"])
    smearing["maximum_fraction_of_upchannel_sample"] = sample_fraction_threshold
    smearing["maximum_fraction_of_reference_pulse_fwhm"] = pulse_fraction_threshold
    smearing["threshold_justification"] = (
        "negligible requires residual sweep below 10% of one hybrid time bin "
        "and below the configured fraction of the accepted pulse FWHM"
    )
    smearing["passed"] = (
        smearing["fraction_of_upchannel_sample"] <= sample_fraction_threshold
        and smearing["fraction_of_reference_pulse_fwhm"] <= pulse_fraction_threshold
    )
    if not smearing["passed"]:
        raise RuntimeError("hybrid residual intra-channel smearing is not negligible")
    injected = injected_absolute_dm_recovery(
        anchor_dm,
        input_coordinate_dm,
        upchannel_sample_time_s,
        float(config["injection_max_error_pc_cm3"]),
    )

    result = {
        "schema_version": 1,
        "status": config["result_status"],
        "burst": event,
        "event_binding_sha256": config["event_binding_sha256"],
        "scope": f"{event} one-event workflow only",
        "source_h5": {"path": str(h5_path), "sha256": expected_h5_sha256},
        "embedded_producer_sha": embedded_sha,
        "baseband_dm_attribute_present": baseband_dm_present,
        "physical_input_state_status": "pending independent review",
        "accepted_reference": {
            "path": str(reference_path),
            "sha256": expected_reference_sha256,
            "dm_pc_cm3": float(config["accepted_chime_reference_dm_pc_cm3"]),
        },
        "support": {
            "full_grid_rows": full_grid_rows,
            "h5_present_count": int(frequency_id.size),
            "h5_missing_count": int(missing_id.size),
            "h5_missing_ids": missing_id.tolist(),
            "h5_present_accepted_dead_count": int(present_dead_id.size),
            "h5_present_accepted_dead_ids": present_dead_id.tolist(),
            "accepted_live_count": int(support["live"].sum()),
            "accepted_dead_count": int((~support["live"]).sum()),
            "accepted_live_absent_from_h5_count": int(live_absent_id.size),
            "proposed_extra_bad_rows": [],
            "manual_event_mask_applied": False,
            "historical_row_sum_replay_applied": False,
        },
        "hybrid_method": {
            "input_coordinate_dm_pc_cm3": input_coordinate_dm,
            "h5_package_dm_attribute_pc_cm3": package_input_dm,
            "anchor_dm_pc_cm3": anchor_dm,
            "coherent_anchor_package_argument_pc_cm3": package_argument,
            "coherent_anchor_count": 1,
            "oracle_only_fully_coherent_count": 3,
            "upchannel_factor": upchannel_factor,
            "fine_row_count": int(upchannel["fine_id"].size),
            "accepted_live_fine_row_count": int(upchannel["accepted_live"].sum()),
            "raw_sample_time_s": raw_sample_time_s,
            "upchannel_sample_time_s": upchannel_sample_time_s,
            "fine_frequency_role": "display and phase-coherence rows",
            "residual_shift_frequency_role": (
                "authoritative H5 coarse centres repeated across fine rows"
            ),
            "residual_rule": "trial absolute DM minus anchor DM exactly once",
            "reference_frequency_mhz": REFERENCE_FREQUENCY_MHZ,
            "nonwrapping_fractional_sample_shifts": True,
            "padding_samples": padding_samples,
            "fixed_crop_samples": output_width_samples,
            "smearing_bound": smearing,
            "injected_absolute_dm_recovery": injected,
        },
        "grid": {
            "coarse": coarse_rows,
            "coarse_fit": coarse_fit,
            "fine": fine_rows,
            "fit": fit,
        },
        "fit_trial": fit_row,
        "anchor_trial": anchor_row,
        "geometry_trial": geometry_row,
        "geometry_dm_pc_cm3": geometry_dm,
        "full_coherent_oracle": {
            "role": oracle_role,
            "dm_pc_cm3": oracle_dm.tolist(),
            "selected_cutoff_hz": float(selected_cutoff),
            "hybrid_rows": hybrid_oracle_rows,
            "fully_coherent_rows": fully_coherent_rows,
            "hybrid_parabolic_peak_pc_cm3": hybrid_oracle_peak,
            "fully_coherent_parabolic_peak_pc_cm3": direct_oracle_peak,
            "absolute_peak_difference_pc_cm3": oracle_difference,
            "material_threshold_pc_cm3": material_threshold,
            "hybrid_normalised_score": hybrid_normalised.tolist(),
            "fully_coherent_normalised_score": direct_normalised.tolist(),
            "normalised_score_absolute_difference": (normalised_difference.tolist()),
            "maximum_normalised_score_absolute_difference": (maximum_normalised_difference),
            "normalised_curve_tolerance": normalised_tolerance,
            "center_score_ratio_hybrid_over_fully_coherent": center_score_ratio,
            "center_score_ratio_tolerance": center_ratio_tolerance,
            "curve_agreement_passed": oracle_curve_agreement,
            "tolerance_justification": (
                "the same three-point objective is required to agree within "
                "10% after center normalization; the raw center score must "
                "agree within 20%, while the independent peak-motion gate "
                "remains 0.005 pc cm^-3"
            ),
            "center_is_maximum_for_both": oracle_center_is_maximum,
            "center_maximum_requirement_applies": center_requirement_applies,
            "passed": True,
        },
        "products": products,
    }
    result_path = output_dir / "chime_hybrid_result.json"
    result_path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--joint-fit-result", type=Path)
    parser.add_argument("--preparation-only", action="store_true")
    args = parser.parse_args()
    verification_dms = None
    if args.joint_fit_result is not None:
        fit_result = json.loads(args.joint_fit_result.read_text())
        summary = fit_result["shared_absolute_dm_pc_cm3"]
        verification_dms = np.asarray(
            [summary["lower"], summary["median"], summary["upper"]],
            dtype=float,
        )
    result = run(
        legacy_stage_config(
            load_config(
                args.config,
                require_execution_authorized=not args.preparation_only,
            )
        ),
        args.output_dir,
        verification_dms_pc_cm3=verification_dms,
        preparation_only=args.preparation_only,
    )
    fit = result["grid"]["fit"]
    print(
        f"{result['burst']} hybrid: {fit['dm_pc_cm3']:.6f} +/- {fit['sigma_pc_cm3']:.6f} pc cm^-3",
        flush=True,
    )


if __name__ == "__main__":
    main()
