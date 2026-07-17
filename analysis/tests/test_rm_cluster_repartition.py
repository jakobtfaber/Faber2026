"""Correctness tests for the Thread 1 RM re-partition record (Kulkarni Thread 1).

Run: pytest tests/test_rm_cluster_repartition.py

Predeclared record: docs/rse/specs/plan-rm-cluster-bfield-repartition-2026-07-17.md.
Nothing here is a regression pin on the script's own output; every expected value
is an independent reference:

1. Pins ......... the PINNED dict must match the machine-readable sources it
                  claims (registry row, budget CSV) -- the S1 lesson: thresholds
                  from pipeline outputs, never prose. A mismatch is a blocking
                  error, not a tolerance.
2. Algebra ...... frame conversions re-derived: RM_cl(obs)/B = 0.812*DM_obs/(1+z_cl),
                  sigma_RM(obs) = 15/(1+z_host)^2; the plan's table values.
3. Rule ......... the frozen material/null/marginal thresholds are fixed
                  multiples of sigma_RM(obs); classify() must implement exactly
                  those.
4. Corner ....... the zero-cluster MC corner must reproduce the companion's
                  published row (RM_host=-756+/-15, B_host=-2.0) -- by closure
                  construction for the median, so this guards frames and signs.
5. Physics ...... the cluster term is odd in B_cl and its magnitude grows with
                  |B_cl|; the cluster-corrected DM_host is strictly below the
                  as-published one.
"""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import rm_cluster_repartition as rcr  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "pipeline/galaxies/foreground/data/intervening_census_registry.csv"


def test_registry_row_matches_pins():
    # Nine cluster rows exist for this sightline (excluded b>R500 systems and
    # the near-miss); exactly one is budget-eligible -- that row carries the pins.
    rows = [
        r
        for r in csv.DictReader(REGISTRY.open())
        if r["type"] == "cluster"
        and r["tns"] == "FRB 20230307A"
        and r["budget_eligible"] == "True"
    ]
    assert len(rows) == 1
    assert rows[0]["obj"].startswith("J115120.4+714435")
    r = rows[0]
    assert float(r["m500_1e14msun"]) == rcr.PINNED["m500_1e14"] == 1.48
    assert float(r["impact_kpc"]) == rcr.PINNED["b_kpc"] == 603.6
    assert float(r["best_z"]) == rcr.PINNED["z_cl"] == 0.200
    assert float(r["host_z_spec"]) == rcr.PINNED["z_host"] == 0.271
    assert float(r["r500_mpc"]) == rcr.PINNED["r500_mpc"] == 0.729
    assert float(r["b_over_r500"]) == rcr.PINNED["b_over_r500"] == 0.83


def test_budget_csv_bracket_matches_pins():
    rows = {
        row[0]: row[1:]
        for row in csv.reader((ROOT / "scripts/dm_budget_uncertainty.csv").open())
        if row
    }
    assert tuple(float(x) for x in rows["cluster_95CI_lo_hi"]) == rcr.PINNED["dm_cl_95ci"]
    assert (
        tuple(float(x) for x in rows["cluster_beta_model_p16_p50_p84"])
        == rcr.PINNED["dm_cl_beta_p16_p50_p84"]
    )


def test_frame_algebra():
    # RM_cl(obs)/B = 0.812 * DM_obs * (1+z_cl) / (1+z_cl)^2 = 0.812*DM_obs/1.2
    assert math.isclose(rcr.rm_per_microgauss_obs(184.0), 124.5, rel_tol=5e-3)
    assert math.isclose(rcr.rm_per_microgauss_obs(84.0), 56.8, rel_tol=5e-3)
    assert math.isclose(rcr.rm_per_microgauss_obs(328.0), 222.0, rel_tol=5e-3)
    # rederive from first principles rather than the module's own constant
    dm = 200.0
    expected = 0.812 * dm * (1 + 0.200) / (1 + 0.200) ** 2
    assert math.isclose(rcr.rm_per_microgauss_obs(dm), expected, rel_tol=1e-12)


