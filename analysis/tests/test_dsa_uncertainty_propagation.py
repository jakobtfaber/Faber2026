from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
if "blimpy" not in sys.modules:
    blimpy = types.ModuleType("blimpy")
    blimpy.Waterfall = object
    sys.modules["blimpy"] = blimpy

import audit_one_event_dsa_state_h17 as dsa_audit  # noqa: E402
from build_one_event_dsa_hybrid_h17 import (  # noqa: E402
    _validated_time_origin,
    aligned_profile_metrics,
    apply_residual_dm_absolute_crop,
    endpoint_gate_summary,
    reference_400_timing_half_width,
)
from one_event_workflow import legacy_stage_config, load_config  # noqa: E402
from run_one_event_absolute_dm_workflow import (  # noqa: E402
    _output_paths,
    expected_stage_outputs,
)


def test_casey_owner_decision_receipt_matches_runtime_configuration() -> None:
    config = load_config(ROOT / "analysis-configs/absolute-dm/casey.json")
    dsa_audit._validate_time_origin_owner_decision(legacy_stage_config(config))


def test_dsa_builder_requires_eligible_400_mhz_time_origin() -> None:
    expected = {
        "trigger_mjd_utc": "60369.37095221912",
        "trigger_reference_frequency_mhz": 1530.0,
        "filterbank_product_dm_pc_cm3": 491.211,
        "filterbank_peak_sample_index": 15259,
        "mapping_ambiguity_s": 0.000098304,
        "mapping_uncertainty_treatment": "owner_approved_discrete_two_anchor_sensitivity",
        "trigger_reference_frequency_status": "owner_approved_provisional_modeling_convention",
        "trigger_reference_frequency_sensitivity_required": True,
    }
    valid = {
        "timing": {
            "fit_observation_time_origin_eligible": True,
            "joint_fit_timing_uncertainty_eligible": True,
            "filterbank_sample_zero_status": (
                "derived_from_owner_approved_trigger_peak_anchor"
            ),
            "product_reference_frequency_mhz": 400.0,
            **expected,
        }
    }
    assert _validated_time_origin(valid, expected) is valid["timing"]
    pending = {
        "timing": valid["timing"] | {"joint_fit_timing_uncertainty_eligible": False}
    }
    assert (
        _validated_time_origin(pending, expected, require_fit_eligible=False)
        is pending["timing"]
    )
    with pytest.raises(RuntimeError, match="not fit eligible"):
        _validated_time_origin(pending, expected)
    for mutation in (
        {"fit_observation_time_origin_eligible": False},
        {"filterbank_sample_zero_status": "blocked"},
        {"product_reference_frequency_mhz": 1530.0},
    ):
        changed = {"timing": valid["timing"] | mutation}
        with pytest.raises(RuntimeError):
            _validated_time_origin(changed, expected)
    changed = {"timing": valid["timing"] | {"filterbank_peak_sample_index": 15258}}
    with pytest.raises(RuntimeError, match="differs from configuration"):
        _validated_time_origin(changed, expected)

    for mutation in (
        {
            "mapping_uncertainty_treatment": (
                "pending_owner_decision_discrete_two_anchor_sensitivity"
            )
        },
        {
            "trigger_reference_frequency_status": (
                "proposed_modeling_convention_pending_owner_decision"
            )
        },
        {"trigger_reference_frequency_sensitivity_required": False},
    ):
        with pytest.raises(RuntimeError, match="not owner approved|requirement is missing"):
            _validated_time_origin(valid, expected | mutation)

    for mutation in (
        {
            "mapping_uncertainty_treatment": (
                "pending_owner_decision_discrete_two_anchor_sensitivity"
            )
        },
        {
            "trigger_reference_frequency_status": (
                "proposed_modeling_convention_pending_owner_decision"
            )
        },
        {"trigger_reference_frequency_sensitivity_required": False},
    ):
        changed = {"timing": valid["timing"] | mutation}
        with pytest.raises(RuntimeError, match="differs from configuration"):
            _validated_time_origin(changed, expected)


