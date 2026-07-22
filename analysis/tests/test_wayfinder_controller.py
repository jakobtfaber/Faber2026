from __future__ import annotations

import importlib.util
import fcntl
import json
import subprocess
import sys
import threading
import time
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load_controller():
    spec = importlib.util.spec_from_file_location(
        "wayfinder_controller", ROOT / "scripts/wayfinder_controller.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_manifest_has_analysis_specific_controller_roots():
    wc = load_controller()
    manifest = wc.load_manifest(ROOT / "docs/rse/control/wayfinder-automation.toml")
    assert manifest.repo == "jakobtfaber/Faber2026-analysis"
    assert (
        manifest.state_dir
        == Path("~/.local/state/Faber2026-analysis/wayfinder-controller").expanduser()
    )
    assert (
        manifest.worktree_root
        == Path(
            "~/Developer/scratch/worktrees/Faber2026-analysis-wayfinder-auto"
        ).expanduser()
    )
    assert manifest.max_parallel == 4
    assert len(wc.tasks_for_wave(manifest, "first")) == 6


def test_manifest_represents_expanded_foreground_active_graph_and_history():
    wc = load_controller()
    manifest = wc.load_manifest(ROOT / "docs/rse/control/wayfinder-automation.toml")
    assert manifest.ticket_glob == (
        "docs/rse/wayfinder/tickets/expanded-foreground-catalog-repair-*.md"
    )
    assert {Path(task.ticket).name for task in manifest.tasks} == {
        f"expanded-foreground-catalog-repair-{number:02d}-{slug}.md"
        for number, slug in [
            (4, "set-figure-3-gate"),
            (5, "set-independent-validation-gate"),
            (9, "repeat-redshift-source-verification"),
            (15, "freeze-protected-nine-sightline-query-evidence"),
            (16, "independently-replay-nine-sightline-query-corpus"),
            (19, "adjudicate-host-redshift-differences"),
        ]
    }
    assert {Path(item.ticket).name for item in manifest.history} == {
        f"expanded-foreground-catalog-repair-{number:02d}-{slug}.md"
        for number, slug in [
            (1, "fail-close-validation"),
            (2, "set-crossmatch-contract"),
            (3, "set-physics-authority"),
            (6, "verify-redshift-verdicts"),
            (7, "freeze-host-redshift-provenance"),
            (8, "freeze-candidate-redshift-provenance"),
            (10, "restore-knowledge-base-launcher"),
            (11, "resolve-zach-intercatalog-redshift"),
            (12, "expand-nine-sightline-catalogs"),
            (13, "set-nine-sightline-search-contract"),
            (14, "freeze-anonymous-nine-sightline-query-corpus"),
            (17, "obtain-authoritative-host-redshift-ledger"),
            (18, "source-zach-whitney-host-redshifts"),
        ]
    }
    wc.validate_manifest_ticket_graph(manifest, ROOT)


def test_manifest_graph_rejects_coverage_dependency_and_execution_drift():
    wc = load_controller()
    manifest = wc.load_manifest(ROOT / "docs/rse/control/wayfinder-automation.toml")

    with pytest.raises(ValueError, match="coverage mismatch"):
        wc.validate_manifest_ticket_graph(
            replace(manifest, tasks=manifest.tasks[1:]), ROOT
        )

    task = next(
        item for item in manifest.tasks if item.id == "set-expanded-figure3-gate"
    )
    drifted = replace(task, depends_on=())
    tasks = tuple(drifted if item.id == task.id else item for item in manifest.tasks)
    with pytest.raises(ValueError, match="dependency mismatch"):
        wc.validate_manifest_ticket_graph(replace(manifest, tasks=tasks), ROOT)

    hitl = next(item for item in manifest.tasks if item.execution == "hitl")
    drifted = replace(hitl, execution="afk")
    tasks = tuple(drifted if item.id == hitl.id else item for item in manifest.tasks)
    with pytest.raises(ValueError, match="execution mismatch"):
        wc.validate_manifest_ticket_graph(replace(manifest, tasks=tasks), ROOT)

    cross_repo = replace(manifest.tasks[0], repo="jakobtfaber/Faber2026")
    tasks = (cross_repo, *manifest.tasks[1:])
    with pytest.raises(ValueError, match="cross-repository"):
        wc.validate_manifest_ticket_graph(replace(manifest, tasks=tasks), ROOT)


def test_hitl_tasks_are_never_ready_or_directly_runnable(tmp_path):
    wc = load_controller()
    manifest = wc.load_manifest(ROOT / "docs/rse/control/wayfinder-automation.toml")
    manifest = replace(manifest, state_dir=tmp_path)
    state = wc.empty_state(manifest)
    hitl = next(item for item in manifest.tasks if item.execution == "hitl")

    assert hitl not in wc.ready_tasks(manifest, state, hitl.wave)
    with pytest.raises(RuntimeError, match="HITL"):
        wc.run_task(manifest, hitl, "1" * 32)


def test_plan_labels_hitl_as_owner_facing(capsys):
    wc = load_controller()
    manifest = wc.load_manifest(ROOT / "docs/rse/control/wayfinder-automation.toml")

    assert wc.print_plan(manifest, "first") == 0
    output = capsys.readouterr().out
    assert "freeze-protected-query-evidence: queued" in output
    assert "execution=hitl" in output


def test_manifest_rejects_unsafe_branch_and_mode(tmp_path):
    wc = load_controller()
    manifest = tmp_path / "bad.toml"
    manifest.write_text(
        """
[controller]
repo = "owner/repo"
base_branch = "main"
ticket_glob = "tickets/*.md"
state_dir = "~/.local/state/test"
model = "gpt-5.5"
reasoning_effort = "medium"
max_parallel = 1
timeout_seconds = 60

[[task]]
id = "bad"
wave = "first"
ticket = "ticket.md"
branch = "main"
mode = "delete"
execution = "afk"
repo = "owner/repo"
depends_on = []
instructions = "bad"

[[history]]
id = "old"
ticket = "old.md"
execution = "afk"
depends_on = []
status = "resolved"
""",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="branch"):
        wc.load_manifest(manifest)


def test_dependency_plan_is_fail_closed(tmp_path):
    wc = load_controller()
    manifest = wc.load_manifest(ROOT / "docs/rse/control/wayfinder-automation.toml")
    state = wc.empty_state(manifest)
    ready = {task.id for task in wc.ready_tasks(manifest, state, "first")}
    assert ready == set()
    assert "freeze-protected-query-evidence" not in ready
    assert "replay-nine-sightline-query-corpus" not in ready


def test_pass_only_ticket_cannot_resolve_as_no_go():
    wc = load_controller()
    no_go = """\
# Gate

- Status: resolved
- Resolution gate: pass-only
- Gate outcome: no-go
"""
    passed = no_go.replace("no-go", "pass")

    assert not wc.ticket_resolution_satisfies(no_go)
    assert wc.ticket_resolution_satisfies(passed)


def test_required_pass_blocker_is_enforced_before_worktree_setup(tmp_path):
    wc = load_controller()
    tickets = tmp_path / "tickets"
    tickets.mkdir()
    upstream = tickets / "upstream.md"
    downstream = tickets / "downstream.md"
    upstream.write_text(
        "# Upstream\n\n- Status: open\n- Resolution gate: pass-only\n"
        "- Gate outcome: no-go\n",
        encoding="utf-8",
    )
    downstream.write_text(
        "# Downstream\n\n- Status: open\n"
        "- Blocked by: [Upstream](upstream.md) (requires `pass`)\n",
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="requires pass"):
        wc.ensure_ticket_blockers_satisfied(downstream.relative_to(tmp_path), tmp_path)

    upstream.write_text(
        "# Upstream\n\n- Status: resolved\n- Resolution gate: pass-only\n"
        "- Gate outcome: pass\n",
        encoding="utf-8",
    )
    wc.ensure_ticket_blockers_satisfied(downstream.relative_to(tmp_path), tmp_path)


def test_ordinary_ticket_blocker_is_enforced_before_worktree_setup(tmp_path):
    wc = load_controller()
    tickets = tmp_path / "tickets"
    tickets.mkdir()
    upstream = tickets / "upstream.md"
    downstream = tickets / "downstream.md"
    upstream.write_text("# Upstream\n\n- Status: open\n", encoding="utf-8")
    downstream.write_text(
        "# Downstream\n\n- Status: open\n- Blocked by: [Upstream](upstream.md)\n",
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="requires resolution"):
        wc.ensure_ticket_blockers_satisfied(downstream.relative_to(tmp_path), tmp_path)

    upstream.write_text("# Upstream\n\n- Status: resolved\n", encoding="utf-8")
    wc.ensure_ticket_blockers_satisfied(downstream.relative_to(tmp_path), tmp_path)


def test_required_pass_blocker_uses_explicit_remote_ref(monkeypatch, tmp_path):
    wc = load_controller()
    downstream = (
        "# Downstream\n\n- Status: open\n"
        "- Blocked by: [Upstream](upstream.md) (requires `pass`)\n"
    )
    upstream_no_go = (
        "# Upstream\n\n- Status: resolved\n- Resolution gate: pass-only\n"
        "- Gate outcome: no-go\n"
    )

    def fake_git(_repo, *args, **_kwargs):
        assert args[0] == "show"
        text = (
            downstream if args[1].endswith(":tickets/downstream.md") else upstream_no_go
        )
        return SimpleNamespace(returncode=0, stdout=text)

    monkeypatch.setattr(wc, "_git", fake_git)
    with pytest.raises(RuntimeError, match="requires pass"):
        wc.ensure_ticket_blockers_satisfied(
            Path("tickets/downstream.md"), tmp_path, ref="origin/main"
        )


def test_state_write_is_atomic_json(tmp_path):
    wc = load_controller()
    target = tmp_path / "state.json"
    payload = {"version": 1, "tasks": {"x": {"status": "queued"}}}
    wc.write_json_atomic(target, payload)
    assert json.loads(target.read_text()) == payload
    assert not (tmp_path / "state.json.tmp").exists()


def test_load_state_rejects_identity_mismatch(tmp_path):
    wc = load_controller()
    manifest = wc.load_manifest(ROOT / "docs/rse/control/wayfinder-automation.toml")
    manifest = replace(manifest, state_dir=tmp_path, path=tmp_path / "current.toml")
    state = wc.empty_state(manifest)
    state["identity"]["repo"] = "jakobtfaber/Faber2026"
    wc.write_json_atomic(tmp_path / "state.json", state)

    with pytest.raises(ValueError, match="state identity mismatch"):
        wc.load_state(manifest)


def test_load_state_accepts_ticket_graph_evolution(tmp_path):
    wc = load_controller()
    manifest = wc.load_manifest(ROOT / "docs/rse/control/wayfinder-automation.toml")
    manifest = replace(manifest, state_dir=tmp_path)
    state = wc.empty_state(manifest)
    stale_task = {
        "status": "resolved",
        "pid": None,
        "attempt_id": "prior",
        "updated_at": None,
        "detail": "preserved",
    }
    state["tasks"]["prior-resolved-task"] = stale_task
    wc.write_json_atomic(tmp_path / "state.json", state)

    loaded = wc.load_state(manifest)

    assert loaded["tasks"]["prior-resolved-task"] == stale_task


def test_repository_and_worktree_identity_mismatches_are_rejected(tmp_path):
    wc = load_controller()
    manifest = wc.load_manifest(ROOT / "docs/rse/control/wayfinder-automation.toml")

    wrong_origin = tmp_path / "wrong-origin"
    wrong_origin.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=wrong_origin, check=True)
    subprocess.run(
        ["git", "remote", "add", "origin", "https://github.com/other/repo.git"],
        cwd=wrong_origin,
        check=True,
    )
    with pytest.raises(RuntimeError, match="origin repository mismatch"):
        wc.validate_repository_identity(manifest, wrong_origin)

    unrelated = tmp_path / "unrelated"
    unrelated.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=unrelated, check=True)
    subprocess.run(
        [
            "git",
            "remote",
            "add",
            "origin",
            "https://github.com/jakobtfaber/Faber2026-analysis.git",
        ],
        cwd=unrelated,
        check=True,
    )
    with pytest.raises(RuntimeError, match="worktree repository mismatch"):
        wc.validate_worktree_identity(manifest, unrelated, ROOT)


