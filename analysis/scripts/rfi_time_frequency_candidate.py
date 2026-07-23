#!/usr/bin/env python3
"""Development-only fixed-threshold time-frequency RFI mask.

This module is a frozen review candidate, not a validated science cleaner.
It never replaces values: rejected finite pixels become explicit missing data.
"""

from __future__ import annotations

import numpy as np


STATUS = "development_only_not_rfi_validated"
ABSOLUTE_PIXEL_THRESHOLD = 6.0


def absolute_pixel_mask(
    values: np.ndarray,
    row_valid: np.ndarray,
    *,
    threshold: float = ABSOLUTE_PIXEL_THRESHOLD,
) -> np.ndarray:
    """Return finite, row-valid pixels whose absolute value meets threshold."""
    data = np.asarray(values)
    valid = np.asarray(row_valid, dtype=bool)
    if data.ndim != 2 or valid.shape != (data.shape[0],):
        raise ValueError("values must be 2D with one row-valid value per row")
    if not np.isfinite(threshold) or threshold <= 0:
        raise ValueError("threshold must be finite and positive")
    return valid[:, None] & np.isfinite(data) & (np.abs(data) >= threshold)


def apply_pixel_mask(
    values: np.ndarray,
    row_valid: np.ndarray,
    *,
    threshold: float = ABSOLUTE_PIXEL_THRESHOLD,
) -> tuple[np.ndarray, np.ndarray]:
    """Copy values and set newly rejected pixels to NaN."""
    data = np.asarray(values)
    mask = absolute_pixel_mask(data, row_valid, threshold=threshold)
    output = np.array(data, copy=True, dtype=np.result_type(data.dtype, np.float32))
    output[mask] = np.nan
    return output, mask
