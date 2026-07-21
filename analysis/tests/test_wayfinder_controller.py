from __future__ import annotations

import importlib.util
import fcntl
import json
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


def test_manifest_has_reviewed_first_wave():
    wc = load_controller()
    manifest = wc.load_manifest(ROOT / "docs/rse/control/wayfinder-automation.toml")
    assert manifest.max_parallel == 2
    assert [task.id for task in wc.tasks_for_wave(manifest, "first")] == [
        "fail-close-expanded-catalog",
        "freeze-candidate-redshifts",
        "audit-results-library-conflicts",
        "correct-census-wording",
        "retire-stage-codes",
    ]


def test_manifest_rejects_unsafe_branch_and_mode(tmp_path):
    wc = load_controller()
    manifest = tmp_path / "bad.toml"
    manifest.write_text(
        """
[controller]
repo = "owner/repo"
base_branch = "main"
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
depends_on = []
instructions = "bad"
""",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="branch"):
        wc.load_manifest(manifest)


def test_dependency_plan_is_fail_closed(tmp_path):
    wc = load_controller()
    manifest = wc.load_manifest(ROOT / "docs/rse/control/wayfinder-automation.toml")
    state = wc.empty_state(manifest)
    ready = wc.ready_tasks(manifest, state, "second")
    assert ready == []
    state["tasks"]["fail-close-expanded-catalog"]["status"] = "resolved"
    state["tasks"]["freeze-candidate-redshifts"]["status"] = "resolved"
    state["tasks"]["audit-results-library-conflicts"]["status"] = "review_ready"
    assert [task.id for task in wc.ready_tasks(manifest, state, "second")] == [
        "review-trust-ledger",
        "review-count-audit",
    ]


def test_state_write_is_atomic_json(tmp_path):
    wc = load_controller()
    target = tmp_path / "state.json"
    payload = {"version": 1, "tasks": {"x": {"status": "queued"}}}
    wc.write_json_atomic(target, payload)
    assert json.loads(target.read_text()) == payload
    assert not (tmp_path / "state.json.tmp").exists()


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
        "pr_url": "https://github.com/jakobtfaber/Faber2026/pull/1",
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
    state["supervisor"] = {"pid": wc.os.getpid(), "wave": "first", "status": "starting"}
    wc.save_state(manifest, state)

    def fail_spawn(*args, **kwargs):
        raise OSError("spawn failed")

    monkeypatch.setattr(wc.subprocess, "Popen", fail_spawn)
    with pytest.raises(OSError, match="spawn failed"):
        wc.supervise(manifest, "first")
    current = wc.load_state(manifest)
    assert current["supervisor"]["status"] == "initializing"
