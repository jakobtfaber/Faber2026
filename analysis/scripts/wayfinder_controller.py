#!/usr/bin/env python3
"""Durable, fail-closed execution controller for reviewed Wayfinder tickets."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import time
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from scripts.wayfinder_state import parse_ticket_text, ticket_clears_dependency
except (
    ModuleNotFoundError
):  # direct ``python scripts/wayfinder_controller.py`` execution
    from wayfinder_state import parse_ticket_text, ticket_clears_dependency


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "docs/rse/control/wayfinder-automation.toml"
RECEIPT_SCHEMA = ROOT / "scripts/wayfinder_receipt.schema.json"
TERMINAL_STATUSES = {
    "resolved",
    "review_ready",
    "blocked",
    "failed",
    "needs_attention",
}
RECEIPT_OUTCOMES = {"resolved", "review_ready", "blocked", "failed"}
MODES = {"resolve", "review"}
EXECUTIONS = {"afk", "hitl"}


@dataclass(frozen=True)
class Task:
    id: str
    wave: str
    ticket: str
    branch: str
    mode: str
    depends_on: tuple[str, ...]
    expected_artifact: str
    instructions: str
    execution: str
    repo: str


@dataclass(frozen=True)
class History:
    id: str
    ticket: str
    execution: str
    depends_on: tuple[str, ...]
    status: str


@dataclass(frozen=True)
class Manifest:
    repo: str
    base_branch: str
    state_dir: Path
    worktree_root: Path
    model: str
    reasoning_effort: str
    max_parallel: int
    timeout_seconds: int
    tasks: tuple[Task, ...]
    history: tuple[History, ...]
    ticket_glob: str
    path: Path


@dataclass
class ExistingProcess:
    """Poll a detached task runner after its original supervisor has exited."""

    pid: int
    exit_path: Path
    attempt_id: str

    def poll(self) -> int | None:
        if process_alive(self.pid):
            return None
        if not self.exit_path.exists():
            return 2
        record = json.loads(self.exit_path.read_text(encoding="utf-8"))
        if record.get("attempt_id") != self.attempt_id:
            return 2
        return int(record.get("returncode", 2))


def _required(mapping: dict[str, Any], key: str, context: str) -> Any:
    if key not in mapping:
        raise ValueError(f"{context} missing {key}")
    return mapping[key]


def load_manifest(path: Path = DEFAULT_MANIFEST) -> Manifest:
    path = path.resolve()
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    control = _required(raw, "controller", "manifest")
    task_rows = _required(raw, "task", "manifest")
    history_rows = _required(raw, "history", "manifest")
    base_branch = str(_required(control, "base_branch", "controller"))
    if base_branch != "main":
        raise ValueError("controller base_branch must be main")
    max_parallel = int(_required(control, "max_parallel", "controller"))
    if not 1 <= max_parallel <= 4:
        raise ValueError("controller max_parallel must be between 1 and 4")
    timeout_seconds = int(_required(control, "timeout_seconds", "controller"))
    if not 60 <= timeout_seconds <= 86400:
        raise ValueError("controller timeout_seconds must be 60..86400")

    state_dir = Path(str(_required(control, "state_dir", "controller"))).expanduser()
    worktree_root = Path(
        str(
            control.get(
                "worktree_root",
                "~/Developer/scratch/worktrees/Faber2026-wayfinder-auto",
            )
        )
    ).expanduser()
    home = Path.home().resolve()
    for label, candidate in (
        ("state_dir", state_dir),
        ("worktree_root", worktree_root),
    ):
        resolved = candidate.resolve()
        if resolved in {Path("/").resolve(), home}:
            raise ValueError(f"controller {label} is too broad")

    tasks: list[Task] = []
    ids: set[str] = set()
    branches: set[str] = set()
    controller_repo = str(_required(control, "repo", "controller"))
    for row in task_rows:
        task = Task(
            id=str(_required(row, "id", "task")),
            wave=str(_required(row, "wave", "task")),
            ticket=str(_required(row, "ticket", "task")),
            branch=str(_required(row, "branch", "task")),
            mode=str(_required(row, "mode", "task")),
            depends_on=tuple(str(value) for value in row.get("depends_on", [])),
            expected_artifact=str(row.get("expected_artifact", "")),
            instructions=str(_required(row, "instructions", "task")),
            execution=str(_required(row, "execution", "task")).lower(),
            repo=str(_required(row, "repo", "task")),
        )
        if task.id in ids:
            raise ValueError(f"duplicate task id: {task.id}")
        if task.branch in branches:
            raise ValueError(f"duplicate task branch: {task.branch}")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", task.id):
            raise ValueError(f"invalid task id: {task.id}")
        if not task.branch.startswith("codex/auto-"):
            raise ValueError(f"task {task.id} branch must start codex/auto-")
        if task.mode not in MODES:
            raise ValueError(f"task {task.id} mode must be resolve or review")
        if task.execution not in EXECUTIONS:
            raise ValueError(f"task {task.id} execution must be afk or hitl")
        if task.repo != controller_repo:
            raise ValueError(
                f"cross-repository task {task.id} must be decomposed into a "
                f"{controller_repo} task"
            )
        if task.mode == "review" and not task.expected_artifact:
            raise ValueError(f"review task {task.id} requires expected_artifact")
        if task.mode == "resolve" and task.expected_artifact:
            raise ValueError(f"resolve task {task.id} cannot set expected_artifact")
        if Path(task.ticket).is_absolute() or ".." in Path(task.ticket).parts:
            raise ValueError(f"task {task.id} ticket must be repo-relative")
        if task.expected_artifact and (
            Path(task.expected_artifact).is_absolute()
            or ".." in Path(task.expected_artifact).parts
        ):
            raise ValueError(f"task {task.id} expected_artifact must be repo-relative")
        ids.add(task.id)
        branches.add(task.branch)
        tasks.append(task)

    history: list[History] = []
    for row in history_rows:
        item = History(
            id=str(_required(row, "id", "history")),
            ticket=str(_required(row, "ticket", "history")),
            execution=str(_required(row, "execution", "history")).lower(),
            depends_on=tuple(str(value) for value in row.get("depends_on", [])),
            status=str(_required(row, "status", "history")).lower(),
        )
        if item.id in ids:
            raise ValueError(f"duplicate node id: {item.id}")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", item.id):
            raise ValueError(f"invalid history id: {item.id}")
        if item.execution not in EXECUTIONS:
            raise ValueError(f"history {item.id} execution must be afk or hitl")
        if item.status != "resolved":
            raise ValueError(f"history {item.id} status must be resolved")
        if Path(item.ticket).is_absolute() or ".." in Path(item.ticket).parts:
            raise ValueError(f"history {item.id} ticket must be repo-relative")
        ids.add(item.id)
        history.append(item)

    unknown = {
        dependency
        for node in [*tasks, *history]
        for dependency in node.depends_on
        if dependency not in ids
    }
    if unknown:
        raise ValueError(f"unknown task dependencies: {sorted(unknown)}")

    manifest = Manifest(
        repo=controller_repo,
        base_branch=base_branch,
        state_dir=state_dir,
        worktree_root=worktree_root,
        model=str(_required(control, "model", "controller")),
        reasoning_effort=str(_required(control, "reasoning_effort", "controller")),
        max_parallel=max_parallel,
        timeout_seconds=timeout_seconds,
        tasks=tuple(tasks),
        history=tuple(history),
        ticket_glob=str(_required(control, "ticket_glob", "controller")),
        path=path,
    )
    repo_root = ROOT if path.is_relative_to(ROOT) else path.parent
    validate_manifest_ticket_graph(manifest, repo_root)
    return manifest


def validate_manifest_ticket_graph(manifest: Manifest, repo: Path = ROOT) -> None:
    """Require exact ticket coverage, dependency parity, and execution parity."""

    repo = repo.resolve()
    matched = {
        path.resolve() for path in repo.glob(manifest.ticket_glob) if path.is_file()
    }
    nodes = [*manifest.tasks, *manifest.history]
    configured: dict[Path, Task | History] = {}
    ids: dict[str, Task | History] = {}
    for node in nodes:
        path = (repo / node.ticket).resolve()
        if not path.is_relative_to(repo):
            raise ValueError(f"ticket escapes repository: {node.ticket}")
        if path in configured:
            raise ValueError(f"duplicate configured ticket: {node.ticket}")
        configured[path] = node
        ids[node.id] = node

    missing = sorted(
        str(path.relative_to(repo)) for path in matched - configured.keys()
    )
    extra = sorted(str(path.relative_to(repo)) for path in configured.keys() - matched)
    if missing or extra:
        raise ValueError(
            f"manifest ticket coverage mismatch; missing={missing}, extra={extra}"
        )

    path_to_id = {path: node.id for path, node in configured.items()}
    task_ids = {task.id for task in manifest.tasks}
    for path, node in configured.items():
        if isinstance(node, Task) and node.repo != manifest.repo:
            raise ValueError(
                f"cross-repository task {node.id} must be decomposed into a "
                f"{manifest.repo} task"
            )
        ticket = parse_ticket_text(path.read_text(encoding="utf-8"), path)
        if node.id in task_ids and not ticket.is_open:
            raise ValueError(f"active task {node.id} ticket is not open")
        if node.id not in task_ids and ticket.status != "resolved":
            raise ValueError(f"history {node.id} ticket is not resolved")
        expected_execution = "hitl" if ticket.is_owner_facing else "afk"
        if node.execution != expected_execution:
            raise ValueError(
                f"ticket execution mismatch for {node.id}: "
                f"expected {expected_execution}, got {node.execution}"
            )

        expected_dependencies: list[str] = []
        for blocker in ticket.blockers:
            if blocker.target is None:
                raise ValueError(f"unresolved textual blocker for {node.id}")
            target = (path.parent / blocker.target).resolve()
            dependency_id = path_to_id.get(target)
            if dependency_id is None:
                raise ValueError(
                    f"blocker for {node.id} is outside configured graph: "
                    f"{blocker.target}"
                )
            expected_dependencies.append(dependency_id)
        if node.depends_on != tuple(expected_dependencies):
            raise ValueError(
                f"dependency mismatch for {node.id}: expected "
                f"{expected_dependencies}, got {list(node.depends_on)}"
            )


def tasks_for_wave(manifest: Manifest, wave: str) -> list[Task]:
    return [task for task in manifest.tasks if task.wave == wave]


def empty_state(manifest: Manifest) -> dict[str, Any]:
    return {
        "version": 1,
        "manifest": str(manifest.path),
        "identity": manifest_state_identity(manifest),
        "supervisor": {"pid": None, "wave": None, "status": "idle"},
        "tasks": {
            task.id: {
                "status": "queued",
                "pid": None,
                "detail": "",
                "updated_at": None,
                "attempt_id": None,
            }
            for task in manifest.tasks
        },
    }


def manifest_state_identity(manifest: Manifest) -> dict[str, Any]:
    """Return stable controller identity; the ticket graph evolves in place."""

    return {
        "repo": manifest.repo,
        "base_branch": manifest.base_branch,
        "state_dir": str(manifest.state_dir.resolve()),
        "worktree_root": str(manifest.worktree_root.resolve()),
        "ticket_glob": manifest.ticket_glob,
    }


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def load_state(manifest: Manifest) -> dict[str, Any]:
    path = manifest.state_dir / "state.json"
    if not path.exists():
        return empty_state(manifest)
    state = json.loads(path.read_text(encoding="utf-8"))
    if state.get("version") != 1:
        raise ValueError("unsupported controller state version")
    expected_identity = manifest_state_identity(manifest)
    if state.get("identity") != expected_identity:
        raise ValueError("controller state identity mismatch")
    for task in manifest.tasks:
        state.setdefault("tasks", {}).setdefault(
            task.id,
            {
                "status": "queued",
                "pid": None,
                "detail": "",
                "updated_at": None,
                "attempt_id": None,
            },
        )
    return state


def save_state(manifest: Manifest, state: dict[str, Any]) -> None:
    write_json_atomic(manifest.state_dir / "state.json", state)


def ready_tasks(manifest: Manifest, state: dict[str, Any], wave: str) -> list[Task]:
    ready: list[Task] = []
    task_state = state["tasks"]
    for task in tasks_for_wave(manifest, wave):
        if task.execution != "afk":
            continue
        if task_state[task.id]["status"] != "queued":
            continue
        if all(
            _dependency_satisfied(manifest, state, item) for item in task.depends_on
        ):
            ready.append(task)
    return ready


def _dependency_satisfied(
    manifest: Manifest, state: dict[str, Any], dependency: str
) -> bool:
    if any(item.id == dependency for item in manifest.history):
        return True
    upstream = _task_by_id(manifest, dependency)
    expected = "review_ready" if upstream.mode == "review" else "resolved"
    return state["tasks"][dependency]["status"] == expected


def ticket_resolution_satisfies(text: str, required_outcome: str | None = None) -> bool:
    """Compatibility wrapper around the shared Wayfinder state authority."""

    return ticket_clears_dependency(parse_ticket_text(text), required_outcome)


def ensure_ticket_blockers_satisfied(
    ticket: Path, repo: Path = ROOT, *, ref: str | None = None
) -> None:
    """Fail closed on pass-required blockers from one explicit repository state."""

    repo = repo.resolve()
    if ticket.is_absolute() or ".." in ticket.parts:
        raise RuntimeError(f"ticket escapes repository: {ticket}")

    def read(relative: Path) -> str:
        if relative.is_absolute() or ".." in relative.parts:
            raise RuntimeError(f"ticket escapes repository: {relative}")
        if ref is None:
            path = (repo / relative).resolve()
            if not path.is_relative_to(repo) or not path.is_file():
                raise RuntimeError(f"ticket is missing: {relative}")
            return path.read_text(encoding="utf-8")
        result = _git(repo, "show", f"{ref}:{relative.as_posix()}", check=False)
        if result.returncode != 0:
            raise RuntimeError(f"ticket is missing from {ref}: {relative}")
        return result.stdout

    parsed = parse_ticket_text(read(ticket), repo / ticket)
    for blocker in parsed.blockers:
        if blocker.target is None:
            raise RuntimeError(f"ticket {ticket} has unresolved blocker text")
        blocker_relative = ticket.parent / blocker.target
        blocker_ticket = parse_ticket_text(
            read(blocker_relative), repo / blocker_relative
        )
        if not ticket_clears_dependency(blocker_ticket, blocker.required_outcome):
            requirement = blocker.required_outcome or "resolution"
            raise RuntimeError(
                f"ticket {ticket} requires {requirement} from {blocker.target}"
            )


def success_status(task: Task) -> str:
    return "resolved" if task.mode == "resolve" else "review_ready"


def validate_receipt(receipt: dict[str, Any], mode: str) -> dict[str, Any]:
    required = {
        "attempt_id",
        "outcome",
        "summary",
        "branch",
        "commit",
        "pr_url",
        "checks",
        "blocker",
    }
    missing = required - set(receipt)
    if missing:
        raise ValueError(f"receipt missing fields: {sorted(missing)}")
    outcome = receipt["outcome"]
    if outcome not in RECEIPT_OUTCOMES:
        raise ValueError(f"invalid receipt outcome: {outcome}")
    allowed = (
        {"resolved", "blocked", "failed"}
        if mode == "resolve"
        else {
            "review_ready",
            "blocked",
            "failed",
        }
    )
    if outcome not in allowed:
        expected = "resolved" if mode == "resolve" else "review_ready"
        raise ValueError(f"{mode} task must end {expected}, blocked, or failed")
    if not isinstance(receipt["summary"], str) or not receipt["summary"].strip():
        raise ValueError("receipt summary must be nonempty")
    if not re.fullmatch(r"[0-9a-f]{32}", str(receipt["attempt_id"])):
        raise ValueError("receipt attempt_id must be 32 lowercase hex characters")
    if not isinstance(receipt["checks"], list) or not all(
        isinstance(value, str) for value in receipt["checks"]
    ):
        raise ValueError("receipt checks must be a string array")
    commit = receipt["commit"]
    if commit and not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("receipt commit must be a full lowercase SHA")
    pr_url = receipt["pr_url"]
    if pr_url and not re.fullmatch(
        r"https://github\.com/[^/]+/[^/]+/pull/[0-9]+", pr_url
    ):
        raise ValueError("receipt pr_url must be a GitHub pull request URL")
    if outcome in {"resolved", "review_ready"} and not commit:
        raise ValueError(f"{outcome} receipt requires a commit")
    if outcome in {"resolved", "review_ready"} and not pr_url:
        raise ValueError(f"{outcome} receipt requires a PR URL")
    if outcome == "resolved" and not receipt["checks"]:
        raise ValueError("resolved receipt requires recorded checks")
    return receipt


def _run(
    command: list[str], cwd: Path, *, check: bool = True
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=check)


def _git(
    repo: Path, *args: str, check: bool = True
) -> subprocess.CompletedProcess[str]:
    return _run(["git", *args], repo, check=check)


def process_alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
    except (ProcessLookupError, PermissionError):
        return False
    return True


def _remote_repo(remote: str) -> str | None:
    match = re.search(r"github\.com(?::|/)([^/]+/[^/]+?)(?:\.git)?$", remote.strip())
    return match.group(1) if match else None


def validate_repository_identity(manifest: Manifest, repo: Path = ROOT) -> None:
    repo = repo.resolve()
    top = _git(repo, "rev-parse", "--show-toplevel", check=False)
    if top.returncode != 0 or Path(top.stdout.strip()).resolve() != repo:
        raise RuntimeError(f"controller repository root mismatch: {repo}")
    remote = _git(repo, "remote", "get-url", "origin", check=False)
    actual_repo = _remote_repo(remote.stdout) if remote.returncode == 0 else None
    if actual_repo != manifest.repo:
        raise RuntimeError(
            f"origin repository mismatch: expected {manifest.repo}, got "
            f"{actual_repo or 'unknown'}"
        )


def _common_git_dir(repo: Path) -> Path:
    result = _git(repo, "rev-parse", "--git-common-dir")
    path = Path(result.stdout.strip())
    return (repo / path).resolve() if not path.is_absolute() else path.resolve()


def validate_worktree_identity(
    manifest: Manifest, worktree: Path, controller_repo: Path = ROOT
) -> None:
    validate_repository_identity(manifest, worktree)
    if _common_git_dir(worktree.resolve()) != _common_git_dir(
        controller_repo.resolve()
    ):
        raise RuntimeError(f"worktree repository mismatch: {worktree}")


def ensure_controller_is_merged(manifest: Manifest, repo: Path = ROOT) -> None:
    validate_repository_identity(manifest, repo)
    _git(repo, "fetch", "origin", manifest.base_branch)
    for relative in (
        "scripts/wayfinder_controller.py",
        "scripts/wayfinder_state.py",
        "scripts/wayfinder_receipt.schema.json",
        "docs/rse/control/wayfinder-automation.toml",
    ):
        local = (repo / relative).read_bytes()
        remote = subprocess.check_output(
            ["git", "show", f"origin/{manifest.base_branch}:{relative}"], cwd=repo
        )
        if local != remote:
            raise RuntimeError(
                f"controller launch refused: {relative} is not merged on origin/main"
            )


def task_prompt(manifest: Manifest, task: Task, attempt_id: str) -> str:
    endpoint = (
        "Resolve the ticket only after its acceptance and validation checks pass; push, open "
        "a focused PR, wait for checks, merge it, and verify origin/main."
        if task.mode == "resolve"
        else (
            "Produce a complete review artifact, push it, open a focused draft PR, wait for all "
            "GitHub checks, but do not merge, resolve the ticket, or promote trust."
        )
    )
    expected = "resolved" if task.mode == "resolve" else "review_ready"
    return f"""Execute Wayfinder task {task.id} in this isolated worktree.

