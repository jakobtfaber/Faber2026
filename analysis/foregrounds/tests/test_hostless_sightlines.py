"""Frozen-evidence contract for hostless foreground sightlines."""

import json

import pandas as pd
import pytest

from foregrounds.census.hostless_sightlines import (
    COVERAGE_CSV,
    CROSS_REFERENCES_CSV,
    OUTPUT_DIR,
    PROVENANCE_CSV,
    SOURCE_PAYLOADS_JSON,
    build_hostless_census_receipt,
    write_hostless_census_artifacts,
)


def test_receipt_derives_the_hostless_roster_from_frozen_bursts():
    receipt = build_hostless_census_receipt()

    assert [row["nickname"] for row in receipt["sightlines"]] == [
        "freya",
        "mahi",
        "wilhelm",
    ]
    assert [row["tns"] for row in receipt["sightlines"]] == [
        "FRB 20230325C",
        "FRB 20240122A",
        "FRB 20221203A",
    ]


def test_receipt_exposes_traceable_candidate_fields_without_admitting_them():
    receipt = build_hostless_census_receipt()
    candidates = {
        (row["nickname"], row["object_id"]): row for row in receipt["candidates"]
    }

    assert set(candidates) == {
        ("freya", "197030881733398302"),
        ("freya", "197040882212782495"),
        ("wilhelm", "194453151328186646"),
    }
    assert candidates[("freya", "197030881733398302")]["model_fields_complete"]
    assert candidates[("freya", "197040882212782495")]["model_fields_complete"]
    assert not candidates[("wilhelm", "194453151328186646")][
        "model_fields_complete"
    ]
    assert not any(row["science_admitted"] for row in receipt["candidates"])
    assert candidates[("wilhelm", "194453151328186646")]["adopted_z"] is None


def test_receipt_fails_closed_on_missing_query_and_coverage_receipts():
    receipt = build_hostless_census_receipt()

    assert receipt["status"] == "blocked"
    assert len(receipt["coverage"]) == 15
    assert sum(row["query_required"] for row in receipt["coverage"]) == 9
    assert {
        (row["nickname"], row["survey"])
        for row in receipt["coverage"]
        if row["query_receipt_status"] == "missing"
    } == {
        (nickname, survey)
        for nickname in ("freya", "mahi", "wilhelm")
        for survey in ("CLUSTERS", "GLADE+", "NED")
    }
    assert {
        (row["nickname"], row["survey"])
        for row in receipt["coverage"]
        if not row["footprint_evidence_ready"]
    } == {
        (nickname, "GLADE+") for nickname in ("freya", "mahi", "wilhelm")
    }
    mahi = next(row for row in receipt["sightlines"] if row["nickname"] == "mahi")
    assert mahi["legacy_candidate_state"] == "empty_unverified"
    assert not mahi["foreground_free"]


def test_receipt_rejects_incomplete_or_hash_drifted_coverage(tmp_path):
    coverage = pd.read_csv(COVERAGE_CSV)
    incomplete = tmp_path / "incomplete.csv"
    coverage.loc[
        ~(
            coverage["nickname"].str.lower().eq("mahi")
            & coverage["survey"].eq("NED")
        )
    ].to_csv(incomplete, index=False)
    with pytest.raises(ValueError, match="coverage must contain"):
        build_hostless_census_receipt(coverage_csv=incomplete)

    drifted = tmp_path / "drifted.csv"
    coverage.loc[
        coverage["survey"] == "DESI_DR8_NORTH", "footprint_sha256"
    ] = "0" * 64
    coverage.to_csv(drifted, index=False)
    with pytest.raises(ValueError, match="footprint hash drift"):
        build_hostless_census_receipt(coverage_csv=drifted)

    unknown = tmp_path / "unknown.csv"
    coverage = pd.read_csv(COVERAGE_CSV)
    coverage.loc[
        coverage["nickname"].str.lower().eq("mahi")
        & coverage["survey"].eq("NED"),
        "footprint_status",
    ] = "unknown"
    coverage.to_csv(unknown, index=False)
    with pytest.raises(ValueError, match="invalid footprint status"):
        build_hostless_census_receipt(coverage_csv=unknown)

    unsupported_exclusion = tmp_path / "unsupported-exclusion.csv"
    coverage = pd.read_csv(COVERAGE_CSV)
    selector = coverage["nickname"].str.lower().eq("mahi") & coverage[
        "survey"
    ].eq("DESI_DR8_NORTH")
    coverage.loc[selector, "footprint_source"] = "unavailable"
    coverage.loc[selector, "footprint_sha256"] = ""
    coverage.to_csv(unsupported_exclusion, index=False)
    with pytest.raises(ValueError, match="unproven footprint exclusion"):
        build_hostless_census_receipt(coverage_csv=unsupported_exclusion)


