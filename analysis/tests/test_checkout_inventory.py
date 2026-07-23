from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load_inventory():
    spec = importlib.util.spec_from_file_location(
        "checkout_inventory", ROOT / "scripts/checkout_inventory.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def git(cwd: Path, *args: str) -> str:
    env = os.environ.copy()
    env.update(
        {
            "GIT_AUTHOR_NAME": "Test User",
            "GIT_AUTHOR_EMAIL": "test@example.com",
            "GIT_COMMITTER_NAME": "Test User",
            "GIT_COMMITTER_EMAIL": "test@example.com",
        }
    )
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        env=env,
    )
    return result.stdout.strip()


def write_commit(repo: Path, rel: str, text: str, message: str) -> str:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    git(repo, "add", rel)
    git(repo, "commit", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def init_repo(path: Path, slug: str, remote_style: str = "ssh") -> str:
    path.mkdir(parents=True)
    git(path, "init", "-b", "main")
    head = write_commit(path, "README.md", f"# {slug}\n", "initial")
    url = (
        f"git@github.com:{slug}.git"
        if remote_style == "ssh"
        else f"https://github.com/{slug}.git"
    )
    git(path, "remote", "add", "origin", url)
    git(path, "update-ref", "refs/remotes/origin/main", head)
    return head


def run_inventory(tmp_path: Path, *scan_roots: Path) -> dict:
    ci = load_inventory()
    out_json = tmp_path / "inventory.json"
    out_html = tmp_path / "inventory.html"
    argv: list[str] = []
    for root in scan_roots:
        argv.extend(["--scan-root", str(root)])
    argv.extend(["--json-out", str(out_json), "--html-out", str(out_html)])
    assert ci.main(argv) == 0
    payload = json.loads(out_json.read_text(encoding="utf-8"))
    payload["_html"] = out_html.read_text(encoding="utf-8")
    return payload


def inventory_outputs(tmp_path: Path, *scan_roots: Path) -> tuple[dict, str, str]:
    ci = load_inventory()
    out_json = tmp_path / "inventory.json"
    out_html = tmp_path / "inventory.html"
    argv: list[str] = []
    for root in scan_roots:
        argv.extend(["--scan-root", str(root)])
    argv.extend(["--json-out", str(out_json), "--html-out", str(out_html)])
    assert ci.main(argv) == 0
    return (
        json.loads(out_json.read_text(encoding="utf-8")),
        out_json.read_text(encoding="utf-8"),
        out_html.read_text(encoding="utf-8"),
    )


def triage_by_path(payload: dict) -> dict[str, dict]:
    return {item["checkout_path"]: item for item in payload["checkout_triage"]}


def dirty_by_path(payload: dict) -> dict[str, dict]:
    return {item["checkout_path"]: item for item in payload["dirty_checkout_details"]}


def bundle_by_parent(payload: dict) -> dict[str | None, dict]:
    return {item["parent_checkout"]: item for item in payload["workspace_bundles"]}


def add_submodule(parent: Path, source: Path, rel: str, slug: str) -> str:
    git(
        parent,
        "-c",
        "protocol.file.allow=always",
        "submodule",
        "add",
        str(source),
        rel,
    )
    git(parent / rel, "remote", "set-url", "origin", f"https://github.com/{slug}.git")
    git(parent, "commit", "-m", f"add {rel}")
    return git(parent, "rev-parse", "HEAD")


def test_cli_requires_explicit_scan_root(tmp_path):
    ci = load_inventory()
    with pytest.raises(SystemExit):
        ci.main(
            [
                "--json-out",
                str(tmp_path / "inventory.json"),
                "--html-out",
                str(tmp_path / "inventory.html"),
            ]
        )


def test_workspace_bundle_with_two_submodules_reports_matching_and_mismatching_pins(
    tmp_path,
):
    analysis_source = tmp_path / "analysis-source"
    pipeline_source = tmp_path / "pipeline-source"
    analysis_initial = init_repo(
        analysis_source, "jakobtfaber/Faber2026-analysis", remote_style="https"
    )
    pipeline_initial = init_repo(
        pipeline_source, "jakobtfaber/dsa110-FLITS", remote_style="ssh"
    )

    matching_parent = tmp_path / "matching" / "Faber2026"
    init_repo(matching_parent, "jakobtfaber/Faber2026")
    add_submodule(
        matching_parent, analysis_source, "analysis", "jakobtfaber/Faber2026-analysis"
    )
    add_submodule(
        matching_parent, pipeline_source, "pipeline", "jakobtfaber/dsa110-FLITS"
    )
    matching_head = git(matching_parent, "rev-parse", "HEAD")
    git(matching_parent, "update-ref", "refs/remotes/origin/main", matching_head)

    mismatch_parent = tmp_path / "mismatch" / "Faber2026"
    init_repo(mismatch_parent, "jakobtfaber/Faber2026")
    add_submodule(
        mismatch_parent, analysis_source, "analysis", "jakobtfaber/Faber2026-analysis"
    )
    add_submodule(
        mismatch_parent, pipeline_source, "pipeline", "jakobtfaber/dsa110-FLITS"
    )
    mismatch_parent_head = git(mismatch_parent, "rev-parse", "HEAD")
    git(mismatch_parent, "update-ref", "refs/remotes/origin/main", mismatch_parent_head)
    analysis_new = write_commit(
        mismatch_parent / "analysis", "new.txt", "new\n", "advance analysis"
    )

    payload = run_inventory(tmp_path, tmp_path)
    bundles = bundle_by_parent(payload)

    matching = bundles[str(matching_parent.resolve())]
    assert matching == {
        "workspace_id": str(matching_parent.resolve()),
        "parent_checkout": str(matching_parent.resolve()),
        "analysis_checkout": str((matching_parent / "analysis").resolve()),
        "pipeline_checkout": str((matching_parent / "pipeline").resolve()),
        "parent_recorded_analysis_pin": analysis_initial,
        "parent_recorded_pipeline_pin": pipeline_initial,
        "actual_analysis_head": analysis_initial,
        "actual_pipeline_head": pipeline_initial,
        "pin_match_status": "matching",
        "aggregate_dirty_status": "clean",
        "warnings": [],
    }

    mismatching = bundles[str(mismatch_parent.resolve())]
    assert mismatching["parent_recorded_analysis_pin"] == analysis_initial
    assert mismatching["actual_analysis_head"] == analysis_new
    assert mismatching["parent_recorded_pipeline_pin"] == pipeline_initial
    assert mismatching["actual_pipeline_head"] == pipeline_initial
    assert mismatching["pin_match_status"] == "mismatching"
    assert "pin_mismatch:analysis" in mismatching["warnings"]


def test_dirty_parent_clean_submodules_and_clean_parent_dirty_submodule(tmp_path):
    analysis_source = tmp_path / "analysis-source"
    pipeline_source = tmp_path / "pipeline-source"
    init_repo(analysis_source, "jakobtfaber/Faber2026-analysis")
    init_repo(pipeline_source, "jakobtfaber/dsa110-FLITS")

    dirty_parent = tmp_path / "dirty-parent" / "Faber2026"
    init_repo(dirty_parent, "jakobtfaber/Faber2026")
    add_submodule(
        dirty_parent, analysis_source, "analysis", "jakobtfaber/Faber2026-analysis"
    )
    add_submodule(dirty_parent, pipeline_source, "pipeline", "jakobtfaber/dsa110-FLITS")
    (dirty_parent / "README.md").write_text("# dirty parent\n", encoding="utf-8")
    (dirty_parent / "note.txt").write_text("untracked\n", encoding="utf-8")

    dirty_submodule_parent = tmp_path / "dirty-submodule" / "Faber2026"
    init_repo(dirty_submodule_parent, "jakobtfaber/Faber2026")
    add_submodule(
        dirty_submodule_parent,
        analysis_source,
        "analysis",
        "jakobtfaber/Faber2026-analysis",
    )
    add_submodule(
        dirty_submodule_parent, pipeline_source, "pipeline", "jakobtfaber/dsa110-FLITS"
    )
    (dirty_submodule_parent / "pipeline" / "README.md").write_text(
        "# dirty pipeline\n", encoding="utf-8"
    )

    payload = run_inventory(tmp_path, tmp_path)
    dirty = dirty_by_path(payload)

    dirty_parent_detail = dirty[str(dirty_parent.resolve())]
    assert dirty_parent_detail["unstaged_file_paths"] == ["README.md"]
    assert dirty_parent_detail["untracked_file_paths"] == ["note.txt"]
    assert dirty_parent_detail["submodule_dirtiness"] == []

    clean_parent_dirty_submodule = dirty[str(dirty_submodule_parent.resolve())]
    assert clean_parent_dirty_submodule["staged_file_paths"] == []
    assert clean_parent_dirty_submodule["unstaged_file_paths"] == []
    assert clean_parent_dirty_submodule["untracked_file_paths"] == []
    assert clean_parent_dirty_submodule["submodule_dirtiness"][0]["path"] == "pipeline"

    bundles = bundle_by_parent(payload)
    assert bundles[str(dirty_parent.resolve())]["aggregate_dirty_status"] == "dirty"
    assert (
        bundles[str(dirty_submodule_parent.resolve())]["aggregate_dirty_status"]
        == "dirty"
    )


def test_independent_same_branch_clones_at_different_commits_and_local_unique_limits(
    tmp_path,
):
    clone_a = tmp_path / "clone-a"
    clone_b = tmp_path / "clone-b"
    init_repo(clone_a, "jakobtfaber/Faber2026")
    init_repo(clone_b, "jakobtfaber/Faber2026")
    head_a = write_commit(clone_a, "a.txt", "a\n", "a work")
    head_b = write_commit(clone_b, "b.txt", "b\n", "b work")
    git(clone_b, "tag", "locally-visible-copy", head_b)

    payload = run_inventory(tmp_path, clone_a, clone_b)
    assert payload["branch_divergence_groups"] == [
        {
            "repository": "jakobtfaber/Faber2026",
            "branch": "main",
            "checkout_paths": [str(clone_a.resolve()), str(clone_b.resolve())],
            "distinct_full_head_commits": sorted([head_a, head_b]),
            "locally_computable_reachability_relationships": [
                {
                    "left_checkout_path": str(clone_a.resolve()),
                    "left_full_head_commit": head_a,
                    "right_checkout_path": str(clone_b.resolve()),
                    "right_full_head_commit": head_b,
                    "relationship": "unrelated_or_not_locally_computable",
                    "checked_from_checkout_path": "",
                    "limits": "Computed only when one local checkout can see both commits; no network used.",
                }
            ],
        }
    ]
    triage = triage_by_path(payload)
    assert (
        triage[str(clone_a.resolve())]["facts"]["locally_unique_looking_full_commits"][
            -1
        ]
        == head_a
    )
    assert (
        "Local ancestry check only"
        in triage[str(clone_a.resolve())]["facts"]["locally_unique_looking_limits"]
    )
    assert (
        triage[str(clone_b.resolve())]["facts"]["locally_unique_looking_full_commits"]
        == []
    )


def test_missing_linked_registration_detached_checkout_and_checkout_kinds(tmp_path):
    repo = tmp_path / "Faber2026"
    head = init_repo(repo, "jakobtfaber/Faber2026")
    linked = tmp_path / "linked-review"
    git(repo, "worktree", "add", "-b", "feature/review", str(linked))
    linked_head = git(linked, "rev-parse", "HEAD")
    missing = tmp_path / "registered-missing"
    git(repo, "worktree", "add", "-b", "feature/missing", str(missing))
    shutil.rmtree(missing)
    detached = tmp_path / "Faber2026-analysis"
    detached_head = init_repo(detached, "jakobtfaber/Faber2026-analysis")
    git(detached, "checkout", "--detach", "HEAD")

    payload = run_inventory(tmp_path, tmp_path)
    triage = triage_by_path(payload)

    assert triage[str(repo.resolve())]["facts"]["checkout_kind"] == "standalone_clone"
    assert triage[str(linked.resolve())]["facts"]["checkout_kind"] == "linked_worktree"
    assert triage[str(detached.resolve())]["facts"]["checkout_kind"] == "detached"
    assert triage[str(detached.resolve())]["facts"]["full_head_commit"] == detached_head

    missing_detail = payload["missing_registration_details"]
    assert missing_detail == [
        {
            "registered_path": str(missing.resolve()),
            "branch_or_ref": "feature/missing",
            "pointed_to_commit": linked_head,
            "source_git_common_dir": str((repo / ".git").resolve()),
            "local_reachability_information": {
                "commit_object_available": True,
                "refs_containing_commit": [
                    "refs/heads/feature/missing",
                    "refs/heads/feature/review",
                    "refs/heads/main",
                    "refs/remotes/origin/main",
                ],
                "limits": "Checked only this local git common directory and its local refs; no network used.",
            },
            "missing_path_statement": "Missing path only means this registered worktree path was not found locally; this is not permission to prune it.",
        }
    ]
    assert head == linked_head


def test_ssh_https_normalization_incomplete_bundles_explicit_roots_and_path_hints(
    tmp_path,
):
    author_archive = tmp_path / "author-archive"
    codex_tmp = tmp_path / "codex-tmp"
    analysis = author_archive / "Faber2026-analysis"
    pipeline = codex_tmp / "pipeline-review"
    excluded = codex_tmp / "FLITS"
    init_repo(analysis, "jakobtfaber/Faber2026-analysis", remote_style="ssh")
    init_repo(pipeline, "jakobtfaber/dsa110-FLITS", remote_style="https")
    init_repo(excluded, "jakobtfaber/flits", remote_style="https")

    payload = run_inventory(tmp_path, author_archive, codex_tmp)
    bundles = payload["workspace_bundles"]
    assert {item["workspace_id"]: item["pin_match_status"] for item in bundles} == {
        str(analysis.resolve()): "missing_pin",
        str(pipeline.resolve()): "missing_pin",
    }
    assert all(
        "no_parent_checkout_seen" in " ".join(item["warnings"]) for item in bundles
    )

    triage = triage_by_path(payload)
    assert str(excluded.resolve()) not in triage
    assert (
        triage[str(analysis.resolve())]["facts"]["repository"]
        == "jakobtfaber/Faber2026-analysis"
    )
    assert (
        triage[str(pipeline.resolve())]["facts"]["repository"]
        == "jakobtfaber/dsa110-FLITS"
    )
    assert triage[str(analysis.resolve())]["facts"]["remote_github_slugs"] == [
        "jakobtfaber/Faber2026-analysis"
    ]
    assert triage[str(pipeline.resolve())]["facts"]["remote_github_slugs"] == [
        "jakobtfaber/dsa110-FLITS"
    ]
    assert any(
        evidence["basis"] == "pathname inference" and "author" in evidence["detail"]
        for evidence in triage[str(analysis.resolve())]["classification_evidence"]
    )
    assert any(
        evidence["basis"] == "pathname inference" and "codex" in evidence["detail"]
        for evidence in triage[str(pipeline.resolve())]["classification_evidence"]
    )
    assert payload["scan_roots"] == sorted(
        [str(author_archive.resolve()), str(codex_tmp.resolve())]
    )
    assert all("authority" not in json.dumps(item["facts"]) for item in triage.values())
    assert any(
        "authoritative is not inferable" in question
        for question in triage[str(analysis.resolve())]["unresolved_questions"]
    )


def test_submodule_checkout_kind_and_every_path_hint_is_labelled_pathname_inference(
    tmp_path,
):
    ci = load_inventory()
    for hint in (
        "tmp",
        "review",
        "publish",
        "recovery",
        "archive",
        "quarantine",
        "codex",
        "author",
    ):
        proposed, evidence = ci.hinted_classification(
            str(tmp_path / f"{hint}-surface" / "Faber2026")
        )
        assert proposed == "path_hint_review"
        assert {
            "basis": "pathname inference",
            "detail": (
                f"path contains '{hint}'; this can suggest review context only "
                "and does not establish authority"
            ),
        } in evidence

    analysis_source = tmp_path / "analysis-source"
    pipeline_source = tmp_path / "pipeline-source"
    init_repo(analysis_source, "jakobtfaber/Faber2026-analysis")
    init_repo(pipeline_source, "jakobtfaber/dsa110-FLITS")
    parent = tmp_path / "Faber2026"
    init_repo(parent, "jakobtfaber/Faber2026")
    add_submodule(parent, analysis_source, "analysis", "jakobtfaber/Faber2026-analysis")
    add_submodule(parent, pipeline_source, "pipeline", "jakobtfaber/dsa110-FLITS")

    payload = run_inventory(tmp_path, parent)
    triage = triage_by_path(payload)
    assert (
        triage[str((parent / "analysis").resolve())]["facts"]["checkout_kind"]
        == "submodule_checkout"
    )
    assert (
        triage[str((parent / "pipeline").resolve())]["facts"]["checkout_kind"]
        == "submodule_checkout"
    )


def test_nested_non_submodule_clone_is_not_reported_as_submodule_checkout(tmp_path):
    parent = tmp_path / "Faber2026"
    nested = parent / "nested-review" / "Faber2026-analysis"
    init_repo(parent, "jakobtfaber/Faber2026")
    init_repo(nested, "jakobtfaber/Faber2026-analysis")

    payload = run_inventory(tmp_path, parent)
    triage = triage_by_path(payload)

    nested_facts = triage[str(nested.resolve())]["facts"]
    assert nested_facts["checkout_kind"] == "standalone_clone"
    assert any(
        evidence["basis"] == "pathname inference" and "review" in evidence["detail"]
        for evidence in triage[str(nested.resolve())]["classification_evidence"]
    )
    bundles = bundle_by_parent(payload)
    assert bundles[str(parent.resolve())]["analysis_checkout"] is None
    assert bundles[str(parent.resolve())]["pin_match_status"] == "unavailable"
    standalone_bundle = {
        item["workspace_id"]: item for item in payload["workspace_bundles"]
    }[str(nested.resolve())]
    assert standalone_bundle["parent_checkout"] is None
    assert standalone_bundle["analysis_checkout"] == str(nested.resolve())
    assert standalone_bundle["pin_match_status"] == "missing_pin"


def test_broken_and_nonexistent_scan_roots_are_reported_in_triage(tmp_path):
    broken = tmp_path / "broken"
    broken.mkdir()
    (broken / ".git").write_text("gitdir: /does/not/exist\n", encoding="utf-8")
    missing = tmp_path / "missing-root"

    payload = run_inventory(tmp_path, broken, missing)
    triage = triage_by_path(payload)

    assert triage[str(broken.resolve())]["facts"] == {
        "scan_problem_classification": "broken_checkout",
        "scan_problem_detail": "git metadata found but git rev-parse failed",
        "repository": None,
        "checkout_kind": None,
    }
    assert (
        triage[str(missing)]["facts"]["scan_problem_classification"]
        == "inaccessible_path"
    )
    assert payload["scan_problems"] == [
        {
            "path": str(broken.resolve()),
            "classification": "broken_checkout",
            "detail": "git metadata found but git rev-parse failed",
        },
        {
            "path": str(missing),
            "classification": "inaccessible_path",
            "detail": "scan root does not exist",
        },
    ]
    assert payload["warnings"] == [
        f"broken_checkout:{broken.resolve()}",
        f"inaccessible_path:{missing}",
    ]


def test_html_renders_all_schema_arrays_and_detailed_dirt(tmp_path):
    repo = tmp_path / "Faber2026"
    init_repo(repo, "jakobtfaber/Faber2026")
    (repo / "README.md").write_text("# dirty\n", encoding="utf-8")
    (repo / "loose.txt").write_text("loose\n", encoding="utf-8")

    payload = run_inventory(tmp_path, repo)
    html = payload["_html"]
    for heading in (
        "workspace_bundles",
        "checkout_triage",
        "branch_divergence_groups",
        "dirty_checkout_details",
        "missing_registration_details",
        "warnings",
        "scan_problems",
    ):
        assert heading in html
    assert "unstaged_file_paths" in html
    assert "untracked_file_paths" in html
    assert "README.md" in html
    assert "loose.txt" in html
    forbidden = ("prunable", "obsolete", "disposable", "abandoned", "safe-to-delete")
    assert not any(word in html.lower() for word in forbidden)
    assert not any(word in json.dumps(payload).lower() for word in forbidden)


def test_command_recorder_proves_inventory_uses_no_mutating_or_network_git(
    tmp_path, monkeypatch
):
    repo = tmp_path / "Faber2026"
    init_repo(repo, "jakobtfaber/Faber2026")
    ci = load_inventory()
    real_run = ci.subprocess.run
    seen: list[list[str]] = []

    def recording_run(cmd, *args, **kwargs):
        if isinstance(cmd, list) and cmd and Path(cmd[0]).name == "git":
            seen.append(cmd)
            assert kwargs["env"]["GIT_OPTIONAL_LOCKS"] == "0"
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(ci.subprocess, "run", recording_run)
    out_json = tmp_path / "inventory.json"
    out_html = tmp_path / "inventory.html"
    assert (
        ci.main(
            [
                "--scan-root",
                str(tmp_path),
                "--json-out",
                str(out_json),
                "--html-out",
                str(out_html),
            ]
        )
        == 0
    )

    forbidden = {
        "add",
        "am",
        "apply",
        "checkout",
        "clean",
        "clone",
        "commit",
        "fetch",
        "gc",
        "ls-remote",
        "merge",
        "mv",
        "pull",
        "push",
        "rebase",
        "reset",
        "restore",
        "rm",
        "remote update",
        "stash",
        "switch",
        "worktree add",
        "worktree move",
        "worktree prune",
        "worktree remove",
        "worktree repair",
        "submodule add",
        "submodule update",
    }

    def git_subcommand(cmd: list[str]) -> str:
        i = 1
        while i < len(cmd):
            part = cmd[i]
            if part in {"-C", "-c", "--git-dir", "--work-tree"}:
                i += 2
                continue
            if part.startswith("--git-dir=") or part.startswith("--work-tree="):
                i += 1
                continue
            if part.startswith("-"):
                i += 1
                continue
            if part in {"worktree", "submodule"} and i + 1 < len(cmd):
                return f"{part} {cmd[i + 1]}"
            return part
        return ""

    observed = [git_subcommand(cmd) for cmd in seen]
    assert not (set(observed) & forbidden)
    assert not ci.git_args_allowed(["gc"])
    assert not ci.git_args_allowed(["remote", "update"])


def test_output_inside_discovered_checkout_rejected_and_override_allowed(tmp_path):
    repo = tmp_path / "Faber2026"
    init_repo(repo, "jakobtfaber/Faber2026")
    ci = load_inventory()

    with pytest.raises(SystemExit) as error:
        ci.main(
            [
                "--scan-root",
                str(tmp_path),
                "--json-out",
                str(repo / "inventory.json"),
                "--html-out",
                str(tmp_path / "inventory.html"),
            ]
        )
    assert "refusing to write output inside discovered Git checkout" in str(error.value)

    assert (
        ci.main(
            [
                "--scan-root",
                str(tmp_path),
                "--json-out",
                str(repo / "inventory.json"),
                "--html-out",
                str(repo / "inventory.html"),
                "--allow-repo-output",
            ]
        )
        == 0
    )
    assert (repo / "inventory.json").exists()
    assert (repo / "inventory.html").exists()


def test_nested_symlink_checkout_escape_is_not_scanned(tmp_path):
    scan_root = tmp_path / "scan"
    scan_root.mkdir()
    external = tmp_path / "external" / "Faber2026"
    init_repo(external, "jakobtfaber/Faber2026")
    (scan_root / "linked").symlink_to(external, target_is_directory=True)

    payload = run_inventory(tmp_path, scan_root)

    assert str(external.resolve()) not in triage_by_path(payload)
    assert payload["workspace_bundles"] == []


def test_missing_checkout_pin_status_for_recorded_submodule_without_checkout(tmp_path):
    analysis_source = tmp_path / "analysis-source"
    init_repo(analysis_source, "jakobtfaber/Faber2026-analysis")
    parent = tmp_path / "Faber2026"
    init_repo(parent, "jakobtfaber/Faber2026")
    add_submodule(parent, analysis_source, "analysis", "jakobtfaber/Faber2026-analysis")
    shutil.rmtree(parent / "analysis")

    payload = run_inventory(tmp_path, parent)
    bundle = bundle_by_parent(payload)[str(parent.resolve())]

    assert bundle["analysis_checkout"] is None
    assert bundle["parent_recorded_analysis_pin"] is not None
    assert bundle["pin_match_status"] == "missing_checkout"


def test_schema_version_tool_version_schema_uri_and_schema_file(tmp_path):
    repo = tmp_path / "Faber2026"
    init_repo(repo, "jakobtfaber/Faber2026")

    payload = run_inventory(tmp_path, repo)
    schema_path = ROOT / "schemas" / "checkout-inventory-v2.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    assert payload["schema_version"] == 2
    assert payload["tool_version"] == "2.0.0"
    assert payload["schema_uri"] == schema["$id"]
    assert "scan_timestamp" not in payload
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["properties"]["schema_version"]["const"] == 2
    for key in (
        "scan_roots",
        "warnings",
        "scan_problems",
        "workspace_bundles",
        "checkout_triage",
        "branch_divergence_groups",
        "dirty_checkout_details",
        "missing_registration_details",
    ):
        assert key in schema["required"]
        assert schema["properties"][key]["type"] == "array"


def test_html_escapes_untrusted_values(tmp_path):
    repo = tmp_path / "Faber<script>2026"
    init_repo(repo, "jakobtfaber/Faber2026")

    payload = run_inventory(tmp_path, repo)
    html = payload["_html"]

    assert "&lt;script&gt;" in html
    assert "<script>" not in html


def test_repeated_outputs_are_byte_deterministic(tmp_path):
    repo = tmp_path / "Faber2026"
    init_repo(repo, "jakobtfaber/Faber2026")

    payload_a, json_a, html_a = inventory_outputs(tmp_path / "a", repo)
    payload_b, json_b, html_b = inventory_outputs(tmp_path / "b", repo)

    assert payload_a == payload_b
    assert json_a == json_b
    assert html_a == html_b


def test_help_exits_zero_and_mentions_required_arguments(capsys):
    ci = load_inventory()
    with pytest.raises(SystemExit) as error:
        ci.main(["--help"])
    assert error.value.code == 0
    output = capsys.readouterr().out
    assert "--scan-root" in output
    assert "--json-out" in output
    assert "--html-out" in output
    assert "--allow-repo-output" in output


def test_local_upstream_and_ahead_behind_are_local_only(tmp_path):
    repo = tmp_path / "Faber2026"
    init_repo(repo, "jakobtfaber/Faber2026")
    git(repo, "branch", "--set-upstream-to=origin/main", "main")
    write_commit(repo, "ahead.txt", "ahead\n", "ahead")

    payload = run_inventory(tmp_path, repo)
    facts = triage_by_path(payload)[str(repo.resolve())]["facts"]

    assert facts["git_dir"] == str((repo / ".git").resolve())
    assert facts["git_common_dir"] == str((repo / ".git").resolve())
    assert facts["local_upstream"] == {
        "has_upstream": True,
        "upstream": "origin/main",
        "upstream_ref": "refs/remotes/origin/main",
        "ahead": 1,
        "behind": 0,
        "state": "locally_computed",
        "limits": "Computed from local refs only; no network fetch or remote query used.",
    }


def test_missing_upstream_is_represented_without_abort(tmp_path):
    repo = tmp_path / "Faber2026"
    init_repo(repo, "jakobtfaber/Faber2026")

    payload = run_inventory(tmp_path, repo)
    facts = triage_by_path(payload)[str(repo.resolve())]["facts"]

    assert facts["local_upstream"] == {
        "has_upstream": False,
        "upstream": None,
        "upstream_ref": None,
        "ahead": None,
        "behind": None,
        "state": "missing_upstream",
        "limits": "Computed from local refs only; no network fetch or remote query used.",
    }
