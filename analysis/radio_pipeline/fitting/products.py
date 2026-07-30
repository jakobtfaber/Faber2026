"""Strict on-disk contract for joint-fit band observations."""

from __future__ import annotations

import hashlib
import json
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path

import numpy as np

from .joint_burst import (
    REFERENCE_FREQUENCY_MHZ,
    BandObservation,
    DispersionState,
)

PRODUCT_SCHEMA_VERSION = 1
MJD_UNIX_EPOCH = Decimal("40587")
SECONDS_PER_DAY = Decimal("86400")


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def mjd_crop_time0_unix_ns(
    tstart_mjd: object,
    crop_start_sample: float,
    sample_time_s: float,
) -> int:
    """Convert a filterbank crop start without binary-float epoch loss."""

    seconds = (Decimal(str(tstart_mjd)) - MJD_UNIX_EPOCH) * SECONDS_PER_DAY + Decimal(
        str(crop_start_sample)
    ) * Decimal(str(sample_time_s))
    return int((seconds * Decimal("1000000000")).to_integral_value(rounding=ROUND_HALF_EVEN))


def unix_seconds_parts_to_ns(
    whole_seconds: np.ndarray,
    fractional_seconds: np.ndarray,
) -> np.ndarray:
    """Combine H5 epoch fields without rounding away sub-microsecond offsets."""

    whole = np.asarray(whole_seconds)
    fraction = np.asarray(fractional_seconds)
    if whole.shape != fraction.shape:
        raise ValueError("whole and fractional epoch fields must have equal shape")
    return np.asarray(
        [
            int(
                (
                    (Decimal(str(base)) + Decimal(str(offset))) * Decimal("1000000000")
                ).to_integral_value(rounding=ROUND_HALF_EVEN)
            )
            for base, offset in zip(whole.flat, fraction.flat, strict=True)
        ],
        dtype=np.int64,
    ).reshape(whole.shape)


