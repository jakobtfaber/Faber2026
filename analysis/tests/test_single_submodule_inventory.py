from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "single_submodule_inventory", ROOT / "scripts/single_submodule_inventory.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def run(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "flits"
    repo.mkdir()
    run(repo, "init")
    run(repo, "config", "user.name", "Test")
    run(repo, "config", "user.email", "test@example.invalid")
    paths = {
        "analysis/demo/result.json": "{}\n",
        "configs/bursts.yaml": "bursts: {}\n",
        "crossmatching/association.py": "def associate(): ...\n",
        "crossmatching/association_report.json": "{}\n",
        "data-manifest.csv": "path,sha256\n",
        "flits/core.py": "VALUE = 1\n",
        "scattering/configs/bursts/chime/casey.yaml": "burst: casey\n",
    }
    for relative, content in paths.items():
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
    run(repo, "add", ".")
    run(repo, "commit", "-m", "fixture")
    return repo


def test_inventory_is_complete_and_routes_project_paths(tmp_path: Path) -> None:
    repo = fixture_repo(tmp_path)
    analysis = tmp_path / "analysis"
    analysis.mkdir()
    commit, rows = MODULE.build_rows(repo, analysis, "HEAD")
    MODULE.verify_rows(repo, commit, rows)

    by_path = {row["old_path"]: row for row in rows}
    assert set(by_path) == {
        "analysis/demo/result.json",
        "configs/bursts.yaml",
        "crossmatching/association.py",
        "crossmatching/association_report.json",
        "data-manifest.csv",
        "flits/core.py",
        "scattering/configs/bursts/chime/casey.yaml",
    }
    assert by_path["analysis/demo/result.json"]["new_path"] == "campaigns/demo/result.json"
    assert by_path["configs/bursts.yaml"]["new_path"] == "config/bursts.yaml"
    assert by_path["data-manifest.csv"]["new_path"] == "data/catalog/data-manifest.csv"
    assert by_path["flits/core.py"]["disposition"] == "keep-reusable"
    assert by_path["crossmatching/association.py"]["disposition"] == "keep-reusable"
    assert (
        by_path["crossmatching/association_report.json"]["new_path"]
        == "campaigns/crossmatching/association_report.json"
    )
    assert (
        by_path["scattering/configs/bursts/chime/casey.yaml"]["new_path"]
        == "config/fits/scattering/bursts/chime/casey.yaml"
    )
    assert all(row["source_commit"] == commit for row in rows)
    assert all(len(row["sha256"]) == 64 for row in rows)


def test_destination_collision_is_recorded(tmp_path: Path) -> None:
    repo = fixture_repo(tmp_path)
    analysis = tmp_path / "analysis"
    collision = analysis / "campaigns/demo/result.json"
    collision.parent.mkdir(parents=True)
    collision.write_text("existing\n")

    _commit, rows = MODULE.build_rows(repo, analysis, "HEAD")
    by_path = {row["old_path"]: row for row in rows}
    assert by_path["analysis/demo/result.json"]["destination_collision"] == "yes"
