#!/usr/bin/env python3
"""Copy path-map ``move`` rows from a frozen Git commit into analysis."""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import subprocess
from pathlib import Path


def git(repo: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
    ).stdout


def apply_map(flits: Path, analysis: Path, path_map: Path) -> tuple[int, int]:
    rows = list(csv.DictReader(path_map.open(encoding="utf-8")))
    copied = 0
    unchanged = 0
    seen: set[str] = set()
    for row in rows:
        if row["disposition"] != "move":
            continue
        destination_text = row["new_path"]
        if destination_text in seen:
            raise ValueError(f"duplicate destination: {destination_text}")
        seen.add(destination_text)
        if row["file_type"] != "blob" or row["file_mode"] not in {"100644", "100755"}:
            raise ValueError(
                f"unsupported moved entry: {row['old_path']} "
                f"{row['file_mode']} {row['file_type']}"
            )
        blob = git(flits, "cat-file", "blob", row["source_blob"])
        digest = hashlib.sha256(blob).hexdigest()
        if digest != row["sha256"]:
            raise ValueError(f"source hash mismatch: {row['old_path']}")
        destination = analysis / destination_text
        if destination.exists() and destination.read_bytes() == blob:
            unchanged += 1
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(blob)
            copied += 1
        os.chmod(destination, 0o755 if row["file_mode"] == "100755" else 0o644)
        if hashlib.sha256(destination.read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError(f"destination hash mismatch: {destination_text}")
    return copied, unchanged


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--flits", type=Path, required=True)
    parser.add_argument("--analysis", type=Path, default=Path.cwd())
    parser.add_argument("--path-map", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    copied, unchanged = apply_map(args.flits, args.analysis, args.path_map)
    print(f"copied={copied} unchanged={unchanged}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
