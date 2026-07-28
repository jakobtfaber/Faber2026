#!/usr/bin/env python3
"""Build the exact FLITS path map required by the one-submodule migration."""

from __future__ import annotations

import argparse
import csv
import hashlib
import subprocess
from dataclasses import dataclass
from pathlib import Path


FIELDNAMES = [
    "source_commit",
    "source_blob",
    "old_path",
    "file_mode",
    "file_type",
    "new_repository",
    "new_path",
    "class",
    "sha256",
    "consumers",
    "destination_collision",
    "history_reachable",
    "split_manifest",
    "disposition",
]


@dataclass(frozen=True)
class TreeEntry:
    mode: str
    kind: str
    oid: str
    path: str


def git(repo: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        input=input_bytes,
        check=True,
        capture_output=True,
    ).stdout


def resolve_commit(repo: Path, revision: str) -> str:
    return git(repo, "rev-parse", "--verify", f"{revision}^{{commit}}").decode().strip()


def tracked_entries(repo: Path, commit: str) -> list[TreeEntry]:
    raw = git(repo, "ls-tree", "-r", "-z", "--full-tree", commit)
    entries: list[TreeEntry] = []
    for item in raw.split(b"\0"):
        if not item:
            continue
        metadata, raw_path = item.split(b"\t", 1)
        mode, kind, oid = metadata.decode().split()
        entries.append(
            TreeEntry(
                mode=mode,
                kind=kind,
                oid=oid,
                path=raw_path.decode("utf-8", errors="surrogateescape"),
            )
        )
    return sorted(entries, key=lambda entry: entry.path)


def blob_hashes(repo: Path, entries: list[TreeEntry]) -> dict[str, str]:
    blob_oids = sorted({entry.oid for entry in entries if entry.kind == "blob"})
    request = b"".join(f"{oid}\n".encode() for oid in blob_oids)
    output = git(repo, "cat-file", "--batch", input_bytes=request)
    hashes: dict[str, str] = {}
    cursor = 0
    for expected_oid in blob_oids:
        line_end = output.index(b"\n", cursor)
        header = output[cursor:line_end].decode().split()
        oid, kind, size_text = header
        if oid != expected_oid or kind != "blob":
            raise ValueError(f"unexpected cat-file record for {expected_oid}: {header}")
        size = int(size_text)
        start = line_end + 1
        end = start + size
        hashes[oid] = hashlib.sha256(output[start:end]).hexdigest()
        cursor = end + 1
    if cursor != len(output):
        raise ValueError("unparsed cat-file output")
    return hashes


def destination(path: str) -> tuple[str, str, str, str]:
    """Return repository, destination path, class, and disposition."""
    if path.startswith("analysis/"):
        relative = path.removeprefix("analysis/")
        return "Faber2026-analysis", f"campaigns/{relative}", "project-campaign", "move"
    if path == "configs/bursts.yaml":
        return "Faber2026-analysis", "config/bursts.yaml", "project-config", "move"
    if path == "data-manifest.csv":
        return (
            "Faber2026-analysis",
            "data/catalog/data-manifest.csv",
            "project-catalog",
            "move",
        )
    if path == "codetections_manifest.yaml":
        return (
            "Faber2026-analysis",
            "data/catalog/codetections_manifest.yaml",
            "project-catalog",
            "move",
        )
    project_prefixes = {
        "crossmatching/": "campaigns/crossmatching/",
        "galaxies/foreground/data/": "campaigns/foregrounds/data/",
        "notebooks/codetections/": "campaigns/codetections/notebooks/",
        "scattering/configs/bursts/": "config/fits/scattering/bursts/",
        "scintillation/configs/bursts/": "config/fits/scintillation/bursts/",
        "scintillation/scint_analysis/reference_arc/": (
            "campaigns/scintillation/reference_arc/"
        ),
        "scripts/h17_codetections/": "campaigns/codetections/h17/",
    }
    for prefix, destination_prefix in project_prefixes.items():
        if path.startswith(prefix):
            relative = path.removeprefix(prefix)
            if prefix == "crossmatching/" and path.endswith(".py"):
                return "dsa110-FLITS", path, "reusable-code", "keep-reusable"
            return (
                "Faber2026-analysis",
                destination_prefix + relative,
                "project-input-or-output",
                "move",
            )
    project_files = {
        "DATA_LOCATIONS.md": "data/catalog/DATA_LOCATIONS.md",
        "DATA_SOURCES.md": "data/catalog/DATA_SOURCES.md",
        "machine_inventory.yaml": "data/catalog/machine_inventory.yaml",
        "docs/codetection-science-plan.md": "campaigns/codetections/codetection-science-plan.md",
        "docs/freya_evidence.html": "campaigns/scintillation/freya_evidence.html",
        "scintillation/freya_analysis_results.json": (
            "campaigns/scintillation/freya_analysis_results.json"
        ),
    }
    if path in project_files:
        return "Faber2026-analysis", project_files[path], "project-record", "move"
    for prefix in ("exports/", "results/"):
        if path.startswith(prefix):
            return (
                "Faber2026-analysis",
                f"campaigns/{path}",
                "project-output",
                "move",
            )
    return "dsa110-FLITS", path, "reusable", "keep-reusable"


def build_rows(
    flits: Path, analysis: Path, revision: str
) -> tuple[str, list[dict[str, str]]]:
    commit = resolve_commit(flits, revision)
    entries = tracked_entries(flits, commit)
    hashes = blob_hashes(flits, entries)
    rows: list[dict[str, str]] = []
    for entry in entries:
        repository, new_path, path_class, disposition = destination(entry.path)
        collision = (
            "yes"
            if repository == "Faber2026-analysis" and (analysis / new_path).exists()
            else "no"
        )
        rows.append(
            {
                "source_commit": commit,
                "source_blob": entry.oid,
                "old_path": entry.path,
                "file_mode": entry.mode,
                "file_type": entry.kind,
                "new_repository": repository,
                "new_path": new_path,
                "class": path_class,
                "sha256": hashes.get(entry.oid, ""),
                "consumers": "",
                "destination_collision": collision,
                "history_reachable": "yes",
                "split_manifest": "",
                "disposition": disposition,
            }
        )
    return commit, rows


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def verify_rows(flits: Path, revision: str, rows: list[dict[str, str]]) -> None:
    commit = resolve_commit(flits, revision)
    expected = {
        (entry.path, entry.mode, entry.kind, entry.oid)
        for entry in tracked_entries(flits, commit)
    }
    observed = {
        (row["old_path"], row["file_mode"], row["file_type"], row["source_blob"])
        for row in rows
    }
    if expected != observed:
        missing = sorted(expected - observed)
        extra = sorted(observed - expected)
        raise ValueError(f"path-map complement mismatch: missing={missing}, extra={extra}")
    if any(row["source_commit"] != commit for row in rows):
        raise ValueError("path map contains more than one source commit")
    if any(not row["sha256"] and row["file_type"] == "blob" for row in rows):
        raise ValueError("blob row lacks SHA-256")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--flits", type=Path, required=True)
    parser.add_argument("--analysis", type=Path, default=Path.cwd())
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    _commit, rows = build_rows(args.flits, args.analysis, args.revision)
    verify_rows(args.flits, args.revision, rows)
    write_rows(args.output, rows)
    print(f"wrote {len(rows)} rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
