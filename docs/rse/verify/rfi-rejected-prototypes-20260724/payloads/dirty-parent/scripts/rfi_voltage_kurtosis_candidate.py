#!/usr/bin/env python3
"""Development-only protected raw-voltage amplitude-tail component."""

from __future__ import annotations

from typing import Any

import numpy as np


STATUS = "development_only_protected_voltage_kurtosis_component"
KURTOSIS_SIGMA = 5.0
KURTOSIS_ITERATIONS = 6
MINIMUM_VOLTAGE_SAMPLES = 100
BROADBAND_VOLTAGE_SIGMA = 8.0
MAXIMUM_BROADBAND_CHANNEL_FRACTION = 0.01


def _validate(
    values: np.ndarray,
    channel_valid: np.ndarray,
    allowed: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    data = np.asarray(values)
    valid = np.asarray(channel_valid, dtype=bool)
    support = np.asarray(allowed, dtype=bool)
    if data.ndim != 3 or valid.shape != (data.shape[0],):
        raise ValueError("values must be channel/polarization/time with channel-valid support")
    if support.shape != (data.shape[0], data.shape[2]):
        raise ValueError("allowed support must have channel/time shape")
    return data, valid, support


def amplitude_kurtosis_by_channel(
    values: np.ndarray,
    channel_valid: np.ndarray,
    allowed: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Return Pearson kurtosis of voltage amplitude on explicitly allowed samples."""
    data, valid, support = _validate(values, channel_valid, allowed)
    kurtosis = np.full(data.shape[0], np.nan, dtype=np.float64)
    sample_count = np.zeros(data.shape[0], dtype=np.int64)
    for channel in np.flatnonzero(valid):
        selected = data[channel, :, support[channel]].reshape(-1)
        amplitude = np.abs(selected[np.isfinite(selected)]).astype(np.float64)
        sample_count[channel] = amplitude.size
        if amplitude.size < MINIMUM_VOLTAGE_SAMPLES:
            continue
        centered = amplitude - np.mean(amplitude)
        variance = np.mean(centered**2)
        if variance > 0:
            kurtosis[channel] = np.mean(centered**4) / variance**2
    return kurtosis, sample_count


def exclude_broadband_voltage_samples(
    values: np.ndarray,
    channel_valid: np.ndarray,
    allowed: np.ndarray,
    *,
    voltage_sigma: float = BROADBAND_VOLTAGE_SIGMA,
    maximum_channel_fraction: float = MAXIMUM_BROADBAND_CHANNEL_FRACTION,
) -> tuple[np.ndarray, np.ndarray]:
    """Exclude allowed times with simultaneous extreme amplitude in many channels."""
    data, valid, support = _validate(values, channel_valid, allowed)
    if not np.isfinite(voltage_sigma) or voltage_sigma <= 0:
        raise ValueError("broadband voltage sigma must be finite and positive")
    if (
        not np.isfinite(maximum_channel_fraction)
        or not 0 < maximum_channel_fraction <= 1
    ):
        raise ValueError("maximum broadband channel fraction must be inside (0, 1]")
    seed_by_channel_time = np.zeros(support.shape, dtype=bool)
    for channel in np.flatnonzero(valid):
        amplitude = np.abs(data[channel]).astype(np.float64)
        training = amplitude[:, support[channel]].reshape(-1)
        training = training[np.isfinite(training)]
        if training.size < MINIMUM_VOLTAGE_SAMPLES:
            continue
        center = float(np.median(training))
        spread = float(1.4826 * np.median(np.abs(training - center)))
        if spread <= 0:
            continue
        seed_by_channel_time[channel] = support[channel] & np.any(
            amplitude > center + voltage_sigma * spread, axis=0
        )
    valid_count = max(int(valid.sum()), 1)
    broadband_times = (
        seed_by_channel_time[valid].sum(axis=0) / valid_count
        > maximum_channel_fraction
    )
    return support & ~broadband_times[None, :], broadband_times


def select_voltage_kurtosis_channels(
    values: np.ndarray,
    channel_valid: np.ndarray,
    allowed: np.ndarray,
    *,
    sigma: float = KURTOSIS_SIGMA,
    iterations: int = KURTOSIS_ITERATIONS,
    broadband_voltage_sigma: float = BROADBAND_VOLTAGE_SIGMA,
    maximum_broadband_channel_fraction: float = MAXIMUM_BROADBAND_CHANNEL_FRACTION,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Select high-tail channels using one-sided iterative median comparison."""
    data, valid, support = _validate(values, channel_valid, allowed)
    if not np.isfinite(sigma) or sigma <= 0:
        raise ValueError("sigma must be finite and positive")
    if not isinstance(iterations, (int, np.integer)) or iterations <= 0:
        raise ValueError("iterations must be a positive integer")
    filtered_support, broadband_times = exclude_broadband_voltage_samples(
        data,
        valid,
        support,
        voltage_sigma=broadband_voltage_sigma,
        maximum_channel_fraction=maximum_broadband_channel_fraction,
    )
    kurtosis, sample_count = amplitude_kurtosis_by_channel(
        data, valid, filtered_support
    )
    selected = valid & ~np.isfinite(kurtosis)
    iterations_run = 0
    center = float("nan")
    spread = float("nan")
    for iteration in range(int(iterations)):
        keep = valid & ~selected
        if int(keep.sum()) < 10:
            break
        center = float(np.median(kurtosis[keep]))
        spread = float(1.4826 * np.median(np.abs(kurtosis[keep] - center)))
        if not np.isfinite(spread) or spread <= 0:
            break
        new = keep & ((kurtosis - center) / spread > sigma)
        iterations_run = iteration + 1
        if not new.any():
            break
        selected |= new
    keep = valid & ~selected
    if np.any(keep):
        center = float(np.median(kurtosis[keep]))
        spread = float(1.4826 * np.median(np.abs(kurtosis[keep] - center)))
    robust_z = np.full(data.shape[0], np.nan, dtype=np.float64)
    if np.isfinite(spread) and spread > 0:
        robust_z[valid] = (kurtosis[valid] - center) / spread
    diagnostics: dict[str, Any] = {
        "status": STATUS,
        "sigma": float(sigma),
        "iterations_requested": int(iterations),
        "iterations_run": int(iterations_run),
        "retained_center": center,
        "retained_spread": spread,
        "selected_channels": int(selected.sum()),
        "broadband_voltage_sigma": float(broadband_voltage_sigma),
        "maximum_broadband_channel_fraction": float(
            maximum_broadband_channel_fraction
        ),
        "excluded_broadband_times": int(broadband_times.sum()),
        "kurtosis": kurtosis,
        "robust_z": robust_z,
        "sample_count": sample_count,
    }
    return selected, diagnostics


def map_coarse_mask_to_fine_rows(
    fine_coarse_ids: np.ndarray,
    coarse_ids: np.ndarray,
    selected_coarse_channels: np.ndarray,
) -> np.ndarray:
    """Map a coarse-channel decision to every matching fine-frequency row."""
    fine = np.asarray(fine_coarse_ids)
    coarse = np.asarray(coarse_ids)
    selected = np.asarray(selected_coarse_channels, dtype=bool)
    if fine.ndim != 1 or coarse.ndim != 1 or selected.shape != coarse.shape:
        raise ValueError("fine IDs, coarse IDs, and selected coarse channels must be 1D")
    return np.isin(fine, coarse[selected])
