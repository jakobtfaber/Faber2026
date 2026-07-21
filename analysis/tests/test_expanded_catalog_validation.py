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
    "moster-input-units",
    "cluver-equation-and-rest-frame",
    "incomplete-crossmatches",
    "non-deterministic-match-selection",
    "stern-selection-interpretation",
    "morphology-summary",
    "missing-pinned-expanded-csv",
    "unversioned-figure-3-input",
}


def test_expanded_catalog_validation_is_fail_closed():
    text = VALIDATION_MD.read_text(encoding="utf-8")
    assert "FAILED - superseded; do not use" in text
    assert "FAILED — superseded; do not use" in text
    assert "Ready / Verified" not in text
    assert "52 / 52" not in text


def test_expanded_catalog_validation_records_required_defects():
    gate = json.loads(VALIDATION_JSON.read_text(encoding="utf-8"))
    assert gate["status"] == "failed"
    assert gate["disposition"] == "superseded_do_not_use"
    assert len(gate["parent_commit"]) == 40
    assert len(gate["pipeline_commit"]) == 40

    defects = gate["defects"]
    assert {defect["id"] for defect in defects} == REQUIRED_DEFECTS
    for defect in defects:
        assert defect["status"] == "failed"
        assert defect["affected_formula_or_artifact"]
        assert defect["rows_or_count"]
        assert defect["scientific_effect"]
        assert defect["required_repair"]


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