def test_receipt_policy_distinguishes_resolution_from_review(tmp_path):
    wc = load_controller()
    resolved = {
        "attempt_id": "1" * 32,
        "outcome": "resolved",
        "summary": "done",
        "branch": "codex/auto-x",
        "commit": "a" * 40,
        "pr_url": "https://github.com/owner/repo/pull/1",
        "checks": ["tests"],
        "blocker": "",
    }
    assert wc.validate_receipt(resolved, "resolve")["outcome"] == "resolved"
    with pytest.raises(ValueError, match="review_ready"):
        wc.validate_receipt(resolved, "review")


def test_codex_command_closes_stdin_and_uses_schema(monkeypatch, tmp_path):
    wc = load_controller()
    monkeypatch.setattr(
        wc.shutil,
        "which",
        lambda name: f"/usr/bin/{name}" if name in {"timeout", "codex"} else None,
    )
    manifest = wc.load_manifest(ROOT / "docs/rse/control/wayfinder-automation.toml")
    task = manifest.tasks[0]
    command = wc.codex_command(
        manifest, task, tmp_path, tmp_path / "receipt.json", ROOT
    )
    assert command[0].endswith("timeout") or command[0].endswith("gtimeout")
    assert any(Path(part).name == "codex" for part in command)
    assert "--output-schema" in command
    assert "--output-last-message" in command
    assert "danger-full-access" in command


