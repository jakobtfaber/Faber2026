"""Notebook policy: no new tracked notebooks beyond the grandfathered allowlist.

New exploratory notebooks live under ~/Data/Faber2026/workbench/ and are never
tracked (docs/rse/ops/live-analysis.md). The notebooks already in the
repository are grandfathered: config/grandfathered-notebooks.txt is the sole
list of permitted tracked notebooks, and this test freezes it.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ALLOWLIST = REPO_ROOT / "config" / "grandfathered-notebooks.txt"


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True
    )


def _allowlist_lines() -> list[str]:
    return [
        line.strip()
        for line in ALLOWLIST.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]


def test_tracked_notebooks_exactly_match_allowlist():
    tracked = _git("ls-files", "*.ipynb")
    assert tracked.returncode == 0, tracked.stderr
    tracked_set = set(tracked.stdout.split())
    allow_set = set(_allowlist_lines())
    added = sorted(tracked_set - allow_set)
    removed = sorted(allow_set - tracked_set)
    assert tracked_set == allow_set, (
        f"tracked notebooks diverge from the grandfathered allowlist; "
        f"newly tracked (not permitted): {added}; "
        f"listed but no longer tracked: {removed}"
    )


def test_allowlist_entries_exist_and_are_well_formed():
    lines = _allowlist_lines()
    assert lines, "allowlist is empty"
    assert len(lines) == len(set(lines)), "duplicate entries in allowlist"
    for entry in lines:
        assert not Path(entry).is_absolute(), f"absolute path in allowlist: {entry}"
        assert (REPO_ROOT / entry).is_file(), f"allowlist entry missing: {entry}"


def test_new_notebook_paths_are_ignored():
    for candidate in ("scratch/new.ipynb", "notebooks/exploratory.ipynb"):
        result = _git("check-ignore", "--quiet", candidate)
        assert result.returncode == 0, (
            f"{candidate} is not gitignored; new notebooks must not be trackable"
        )


def test_checkpoint_directories_are_ignored():
    result = _git("check-ignore", "--quiet", ".ipynb_checkpoints/anything.ipynb")
    assert result.returncode == 0
