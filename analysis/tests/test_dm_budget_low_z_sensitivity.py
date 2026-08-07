"""Correctness and decision guards for the low-redshift sensitivity check."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import dm_budget_low_z_sensitivity as sensitivity  # noqa: E402


def test_catalog_interpolation_is_per_ray_and_linear():
    redshifts = np.array([0.01, 0.02, 0.03])
    dm_values = np.array([[1.0, 10.0], [3.0, 14.0], [9.0, 22.0]])
    actual = sensitivity.interpolate_catalog_rays(redshifts, dm_values, 0.015)
    assert actual == pytest.approx([2.0, 12.0])


def test_empirical_pdf_preserves_probability_and_median():
    samples = np.array([1.0, 1.0, 2.0, 3.0, 3.0])
    pdf = sensitivity.empirical_pdf(samples, dx=0.1)
    assert pdf.density.sum() * pdf.dx == pytest.approx(1.0)
    assert sensitivity.dbu.pdf_quantile(pdf, 0.5) == pytest.approx(2.0, abs=0.1)


def test_committed_benchmark_preserves_low_z_headline():
    """All tested models keep positive medians and P(host < 0) below 0.1."""
    report = json.loads(
        (ROOT / "scripts" / "dm_budget_low_z_sensitivity.json").read_text()
    )
    assert report["inputs"]["pyhesdm"]["sha256"] == (
        "3dd0293f822a60ee17530091f3f08227c17e5230c870b68c3d5fb65dc17eade0"
    )
    assert report["inputs"]["konietzka"]["sha256"] == (
        "fab9bb7dc0babe1c8577c4b6c500d756fc21c0f5049057350976ce977d928e44"
    )
    assert {row["burst"] for row in report["sightlines"]} == {
        "FRB 20220207C",
        "FRB 20240203A",
    }
    for row in report["sightlines"]:
        assert abs(row["pyhesdm"]["galactic_b_deg"]) > 10.0
        assert abs(row["host_median_shift"]["pyhesdm_minus_current"]) < 10.0
        for result in row["host_dm_observer_frame"].values():
            assert result["p50"] > 0.0
            assert result["p_host_negative"] < 0.1