def test_resolved_outcome_requires_remote_checks(monkeypatch, tmp_path):
    wc = load_controller()
    manifest = wc.load_manifest(ROOT / "docs/rse/control/wayfinder-automation.toml")
    task = manifest.tasks[0]
    receipt = {
        "attempt_id": "1" * 32,
        "outcome": "resolved",
        "summary": "done",
        "branch": task.branch,
        "commit": "a" * 40,
        "pr_url": "https://github.com/jakobtfaber/Faber2026/pull/999",
        "checks": ["tests"],
        "blocker": "",
    }
    monkeypatch.setattr(wc, "remote_resolution_evidence", lambda *_: (False, "PR open"))
    status, detail = wc.classify_receipt(manifest, task, receipt, ROOT)
    assert status == "needs_attention"
    assert detail == "PR open"


def test_existing_process_uses_recorded_exit_after_restart(monkeypatch, tmp_path):
    wc = load_controller()
    exit_path = tmp_path / "runner-exit.json"
    process = wc.ExistingProcess(1234, exit_path, "1" * 32)
    monkeypatch.setattr(wc, "process_alive", lambda _pid: True)
    assert process.poll() is None
    monkeypatch.setattr(wc, "process_alive", lambda _pid: False)
    assert process.poll() == 2
    exit_path.write_text(
        '{"attempt_id": "' + "1" * 32 + '", "returncode": 0}\n',
        encoding="utf-8",
    )
    assert process.poll() == 0


