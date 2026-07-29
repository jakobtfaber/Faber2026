from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
if "blimpy" not in sys.modules:
    blimpy = types.ModuleType("blimpy")
    blimpy.Waterfall = object
    sys.modules["blimpy"] = blimpy

from build_one_event_dsa_hybrid_h17 import (  # noqa: E402
    aligned_profile_metrics,
    apply_residual_dm_absolute_crop,
    endpoint_gate_summary,
    reference_400_timing_half_width,
)
from run_one_event_absolute_dm_workflow import (  # noqa: E402
    _output_paths,
    expected_stage_outputs,
)


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