def test_negligibility_fields():
    # sigma_RM_host(obs) = 15/(1+0.271)^2 = 9.29 rad/m^2 (plan table)
    assert math.isclose(rcr.SIGMA_RM_OBS, 9.29, abs_tol=0.01)
    assert math.isclose(rcr.b_negligibility(184.0), 0.075, abs_tol=0.002)
    assert math.isclose(rcr.b_negligibility(84.0), 0.163, abs_tol=0.003)
    assert math.isclose(rcr.b_negligibility(328.0), 0.042, abs_tol=0.002)


def test_classification_frozen_thresholds():
    assert rcr.classify(rm_lit=25.0) == "material"
    assert rcr.classify(rm_lit=5.0) == "null"
    assert rcr.classify(rm_lit=12.0) == "marginal"
    # boundary semantics exactly as frozen: material at >= 2 sigma, null strictly below 1 sigma
    assert rcr.classify(2.0 * rcr.SIGMA_RM_OBS) == "material"
    assert rcr.classify(rcr.SIGMA_RM_OBS) == "marginal"


def test_literature_admissions_meet_criteria():
    for s in rcr.LITERATURE["admitted"]:
        assert s["n_sightlines"] >= 10, s["study"]
        assert s["sigma_rm_local"] > 0
    assert len(rcr.LITERATURE["admitted"]) >= 3
    for s in rcr.LITERATURE["rejected"]:
        assert s["reason"]


def test_rm_lit_dilution():
    med = float(np.median([s["sigma_rm_local"] for s in rcr.LITERATURE["admitted"]]))
    assert math.isclose(rcr.rm_lit_obs(), med / 1.44, rel_tol=1e-12)


def test_closure_substitution_recovers_their_error_budget():
    # By construction sqrt(RM_MW_SIGMA^2 + 6^2 + 0.09^2) must equal sigma_RM(obs):
    # the substitution redistributes, never invents, variance.
    total = math.sqrt(rcr.RM_MW_SIGMA**2 + 6.0**2 + 0.09**2)
    assert math.isclose(total, rcr.SIGMA_RM_OBS, rel_tol=1e-9)
    # -473.49 + 756/(1.271)^2 = -5.506
    assert math.isclose(rcr.RM_MW_CLOSURE, -5.506, abs_tol=0.01)


@pytest.fixture(scope="module")
def mc():
    return rcr.repartition_mc(b_cl_grid=(0.0, 0.25, -0.25), n=6000, pool_size=1500)


def test_zero_cluster_corner_reproduces_companion(mc):
    row = mc[0.0]
    assert abs(row["rm_host_p50"] - (-756.0)) < 30.0
    assert abs(row["b_host_p50"] - (-2.0)) < 0.3


def test_cluster_term_odd_and_monotonic(mc):
    # RM_obs<0 and a positive (toward-us) coherent field makes RM_cl>0, pushing
    # RM_host MORE negative; the sign convention must be odd in B_cl.
    assert mc[0.25]["rm_host_p50"] < mc[0.0]["rm_host_p50"] < mc[-0.25]["rm_host_p50"]
    up = mc[0.25]["rm_cl_obs_p16_p50_p84"][1]
    dn = mc[-0.25]["rm_cl_obs_p16_p50_p84"][1]
    assert up > 0 > dn
    assert math.isclose(up, -dn, rel_tol=0.1)


def test_cluster_corrected_dm_host_lowers_field_magnitude(mc):
    # Removing the cluster column from DM_host (at fixed RM_host) must raise
    # |B_host| (same RM over less DM): corrected p50 more negative than published.
    row = mc[0.0]
    assert row["b_host_corr_p16_p50_p84"][1] < row["b_host_pub_p16_p50_p84"][1] < 0


def test_mc_deterministic(mc):
    again = rcr.repartition_mc(b_cl_grid=(0.0, 0.25, -0.25), n=6000, pool_size=1500)
    assert again[0.25]["rm_host_p16_p50_p84"] == mc[0.25]["rm_host_p16_p50_p84"]
