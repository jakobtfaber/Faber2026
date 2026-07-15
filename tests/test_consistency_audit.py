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
            return text.replace("We present twelve fast radio bursts",
                                "We present eleven fast radio bursts", 1)
        return text

    monkeypatch.setattr(audit, "read_text", read_with_bad_abstract_count)
    findings = []
    audit.check_sample_counts(audit.tex_files(), findings)
    assert any("abstract sample count is eleven" in finding
               for finding in findings)


def test_all_compiled_figures_exist_and_are_manifested():
    findings = []
    audit.check_figures_and_provenance(audit.tex_files(), findings)
    assert findings == []


def test_unmanifested_compiled_figure_is_reported(monkeypatch):
    monkeypatch.setattr(audit, "manifest_entries", lambda: [])
    findings = []
    audit.check_figures_and_provenance(audit.tex_files(), findings)
    assert any("has no embedded figure row" in finding for finding in findings)


def test_count_parser_accepts_words_and_digits():
    assert audit.parse_count("twelve") == 12
    assert audit.parse_count("24") == 24
    assert audit.parse_count("many") is None


def test_figure_paths_follow_graphicspath_and_macro_conventions():
    assert audit.normalize_figure_path("figures/example.pdf") == \
        "figures/example.pdf"
    assert audit.normalize_figure_path("association_cards/card_#1.pdf") == \
        "figures/association_cards/card_*.pdf"