def test_worker_prompt_preserves_manual_gates():
    wc = load_controller()
    manifest = wc.load_manifest(ROOT / "docs/rse/control/wayfinder-automation.toml")
    prompt = wc.task_prompt(manifest, manifest.tasks[0], "1" * 32)
    assert "Never delete or move data" in prompt
    assert "promote scientific trust" in prompt
    assert "re-adjudicate foreground redshifts/budgets" in prompt
    assert "Stop fail-closed" in prompt


def test_attempt_mismatch_is_never_accepted(tmp_path):
    wc = load_controller()
    manifest = wc.load_manifest(ROOT / "docs/rse/control/wayfinder-automation.toml")
    task = manifest.tasks[0]
    receipt = {
        "attempt_id": "1" * 32,
        "outcome": "blocked",
        "summary": "blocked",
        "branch": task.branch,
        "commit": "",
        "pr_url": "",
        "checks": [],
        "blocker": "evidence missing",
    }
    status, detail = wc.classify_receipt(
        manifest, task, receipt, ROOT, expected_attempt="2" * 32
    )
    assert status == "needs_attention"
    assert "attempt" in detail


def test_retry_only_resets_nonrunning_terminal_task(tmp_path):
    wc = load_controller()
    manifest = wc.load_manifest(ROOT / "docs/rse/control/wayfinder-automation.toml")
    manifest = replace(manifest, state_dir=tmp_path)
    state = wc.empty_state(manifest)
    state["tasks"][manifest.tasks[0].id]["status"] = "blocked"
    wc.save_state(manifest, state)
    wc.retry_task(manifest, manifest.tasks[0].id)
    assert wc.load_state(manifest)["tasks"][manifest.tasks[0].id]["status"] == "queued"
    state = wc.load_state(manifest)
    state["tasks"][manifest.tasks[0].id]["status"] = "running"
    wc.save_state(manifest, state)
    with pytest.raises(RuntimeError, match="running"):
        wc.retry_task(manifest, manifest.tasks[0].id)
    state = wc.load_state(manifest)
    state["tasks"][manifest.tasks[0].id]["status"] = "starting"
    wc.save_state(manifest, state)
    with pytest.raises(RuntimeError, match="starting"):
        wc.retry_task(manifest, manifest.tasks[0].id)