def test_dsa_timing_becomes_fit_eligible_only_from_exact_reviewed_roster(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    roster_path = tmp_path / "timing-sensitivity-roster.json"
    roster = {"status": "prepared_pending_independent_review"}
    roster_path.write_text(json.dumps(roster))
    config = {
        "paths": {"output_root": str(tmp_path)},
        "joint_fit": {
            "review_decision": {
                "status": "approved",
                "timing_sensitivity_review_status": "approved",
                "timing_sensitivity_roster_sha256": dsa_audit.sha256(roster_path),
            }
        },
    }
    result = {"timing": {"joint_fit_timing_uncertainty_eligible": False}}
    checked: list[dict] = []
    monkeypatch.setattr(
        dsa_audit,
        "validate_timing_sensitivity_roster",
        lambda supplied_config, supplied_roster: checked.append(supplied_roster),
    )

    dsa_audit._admit_reviewed_timing_sensitivity(config, result)

    assert checked == [roster]
    assert result["timing"]["joint_fit_timing_uncertainty_eligible"] is True
    assert result["timing"]["timing_sensitivity_roster"]["sha256"] == (
        config["joint_fit"]["review_decision"]["timing_sensitivity_roster_sha256"]
    )

    roster_path.write_text(json.dumps({"status": "tampered"}))
    result = {"timing": {"joint_fit_timing_uncertainty_eligible": False}}
    with pytest.raises(RuntimeError, match="differs from reviewed input"):
        dsa_audit._admit_reviewed_timing_sensitivity(config, result)


def test_dsa_audit_rejects_unbound_owner_decision_before_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "dsa_state_audit.json"
    output.write_text("preserved\n")
    monkeypatch.setattr(
        dsa_audit,
        "audit",
        lambda _config: pytest.fail("audit must not run before owner receipt validation"),
    )
    config = {
        "event": "casey",
        "dsa_time_origin": {
            "owner_decision_receipt": (
                "analysis-configs/absolute-dm/decisions/casey-trigger-peak.json"
            ),
            "owner_decision_receipt_sha256": "0" * 64,
        },
    }
    with pytest.raises(RuntimeError, match="owner decision receipt SHA-256 mismatch"):
        dsa_audit.publish_audit(config, output)
    assert output.read_text() == "preserved\n"


def test_dsa_audit_owner_decision_comparison_preserves_decimal_precision() -> None:
    decision = ROOT / "analysis-configs/absolute-dm/decisions/casey-trigger-peak.json"
    config = {
        "event": "casey",
        "dsa_time_origin": {
            "owner_decision_receipt": (
                "analysis-configs/absolute-dm/decisions/casey-trigger-peak.json"
            ),
            "owner_decision_receipt_sha256": dsa_audit.sha256(decision),
            "trigger_mjd_utc": "60369.370952219121",
            "filterbank_peak_sample_index": 15259,
            "filterbank_product_dm_pc_cm3": 491.211,
        },
    }
    with pytest.raises(RuntimeError, match="scope differs"):
        dsa_audit._validate_time_origin_owner_decision(config)


def test_dsa_audit_owner_decision_path_cannot_leave_decision_directory() -> None:
    config = {
        "event": "casey",
        "dsa_time_origin": {
            "owner_decision_receipt": (
                "analysis-configs/absolute-dm/decisions/../casey-trigger-peak.json"
            ),
            "owner_decision_receipt_sha256": "0" * 64,
        },
    }
    with pytest.raises(RuntimeError, match="leaves the decision directory"):
        dsa_audit._validate_time_origin_owner_decision(config)


def test_dsa_audit_publication_is_atomic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "dsa_state_audit.json"
    output.write_text("preserved\n")
    monkeypatch.setattr(dsa_audit, "audit", lambda _config: {"status": "pass"})
    monkeypatch.setattr(
        dsa_audit.os,
        "replace",
        lambda _source, _destination: (_ for _ in ()).throw(OSError("injected")),
    )
    with pytest.raises(OSError, match="injected"):
        dsa_audit.publish_audit({}, output)
    assert output.read_text() == "preserved\n"
    assert list(tmp_path.glob(".*.tmp")) == []


def test_absolute_crop_uses_nonwrapping_fractional_coordinates() -> None:
    raw = np.repeat(np.arange(64, dtype=float)[None, :], 2, axis=0)
    frequency = np.asarray([500.0, 700.0])
    sample_time_s = 0.01
    residual_dm = 0.2
    crop_start = 20.25
    result = apply_residual_dm_absolute_crop(
        raw,
        frequency,
        sample_time_s,
        residual_dm,
        crop_start,
        8,
    )
    shift = (
        -4148.808
        * residual_dm
        * (frequency**-2 - 400.0**-2)
        / sample_time_s
    )
    expected = crop_start + np.arange(8)[None, :] - shift[:, None]

    assert np.allclose(result, expected)

    edge = apply_residual_dm_absolute_crop(
        raw,
        frequency,
        sample_time_s,
        residual_dm,
        0.0,
        8,
    )
    assert np.isnan(edge).any()


def test_profile_alignment_reports_shift_without_morphology_loss() -> None:
    sample = np.arange(128, dtype=float)
    profile = np.exp(-0.5 * ((sample - 64.0) / 5.0) ** 2)
    nominal = np.repeat(profile[None, :], 8, axis=0)
    endpoint = np.roll(nominal, 7, axis=1)
    live = np.ones(8, dtype=bool)

    result = aligned_profile_metrics(
        nominal,
        endpoint,
        live,
        maximum_lag_samples=12,
    )

    assert abs(result["lag_samples"]) == 7
    assert result["correlation"] > 0.999


def test_endpoint_gate_passes_and_fails_closed() -> None:
    endpoint_review = {
        target: {
            endpoint: {
                "measured_profile_lag_native_samples": 12,
                "peak_aligned_profile_correlation": 0.995,
                "timing_gate_passed": True,
                "morphology_gate_passed": True,
            }
            for endpoint in ("low", "high")
        }
        for target in ("anchor_dm", "hybrid_fit_dm", "geometry_dm")
    }
    passed = endpoint_gate_summary(
        endpoint_review,
        predicted_timing_half_width_native_samples=12.5,
        timing_limit_native_samples=16.0,
        correlation_limit=0.98,
    )
    assert passed["gallery_alignment_conclusion"] == (
        "robust_with_bounded_time_envelope"
    )

    endpoint_review["geometry_dm"]["high"][
        "peak_aligned_profile_correlation"
    ] = 0.97
    endpoint_review["geometry_dm"]["high"]["morphology_gate_passed"] = False
    failed = endpoint_gate_summary(
        endpoint_review,
        predicted_timing_half_width_native_samples=12.5,
        timing_limit_native_samples=16.0,
        correlation_limit=0.98,
    )
    assert failed["morphology_gate_passed"] is False
    assert failed["gallery_alignment_conclusion"] == (
        "not_robust_to_bound_endpoints"
    )


def test_reference_timing_and_conditional_endpoint_output_set() -> None:
    timing = reference_400_timing_half_width(
        0.015432014765899588,
        1530.0,
        32.768e-6,
    )
    assert timing["ms"] > 0
    assert timing["native_samples"] < 16

    config = {
        "workflow": {
            "regression_fixture": False,
        },
        "paths": {
            "output_root": "/tmp/event-one-event-workflow",
        },
    }
    outputs = expected_stage_outputs(
        "dsa_products",
        _output_paths(config),
        config,
    )
    assert len(outputs) == 12
    assert len({path.name for path in outputs}) == 12