Ticket: {task.ticket}
Branch: {task.branch}
Base: origin/{manifest.base_branch}
Mode: {task.mode}
Attempt ID: {attempt_id}

Task instructions:
{task.instructions}

Required workflow:
- Read AGENTS.md, the complete ticket, its map, linked evidence, and applicable skills.
- Re-read origin/main and the ticket header before claiming and before resolution.
- Preserve concurrent work and the pipeline gitlink unless the ticket explicitly owns it.
- Work test-first; run task-scoped checks, make test-science when applicable, and agent-closeout-check.
- {endpoint}
- Never delete or move data, rewrite history, change services, submit the manuscript, promote Figure 3, promote scientific trust, re-adjudicate foreground redshifts/budgets, or change coauthors.
- Stop fail-closed if evidence is missing, independent checks disagree, or a material scientific claim would change.
- Normal progress prose may go to stdout. Your final response MUST satisfy the supplied JSON schema.

Final receipt rules:
- outcome={expected} only when the endpoint above is independently true.
- outcome=blocked with the exact blocker when a recorded gate stops work.
- outcome=failed for implementation or validation failure.
- branch must equal {task.branch}; use a full 40-character commit SHA.
- attempt_id must equal {attempt_id}.
- checks must list exactly the successful GitHub check names shown on the PR;
  describe local checks in summary. Include the PR URL when one exists.
