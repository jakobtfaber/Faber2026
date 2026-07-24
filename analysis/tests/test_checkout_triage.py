from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import jsonschema
import pytest


ROOT = Path(__file__).resolve().parents[1]


def load_triage():
    spec = importlib.util.spec_from_file_location(
        "checkout_triage", ROOT / "scripts/checkout_triage.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


CT = load_triage()


def upstream(
    has_upstream: bool = False,
    upstream: str | None = None,
    upstream_ref: str | None = None,
    ahead: int | None = None,
    behind: int | None = None,
    state: str = "missing_upstream",
):
    return {
        "has_upstream": has_upstream,
        "upstream": upstream,
        "upstream_ref": upstream_ref,
        "ahead": ahead,
        "behind": behind,
        "state": state,
        "limits": "Computed from local refs only; no network fetch or remote query used.",
    }


def checkout(
    path: str,
    repository: str | None = "jakobtfaber/Faber2026",
    branch: str | None = "main",
    head: str = "abc123",
    kind: str | None = "standalone_clone",
    detached: bool = False,
    dirty: bool = False,
    ahead: int | None = None,
    behind: int | None = None,
    unique: list[str] | None = None,
    git_common_dir: str | None = None,
    git_dir: str | None = None,
    broken: bool = False,
    scan_problem: str = "",
) -> dict[str, Any]:
    if git_dir is None:
        git_dir = f"{path}/.git"
    if git_common_dir is None:
        git_common_dir = git_dir
    status = {
        "branch_line": f"## {branch or 'HEAD (no branch)'}" + (
            f"...origin/{branch}" if branch and not detached and ahead is None and behind is None else ""
        ),
        "staged_file_paths": ["staged.txt"] if dirty else [],
        "unstaged_file_paths": ["unstaged.txt"] if dirty else [],
        "untracked_file_paths": ["untracked.txt"] if dirty else [],
        "raw_entries": [],
    }
    facts: dict[str, Any] = {
        "repository": None if broken else repository,
        "checkout_kind": None if broken else kind,
        "branch": None if (detached or broken) else branch,
        "full_head_commit": None if broken else head,
        "detached_head": detached and not broken,
        "git_dir": None if broken else git_dir,
        "git_common_dir": None if broken else git_common_dir,
        "local_upstream": upstream(
            has_upstream=ahead is not None or behind is not None,
            upstream=f"origin/{branch}" if branch else None,
            upstream_ref=f"refs/remotes/origin/{branch}" if branch else None,
            ahead=ahead,
            behind=behind,
            state="locally_computed" if (ahead is not None or behind is not None) else "missing_upstream",
        ),
        "remote_github_slugs": [] if broken else [repository],
        "staged_file_count": 1 if dirty else 0,
        "unstaged_file_count": 1 if dirty else 0,
        "untracked_file_count": 1 if dirty else 0,
        "dirty_submodule_count": 0,
        "locally_unique_looking_full_commits": unique or [],
        "locally_unique_looking_limits": "Local ancestry check only; no network used.",
        "status": status,
    }
    if broken:
        facts["scan_problem_classification"] = scan_problem or "broken_checkout"
        facts["scan_problem_detail"] = "git metadata found but git rev-parse failed"
    return {
        "checkout_path": path,
        "facts": facts,
        "proposed_classification": "inventory_only",
        "classification_confidence": "medium",
        "classification_evidence": [],
        "unresolved_questions": [],
        "preservation_priority": "low",
    }


def make_inventory(
    checkouts: list[dict[str, Any]],
    divergences: list[dict[str, Any]] | None = None,
    missing: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": 2,
        "schema_uri": "https://faber2026.jakobtfaber.com/schemas/checkout-inventory-v2.schema.json",
        "tool_version": "2.0.0",
        "scan_roots": ["/tmp/scan"],
        "warnings": [],
        "scan_problems": [],
        "workspace_bundles": [],
        "checkout_triage": checkouts,
        "branch_divergence_groups": divergences or [],
        "dirty_checkout_details": [],
        "missing_registration_details": missing or [],
        "method": {"network": "not_used"},
    }


def run_triage(tmp_path: Path, inventory: dict[str, Any]):
    inv_path = tmp_path / "inventory.json"
    inv_path.write_text(json.dumps(inventory, indent=2, sort_keys=True), encoding="utf-8")
    json_out = tmp_path / "triage.json"
    html_out = tmp_path / "triage.html"
    assert CT.main(["--inventory", str(inv_path), "--json-output", str(json_out), "--html-output", str(html_out)]) == 0
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    payload["_html"] = html_out.read_text(encoding="utf-8")
    payload["_input_bytes"] = inv_path.read_bytes()
    return payload


def record_by_path(payload: dict) -> dict[str, dict]:
    return {r["checkout_id"]: r for r in payload["advisory_records"]}


def test_help_exits_zero_and_mentions_required_args(capsys):
    with pytest.raises(SystemExit) as exc:
        CT.main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "--inventory" in out
    assert "--json-output" in out
    assert "--html-output" in out


def test_schema_validation(tmp_path):
    with open(ROOT / "schemas" / "checkout-triage-v1.schema.json") as f:
        schema = json.load(f)
    run_triage(tmp_path, make_inventory([checkout("/tmp/c")]))
    raw = json.loads((tmp_path / "triage.json").read_text(encoding="utf-8"))
    jsonschema.validate(raw, schema)


def test_deterministic_byte_for_byte_output(tmp_path):
    inv = make_inventory([checkout("/work/clean", branch="feature", ahead=1)])
    for sub in ("a", "b"):
        (tmp_path / sub).mkdir()
    run_triage(tmp_path / "a", inv)
    run_triage(tmp_path / "b", inv)
    for name in ("triage.json", "triage.html"):
        a = (tmp_path / "a" / name).read_bytes()
        b = (tmp_path / "b" / name).read_bytes()
        assert a == b


def test_input_sha256_binds_to_inventory_bytes(tmp_path):
    inv = make_inventory([checkout("/tmp/c")])
    inv_path = tmp_path / "inventory.json"
    inv_path.write_text(json.dumps(inv, indent=2, sort_keys=True), encoding="utf-8")
    json_out = tmp_path / "triage.json"
    html_out = tmp_path / "triage.html"
    CT.main(["--inventory", str(inv_path), "--json-output", str(json_out), "--html-output", str(html_out)])
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    expected = hashlib.sha256(inv_path.read_bytes()).hexdigest()
    assert payload["input_sha256"] == expected


def test_default_to_unknown_for_clean_main(tmp_path):
    payload = run_triage(tmp_path, make_inventory([checkout("/tmp/clean-main")]))
    rec = record_by_path(payload)["/tmp/clean-main"]
    assert rec["proposed_classification"] == "unknown"
    assert rec["confidence"] == "low"


def test_dirty_state_alone_does_not_produce_strong_classification(tmp_path):
    # dirty + no path hint + no upstream + main branch -> unknown (not author-scratch)
    payload = run_triage(
        tmp_path,
        make_inventory([checkout("/tmp/clean-main", dirty=True, branch="main")]),
    )
    rec = record_by_path(payload)["/tmp/clean-main"]
    assert rec["proposed_classification"] == "unknown"
    assert rec["confidence"] == "low"


def test_branch_name_alone_does_not_produce_high_confidence(tmp_path):
    # branch != main but no dirty, no ahead, no unique -> unknown
    payload = run_triage(tmp_path, make_inventory([checkout("/tmp/branch", branch="feature")]))
    rec = record_by_path(payload)["/tmp/branch"]
    assert rec["proposed_classification"] == "unknown"
    assert rec["confidence"] == "low"


def test_review_ready_clean_ahead_not_behind(tmp_path):
    payload = run_triage(
        tmp_path,
        make_inventory([checkout("/tmp/review", branch="feature", ahead=2, behind=0)]),
    )
    rec = record_by_path(payload)["/tmp/review"]
    assert rec["proposed_classification"] == "review-ready"
    assert rec["confidence"] == "high"


def test_candidate_clean_nonmain_unique_commits(tmp_path):
    payload = run_triage(
        tmp_path,
        make_inventory([checkout("/tmp/cand", branch="feature", unique=["def456"])]),
    )
    rec = record_by_path(payload)["/tmp/cand"]
    assert rec["proposed_classification"] == "candidate"
    assert rec["confidence"] == "medium"


def test_active_dirty_nonmain_branch(tmp_path):
    payload = run_triage(
        tmp_path,
        make_inventory([checkout("/tmp/active", branch="feature", dirty=True)]),
    )
    rec = record_by_path(payload)["/tmp/active"]
    assert rec["proposed_classification"] == "active"
    assert rec["confidence"] == "medium"


def test_author_scratch_dirty_path_hint(tmp_path):
    payload = run_triage(
        tmp_path,
        make_inventory([checkout("/tmp/scratch-work", dirty=True)]),
    )
    rec = record_by_path(payload)["/tmp/scratch-work"]
    assert rec["proposed_classification"] == "author-scratch"
    assert rec["confidence"] == "medium"


def test_superseded_by_upstream(tmp_path):
    payload = run_triage(
        tmp_path,
        make_inventory([checkout("/tmp/old-main", branch="main", ahead=0, behind=3)]),
    )
    rec = record_by_path(payload)["/tmp/old-main"]
    assert rec["proposed_classification"] == "superseded"
    assert rec["confidence"] == "high"


def test_true_local_ancestry_supports_superseded(tmp_path):
    older = checkout("/tmp/older", branch="feature", head="aaa")
    newer = checkout("/tmp/newer", branch="feature", head="bbb")
    divergence = [
        {
            "repository": "jakobtfaber/Faber2026",
            "branch": "feature",
            "checkout_paths": ["/tmp/older", "/tmp/newer"],
            "distinct_full_head_commits": ["aaa", "bbb"],
            "locally_computable_reachability_relationships": [
                {
                    "left_checkout_path": "/tmp/older",
                    "left_full_head_commit": "aaa",
                    "right_checkout_path": "/tmp/newer",
                    "right_full_head_commit": "bbb",
                    "relationship": "left_ancestor_of_right",
                    "checked_from_checkout_path": "/tmp/newer",
                    "limits": "local ancestry only",
                }
            ],
        }
    ]
    payload = run_triage(tmp_path, make_inventory([older, newer], divergences=divergence))
    assert record_by_path(payload)["/tmp/older"]["proposed_classification"] == "superseded"
    assert record_by_path(payload)["/tmp/newer"]["proposed_classification"] == "active"
    contained = [r for r in payload["relationships"] if r["kind"] == "contained_checkouts"]
    assert len(contained) == 1
    assert sorted(contained[0]["checkout_ids"]) == ["/tmp/newer", "/tmp/older"]


def test_divergent_clones_produce_conflict_not_winner(tmp_path):
    a = checkout("/tmp/clone-a", branch="feature", head="aaa")
    b = checkout("/tmp/clone-b", branch="feature", head="bbb")
    divergence = [
        {
            "repository": "jakobtfaber/Faber2026",
            "branch": "feature",
            "checkout_paths": ["/tmp/clone-a", "/tmp/clone-b"],
            "distinct_full_head_commits": ["aaa", "bbb"],
            "locally_computable_reachability_relationships": [
                {
                    "left_checkout_path": "/tmp/clone-a",
                    "left_full_head_commit": "aaa",
                    "right_checkout_path": "/tmp/clone-b",
                    "right_full_head_commit": "bbb",
                    "relationship": "unrelated_or_not_locally_computable",
                    "checked_from_checkout_path": "/tmp/clone-a",
                    "limits": "local ancestry only",
                }
            ],
        }
    ]
    payload = run_triage(tmp_path, make_inventory([a, b], divergences=divergence))
    conflict_kinds = {c["kind"] for c in payload["conflicts"]}
    assert "divergent_clones" in conflict_kinds
    assert "independent_clones_divergent" in conflict_kinds or "divergent_clones" in conflict_kinds


def test_branch_name_collision_at_different_heads(tmp_path):
    a = checkout("/tmp/a", branch="feature", head="aaa")
    b = checkout("/tmp/b", branch="feature", head="bbb")
    divergence = [
        {
            "repository": "jakobtfaber/Faber2026",
            "branch": "feature",
            "checkout_paths": ["/tmp/a", "/tmp/b"],
            "distinct_full_head_commits": ["aaa", "bbb"],
            "locally_computable_reachability_relationships": [],
        }
    ]
    payload = run_triage(tmp_path, make_inventory([a, b], divergences=divergence))
    rels = {r["kind"] for r in payload["relationships"]}
    assert "same_repository_divergent_heads" in rels
    assert any(c["kind"] == "divergent_clones" for c in payload["conflicts"])


def test_linked_worktree_grouping(tmp_path):
    main = checkout("/tmp/main", kind="standalone_clone", git_dir="/tmp/main/.git", git_common_dir="/tmp/main/.git")
    linked = checkout("/tmp/linked", kind="linked_worktree", branch="feature", git_dir="/tmp/main/.git/worktrees/linked", git_common_dir="/tmp/main/.git")
    payload = run_triage(tmp_path, make_inventory([main, linked]))
    rels = [r for r in payload["relationships"] if r["kind"] == "linked_worktrees"]
    assert len(rels) == 1
    assert sorted(rels[0]["checkout_ids"]) == ["/tmp/linked", "/tmp/main"]


def test_independent_clone_grouping(tmp_path):
    a = checkout("/tmp/clone-a", head="aaa")
    b = checkout("/tmp/clone-b", head="aaa")
    payload = run_triage(tmp_path, make_inventory([a, b]))
    rels = [r for r in payload["relationships"] if r["kind"] == "same_repository_same_head"]
    assert len(rels) == 1


def test_detached_and_inaccessible_records(tmp_path):
    detached = checkout("/tmp/detached", branch=None, detached=True)
    broken = checkout("/tmp/broken", broken=True)
    payload = run_triage(tmp_path, make_inventory([detached, broken]))
    recs = record_by_path(payload)
    assert recs["/tmp/detached"]["proposed_classification"] == "potentially-orphaned"
    assert recs["/tmp/broken"]["proposed_classification"] == "potentially-orphaned"
    rels = {r["kind"] for r in payload["relationships"]}
    assert "detached_checkouts" in rels
    assert "inaccessible_checkout" in rels


def test_confidence_reduction_under_contradictory_evidence(tmp_path):
    # dirty + path hint suggests author-scratch, but main branch with upstream and commits ahead contradicts it
    payload = run_triage(
        tmp_path,
        make_inventory([checkout("/tmp/scratch-main", branch="main", dirty=True, ahead=2, behind=0)]),
    )
    rec = record_by_path(payload)["/tmp/scratch-main"]
    assert rec["proposed_classification"] == "author-scratch"
    assert rec["confidence"] == "low"
    assert "scratch_with_commits_ahead" in rec["conflicts"]


def test_refuses_to_overwrite_input(tmp_path):
    inv = make_inventory([checkout("/tmp/c")])
    inv_path = tmp_path / "inventory.json"
    inv_path.write_text(json.dumps(inv, indent=2, sort_keys=True), encoding="utf-8")
    sha_before = hashlib.sha256(inv_path.read_bytes()).hexdigest()
    with pytest.raises(SystemExit) as exc:
        CT.main(
            [
                "--inventory",
                str(inv_path),
                "--json-output",
                str(inv_path),
                "--html-output",
                str(tmp_path / "out.html"),
            ]
        )
    assert exc.value.code != 0
    sha_after = hashlib.sha256(inv_path.read_bytes()).hexdigest()
    assert sha_before == sha_after


def test_refuses_identical_json_and_html_paths(tmp_path):
    inv = make_inventory([checkout("/tmp/c")])
    inv_path = tmp_path / "inventory.json"
    inv_path.write_text(json.dumps(inv), encoding="utf-8")
    out = tmp_path / "same.json"
    with pytest.raises(SystemExit) as exc:
        CT.main(
            [
                "--inventory",
                str(inv_path),
                "--json-output",
                str(out),
                "--html-output",
                str(out),
            ]
        )
    assert exc.value.code != 0


def test_refuses_missing_output_parent_directory(tmp_path):
    inv = make_inventory([checkout("/tmp/c")])
    inv_path = tmp_path / "inventory.json"
    inv_path.write_text(json.dumps(inv), encoding="utf-8")
    missing_parent = tmp_path / "missing_dir" / "triage.json"
    with pytest.raises(SystemExit) as exc:
        CT.main(
            [
                "--inventory",
                str(inv_path),
                "--json-output",
                str(missing_parent),
                "--html-output",
                str(tmp_path / "triage.html"),
            ]
        )
    assert exc.value.code != 0
    assert not missing_parent.exists()


def test_refuses_output_path_that_is_a_directory(tmp_path):
    inv = make_inventory([checkout("/tmp/c")])
    inv_path = tmp_path / "inventory.json"
    inv_path.write_text(json.dumps(inv), encoding="utf-8")
    bad_json = tmp_path / "json_dir"
    bad_json.mkdir()
    with pytest.raises(SystemExit) as exc:
        CT.main(
            [
                "--inventory",
                str(inv_path),
                "--json-output",
                str(bad_json),
                "--html-output",
                str(tmp_path / "triage.html"),
            ]
        )
    assert exc.value.code != 0


def test_no_subprocess_git_network_or_filesystem_discovery(tmp_path, monkeypatch):
    called = []

    def forbidden(*args, **kwargs):
        called.append(args)
        raise RuntimeError("forbidden filesystem/network/subprocess call")

    monkeypatch.setattr(CT.os, "walk", forbidden)
    monkeypatch.setattr(CT.os, "listdir", forbidden)
    monkeypatch.setattr(CT.os, "scandir", forbidden)
    monkeypatch.setattr(CT, "subprocess", subprocess, raising=False)
    monkeypatch.setattr(subprocess, "run", forbidden)

    inv = make_inventory([checkout("/tmp/c")])
    run_triage(tmp_path, inv)
    assert not called


def test_html_escapes_untrusted_values(tmp_path):
    inv = make_inventory([checkout("/tmp/<script>alert(1)</script>")])
    payload = run_triage(tmp_path, inv)
    assert "&lt;script&gt;" in payload["_html"]
    assert "<script>alert(1)</script>" not in payload["_html"]


def test_forbidden_cleanup_terminology_absent(tmp_path):
    inv = make_inventory([checkout("/tmp/c")])
    run_triage(tmp_path, inv)
    forbidden = ("safe-to-delete", "disposable", "obsolete", "prune", "cleanup-ready", "archive-now")
    json_text = (tmp_path / "triage.json").read_text(encoding="utf-8").lower()
    html = (tmp_path / "triage.html").read_text(encoding="utf-8").lower()
    for word in forbidden:
        assert word not in json_text
        assert word not in html


def test_existing_outputs_require_explicit_overwrite(tmp_path):
    inv = make_inventory([checkout("/tmp/c")])
    inv_path = tmp_path / "inventory.json"
    inv_path.write_text(json.dumps(inv), encoding="utf-8")
    json_out = tmp_path / "triage.json"
    html_out = tmp_path / "triage.html"
    json_out.write_text("preserve-json", encoding="utf-8")
    html_out.write_text("preserve-html", encoding="utf-8")

    with pytest.raises(SystemExit) as exc:
        CT.main(
            [
                "--inventory",
                str(inv_path),
                "--json-output",
                str(json_out),
                "--html-output",
                str(html_out),
            ]
        )
    assert exc.value.code == 2
    assert json_out.read_text(encoding="utf-8") == "preserve-json"
    assert html_out.read_text(encoding="utf-8") == "preserve-html"

    assert (
        CT.main(
            [
                "--inventory",
                str(inv_path),
                "--json-output",
                str(json_out),
                "--html-output",
                str(html_out),
                "--overwrite",
            ]
        )
        == 0
    )
    assert json.loads(json_out.read_text(encoding="utf-8"))["schema_version"] == 1


def test_resolved_output_aliases_are_rejected(tmp_path):
    inv = make_inventory([checkout("/tmp/c")])
    inv_path = tmp_path / "inventory.json"
    inv_path.write_text(json.dumps(inv), encoding="utf-8")
    output = tmp_path / "triage.json"
    alias = tmp_path / "triage.html"
    alias.symlink_to(output.name)
    with pytest.raises(SystemExit) as exc:
        CT.main(
            [
                "--inventory",
                str(inv_path),
                "--json-output",
                str(output),
                "--html-output",
                str(alias),
                "--overwrite",
            ]
        )
    assert exc.value.code == 2


def test_paired_output_write_rolls_back_on_second_failure(tmp_path, monkeypatch):
    json_out = tmp_path / "triage.json"
    html_out = tmp_path / "triage.html"
    real_link = CT.os.link
    calls = 0

    def fail_second_link(source, destination):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected second-link failure")
        return real_link(source, destination)

    monkeypatch.setattr(CT.os, "link", fail_second_link)
    with pytest.raises(SystemExit) as exc:
        CT.atomic_write_outputs(
            ((json_out, "json"), (html_out, "html")), overwrite=False
        )
    assert exc.value.code == 2
    assert not json_out.exists()
    assert not html_out.exists()


def test_paired_overwrite_restores_old_outputs_on_second_failure(tmp_path, monkeypatch):
    json_out = tmp_path / "triage.json"
    html_out = tmp_path / "triage.html"
    json_out.write_text("old-json", encoding="utf-8")
    html_out.write_text("old-html", encoding="utf-8")
    real_replace = CT.os.replace
    calls = 0

    def fail_second_replace(source, destination):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected second-replace failure")
        return real_replace(source, destination)

    monkeypatch.setattr(CT.os, "replace", fail_second_replace)
    with pytest.raises(SystemExit) as exc:
        CT.atomic_write_outputs(
            ((json_out, "new-json"), (html_out, "new-html")), overwrite=True
        )
    assert exc.value.code == 2
    assert json_out.read_text(encoding="utf-8") == "old-json"
    assert html_out.read_text(encoding="utf-8") == "old-html"


def test_same_commit_in_different_repositories_is_not_same_repository_same_head(tmp_path):
    a = checkout("/tmp/a", repository="owner/repo-a", head="same")
    b = checkout("/tmp/b", repository="owner/repo-b", head="same")
    payload = run_triage(tmp_path, make_inventory([a, b]))
    relationships = {
        (item["kind"], tuple(item["checkout_ids"])) for item in payload["relationships"]
    }
    assert ("same_repository_same_head", ("/tmp/a", "/tmp/b")) not in relationships


def test_divergent_linked_worktrees_are_not_independent_clones(tmp_path):
    common = "/tmp/main/.git"
    main = checkout(
        "/tmp/main",
        head="aaa",
        kind="standalone_clone",
        git_dir=common,
        git_common_dir=common,
    )
    linked = checkout(
        "/tmp/linked",
        branch="feature",
        head="bbb",
        kind="linked_worktree",
        git_dir=f"{common}/worktrees/linked",
        git_common_dir=common,
    )
    payload = run_triage(tmp_path, make_inventory([main, linked]))
    assert not any(
        item["kind"] in {"independent_clones", "independent_clones_divergent"}
        for item in payload["relationships"] + payload["conflicts"]
    )


def test_malformed_checkout_inventory_fails_cleanly(tmp_path):
    inventory = make_inventory([{"checkout_path": "/tmp/broken"}])
    inv_path = tmp_path / "inventory.json"
    inv_path.write_text(json.dumps(inventory), encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        CT.main(
            [
                "--inventory",
                str(inv_path),
                "--json-output",
                str(tmp_path / "triage.json"),
                "--html-output",
                str(tmp_path / "triage.html"),
            ]
        )
    assert exc.value.code == 2


def test_malformed_nested_checkout_facts_fail_cleanly(tmp_path):
    broken = checkout("/tmp/broken")
    broken["facts"]["local_upstream"] = "not-an-object"
    inventory = make_inventory([broken])
    inv_path = tmp_path / "inventory.json"
    inv_path.write_text(json.dumps(inventory), encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        CT.main(
            [
                "--inventory",
                str(inv_path),
                "--json-output",
                str(tmp_path / "triage.json"),
                "--html-output",
                str(tmp_path / "triage.html"),
            ]
        )
    assert exc.value.code == 2


@pytest.mark.parametrize(
    "mutation",
    [
        lambda payload: payload.__setitem__("scan_roots", ["", ""]),
        lambda payload: payload["checkout_triage"][0]["facts"].__setitem__(
            "repository", ["not", "a", "string"]
        ),
        lambda payload: payload["missing_registration_details"].append(
            {
                "registered_path": "",
                "branch_or_ref": None,
                "pointed_to_commit": None,
                "source_git_common_dir": "/tmp/repo/.git",
                "local_reachability_information": {},
                "missing_path_statement": "missing",
            }
        ),
    ],
)
def test_schema_invalid_consumed_fields_fail_cleanly(tmp_path, mutation):
    inventory = make_inventory([checkout("/tmp/broken")])
    mutation(inventory)
    inv_path = tmp_path / "inventory.json"
    inv_path.write_text(json.dumps(inventory), encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        CT.main(
            [
                "--inventory",
                str(inv_path),
                "--json-output",
                str(tmp_path / "triage.json"),
                "--html-output",
                str(tmp_path / "triage.html"),
            ]
        )
    assert exc.value.code == 2


def test_schema_rejects_unknown_count_keys(tmp_path):
    with open(ROOT / "schemas" / "checkout-triage-v1.schema.json") as f:
        schema = json.load(f)
    payload = run_triage(tmp_path, make_inventory([checkout("/tmp/c")]))
    payload.pop("_html")
    payload.pop("_input_bytes")
    payload["aggregate_counts"]["classification_counts"]["invented"] = 1
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, schema)


def test_source_uses_only_audited_imports_and_filesystem_calls():
    source = (ROOT / "scripts" / "checkout_triage.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    allowed_modules = {
        "__future__",
        "argparse",
        "hashlib",
        "html",
        "json",
        "os",
        "re",
        "sys",
        "tempfile",
        "collections",
        "datetime",
        "pathlib",
        "typing",
    }
    allowed_os_calls = {"link", "replace", "unlink"}
    allowed_path_calls = {
        "exists",
        "is_dir",
        "is_file",
        "read_bytes",
        "resolve",
    }
    forbidden_discovery_calls = {
        "fwalk",
        "glob",
        "iterdir",
        "listdir",
        "rglob",
        "scandir",
        "walk",
    }
    forbidden_path_mutations = {
        "chmod",
        "mkdir",
        "rename",
        "replace",
        "rmdir",
        "touch",
        "unlink",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(alias.name.split(".")[0] in allowed_modules for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.module is not None
            assert node.module.split(".")[0] in allowed_modules
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden_discovery_calls
            if not (
                isinstance(node.func.value, ast.Name)
                and node.func.value.id == "os"
            ):
                assert node.func.attr not in forbidden_path_mutations
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "os":
                assert node.func.attr in allowed_os_calls
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "Path":
                assert node.func.attr in allowed_path_calls
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"__import__", "eval", "exec"}
