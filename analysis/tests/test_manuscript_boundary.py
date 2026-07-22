"""Fail-closed checks for the Overleaf manuscript projection."""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOUNDARY = ROOT / "manuscript-boundary.txt"
GITLINKS = {"analysis", "pipeline"}
EDITABLE_SUFFIXES = {
    ".bib",
    ".bst",
    ".cls",
    ".csv",
    ".html",
    ".json",
    ".md",
    ".py",
    ".sh",
    ".sty",
    ".tex",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}


def _index() -> dict[str, str]:
    output = subprocess.run(
        ["git", "ls-files", "--stage", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    entries: dict[str, str] = {}
    for raw in output.split(b"\0"):
        if not raw:
            continue
        metadata, raw_path = raw.split(b"\t", 1)
        mode = metadata.split(b" ", 1)[0].decode()
        entries[raw_path.decode()] = mode
    return entries


def _allowlist() -> set[str]:
    return {
        line.strip()
        for line in BOUNDARY.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    }


def test_parent_tree_matches_allowlist() -> None:
    index = _index()
    regular_files = {path for path, mode in index.items() if mode != "160000"}
    assert regular_files == _allowlist()


def test_analysis_and_pipeline_are_gitlinks() -> None:
    index = _index()
    assert {path for path, mode in index.items() if mode == "160000"} == GITLINKS


def test_parent_stays_below_overleaf_limits() -> None:
    index = _index()
    regular_paths = [ROOT / path for path, mode in index.items() if mode != "160000"]
    missing = [str(path.relative_to(ROOT)) for path in regular_paths if not path.is_file()]
    assert not missing, f"indexed files missing from working tree: {missing}"

    total_bytes = sum(path.stat().st_size for path in regular_paths)
    editable_bytes = sum(
        path.stat().st_size
        for path in regular_paths
        if path.suffix.lower() in EDITABLE_SUFFIXES or path.name == "Makefile"
    )
    assert editable_bytes < 7_000_000
    assert total_bytes < 100_000_000
