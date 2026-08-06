#!/usr/bin/env python3

import subprocess
from collections import defaultdict
from pathlib import Path

import tomllib

ROOT = Path(__file__).parents[1]
REGISTRY = ROOT / "analysis/docs/rse/control/results-registry.toml"


def required_commits(registry: dict[str, object]) -> dict[str, tuple[str, ...]]:
    commits: dict[str, set[str]] = defaultdict(set)
    for result in registry.get("result", []):
        for ref in result.get("provenance_refs", []):
            repository = ref.get("repository")
            commit = ref.get("commit")
            if repository in {"analysis", "manuscript"} and commit:
                commits[repository].add(commit)
    return {repository: tuple(sorted(values)) for repository, values in commits.items()}


def main() -> int:
    repositories = {
        "analysis": ROOT / "analysis",
        "manuscript": ROOT,
    }
    registry = tomllib.loads(REGISTRY.read_text())
    for repository, commits in required_commits(registry).items():
        missing = [
            commit
            for commit in commits
            if subprocess.run(
                ["git", "-C", str(repositories[repository]), "cat-file", "-e", commit],
                check=False,
                capture_output=True,
            ).returncode
        ]
        if missing:
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(repositories[repository]),
                    "fetch",
                    "--no-tags",
                    "--depth=1",
                    "origin",
                    *missing,
                ],
                check=True,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
