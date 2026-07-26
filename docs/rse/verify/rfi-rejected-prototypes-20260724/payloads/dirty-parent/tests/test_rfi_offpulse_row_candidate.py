from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest


SCRIPT = Path(__file__).parents[1] / "scripts" / "rfi_offpulse_row_candidate.py"
SPEC = importlib.util.spec_from_file_location("rfi_offpulse_row_candidate", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def scaled_alternating_rows(scales: np.ndarray) -> np.ndarray:
    time = np.tile([-1.0, 1.0], 8)
    return np.vstack([scale * time for scale in scales])


def test_decisions_ignore_every_value_outside_training():
    base = scaled_alternating_rows(np.linspace(0.8, 1.2, 12))
    changed = base.copy()
    changed[:, 8:] = 1e6

    first, _ = MODULE.robust_offpulse_row_mask(
        base, np.ones(12, dtype=bool), (0, 8)
    )
    second, _ = MODULE.robust_offpulse_row_mask(
        changed, np.ones(12, dtype=bool), (0, 8)
    )

    np.testing.assert_array_equal(first, second)


def test_obvious_variable_row_is_flagged_but_noise_rows_are_retained():
    rows = scaled_alternating_rows(
        np.concatenate((np.linspace(0.8, 1.2, 11), [8.0]))
    )

    selected, diagnostics = MODULE.robust_offpulse_row_mask(
        rows, np.ones(12, dtype=bool), (0, 16)
    )

    assert selected.sum() == 1
    assert selected[-1]
    assert diagnostics["selected_rows"] == 1
    assert diagnostics["sigma"] == 5.0


def test_row_mask_changes_only_selected_finite_values_without_mutation():
    values = np.array([[1.0, np.nan], [2.0, 3.0], [4.0, 5.0]], dtype=np.float32)
    original = values.copy()

    output, pixel_mask = MODULE.apply_row_mask(
        values, np.array([False, True, False])
    )

    np.testing.assert_array_equal(values, original)
    np.testing.assert_array_equal(
        pixel_mask,
        np.array([[False, False], [True, True], [False, False]]),
    )
    np.testing.assert_array_equal(output[~pixel_mask], original[~pixel_mask])
    assert np.isnan(output[pixel_mask]).all()


def test_invalid_shapes_training_and_configuration_fail_closed():
    values = np.ones((12, 16))
    valid = np.ones(12, dtype=bool)
    with pytest.raises(ValueError, match="one row-valid"):
        MODULE.robust_offpulse_row_mask(values, valid[:-1], (0, 8))
    with pytest.raises(ValueError, match="training interval"):
        MODULE.robust_offpulse_row_mask(values, valid, (8, 8))
    with pytest.raises(ValueError, match="training interval"):
        MODULE.robust_offpulse_row_mask(values, valid, (0, 17))
    with pytest.raises(ValueError, match="positive"):
        MODULE.robust_offpulse_row_mask(values, valid, (0, 8), sigma=0)
    with pytest.raises(ValueError, match="positive"):
        MODULE.robust_offpulse_row_mask(values, valid, (0, 8), iterations=0)


def test_seed_promotion_excludes_protected_burst_and_requires_group_recurrence():
    values = np.zeros((128, 12), dtype=float)
    values[:, 4:8] = 1000.0
    values[:4, 1] = 7.0
    values[64, 1] = 7.0

    selected, diagnostics = MODULE.offpulse_seed_row_mask(
        values,
        np.ones(128, dtype=bool),
        (4, 8),
        pixel_threshold=6.0,
        group_size=64,
        minimum_seed_rows_per_group=4,
        maximum_broadband_seed_fraction=0.1,
    )

    assert selected[:4].all()
    assert not selected[4:].any()
    assert diagnostics["selected_rows"] == 4
    assert diagnostics["qualifying_groups"] == 1


def test_seed_promotion_decisions_ignore_every_protected_value():
    values = np.zeros((64, 10), dtype=float)
    values[:5, 0] = 7.0
    changed = values.copy()
    changed[:, 3:7] = np.arange(64)[:, None] * 1e9

    first, _ = MODULE.offpulse_seed_row_mask(
        values,
        np.ones(64, bool),
        (3, 7),
        maximum_broadband_seed_fraction=0.1,
    )
    second, _ = MODULE.offpulse_seed_row_mask(
        changed,
        np.ones(64, bool),
        (3, 7),
        maximum_broadband_seed_fraction=0.1,
    )

    np.testing.assert_array_equal(first, second)


def test_optional_single_seed_rule_accepts_isolated_strong_offpulse_row():
    values = np.zeros((64, 10), dtype=float)
    values[17, 1] = 7.0

    selected, diagnostics = MODULE.offpulse_seed_row_mask(
        values,
        np.ones(64, bool),
        (3, 7),
        minimum_seed_rows_per_group=1,
        maximum_broadband_seed_fraction=0.1,
    )

    assert selected.sum() == 1
    assert selected[17]
    assert diagnostics["minimum_seed_rows_per_group"] == 1


def test_seed_promotion_does_not_convert_broadband_impulse_to_row_vetoes():
    values = np.zeros((128, 12), dtype=float)
    values[:, 1] = 8.0
    values[:5, 2] = 8.0

    selected, diagnostics = MODULE.offpulse_seed_row_mask(
        values,
        np.ones(128, bool),
        (4, 8),
        maximum_broadband_seed_fraction=0.1,
    )

    assert selected[:5].all()
    assert not selected[5:].any()
    assert diagnostics["excluded_broadband_columns"] == 1
