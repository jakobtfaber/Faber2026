from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent.parent
ROSTER = ROOT / "figure_review" / "definitions" / "owner-morphology.yaml"
TRIPTYCH_MANIFEST = ROOT / "scripts" / "jointmodel_triptych_manifest.yaml"


def test_owner_morphology_roster_is_complete_and_matches_sample():
    roster = yaml.safe_load(ROSTER.read_text())
    triptych = yaml.safe_load(TRIPTYCH_MANIFEST.read_text())
    owner_rows = roster["bursts"]
    expected = [(row["nick"].lower(), row["tns"]) for row in triptych["bursts"]]
    observed = [(row["nick"].lower(), row["tns"]) for row in owner_rows]
    assert observed == expected
    assert len(observed) == len(set(observed)) == 12


def test_owner_morphology_counts_and_uncertainty_are_explicit():
    roster = yaml.safe_load(ROSTER.read_text())
    rows = {row["nick"].lower(): row for row in roster["bursts"]}
    assert {(row["C"], row["D"]) for row in rows.values()} <= {
        (1, 1),
        (2, 2),
        (2, 4),
        (3, 4),
        (5, 1),
    }
    assert {nick for nick, row in rows.items() if row["confidence"] == "uncertain"} == {
        "phineas",
        "hamilton",
    }
    assert all(row["confidence"] in {"confirmed", "uncertain"} for row in rows.values())


def test_review_figure_is_data_only_and_has_shared_time_support():
    roster = yaml.safe_load(ROSTER.read_text())
    figure = roster["review_figure"]
    assert figure["kind"] == "data-only dynamic spectra and band-summed time profiles"
    assert figure["shared_time_support"] is True
    assert len(figure["output_sha256"]) == 64


def test_known_fit_mismatches_and_rerun_caveats_are_not_lost():
    rows = {
        row["nick"].lower(): row for row in yaml.safe_load(ROSTER.read_text())["bursts"]
    }
    assert (rows["zach"]["C"], rows["zach"]["D"]) == (2, 4)
    assert (rows["johndoeii"]["C"], rows["johndoeii"]["D"]) == (2, 2)
    assert "C1D2" in rows["johndoeii"]["note"]
    assert "residual adequacy" in rows["oran"]["note"]
