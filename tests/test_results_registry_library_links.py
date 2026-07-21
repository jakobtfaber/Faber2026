from __future__ import annotations

import tomllib
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs/rse/control/results-registry.toml"
CATALOG = ROOT / "scripts/results_library_catalog.yaml"


def _load():
    registry = tomllib.loads(REGISTRY.read_text())
    catalog = yaml.safe_load(CATALOG.read_text())
    return registry, catalog


def test_result_and_library_crosslinks_are_explicit_and_valid():
    registry, catalog = _load()
    results = {row["id"]: row for row in registry["result"]}
    entries = {row["id"]: row for row in catalog["entries"]}

    for result_id, row in results.items():
        assert isinstance(row.get("library_slots"), list), result_id
        for slot_id in row["library_slots"]:
            assert slot_id in entries, (result_id, slot_id)
            assert result_id in entries[slot_id]["result_ids"]

    for slot_id, row in entries.items():
        assert isinstance(row.get("result_ids"), list), slot_id
        for result_id in row["result_ids"]:
            assert result_id in results, (slot_id, result_id)
            assert slot_id in results[result_id]["library_slots"]


def test_incomplete_input_lineages_are_explicit_exceptions():
    registry, _ = _load()
    exceptions = registry["input_exception"]
    assert sum(row["class"] == "remediation_packet" for row in exceptions) == 12
    assert sum(row["class"] == "freya_package_manifest" for row in exceptions) == 3
    assert all(row["status"] == "incomplete_lineage" for row in exceptions)
    assert all("producing Git identity" in row["reason"] for row in exceptions)
    assert not any(row["id"].startswith("input.") for row in registry["result"])
