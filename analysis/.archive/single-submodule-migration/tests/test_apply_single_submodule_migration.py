from __future__ import annotations

import csv
import hashlib
import importlib.util
import subprocess
from pathlib import Path

import pytest


def load_module():
    path = Path(__file__).parents[1] / "scripts" / "apply_single_submodule_migration.py"
    spec = importlib.util.spec_from_file_location("apply_single_submodule_migration", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


migration = load_module()


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def fixture(tmp_path: Path) -> tuple[Path, Path, Path, str]:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()
    git(source, "init")
    git(source, "config", "user.email", "test@example.com")
    git(source, "config", "user.name", "Test")
    payload = b"frozen payload\n"
    (source / "result.json").write_bytes(payload)
    git(source, "add", "result.json")
    git(source, "commit", "-m", "fixture")
    blob = git(source, "rev-parse", "HEAD:result.json")
    path_map = tmp_path / "path-map.csv"
    row = {
        "source_blob": blob,
        "old_path": "result.json",
        "file_mode": "100644",
        "file_type": "blob",
        "new_path": "campaigns/result.json",
        "sha256": hashlib.sha256(payload).hexdigest(),
        "disposition": "move",
    }
    with path_map.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=row)
        writer.writeheader()
        writer.writerow(row)
    return source, destination, path_map, blob


def test_apply_map_copies_and_rechecks_frozen_blob(tmp_path):
    source, destination, path_map, _blob = fixture(tmp_path)
    assert migration.apply_map(source, destination, path_map) == (1, 0)
    assert (destination / "campaigns/result.json").read_bytes() == b"frozen payload\n"
    assert migration.apply_map(source, destination, path_map) == (0, 1)


def test_apply_map_rejects_forged_hash(tmp_path):
    source, destination, path_map, _blob = fixture(tmp_path)
    text = path_map.read_text().replace(
        hashlib.sha256(b"frozen payload\n").hexdigest(), "0" * 64
    )
    path_map.write_text(text)
    with pytest.raises(ValueError, match="source hash mismatch"):
        migration.apply_map(source, destination, path_map)
