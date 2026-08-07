#!/usr/bin/env python3
"""Pure helpers for the conditional CHIME absolute-DM voltage campaign."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np

K_DM_S_MHZ2 = 4148.808
REFERENCE_FREQUENCY_MHZ = 400.0


def sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def differential_dm(
    target_total_dm: float,
    input_coordinate_dm: float,
) -> float:
    """Convert the public absolute-DM coordinate to one internal correction."""

    target = float(target_total_dm)
    starting = float(input_coordinate_dm)
    if not np.isfinite(target) or not np.isfinite(starting):
        raise ValueError("target and certified input DMs must be finite")
    return target - starting


def package_dm_argument(
    target_total_dm: float,
    input_coordinate_dm: float,
    *,
    package_dispersion_constant: float,
    physical_dispersion_constant: float = K_DM_S_MHZ2,
) -> float:
    """Scale one physical DM correction onto a package's phase convention."""

    package_constant = float(package_dispersion_constant)
    physical_constant = float(physical_dispersion_constant)
    if (
        not np.isfinite(package_constant)
        or package_constant <= 0
        or not np.isfinite(physical_constant)
        or physical_constant <= 0
    ):
        raise ValueError("dispersion constants must be finite and positive")
    correction = differential_dm(target_total_dm, input_coordinate_dm)
    return correction * physical_constant / package_constant


def physical_dm_from_package_coordinate(
    package_dm: float,
    *,
    package_dispersion_constant: float,
    physical_dispersion_constant: float = K_DM_S_MHZ2,
) -> float:
    """Express an H5 package-DM attribute on the physical phase coordinate."""

    value = float(package_dm)
    package_constant = float(package_dispersion_constant)
    physical_constant = float(physical_dispersion_constant)
    if (
        not np.isfinite(value)
        or not np.isfinite(package_constant)
        or package_constant <= 0
        or not np.isfinite(physical_constant)
        or physical_constant <= 0
    ):
        raise ValueError("H5 DM and dispersion constants must be finite")
    return value * package_constant / physical_constant


def validate_frequency_map(
    frequency_id: np.ndarray,
    frequency_mhz: np.ndarray,
    n_rows: int,
) -> np.ndarray:
    """Return row order by increasing H5 centre after strict identity checks."""

    ids = np.asarray(frequency_id)
    centres = np.asarray(frequency_mhz, dtype=float)
    if ids.ndim != 1 or centres.ndim != 1:
        raise ValueError("frequency IDs and centres must be one-dimensional")
    if ids.size != n_rows or centres.size != n_rows:
        raise ValueError("H5 frequency metadata must map one-to-one onto voltage rows")
    if np.unique(ids).size != ids.size:
        raise ValueError("H5 frequency IDs must be unique")
    if np.unique(centres).size != centres.size or not np.all(np.isfinite(centres)):
        raise ValueError("H5 frequency centres must be finite and unique")
    return np.argsort(centres)


def authoritative_fine_frequency_centres(
    frequency_id: np.ndarray,
    frequency_mhz: np.ndarray,
    upchannel_factor: int,
) -> np.ndarray:
    """Place fine FFT bins inside the authoritative H5 coarse channels."""

    channel_id = np.asarray(frequency_id, dtype=np.int64)
    centre = np.asarray(frequency_mhz, dtype=float)
    if (
        channel_id.ndim != 1
        or centre.ndim != 1
        or channel_id.size != centre.size
        or channel_id.size < 2
    ):
        raise ValueError("authoritative coarse frequency map must be paired 1D arrays")
    if (
        isinstance(upchannel_factor, bool)
        or not isinstance(upchannel_factor, int)
        or upchannel_factor < 1
    ):
        raise ValueError("upchannel_factor must be a positive integer")
    order = np.argsort(channel_id)
    id_step = np.diff(channel_id[order])
    centre_step = np.diff(centre[order])
    if np.any(id_step <= 0) or np.any(~np.isfinite(centre_step)):
        raise ValueError("authoritative channel IDs and centres must be ordered and finite")
    slope = centre_step / id_step
    channel_slope_mhz = float(np.median(slope))
    if not np.allclose(slope, channel_slope_mhz, rtol=0.0, atol=1.0e-9):
        raise ValueError("authoritative H5 channel-centre spacing is not uniform")
    # The production transform averages adjacent bins from a 2U-point FFT.
    # Pair j has mean FFT index -U + 2j + 0.5, hence the quarter-bin term.
    fractional_id = (
        (np.arange(upchannel_factor, dtype=float) + 0.25) / upchannel_factor
        - 0.5
    )
    return (
        centre[:, None] + channel_slope_mhz * fractional_id[None, :]
    ).reshape(-1)


