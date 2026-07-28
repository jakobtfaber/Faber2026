#!/usr/bin/env python3
"""Pure helpers for one anchored-hybrid absolute-DM event."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

K_DM_S_MHZ2 = 4148.808
REFERENCE_FREQUENCY_MHZ = 400.0
CUTOFFS_HZ = (500.0, 1000.0, 1500.0, 2500.0, 5000.0)


def _normalise_for_profile(
    waterfall: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    finite_fraction = np.isfinite(waterfall).mean(axis=1)
    median = np.nanmedian(waterfall, axis=1)
    mad = np.nanmedian(np.abs(waterfall - median[:, None]), axis=1)
    sigma = 1.4826 * mad
    valid = (finite_fraction >= 0.90) & np.isfinite(sigma) & (sigma > 0)
    if valid.sum() < 16:
        raise RuntimeError("fewer than 16 usable channels after accepted support mask")
    z = (waterfall[valid] - median[valid, None]) / sigma[valid, None]
    return np.nan_to_num(z), valid


def peak_time(
    waterfall: np.ndarray,
    time_s: np.ndarray,
    sample_time_s: float,
) -> tuple[float, int]:
    """Find a stable positive-profile peak on half-covered rows."""

    finite_fraction = np.isfinite(waterfall).mean(axis=1)
    median = np.nanmedian(waterfall, axis=1)
    mad = np.nanmedian(np.abs(waterfall - median[:, None]), axis=1)
    sigma = 1.4826 * mad
    valid = (finite_fraction >= 0.50) & np.isfinite(sigma) & (sigma > 0)
    if valid.sum() < 16:
        raise RuntimeError("fewer than 16 half-covered channels after support mask")
    z = (waterfall[valid] - median[valid, None]) / sigma[valid, None]
    positive = np.clip(z, 0.0, None)
    count = np.isfinite(positive).sum(axis=0)
    profile = np.divide(
        np.nansum(positive, axis=0),
        count,
        out=np.full(positive.shape[1], -np.inf),
        where=count > 0,
    )
    supported = count >= 0.50 * np.max(count)
    smooth = max(1, int(round(1.0e-4 / sample_time_s)))
    if smooth > 1:
        profile = np.convolve(
            np.where(supported, profile, 0.0),
            np.ones(smooth) / smooth,
            mode="same",
        )
    profile[~supported] = -np.inf
    peak = int(np.argmax(profile))
    return float(time_s[peak]), peak


def absolute_crop(
    waterfall: np.ndarray,
    time_s: np.ndarray,
    *,
    peak_time_s: float,
    sample_time_s: float,
    window_s: float = 0.030,
) -> np.ndarray:
    """Take a fixed absolute-time crop without wrapping."""

    width = int(round(window_s / sample_time_s))
    center = int(round((peak_time_s - float(time_s[0])) / sample_time_s))
    start = center - width // 2
    stop = start + width
    if start < 0 or stop > waterfall.shape[1]:
        raise RuntimeError("fixed absolute-time crop extends beyond non-wrapping data")
    return np.asarray(waterfall[:, start:stop], dtype=float)


def score_crop(
    crop: np.ndarray,
    sample_time_s: float,
    *,
    frequency_id: np.ndarray,
    jackknife_groups: int = 12,
) -> dict[str, Any]:
    """Score frequency-channel phase coherence across fluctuation cutoffs."""

    z, valid = _normalise_for_profile(crop)
    selected_id = np.asarray(frequency_id)[valid]
    order = np.argsort(selected_id)
    z = z[order]
    selected_id = selected_id[order]
    spectrum = np.fft.rfft(z, axis=1)
    amplitude = np.abs(spectrum)
    phase = np.divide(
        spectrum,
        amplitude,
        out=np.zeros_like(spectrum),
        where=amplitude > np.finfo(float).tiny,
    )
    fluctuation = np.fft.rfftfreq(z.shape[1], sample_time_s)
    use_low = fluctuation >= 50.0
    coherent = np.sum(phase, axis=0)
    group_count = min(jackknife_groups, z.shape[0])
    group = np.arange(z.shape[0]) % group_count
    score: dict[str, float] = {}
    jackknife: dict[str, list[float]] = {}
    for cutoff in CUTOFFS_HZ:
        use = use_low & (fluctuation <= cutoff)
        weight = fluctuation[use] ** 2
        score[str(cutoff)] = float(np.sum(np.abs(coherent[use]) ** 2 * weight))
        jackknife[str(cutoff)] = [
            float(
                np.sum(
                    np.abs(
                        coherent[use]
                        - np.sum(phase[group == group_index][:, use], axis=0)
                    )
                    ** 2
                    * weight
                )
            )
            for group_index in range(group_count)
        ]
    profile = np.mean(np.clip(z, 0.0, None), axis=0)
    half_max = 0.5 * float(np.max(profile))
    above = np.flatnonzero(profile >= half_max)
    width_samples = int(above[-1] - above[0] + 1) if above.size else 0
    return {
        "score": score,
        "jackknife_score": jackknife,
        "valid_channel_count": int(z.shape[0]),
        "profile_peak": float(np.max(profile)),
        "profile_fwhm_ms": float(width_samples * sample_time_s * 1000.0),
    }


def parabolic_peak(grid: np.ndarray, score: np.ndarray) -> float:
    """Interpolate a three-point interior maximum."""

    index = int(np.nanargmax(score))
    if index == 0 or index == grid.size - 1:
        return float(grid[index])
    x = grid[index - 1 : index + 2]
    y = score[index - 1 : index + 2]
    coefficient = np.polyfit(x - x[1], y, 2)
    if coefficient[0] >= 0 or np.any(~np.isfinite(coefficient)):
        return float(x[1])
    return float(
        np.clip(
            x[1] - coefficient[1] / (2.0 * coefficient[0]),
            x[0],
            x[-1],
        )
    )


def fit_grid(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Fit a DM grid and combine grid, channel, and cutoff uncertainty."""

    grid = np.asarray([row["target_total_dm_pc_cm3"] for row in rows])
    cutoff_peak: dict[str, float] = {}
    contrast: dict[str, float] = {}
    for cutoff in CUTOFFS_HZ:
        key = str(cutoff)
        score = np.asarray([row["score"][key] for row in rows])
        cutoff_peak[key] = parabolic_peak(grid, score)
        baseline = float(np.median(score))
        contrast[key] = float(np.max(score) / baseline) if baseline > 0 else math.inf
    candidates = list(map(str, CUTOFFS_HZ))
    stable = []
    for index, key in enumerate(candidates):
        neighbours = (
            candidates[max(0, index - 1) : index]
            + candidates[index + 1 : index + 2]
        )
        if any(
            abs(cutoff_peak[key] - cutoff_peak[other]) <= 0.10
            for other in neighbours
        ):
            stable.append(key)
    selected = max(stable or candidates, key=lambda key: contrast[key])
    score = np.asarray([row["score"][selected] for row in rows])
    peak = parabolic_peak(grid, score)
    group_count = len(rows[0]["jackknife_score"][selected])
    jackknife_peak = np.asarray(
        [
            parabolic_peak(
                grid,
                np.asarray(
                    [row["jackknife_score"][selected][group] for row in rows]
                ),
            )
            for group in range(group_count)
        ]
    )
    mean = float(np.mean(jackknife_peak))
    n = jackknife_peak.size
    sigma_jackknife = float(
        np.sqrt((n - 1.0) / n * np.sum((jackknife_peak - mean) ** 2))
    )
    cutoff_values = np.asarray(list(cutoff_peak.values()))
    sigma_cutoff = float(np.std(cutoff_values, ddof=1))
    step = float(np.median(np.diff(grid)))
    return {
        "dm_pc_cm3": peak,
        "sigma_pc_cm3": max(step, sigma_jackknife, sigma_cutoff),
        "sigma_components_pc_cm3": {
            "grid_step": step,
            "channel_jackknife": sigma_jackknife,
            "cutoff": sigma_cutoff,
        },
        "selected_cutoff_hz": float(selected),
        "cutoff_peaks_pc_cm3": cutoff_peak,
        "cutoff_contrast": contrast,
        "jackknife_peaks_pc_cm3": jackknife_peak.tolist(),
        "selected_score": score.tolist(),
    }


