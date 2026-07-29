import importlib.util
import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.historical_replay

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/replay_frozen_nine_sightline_corpora.py"
FROZEN_REGISTRY_REPLAY = (
    ROOT
    / "docs/rse/specs/evidence/nine-sightline-registry-replay-2026-07-23/replay.json"
)


def _module():
    spec = importlib.util.spec_from_file_location("corpus_replay", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_replay_matches_corpora_and_current_production_registry():
    module = _module()
    result = module.replay(ROOT)
    frozen = json.loads(FROZEN_REGISTRY_REPLAY.read_text())
    assert result["ok"] is True
    assert result["anonymous"]["cells"] == 135
    assert result["anonymous"]["coverage_cells_independently_replayed"] == 36
    assert result["anonymous"]["admitted_rows"] == 115_713
    assert result["anonymous"]["guard_only_rows"] == 1_516
    assert result["anonymous"]["states"] == {
        "matched": 37,
        "outside_footprint": 67,
        "unmatched": 31,
    }
    assert result["protected"]["raw_rows"] == 26_540
    assert result["protected"]["exact_cone_rows"] == 20_788
    assert result["protected"]["guard_only_rows"] == 5_752
    assert result["protected"]["shared_wise_identifier_groups"] == 242
    assert result["protected"]["ambiguous_shared_wise_groups"] == 242
    assert result["cadc_cfis"]["status"] == "access_denied"
    assert result["roster_case_aliases"] == {"johndoeii": "johndoeII"}
    assert result["registry_replay"]["verdict_mismatches"] == []
    assert result["registry_replay"]["budget_mismatches"] == []
    assert result["registry_replay"]["pipeline_commit"] == frozen["pipeline_commit"]
    assert frozen["pipeline_commit"] == module.EXPECTED_PIPELINE_COMMIT
    assert (
        result["registry_replay"]["input_sha256"]
        == frozen["input_sha256"]
        == module.EXPECTED_REGISTRY_INPUT_SHA256
    )
    assert result["registry_replay"]["rows"] == frozen["rows"] == 52
    assert result["registry_replay"]["finite_host_rows"] == frozen["finite_host_rows"] == 49
    assert result["registry_replay"]["provenance_rows"] == 52
    assert sum(
        item["matches"] for item in result["registry_replay"]["duplicate_checks"]
    ) == frozen["duplicate_checks_passed"] == 7
    assert frozen["verdict_mismatches"] == []
    assert frozen["budget_mismatches"] == []
    assert frozen["status"] == "validated"
    assert result["errors"] == []


def test_exact_cone_check_rejects_a_guard_row_as_admitted():
    module = _module()
    errors = []
    module.check_separation(
        {"separation_arcmin": 15.05, "admission_state": "admitted"},
        "synthetic/admitted",
        admitted=True,
        errors=errors,
    )
    assert errors == ["synthetic/admitted: admitted separation exceeds 15 arcmin"]


def test_anonymous_geometry_rejects_a_producer_written_wrong_separation():
    module = _module()
    errors = []
    module.check_anonymous_geometry(
        {
            "ra_deg": 10.0,
            "dec_deg": 20.0,
            "separation_arcmin": 0.0,
            "admission_state": "admitted",
        },
        "synthetic/geometry",
        center=(11.0, 20.0),
        admitted=True,
        errors=errors,
    )
    assert errors == ["synthetic/geometry: stored separation disagrees with coordinates"]


def test_protected_rectangle_rejects_sql_bounds_that_do_not_match_manifest():
    module = _module()
    errors = []
    module.check_protected_rectangle(
        sql=("WHERE r.raMean >= 1 AND r.raMean <= 2 "
             "AND r.decMean >= 3 AND r.decMean <= 4;"),
        bounds={"ra_min": 1.0, "ra_max": 2.1, "dec_min": 3.0, "dec_max": 4.0},
        center=(1.5, 3.5),
        label="synthetic",
        errors=errors,
    )
    assert errors == ["synthetic: SQL bounds disagree with manifest bounding box"]


def test_protected_geometry_uses_manifest_center_not_csv_center():
    module = _module()
    errors = []
    separation = module.protected_row_separation(
        {
            "center_ra_deg": "100",
            "center_dec_deg": "20",
            "raMean": "11",
            "decMean": "20",
        },
        center=(10.0, 20.0),
        label="synthetic",
        errors=errors,
    )
    assert separation > 50
    assert errors == ["synthetic: CSV center disagrees with manifest center"]


def test_tap_coverage_rejects_overflow_and_error_statuses():
    module = _module()
    for status in ("OVERFLOW", "ERROR"):
        payload = (
            '<?xml version="1.0"?><VOTABLE><RESOURCE>'
            f'<INFO name="QUERY_STATUS" value="{status}"/>'
            '<TABLE><FIELD name="id"/><DATA><TABLEDATA/></DATA></TABLE>'
            '</RESOURCE></VOTABLE>'
        ).encode()
        import gzip

        import pytest

        with pytest.raises(ValueError, match="not complete OK"):
            module.replay_coverage_evidence(
                "tap_polygon", gzip.compress(payload), (0.0, 0.0)
            )


def test_shared_wise_replay_rejects_manifest_group_not_present_in_raw_rows():
    module = _module()
    groups = module.shared_wise_groups(
        [
            {"cntr": "1", "objID": "a", "separation_arcmin": 1.0},
            {"cntr": "1", "objID": "b", "separation_arcmin": 2.0},
            {"cntr": "2", "objID": "c", "separation_arcmin": 3.0},
        ]
    )
    assert groups == {"1": ("a", "b")}


def test_command_writes_valid_json(tmp_path):
    output = tmp_path / "replay.json"
    import subprocess

    completed = subprocess.run(
        ["python3", str(SCRIPT), "--output", str(output)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(output.read_text())["ok"] is True
