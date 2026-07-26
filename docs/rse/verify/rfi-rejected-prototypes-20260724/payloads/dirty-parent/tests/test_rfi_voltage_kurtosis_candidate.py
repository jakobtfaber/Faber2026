from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest


SCRIPT = Path(__file__).parents[1] / "scripts" / "rfi_voltage_kurtosis_candidate.py"
SPEC = importlib.util.spec_from_file_location("rfi_voltage_kurtosis_candidate", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def synthetic_voltage(seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return (
        rng.standard_normal((32, 2, 512))
        + 1j * rng.standard_normal((32, 2, 512))
    ).astype(np.complex64)


def test_protected_values_cannot_change_voltage_kurtosis_decisions():
    values = synthetic_voltage()
    allowed = np.ones((32, 512), dtype=bool)
    allowed[:, 200:320] = False
    changed = values.copy()
    changed[:, :, 200:320] = 1e12 + 1e12j

    first, _ = MODULE.select_voltage_kurtosis_channels(
        values, np.ones(32, bool), allowed
    )
    second, _ = MODULE.select_voltage_kurtosis_channels(
        changed, np.ones(32, bool), allowed
    )

    np.testing.assert_array_equal(first, second)


def test_impulsive_voltage_channels_selected_and_clean_control_retained():
    values = synthetic_voltage()
    allowed = np.ones((32, 512), dtype=bool)
    contaminated = values.copy()
    columns = np.arange(0, 80, 8)
    contaminated[:4, :, columns] += 50.0 + 50.0j

    selected, diagnostics = MODULE.select_voltage_kurtosis_channels(
        contaminated,
        np.ones(32, bool),
        allowed,
        maximum_broadband_channel_fraction=0.2,
    )
    clean_selected, _ = MODULE.select_voltage_kurtosis_channels(
        values,
        np.ones(32, bool),
        allowed,
        maximum_broadband_channel_fraction=0.2,
    )

    assert selected[:4].all()
    assert not selected[4:].any()
    assert not clean_selected.any()
    assert diagnostics["selected_channels"] == 4


def test_coarse_selection_maps_only_matching_fine_rows():
    fine_ids = np.array([2, 2, 4, 4, 7, 7])
    selected = MODULE.map_coarse_mask_to_fine_rows(
        fine_ids,
        np.array([2, 4, 7]),
        np.array([False, True, False]),
    )

    np.testing.assert_array_equal(selected, [False, False, True, True, False, False])


def test_voltage_kurtosis_invalid_inputs_fail_closed():
    values = synthetic_voltage()
    with pytest.raises(ValueError, match="channel-valid"):
        MODULE.select_voltage_kurtosis_channels(
            values, np.ones(31, bool), np.ones((32, 512), bool)
        )
    with pytest.raises(ValueError, match="allowed"):
        MODULE.select_voltage_kurtosis_channels(
            values, np.ones(32, bool), np.ones((32, 511), bool)
        )
    with pytest.raises(ValueError, match="positive"):
        MODULE.select_voltage_kurtosis_channels(
            values, np.ones(32, bool), np.ones((32, 512), bool), sigma=0
        )