def assert_exactly_once_identity(
    input_dm_pc_cm3: float,
    anchor_dm_pc_cm3: float,
    trial_dm_pc_cm3: float,
) -> dict[str, float]:
    """Assert input + coherent anchor + residual equals the public trial DM."""

    input_dm = float(input_dm_pc_cm3)
    anchor_dm = float(anchor_dm_pc_cm3)
    trial_dm = float(trial_dm_pc_cm3)
    values = np.asarray([input_dm, anchor_dm, trial_dm])
    if not np.all(np.isfinite(values)):
        raise ValueError("DM identity values must be finite")
    coherent_correction = anchor_dm - input_dm
    residual_correction = trial_dm - anchor_dm
    reconstructed = input_dm + coherent_correction + residual_correction
    if not np.isclose(reconstructed, trial_dm, rtol=0.0, atol=1.0e-12):
        raise RuntimeError("exactly-once DM identity failed")
    return {
        "input_dm_pc_cm3": input_dm,
        "coherent_anchor_correction_pc_cm3": coherent_correction,
        "incoherent_residual_correction_pc_cm3": residual_correction,
        "reconstructed_trial_dm_pc_cm3": reconstructed,
    }


def residual_shift_samples(
    frequency_mhz: np.ndarray,
    sample_time_s: float,
    residual_dm_pc_cm3: float,
) -> np.ndarray:
    """Delay each row from the anchor coordinate to one absolute trial."""

    frequency = np.asarray(frequency_mhz, dtype=float)
    sample_time = float(sample_time_s)
    if frequency.ndim != 1 or not np.all(np.isfinite(frequency)):
        raise ValueError("frequency must be one-dimensional and finite")
    if sample_time <= 0 or not np.isfinite(sample_time):
        raise ValueError("sample time must be finite and positive")
    return (
        -K_DM_S_MHZ2
        * float(residual_dm_pc_cm3)
        * (frequency**-2 - REFERENCE_FREQUENCY_MHZ**-2)
        / sample_time
    )


