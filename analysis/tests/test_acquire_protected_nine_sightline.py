from __future__ import annotations

import csv
import math
import xml.etree.ElementTree as ET
from pathlib import Path

from scripts.acquire_protected_nine_sightline import (
    CasJobsClient,
    GUARD_ARCSEC,
    RADIUS_ARCMIN,
    audit_response,
    bounding_box,
    load_sightlines,
    sql_for_sightline,
)


def test_load_sightlines_selects_exactly_nine_finite_positive_host_redshifts(
    tmp_path: Path,
):
    path = tmp_path / "bursts.csv"
    rows = [
        {
            "nickname": f"n{index}",
            "tns": f"FRB {index}",
            "ra_deg": str(100 + index),
            "dec_deg": "70",
            "z_spec": "0.2",
        }
        for index in range(9)
    ]
    rows.extend(
        [
            {"nickname": "blank", "tns": "x", "ra_deg": "1", "dec_deg": "2", "z_spec": ""},
            {"nickname": "zero", "tns": "x", "ra_deg": "1", "dec_deg": "2", "z_spec": "0"},
        ]
    )
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)

    selected = load_sightlines(path)

    assert [row["nickname"] for row in selected] == [f"n{i}" for i in range(9)]


def test_bounding_box_contains_guarded_cone_at_high_declination():
    box = bounding_box(310.199525, 72.8823272222)
    guarded_radius_deg = RADIUS_ARCMIN / 60 + GUARD_ARCSEC / 3600

    assert math.isclose(box["dec_max"] - 72.8823272222, guarded_radius_deg)
    assert box["ra_max"] - 310.199525 > guarded_radius_deg
    assert 310.199525 - box["ra_min"] == box["ra_max"] - 310.199525


def test_sql_is_unlimited_native_row_materialization_with_auditable_bounds():
    sightline = {
        "nickname": "zach",
        "tns": "FRB 20220207C",
        "ra_deg": 310.199525,
        "dec_deg": 72.8823272222,
        "host_z": 0.043,
    }

    sql = sql_for_sightline(sightline, "f26_ps1strm_zach_test")

    assert "TOP " not in sql.upper()
    assert "INTO MyDB.f26_ps1strm_zach_test" in sql
    assert "FROM catalogRecordRowStore AS r" in sql
    assert "r.*" in sql
    assert "r.raMean >=" in sql
    assert "r.raMean <=" in sql
    assert "r.decMean >=" in sql
    assert "r.decMean <=" in sql


def test_output_metadata_polling_handles_finished_before_url_is_visible(monkeypatch):
    client = object.__new__(CasJobsClient)
    responses = iter(
        [
            {"JobID": "7", "Status": "5", "OutputLoc": ""},
            {"JobID": "7", "Status": "5", "OutputLoc": "https://example/data.csv"},
        ]
    )
    monkeypatch.setattr(client, "job_info", lambda _job_id: next(responses))
    monkeypatch.setattr("scripts.acquire_protected_nine_sightline.time.sleep", lambda _: None)

    info = client.wait_for_output_info(7)

    assert info["OutputLoc"] == "https://example/data.csv"


def test_job_info_selects_record_not_array_wrapper(monkeypatch):
    client = object.__new__(CasJobsClient)
    client.wsid = "1"
    client.password = "not-used"
    xml = ET.fromstring(
        """
        <ArrayOfCJJob xmlns="http://Services.Cas.jhu.edu">
          <CJJob>
            <JobID>7</JobID>
            <OutputLoc>https://example/data.csv</OutputLoc>
          </CJJob>
        </ArrayOfCJJob>
        """
    )
    monkeypatch.setattr(client, "_jobs", lambda _operation, _fields: xml)

    info = client.job_info(7)

    assert info == {"JobID": "7", "OutputLoc": "https://example/data.csv"}


def test_response_audit_keeps_shared_wise_identifiers_ambiguous():
    response = (
        "sightline,center_ra_deg,center_dec_deg,objID,raMean,decMean,cntr\n"
        "zach,10,70,1,10,70,99\n"
        "zach,10,70,2,10.001,70,99\n"
        "zach,10,70,3,20,70,100\n"
    ).encode()
    sightline = {"ra_deg": 10.0, "dec_deg": 70.0}

    audit = audit_response(response, sightline)

    assert audit["raw_row_count"] == 3
    assert audit["exact_cone_row_count"] == 2
    assert audit["guard_only_row_count"] == 1
    assert audit["native_column_count"] == 4
    assert audit["shared_wise_identifier_groups"] == [
        {"cntr": "99", "objIDs": ["1", "2"]}
    ]
