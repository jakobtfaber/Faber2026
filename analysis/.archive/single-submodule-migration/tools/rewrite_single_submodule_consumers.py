#!/usr/bin/env python3
"""Rewrite exact ``pipeline/<moved path>`` references to analysis destinations."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

TEXT_SUFFIXES = {
    ".csv",
    ".html",
    ".json",
    ".md",
    ".py",
    ".tex",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
ACTIVE_ROOTS = {"config", "scripts", "tests"}
ACTIVE_FILES = {
    Path("Makefile"),
    Path("RESULTS.md"),
    Path("REPRODUCE.md"),
    Path("README.md"),
    Path("repro_manifest.csv"),
    Path("figure_review/slots.json"),
    Path("figures/catalog.yaml"),
}


def replacements(path_map: Path) -> dict[str, str]:
    rows = list(csv.DictReader(path_map.open(encoding="utf-8")))
    return {
        f"pipeline/{row['old_path']}": row["new_path"]
        for row in rows
        if row["disposition"] == "move"
    }


def rewrite_tree(root: Path, path_map: Path) -> tuple[int, int]:
    root = root.resolve()
    path_map = path_map.resolve()
    mapping = replacements(path_map)
    changed_files = 0
    changed_references = 0
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        relative = path.relative_to(root)
        if relative == path_map.relative_to(root):
            continue
        if relative not in ACTIVE_FILES and relative.parts[0] not in ACTIVE_ROOTS:
            continue
        try:
            original = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rewritten = original
        replacements_in_file = 0
        for old, new in mapping.items():
            count = rewritten.count(old)
            if count:
                rewritten = rewritten.replace(old, new)
                replacements_in_file += count
        if rewritten != original:
            path.write_text(rewritten, encoding="utf-8")
            changed_files += 1
            changed_references += replacements_in_file
    return changed_files, changed_references


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--path-map", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    files, references = rewrite_tree(args.root, args.path_map)
    print(f"changed_files={files} changed_references={references}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