def apply_fractional_residual_dm(
    waterfall: np.ndarray,
    frequency_mhz: np.ndarray,
    sample_time_s: float,
    residual_dm_pc_cm3: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Apply one non-circular fractional-sample residual shift."""

    values = np.asarray(waterfall, dtype=float)
    frequency = np.asarray(frequency_mhz, dtype=float)
    if values.ndim != 2 or frequency.shape != (values.shape[0],):
        raise ValueError("waterfall and frequency dimensions differ")
    shift_sample = residual_shift_samples(
        frequency,
        sample_time_s,
        residual_dm_pc_cm3,
    )
    sample = np.arange(values.shape[1], dtype=float)
    shifted = np.full(values.shape, np.nan, dtype=float)
    for row, shift in enumerate(shift_sample):
        shifted[row] = np.interp(
            sample - shift,
            sample,
            values[row],
            left=np.nan,
            right=np.nan,
        )
    return shifted, shift_sample


def residual_intra_channel_smearing_bound(
    coarse_frequency_mhz: np.ndarray,
    *,
    coarse_channel_width_mhz: float,
    maximum_absolute_residual_dm_pc_cm3: float,
) -> dict[str, float]:
    """Bound residual sweep across one coarse channel after anchor de-chirping."""

    frequency = np.asarray(coarse_frequency_mhz, dtype=float)
    width = float(coarse_channel_width_mhz)
    residual = abs(float(maximum_absolute_residual_dm_pc_cm3))
    if (
        frequency.ndim != 1
        or not np.all(np.isfinite(frequency))
        or np.any(frequency <= width / 2.0)
    ):
        raise ValueError("coarse frequencies do not support a channel-edge bound")
    if not np.isfinite(width) or width <= 0:
        raise ValueError("coarse channel width must be finite and positive")
    lower = frequency - width / 2.0
    upper = frequency + width / 2.0
    smear_s = K_DM_S_MHZ2 * residual * np.abs(lower**-2 - upper**-2)
    index = int(np.argmax(smear_s))
    return {
        "maximum_absolute_residual_dm_pc_cm3": residual,
        "coarse_channel_width_mhz": width,
        "maximum_smearing_s": float(smear_s[index]),
        "worst_coarse_frequency_mhz": float(frequency[index]),
    }
