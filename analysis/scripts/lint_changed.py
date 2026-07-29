#!/usr/bin/env python3
"""Lint Python files changed by the commit or pull-request merge."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    base = os.environ.get("BASE_SHA")
    if not base:
        base = subprocess.run(
            ["git", "merge-base", "origin/main", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    changed = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMR", base, "HEAD", "--", "*.py"],
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
