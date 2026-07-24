from __future__ import annotations

import subprocess
import sys
import tomllib
import os
from copy import deepcopy
from pathlib import Path

import pytest

from scripts.generate_results_coverage import generate
from scripts.render_results_registry import (
    CANONICAL_RESULT_IDS,
    CANONICAL_INPUT_EXCEPTION_NAMES,
    EXPECTED_CLAIM_OWNER_FIELDS,
    EXPECTED_REGISTRY_FIELDS,
    EXPECTED_SCHEMA_VERSION,
    REQUIRED_FIELDS,
    compiled_artifacts,
    has_canonical_input_exception_inventory,
    has_canonical_result_inventory,
    has_exact_result_schema,
    numeric_claims,
    validate_claim_owner_ledger,
    validate_registry,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs/rse/control/results-registry.toml"
CLAIM_OWNERS = ROOT / "docs/rse/control/results-registry-claim-owners.toml"
RESULTS = ROOT / "RESULTS.md"
RENDERER = ROOT / "scripts/render_results_registry.py"
MAKEFILE = ROOT / "Makefile"


def _registry() -> dict:
    return tomllib.loads(REGISTRY.read_text())


def test_all_results_have_explicit_provenance_state() -> None:
    rows = _registry()["result"]
    ids = [row["id"] for row in rows]
    assert len(ids) == len(set(ids))

    for row in rows:
        assert row["trust"] in {"trusted", "pending", "revoked"}, row["id"]
        assert row["provenance_state"] in {"complete", "pending"}, row["id"]
        gaps = row.get("provenance_gaps", [])
        if row["provenance_state"] == "pending":
            assert gaps and all(gap.strip() for gap in gaps), row["id"]
        else:
            assert not gaps, row["id"]
            for field in ("producing_script", "pipeline_pin", "inputs", "artifact"):
                assert row[field], (row["id"], field)


def _manuscript_root() -> Path:
    root = Path(__import__("os").environ.get("FABER2026_ROOT", ROOT.parent))
    if not (root / "main.tex").is_file():
        pytest.skip("set FABER2026_ROOT when testing a standalone analysis worktree")
    return root


def test_registry_covers_compiled_manuscript() -> None:
    assert validate_registry(_registry(), _manuscript_root()) == []


def test_budget_cluster_column_is_demoted_to_current_probabilistic_values() -> None:
    row = next(
        item for item in _registry()["result"] if item["id"] == "budget.cluster_column"
    )
    assert row["value"] == "DM_int=255 (+67/-52); host DM p50=62"
    assert row["trust"] == "pending"
    assert row["provenance_state"] == "pending"
    assert row["pipeline_pin"] == ""
    assert "252" not in row["value"]


def test_toa_claims_have_semantic_owners() -> None:
    source = next(
        item
        for item in _registry()["prose_source"]
        if item["source"] == "sections/toa.tex"
    )
    owners = {claim["line"]: claim["owner_result_id"] for claim in source["claims"]}
    assert owners[22] == "association.sample_table"  # dispersion constant
    assert owners[150] == "association.pcc_sum"  # P_cc equation
    assert owners[240] == "association.toa_offset_figure"  # residual diagnostic
    assert owners[322] == "association.pcc_sum"  # post-figure P_cc claim


def test_association_cards_and_pending_toa_have_disjoint_scope() -> None:
    rows = {row["id"]: row for row in _registry()["result"]}
    cards = rows["association.cards_figures"]
    toa = rows["association.toa_offset_figure"]
    assert (
        cards["description"]
        == "Twelve per-burst association cards (fig:assoc-cards-grid)"
    )
    assert cards["consumed_by"] == ["sections/appendix.tex"]
    assert toa["trust"] == "pending"
    assert set(cards["consumed_by"]).isdisjoint(toa["consumed_by"])


def test_association_cards_cannot_claim_pending_toa_consumer() -> None:
    registry = deepcopy(_registry())
    cards = next(
        row for row in registry["result"] if row["id"] == "association.cards_figures"
    )
    cards["consumed_by"].append("sections/toa.tex")
    errors = validate_registry(registry, _manuscript_root())
    assert any("association cards consumers exceed" in error for error in errors)
    assert any("pending TOA figure consumers overlap" in error for error in errors)


def test_association_cards_cannot_own_pending_toa_artifact() -> None:
    registry = deepcopy(_registry())
    record = next(
        item
        for item in registry["artifact_coverage"]
        if item["paths"] == ["figures/toa_offset_decomposition.pdf"]
    )
    record["result_id"] = "association.cards_figures"
    errors = validate_registry(registry, _manuscript_root())
    assert "association cards must own exactly the twelve card artifacts" in errors
    assert "pending TOA row must solely own the TOA decomposition artifact" in errors


def test_unrelated_known_claim_owner_fails_semantic_review() -> None:
    registry = deepcopy(_registry())
    source = next(
        item
        for item in registry["prose_source"]
        if item["source"] == "sections/toa.tex"
    )
    claim = next(item for item in source["claims"] if item["line"] == 150)
    claim["owner_result_id"] = "energies.burst_energies_table"
    errors = validate_registry(registry, _manuscript_root())
    assert "claim ownership differs from independent semantic review" in errors


def _claim_owners() -> dict:
    return tomllib.loads(CLAIM_OWNERS.read_text())


def test_claim_owner_ledger_has_exact_top_level_schema() -> None:
    reviewed = _claim_owners()
    assert set(reviewed) == EXPECTED_CLAIM_OWNER_FIELDS
    reviewed["unexpected"] = []
    errors, _ = validate_claim_owner_ledger(reviewed, set(CANONICAL_RESULT_IDS))
    assert "claim-owner ledger has incorrect top-level fields" in errors


def test_claim_owner_ledger_schema_version_is_exact() -> None:
    reviewed = _claim_owners()
    reviewed["schema_version"] += 1
    errors, _ = validate_claim_owner_ledger(reviewed, set(CANONICAL_RESULT_IDS))
    assert "claim-owner ledger has unsupported schema_version" in errors


def test_duplicate_claim_owner_source_fails_before_lookup_collapse() -> None:
    reviewed = _claim_owners()
    reviewed["source"].append(deepcopy(reviewed["source"][0]))
    errors, _ = validate_claim_owner_ledger(reviewed, set(CANONICAL_RESULT_IDS))
    assert any("duplicate sources" in error for error in errors)


def test_duplicate_claim_owner_claim_fails_before_lookup_collapse() -> None:
    reviewed = _claim_owners()
    reviewed["source"][0]["claims"].append(deepcopy(reviewed["source"][0]["claims"][0]))
    errors, _ = validate_claim_owner_ledger(reviewed, set(CANONICAL_RESULT_IDS))
    assert any("duplicate claim" in error for error in errors)


def test_claim_owner_records_enforce_exact_keys_and_types() -> None:
    reviewed = _claim_owners()
    source = reviewed["source"][0]
    source["unexpected"] = "value"
    claim = source["claims"][0]
    claim["unexpected"] = "value"
    claim["occurrence"] = True
    errors, _ = validate_claim_owner_ledger(reviewed, set(CANONICAL_RESULT_IDS))
    assert any("source 0 has incorrect fields" in error for error in errors)
    assert any("claim 0 has incorrect fields" in error for error in errors)
    assert any("occurrence must be a positive integer" in error for error in errors)


def test_coverage_generator_preserves_reviewed_assignments_byte_for_byte() -> None:
    registry = _registry()
    regenerated = tomllib.loads(generate(_manuscript_root(), registry))
    assert regenerated["prose_source"] == registry["prose_source"]
    assert regenerated["artifact_coverage"] == registry["artifact_coverage"]


def test_new_numeric_claim_fails_closed(tmp_path: Path) -> None:
    main = tmp_path / "main.tex"
    main.write_text("The reviewed result is 1.25.\n")
    claim = numeric_claims(main)[0]
    registry = {
        "prose_source": [
            {
                "source": "main.tex",
                "claims": [
                    {
                        **claim,
                        "owner_result_id": "association.sample_roster",
                    }
                ],
            }
        ],
        "artifact_coverage": [],
    }
    main.write_text("The reviewed result is 1.25.\nA new result is 123.456.\n")
    regenerated = tomllib.loads(generate(tmp_path, registry))
    claims = regenerated["prose_source"][0]["claims"]
    assert claims[0]["owner_result_id"] == "association.sample_roster"
    assert claims[1]["owner_result_id"] == "__SELECT_OWNER__"

    full_registry = deepcopy(_registry())
    full_registry["prose_source"] = regenerated["prose_source"]
    full_registry["artifact_coverage"] = []
    errors = validate_registry(full_registry, tmp_path)
    assert any("claim ownership is unresolved" in error for error in errors)


def test_unregistered_figure_fails_closed(tmp_path: Path) -> None:
    (tmp_path / "figures").mkdir()
    (tmp_path / "figures/new.pdf").write_bytes(b"placeholder")
    (tmp_path / "main.tex").write_text("\\includegraphics{figures/new.pdf}\n")
    registry = deepcopy(_registry())
    registry["prose_source"] = [{"source": "main.tex", "claims": []}]
    registry["artifact_coverage"] = []
    errors = validate_registry(registry, tmp_path)
    assert "figures/new.pdf: expected exactly one registry owner, found 0" in errors


def test_include_nested_table_and_figure_wrapper_are_discovered(tmp_path: Path) -> None:
    (tmp_path / "sections").mkdir()
    (tmp_path / "tables").mkdir()
    (tmp_path / "figures").mkdir()
    (tmp_path / "main.tex").write_text("\\include{sections/body}\n")
    (tmp_path / "sections/body.tex").write_text(
        "\\input{../tables/generated}\n\\input{figure_wrapper}\n"
    )
    (tmp_path / "tables/generated.tex").write_text(
        "\\begin{table}\nvalue 1 \\\\\n\\end{table}\n"
    )
    (tmp_path / "sections/figure_wrapper.tex").write_text(
        "\\includegraphics{figures/wrapped.pdf}\n"
    )
    (tmp_path / "figures/wrapped.pdf").write_bytes(b"pdf")
    tables, figures = compiled_artifacts(tmp_path)
    assert tables == {"tables/generated.tex"}
    assert figures == {"figures/wrapped.pdf"}


def test_fresh_fls_adds_recorder_only_figure_wrapper(tmp_path: Path) -> None:
    (tmp_path / "wrappers").mkdir()
    (tmp_path / "figures").mkdir()
    (tmp_path / "main.tex").write_text("No dependencies.\n")
    (tmp_path / "wrappers/only-in-recorder.tex").write_text(
        "\\includegraphics{figures/recorder.pdf}\n"
    )
    (tmp_path / "figures/recorder.pdf").write_bytes(b"pdf")
    recorder = tmp_path / "main.fls"
    recorder.write_text("INPUT main.tex\nINPUT wrappers/only-in-recorder.tex\n")
    recorder.touch()
    tables, figures = compiled_artifacts(tmp_path)
    assert tables == set()
    assert figures == {"figures/recorder.pdf"}


def test_fls_is_rejected_when_recorder_only_wrapper_is_newer(tmp_path: Path) -> None:
    (tmp_path / "wrappers").mkdir()
    (tmp_path / "figures").mkdir()
    (tmp_path / "main.tex").write_text("No dependencies.\n")
    wrapper = tmp_path / "wrappers/newer-than-recorder.tex"
    wrapper.write_text("\\includegraphics{figures/stale.pdf}\n")
    (tmp_path / "figures/stale.pdf").write_bytes(b"pdf")
    recorder = tmp_path / "main.fls"
    recorder.write_text("INPUT main.tex\nINPUT wrappers/newer-than-recorder.tex\n")
    newer = recorder.stat().st_mtime_ns + 1_000_000_000
    os.utime(wrapper, ns=(newer, newer))
    tables, figures = compiled_artifacts(tmp_path)
    assert tables == set()
    assert figures == set()


def test_complete_provenance_rejects_inferred_pin_and_missing_input() -> None:
    registry = deepcopy(_registry())
    row = next(
        item for item in registry["result"] if item["id"] == "association.sample_table"
    )
    row["pipeline_pin"] = "9175b92 (inferred; confirm receipt)"
    row["inputs"] = ["pipeline/definitely-missing.json"]
    errors = validate_registry(registry, _manuscript_root())
    assert any(
        "complete provenance contains unresolved wording" in error for error in errors
    )
    assert any("input path does not exist" in error for error in errors)


def test_complete_rows_use_full_repository_specific_commits() -> None:
    complete = [
        row for row in _registry()["result"] if row["provenance_state"] == "complete"
    ]
    assert complete
    for row in complete:
        assert len(row["pipeline_pin"]) == 40
        assert row["provenance_refs"]
        assert all(len(ref["commit"]) == 40 for ref in row["provenance_refs"])


def test_analysis_producer_cannot_be_declared_as_pipeline() -> None:
    registry = deepcopy(_registry())
    row = next(
        item for item in registry["result"] if item["id"] == "association.sample_table"
    )
    producer = next(ref for ref in row["provenance_refs"] if ref["role"] == "producer")
    producer["repository"] = "pipeline"
    producer["commit"] = row["pipeline_pin"]
    errors = validate_registry(registry, _manuscript_root())
    assert any("must declare repository analysis" in error for error in errors)


def _minimal_registry(tmp_path: Path) -> tuple[dict, dict]:
    (tmp_path / "main.tex").write_text("")
    row = deepcopy(
        next(item for item in _registry()["result"] if item["section"] == "§0")
    )
    row["pipeline_pin"] = ""
    return {
        "result": [row],
        "prose_source": [{"source": "main.tex", "claims": []}],
        "artifact_coverage": [],
    }, row


@pytest.mark.parametrize("field", sorted(REQUIRED_FIELDS))
def test_every_result_field_is_required(tmp_path: Path, field: str) -> None:
    registry, row = _minimal_registry(tmp_path)
    del row[field]
    errors = validate_registry(registry, tmp_path)
    assert any(f"missing required field {field}" in error for error in errors)


@pytest.mark.parametrize("removed_id", CANONICAL_RESULT_IDS)
def test_deleting_any_canonical_row_fails_inventory(removed_id: str) -> None:
    rows = [row for row in _registry()["result"] if row["id"] != removed_id]
    assert not has_canonical_result_inventory(rows)


def test_adding_unknown_row_fails_inventory() -> None:
    rows = deepcopy(_registry()["result"])
    extra = deepcopy(rows[-1])
    extra["id"] = "unknown.extra"
    rows.append(extra)
    assert not has_canonical_result_inventory(rows)


def test_unknown_row_key_fails_validation() -> None:
    registry = deepcopy(_registry())
    registry["result"][0]["unexpected"] = "value"
    assert not has_exact_result_schema(registry["result"][0])
    errors = validate_registry(registry, _manuscript_root())
    assert any("unknown fields: unexpected" in error for error in errors)


def test_registry_top_level_fields_are_exact() -> None:
    registry = deepcopy(_registry())
    assert set(registry) == set(EXPECTED_REGISTRY_FIELDS)
    registry["unexpected"] = []
    errors = validate_registry(registry, _manuscript_root())
    assert "registry has incorrect top-level fields" in errors


def test_registry_missing_top_level_field_fails() -> None:
    registry = deepcopy(_registry())
    del registry["updated"]
    errors = validate_registry(registry, _manuscript_root())
    assert "registry has incorrect top-level fields" in errors
    assert "registry missing top-level field updated" in errors


def test_registry_schema_version_is_exact() -> None:
    registry = deepcopy(_registry())
    assert registry["schema_version"] == EXPECTED_SCHEMA_VERSION
    registry["schema_version"] += 1
    errors = validate_registry(registry, _manuscript_root())
    assert f"registry schema_version must be {EXPECTED_SCHEMA_VERSION}" in errors


def test_duplicate_registry_prose_source_fails_before_lookup_collapse() -> None:
    registry = deepcopy(_registry())
    registry["prose_source"].append(deepcopy(registry["prose_source"][0]))
    errors = validate_registry(registry, _manuscript_root())
    assert any("duplicate registry prose_source blocks" in error for error in errors)


def test_prose_source_nested_schema_is_exact() -> None:
    registry = deepcopy(_registry())
    registry["prose_source"][0]["unexpected"] = "value"
    errors = validate_registry(registry, _manuscript_root())
    assert any("prose_source has incorrect fields" in error for error in errors)


def test_prose_claim_nested_schema_and_types_are_exact() -> None:
    registry = deepcopy(_registry())
    claim = registry["prose_source"][0]["claims"][0]
    claim["unexpected"] = "value"
    claim["line"] = True
    errors = validate_registry(registry, _manuscript_root())
    assert any("prose claim has incorrect fields" in error for error in errors)
    assert any(
        "prose claim line must be a positive integer" in error for error in errors
    )


def test_artifact_coverage_nested_schema_and_types_are_exact() -> None:
    registry = deepcopy(_registry())
    record = registry["artifact_coverage"][0]
    record["unexpected"] = "value"
    record["paths"] = []
    errors = validate_registry(registry, _manuscript_root())
    assert "artifact coverage entry has incorrect fields" in errors
    assert "artifact coverage paths must be a non-empty list of strings" in errors


def test_input_exception_nested_schema_and_types_are_exact() -> None:
    registry = deepcopy(_registry())
    item = registry["input_exception"][0]
    item["unexpected"] = "value"
    item["reason"] = []
    errors = validate_registry(registry, _manuscript_root())
    assert any("input exception has incorrect fields" in error for error in errors)
    assert any(
        "input exception reason must be a non-empty string" in error for error in errors
    )


def test_input_exception_inventory_is_exactly_fifteen_records() -> None:
    rows = _registry()["input_exception"]
    assert tuple(item["name"] for item in rows) == CANONICAL_INPUT_EXCEPTION_NAMES
    assert len(rows) == 15
    assert has_canonical_input_exception_inventory(rows)
    assert not has_canonical_input_exception_inventory(rows[:-1])
    assert not has_canonical_input_exception_inventory(rows + [deepcopy(rows[-1])])


@pytest.mark.parametrize("field", sorted(REQUIRED_FIELDS))
def test_result_field_types_are_enforced(tmp_path: Path, field: str) -> None:
    registry, row = _minimal_registry(tmp_path)
    expected = REQUIRED_FIELDS[field]
    row[field] = (
        "not-a-list" if expected is list else "not-a-bool" if expected is bool else []
    )
    errors = validate_registry(registry, tmp_path)
    assert any(f"{field} must be {expected.__name__}" in error for error in errors)


@pytest.mark.parametrize("token", ["TBD", "TODO", "N/A"])
def test_placeholder_tokens_are_rejected(tmp_path: Path, token: str) -> None:
    registry, row = _minimal_registry(tmp_path)
    row["notes"] = f"status {token}"
    errors = validate_registry(registry, tmp_path)
    assert any("notes contains a placeholder token" in error for error in errors)


def _git_commit(repo: Path) -> str:
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.email", "test@example.invalid"],
        check=True,
    )
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
    (repo / "tracked").write_text(repo.name)
    subprocess.run(["git", "-C", str(repo), "add", "tracked"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "fixture"], check=True)
    return subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
    ).strip()


