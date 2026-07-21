from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


VALIDATION_MD = Path(
    "docs/rse/specs/validation-expanded-foreground-photometry-and-morphology-catalog.md"
)
VALIDATION_JSON = Path("docs/rse/specs/validation-expanded-foreground-catalog.json")

REQUIRED_DEFECTS = {
    "matching-physics-quality-figure-input",
    "host-redshift-source-evidence",
    "figure-3-owner-approval",
}


def test_expanded_catalog_validation_is_fail_closed():
    text = VALIDATION_MD.read_text(encoding="utf-8")
    assert "FAILED — host-redshift provenance incomplete" in text
    assert "Calculation and artifact validation: **passed**" in text
    assert "Scientific release validation: **failed closed**" in text
    assert "Ready / Verified" not in text
    assert "52 / 52" not in text


def test_expanded_catalog_validation_records_required_defects():
    gate = json.loads(VALIDATION_JSON.read_text(encoding="utf-8"))
    assert gate["status"] == "failed"
    assert gate["disposition"] == "blocked_host_redshift_provenance"
    assert gate["calculation_validation"]["status"] == "passed"
    assert gate["calculation_validation"]["mismatches"] == 0
    assert len(gate["parent_input_commit"]) == 40
    assert len(gate["pipeline_commit"]) == 40

    defects = gate["defects"]
    assert {defect["id"] for defect in defects} == REQUIRED_DEFECTS
    statuses = {defect["id"]: defect["status"] for defect in defects}
    assert statuses["matching-physics-quality-figure-input"] == "passed"
    assert statuses["host-redshift-source-evidence"] == "failed"
    assert statuses["figure-3-owner-approval"] == "failed"


def test_expanded_catalog_validator_exits_nonzero_until_rebuilt():
    result = subprocess.run(
        [
            sys.executable,
            "scripts/validate_expanded_foreground_catalog_gate.py",
            "--gate",
            str(VALIDATION_JSON),
        ],
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 1
    assert "expanded foreground catalog gate failed" in result.stderr
