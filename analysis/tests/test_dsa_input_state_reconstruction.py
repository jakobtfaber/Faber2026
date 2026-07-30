import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from generate_phase_b_workflow_configs import (  # noqa: E402
    anchor_grid,
    reconstruction_blockers,
    reconstruction_contract,
    window_seconds,
)
from one_event_workflow import (  # noqa: E402
    event_binding_sha256,
    validate_config,
)
from reconstruct_dsa_input_state_h17 import (  # noqa: E402
    apply_known_zero_systematic_model,
    robust_delay_fit,
    synthetic_sign_oracle,
)


def test_synthetic_sign_oracle_recovers_positive_residual() -> None:
    result = synthetic_sign_oracle()

    assert result["passed"] is True
    assert result["absolute_error_pc_cm3"] < 0.003
    assert result["wrong_sign_error_pc_cm3"] > 0.25


def test_robust_delay_fit_rejects_outlier() -> None:
    delay = np.linspace(-0.2, -0.15, 128)
    expected_dm = -0.12
    start = 14000.0 + 4148.808 * expected_dm * delay
    start[31] += 20.0
    correlation = np.full(delay.size, 0.9)

    result = robust_delay_fit(delay, start, correlation)

    assert abs(result["reference_minus_raw_dm_pc_cm3"] - expected_dm) < 1.0e-9
    assert result["used_count"] == 127


def test_anchor_grid_covers_review_coordinates() -> None:
    result = anchor_grid(411.4359, 411.6966845542555, 411.62294699065603)

    assert result == {
        "anchor_dm_pc_cm3": 411.62,
        "coarse_half_width_pc_cm3": 0.25,
    }


def test_window_has_floor_and_width_margin() -> None:
    assert window_seconds(0.0002) == 0.03
    assert window_seconds(0.024286) == 0.04
    assert window_seconds(0.074202) == 0.1


def test_blocked_reconstruction_is_bound_as_blocker() -> None:
    contract = {
        "admissible": False,
        "failed_checks": [
            "held_out_correction",
            "shared_known_zero_control",
        ],
    }

    assert reconstruction_blockers(contract) == [
        "dsa_reconstruction_failed:held_out_correction",
        "dsa_reconstruction_failed:shared_known_zero_control",
    ]


def test_nonmaterial_reconstruction_uses_nominal_product_dm_with_bound() -> None:
    reconstruction = {
        "accepted_reference_dm_pc_cm3": 100.0,
        "reference_minus_raw_dm_pc_cm3": 0.04,
        "inferred_raw_input_dm_pc_cm3": 99.96,
        "conservative_uncertainty_pc_cm3": 0.015,
        "accepted_for_config_review": False,
        "material_nonzero_residual_proven": False,
        "checks": {
            "direct_order": True,
            "fit_precision": True,
            "flat_after_correction": True,
            "window_consistency": True,
            "separated_frequency_consistency": True,
            "integer_subsample_consistency": True,
            "corrected_row_match": True,
            "known_zero_systematic_model": True,
            "correction_improves_match": False,
            "correction_improves_profile": False,
            "held_out_correction": False,
            "material_nonzero_residual": False,
        },
    }

    contract = reconstruction_contract(reconstruction)

    assert contract["method"] == (
        "accepted_product_dm_nominal_with_residual_bound"
    )
    assert contract["nominal_input_dm_pc_cm3"] == 100.0
    assert contract["input_dm_half_width_pc_cm3"] == pytest.approx(0.055)
    assert contract["conservative_bound_accepted_for_config_review"] is True


def test_execution_requires_independent_uncertainty_review() -> None:
    config = json.loads(
        (
            ROOT / "analysis-configs/absolute-dm/casey.json"
        ).read_text()
    )
    config["workflow"]["regression_fixture"] = False
    config["workflow"]["execution_authorized"] = True
    config.pop("joint_fit")
    reconstruction = Path("/data/Faber2026/casey-dsa-reconstruction.json")
    config["paths"]["dsa_state_reconstruction"] = str(reconstruction)
    config["identity"]["input_basenames"]["dsa_state_reconstruction"] = (
        reconstruction.name
    )
    config["input_sha256"]["dsa_state_reconstruction"] = "1" * 64
    accepted_dm = float(config["dsa"]["accepted_reference_dm_pc_cm3"])
    config["dsa"].update(
        {
            "input_dm_pc_cm3": accepted_dm - 0.1,
            "input_dm_method": "inferred_raw_reference_row_timing",
            "input_dm_bound_source": "v3_inferred_value",
            "input_dm_half_width_pc_cm3": 0.01,
            "reference_minus_raw_dm_pc_cm3": 0.1,
            "reference_minus_raw_dm_interval_pc_cm3": [0.09, 0.11],
            "input_dm_reconstruction_sha256": "1" * 64,
            "raw_reference_frequency_crop_start_sample": 13998.0,
            "native_sample_time_s": 32.768e-6,
        }
    )
    config["dsa"]["gates"].update(
        {
            "input_dm_reference_timing_half_width_max_native_samples": 16.0,
            "input_dm_aligned_profile_correlation_min": 0.98,
            "gallery_alignment_must_be_robust": True,
        }
    )
    config["review"] = {
        "configuration_status": "reviewed",
        "blockers": [],
        "dsa_input_state": {
            "authority": "raw_reference_row_timing_v3_value_or_bound",
            "reconstruction_sha256": "1" * 64,
            "independent_uncertainty_review_status": "pending",
            "accepted_for_config_review": True,
            "conservative_bound_accepted_for_config_review": False,
            "material_nonzero_residual_proven": True,
            "inferred_raw_input_dm_pc_cm3": accepted_dm - 0.1,
            "conservative_uncertainty_pc_cm3": 0.01,
        },
    }
    config["event_binding_sha256"] = event_binding_sha256(config)

    with pytest.raises(PermissionError, match="reviewed, unblocked"):
        validate_config(config, require_execution_authorized=True)


def test_known_zero_control_sets_floor_and_rejects_nonmaterial_result() -> None:
    def row(event: str, residual: float, improvement: float) -> dict:
        return {
            "event": event,
            "reference_minus_raw_dm_pc_cm3": residual,
            "conservative_uncertainty_pc_cm3": 0.003,
            "correction_validation": {
                "corrected_row_correlation_median": 0.95,
                "uncorrected_row_correlation_median": 0.80,
                "row_correlation_improvement": improvement,
                "corrected_profile_correlation": 0.95,
                "uncorrected_profile_correlation": 0.80,
            },
            "held_out_validation": {
                "correction": {
                    "corrected_row_correlation_median": 0.95,
                    "uncorrected_row_correlation_median": 0.80,
                    "row_correlation_improvement": improvement,
                    "corrected_profile_correlation": 0.95,
                    "uncorrected_profile_correlation": 0.80,
                }
            },
            "checks": {
                "direct_order": True,
                "fit_precision": True,
                "flat_after_correction": True,
                "window_consistency": True,
                "separated_frequency_consistency": True,
                "integer_subsample_consistency": True,
                "corrected_row_match": True,
                "correction_improves_match": True,
                "correction_improves_profile": True,
                "held_out_correction": True,
            },
        }

    events = [row("casey", -0.0104, 0.0), row("oran", -0.11, 0.1)]

    control = apply_known_zero_systematic_model(events)

    assert control["strict_tolerance_passed"] is False
    assert control["derived_systematic_floor_pc_cm3"] == pytest.approx(0.0154)
    assert events[0]["accepted_for_config_review"] is False
    assert events[1]["accepted_for_config_review"] is True
