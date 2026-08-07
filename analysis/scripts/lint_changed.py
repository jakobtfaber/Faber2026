#!/usr/bin/env python3
"""Lint Python files changed by the commit or pull-request merge."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _resolve_base() -> str | None:
    base = os.environ.get("BASE_SHA")
    if base:
        return base
    # No BASE_SHA (e.g. workflow_dispatch): derive one. A shallow CI checkout
    # has no origin/main ref, so fetch it before asking for the merge base;
    # when even that fails, return None and the caller lints everything.
    # The explicit destination refspec matters: a bare `fetch origin main`
    # writes only FETCH_HEAD, leaving refs/remotes/origin/main absent and the
    # retry below failing exactly as before.
    fetch_main = [
        "git",
        "fetch",
        "--no-tags",
        "--depth=50",
        "origin",
        "+refs/heads/main:refs/remotes/origin/main",
    ]
    for prepare in (None, fetch_main):
        if prepare is not None:
            subprocess.run(prepare, cwd=ROOT, check=False, capture_output=True)
        found = subprocess.run(
            ["git", "merge-base", "origin/main", "HEAD"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if found.returncode == 0 and found.stdout.strip():
            return found.stdout.strip()
    return None


def main() -> int:
    base = _resolve_base()
    if base is None:
        # Only non-pull-request contexts (workflow_dispatch on a shallow,
        # credential-less checkout) land here. HEAD^ is a deterministic
        # fallback that still lints the newest commit's changes instead of
        # silently passing the gate; a repository without a parent commit
        # fails closed.
        head_parent = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", "HEAD^"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if head_parent.returncode == 0 and head_parent.stdout.strip():
            print("No origin/main base; falling back to HEAD^ for lint scope.")
            base = head_parent.stdout.strip()
        else:
            print("No diff base resolvable and no parent commit; failing.")
            return 1
    changed = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "--diff-filter=ACMR",
            base,
            "HEAD",
            "--",
            "*.py",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    paths = [path for path in changed if (ROOT / path).is_file()]
    if not paths:
        print("No changed Python files.")
        return 0
    return subprocess.run(["ruff", "check", *paths], cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
