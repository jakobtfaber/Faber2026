#!/usr/bin/env python3
"""Development-only robust off-pulse frequency-row RFI component.

All decisions use only the supplied half-open off-pulse training interval.
Selected rows become explicit missing data; retained values are unchanged.
This component is not a complete or validated RFI cleaner.
"""

from __future__ import annotations

from typing import Any

import numpy as np


STATUS = "development_only_horizontal_row_component"
ROBUST_SIGMA = 5.0
ROBUST_ITERATIONS = 6
SEED_PIXEL_THRESHOLD = 6.0
SEED_GROUP_SIZE = 64
MINIMUM_SEED_ROWS_PER_GROUP = 4
MAXIMUM_BROADBAND_SEED_FRACTION = 0.01


def _validate(
    values: np.ndarray,
    row_valid: np.ndarray,
    training: tuple[int, int],
) -> tuple[np.ndarray, np.ndarray, int, int]:
    data = np.asarray(values)
    valid = np.asarray(row_valid, dtype=bool)
    if data.ndim != 2 or valid.shape != (data.shape[0],):
        raise ValueError("values must be 2D with one row-valid value per row")
    start, stop = (int(training[0]), int(training[1]))
    if not 0 <= start < stop <= data.shape[1]:
        raise ValueError("training interval must be non-empty and inside values")
    return data, valid, start, stop


def _mad_z(values: np.ndarray) -> tuple[np.ndarray, float, float]:
    data = np.asarray(values, dtype=np.float64)
    center = float(np.nanmedian(data))
    spread = float(1.4826 * np.nanmedian(np.abs(data - center)))
    if not np.isfinite(spread) or spread == 0:
        return np.zeros_like(data), center, 0.0
    return (data - center) / spread, center, spread


def offpulse_channel_stats(
    values: np.ndarray,
    row_valid: np.ndarray,
    training: tuple[int, int],
) -> dict[str, np.ndarray]:
    """Return per-row mean, standard deviation, and lag-one correlation."""
    data, valid, start, stop = _validate(values, row_valid, training)
    segment_data = np.asarray(data[:, start:stop], dtype=np.float64)
    segment_mask = ~np.isfinite(segment_data) | ~valid[:, None]
    segment = np.ma.MaskedArray(segment_data, mask=segment_mask)
    mean = np.ma.filled(np.ma.mean(segment, axis=1), np.nan)
    standard_deviation = np.ma.filled(np.ma.std(segment, axis=1), np.nan)
    centered = segment - np.ma.mean(segment, axis=1, keepdims=True)
    centered_filled = np.ma.filled(centered, 0.0)
    numerator = np.sum(centered_filled[:, 1:] * centered_filled[:, :-1], axis=1)
    denominator = np.sum(centered_filled * centered_filled, axis=1)
    lag1_correlation = np.zeros(data.shape[0], dtype=np.float64)
    np.divide(
        numerator,
        denominator,
        out=lag1_correlation,
        where=denominator > 0,
    )
    lag1_correlation[~valid] = np.nan
    return {
        "mean": mean,
        "standard_deviation": standard_deviation,
        "lag1_correlation": lag1_correlation,
    }