"""


def codex_command(
    manifest: Manifest,
    task: Task,
    worktree: Path,
    receipt_path: Path,
    controller_root: Path = ROOT,
    attempt_id: str = "0" * 32,
) -> list[str]:
    timeout = shutil.which("timeout") or shutil.which("gtimeout")
    codex = shutil.which("codex")
    if not timeout or not codex:
        raise RuntimeError("controller requires timeout (or gtimeout) and codex")
    return [
        timeout,
        "--signal=TERM",
        "--kill-after=30",
        str(manifest.timeout_seconds),
        codex,
        "exec",
        "-m",
        manifest.model,
        "-c",
        f'model_reasoning_effort="{manifest.reasoning_effort}"',
        "-c",
        'approval_policy="never"',
        "--sandbox",
        "danger-full-access",
        "-C",
        str(worktree),
        "--output-schema",
        str(controller_root / "scripts/wayfinder_receipt.schema.json"),
        "--output-last-message",
        str(receipt_path),
        task_prompt(manifest, task, attempt_id),
    ]


@contextmanager
def repository_mutation_lock(manifest: Manifest):
    """Serialize Git operations that mutate the repository's shared metadata."""
    manifest.state_dir.mkdir(parents=True, exist_ok=True)
    lock_path = manifest.state_dir / "repository.lock"
    with lock_path.open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def prepare_worktree(manifest: Manifest, task: Task, repo: Path = ROOT) -> Path:
    validate_repository_identity(manifest, repo)
    path = manifest.worktree_root / task.id
    manifest.worktree_root.mkdir(parents=True, exist_ok=True)
    with repository_mutation_lock(manifest):
        _git(repo, "fetch", "origin", manifest.base_branch)
        ensure_ticket_blockers_satisfied(
            Path(task.ticket), repo, ref=f"origin/{manifest.base_branch}"
        )
        if path.exists():
            status = _git(path, "status", "--short").stdout.strip()
            branch = _git(path, "branch", "--show-current").stdout.strip()
            if status:
                raise RuntimeError(f"existing task worktree is dirty: {path}")
            if branch != task.branch:
                raise RuntimeError(
                    f"existing task worktree has branch {branch}, expected {task.branch}"
                )
        else:
            local_branch = (
                _git(
                    repo,
                    "show-ref",
                    "--verify",
                    f"refs/heads/{task.branch}",
                    check=False,
                ).returncode
                == 0
            )
            remote_branch = (
                _git(
                    repo,
                    "show-ref",
                    "--verify",
                    f"refs/remotes/origin/{task.branch}",
                    check=False,
                ).returncode
                == 0
            )
            if local_branch:
                _git(repo, "worktree", "add", str(path), task.branch)
            elif remote_branch:
                _git(
                    repo,
                    "worktree",
                    "add",
                    "-b",
                    task.branch,
                    str(path),
                    f"origin/{task.branch}",
                )
            else:
                _git(
                    repo,
                    "worktree",
                    "add",
                    "-b",
                    task.branch,
                    str(path),
                    f"origin/{manifest.base_branch}",
                )
        validate_worktree_identity(manifest, path, repo)
        _git(path, "submodule", "update", "--init", "--recursive")
    return path


