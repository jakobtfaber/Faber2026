"""Unit tests for the Figure 1 residual-drift gate."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from audit_fig1_residual_drift import product_dm, zero_consistency  # noqa: E402
from audit_fig1_frequency_axes import order  # noqa: E402


def test_product_dm_parses_archival_filename():
    assert product_dm(Path("chromatica_chime_I_272_368_cntr_bpc.npy")) == 272.368


def test_zero_consistency_is_fail_closed():
    assert zero_consistency({"n": 8, "residual_dm": 0.01, "sigma": 0.01}) == "consistent_zero"
    assert zero_consistency({"n": 8, "residual_dm": 0.03, "sigma": 0.01}) == "nonzero"
    assert zero_consistency({"n": 2, "residual_dm": None, "sigma": None}) == "unconstrained"


def test_frequency_order_is_explicit():
    assert order(1498.75, 1311.28) == "descending"
    assert order(400.0, 800.0) == "ascending"
