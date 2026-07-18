import math
import json
from pathlib import Path

from scripts.build_provisional_propagation_tables import (
    classify_foreground_alignment,
    classify_products,
    screen_product,
)


def test_screen_product_reproduces_thin_screen_identity():
    dnu_mhz = 1.0 / (2.0 * math.pi * 1000.0)
    value, error = screen_product(
        tau_1ghz_ms=1.0,
        tau_err_ms=0.0,
        alpha=4.0,
        alpha_err=0.0,
        center_freq_mhz=1000.0,
        dnu_mhz=dnu_mhz,
        dnu_err_mhz=0.0,
    )
    assert math.isclose(value, 1.0 / (2.0 * math.pi), rel_tol=1e-12)
    assert error == 0.0


def test_screen_product_scales_tau_at_component_frequency():
    value, _ = screen_product(1.0, 0.0, 4.0, 0.0, 2000.0, 1.0, 0.0)
    assert math.isclose(value, 62.5, rel_tol=1e-12)


def test_two_screen_verdict_requires_every_component_above_range_with_error():
    assert classify_products([(10.0, 1.0), (3.0, 0.5)]) == "two-screen favored"
    assert classify_products([(10.0, 1.0), (2.4, 0.5)]) == "indeterminate"


def test_foreground_alignment_classification_is_cautious_and_coverage_aware():
    assert classify_foreground_alignment("accepted_physical", 4, False, 0.22) == (
        "plausible partial foreground contribution")
    assert classify_foreground_alignment("accepted_physical", 1, False, 0.005) == (
        "foreground contribution small in fiducial model")
    assert classify_foreground_alignment("accepted_physical", 0, True, 0.0) == (
        "coverage-limited; no eligible foreground identified")
    assert classify_foreground_alignment("morphology_only", 2, False, 11.0) == (
        "fit unusable; foreground prediction exceeds fit")


def test_frozen_result_roster_and_status_are_explicit():
    result = json.loads(Path("analysis/provisional_propagation/results.json").read_text())
    assert result["status"] == "SCREEN_ANALYSIS_PENDING"
    assert result["screen_analysis_status"] == "PENDING_ALPHA4_CONSISTENCY_REFITS"
    assert len(result["screen_rows"]) == 7
    assert all(r["verdict"] == "pending fixed-index consistency refit"
               for r in result["screen_rows"])
    assert all(not r["products"] for r in result["screen_rows"])
    assert "foreground_alignment_rows" not in result