def remote_pr_evidence(
    manifest: Manifest,
    task: Task,
    receipt: dict[str, Any],
    expected_state: str,
    repo: Path = ROOT,
) -> tuple[bool, str]:
    expected_prefix = f"https://github.com/{manifest.repo}/pull/"
    if not receipt.get("pr_url", "").startswith(expected_prefix):
        return False, "PR URL repository differs from manifest"
    result = _run(
        [
            "gh",
            "pr",
            "view",
            receipt["pr_url"],
            "--json",
            "state,baseRefName,headRefName,headRefOid,mergeCommit,statusCheckRollup",
        ],
        repo,
        check=False,
    )
    if result.returncode != 0:
        return False, "GitHub PR verification failed"
    pr = json.loads(result.stdout)
    if pr.get("state") != expected_state:
        return False, f"PR {pr.get('state', 'unknown').lower()}"
    if (
        pr.get("baseRefName") != manifest.base_branch
        or pr.get("headRefName") != task.branch
    ):
        return False, "PR branch/base differs from manifest"
    if pr.get("headRefOid") != receipt.get("commit"):
        return False, "receipt commit differs from PR head"
    checks = pr.get("statusCheckRollup", [])
    if not checks:
        return False, "PR has no reported checks"
    names: set[str] = set()
    for check in checks:
        name = check.get("name") or check.get("context")
        if name:
            names.add(name)
        if check.get("status") and (
            check.get("status") != "COMPLETED"
            or check.get("conclusion") not in {"SUCCESS", "NEUTRAL", "SKIPPED"}
        ):
            return False, "PR has a pending or failed check"
        if check.get("state") and check.get("state") != "SUCCESS":
            return False, "PR has a pending or failed status context"
    if set(receipt["checks"]) != names:
        return False, "receipt check names differ from GitHub"
    return True, "PR repository, head commit, and checks verified"


