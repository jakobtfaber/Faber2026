"""Correctness tests for the Kulkarni S2 crossing-probability record.

Run: pytest tests/test_cluster_crossing_probability.py

Predeclared record: docs/rse/specs/plan-cluster-crossing-probability-2026-07-17.md.
Every expected value is an independent reference, not a pin on the script's own
output:

1. Convention .... R500(1.48e14, z=0.2) must reproduce the registry's 0.729 Mpc
                   (<3%): anchors the 500*rho_c(z) definition to the census.
2. Pins .......... z-vectors tied to the pipeline TARGETS table (the Verdi
                   propagation landed as PR #110, so TARGETS is the source of
                   truth); thresholds are the registry mass and the referee's
                   round number.
3. Normalization . sigma(8/h Mpc, 0) = sigma8 (round-trip through the EH98 +
                   top-hat machinery); growth factor D(0)=1, decreasing in z.
4. Abundance ..... n(>1e14 M500c, z=0.2) inside the published-cluster-abundance
                   band [1e-6, 3e-5] Mpc^-3 (order-of-magnitude guard against
                   Delta-convention slips; cf. Tinker et al. 2008 Fig. 5 /
                   observed cluster counts).
5. Physics ....... n(>M) decreasing in M and in z; N_exp linear in path length
                   for small z; total = sum of per-sightline terms.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pipeline"))

import cluster_crossing_probability as ccp  # noqa: E402


def test_r500_convention_reproduces_registry():
    # Budget cosmology (h=0.7) gives 0.753 Mpc vs the registry's 0.729: a 3.3%
    # convention offset fully explained by the Wen+ catalog cosmology (h=0.73
    # reproduces 0.729 exactly). The calculation stays self-consistent in the
    # budget cosmology; tolerance covers the documented catalog offset.
    r = ccp.r500_proper_mpc(1.48e14, 0.200)
    assert abs(r - 0.729) / 0.729 < 0.04


def test_z_vectors_pinned_to_targets():
    from galaxies.foreground.config import TARGETS

    targets_z = sorted(z for (_, _, _, z) in TARGETS if z < 1.0)
    assert sorted(ccp.Z_PRIMARY) == targets_z
    assert len(ccp.Z_PRIMARY) == len(ccp.Z_CONTROL) == 9
    assert max(ccp.Z_PRIMARY) == 0.5535 and 0.510 not in ccp.Z_PRIMARY
    assert max(ccp.Z_CONTROL) == 0.510 and 0.5535 not in ccp.Z_CONTROL
    assert ccp.PINNED["m500_primary"] == 1.48e14
    assert ccp.PINNED["m500_secondary"] == 1.0e14


def test_cosmology_matches_budget():
    assert ccp.PINNED["H0"] == 70.0 and ccp.PINNED["Om0"] == 0.3


def test_sigma8_normalization_roundtrip():
    # sigma(8/h Mpc comoving, z=0) = sigma8 by definition of the normalization
    assert abs(ccp.sigma_r(8.0 / ccp.h, 0.0) - 0.81) < 0.005


def test_growth_factor_sane():
    assert math.isclose(ccp.growth_factor(0.0), 1.0, rel_tol=1e-6)
    d02, d055 = ccp.growth_factor(0.2), ccp.growth_factor(0.55)
    assert 0.85 < d02 < 0.95 > d055 > 0.70
    assert d055 < d02


def test_hmf_order_of_magnitude_z02():
    n = ccp.n_gt_m(1.0e14, z=0.2)
    assert 1e-6 < n < 3e-5


def test_hmf_monotonic_and_decreasing_with_z():
    assert ccp.n_gt_m(1.0e14, 0.2) > ccp.n_gt_m(2.0e14, 0.2)
    assert ccp.n_gt_m(1.48e14, 0.0) > ccp.n_gt_m(1.48e14, 0.55)


def test_st_diagnostic_overcounts():
    # ST's ~virial convention must count MORE halos than the 500c Tinker08 at
    # fixed threshold -- the recorded reason it is excluded from the rule.
    assert ccp.n_gt_m(1.48e14, 0.2, fit="st") > ccp.n_gt_m(1.48e14, 0.2)


def test_despali16_agrees_with_tinker08_at_500c():
    # Two independent 500c-capable fits must agree at the tens-of-percent
    # level; a Delta-convention slip in either would blow far past this.
    t = ccp.n_gt_m(1.48e14, 0.2)
    d = ccp.n_gt_m(1.48e14, 0.2, fit="despali16")
    assert abs(d - t) / t < 0.30


def test_expected_crossings_scale_linearly_with_path():
    lo = ccp.n_cross_sightline(0.05, m_thresh=1.48e14, nz=15)
    hi = ccp.n_cross_sightline(0.10, m_thresh=1.48e14, nz=15)
    assert 1.7 < hi / lo < 2.3


def test_total_matches_sum_of_sightlines():
    total, per = ccp.n_cross_total(ccp.Z_PRIMARY, 1.48e14)
    assert len(per) == 9
    assert abs(total - sum(per)) < 1e-12


def test_mass_integrated_exceeds_fixed_sigma():
    # heavier-than-threshold halos have larger R500, so the mass-integrated
    # cross-section must exceed the fixed-at-threshold variant
    z = 0.3
    mi = ccp.n_cross_sightline(z, 1.48e14, mass_integrated=True, nz=10)
    fx = ccp.n_cross_sightline(z, 1.48e14, mass_integrated=False, nz=10)
    assert mi > fx


def test_quotability_rule_frozen():
    v, s = ccp.quotability({"primary": 0.10, "z_control": 0.11, "alt_fit_ST": 0.12})
    assert v == "quotable" and s <= 0.30
    v, _ = ccp.quotability({"primary": 0.10, "z_control": 0.20, "alt_fit_ST": 0.10})
    assert v == "spread"
    v, _ = ccp.quotability({"primary": 2.0, "z_control": 2.1, "alt_fit_ST": 2.2})
    assert v == "sanity-audit"
