"""Guards for the frozen all-12 discovery-survey footprint receipt."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "build_survey_coverage_receipt.py"
RECEIPT = (
    ROOT
    / "foregrounds"
    / "studies"
    / "census"
    / "data"
    / "survey_coverage"
    / "all_12_sightlines.json"
)


def _module():
    spec = importlib.util.spec_from_file_location("coverage_receipt", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_receipt_covers_every_sightline_and_discovery_survey():
    payload = json.loads(RECEIPT.read_text())
    rows = payload["rows"]
    assert len(rows) == 12 * 5
    assert len({row["nickname"] for row in rows}) == 12
    assert {row["survey"] for row in rows} == {
        "NED",
        "GLADE+",
        "DESI_DR8_NORTH",
        "SDSS_DR12",
        "CLUSTERS",
    }
    assert all(
        row["footprint_status"] in {"covered", "not_covered", "unknown"}
        for row in rows
    )


def test_receipt_is_exactly_reproducible_from_pinned_mocs_and_contract():
    module = _module()
    _, expected_json = module.render()
    assert RECEIPT.read_text() == expected_json


def test_hostless_sightlines_remain_diagnostic():
    payload = json.loads(RECEIPT.read_text())
    statuses = {
        row["nickname"]: row["host_redshift_status"] for row in payload["rows"]
    }
    assert statuses["Wilhelm"] == "dm_z_diagnostic"
    assert statuses["Freya"] == "dm_z_diagnostic"
    assert statuses["Mahi"] == "dm_z_diagnostic"
