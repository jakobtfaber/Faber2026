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


def test_committed_toa_convention_respects_model_correction_gate():
    findings = []
    audit.check_toa_correction_gate(findings)
    assert findings == []


def test_committed_foreground_census_wording_matches_frozen_registry():
    findings = []
    audit.check_foreground_census_wording(findings)
    assert findings == []


def test_unvalidated_toa_cannot_replace_peak_offset(monkeypatch):
    original_read_text = audit.read_text

    def read_with_promoted_unvalidated_model(path):
        text = original_read_text(path)
        if path == audit.ROOT / "pipeline/crossmatching/toa_crossmatch_results.json":
            import json

            rows = json.loads(text)
            row = next(iter(rows.values()))
            row["measured_offset_ms"] = row["model_corrected_offset_ms"]
            return json.dumps(rows)
        return text

    monkeypatch.setattr(audit, "read_text", read_with_promoted_unvalidated_model)
    findings = []
    audit.check_toa_correction_gate(findings)
    assert any(
        "measured_offset_ms does not preserve the observed-peak offset" in finding
        for finding in findings
    )


def test_unvalidated_toa_model_promotion_wording_is_reported(monkeypatch):
    original_read_text = audit.read_text

    def read_with_promotion(path):
        text = original_read_text(path)
        if path == audit.ROOT / "sections/toa.tex":
            return text + "\nWe adopt the model TOA on each band.\n"
        return text

    monkeypatch.setattr(audit, "read_text", read_with_promotion)
    findings = []
    audit.check_toa_correction_gate(findings)
    assert any("unconditional model-TOA adoption" in finding for finding in findings)


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


def test_pipeline_figure_paths_remain_repo_relative():
    assert audit.normalize_figure_path("pipeline/results/diagnostic.png") == \
        "pipeline/results/diagnostic.png"


def test_compiled_generated_tables_have_provenance():
    findings = []
    audit.check_inputs_and_provenance(audit.tex_files(), findings)
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