def test_concurrent_launch_is_rejected_before_spawn(monkeypatch, tmp_path):
    wc = load_controller()
    manifest = wc.load_manifest(ROOT / "docs/rse/control/wayfinder-automation.toml")
    manifest = replace(manifest, state_dir=tmp_path)
    monkeypatch.setattr(wc, "ensure_controller_is_merged", lambda *_: None)
    lock_path = tmp_path / "launch.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w") as held:
        fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(RuntimeError, match="launch is in progress"):
            wc.launch(manifest, "first")


def test_task_lock_prevents_duplicate_worker(tmp_path):
    wc = load_controller()
    manifest = wc.load_manifest(ROOT / "docs/rse/control/wayfinder-automation.toml")
    manifest = replace(manifest, state_dir=tmp_path)
    task = manifest.tasks[0]
    lock_path = tmp_path / "tasks" / task.id / "task.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w") as held:
        fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(RuntimeError, match="live runner"):
            wc.run_task(manifest, task, "1" * 32)


def test_repository_lock_serializes_parallel_worktree_setup(tmp_path):
    wc = load_controller()
    manifest = wc.load_manifest(ROOT / "docs/rse/control/wayfinder-automation.toml")
    manifest = replace(manifest, state_dir=tmp_path)
    entered = threading.Event()

    def wait_for_lock():
        with wc.repository_mutation_lock(manifest):
            entered.set()

    with wc.repository_mutation_lock(manifest):
        contender = threading.Thread(target=wait_for_lock)
        contender.start()
        time.sleep(0.05)
        assert not entered.is_set()
    contender.join(timeout=1)
    assert entered.is_set()


def test_launch_rejects_supervisor_that_exits_immediately(monkeypatch, tmp_path):
    wc = load_controller()
    manifest = wc.load_manifest(ROOT / "docs/rse/control/wayfinder-automation.toml")
    manifest = replace(manifest, state_dir=tmp_path)
    monkeypatch.setattr(wc, "ensure_controller_is_merged", lambda *_: None)

    class FailedProcess:
        pid = 4321

        def poll(self):
            return 2

    monkeypatch.setattr(wc.subprocess, "Popen", lambda *args, **kwargs: FailedProcess())
    with pytest.raises(RuntimeError, match="exited during launch"):
        wc.launch(manifest, "first")


def test_remote_pr_is_bound_to_repo_head_and_check_names(monkeypatch):
    wc = load_controller()
    manifest = wc.load_manifest(ROOT / "docs/rse/control/wayfinder-automation.toml")
    task = manifest.tasks[0]
    receipt = {
        "attempt_id": "1" * 32,
        "outcome": "resolved",
        "summary": "done",
        "branch": task.branch,
        "commit": "a" * 40,
        "pr_url": "https://github.com/jakobtfaber/Faber2026-analysis/pull/1",
        "checks": ["root-science-tests"],
        "blocker": "",
    }
    pr = {
        "state": "MERGED",
        "baseRefName": "main",
        "headRefName": task.branch,
        "headRefOid": "b" * 40,
        "statusCheckRollup": [
            {
                "name": "root-science-tests",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
            }
        ],
    }
    monkeypatch.setattr(
        wc,
        "_run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=json.dumps(pr)),
    )
    ok, detail = wc.remote_pr_evidence(manifest, task, receipt, "MERGED", ROOT)
    assert not ok
    assert detail == "receipt commit differs from PR head"
    receipt["pr_url"] = "https://github.com/someone/else/pull/1"
    ok, detail = wc.remote_pr_evidence(manifest, task, receipt, "MERGED", ROOT)
    assert not ok
    assert detail == "PR URL repository differs from manifest"


def test_supervisor_does_not_signal_running_before_first_spawn(monkeypatch, tmp_path):
    wc = load_controller()
    manifest = wc.load_manifest(ROOT / "docs/rse/control/wayfinder-automation.toml")
    manifest = replace(manifest, state_dir=tmp_path)
    state = wc.empty_state(manifest)
    state["tasks"]["freeze-protected-query-evidence"]["status"] = "resolved"
    state["supervisor"] = {
        "pid": wc.os.getpid(),
        "wave": "first",
        "status": "starting",
    }
    wc.save_state(manifest, state)

    def fail_spawn(*args, **kwargs):
        raise OSError("spawn failed")

    monkeypatch.setattr(wc.subprocess, "Popen", fail_spawn)
    with pytest.raises(OSError, match="spawn failed"):
        wc.supervise(manifest, "first")
    current = wc.load_state(manifest)
    assert current["supervisor"]["status"] == "initializing"
