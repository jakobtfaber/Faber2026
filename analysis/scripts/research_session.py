#!/usr/bin/env python3
"""Open a live-analysis session workbench outside both git checkouts.

The session directory lives under ``~/Data/Faber2026/workbench`` (override with
``FABER2026_WORKBENCH``); the git checkouts stay clean. Two files split the
record:

``TASK.md``
    The human scientific contract -- phase, objective, may/must-not change,
    done-when, verification command. The launcher pre-fills the empty form and
    never overwrites it afterwards.
``session.json``
    Machine-derived state only -- issue and event identifiers, both repository
    paths and commits, branch names, the parent's ``analysis`` gitlink,
    dirty-state summaries, ahead/behind against the *local* ``origin/main``
    remote-tracking ref, the interpreter path, and the creation time.

Ahead/behind is computed from the remote-tracking ref already on disk; no fetch
happens unless ``--fetch`` is passed. A session started on a stale base is the
failure that field exists to catch.

An existing ``session.json`` is never touched by accident: ``start`` fails,
``--resume`` reopens it after checking the repository identities still match,
and ``--force`` overwrites it.

Commands:
  start --issue N --phase PHASE [--event E] [--check CMD ...]
        [--resume | --force] [--worktree] [--fetch] [--dry-run] [--json]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from workspace import ANALYSIS_ROOT, manuscript_root

DEFAULT_WORKBENCH = Path.home() / "Data" / "Faber2026" / "workbench"
# Read-only input and recorded-result trees (jupyter-surface.md, data mounts):
# a workbench override inside one of these would let session writes alter
# inputs or recorded results.
RESERVED_DATA_TREES = (
    Path.home() / "Data" / "Faber2026" / "dsa110",
    Path.home() / "Data" / "Faber2026" / "chimefrb",
    Path.home() / "Data" / "Faber2026" / "results-library",
)
WORKBENCH_ENV = "FABER2026_WORKBENCH"
PHASES = ("exploration", "validation", "publication")
# live-analysis.md names the middle phase "scientific validation"; the command
# line accepts the shorthand, the written contract carries the documented value.
PHASE_HEADER = {
    "exploration": "exploration",
    "validation": "scientific validation",
    "publication": "publication",
}
SCHEMA_VERSION = 1
TASK_FILENAME = "TASK.md"
SESSION_FILENAME = "session.json"
NO_FETCH_BASIS = "local remote-tracking ref; no fetch performed"
FETCHED_BASIS = "local remote-tracking ref refreshed by --fetch"
NO_REF_BASIS = "origin/main not present locally; no fetch performed"
MANAGED_KEYS = (
    "schema_version",
    "slug",
    "issue",
    "event",
    "state",
    "created_at",
    "updated_at",
    "workbench",
    "interpreter",
    "project",
    "checks",
    "repositories",
    "git",
    "worktree",
    "warnings",
)

_SLUG_SEPARATORS = re.compile(r"[^a-z0-9]+")

# Distinguishes THIS invocation's pending-ownership marker from a concurrent
# invocation's: failure cleanup removes only its own marker.
_INVOCATION_TOKEN = f"{os.getpid()}-{os.urandom(4).hex()}"


@contextmanager
def session_write_lock(session_file: Path) -> Any:
    """Exclusive lock serializing every session.json ownership write."""
    lock = session_file.with_name(session_file.name + ".writing")
    for _attempt in range(50):
        try:
            os.close(os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
            break
        except FileExistsError:
            time.sleep(0.1)
    else:
        raise SessionError(
            "RECORD_LOCKED",
            f"{lock} held for over five seconds; another invocation is "
            "writing this session -- retry, or remove the lock if its "
            "process died",
        )
    try:
        yield
    finally:
        lock.unlink(missing_ok=True)


class SessionError(Exception):
    """Typed failure for session-launch problems."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def workbench_root() -> Path:
    # An exported-but-empty override would resolve to the current directory,
    # which under `make session` is the analysis checkout itself.
    override = os.environ.get(WORKBENCH_ENV, "").strip()
    return Path(override or str(DEFAULT_WORKBENCH)).expanduser().resolve()


def workbench_root_source() -> str:
    return WORKBENCH_ENV if os.environ.get(WORKBENCH_ENV, "").strip() else "default"


def require_workbench_root() -> Path:
    root = workbench_root()
    if not root.is_dir():
        raise FileNotFoundError(
            f"workbench root missing: {root}. "
            f"Run mkdir -p '{root}' or set {WORKBENCH_ENV}=/path/to/workbench."
        )
    for reserved_tree in RESERVED_DATA_TREES:
        reserved = reserved_tree.resolve()
        if root == reserved or reserved in root.parents:
            raise SessionError(
                "WORKBENCH_IN_DATA_TREE",
                f"workbench root {root} is inside the read-only data tree "
                f"{reserved}; session writes must never reach input or "
                "recorded-result storage",
            )
    parent, _ = resolve_manuscript()
    checkouts: list[tuple[str, Path]] = [("analysis", ANALYSIS_ROOT)]
    if parent is not None:
        checkouts.append(("manuscript", parent))
    for wt in analysis_worktree_paths():
        checkouts.append(("analysis worktree", wt))
    for wt in worktree_paths(parent):
        checkouts.append(("manuscript worktree", wt))
    for name, checkout in checkouts:
        resolved = Path(checkout).resolve()
        if root == resolved or resolved in root.parents:
            raise SessionError(
                "WORKBENCH_INSIDE_CHECKOUT",
                f"workbench root {root} is inside the {name} checkout {resolved}; "
                "sessions live outside every git checkout",
            )
    return root


def _slugify(value: str) -> str:
    return _SLUG_SEPARATORS.sub("-", value.strip().lower()).strip("-")


def session_slug(issue: str, event: str | None) -> str:
    """Deterministic, filesystem-safe directory name for an issue/event pair."""
    issue_part = _slugify(issue)
    if not issue_part:
        raise SessionError("BAD_ISSUE", f"issue has no slug-safe characters: {issue!r}")
    parts = ["issue", issue_part]
    if event:
        event_part = _slugify(event)
        if not event_part:
            raise SessionError("BAD_EVENT", f"event has no slug-safe characters: {event!r}")
        parts.append(event_part)
    return "-".join(parts)


def _git(args: list[str], cwd: Path | None, *, strip: bool = True) -> str | None:
    """Run git and return stdout, or None when it cannot answer.

    ``strip=False`` preserves the leading status columns of
    ``git status --porcelain``, where the first character is the staged state.
    """
    if cwd is None or not cwd.is_dir():
        return None
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() if strip else proc.stdout


def _head(repo: Path | None) -> str | None:
    return _git(["rev-parse", "HEAD"], repo)


def _branch(repo: Path | None) -> str | None:
    name = _git(["rev-parse", "--abbrev-ref", "HEAD"], repo)
    return None if name in (None, "HEAD") else name


def dirty_summary(repo: Path | None) -> dict[str, Any] | None:
    """Counts from ``git status --porcelain``; None when git cannot answer."""
    raw = _git(["status", "--porcelain"], repo, strip=False)
    if raw is None:
        return None
    lines = [line for line in raw.splitlines() if line.strip()]
    untracked = sum(1 for line in lines if line.startswith("??"))
    staged = sum(1 for line in lines if not line.startswith("??") and line[:1] not in (" ", ""))
    unstaged = sum(1 for line in lines if not line.startswith("??") and line[1:2] not in (" ", ""))
    return {
        "clean": not lines,
        "staged": staged,
        "unstaged": unstaged,
        "untracked": untracked,
    }


def origin_main_state(repo: Path | None, *, fetched: bool = False) -> dict[str, Any]:
    """Ahead/behind against the local ``origin/main`` ref. Never fetches."""
    local_ref = _git(["rev-parse", "--verify", "--quiet", "origin/main"], repo)
    if not local_ref:
        return {
            "local_ref": None,
            "ahead": None,
            "behind": None,
            "comparison_basis": NO_REF_BASIS,
        }
    basis = FETCHED_BASIS if fetched else NO_FETCH_BASIS
    counts = _git(["rev-list", "--left-right", "--count", "HEAD...origin/main"], repo)
    ahead: int | None = None
    behind: int | None = None
    if counts:
        fields = counts.split()
        if len(fields) == 2:
            try:
                ahead, behind = int(fields[0]), int(fields[1])
            except ValueError:
                ahead, behind = None, None
    return {
        "local_ref": local_ref,
        "ahead": ahead,
        "behind": behind,
        "comparison_basis": basis,
    }


