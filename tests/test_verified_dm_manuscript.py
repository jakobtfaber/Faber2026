"""Cross-artifact parity checks for the adopted phase-coherence DMs."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import render_budget_table  # noqa: E402
import render_dm_measurements_table  # noqa: E402


def _catalog() -> list[dict[str, str]]:
    path = ROOT / "analysis" / "dm-joint-phase-v2" / "manuscript_dm_catalog.csv"
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def test_catalog_matches_full_fit_results_and_uniform_adoption():
    rows = _catalog()
    fits = {
        row["burst"].lower(): row
        for row in json.loads(
            (ROOT / "analysis" / "dm-joint-phase-v2" / "results" / "fits.json").read_text()
        )
    }
    assert len(rows) == len(fits) == 12
    for row in rows:
        fit = fits[row["nick"].lower()]
        assert row["adoption"] == "chime_primary"
        assert np.isclose(float(row["chime_dm"]), fit["chime"]["dm"], atol=5e-7)
        assert np.isclose(float(row["dsa_dm"]), fit["dsa"]["dm"], atol=5e-7)
        assert np.isclose(float(row["adopted_dm"]), fit["chime"]["dm"], atol=5e-7)


def test_dm_measurement_table_matches_catalog_rounding():
    tex = (ROOT / "dm_measurements_table.tex").read_text()
    assert tex == render_dm_measurements_table.render()
    for row in _catalog():
        expected = (
            f'{row["tns"]} & '
            f'${float(row["chime_dm"]):.4f}\\pm{float(row["chime_sigma"]):.4f}$ & '
            f'${float(row["dsa_dm"]):.4f}\\pm{float(row["dsa_sigma"]):.4f}$ & '
            f'${float(row["chime_minus_dsa"]):+.4f}$ & '
            f'${float(row["adopted_dm"]):.4f}\\pm{float(row["adopted_sigma"]):.4f}$'
        )
        assert expected in tex


def test_budget_table_is_rendered_from_verified_products():
    assert (ROOT / "budget_table.tex").read_text() == render_budget_table.render()