def estimate_row_baseline_noise(
    waterfall: np.ndarray,
    valid: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Estimate each row from the outer quarters of the locked time crop."""

    values = np.asarray(waterfall, dtype=float)
    mask = np.asarray(valid, dtype=bool)
    if values.ndim != 2 or mask.shape != values.shape:
        raise ValueError("waterfall and valid mask must have identical 2D shape")
    quarter = values.shape[1] // 4
    if quarter < 4:
        raise ValueError("crop is too short for an off-pulse noise estimate")
    off_pulse = np.zeros(values.shape, dtype=bool)
    off_pulse[:, :quarter] = True
    off_pulse[:, -quarter:] = True
    use = mask & off_pulse
    baseline = np.full(values.shape[0], np.nan, dtype=float)
    noise = np.full(values.shape[0], np.nan, dtype=float)
    for row in range(values.shape[0]):
        samples = values[row, use[row]]
        if samples.size < 8:
            continue
        center = float(np.median(samples))
        sigma = float(1.4826 * np.median(np.abs(samples - center)))
        if np.isfinite(sigma) and sigma > 0:
            baseline[row] = center
            noise[row] = sigma
    return baseline, noise


def noise_estimation_mask(
    waterfall: np.ndarray,
    valid: np.ndarray,
) -> np.ndarray:
    """Return the exact valid pixels used for the outer-quarter noise fit."""

    values = np.asarray(waterfall)
    mask = np.asarray(valid, dtype=bool)
    if values.ndim != 2 or mask.shape != values.shape:
        raise ValueError("waterfall and valid mask must have identical 2D shape")
    quarter = values.shape[1] // 4
    if quarter < 4:
        raise ValueError("crop is too short for an off-pulse noise estimate")
    outer = np.zeros(values.shape, dtype=bool)
    outer[:, :quarter] = True
    outer[:, -quarter:] = True
    return mask & np.isfinite(values) & outer


def write_band_observation_product(
    path: str | Path,
    *,
    instrument: str,
    waterfall: np.ndarray,
    valid: np.ndarray,
    frequency_mhz: np.ndarray,
    channel_width_mhz: np.ndarray | float,
    sample_interval_s: float,
    time0_unix_ns: int,
    dispersion: DispersionState,
    input_sha256: dict[str, str],
    extra: dict[str, np.ndarray] | None = None,
) -> dict[str, object]:
    """Write one complete, baseline-subtracted fitting observation."""

    values = np.asarray(waterfall, dtype=float)
    mask = np.asarray(valid, dtype=bool) & np.isfinite(values)
    off_pulse = noise_estimation_mask(values, mask)
    baseline, noise = estimate_row_baseline_noise(values, mask)
    usable_rows = np.isfinite(baseline) & np.isfinite(noise) & (noise > 0)
    mask &= usable_rows[:, None]
    if not np.any(mask):
        raise ValueError("no rows have a valid off-pulse noise estimate")
    centered = values - baseline[:, None]
    widths = np.asarray(channel_width_mhz, dtype=float)
    if widths.ndim == 0:
        widths = np.full(values.shape[0], float(widths))
    payload: dict[str, np.ndarray] = {
        "schema_version": np.asarray(PRODUCT_SCHEMA_VERSION),
        "instrument": np.asarray(instrument),
        "waterfall": centered.astype(np.float32),
        "pixel_valid": mask,
        "noise_estimation_mask": off_pulse & usable_rows[:, None],
        "frequency_mhz": np.asarray(frequency_mhz, dtype=np.float64),
        "channel_width_mhz": widths.astype(np.float64),
        "baseline": baseline.astype(np.float64),
        "noise_std": noise.astype(np.float64),
        "sample_interval_s": np.asarray(sample_interval_s, dtype=np.float64),
        "time0_unix_ns": np.asarray(time0_unix_ns, dtype=np.int64),
        "reference_frequency_mhz": np.asarray(REFERENCE_FREQUENCY_MHZ, dtype=np.float64),
        "input_dm_pc_cm3": np.asarray(dispersion.input_dm_pc_cm3, dtype=np.float64),
        "coherent_correction_pc_cm3": np.asarray(
            dispersion.coherent_correction_pc_cm3, dtype=np.float64
        ),
        "incoherent_correction_pc_cm3": np.asarray(
            dispersion.incoherent_correction_pc_cm3, dtype=np.float64
        ),
        "product_dm_pc_cm3": np.asarray(dispersion.product_dm_pc_cm3, dtype=np.float64),
        "dispersion_mode": np.asarray(dispersion.mode),
        "input_sha256_json": np.asarray(
            json.dumps(input_sha256, sort_keys=True, separators=(",", ":"))
        ),
    }
    if extra:
        overlap = set(payload).intersection(extra)
        if overlap:
            raise ValueError(f"extra product fields replace contract fields: {overlap}")
        payload.update(extra)
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output, **payload)
    return {
        "path": str(output),
        "sha256": sha256_file(output),
        "instrument": instrument,
        "product_dm_pc_cm3": dispersion.product_dm_pc_cm3,
        "valid_pixel_count": int(mask.sum()),
        "valid_row_count": int(np.any(mask, axis=1).sum()),
        "time0_unix_ns": int(time0_unix_ns),
    }


def load_band_observation_product(
    path: str | Path,
    *,
    expected_sha256: str | None = None,
) -> BandObservation:
    """Load and validate the complete observation contract."""

    product = Path(path)
    if expected_sha256 is not None and sha256_file(product) != expected_sha256:
        raise ValueError("observation product SHA-256 mismatch")
    required = {
        "schema_version",
        "instrument",
        "waterfall",
        "pixel_valid",
        "noise_estimation_mask",
        "frequency_mhz",
        "channel_width_mhz",
        "noise_std",
        "sample_interval_s",
        "time0_unix_ns",
        "reference_frequency_mhz",
        "input_dm_pc_cm3",
        "coherent_correction_pc_cm3",
        "incoherent_correction_pc_cm3",
        "product_dm_pc_cm3",
        "dispersion_mode",
        "input_sha256_json",
    }
    with np.load(product, allow_pickle=False) as archive:
        missing = required.difference(archive.files)
        if missing:
            raise ValueError(f"observation product is incomplete: {sorted(missing)}")
        if int(archive["schema_version"]) != PRODUCT_SCHEMA_VERSION:
            raise ValueError("unsupported observation-product schema")
        noise_mask = np.asarray(archive["noise_estimation_mask"], dtype=bool)
        pixel_valid = np.asarray(archive["pixel_valid"], dtype=bool)
        if noise_mask.shape != pixel_valid.shape or np.any(noise_mask & ~pixel_valid):
            raise ValueError("noise-estimation mask is invalid")
        hashes = json.loads(str(archive["input_sha256_json"]))
        if not isinstance(hashes, dict) or not all(
            isinstance(key, str) and isinstance(value, str) for key, value in hashes.items()
        ):
            raise ValueError("input hashes must be a string mapping")
        return BandObservation(
            instrument=str(archive["instrument"]),
            waterfall=archive["waterfall"],
            valid=archive["pixel_valid"],
            frequency_mhz=archive["frequency_mhz"],
            channel_width_mhz=archive["channel_width_mhz"],
            noise_std=archive["noise_std"],
            sample_interval_s=float(archive["sample_interval_s"]),
            time0_unix_ns=int(archive["time0_unix_ns"]),
            reference_frequency_mhz=float(archive["reference_frequency_mhz"]),
            dispersion=DispersionState(
                input_dm_pc_cm3=float(archive["input_dm_pc_cm3"]),
                coherent_correction_pc_cm3=float(archive["coherent_correction_pc_cm3"]),
                incoherent_correction_pc_cm3=float(archive["incoherent_correction_pc_cm3"]),
                product_dm_pc_cm3=float(archive["product_dm_pc_cm3"]),
                mode=str(archive["dispersion_mode"]),
            ),
            input_sha256=hashes,
        )