def fetch_origin_main(repo: Path | None) -> str | None:
    """Explicit, opt-in fetch. Returns an error string on failure."""
    if repo is None or not repo.is_dir():
        return "analysis checkout not found"
    try:
        proc = subprocess.run(
            # Explicit destination refspec: a bare `fetch origin main` can
            # update only FETCH_HEAD, leaving the origin/main ref that
            # origin_main_state() compares against missing or stale.
            ["git", "fetch", "origin", "+refs/heads/main:refs/remotes/origin/main"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return str(exc)
    if proc.returncode != 0:
        return (proc.stderr or proc.stdout or "").strip()
    return None


def gitlink(repo: Path | None, path: str = "analysis") -> str | None:
    """The commit a parent repository pins for a submodule path."""
    raw = _git(["ls-tree", "HEAD", path], repo)
    if not raw:
        return None
    fields = raw.split()
    return fields[2] if len(fields) >= 3 else None


def resolve_manuscript() -> tuple[Path | None, str | None]:
    """Return the manuscript root, or None plus the actionable hint."""
    try:
        return manuscript_root(), None
    except RuntimeError as exc:
        return None, str(exc)


def collect_git_state(
    *, fetched: bool = False, analysis_checkout: Path | None = None
) -> tuple[dict[str, Any], Path | None]:
    """Git state of the checkout the session executes against.

    ``analysis_checkout`` is the session worktree when one is registered --
    provenance must describe the code the kernel actually runs, not the
    canonical checkout it was forked from.
    """
    analysis = analysis_checkout or ANALYSIS_ROOT
    parent, parent_error = resolve_manuscript()
    analysis_head = _head(analysis)
    pinned = gitlink(parent)
    state = {
        "analysis": {
            "checkout": str(analysis),
            "head": analysis_head,
            "branch": _branch(analysis),
            "dirty": dirty_summary(analysis),
            "origin_main": origin_main_state(analysis, fetched=fetched),
        },
        "manuscript": {
            "head": _head(parent),
            "branch": _branch(parent),
            "gitlink": pinned,
            "gitlink_matches_analysis_head": (
                None if (pinned is None or analysis_head is None) else pinned == analysis_head
            ),
            "dirty": dirty_summary(parent),
            "error": parent_error,
        },
    }
    return state, parent


def interpreter_path(project: Path | None = None) -> Path:
    """The locked interpreter of the checkout the session actually runs against.

    A worktree session must use the worktree's own environment, not the main
    checkout's -- otherwise the session branch's changes never reach the kernel
    (jupyter-surface.md, "one environment per active worktree").
    """
    return (project or ANALYSIS_ROOT) / ".venv" / "bin" / "python"


def render_task_contract(phase: str, checks: list[str]) -> str:
    """The five-line operational contract, empty for the human to complete."""
    verification = "Verification command:"
    if checks:
        verification = "\n".join([verification, *(f"  {check}" for check in checks)])
    return (
        f"Scientific phase: {PHASE_HEADER[phase]}\n"
        "\n"
        "Objective:\n"
        "\n"
        "May change:\n"
        "\n"
        "Must not change:\n"
        "\n"
        "Done when:\n"
        "\n"
        f"{verification}\n"
    )


def build_record(
    *,
    slug: str,
    issue: str,
    event: str | None,
    checks: list[str],
    root: Path,
    session_dir: Path,
    git_state: dict[str, Any],
    parent: Path | None,
    state: str,
    project: Path | None = None,
) -> dict[str, Any]:
    now = datetime.now(UTC).isoformat()
    return {
        "schema_version": SCHEMA_VERSION,
        "slug": slug,
        "issue": issue,
        "event": event,
        "state": state,
        "created_at": now,
        "updated_at": now,
        "workbench": {
            "root": str(root),
            "root_source": workbench_root_source(),
            "session_dir": str(session_dir),
            "scratch": str(session_dir / "scratch"),
            "exports": str(session_dir / "exports"),
            "task_file": str(session_dir / TASK_FILENAME),
        },
        "interpreter": str(interpreter_path(project)),
        "project": str(project) if project else str(ANALYSIS_ROOT),
        "checks": list(checks),
        "repositories": {
            "analysis": str(ANALYSIS_ROOT),
            "manuscript": str(parent) if parent else None,
        },
        "git": git_state,
        "worktree": {"path": str(session_dir / "worktree"), "created": False},
        "warnings": [],
    }


def recorded_analysis_head(existing: dict[str, Any]) -> str | None:
    """The recorded git.analysis.head, None when any nesting level is off-shape."""
    git_state = existing.get("git")
    if not isinstance(git_state, dict):
        return None
    analysis = git_state.get("analysis")
    if not isinstance(analysis, dict):
        return None
    head = analysis.get("head")
    return head if isinstance(head, str) else None


def read_existing_lenient(session_file: Path) -> dict[str, Any]:
    """Best-effort read for merge decisions; {} on any failure."""
    if not session_file.is_file():
        return {}
    try:
        loaded = json.loads(session_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def read_existing(session_file: Path) -> dict[str, Any]:
    """Load the existing record; a malformed file is an error, never overwritten."""
    if not session_file.is_file():
        return {}
    try:
        loaded = json.loads(session_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise SessionError(
            "MALFORMED_SESSION",
            f"{session_file} is not readable JSON ({exc}); refusing to resume over it. "
            "Inspect or repair the file, or pass --force to overwrite it deliberately.",
        ) from exc
    if not isinstance(loaded, dict):
        raise SessionError(
            "MALFORMED_SESSION",
            f"{session_file} does not contain a JSON object; refusing to resume over it",
        )
    return loaded


def identity_warnings(existing: dict[str, Any], record: dict[str, Any]) -> list[str]:
    """Repository identities recorded at creation vs. the ones in play now."""
    warnings: list[str] = []
    recorded = existing.get("repositories")
    if not isinstance(recorded, dict) or not isinstance(
        recorded.get("analysis"), str
    ):
        raise SessionError(
            "RECORD_INCOMPLETE",
            "session.json records no usable repository identities (analysis "
            "path missing); repair the record or pass --force to rebind it "
            "deliberately",
        )
    for name in ("analysis", "manuscript"):
        was = recorded.get(name)
        now = record["repositories"][name]
        if was != now:
            warnings.append(f"{name} repository moved: recorded {was!r}, now {now!r}")
    return warnings


def merge_record(record: dict[str, Any], existing: dict[str, Any]) -> dict[str, Any]:
    """Refresh machine state while keeping created_at and owner-added keys."""
    merged = dict(record)
    created = existing.get("created_at")
    if isinstance(created, str) and created:
        merged["created_at"] = created
    if not record["checks"] and isinstance(existing.get("checks"), list):
        # A resume without --check keeps the recorded verification commands.
        merged["checks"] = list(existing["checks"])
    for key, value in existing.items():
        if key not in MANAGED_KEYS:
            merged[key] = value
    return merged


def write_record(session_file: Path, record: dict[str, Any]) -> None:
    # Per-process temporary name: concurrent writers must not share one .tmp.
    temporary = session_file.with_name(f"{session_file.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    temporary.replace(session_file)


def claim_session_file(session_file: Path) -> None:
    """Atomically claim the slug: exclusive creation of an empty session.json.

    Two concurrent starts whose identifiers normalize to one slug both pass the
    exists-check; only one may win this creation, the other gets SESSION_EXISTS.
    """
    try:
        os.close(os.open(session_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    except FileExistsError:
        raise SessionError(
            "SESSION_EXISTS",
            f"{session_file} was created concurrently; pass --resume to reopen it",
        ) from None


def write_task_contract(task_file: Path, phase: str, checks: list[str]) -> bool:
    """Write the contract only when absent. Returns True when written.

    Exclusive creation (O_EXCL): a contract created or repaired by an
    external process between any existence check and this write survives --
    the never-overwrite guarantee holds against non-cooperating writers too.
    """
    try:
        fd = os.open(task_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False
    try:
        os.write(fd, render_task_contract(phase, checks).encode("utf-8"))
    finally:
        os.close(fd)
    return True


# The documented five-line header (live-analysis.md) is the gate: phase plus
# these four. Verification command stays in the template but is optional.
CONTRACT_REQUIRED_SECTIONS = (
    "Objective:",
    "May change:",
    "Must not change:",
    "Done when:",
)
_CONTRACT_HEADINGS = (
    "Objective:",
    "May change:",
    "Must not change:",
    "Done when:",
    "Verification command:",
)


def _read_contract_text(task_file: Path) -> str:
    """Read TASK.md, converting decode and I/O failures into session errors."""
    try:
        return task_file.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as exc:
        raise SessionError(
            "CONTRACT_UNREADABLE",
            f"{task_file} cannot be read as UTF-8 text ({exc}); repair or "
            "replace the contract before continuing",
        ) from exc


def read_contract_phase(task_file: Path) -> str | None:
    """The 'Scientific phase:' value recorded in TASK.md, or None when absent."""
    if not task_file.is_file():
        return None
    for line in _read_contract_text(task_file).splitlines():
        if line.startswith("Scientific phase:"):
            return line.split(":", 1)[1].strip() or None
    return None


def read_contract_checks(task_file: Path) -> list[str]:
    """The verification commands recorded in TASK.md (the contract of record)."""
    if not task_file.is_file():
        return []
    checks: list[str] = []
    capturing = False
    for line in _read_contract_text(task_file).splitlines():
        stripped = line.strip()
        if stripped.startswith("Verification command:"):
            inline = stripped[len("Verification command:"):].strip()
            if inline:
                checks.append(inline)
            capturing = True
            continue
        if capturing and any(stripped.startswith(h) for h in _CONTRACT_HEADINGS):
            break
        if capturing and stripped:
            checks.append(stripped)
    return checks


def contract_incomplete(task_file: Path) -> str | None:
    """The first required contract section still empty, or None when filled.

    Both documented forms count as content: inline (``Objective: measure x``)
    and block (heading line followed by indented lines).
    """
    if not task_file.is_file():
        return "the contract (missing TASK.md)"
    lines = _read_contract_text(task_file).splitlines()
    if read_contract_phase(task_file) is None:
        return "'Scientific phase'"
    for section in CONTRACT_REQUIRED_SECTIONS:
        content: list[str] = []
        capturing = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(section):
                inline = stripped[len(section):].strip()
                if inline:
                    content.append(inline)
                capturing = True
                continue
            if capturing and any(stripped.startswith(h) for h in _CONTRACT_HEADINGS):
                break
            if capturing and stripped:
                content.append(stripped)
        if not content:
            return f"'{section.rstrip(':')}'"
    return None


def worktree_argv(
    worktree_path: Path,
    slug: str,
    *,
    branch_exists: bool,
    base_commit: str | None = None,
) -> list[str]:
    # `-b` creates the branch; recovery after a removed worktree must reuse the
    # preserved session branch instead, or every retry fails on the collision.
    # When both worktree and branch are gone, the recorded session commit is
    # the base -- basing on the canonical HEAD would resume old notebooks
    # against unrelated code.
    argv = ["git", "-C", str(ANALYSIS_ROOT), "worktree", "add", str(worktree_path)]
    if branch_exists:
        argv.append(f"session/{slug}")
        return argv
    argv.extend(["-b", f"session/{slug}"])
    if base_commit:
        argv.append(base_commit)
    return argv


def worktree_paths(repo: Path | None) -> list[Path]:
    """Every worktree path git lists for a repository.

    Fails CLOSED: an enumeration failure must not read as "no worktrees" --
    the containment guards would then wave through paths inside unenumerated
    checkouts.
    """
    if repo is None:
        return []
    raw = _git(["worktree", "list", "--porcelain"], repo)
    if raw is None:
        raise SessionError(
            "WORKTREE_ENUMERATION_FAILED",
            f"git could not enumerate worktrees for {repo}; repair the "
            "repository (or git availability) before continuing",
        )
    return [
        Path(line.split(" ", 1)[1])
        for line in raw.splitlines()
        if line.startswith("worktree ")
    ]


def analysis_worktree_paths() -> list[Path]:
    return worktree_paths(ANALYSIS_ROOT)


def registered_worktree(worktree_path: Path) -> bool:
    """True when git itself lists this path as a worktree of the analysis repo.

    A symlink at the session's worktree path is never accepted: resolving it
    would alias an external checkout while the record keeps advertising the
    session-local path.
    """
    if worktree_path.is_symlink():
        return False
    resolved = worktree_path.resolve()
    return any(p.resolve() == resolved for p in analysis_worktree_paths())


def add_worktree(
    worktree_path: Path,
    slug: str,
    base_commit: str | None = None,
    *,
    allow_branch_reuse: bool = False,
) -> tuple[bool, str | None]:
    if worktree_path.is_symlink():
        # A live symlink aliases an external checkout; a dangling one makes
        # `git worktree add` fail forever. Either way: reject, never create.
        return False, (
            f"{worktree_path} is a symlink (target "
            f"{'missing' if not worktree_path.exists() else 'external'}); "
            "remove it before creating the session worktree"
        )
    if worktree_path.exists():
        if not registered_worktree(worktree_path):
            return False, (
                f"{worktree_path} exists but is not a registered git worktree; "
                "remove or move it before creating the session worktree"
            )
        branch = _branch(worktree_path)
        if branch != f"session/{slug}":
            return False, (
                f"{worktree_path} is on branch {branch!r}, not session/{slug}; "
                "the session must not silently run against another branch"
            )
        return False, None
    branch_ref = f"refs/heads/session/{slug}"
    branch_preexisted = (
        _git(["rev-parse", "--verify", "--quiet", branch_ref], ANALYSIS_ROOT)
        is not None
    )
    if branch_preexisted and not allow_branch_reuse:
        # Only a session recorded as worktree-backed may reuse its preserved
        # branch; a NEW session colliding with an old session/<slug> must not
        # silently adopt that branch's history.
        return False, (
            f"branch session/{slug} already exists but this session was never "
            "worktree-backed; delete the stale branch (or resume the session "
            "that owns it) before creating a worktree here"
        )
    if branch_preexisted and allow_branch_reuse and base_commit:
        # Reuse must prove the preserved branch really is this session's:
        # the recorded base commit has to be an ancestor of the branch tip.
        # An unrelated branch that merely shares the slug fails this.
        ancestor_ok = (
            _git(
                ["merge-base", "--is-ancestor", base_commit, branch_ref],
                ANALYSIS_ROOT,
            )
            is not None
        )
        if not ancestor_ok:
            return False, (
                f"branch session/{slug} does not contain the session's "
                f"recorded base commit {base_commit[:12]}; it belongs to "
                "another lineage -- delete or rename it before recovery"
            )
    # Exclusive per-slug lock: two concurrent recoveries must not race, or the
    # loser's cleanup would tear down the winner's freshly registered worktree.
    lock_file = worktree_path.parent / f".{worktree_path.name}.creating"
    try:
        os.close(os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    except FileExistsError:
        return False, (
            f"another invocation is creating {worktree_path} (lock {lock_file} "
            "exists); wait for it, or remove the lock if its process died"
        )
    try:
        # Recheck under the lock: a concurrent recovery may have completed
        # creation between the pre-lock checks and acquisition. Adopting the
        # valid worktree here (instead of attempting another add) means its
        # creator's work can never be mistaken for our own failed attempt.
        if worktree_path.exists() and registered_worktree(worktree_path):
            branch = _branch(worktree_path)
            if branch != f"session/{slug}":
                return False, (
                    f"{worktree_path} is on branch {branch!r}, not "
                    f"session/{slug}; the session must not silently run "
                    "against another branch"
                )
            if base_commit:
                # The checkout appeared after planning: adopt it only if it
                # provably descends from the session's recorded base -- a
                # branch-name match alone does not prove lineage.
                tip = _head(worktree_path)
                lineage_ok = (
                    tip is not None
                    and _git(
                        ["merge-base", "--is-ancestor", base_commit, tip],
                        ANALYSIS_ROOT,
                    )
                    is not None
                )
                if not lineage_ok:
                    return False, (
                        f"{worktree_path} appeared during creation but does "
                        "not contain the session's recorded base commit "
                        f"{base_commit[:12]}; refusing to adopt it"
                    )
            return False, None
        if registered_worktree(worktree_path) and not worktree_path.exists():
            # Stale registration repair, under the lock so it can never race a
            # concurrent recreation: prune, then unlock a LOCKED registration
            # and prune again, then fall back to explicit removal.
            _git(["worktree", "prune"], ANALYSIS_ROOT)
            if registered_worktree(worktree_path):
                _git(["worktree", "unlock", str(worktree_path)], ANALYSIS_ROOT)
                _git(["worktree", "prune"], ANALYSIS_ROOT)
            if registered_worktree(worktree_path):
                if worktree_path.exists() and _head(worktree_path) is not None:
                    # A live checkout appeared during the repair (external
                    # writers do not honor our lock): never force-remove it.
                    return False, (
                        f"{worktree_path} became a live checkout during "
                        "stale-registration repair; re-run to re-evaluate it"
                    )
                _git(
                    ["worktree", "remove", "--force", str(worktree_path)],
                    ANALYSIS_ROOT,
                )
            if registered_worktree(worktree_path):
                return False, (
                    f"stale registration for {worktree_path} survived prune, "
                    "unlock, and forced removal; repair it manually"
                )
        # Recomputed UNDER the lock: a branch created concurrently between the
        # pre-lock check and acquisition must never be mistaken for one this
        # failed command created (cleanup would `branch -D` someone else's
        # unmerged work).
        branch_tip_in_lock = _git(
            ["rev-parse", "--verify", "--quiet", branch_ref], ANALYSIS_ROOT
        )
        branch_now_exists = branch_tip_in_lock is not None
        if branch_now_exists and not branch_preexisted:
            # The branch APPEARED between the pre-lock authorization checks
            # and here (external git processes do not honor our lock). Never
            # silently create-onto or reuse it: the reuse and lineage checks
            # ran against a world where it did not exist.
            if not (allow_branch_reuse and base_commit and (
                _git(
                    ["merge-base", "--is-ancestor", base_commit, branch_ref],
                    ANALYSIS_ROOT,
                )
                is not None
            )):
                return False, (
                    f"branch session/{slug} appeared concurrently during "
                    "creation and its lineage is unverified; re-run to "
                    "re-evaluate it"
                )
        try:
            proc = subprocess.run(
                worktree_argv(
                    worktree_path,
                    slug,
                    branch_exists=branch_now_exists,
                    base_commit=base_commit,
                ),
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as exc:
            return False, str(exc)
        if proc.returncode != 0:
            # A failed `worktree add -b` can leave a partial directory and the
            # freshly created branch behind; without cleanup the retry is
            # blocked. Branch deletion inside the cleanup is PROVEN-OWN only:
            # it requires that no branch existed at the in-lock check and that
            # the branch's current tip equals the base this add would have
            # created it from -- a concurrent writer's ref never matches both.
            our_base = base_commit or _git(["rev-parse", "HEAD"], ANALYSIS_ROOT)
            # Deletion authority passes the EXPECTED tip down; the cleanup
            # deletes via `update-ref -d <ref> <expected-old>`, which is
            # atomic -- if an external writer advanced the ref after this
            # point, the delete simply fails instead of destroying their work.
            branch_deletable = not branch_now_exists and our_base is not None
            _cleanup_failed_worktree(
                worktree_path,
                slug,
                not branch_deletable,
                expected_branch_tip=our_base if branch_deletable else None,
            )
            return False, (proc.stderr or proc.stdout or "").strip()
        return True, None
    finally:
        lock_file.unlink(missing_ok=True)


def _cleanup_failed_worktree(
    worktree_path: Path,
    slug: str,
    branch_preexisted: bool,
    expected_branch_tip: str | None = None,
) -> None:
    # A failed add can leave the path REGISTERED (e.g. a failing post-checkout
    # hook): remove it first, or the branch stays checked out and every retry
    # is blocked. Removal must be attributable to OUR failed attempt: a
    # registration whose checkout is complete (HEAD resolves) may be a
    # concurrent winner's and is left alone.
    if registered_worktree(worktree_path):
        if worktree_path.exists() and _head(worktree_path) is not None:
            print(
                f"WARNING: {worktree_path} is a complete registered checkout; "
                "leaving it for its owner rather than force-removing",
                file=sys.stderr,
            )
            return
        _git(["worktree", "remove", "--force", str(worktree_path)], ANALYSIS_ROOT)
    if worktree_path.exists() and not registered_worktree(worktree_path):
        parent_repo, _ = resolve_manuscript()
        foreign = parent_repo is not None and any(
            p.resolve() == worktree_path.resolve()
            for p in worktree_paths(parent_repo)
        )
        complete = (worktree_path / ".git").exists() and _head(
            worktree_path
        ) is not None
        if foreign or complete or not (worktree_path / ".git").exists():
            # A checkout another repository registered here, a complete
            # checkout, or a plain directory some other producer created is
            # not attributable to this failed add; leave it for its owner.
            # (Our own partial `worktree add` always leaves a .git entry.)
            print(
                f"WARNING: {worktree_path} is not attributable to this failed "
                "worktree add; leaving it rather than deleting",
                file=sys.stderr,
            )
            return
        shutil.rmtree(worktree_path, ignore_errors=True)
    _git(["worktree", "prune"], ANALYSIS_ROOT)
    if not branch_preexisted and expected_branch_tip:
        # Atomic compare-and-delete: `update-ref -d <ref> <expected-old>`
        # fails if the ref moved, so an external writer's advanced branch is
        # never deleted (branch -D would delete even unmerged commits).
        _git(
            [
                "update-ref",
                "-d",
                f"refs/heads/session/{slug}",
                expected_branch_tip,
            ],
            ANALYSIS_ROOT,
        )


def base_line(record: dict[str, Any]) -> str:
    origin = record["git"]["analysis"]["origin_main"]
    basis = origin["comparison_basis"]
    if origin["behind"] is None:
        return f"analysis: ahead/behind origin/main UNKNOWN ({basis})"
    line = f"analysis: {origin['ahead']} ahead, {origin['behind']} behind origin/main ({basis})"
    if origin["behind"]:
        return line + " -- STALE BASE, rebase before recording results"
    return line


def next_commands(record: dict[str, Any]) -> list[str]:
    # Kernel-only surface: the editor selects the project's own locked
    # interpreter directly. No user-level kernelspec is ever installed
    # (jupyter-surface.md forbids `ipykernel install --user`).
    project = shlex.quote(record.get("project", record["repositories"]["analysis"]))
    interpreter = shlex.quote(record["interpreter"])
    return [
        "1) fill in the contract, including its verification command",
        "   (the task boundary comes before any task work):",
        f"     edit {shlex.quote(record['workbench']['task_file'])}",
        "2) build or refresh the frozen environment (includes the kernel);",
        "   clearing VIRTUAL_ENV and UV_PROJECT_ENVIRONMENT keeps uv off any",
        "   inherited interpreter or alternate environment:",
        "     env -u VIRTUAL_ENV -u UV_PROJECT_ENVIRONMENT \\",
        f"       uv sync --frozen --group notebook --project {project}",
        "3) verify the interpreter:",
        f"     {interpreter} -c 'import sys; print(sys.executable, sys.version)'",
        "4) in the editor, select that interpreter as the notebook kernel",
        "   (no `ipykernel install --user`; the surface is kernel-only).",
    ]


def report(
    record: dict[str, Any], *, stream: Any, dry_run: bool, fresh: bool = False
) -> None:
    prefix = "DRY RUN: would open" if dry_run else record["state"]
    print(f"{prefix} {record['slug']} -> {record['workbench']['session_dir']}", file=stream)
    print(f"  contract: {record['workbench']['task_file']}", file=stream)
    print(f"  {base_line(record)}", file=stream)
    manuscript_error = record["git"]["manuscript"]["error"]
    if manuscript_error:
        print(f"  manuscript: UNRESOLVED -- {manuscript_error}", file=stream)
    else:
        print(f"  manuscript: {record['repositories']['manuscript']}", file=stream)
        if record["git"]["manuscript"]["gitlink_matches_analysis_head"] is False:
            pinned = record["git"]["manuscript"]["gitlink"]
            print(f"  manuscript pins analysis at {pinned} (not this HEAD)", file=stream)
    if record["worktree"]["created"]:
        print(f"  worktree: {record['worktree']['path']}", file=stream)
    else:
        # No manual `git worktree add` route: a by-hand worktree would leave
        # this record's project and interpreter pointing at the canonical
        # checkout, so branch work would silently run the wrong environment.
        if dry_run and fresh:
            # No record exists after a fresh dry run; --resume would return
            # NO_SESSION, so the recovery path starts with a real start.
            print(
                "  worktree: not created; run the start for real, fill in the "
                "contract, then rerun with --resume --worktree",
                file=stream,
            )
        else:
            print(
                "  worktree: not created; fill in the contract, then rerun with "
                "--resume --worktree (the printed environment commands refresh "
                "to the worktree on that resume)",
                file=stream,
            )
    print("next commands:", file=stream)
    for line in next_commands(record):
        print(f"  {line}", file=stream)


def cmd_start(
    *,
    issue: str,
    phase: str,
    event: str | None,
    checks: list[str],
    resume: bool,
    force: bool,
    worktree: bool,
    fetch: bool,
    dry_run: bool,
    as_json: bool,
) -> int:
    root = require_workbench_root()
    slug = session_slug(issue, event)
    session_dir = root / slug
    session_file = session_dir / SESSION_FILENAME
    if os.path.lexists(session_file) and (
        session_file.is_symlink() or not session_file.is_file()
    ):
        # A symlinked record would let resume run under another session's
        # ownership state; a broken link would dead-end every mode.
        raise SessionError(
            "RECORD_REDIRECTED",
            f"{session_file} is a symlink or not a regular file; the session "
            "record must be a plain file inside the session directory",
        )
    exists = session_file.is_file()

    if exists and not (resume or force):
        raise SessionError(
            "SESSION_EXISTS",
            f"{session_file} already exists; pass --resume to reopen it or --force to overwrite it",
        )
    if resume and not exists:
        raise SessionError(
            "NO_SESSION",
            f"nothing to resume at {session_file}; run start without --resume to create it",
        )
    if resume and checks:
        # A replacement list would update session.json while TASK.md kept the
        # old commands; the two records must never disagree.
        raise SessionError(
            "CHECKS_ON_RESUME",
            "--check cannot be combined with --resume; edit the verification "
            "command in TASK.md instead, which stays the human contract of record",
        )
    task_file = session_dir / TASK_FILENAME
    if task_file.exists() and (
        task_file.is_symlink()
        or not task_file.is_file()
        or task_file.resolve().parent != session_dir.resolve()
    ):
        # A redirected contract would carry the operator's edits (and any
        # `edit` instruction this launcher prints) outside the workbench.
        raise SessionError(
            "CONTRACT_REDIRECTED",
            f"{task_file} is a symlink or resolves outside the session "
            "directory; the contract must be a plain file in the session",
        )
    parent_repo_for_children, _ = resolve_manuscript()
    checkout_paths = {
        p.resolve()
        for repo in (ANALYSIS_ROOT, parent_repo_for_children)
        if repo is not None
        for p in worktree_paths(repo)
    }
    for child in ("scratch", "exports"):
        child_dir = session_dir / child
        # lexists catches broken symlinks (exists() is false for them); the
        # checkout comparison runs regardless of filesystem existence so a
        # stale registration cannot be recreated over.
        if child_dir.resolve() in checkout_paths or (
            os.path.lexists(child_dir)
            and (
                child_dir.is_symlink()
                or not child_dir.is_dir()
                or child_dir.resolve().parent != session_dir.resolve()
            )
        ):
            # Validated on EVERY invocation (create and resume): a redirected
            # managed directory would carry notebook writes out of the
            # workbench -- into a checkout or a read-only input tree.
            raise SessionError(
                "SESSION_CHILD_REDIRECTED",
                f"{child_dir} is a symlink, resolves outside the session "
                "directory, or is itself a registered checkout; managed "
                "session directories must be plain directories",
            )
    if not exists and not force and task_file.is_file():
        # A leftover contract with no session record is a half-deleted session;
        # silently pairing it with fresh options would let human and machine
        # state diverge from the first command.
        raise SessionError(
            "STALE_CONTRACT",
            f"{task_file} exists but {session_file} does not; pass --force to "
            "adopt the preserved contract deliberately (its phase and "
            "verification commands are validated against the supplied options)",
        )
    observed_generation: str | None = None
    if force:
        # --force must not replace the record while a worktree creation is in
        # flight: the replacement would swap the recorded base provenance
        # under the creator and strand its checkout behind lineage checks.
        live = read_existing_lenient(session_file)
        if isinstance(live.get("created_at"), str):
            observed_generation = live["created_at"]
        live_worktree = (
            live.get("worktree") if isinstance(live.get("worktree"), dict) else {}
        )
        if live_worktree.get("pending"):
            raise SessionError(
                "CREATION_IN_FLIGHT",
                f"{session_file} carries a live worktree-creation marker; wait "
                "for the creating invocation to finish (or repair its record) "
                "before forcing a replacement",
            )
    if force and task_file.is_file():
        # --force replaces session.json but never TASK.md; the supplied options
        # must agree with the contract that survives.
        if checks:
            raise SessionError(
                "CHECKS_ON_FORCE",
                "--check cannot be combined with --force while TASK.md exists; "
                "the preserved contract keeps its own verification commands",
            )
        stored_phase = read_contract_phase(task_file)
        if stored_phase is None:
            # Adopting a phase-less contract would create a session that can
            # never resume (the resume path raises PHASE_MISSING).
            raise SessionError(
                "PHASE_MISSING",
                f"{task_file} records no 'Scientific phase:' line; restore it "
                "before adopting the preserved contract with --force",
            )
        if stored_phase != PHASE_HEADER[phase]:
            raise SessionError(
                "PHASE_MISMATCH",
                f"the preserved contract records scientific phase {stored_phase!r} "
                f"but --force supplied {PHASE_HEADER[phase]!r}; edit TASK.md to "
                "change the phase",
            )
    if os.path.lexists(session_dir) and (
        session_dir.is_symlink()
        or not session_dir.is_dir()
        or session_dir.resolve().parent != root
    ):
        raise SessionError(
            "SESSION_DIR_NOT_PLAIN",
            f"{session_dir} is a symlink, not a directory, or resolves outside "
            "the workbench root; session directories must be plain directories "
            "under the workbench",
        )
    # Checked regardless of filesystem existence: a stale registration whose
    # directory was deleted would otherwise let a fresh start recreate the
    # path, then dead-end every later resume on this same guard.
    parent_repo, _ = resolve_manuscript()
    resolved_session = session_dir.resolve()
    for repo in (ANALYSIS_ROOT, parent_repo):
        if repo is None:
            continue
        if any(p.resolve() == resolved_session for p in worktree_paths(repo)):
            raise SessionError(
                "SESSION_DIR_IS_CHECKOUT",
                f"{session_dir} is a registered git worktree of {repo}; a "
                "session must never write its records inside a checkout",
            )

    fetch_error = fetch_origin_main(ANALYSIS_ROOT) if (fetch and not dry_run) else None
    worktree_dir = session_dir / "worktree"
    parent_for_target, _ = resolve_manuscript()
    if parent_for_target is not None and any(
        p.resolve() == worktree_dir.resolve()
        for p in worktree_paths(parent_for_target)
    ):
        # A manuscript-repository registration at this path (stale or live)
        # would leave two repositories claiming one directory after an
        # analysis checkout is created there.
        raise SessionError(
            "WORKTREE_TARGET_FOREIGN",
            f"{worktree_dir} is registered as a worktree of the manuscript "
            "repository; prune that registration before using this session",
        )
    worktree_registered = registered_worktree(worktree_dir)
    if worktree_registered and not worktree_dir.is_dir():
        # A deleted-but-unpruned worktree has a registration and no directory.
        # Planning NEVER repairs it here -- an unlocked prune would race a
        # concurrent recreation and tear down the winner's fresh worktree. The
        # repair happens inside add_worktree, under the per-session lock;
        # plain resume is directed there via WORKTREE_MISSING.
        if not resume:
            # A fresh session over a stale registration would strand its
            # advertised recovery: the surviving session/<slug> branch is
            # rejected later because the new record never owned a worktree.
            raise SessionError(
                "STALE_WORKTREE_REGISTRATION",
                f"{worktree_dir} has a stale git registration (directory "
                "missing); prune it (git worktree prune) and delete any "
                f"surviving session/{slug} branch before starting fresh",
            )
        print(
            f"WARNING: stale worktree registration at {worktree_dir} "
            "(directory missing); --resume --worktree repairs it under the "
            "session lock",
            file=sys.stderr,
        )
        worktree_registered = False
    if worktree_registered:
        # Never adopt a worktree that was switched to another branch, whether
        # or not --worktree was passed this time.
        wt_branch = _branch(worktree_dir)
        if wt_branch != f"session/{slug}":
            raise SessionError(
                "WORKTREE_BRANCH_MISMATCH",
                f"{worktree_dir} is on branch {wt_branch!r}, not session/{slug}; "
                "the session must not silently run against another branch",
            )
    session_project = worktree_dir if (worktree or worktree_registered) else None
    git_state, parent = collect_git_state(
        fetched=fetch and not fetch_error and not dry_run,
        analysis_checkout=worktree_dir if worktree_registered else None,
    )
    record = build_record(
        project=session_project,
        slug=slug,
        issue=issue,
        event=event,
        checks=checks,
        root=root,
        session_dir=session_dir,
        git_state=git_state,
        parent=parent,
        state="resumed" if resume else "created",
    )
    if fetch_error:
        record["warnings"].append(f"fetch failed: {fetch_error}")

    if force and task_file.is_file():
        # The preserved contract's commands carry into the replacement record.
        record["checks"] = read_contract_checks(task_file)

    if worktree_registered and not resume:
        # A fresh session (including --force replacement) must never adopt a
        # pre-registered checkout at its worktree path: no record proves the
        # checkout's lineage.
        raise SessionError(
            "WORKTREE_UNRECORDED",
            f"{worktree_dir} is already a registered worktree but this is a "
            "fresh session with no record of creating it; remove the worktree "
            "before starting",
        )

    branch_reuse_ok = False
    if resume:
        existing = read_existing(session_file)
        recorded_worktree_state = existing.get("worktree")
        if not isinstance(recorded_worktree_state, dict) or not isinstance(
            recorded_worktree_state.get("created"), bool
        ):
            raise SessionError(
                "MALFORMED_SESSION",
                f"{session_file} lacks a valid worktree record; refusing to derive "
                "recovery state from an incomplete session -- repair the file or "
                "pass --force to overwrite it deliberately",
            )
        # `pending` marks ownership persisted just before `git worktree add`,
        # so an interruption between creation and the final record write still
        # leaves a recoverable session.
        recorded_worktree = recorded_worktree_state["created"] or bool(
            recorded_worktree_state.get("pending")
        )
        branch_reuse_ok = bool(recorded_worktree)
        if worktree_registered and not recorded_worktree:
            # A registered worktree the record never created -- even on the
            # right branch -- may be based on an unrelated commit; adopting it
            # would silently swap the code under the session's notebooks.
            raise SessionError(
                "WORKTREE_UNRECORDED",
                f"{worktree_dir} is a registered worktree but this session's "
                "record never created one; remove it or repair the record "
                "before resuming",
            )
        if (
            worktree_registered
            and not recorded_worktree_state["created"]
            and recorded_worktree_state.get("pending")
        ):
            # pending ownership adopts an already-registered checkout without
            # going through add_worktree's ancestry check, so prove lineage
            # here: the recorded base must be an ancestor of the checkout tip.
            pending_base = recorded_analysis_head(existing)
            tip = _head(worktree_dir)
            lineage_ok = (
                isinstance(pending_base, str)
                and tip is not None
                and _git(
                    ["merge-base", "--is-ancestor", pending_base, tip],
                    ANALYSIS_ROOT,
                )
                is not None
            )
            if not lineage_ok:
                raise SessionError(
                    "WORKTREE_LINEAGE_MISMATCH",
                    f"{worktree_dir} does not contain the session's recorded "
                    "base commit; the pending recovery cannot adopt an "
                    "unrelated checkout -- remove it or repair the record",
                )
        if recorded_worktree and not worktree_registered and not worktree:
            raise SessionError(
                "WORKTREE_MISSING",
                f"the session records a worktree at {worktree_dir} but git no longer "
                "lists it; recreate it with --resume --worktree or repair it before "
                "resuming, so notebook work cannot silently fall back to the "
                "canonical checkout",
            )
        recorded_schema = existing.get("schema_version")
        if recorded_schema != SCHEMA_VERSION:
            raise SessionError(
                "SCHEMA_MISMATCH",
                f"session records schema_version={recorded_schema!r} but this launcher "
                f"writes version {SCHEMA_VERSION}; refusing to silently rewrite the record",
            )
        stored_phase = read_contract_phase(session_dir / TASK_FILENAME)
        if stored_phase is None:
            raise SessionError(
                "PHASE_MISSING",
                f"{session_dir / TASK_FILENAME} records no 'Scientific phase:' line; "
                "restore it before resuming -- a session without a declared phase "
                "must not be activated",
            )
        if stored_phase != PHASE_HEADER[phase]:
            raise SessionError(
                "PHASE_MISMATCH",
                f"the contract records scientific phase {stored_phase!r} but this resume "
                f"supplied {PHASE_HEADER[phase]!r}; a phase change must be an explicit "
                "edit to TASK.md, not a resume flag",
            )
        for name, value in (("issue", issue), ("event", event)):
            if name not in existing:
                # A record without its identity fields cannot prove which
                # session it is; accepting any same-slug identifier would let
                # a resume silently relabel it.
                raise SessionError(
                    "RECORD_INCOMPLETE",
                    f"{session_file} records no {name!r} field; repair the "
                    "record before resuming",
                )
            was = existing.get(name)
            if was != value:
                raise SessionError(
                    "IDENTITY_MISMATCH",
                    f"session records {name}={was!r} but this resume supplied {value!r}; "
                    "distinct identifiers that share a slug must not relabel a session",
                )
        record["warnings"].extend(identity_warnings(existing, record))
        record = merge_record(record, existing)
        # TASK.md is the contract of record: the machine field follows it
        # unconditionally, including down to empty when the operator cleared
        # the commands (--worktree still rejects an incomplete contract).
        record["checks"] = read_contract_checks(session_dir / TASK_FILENAME)
        record["state"] = "resumed"

    # The reported flag reflects live git state even on --dry-run, so a
    # resume of a registered worktree is never told to recreate it.
    record["worktree"]["created"] = worktree_registered

    if not dry_run:
        if not resume:
            session_dir.mkdir(parents=True, exist_ok=True)
            if not exists:
                # Atomic claim: serializes concurrent starts on one slug.
                claim_session_file(session_file)
            # Resume must never touch scratch/ or exports/; redirection was
            # already rejected above for both create and resume.
            for child in ("scratch", "exports"):
                (session_dir / child).mkdir(parents=True, exist_ok=True)
            # Contract creation and the record write share the session lock:
            # two overlapping --force invocations must not interleave their
            # absence check and write, or TASK.md could come from one while
            # session.json comes from the other.
            with session_write_lock(session_file):
                pre_write = read_existing_lenient(session_file)
                pre_gen = (
                    pre_write["created_at"]
                    if isinstance(pre_write.get("created_at"), str)
                    else None
                )
                if pre_gen != observed_generation:
                    # The record changed between validation and this locked
                    # initialization write (a concurrent --force completed, or
                    # a force landed after our fresh claim): abort instead of
                    # restoring a stale generation the later guard would then
                    # trust.
                    raise SessionError(
                        "RECORD_REPLACED",
                        f"{session_file} was replaced between validation and "
                        "initialization; re-run against the new record",
                    )
                contract_written = write_task_contract(
                    session_dir / TASK_FILENAME, phase, checks
                )
                if not contract_written:
                    # A concurrent invocation created the contract between our
                    # pre-lock validation and this lock (applies to --force
                    # AND a fresh claimant): revalidate against the contract
                    # that actually survives.
                    surviving_phase = read_contract_phase(
                        session_dir / TASK_FILENAME
                    )
                    if surviving_phase != PHASE_HEADER[phase]:
                        if not exists:
                            # Release OUR zero-byte claim, or every retry
                            # dead-ends on SESSION_EXISTS / MALFORMED_SESSION.
                            session_file.unlink(missing_ok=True)
                        raise SessionError(
                            "PHASE_MISMATCH",
                            "a concurrent invocation wrote the contract with "
                            f"phase {surviving_phase!r} but this start "
                            f"supplied {PHASE_HEADER[phase]!r}; re-run against "
                            "the surviving contract",
                        )
                    record["checks"] = read_contract_checks(
                        session_dir / TASK_FILENAME
                    )
                # Replace the zero-byte claim with a valid record immediately,
                # so an expected rejection below (e.g. the contract gate on a
                # fresh `start --worktree`) leaves a resumable session, not a
                # malformed file, preserving any concurrent invocation's
                # ownership markers (--force racing a creator).
                on_disk = read_existing_lenient(session_file)
                disk_worktree = (
                    on_disk.get("worktree")
                    if isinstance(on_disk.get("worktree"), dict)
                    else {}
                )
                disk_pending = disk_worktree.get("pending")
                if force and disk_pending and disk_pending != _INVOCATION_TOKEN:
                    # Rechecked under the lock: a creation that started after
                    # the pre-lock check must still block the forced
                    # replacement, or the creator's recorded base would be
                    # swapped mid-creation.
                    raise SessionError(
                        "CREATION_IN_FLIGHT",
                        f"{session_file} gained a live worktree-creation "
                        "marker while this --force ran; wait for the creating "
                        "invocation before forcing a replacement",
                    )
                if disk_pending and disk_pending != _INVOCATION_TOKEN:
                    record["worktree"]["pending"] = disk_pending
                if disk_worktree.get("created"):
                    record["worktree"]["created"] = True
                write_record(session_file, record)
        worktree_owned = False
        if worktree:
            # The task boundary comes before repository-changing side effects
            # (live-analysis.md): no worktree until the contract is filled in.
            incomplete = contract_incomplete(session_dir / TASK_FILENAME)
            if incomplete:
                raise SessionError(
                    "CONTRACT_INCOMPLETE",
                    f"fill in {incomplete} in {session_dir / TASK_FILENAME} before "
                    "creating the session worktree; rerun with --worktree afterwards",
                )
            recorded_head = None
            if resume:
                recorded_head = recorded_analysis_head(existing)
            else:
                # Forced and fresh creations pass their planned base too, so
                # the appeared-checkout lineage gate applies to every
                # worktree-creating invocation.
                recorded_head = recorded_analysis_head(record)
            if branch_reuse_ok and not worktree_registered and not isinstance(
                recorded_head, str
            ):
                # Recreating a worktree-backed session without its recorded
                # commit would silently base the branch on the canonical
                # HEAD -- unrelated code under old notebooks.
                raise SessionError(
                    "RECORD_INCOMPLETE",
                    f"{session_file} marks this session worktree-backed but "
                    "records no git.analysis.head commit; repair the record "
                    "before recreating the worktree",
                )
            # Persist ownership BEFORE creating (under the record lock): an
            # interruption between the add and the final record write must not
            # orphan the worktree behind WORKTREE_UNRECORDED. The token marks
            # the marker as THIS invocation's.
            with session_write_lock(session_file):
                # Never replace a DIFFERENT invocation's live marker: its
                # crash-recovery protection must survive this invocation's
                # attempt (which will lose the creation lock anyway).
                on_disk = read_existing_lenient(session_file)
                if (
                    isinstance(on_disk.get("created_at"), str)
                    and on_disk["created_at"] != record.get("created_at")
                ):
                    # A concurrent --force completed since this invocation
                    # read the record; writing would silently undo it and the
                    # later generation guard could not tell.
                    raise SessionError(
                        "RECORD_REPLACED",
                        f"{session_file} was replaced by another invocation "
                        "before creation began; re-run against the new record",
                    )
                disk_pending = (
                    on_disk.get("worktree", {}).get("pending")
                    if isinstance(on_disk.get("worktree"), dict)
                    else None
                )
                if disk_pending and disk_pending != _INVOCATION_TOKEN:
                    record["worktree"]["pending"] = disk_pending
                else:
                    record["worktree"]["pending"] = _INVOCATION_TOKEN
                write_record(session_file, record)
            created, failure = add_worktree(
                worktree_dir,
                slug,
                recorded_head,
                allow_branch_reuse=resume and branch_reuse_ok,
            )
            if failure:
                # Under the lock: drop OUR marker unless the session already
                # owned its worktree lineage before this attempt (a verified
                # recovery must stay retryable); always preserve a concurrent
                # invocation's marker (different token) and created state.
                if not (resume and branch_reuse_ok):
                    record["worktree"].pop("pending", None)
                with session_write_lock(session_file):
                    latest = read_existing_lenient(session_file)
                    if (
                        isinstance(latest.get("created_at"), str)
                        and latest["created_at"] != record.get("created_at")
                    ):
                        # A concurrent --force replaced the record while this
                        # failed creation ran; the stale failure record must
                        # not undo it.
                        print(f"ERROR WORKTREE_FAILED: {failure}", file=sys.stderr)
                        raise SessionError(
                            "RECORD_REPLACED",
                            f"{session_file} was replaced by another "
                            "invocation during the failed creation; re-run "
                            "against the new record",
                        )
                    locked_phase = read_contract_phase(
                        session_dir / TASK_FILENAME
                    )
                    if locked_phase != PHASE_HEADER[phase]:
                        print(
                            f"ERROR WORKTREE_FAILED: {failure}", file=sys.stderr
                        )
                        raise SessionError(
                            "PHASE_MISMATCH",
                            "the contract's phase changed to "
                            f"{locked_phase!r} during the failed creation; "
                            "re-run against the current contract",
                        )
                    record["checks"] = read_contract_checks(
                        session_dir / TASK_FILENAME
                    )
                    latest_worktree = (
                        latest.get("worktree")
                        if isinstance(latest.get("worktree"), dict)
                        else {}
                    )
                    other_pending = latest_worktree.get("pending")
                    creation_active = (
                        worktree_dir.parent / f".{worktree_dir.name}.creating"
                    ).exists()
                    winner_uncommitted = registered_worktree(
                        worktree_dir
                    ) and not latest_worktree.get("created")
                    if other_pending and (
                        other_pending != _INVOCATION_TOKEN
                        or creation_active
                        or winner_uncommitted
                    ):
                        # Keep a foreign token always; keep even our own while
                        # another invocation holds the creation lock -- the
                        # marker may be the only crash protection the active
                        # creator has (it may have preserved ours instead of
                        # writing its own).
                        record["worktree"]["pending"] = other_pending
                    if latest_worktree.get("created"):
                        # The winner finished: carry the winner's VALIDATED
                        # fields from its final write; a fresh sample could
                        # capture a checkout switched after the winner's
                        # validation, poisoning the trusted base.
                        record["worktree"]["created"] = True
                        if isinstance(latest.get("git"), dict):
                            record["git"] = latest["git"]
                            if isinstance(latest.get("project"), str):
                                record["project"] = latest["project"]
                            if isinstance(latest.get("interpreter"), str):
                                record["interpreter"] = latest["interpreter"]
                        else:
                            sampled_git, _ = collect_git_state(
                                analysis_checkout=worktree_dir
                            )
                            sampled_ok = (
                                isinstance(sampled_git.get("analysis"), dict)
                                and sampled_git["analysis"].get("branch")
                                == f"session/{slug}"
                            )
                            if sampled_ok:
                                record["project"] = str(worktree_dir)
                                record["interpreter"] = str(
                                    interpreter_path(worktree_dir)
                                )
                                record["git"] = sampled_git
                            else:
                                record["worktree"]["created"] = False
                                record["worktree"]["pending"] = (
                                    other_pending or _INVOCATION_TOKEN
                                )
                    write_record(session_file, record)
                print(f"ERROR WORKTREE_FAILED: {failure}", file=sys.stderr)
                return 1
            record["worktree"].pop("pending", None)
            worktree_owned = True
            if created:
                # Provenance must describe the worktree the kernel runs against.
                record["git"], _ = collect_git_state(
                    fetched=fetch and not fetch_error,
                    analysis_checkout=worktree_dir,
                )
        # The final read-merge-write runs under the same per-slug lock every
        # ownership write uses, so the marker's whole lifetime (pending ->
        # created) is serialized against this replacement: no stale
        # created=false can land after either.
        with session_write_lock(session_file):
            now_registered = registered_worktree(worktree_dir)
            latest = read_existing_lenient(session_file)
            if (
                isinstance(latest.get("created_at"), str)
                and latest["created_at"] != record.get("created_at")
            ):
                # EVERY initializer checks its record generation: a concurrent
                # --force (or a force undone by a delayed fresh claimant)
                # replaced the record after this invocation last wrote it;
                # overwriting would silently undo that reset.
                raise SessionError(
                    "RECORD_REPLACED",
                    f"{session_file} was replaced by another invocation while "
                    "this one ran; re-run against the new record",
                )
            if resume:
                # Same-generation resumes can still cross-edit: reread the
                # contract under the lock so the record follows the contract
                # that actually survives, and abort on a phase change.
                locked_phase = read_contract_phase(session_dir / TASK_FILENAME)
                if locked_phase != PHASE_HEADER[phase]:
                    raise SessionError(
                        "PHASE_MISMATCH",
                        f"the contract's phase changed to {locked_phase!r} "
                        "while this resume ran; re-run against the current "
                        "contract",
                    )
                record["checks"] = read_contract_checks(
                    session_dir / TASK_FILENAME
                )
            latest_worktree = (
                latest.get("worktree")
                if isinstance(latest.get("worktree"), dict)
                else {}
            )
            # Adoption of a late-registered worktree requires OWNERSHIP: this
            # invocation created/verified it, the resumed record owned it, or
            # the on-disk record shows a live marker. A checkout somebody
            # registered out of band is never silently adopted.
            owned = (
                worktree_owned
                or branch_reuse_ok
                or bool(latest_worktree.get("pending"))
                or bool(latest_worktree.get("created"))
            )
            branch_still_ours = (
                _branch(worktree_dir) == f"session/{slug}"
                if now_registered
                else False
            )
            if now_registered and owned and not branch_still_ours:
                # Someone switched the checkout's branch after the planning
                # checks; recording it as this session's would report the old
                # branch while the interpreter runs the new one.
                print(
                    f"WARNING: {worktree_dir} is no longer on session/{slug}; "
                    "not recording it as this session's worktree",
                    file=sys.stderr,
                )
            adopt = now_registered and owned and branch_still_ours
            validated_tip = None
            if adopt:
                # The branch name alone does not prove history: a reset to
                # unrelated commits keeps the name. Re-prove the recorded base
                # is an ancestor of the checkout's CURRENT tip.
                final_base = recorded_analysis_head(
                    existing if resume else record
                )
                if final_base is None:
                    # Missing provenance rejects adoption, matching the
                    # missing- and pending-recovery paths.
                    print(
                        f"WARNING: {worktree_dir} cannot be adopted -- the "
                        "record holds no valid git.analysis.head to prove "
                        "lineage against; repair the record",
                        file=sys.stderr,
                    )
                    adopt = False
                if final_base is not None:
                    final_tip = _head(worktree_dir)
                    if final_tip is None or (
                        _git(
                            ["merge-base", "--is-ancestor", final_base, final_tip],
                            ANALYSIS_ROOT,
                        )
                        is None
                    ):
                        print(
                            f"WARNING: {worktree_dir} no longer contains the "
                            "session's recorded base commit; not recording it "
                            "as this session's worktree",
                            file=sys.stderr,
                        )
                        adopt = False
                    else:
                        validated_tip = final_tip
            if adopt:
                # Provenance is ALWAYS rebuilt from the checkout being
                # adopted -- a stale recorded commit must never survive next
                # to a live interpreter running different code. The sample is
                # validated against the values the checks above proved: a
                # reset or switch between validation and sampling must not be
                # recorded as owned.
                sampled_git, _ = collect_git_state(
                    fetched=fetch and not fetch_error,
                    analysis_checkout=worktree_dir,
                )
                sampled = (
                    sampled_git.get("analysis")
                    if isinstance(sampled_git.get("analysis"), dict)
                    else {}
                )
                sample_valid = sampled.get("branch") == f"session/{slug}"
                if sample_valid:
                    # The reference is the tip the ancestry check VALIDATED,
                    # not a fresh read (a reset between validation and
                    # sampling would fool a fresh read).
                    reference_tip = validated_tip or _head(worktree_dir)
                    sample_valid = (
                        sampled.get("head") is not None
                        and sampled.get("head") == reference_tip
                    )
                if not sample_valid:
                    print(
                        f"WARNING: {worktree_dir} changed between validation "
                        "and provenance sampling; not adopting it",
                        file=sys.stderr,
                    )
                    adopt = False
                else:
                    record["project"] = str(worktree_dir)
                    record["interpreter"] = str(interpreter_path(worktree_dir))
                    record["git"] = sampled_git
            if now_registered and not owned:
                print(
                    f"WARNING: {worktree_dir} was registered by an unrecorded "
                    "party during this invocation; not adopting it",
                    file=sys.stderr,
                )
            record["worktree"]["created"] = adopt
            if now_registered and owned and not adopt:
                # Final validation (branch or lineage) refused an OWNED
                # checkout; retain ownership as a pending marker so the
                # supported --resume --worktree recovery stays available once
                # the operator restores the correct branch or lineage.
                record["worktree"]["pending"] = (
                    latest_worktree.get("pending") or _INVOCATION_TOKEN
                )
                # And never persist provenance sampled from the REJECTED
                # checkout: restore the trusted recorded state (resume) or
                # recollect from the canonical checkout, so the untrusted tip
                # cannot become the next resume's recorded base.
                if resume and isinstance(existing.get("git"), dict):
                    record["git"] = existing["git"]
                else:
                    record["git"], _ = collect_git_state(
                        fetched=fetch and not fetch_error
                    )
                # Never route commands at the REJECTED checkout: until
                # --resume --worktree revalidates it, the canonical checkout
                # is the only safe execution surface.
                record["project"] = str(ANALYSIS_ROOT)
                record["interpreter"] = str(interpreter_path())
            if not now_registered and owned:
                # A previously verified checkout vanished mid-invocation; git
                # preserves its session/<slug> branch, so KEEP ownership (as a
                # pending marker) or the supported --resume --worktree
                # recovery would refuse the branch as never worktree-backed.
                record["worktree"]["pending"] = (
                    latest_worktree.get("pending") or _INVOCATION_TOKEN
                )
                print(
                    f"WARNING: {worktree_dir} disappeared during this "
                    "invocation; ownership retained for recovery with "
                    "--resume --worktree",
                    file=sys.stderr,
                )
                # Never route commands at the vanished checkout.
                record["project"] = str(ANALYSIS_ROOT)
                record["interpreter"] = str(interpreter_path())
            other_pending = latest_worktree.get("pending")
            if (
                other_pending
                and other_pending != _INVOCATION_TOKEN
                and not record["worktree"].get("created")
            ):
                record["worktree"]["pending"] = other_pending
            write_record(session_file, record)

    stream = sys.stderr if as_json else sys.stdout
    for warning in record["warnings"]:
        print(f"WARNING: {warning}", file=sys.stderr)
    report(record, stream=stream, dry_run=dry_run, fresh=not (resume or exists))
    if as_json:
        print(json.dumps(record, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    start = sub.add_parser("start", help="open, resume, or plan a session workbench")
    start.add_argument("--issue", required=True, help="wayfinder or GitHub issue identifier")
    start.add_argument("--phase", required=True, choices=PHASES, help="scientific phase")
    start.add_argument("--event", help="burst or event name the session is about")
    start.add_argument(
        "--check",
        action="append",
        dest="checks",
        default=[],
        help="verification command for TASK.md (repeatable)",
    )
    existing = start.add_mutually_exclusive_group()
    existing.add_argument(
        "--resume", action="store_true", help="reopen an existing session after identity checks"
    )
    existing.add_argument(
        "--force", action="store_true", help="overwrite an existing session.json"
    )
    start.add_argument(
        "--worktree",
        action="store_true",
        help="create the git worktree instead of only printing the command",
    )
    start.add_argument(
        "--fetch",
        action="store_true",
        help="fetch origin/main first; off by default, so ahead/behind uses the local ref",
    )
    start.add_argument("--dry-run", action="store_true", help="print the plan, write nothing")
    start.add_argument("--json", action="store_true", help="print the session record as JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "start":
        try:
            return cmd_start(
                issue=args.issue,
                phase=args.phase,
                event=args.event,
                checks=list(args.checks or []),
                resume=args.resume,
                force=args.force,
                worktree=args.worktree,
                fetch=args.fetch,
                dry_run=args.dry_run,
                as_json=args.json,
            )
        except (SessionError, FileNotFoundError) as exc:
            print(f"ERROR {exc}", file=sys.stderr)
            return 2
    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