def remote_resolution_evidence(
    manifest: Manifest, task: Task, receipt: dict[str, Any], repo: Path = ROOT
) -> tuple[bool, str]:
    ok, detail = remote_pr_evidence(manifest, task, receipt, "MERGED", repo)
    if not ok:
        return False, detail
    _git(repo, "fetch", "origin", manifest.base_branch)
    ticket = _git(
        repo, "show", f"origin/{manifest.base_branch}:{task.ticket}", check=False
    )
    if ticket.returncode != 0:
        return False, "ticket missing from origin/main"
    if not ticket_resolution_satisfies(ticket.stdout):
        return (
            False,
            "ticket is not resolved with its required gate outcome on origin/main",
        )
    return True, "merged PR and resolved ticket verified on origin/main"


def remote_review_evidence(
    manifest: Manifest, task: Task, receipt: dict[str, Any], repo: Path = ROOT
) -> tuple[bool, str]:
    ok, detail = remote_pr_evidence(manifest, task, receipt, "OPEN", repo)
    if not ok:
        return False, detail
    _git(repo, "fetch", "origin", task.branch)
    artifact = _git(
        repo,
        "cat-file",
        "-e",
        f"{receipt['commit']}:{task.expected_artifact}",
        check=False,
    )
    if artifact.returncode != 0:
        return False, f"review artifact missing: {task.expected_artifact}"
    return True, "open PR, head commit, checks, and review artifact verified"