def test_receipt_rejects_candidate_source_payload_hash_drift(tmp_path):
    payload = json.loads(SOURCE_PAYLOADS_JSON.read_text())
    target = next(
        row
        for row in payload["entries"]
        if row["key"] == "freya|halo|197030881733398302"
    )
    target["selected_row"]["z_phot"] = 0.9
    drifted = tmp_path / "payload.json"
    drifted.write_text(json.dumps(payload))

    with pytest.raises(ValueError, match="candidate source hash drift"):
        build_hostless_census_receipt(source_payloads_json=drifted)

    payload = json.loads(SOURCE_PAYLOADS_JSON.read_text())
    target = next(
        row
        for row in payload["entries"]
        if row["key"] == "freya|halo|197030881733398302"
    )
    target["query_response"] = {"rows": []}
    drifted_query = tmp_path / "query-payload.json"
    drifted_query.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="query-response hash drift"):
        build_hostless_census_receipt(source_payloads_json=drifted_query)


def test_receipt_rejects_adopted_redshift_drift_from_hashed_source(tmp_path):
    provenance = pd.read_csv(PROVENANCE_CSV, dtype={"obj": str})
    provenance.loc[
        provenance["nickname"].eq("freya")
        & provenance["obj"].eq("197030881733398302"),
        "adopted_z",
    ] = 0.999
    drifted = tmp_path / "provenance.csv"
    provenance.to_csv(drifted, index=False)

    with pytest.raises(ValueError, match="adopted redshift drift"):
        build_hostless_census_receipt(provenance_csv=drifted)

    cross_refs = pd.read_csv(CROSS_REFERENCES_CSV, dtype={"object_id": str})
    cross_refs.loc[
        cross_refs["nickname"].eq("freya")
        & cross_refs["object_id"].eq("197030881733398302"),
        "impact_kpc",
    ] = 999.0
    drifted_join = tmp_path / "cross-references.csv"
    cross_refs.to_csv(drifted_join, index=False)
    with pytest.raises(ValueError, match="joined-field drift"):
        build_hostless_census_receipt(cross_references_csv=drifted_join)


def test_writer_is_deterministic_and_binds_source_hashes(tmp_path):
    first = write_hostless_census_artifacts(tmp_path / "first")
    second = write_hostless_census_artifacts(tmp_path / "second")

    assert first == second
    for name in ("receipt.json", "candidates.csv", "coverage.csv"):
        assert (tmp_path / "first" / name).read_bytes() == (
            tmp_path / "second" / name
        ).read_bytes()
        assert (OUTPUT_DIR / name).read_bytes() == (
            tmp_path / "first" / name
        ).read_bytes()

    receipt = json.loads((tmp_path / "first" / "receipt.json").read_text())
    assert (
        receipt["source_files"]["frozen_census/bursts.csv"]
        == "6610aabb1527137c647149b86f6f65a3a1c4782680d618dd5c5f712b9f3c4536"
    )
