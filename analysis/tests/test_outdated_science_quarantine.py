"""Guards for obsolete manuscript science moved into quarantine."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUARANTINE = ROOT / "quarantine" / "2026-07-17-outdated-science"


def test_obsolete_tables_and_full_ledger_are_quarantined():
    moved = {
        ROOT / "joint_fit_provisional_table.tex":
            QUARANTINE / "joint_fit_provisional_table.tex",
        ROOT / "dsa_scint_provisional_table.tex":
            QUARANTINE / "dsa_scint_provisional_table.tex",
        ROOT / "foreground_propagation_provisional_table.tex":
            QUARANTINE / "foreground_propagation_provisional_table.tex",
    }
    for active, quarantined in moved.items():
        assert quarantined.is_file(), quarantined
        assert not active.exists(), active
    assert (QUARANTINE / "analysis/provisional_propagation/results.json").is_file()


def test_compiled_tex_has_no_quarantined_labels_or_inputs():
    compiled = "\n".join(
        (ROOT / path).read_text()
        for path in ("sections/results.tex", "sections/discussion.tex")
    )
    for token in (
        "tab:joint-fit-provisional",
        "tab:dsa-scint-provisional",
        "tab:foreground-propagation-provisional",
        "joint_fit_provisional_table",
        "dsa_scint_provisional_table",
        "foreground_propagation_provisional_table",
        "approximately 22\\%",
        "factor of about 11",
    ):
        assert token not in compiled
    assert "\\input{twoscreen_provisional_table}" in compiled


def test_active_propagation_ledger_is_fail_closed_only():
    active = json.loads(
        (ROOT / "analysis/provisional_propagation/results.json").read_text()
    )
    assert active["screen_analysis_status"] == "PENDING_ALPHA4_CONSISTENCY_REFITS"
    assert "foreground_alignment_rows" not in active
    assert len(active["screen_rows"]) == 7
    assert all(not row["products"] for row in active["screen_rows"])


def test_generator_cannot_recreate_live_obsolete_tables():
    source = (ROOT / "scripts/build_provisional_propagation_tables.py").read_text()
    assert "2026-07-17-outdated-science" in source
    assert 'table(ROOT / "joint_fit_provisional_table.tex"' not in source
    assert 'table(ROOT / "dsa_scint_provisional_table.tex"' not in source
    assert 'table(ROOT / "foreground_propagation_provisional_table.tex"' not in source


def test_quarantine_has_review_index():
    index = (QUARANTINE / "README.md").read_text()
    assert "Do not cite" in index
    assert "Original path" in index
