from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAST = ROOT / "docs/rse/specs/evidence/protected-nine-sightline-2026-07-22"
CADC = ROOT / "docs/rse/specs/evidence/cadc-cfis-access-2026-07-22"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_mast_manifest_freezes_complete_nine_sightline_native_corpus():
    manifest = json.loads((MAST / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "protected_source_responses_frozen"
    assert manifest["context"] == "HLSP_WISE_PS1_STRM"
    assert manifest["source_table"] == "catalogRecordRowStore"
    assert manifest["authenticated_account"] == "jfaber"
    assert manifest["credentials_recorded"] is False
    assert manifest["pagination"]["row_limit"] is None
    assert manifest["pagination"]["truncation_allowed"] is False
    assert [row["nickname"] for row in manifest["sightlines"]] == [
        "zach",
        "whitney",
        "oran",
        "isha",
        "phineas",
        "johndoeII",
        "hamilton",
        "chromatica",
        "casey",
    ]
    serialized_manifest = json.dumps(manifest).lower()
    assert "host_z" not in serialized_manifest
    assert "redshift" not in serialized_manifest
    assert "authority" not in serialized_manifest

    exact_total = 0
    for record in manifest["sightlines"]:
        response = MAST / record["response_file"]
        sql = MAST / record["sql_file"]
        assert digest(response) == record["response_sha256"]
        assert digest(sql) == record["sql_sha256"]
        assert record["query_job"]["Status"] == "5"
        assert record["output_job"]["Status"] == "5"
        assert "TOP " not in sql.read_text(encoding="utf-8").upper()
        with response.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
        assert len(reader.fieldnames or []) == 213
        assert len(rows) == record["response_audit"]["raw_row_count"]
        assert record["response_audit"]["native_column_count"] == 210
        assert record["response_audit"]["shared_wise_identity_state"] == "ambiguous"
        assert record["response_audit"]["shared_wise_identifier_groups"]
        exact_total += record["response_audit"]["exact_cone_row_count"]
    assert exact_total == 20_788


def test_cadc_manifest_freezes_authenticated_access_denied_not_unmatched():
    manifest = json.loads((CADC / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "access_denied"
    assert manifest["authenticated"] is True
    assert manifest["table"] == "cfht.cfiscat"
    assert manifest["release"] == "UNIONS CFIS DR3"
    assert manifest["scientific_changes_authorized"] is False
    assert digest(CADC / manifest["response_file"]) == manifest["response_sha256"]
    assert (
        digest(CADC / manifest["vospace_handshake_file"])
        == manifest["vospace_handshake_sha256"]
    )
    response = (CADC / manifest["response_file"]).read_text(encoding="utf-8")
    assert "not found in TapSchema" in response
    assert "unmatched" not in response.lower()
