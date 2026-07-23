from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest


SCRIPT = Path(__file__).parents[1] / "scripts" / "rfi_time_frequency_candidate.py"
SPEC = importlib.util.spec_from_file_location("rfi_time_frequency_candidate", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_absolute_pixel_mask_has_analytic_threshold_and_missing_data_semantics():
    values = np.array(
        [
            [5.999, 6.0, -6.0, np.nan],
            [100.0, -100.0, 7.0, 0.0],
        ]
    )
    mask = MODULE.absolute_pixel_mask(values, np.array([True, False]))

    np.testing.assert_array_equal(
        mask,
        np.array(
            [
                [False, True, True, False],
                [False, False, False, False],
            ]
        ),
    )


def test_apply_pixel_mask_changes_only_masked_values_and_does_not_mutate_input():
    values = np.array([[1.0, 6.0, -7.0], [2.0, 3.0, 4.0]], dtype=np.float32)
    original = values.copy()

    cleaned, mask = MODULE.apply_pixel_mask(values, np.array([True, True]))

    np.testing.assert_array_equal(values, original)
    np.testing.assert_array_equal(mask, [[False, True, True], [False, False, False]])
    np.testing.assert_array_equal(cleaned[~mask], original[~mask])
    assert np.isnan(cleaned[mask]).all()


def test_pixel_mask_rejects_invalid_shapes_and_thresholds():
    with pytest.raises(ValueError, match="one row-valid value"):
        MODULE.absolute_pixel_mask(np.ones((2, 3)), np.array([True]))
    with pytest.raises(ValueError, match="positive"):
        MODULE.absolute_pixel_mask(np.ones((2, 3)), np.array([True, True]), threshold=0)
