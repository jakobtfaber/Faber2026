"""Fail-closed checks for the post-PL-PBF joint-fit figure gate."""

import csv
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_audit():
    spec = importlib.util.spec_from_file_location(
        "consistency_audit", ROOT / "scripts/consistency_audit.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _compiled_tex() -> str:
    """Return the comment-stripped TeX graph reachable from main.tex."""
    audit = _load_audit()
    return "\n".join(
        audit.strip_comments(path.read_text()) for path in audit.tex_files()
    )


def _manifest_rows():
    with (ROOT / "repro_manifest.csv").open(newline="") as handle:
        return {row["output"]: row for row in csv.DictReader(handle)}


def test_pre_pl_pbf_joint_fit_figures_are_not_compiled():
    tex = _compiled_tex()
    assert "sections/codetection_triptychs.tex" not in tex
    assert "sections/jointmodel_pairs.tex" not in tex
    assert "fig:codetection-triptych-whitney" not in tex
    assert "figures/codetection_triptych/" not in tex
    assert "figures/jointmodel_pair/" not in tex


def test_observations_names_full_refit_dump_and_review_gate():
    text = (ROOT / "sections/observations.tex").read_text()
    assert "complete post-PL-PBF production refit" in text
    assert "matching model dumps" in text
    assert "pass author figure review" in text
    assert "pending author figure review" not in text


def test_historical_sources_are_retained_for_provenance():
    assert (ROOT / "sections/codetection_triptychs.tex").is_file()
    assert (ROOT / "sections/jointmodel_pairs.tex").is_file()


def test_suppressed_families_are_unembedded_and_pin_the_blocker():
    rows = _manifest_rows()
    for output in (
        "figures/codetection_triptych/*_triptych.pdf",
        "figures/jointmodel_pair/*_jointmodel_pair.pdf",
    ):
        row = rows[output]
        assert row["embedded_in_manuscript"] == "no"
        assert row["clone_verified"] == "superseded_pre_pl_pbf"
        assert "17d9d266" in row["notes"]
        assert "post-PL-PBF" in row["notes"]