def test_pipeline_pin_is_anchored_and_verified_in_pipeline_repo(tmp_path: Path) -> None:
    registry, row = _minimal_registry(tmp_path)
    pipeline_sha = _git_commit(tmp_path / "pipeline")
    analysis_sha = _git_commit(tmp_path / "analysis")

    row["pipeline_pin"] = f"prefix {pipeline_sha[:12]}"
    errors = validate_registry(registry, tmp_path)
    assert any("pipeline_pin has invalid format" in error for error in errors)

    row["pipeline_pin"] = analysis_sha
    errors = validate_registry(registry, tmp_path)
    assert any("pipeline pin does not exist" in error for error in errors)

    row["pipeline_pin"] = pipeline_sha
    errors = validate_registry(registry, tmp_path)
    assert not any(
        "pipeline_pin" in error or "pipeline pin" in error for error in errors
    )


def test_provenance_path_must_exist_at_declared_commit(tmp_path: Path) -> None:
    registry, row = _minimal_registry(tmp_path)
    pipeline = tmp_path / "pipeline"
    old_commit = _git_commit(pipeline)
    (pipeline / "new.py").write_text("print('new')\n")
    subprocess.run(["git", "-C", str(pipeline), "add", "new.py"], check=True)
    subprocess.run(
        ["git", "-C", str(pipeline), "commit", "-qm", "add new path"], check=True
    )
    row["producing_script"] = "pipeline/new.py"
    row["pipeline_pin"] = old_commit
    row["inputs"] = []
    row["artifact"] = ""
    row["provenance_refs"] = [
        {
            "role": "producer",
            "path": "pipeline/new.py",
            "repository": "pipeline",
            "commit": old_commit,
        }
    ]
    errors = validate_registry(registry, tmp_path)
    assert any(
        "provenance path does not exist at declared pipeline commit" in error
        for error in errors
    )


def test_makefile_check_state_gates_registry_and_generated_view() -> None:
    text = MAKEFILE.read_text()
    check_state = text.split("check-state: check-mount", 1)[1].split("\ntest:", 1)[0]
    assert "render_results_registry.py --validate" in check_state
    assert "render_results_registry.py --check" in check_state


def test_results_view_is_byte_current() -> None:
    subprocess.run(
        [sys.executable, str(RENDERER), "--check"],
        cwd=ROOT,
        check=True,
    )
    first = subprocess.check_output(
        [sys.executable, str(RENDERER), "--stdout"], cwd=ROOT
    )
    second = subprocess.check_output(
        [sys.executable, str(RENDERER), "--stdout"], cwd=ROOT
    )
    assert first == second == RESULTS.read_bytes()