def trusted_notebook_rfi_mask(
    intensity: np.ndarray,
    *,
    time_limits: tuple[int, int],
    rfi_limits: tuple[float, float],
) -> tuple[np.ndarray, dict[str, np.ndarray | int | float]]:
    """Replay the original event-mask notebook exactly.

    The notebook standardised each full-grid row on the strict
    ``time_limits[0] < sample < time_limits[1]`` window, replaced non-finite
    values by zero, and rejected rows whose full-profile sum exceeded either
    fixed threshold.
    """

    values = np.asarray(intensity, dtype=float)
    if values.ndim != 2:
        raise ValueError("intensity must have shape (frequency, time)")
    start, stop = (int(time_limits[0]), int(time_limits[1]))
    sample = np.arange(values.shape[1])
    noise = (sample > start) & (sample < stop)
    if not np.any(noise):
        raise ValueError("trusted notebook noise window contains no samples")
    upper, lower = (float(rfi_limits[0]), float(rfi_limits[1]))
    if not np.isfinite(upper) or not np.isfinite(lower) or upper <= lower:
        raise ValueError("trusted notebook RFI limits must be finite and ordered")
    mean = np.nanmean(values[:, noise], axis=1, keepdims=True)
    standard_deviation = np.nanstd(values[:, noise], axis=1, keepdims=True)
    with np.errstate(invalid="ignore", divide="ignore"):
        normalised = (values - mean) / standard_deviation
    normalised = np.nan_to_num(
        normalised,
        nan=0.0,
        posinf=0.0,
        neginf=0.0,
    )
    row_sum = np.sum(normalised, axis=1)
    keep = (row_sum <= upper) & (row_sum >= lower)
    return keep, {
        "row_sum": row_sum,
        "noise_sample_count": int(noise.sum()),
        "upper_threshold": upper,
        "lower_threshold": lower,
    }


def map_full_grid_mask_to_h5(
    full_grid_keep: np.ndarray,
    h5_frequency_id: np.ndarray,
) -> np.ndarray:
    """Map a full CHIME grid mask by integer channel ID, never row position."""

    keep = np.asarray(full_grid_keep)
    ids = np.asarray(h5_frequency_id)
    if keep.ndim != 1 or keep.dtype != np.bool_:
        raise ValueError("full-grid keep mask must be a one-dimensional boolean array")
    if ids.ndim != 1 or not np.issubdtype(ids.dtype, np.integer):
        raise ValueError("H5 frequency IDs must be a one-dimensional integer array")
    if np.any(ids < 0) or np.any(ids >= keep.size):
        raise ValueError("H5 frequency ID falls outside the trusted full grid")
    if np.unique(ids).size != ids.size:
        raise ValueError("H5 frequency IDs must be unique")
    return keep[ids]


def nonwrapping_row_placement(
    waterfall: np.ndarray,
    frequency_mhz: np.ndarray,
    row_start_s: np.ndarray,
    sample_time_s: float,
    total_dm: float,
    *,
    reference_frequency_mhz: float = REFERENCE_FREQUENCY_MHZ,
) -> tuple[np.ndarray, np.ndarray]:
    """Place rows on a shared 400-MHz time axis without circular wrapping."""

    values = np.asarray(waterfall, dtype=float)
    frequency = np.asarray(frequency_mhz, dtype=float)
    start = np.asarray(row_start_s, dtype=float)
    dt = float(sample_time_s)
    dm = float(total_dm)
    if values.ndim != 2:
        raise ValueError("waterfall must have shape (frequency, time)")
    if frequency.shape != (values.shape[0],) or start.shape != (values.shape[0],):
        raise ValueError("each waterfall row needs a frequency and start time")
    if not np.isfinite(dt) or dt <= 0:
        raise ValueError("sample time must be finite and positive")
    if reference_frequency_mhz != REFERENCE_FREQUENCY_MHZ:
        raise ValueError("campaign requires a shared 400 MHz reference")
    referred_start = start - K_DM_S_MHZ2 * dm * (
        frequency**-2 - reference_frequency_mhz**-2
    )
    origin = float(np.min(referred_start))
    offset = np.rint((referred_start - origin) / dt).astype(int)
    length = int(values.shape[1] + np.max(offset))
    placed = np.full((values.shape[0], length), np.nan, dtype=float)
    for row, row_offset in enumerate(offset):
        placed[row, row_offset : row_offset + values.shape[1]] = values[row]
    time_s = origin + np.arange(length, dtype=float) * dt
    return placed, time_s


def phase_coherence_score(
    waterfall: np.ndarray,
    sample_time_s: float,
    *,
    low_hz: float = 50.0,
    high_hz: float = 5000.0,
) -> float:
    """Current DM-phase statistic at zero residual DM."""

    values = np.asarray(waterfall, dtype=float)
    finite_fraction = np.isfinite(values).mean(axis=1)
    median = np.nanmedian(values, axis=1)
    mad = np.nanmedian(np.abs(values - median[:, None]), axis=1)
    sigma = 1.4826 * mad
    valid = (finite_fraction >= 0.90) & np.isfinite(sigma) & (sigma > 0)
    if valid.sum() < 16:
        raise ValueError("fewer than 16 valid frequency channels")
    z = (values[valid] - median[valid, None]) / sigma[valid, None]
    z = np.nan_to_num(z)
    spectrum = np.fft.rfft(z, axis=1)
    amplitude = np.abs(spectrum)
    phase = np.divide(
        spectrum,
        amplitude,
        out=np.zeros_like(spectrum),
        where=amplitude > np.finfo(float).tiny,
    )
    fluctuation = np.fft.rfftfreq(z.shape[1], float(sample_time_s))
    use = (fluctuation >= low_hz) & (fluctuation <= high_hz)
    if use.sum() < 5:
        raise ValueError("fluctuation-frequency window contains fewer than five bins")
    coherent = np.abs(np.sum(phase[:, use], axis=0)) ** 2
    return float(np.sum(coherent * fluctuation[use] ** 2))


def fixed_peak_crop(
    waterfall: np.ndarray,
    *,
    center: int,
    width: int,
) -> np.ndarray:
    """Take the same crop for every trial, failing instead of edge padding."""

    values = np.asarray(waterfall)
    start = int(center) - int(width) // 2
    stop = start + int(width)
    if start < 0 or stop > values.shape[1]:
        raise ValueError("fixed peak crop extends beyond non-wrapping data")
    return values[:, start:stop]