def robust_offpulse_row_mask(
    values: np.ndarray,
    row_valid: np.ndarray,
    training: tuple[int, int],
    *,
    sigma: float = ROBUST_SIGMA,
    iterations: int = ROBUST_ITERATIONS,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Return additional row vetoes learned only from off-pulse statistics."""
    data, valid, start, stop = _validate(values, row_valid, training)
    if not np.isfinite(sigma) or sigma <= 0:
        raise ValueError("sigma must be finite and positive")
    if not isinstance(iterations, (int, np.integer)) or iterations <= 0:
        raise ValueError("iterations must be a positive integer")
    statistics = offpulse_channel_stats(data, valid, (start, stop))
    standard_deviation = statistics["standard_deviation"]
    lag1_correlation = statistics["lag1_correlation"]
    selected = valid & (
        ~np.isfinite(standard_deviation) | (standard_deviation <= 0)
    )
    iterations_run = 0
    selected_by_standard_deviation = np.zeros(data.shape[0], dtype=bool)
    selected_by_lag1 = np.zeros(data.shape[0], dtype=bool)
    for iteration in range(int(iterations)):
        keep = valid & ~selected
        if int(keep.sum()) < 10:
            break
        newly = np.zeros(data.shape[0], dtype=bool)
        for values_by_row, selected_by_feature in (
            (standard_deviation, selected_by_standard_deviation),
            (lag1_correlation, selected_by_lag1),
        ):
            z_keep, _, spread = _mad_z(values_by_row[keep])
            if spread == 0:
                continue
            feature_new = np.zeros(data.shape[0], dtype=bool)
            feature_new[keep] = np.abs(z_keep) > sigma
            selected_by_feature |= feature_new
            newly |= feature_new
        iterations_run = iteration + 1
        if not newly.any():
            break
        selected |= newly

    sd_z, sd_center, sd_spread = _mad_z(standard_deviation[valid & ~selected])
    lag_z, lag_center, lag_spread = _mad_z(lag1_correlation[valid & ~selected])
    diagnostics: dict[str, Any] = {
        "status": STATUS,
        "training": [start, stop],
        "sigma": float(sigma),
        "iterations_requested": int(iterations),
        "iterations_run": int(iterations_run),
        "selected_rows": int(selected.sum()),
        "selected_by_standard_deviation": int(selected_by_standard_deviation.sum()),
        "selected_by_lag1_correlation": int(selected_by_lag1.sum()),
        "retained_standard_deviation_center": sd_center,
        "retained_standard_deviation_spread": sd_spread,
        "retained_lag1_center": lag_center,
        "retained_lag1_spread": lag_spread,
        "retained_standard_deviation_z_max": (
            float(np.max(np.abs(sd_z))) if sd_z.size else None
        ),
        "retained_lag1_z_max": float(np.max(np.abs(lag_z))) if lag_z.size else None,
        "standard_deviation": standard_deviation,
        "lag1_correlation": lag1_correlation,
    }
    return selected, diagnostics


def apply_row_mask(
    values: np.ndarray,
    selected_rows: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Copy values and replace finite samples in selected rows by NaN."""
    data = np.asarray(values)
    rows = np.asarray(selected_rows, dtype=bool)
    if data.ndim != 2 or rows.shape != (data.shape[0],):
        raise ValueError("values must be 2D with one selected-row value per row")
    pixel_mask = rows[:, None] & np.isfinite(data)
    output = np.array(data, copy=True, dtype=np.result_type(data.dtype, np.float32))
    output[pixel_mask] = np.nan
    return output, pixel_mask


def offpulse_seed_row_mask(
    values: np.ndarray,
    row_valid: np.ndarray,
    protected: tuple[int, int],
    *,
    pixel_threshold: float = SEED_PIXEL_THRESHOLD,
    group_size: int = SEED_GROUP_SIZE,
    minimum_seed_rows_per_group: int = MINIMUM_SEED_ROWS_PER_GROUP,
    maximum_broadband_seed_fraction: float = MAXIMUM_BROADBAND_SEED_FRACTION,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Promote strong off-pulse seeds to rows in recurrent coarse groups.

    Values inside the half-open protected interval never affect a decision.
    A seed row contains at least one qualifying off-pulse pixel. Seed rows are
    Values inside the half-open protected interval never affect a decision.
    A seed row contains at least one qualifying off-pulse pixel. Seed rows are
    selected only when enough distinct seed rows occur in the same group.
    """
    data, valid, start, stop = _validate(values, row_valid, protected)
    if start == 0 and stop == data.shape[1]:
        raise ValueError("protected interval must leave off-pulse columns")
    if not np.isfinite(pixel_threshold) or pixel_threshold <= 0:
        raise ValueError("pixel threshold must be finite and positive")
    if not isinstance(group_size, (int, np.integer)) or group_size <= 0:
        raise ValueError("group size must be a positive integer")
    if data.shape[0] % int(group_size):
        raise ValueError("frequency rows must be divisible by group size")
    if (
        not isinstance(minimum_seed_rows_per_group, (int, np.integer))
        or minimum_seed_rows_per_group <= 0
        or minimum_seed_rows_per_group > group_size
    ):
        raise ValueError("minimum seed rows must be inside the group size")
    if (
        not np.isfinite(maximum_broadband_seed_fraction)
        or not 0 < maximum_broadband_seed_fraction <= 1
    ):
        raise ValueError("maximum broadband seed fraction must be inside (0, 1]")

    offpulse = np.ones(data.shape[1], dtype=bool)
    offpulse[start:stop] = False
    raw_seed_pixels = (
        valid[:, None]
        & np.isfinite(data)
        & offpulse[None, :]
        & (np.abs(data) >= pixel_threshold)
    )
    valid_count = max(int(valid.sum()), 1)
    broadband_columns = (
        raw_seed_pixels.sum(axis=0) / valid_count
        > maximum_broadband_seed_fraction
    )
    seed_hits = np.sum(
        raw_seed_pixels & ~broadband_columns[None, :],
        axis=1,
    )
    seed_rows = valid & (seed_hits > 0)
    seed_count_by_group = seed_rows.reshape(-1, int(group_size)).sum(axis=1)
    qualifying_groups = seed_count_by_group >= int(minimum_seed_rows_per_group)
    selected = seed_rows & np.repeat(qualifying_groups, int(group_size))
    diagnostics: dict[str, Any] = {
        "status": STATUS,
        "protected": [start, stop],
        "pixel_threshold": float(pixel_threshold),
        "group_size": int(group_size),
        "minimum_seed_rows_per_group": int(minimum_seed_rows_per_group),
        "maximum_broadband_seed_fraction": float(
            maximum_broadband_seed_fraction
        ),
        "offpulse_columns": int(offpulse.sum()),
        "excluded_broadband_columns": int(broadband_columns.sum()),
        "seed_rows": int(seed_rows.sum()),
        "qualifying_groups": int(qualifying_groups.sum()),
        "selected_rows": int(selected.sum()),
        "seed_hits_by_row": seed_hits,
        "seed_count_by_group": seed_count_by_group,
    }
    return selected, diagnostics
