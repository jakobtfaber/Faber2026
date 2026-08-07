from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from calibrate_dsa_input_state_h17 import (  # noqa: E402
    finalize_bounds,
    fit_free_intercept_calibration,
    integer_lag_consistent_interval,
    intersect_intervals,
)


def test_free_intercept_calibration_recovers_bias_without_forcing_zero() -> None:
    injected = np.linspace(-0.12, 0.12, 9)
    training = -0.011 + 0.97 * injected
    validation = -0.0105 + 0.971 * injected

    result = fit_free_intercept_calibration(
        injected,
        training,
        validation,
    )

    assert result["zero_intercept_forced"] is False
    assert result["intercept_pc_cm3"] == pytest.approx(-0.011)
    assert result["slope"] == pytest.approx(0.97)
    assert result["held_out_max_abs_error_pc_cm3"] < 0.001
    assert result["passed"] is True


def test_free_intercept_calibration_rejects_nonmonotonic_holdout() -> None:
    injected = np.linspace(-0.12, 0.12, 9)
    training = injected.copy()
    validation = injected.copy()
    validation[4], validation[5] = validation[5], validation[4]

    result = fit_free_intercept_calibration(
        injected,
        training,
        validation,
    )

    assert result["checks"]["monotonic"] is False
    assert result["passed"] is False


def test_integer_lag_interval_contains_injected_dm() -> None:
    delay = np.linspace(-0.21, -0.14, 128)
    injected_dm = 0.06
    start = np.rint(14000.2 + 4148.808 * injected_dm * delay)
    correlation = np.full(delay.size, 0.95)

    result = integer_lag_consistent_interval(
        delay,
        start,
        correlation,
        dm_min=-0.1,
        dm_max=0.2,
    )

    assert result["accepted"] is True
    lower, upper = result["consistent_interval_pc_cm3"]
    assert lower <= injected_dm <= upper
    assert result["best_quantile_abs_residual_samples"] <= 0.75


def test_interval_intersection_is_fail_closed() -> None:
    assert intersect_intervals([-0.1, 0.1], [-0.05, 0.2]) == [-0.05, 0.1]
    assert intersect_intervals([-0.1, -0.05], [0.0, 0.1]) is None


def test_finalize_requires_casey_gate_and_three_way_overlap() -> None:
    def event(name: str, calibrated: float, integer: list[float]) -> dict:
        return {
            "event": name,
            "calibrated_observed_residual_dm_pc_cm3": calibrated,
            "preliminary_calibration_uncertainty_pc_cm3": 0.003,
            "integer_lag_interval": {
                "consistent_interval_pc_cm3": integer,
            },
            "checks_before_zero_control": {
                "all_windows_calibrated": True,
                "window_observed_consistency": True,
                "integer_lag_interval": True,
            },
        }

    events = [
        event("control", 0.001, [-0.02, 0.02]),
        event("target", 0.04, [0.03, 0.05]),
    ]
    reconstruction = {
        "control": {
            "reference_minus_raw_dm_pc_cm3": 0.01,
            "conservative_uncertainty_pc_cm3": 0.02,
        },
        "target": {
            "reference_minus_raw_dm_pc_cm3": 0.04,
            "conservative_uncertainty_pc_cm3": 0.02,
        },
    }

    control = finalize_bounds(
        events,
        reconstruction,
        zero_control_event="control",
    )

    assert control["passed"] is True
    assert events[1]["calibration_accepted_for_bound_narrowing"] is True
    assert events[1]["selected_residual_interval_pc_cm3"] == pytest.approx(
        [0.034, 0.046]
    )
