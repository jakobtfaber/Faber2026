"""Focused regression tests for the F3 manuscript consistency audit."""
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_audit():
    spec = importlib.util.spec_from_file_location(
        "consistency_audit", ROOT / "scripts/consistency_audit.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


audit = _load_audit()


def test_committed_sample_counts_and_rosters_are_consistent():
    findings = []
    audit.check_sample_counts(audit.tex_files(), findings)
    assert findings == []


def test_sample_count_regression_is_reported(monkeypatch):
    original_read_text = audit.read_text

    def read_with_bad_abstract_count(path):
        text = original_read_text(path)
        if path == audit.ROOT / "main.tex":
            replacements = (
                ("Here we analyze twelve FRBs",
                 "Here we analyze eleven FRBs"),
                ("We present twelve fast radio bursts",
                 "We present eleven fast radio bursts"),
                ("All twelve pass timing", "All eleven pass timing"),
                ("twelve events", "eleven events"),
                ("all twelve sightlines", "all eleven sightlines"),
            )
            for before, after in replacements:
                text = text.replace(before, after, 1)
        return text

    monkeypatch.setattr(audit, "read_text", read_with_bad_abstract_count)
    findings = []
    audit.check_sample_counts(audit.tex_files(), findings)
    for description in ("abstract sample", "abstract association census",
                        "abstract DM census", "abstract foreground census"):
        assert any(f"{description} count is eleven" in finding
                   for finding in findings)


def test_all_compiled_figures_exist_and_are_manifested():
    findings = []
    audit.check_figures_and_provenance(audit.tex_files(), findings)
    assert findings == []


def test_unmanifested_compiled_figure_is_reported(monkeypatch):
    monkeypatch.setattr(audit, "manifest_entries", lambda kind=None: [])
    findings = []
    audit.check_figures_and_provenance(audit.tex_files(), findings)
    assert any("has no embedded figure row" in finding for finding in findings)


def test_incomplete_wildcard_figure_family_is_reported(monkeypatch):
    monkeypatch.setattr(
        audit, "figure_assets",
        lambda pattern: ([Path(f"card-{i}.pdf") for i in range(11)]
                         if "*" in pattern else [Path(pattern)]))
    findings = []
    audit.check_figures_and_provenance(audit.tex_files(), findings)
    assert any("has 11 assets; expected 12" in finding for finding in findings)


def test_unmanifested_generated_table_is_reported(monkeypatch):
    real_entries = audit.manifest_entries
    monkeypatch.setattr(
        audit, "manifest_entries",
        lambda kind=None: [] if kind == "table" else real_entries(kind))
    findings = []
    audit.check_inputs_and_provenance(audit.tex_files(), findings)
    assert any("generated table has no embedded table row" in finding
               for finding in findings)


def test_count_parser_accepts_words_and_digits():
    assert audit.parse_count("twelve") == 12
    assert audit.parse_count("24") == 24
    assert audit.parse_count("many") is None


def test_figure_paths_follow_graphicspath_and_macro_conventions():
    assert audit.normalize_figure_path("figures/example.pdf") == \
        "figures/example.pdf"
    assert audit.normalize_figure_path("association_cards/card_#1.pdf") == \
        "figures/association_cards/card_*.pdf"
