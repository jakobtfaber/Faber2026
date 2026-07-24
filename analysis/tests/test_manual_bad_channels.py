from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

SCRIPT = Path(__file__).parents[1] / "scripts" / "manual_bad_channels.py"
SPEC = importlib.util.spec_from_file_location("manual_bad_channels", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def approved_map() -> dict:
    return {
        "schema_version": 1,
        "status": "owner_approved",
        "event": "example",
        "instrument": "chime-frb",
        "source_product": {"sha256": "source"},
        "frequency_axis": {"sha256": "abc", "row_count": 6},
        "bad_row_ranges": [
            {
                "start": 1,
                "stop": 3,
                "frequency_min_mhz": 701.0,
                "frequency_max_mhz": 702.0,
                "reason": "horizontal interference outside burst window",
                "evidence": "review.svg#candidate-1",
            }
        ],
        "review": {"reviewer": "owner", "reviewed_at": "2026-07-21T00:00:00Z"},
    }


def test_approved_map_selects_only_exact_bound_rows():
    frequency = np.arange(700.0, 706.0)

    mask = MODULE.bad_row_mask(
        approved_map(), frequency, frequency_sha256="abc", source_sha256="source"
    )

    np.testing.assert_array_equal(mask, [False, True, True, False, False, False])


def test_draft_and_frequency_drift_fail_closed():
    frequency = np.arange(700.0, 706.0)
    payload = approved_map()
    payload["status"] = "draft"
    with pytest.raises(ValueError, match="not owner-approved"):
        MODULE.bad_row_mask(
            payload, frequency, frequency_sha256="abc", source_sha256="source"
        )

    payload["status"] = "owner_approved"
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        MODULE.bad_row_mask(
            payload, frequency, frequency_sha256="changed", source_sha256="source"
        )

    with pytest.raises(ValueError, match="source-product SHA-256 mismatch"):
        MODULE.bad_row_mask(
            payload, frequency, frequency_sha256="abc", source_sha256="changed"
        )


def test_ranges_must_be_sorted_nonoverlapping_and_frequency_bound():
    frequency = np.arange(700.0, 706.0)
    payload = approved_map()
    payload["bad_row_ranges"].append(
        {
            "start": 2,
            "stop": 4,
            "frequency_min_mhz": 702.0,
            "frequency_max_mhz": 703.0,
            "reason": "overlap",
            "evidence": "review.svg#candidate-2",
        }
    )
    with pytest.raises(ValueError, match="sorted and non-overlapping"):
        MODULE.bad_row_mask(
            payload, frequency, frequency_sha256="abc", source_sha256="source"
        )

    payload = approved_map()
    payload["bad_row_ranges"][0]["frequency_max_mhz"] = 999.0
    with pytest.raises(ValueError, match="maximum frequency"):
        MODULE.bad_row_mask(
            payload, frequency, frequency_sha256="abc", source_sha256="source"
        )


def test_apply_bad_rows_changes_only_selected_rows_without_mutation():
    values = np.arange(12, dtype=np.float32).reshape(6, 2)
    original = values.copy()
    mask = np.array([False, True, False, False, True, False])

    output = MODULE.apply_bad_rows(values, mask)

    np.testing.assert_array_equal(values, original)
    np.testing.assert_array_equal(output[~mask], original[~mask])
    assert np.isnan(output[mask]).all()


def test_effective_mask_is_exact_source_unavailable_manual_union():
    frequency = np.arange(700.0, 706.0)
    source_valid = np.array([True, False, True, True, False, True])
    payload = approved_map()
    payload["frequency_axis"]["source_valid_sha256"] = "source-valid"

    effective, components = MODULE.effective_bad_row_mask(
        payload,
        frequency,
        source_valid,
        frequency_sha256="abc",
        source_sha256="source",
        source_valid_sha256="source-valid",
    )

    np.testing.assert_array_equal(components["source_unavailable"], ~source_valid)
    np.testing.assert_array_equal(
        components["manual"], [False, True, True, False, False, False]
    )
    np.testing.assert_array_equal(
        effective, [False, True, True, False, True, False]
    )


def test_effective_mask_rejects_wrong_source_valid_hash_and_draft():
    frequency = np.arange(700.0, 706.0)
    source_valid = np.ones(6, dtype=bool)
    payload = approved_map()
    payload["frequency_axis"]["source_valid_sha256"] = "expected"

    with pytest.raises(ValueError, match="source-valid SHA-256 mismatch"):
        MODULE.effective_bad_row_mask(
            payload,
            frequency,
            source_valid,
            frequency_sha256="abc",
            source_sha256="source",
            source_valid_sha256="changed",
        )

    payload["status"] = "draft"
    with pytest.raises(ValueError, match="not owner-approved"):
        MODULE.effective_bad_row_mask(
            payload,
            frequency,
            source_valid,
            frequency_sha256="abc",
            source_sha256="source",
            source_valid_sha256="expected",
        )


def test_materialized_provenance_binds_exact_mask_and_components(tmp_path):
    frequency = np.arange(700.0, 706.0)
    source_valid = np.array([True, False, True, True, False, True])
    payload = approved_map()
    payload["frequency_axis"]["source_valid_sha256"] = "source-valid"
    mask_path = tmp_path / "effective.npy"
    provenance_path = tmp_path / "effective.json"

    record = MODULE.write_effective_mask_artifact(
        payload,
        frequency,
        source_valid,
        frequency_sha256="abc",
        source_sha256="source",
        source_valid_sha256="source-valid",
        map_sha256="map",
        output_mask=mask_path,
        output_provenance=provenance_path,
    )

    np.testing.assert_array_equal(
        np.load(mask_path), [False, True, True, False, True, False]
    )
    assert json.loads(provenance_path.read_text()) == record
    assert record["status"] == "owner_approved_effective_mask"
    assert record["components"]["source_unavailable"]["rows"] == 2
    assert record["components"]["owner_manual"]["rows"] == 2
    assert record["effective_mask"]["rows"] == 3
    assert record["union_rule"] == "source_unavailable OR owner_manual"