def classify_receipt(
    manifest: Manifest,
    task: Task,
    receipt: dict[str, Any],
    repo: Path = ROOT,
    expected_attempt: str | None = None,
) -> tuple[str, str]:
    receipt = validate_receipt(receipt, task.mode)
    if expected_attempt is not None and receipt["attempt_id"] != expected_attempt:
        return "needs_attention", "receipt attempt differs from running attempt"
    if receipt["branch"] != task.branch:
        return "needs_attention", "receipt branch differs from manifest"
    if receipt["outcome"] == "resolved":
        ok, detail = remote_resolution_evidence(manifest, task, receipt, repo)
        return ("resolved", detail) if ok else ("needs_attention", detail)
    if receipt["outcome"] == "review_ready":
        ok, detail = remote_review_evidence(manifest, task, receipt, repo)
        return ("review_ready", detail) if ok else ("needs_attention", detail)
    if receipt["outcome"] == "blocked":
        return "blocked", receipt["blocker"] or receipt["summary"]
    return "failed", receipt["blocker"] or receipt["summary"]


def _task_by_id(manifest: Manifest, task_id: str) -> Task:
    for task in manifest.tasks:
        if task.id == task_id:
            return task
    raise ValueError(f"unknown task: {task_id}")


def run_task(manifest: Manifest, task: Task, attempt_id: str) -> int:
    if task.execution != "afk":
        raise RuntimeError(f"HITL task {task.id} cannot be run by the controller")
    task_dir = manifest.state_dir / "tasks" / task.id
    task_dir.mkdir(parents=True, exist_ok=True)
    attempt_dir = task_dir / "attempts" / attempt_id
    attempt_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = attempt_dir / "receipt.json"
    stdout_path = attempt_dir / "codex.stdout.log"
    stderr_path = attempt_dir / "codex.stderr.log"
    lock_path = task_dir / "task.lock"
    with lock_path.open("w") as task_lock:
        try:
            fcntl.flock(task_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError(f"task {task.id} already has a live runner") from error
        write_json_atomic(
            attempt_dir / "runner-owner.json",
            {
                "attempt_id": attempt_id,
                "pid": os.getpid(),
                "started_at": int(time.time()),
            },
        )
        worktree = prepare_worktree(manifest, task)
        command = codex_command(
            manifest, task, worktree, receipt_path, attempt_id=attempt_id
        )
        with stdout_path.open("ab") as stdout, stderr_path.open("ab") as stderr:
            result = subprocess.run(
                command,
                cwd=worktree,
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                check=False,
            )
        return result.returncode


def run_task_and_record(manifest: Manifest, task: Task, attempt_id: str) -> int:
    task_dir = manifest.state_dir / "tasks" / task.id
    task_dir.mkdir(parents=True, exist_ok=True)
    attempt_dir = task_dir / "attempts" / attempt_id
    exit_path = attempt_dir / "runner-exit.json"
    try:
        returncode = run_task(manifest, task, attempt_id)
        detail = ""
    except Exception as error:
        returncode = 2
        detail = str(error)
    write_json_atomic(
        exit_path,
        {
            "attempt_id": attempt_id,
            "returncode": returncode,
            "detail": detail,
            "finished_at": int(time.time()),
        },
    )
    if detail:
        print(f"wayfinder-controller task {task.id}: {detail}", file=sys.stderr)
    return returncode


def supervise(manifest: Manifest, wave: str) -> int:
    manifest.state_dir.mkdir(parents=True, exist_ok=True)
    lock_path = manifest.state_dir / "supervisor.lock"
    with lock_path.open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return 2
        for _ in range(100):
            state = load_state(manifest)
            if state.get("supervisor", {}).get("pid") == os.getpid():
                break
            time.sleep(0.1)
        else:
            print("supervisor launch handshake timed out", file=sys.stderr)
            return 2
        state["supervisor"] = {
            "pid": os.getpid(),
            "wave": wave,
            "status": "initializing",
        }
        save_state(manifest, state)
        running: dict[str, subprocess.Popen[bytes] | ExistingProcess] = {}
        runner_logs: dict[str, Any] = {}
        try:
            for task in tasks_for_wave(manifest, wave):
                entry = state["tasks"][task.id]
                if entry["status"] not in {"starting", "running"}:
                    continue
                attempt_id = entry.get("attempt_id")
                if not attempt_id:
                    entry.update({"status": "queued", "pid": None})
                    continue
                attempt_dir = (
                    manifest.state_dir / "tasks" / task.id / "attempts" / attempt_id
                )
                pid = entry.get("pid")
                owner_path = attempt_dir / "runner-owner.json"
                if not pid and owner_path.exists():
                    owner = json.loads(owner_path.read_text(encoding="utf-8"))
                    if owner.get("attempt_id") == attempt_id:
                        pid = owner.get("pid")
                if not pid:
                    entry.update({"status": "queued", "pid": None, "attempt_id": None})
                    continue
                running[task.id] = ExistingProcess(
                    int(pid),
                    attempt_dir / "runner-exit.json",
                    attempt_id,
                )
                entry.update({"status": "running", "pid": int(pid)})
            save_state(manifest, state)
            while True:
                for task_id, process in list(running.items()):
                    returncode = process.poll()
                    if returncode is None:
                        continue
                    stream = runner_logs.pop(task_id, None)
                    if stream is not None:
                        stream.close()
                    task = _task_by_id(manifest, task_id)
                    entry = state["tasks"][task_id]
                    attempt_id = entry.get("attempt_id")
                    entry["pid"] = None
                    entry["updated_at"] = int(time.time())
                    if returncode != 0:
                        entry["status"] = "failed"
                        entry["detail"] = f"task runner exited {returncode}"
                    else:
                        receipt_path = (
                            manifest.state_dir
                            / "tasks"
                            / task_id
                            / "attempts"
                            / str(attempt_id)
                            / "receipt.json"
                        )
                        try:
                            receipt = json.loads(
                                receipt_path.read_text(encoding="utf-8")
                            )
                            status, detail = classify_receipt(
                                manifest,
                                task,
                                receipt,
                                expected_attempt=str(attempt_id),
                            )
                        except Exception as error:  # fail-closed receipt boundary
                            status, detail = (
                                "needs_attention",
                                f"receipt verification failed: {error}",
                            )
                        entry["status"] = status
                        entry["detail"] = detail
                    running.pop(task_id)
                    save_state(manifest, state)

                capacity = manifest.max_parallel - len(running)
                for task in ready_tasks(manifest, state, wave)[:capacity]:
                    task_dir = manifest.state_dir / "tasks" / task.id
                    task_dir.mkdir(parents=True, exist_ok=True)
                    attempt_id = secrets.token_hex(16)
                    attempt_dir = task_dir / "attempts" / attempt_id
                    state["tasks"][task.id].update(
                        {
                            "status": "starting",
                            "pid": None,
                            "attempt_id": attempt_id,
                            "detail": "",
                            "updated_at": int(time.time()),
                        }
                    )
                    save_state(manifest, state)
                    attempt_dir.mkdir(parents=True, exist_ok=True)
                    runner_log = (attempt_dir / "runner.log").open("ab")
                    try:
                        process = subprocess.Popen(
                            [
                                sys.executable,
                                str(Path(__file__).resolve()),
                                "_run-task",
                                "--manifest",
                                str(manifest.path),
                                "--task",
                                task.id,
                                "--attempt",
                                attempt_id,
                            ],
                            cwd=ROOT,
                            stdin=subprocess.DEVNULL,
                            stdout=runner_log,
                            stderr=subprocess.STDOUT,
                            start_new_session=True,
                        )
                    except Exception:
                        runner_log.close()
                        raise
                    running[task.id] = process
                    runner_logs[task.id] = runner_log
                    state["tasks"][task.id].update(
                        {
                            "status": "running",
                            "pid": process.pid,
                            "attempt_id": attempt_id,
                            "detail": "",
                            "updated_at": int(time.time()),
                        }
                    )
                    save_state(manifest, state)

                if state["supervisor"]["status"] == "initializing":
                    state["supervisor"] = {
                        "pid": os.getpid(),
                        "wave": wave,
                        "status": "running",
                    }
                    save_state(manifest, state)

                selected = tasks_for_wave(manifest, wave)
                if not running and all(
                    state["tasks"][task.id]["status"] in TERMINAL_STATUSES
                    for task in selected
                ):
                    break
                if not running and not ready_tasks(manifest, state, wave):
                    break
                time.sleep(5)
        finally:
            for stream in runner_logs.values():
                stream.close()
        unsuccessful = [
            task.id
            for task in tasks_for_wave(manifest, wave)
            if state["tasks"][task.id]["status"] != success_status(task)
        ]
        state["supervisor"] = {
            "pid": None,
            "wave": wave,
            "status": "completed" if not unsuccessful else "attention_required",
        }
        save_state(manifest, state)
        return 0 if not unsuccessful else 1


def launch(manifest: Manifest, wave: str) -> int:
    if not tasks_for_wave(manifest, wave):
        raise ValueError(f"manifest has no wave: {wave}")
    ensure_controller_is_merged(manifest)
    manifest.state_dir.mkdir(parents=True, exist_ok=True)
    launch_lock_path = manifest.state_dir / "launch.lock"
    with launch_lock_path.open("w") as launch_lock:
        try:
            fcntl.flock(launch_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError("another controller launch is in progress") from error
        state = load_state(manifest)
        existing_pid = state.get("supervisor", {}).get("pid")
        if process_alive(existing_pid):
            raise RuntimeError(f"supervisor already running as PID {existing_pid}")
        state["supervisor"] = {"pid": None, "wave": wave, "status": "starting"}
        save_state(manifest, state)
        supervisor_log = (manifest.state_dir / f"supervisor-{wave}.log").open("ab")
        try:
            process = subprocess.Popen(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "_supervise",
                    "--manifest",
                    str(manifest.path),
                    "--wave",
                    wave,
                ],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                stdout=supervisor_log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        finally:
            supervisor_log.close()
        state["supervisor"] = {"pid": process.pid, "wave": wave, "status": "starting"}
        save_state(manifest, state)
        for _ in range(150):
            current = load_state(manifest)
            current_supervisor = current.get("supervisor", {})
            returncode = process.poll()
            if (
                returncode is None
                and current_supervisor.get("pid") == process.pid
                and current_supervisor.get("status") == "running"
            ):
                print(f"launched wave {wave}: supervisor PID {process.pid}")
                print(f"state: {manifest.state_dir / 'state.json'}")
                return 0
            if returncode is not None:
                raise RuntimeError(f"supervisor exited during launch with {returncode}")
            time.sleep(0.1)
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        raise RuntimeError("supervisor failed its launch handshake")


def retry_task(manifest: Manifest, task_id: str) -> int:
    _task_by_id(manifest, task_id)
    state = load_state(manifest)
    supervisor_pid = state.get("supervisor", {}).get("pid")
    if process_alive(supervisor_pid):
        raise RuntimeError(f"supervisor is running as PID {supervisor_pid}")
    entry = state["tasks"][task_id]
    if entry["status"] in {"starting", "running"}:
        raise RuntimeError(f"task {task_id} is still {entry['status']}")
    if entry["status"] == "resolved":
        raise RuntimeError(f"task {task_id} is already resolved")
    entry.update(
        {
            "status": "queued",
            "pid": None,
            "detail": "",
            "updated_at": int(time.time()),
            "attempt_id": None,
        }
    )
    save_state(manifest, state)
    print(f"queued retry: {task_id}")
    return 0


def print_plan(manifest: Manifest, wave: str) -> int:
    state = load_state(manifest)
    selected = tasks_for_wave(manifest, wave)
    if not selected:
        raise ValueError(f"manifest has no wave: {wave}")
    for task in selected:
        dependencies = ",".join(task.depends_on) or "none"
        print(
            f"{task.id}: {state['tasks'][task.id]['status']} "
            f"mode={task.mode} execution={task.execution} "
            f"dependencies={dependencies}"
        )
    return 0


def print_status(manifest: Manifest, as_json: bool) -> int:
    state = load_state(manifest)
    pid = state.get("supervisor", {}).get("pid")
    state["supervisor"]["alive"] = process_alive(pid)
    if as_json:
        print(json.dumps(state, indent=2, sort_keys=True))
    else:
        supervisor = state["supervisor"]
        print(
            f"supervisor: {supervisor['status']} pid={supervisor.get('pid')} "
            f"alive={supervisor['alive']} wave={supervisor.get('wave')}"
        )
        for task in manifest.tasks:
            entry = state["tasks"][task.id]
            print(
                f"{task.id}: {entry['status']} execution={task.execution} "
                f"{entry.get('detail', '')}".rstrip()
            )
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    subparsers = result.add_subparsers(dest="command", required=True)
    for name in ("plan", "launch", "_supervise"):
        command = subparsers.add_parser(name)
        command.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
        command.add_argument("--wave", required=True)
    status = subparsers.add_parser("status")
    status.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    status.add_argument("--json", action="store_true")
    retry = subparsers.add_parser("retry")
    retry.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    retry.add_argument("--task", required=True)
    run_task_parser = subparsers.add_parser("_run-task")
    run_task_parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    run_task_parser.add_argument("--task", required=True)
    run_task_parser.add_argument("--attempt", required=True)
    return result


def main() -> int:
    args = parser().parse_args()
    manifest = load_manifest(args.manifest)
    if args.command == "plan":
        return print_plan(manifest, args.wave)
    if args.command == "launch":
        return launch(manifest, args.wave)
    if args.command == "status":
        return print_status(manifest, args.json)
    if args.command == "retry":
        return retry_task(manifest, args.task)
    if args.command == "_supervise":
        return supervise(manifest, args.wave)
    if args.command == "_run-task":
        return run_task_and_record(
            manifest, _task_by_id(manifest, args.task), args.attempt
        )
    raise AssertionError(args.command)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        print(f"wayfinder-controller: {error}", file=sys.stderr)
        raise SystemExit(2)
