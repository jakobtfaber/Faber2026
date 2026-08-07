from __future__ import annotations

import csv
import importlib.util
from pathlib import Path


def load_module():
    path = (
        Path(__file__).parents[1]
        / "scripts"
        / "rewrite_single_submodule_consumers.py"
    )
    spec = importlib.util.spec_from_file_location(
        "rewrite_single_submodule_consumers", path
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rewrite = load_module()


def test_rewrite_tree_only_rewrites_exact_moved_paths(tmp_path):
    path_map = tmp_path / "path-map.csv"
    rows = [
        {
            "old_path": "analysis/run/result.json",
            "new_path": "campaigns/run/result.json",
            "disposition": "move",
        },
        {
            "old_path": "flits/batch/cli.py",
            "new_path": "flits/batch/cli.py",
            "disposition": "keep-reusable",
        },
    ]
    with path_map.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    consumer = tmp_path / "consumer.py"
    consumer.write_text(
        'MOVED = "pipeline/analysis/run/result.json"\n'
        'KEPT = "pipeline/flits/batch/cli.py"\n'
    )
    assert rewrite.rewrite_tree(tmp_path, path_map) == (0, 0)
    assert consumer.read_text() == (
        'MOVED = "pipeline/analysis/run/result.json"\n'
        'KEPT = "pipeline/flits/batch/cli.py"\n'
    )


def test_rewrite_tree_preserves_historical_evidence(tmp_path):
    path_map = tmp_path / "path-map.csv"
    row = {
        "old_path": "analysis/run/result.json",
        "new_path": "campaigns/run/result.json",
        "disposition": "move",
    }
    with path_map.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=row)
        writer.writeheader()
        writer.writerow(row)
    evidence = tmp_path / "docs/rse/specs/evidence/receipt.json"
    evidence.parent.mkdir(parents=True)
    evidence.write_text('{"source": "pipeline/analysis/run/result.json"}\n')
    script = tmp_path / "scripts/live.py"
    script.parent.mkdir()
    script.write_text('SOURCE = "pipeline/analysis/run/result.json"\n')

    assert rewrite.rewrite_tree(tmp_path, path_map) == (1, 1)
    assert evidence.read_text() == (
        '{"source": "pipeline/analysis/run/result.json"}\n'
    )
    assert script.read_text() == 'SOURCE = "campaigns/run/result.json"\n'
