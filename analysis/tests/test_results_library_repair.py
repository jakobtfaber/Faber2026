from __future__ import annotations

import json
import hashlib
import sys
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_results_library_inventory import (  # noqa: E402
    build_receipt,
    link_dest,
    load_catalog,
    select_entries,
    snapshot_path,
    tree_manifest,
)
from materialize_results_library import materialize_one  # noqa: E402


def _catalog(tmp_path: Path) -> Path:
    path = tmp_path / "catalog.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "schema": "faber2026-results-library-catalog/v1",
                "trust_legend": {"live": "current"},
                "entries": [
                    {
                        "id": "dispersion.test",
                        "domain": "dispersion",
                        "slot": "dispersion/dm-test",
                        "trust": "live",
                        "repo": "parent",
                        "mode": "materialize",
                        "sources": ["analysis/test/results/diagnostics"],
                        "destinations": {
                            "analysis/test/results/diagnostics": "diagnostics"
                        },
                        "result_ids": [],
                        "notes": "test",
                    },
                    {
                        "id": "manuscript.test",
                        "domain": "manuscript",
                        "slot": "manuscript/test",
                        "trust": "live",
                        "repo": "parent",
                        "mode": "link_only",
                        "sources": ["figures"],
                        "result_ids": ["sample.gallery_fig1"],
                        "notes": "test",
                    },
                ],
            },
            sort_keys=False,
        )
    )
    return path


def test_explicit_nested_destination_and_result_ids(tmp_path: Path) -> None:
    catalog = load_catalog(_catalog(tmp_path))
    entry = catalog.entries[0]
    assert entry.result_ids == ( )
    assert link_dest(
        entry,
        "analysis/test/results/diagnostics",
        external_name=None,
    ) == Path("dispersion/dm-test/diagnostics")


def test_selection_is_known_unique_and_preserves_request_order(tmp_path: Path) -> None:
    catalog = load_catalog(_catalog(tmp_path))
    selected = select_entries(catalog, ["manuscript.test", "dispersion.test"])
    assert [entry.id for entry in selected.entries] == [
        "manuscript.test",
        "dispersion.test",
    ]
    with pytest.raises(SystemExit, match="unknown catalog entry"):
        select_entries(catalog, ["missing.test"])
    with pytest.raises(SystemExit, match="duplicate --only"):
        select_entries(catalog, ["dispersion.test", "dispersion.test"])


def test_broken_symlink_snapshot_uses_lstat(tmp_path: Path) -> None:
    broken = tmp_path / "broken"
    broken.symlink_to(tmp_path / "absent")
    assert not broken.exists()
    state = snapshot_path(broken, manifest=False)
    assert state["type"] == "symlink"
    assert state["raw_link_target"] == str(tmp_path / "absent")
    assert state["resolved_target"] == str(tmp_path / "absent")
    assert state["resolves"] is False


def test_tree_manifest_sorts_by_relative_path_string(tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "a.txt").write_text("top")
    (tmp_path / "a/z.txt").write_text("nested")
    rows = []
    for rel in ("a.txt", "a/z.txt"):
        path = tmp_path / rel
        rows.append(
            f"{rel}\0{path.stat().st_size}\0{hashlib.sha256(path.read_bytes()).hexdigest()}\n"
        )
    expected = hashlib.sha256("".join(rows).encode()).hexdigest()
    assert tree_manifest(tmp_path)["sha256"] == expected


def test_materializer_keeps_both_real_fail_closed(tmp_path: Path) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()
    (source / "source.txt").write_text("source")
    (destination / "destination.txt").write_text("destination")
    assert materialize_one(source, destination, dry_run=True) == (
        "would-conflict-both-real"
    )
    assert materialize_one(source, destination, dry_run=False) == (
        "conflict-both-real"
    )
    assert (source / "source.txt").read_text() == "source"
    assert (destination / "destination.txt").read_text() == "destination"


def test_receipt_records_git_selection_and_link_state(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    pipeline = root / "pipeline"
    library = tmp_path / "library"
    source = root / "figures"
    destination = library / "manuscript/test"
    pipeline.mkdir(parents=True)
    source.mkdir(parents=True)
    (source / "figure.txt").write_text("bytes")
    destination.parent.mkdir(parents=True)
    destination.symlink_to(source)

    inventory = {
        "generated_at": "2026-07-21T00:00:00Z",
        "library_root": str(library),
        "faber2026_root": str(root),
        "pipeline_root": str(pipeline),
        "entries": [
            {
                "id": "manuscript.test",
                "sources": [
                    {
                        "abs": str(source),
                        "dest": str(destination),
                        "link_status": "linked",
                    }
                ],
            }
        ],
    }
    receipt = build_receipt(
        inventory,
        selected_ids=["manuscript.test"],
        parent_commit="parent-sha",
        pipeline_commit="pipeline-sha",
    )
    assert receipt["selected_ids"] == ["manuscript.test"]
    assert receipt["git"] == {
        "parent_commit": "parent-sha",
        "pipeline_commit": "pipeline-sha",
    }
    state = receipt["entries"][0]["sources"][0]
    assert state["destination"]["type"] == "symlink"
    assert state["destination"]["raw_link_target"] == str(source)
    assert state["destination"]["resolves"] is True
    assert state["source"]["manifest"]["files"] == 1
    assert state["source"]["manifest"]["bytes"] == 5
    json.dumps(receipt)
