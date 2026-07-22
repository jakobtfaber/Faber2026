import hashlib
import gzip
import importlib.util
import json
import math
from pathlib import Path

import pytest
from astropy.coordinates import SkyCoord
import astropy.units as u


SCRIPT = Path(__file__).parents[1] / "scripts" / "freeze_anonymous_nine_sightline_corpus.py"
SPEC = importlib.util.spec_from_file_location("freeze_corpus", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


EXPECTED_SERVICES = {
    "desi_dr1",
    "sdss_dr19",
    "lamost_dr11",
    "legacy_dr10_photoz",
    "ps1_strm_v1",
    "jplus_dr3",
    "minijpas_pdr201912",
    "gaia_dr3",
    "lotss_dr3",
    "vlass_ql_epoch1",
    "erass1_main_v1_2",
    "erass1_clusters_primary_v3_2",
    "xmm_newton_exposure",
    "chandra_exposure",
    "swift_exposure",
}


def _write(path: Path, data: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def _complete_manifest(tmp_path: Path) -> dict:
    cells = []
    for sightline in MODULE.SIGHTLINE_NAMES:
        for service in MODULE.SERVICES:
            raw_path = Path("raw") / sightline / f"{service.key}.csv"
            canonical_path = Path("canonical") / sightline / f"{service.key}.json"
            raw_sha = _write(tmp_path / raw_path, b"source_id,ra,dec\n")
            canonical = json.dumps([], separators=(",", ":")).encode()
            canonical_sha = _write(tmp_path / canonical_path, canonical)
            cell = {
                "sightline": sightline,
                "service": service.key,
                "release": service.release,
                "role": service.role,
                "endpoint": service.endpoint,
                "exact_query": "SELECT * FROM release WHERE cone <= 15.1 arcmin",
                "retrieved_at_utc": "2026-07-22T12:00:00Z",
                "coverage": "inside",
                "status": "unmatched",
                "raw_path": str(raw_path),
                "raw_sha256": raw_sha,
                "canonical_path": str(canonical_path),
                "canonical_sha256": canonical_sha,
                "native_columns": ["source_id", "ra", "dec"],
                "row_count": 0,
                "guard_ring_count": 0,
                "pagination": {
                    "method": "tap_sync",
                    "complete": True,
                    "overflow": False,
                    "pages": 1,
                    "row_limit": 100000,
                    "server_total": 0,
                },
            }
            if service.key in MODULE.COVERAGE_CONFIG:
                coverage_path = Path("coverage") / sightline / f"{service.key}.json"
                coverage_sha = _write(tmp_path / coverage_path, b"{}")
                cell.update(
                    coverage_checked=True,
                    coverage_evidence_path=str(coverage_path),
                    coverage_evidence_sha256=coverage_sha,
                )
            cells.append(cell)
    return {
        "schema_version": MODULE.SCHEMA_VERSION,
        "input_sha256": MODULE.FROZEN_INPUT_SHA256,
        "cells": cells,
    }


def test_required_matrix_is_exact_and_has_release_authority():
    assert len(MODULE.SIGHTLINE_NAMES) == 9
    assert {service.key for service in MODULE.SERVICES} == EXPECTED_SERVICES
    assert all(service.release and service.endpoint for service in MODULE.SERVICES)
    assert len(MODULE.required_cell_keys()) == 9 * len(EXPECTED_SERVICES)


def test_complete_manifest_passes(tmp_path):
    manifest = _complete_manifest(tmp_path)
    assert MODULE.validate_manifest(manifest, tmp_path) == []


def test_canonical_payload_is_bound_to_cell_count_and_geometry(tmp_path):
    manifest = _complete_manifest(tmp_path)
    cell = next(c for c in manifest["cells"] if c["service"] == "gaia_dr3")
    row = {
        "sightline": cell["sightline"],
        "service": cell["service"],
        "release": cell["release"],
        "status": "matched",
        "source_id": "1",
        "ra_deg": MODULE.SIGHTLINE_COORDS[cell["sightline"]][0],
        "dec_deg": MODULE.SIGHTLINE_COORDS[cell["sightline"]][1],
        "separation_arcmin": 0.0,
        "admission_state": "admitted",
        "native": {"source_id": "1"},
    }
    payload = json.dumps([row], separators=(",", ":")).encode() + b"\n"
    path = tmp_path / cell["canonical_path"]
    stored = gzip.compress(payload, mtime=0) if path.suffix == ".gz" else payload
    path.write_bytes(stored)
    cell["canonical_sha256"] = hashlib.sha256(stored).hexdigest()
    errors = MODULE.validate_manifest(manifest, tmp_path)
    assert any("canonical row count 1 does not equal manifest 0" in error for error in errors)


def test_missing_cell_and_unresolved_service_fail_closed(tmp_path):
    manifest = _complete_manifest(tmp_path)
    manifest["cells"].pop()
    manifest["cells"][0]["status"] = "query_error"
    errors = MODULE.validate_manifest(manifest, tmp_path)
    assert any("missing matrix cell" in error for error in errors)
    assert any("unresolved status query_error" in error for error in errors)


def test_wrong_burst_center_authority_hash_fails_closed(tmp_path):
    manifest = _complete_manifest(tmp_path)
    manifest["input_sha256"] = "a" * 64
    errors = MODULE.validate_manifest(manifest, tmp_path)
    assert any("frozen burst-center authority" in error for error in errors)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("complete", False, "pagination incomplete"),
        ("overflow", True, "response overflow"),
        ("pages", 0, "pagination pages"),
    ],
)
def test_pagination_and_overflow_fail_closed(tmp_path, field, value, message):
    manifest = _complete_manifest(tmp_path)
    manifest["cells"][0]["pagination"][field] = value
    assert any(message in error for error in MODULE.validate_manifest(manifest, tmp_path))


def test_raw_and_canonical_hashes_are_checked_separately(tmp_path):
    manifest = _complete_manifest(tmp_path)
    cell = manifest["cells"][0]
    (tmp_path / cell["raw_path"]).write_bytes(b"changed raw bytes")
    errors = MODULE.validate_manifest(manifest, tmp_path)
    assert any("raw SHA-256 mismatch" in error for error in errors)
    assert not any("canonical SHA-256 mismatch" in error for error in errors)


def test_xray_query_cannot_precede_exposure_coverage(tmp_path):
    manifest = _complete_manifest(tmp_path)
    cell = next(c for c in manifest["cells"] if c["service"] == "xmm_newton_exposure")
    cell["coverage_checked"] = False
    errors = MODULE.validate_manifest(manifest, tmp_path)
    assert any("required coverage not checked" in error for error in errors)


def test_guard_ring_uses_unrounded_spherical_separation():
    assert MODULE.admission_state(15.0) == "admitted"
    assert MODULE.admission_state(15.0 + 1e-12) == "guard_ring"
    assert MODULE.admission_state(15.1) == "guard_ring"
    assert MODULE.admission_state(15.1 + 1e-12) == "outside_query"


def test_cluster_boundary_uses_planck18_proper_separation():
    from astropy.cosmology import Planck18

    redshift = 0.2
    distance_mpc = Planck18.angular_diameter_distance(redshift).value
    boundary_arcmin = math.degrees(5.0 / distance_mpc) * 60.0
    assert MODULE.cluster_admission_state(boundary_arcmin, redshift) == "admitted"
    assert MODULE.cluster_admission_state(boundary_arcmin * (1.0 + 1e-10), redshift) == "outside_query"
    for invalid in (0.0, -0.1, float("nan")):
        with pytest.raises(ValueError):
            MODULE.cluster_projected_separation_mpc(1.0, invalid)


def test_spherical_separation_agrees_with_independent_astropy_path():
    center_ra, center_dec = MODULE.SIGHTLINE_COORDS["zach"]
    row_ra, row_dec = 310.71321, 72.94567
    produced = MODULE.spherical_separation_arcmin(center_ra, center_dec, row_ra, row_dec)
    reference = SkyCoord(row_ra * u.deg, row_dec * u.deg).separation(
        SkyCoord(center_ra * u.deg, center_dec * u.deg)
    ).arcminute
    assert math.isclose(produced, reference, rel_tol=1e-10, abs_tol=1e-12)


def test_missing_native_quality_and_query_provenance_fail(tmp_path):
    manifest = _complete_manifest(tmp_path)
    cell = manifest["cells"][0]
    cell["native_columns"] = []
    cell["exact_query"] = ""
    cell["retrieved_at_utc"] = "2026-07-22T12:00:00"
    errors = MODULE.validate_manifest(manifest, tmp_path)
    assert any("native columns missing" in error for error in errors)
    assert any("exact query missing" in error for error in errors)
    assert any("retrieval time missing or invalid" in error for error in errors)


def test_ps1_strm_route_is_explicitly_not_anonymous_cone_query():
    service = next(service for service in MODULE.SERVICES if service.key == "ps1_strm_v1")
    assert service.transport == "bulk_or_authenticated_casjobs"
    assert service.anonymous_cone is False
    assert service.bulk_object == "hlsp_ps1-strm_ps1_gpc1_p69-p77_multi_v1_cat.csv.gz"


def test_http_200_votable_query_error_is_not_reachable():
    body = b'<INFO name="QUERY_STATUS" value="ERROR">Unsupported format</INFO>'
    assert MODULE.application_response_error(body) == "TAP query status ERROR"


def test_legacy_probe_uses_a_real_table_not_the_join_authority_label():
    service = next(service for service in MODULE.SERVICES if service.key == "legacy_dr10_photoz")
    assert MODULE._tap_probe_query(service) == "SELECT TOP 1 * FROM ls_dr10.photo_z"


def test_source_queries_use_frozen_guard_cone_and_release_tables():
    by_key = {service.key: service for service in MODULE.SERVICES}
    desi_query, desi_count = MODULE.source_queries(by_key["desi_dr1"], "zach")
    assert "0.251666666667" in desi_query
    assert "mean_fiber_ra" in desi_query
    assert "COUNT(*)" in desi_count
    legacy_query, _ = MODULE.source_queries(by_key["legacy_dr10_photoz"], "zach")
    assert "photo_z AS p JOIN ls_dr10.tractor AS t" in legacy_query
    assert "match_ra" in legacy_query
    assert by_key["xmm_newton_exposure"].table == "xmmssc"
    assert by_key["chandra_exposure"].table == "csc"
    assert by_key["swift_exposure"].table == "swiftlsxps"


def test_exposure_first_queries_are_separate_from_source_queries():
    by_key = {service.key: service for service in MODULE.SERVICES}
    for key, coverage_table in (
        ("xmm_newton_exposure", "xmmmaster"),
        ("chandra_exposure", "chanmaster"),
        ("swift_exposure", "swiftmastr"),
    ):
        source, _ = MODULE.source_queries(by_key[key], "zach")
        coverage, coverage_count = MODULE.coverage_queries(by_key[key], "zach")
        assert coverage_table in coverage
        assert by_key[key].table in source
        assert coverage_table not in source
        assert "COUNT(*)" in coverage_count


def test_legacy_and_erass_coverage_routes_are_explicit():
    by_key = {service.key: service for service in MODULE.SERVICES}
    legacy_coverage, _ = MODULE.coverage_queries(by_key["legacy_dr10_photoz"], "zach")
    assert "ls_dr10.tractor" in legacy_coverage
    assert "q3c_radial_query" in legacy_coverage
    assert MODULE.COVERAGE_CONFIG["erass1_main_v1_2"]["kind"] == "erass1_german_half"
    assert MODULE.COVERAGE_CONFIG["erass1_clusters_primary_v3_2"]["kind"] == "erass1_german_half"
    assert MODULE.ERASS1_WESTERN_L_MIN_DEG == 179.94423568
    assert MODULE.ERASS1_WESTERN_L_MAX_DEG == 359.94423568


def test_normalization_is_geometry_first_and_fails_bad_identity():
    service = next(service for service in MODULE.SERVICES if service.key == "gaia_dr3")
    rows, defects = MODULE._normalize_rows(
        service,
        "zach",
        [
            {"source_id": "1", "ra": "310.199525", "dec": "72.8823272222", "quality": "bad"},
            {"source_id": "", "ra": "310.199525", "dec": "72.8823272222"},
            {"source_id": "3", "ra": "10", "dec": "0"},
        ],
    )
    assert len(rows) == 1
    assert rows[0]["native"]["quality"] == "bad"
    assert any("missing stable source identifier" in defect for defect in defects)
    assert any("beyond guard cone" in defect for defect in defects)


def test_ps1_bulk_filter_keeps_admitted_and_guard_ring_rows(tmp_path):
    source = tmp_path / "ps1.csv.gz"
    def ordered_row(**updates):
        native = dict.fromkeys(MODULE.PS1_STRM_COLUMNS, "")
        native.update(updates)
        return ",".join(native[column] for column in MODULE.PS1_STRM_COLUMNS)

    payload = (
        ",".join(MODULE.PS1_STRM_COLUMNS)
        + "\n"
        + ordered_row(
            objID="1", uniquePspsOBid="101", raMean="310.199525", decMean="72.8823272222",
            **{"class": "GALAXY", "z_phot": "0.03", "z_photErr": "0.01", "z_phot0": "0.031",
               "extrapolation_Class": "0", "extrapolation_Photoz": "0"}
        )
        + "\n"
        + ordered_row(
            objID="2", uniquePspsOBid="102", raMean="310.199525", decMean="73.1331605555",
            **{"class": "GALAXY", "z_phot": "0.04", "z_photErr": "0.02", "z_phot0": "0.041",
               "extrapolation_Class": "0", "extrapolation_Photoz": "1"}
        )
        + "\n"
        + ordered_row(objID="3", uniquePspsOBid="103", raMean="10.0", decMean="0.0", **{"class": "STAR"})
        + "\n"
    ).encode()
    with gzip.open(source, "wb") as handle:
        handle.write(payload)
    result = MODULE.extract_ps1_strm(source, tmp_path / "selected.json")
    assert result["source_rows_scanned"] == 3
    assert result["selected_rows"] == 2
    rows = json.loads((tmp_path / "selected.json").read_text())
    assert rows[0]["admission_state"] == "admitted"
    assert rows[0]["native"]["extrapolation_Photoz"] == "0"
    assert rows[1]["admission_state"] == "guard_ring"


def test_ps1_bulk_filter_uses_published_order_for_headerless_archive(tmp_path):
    source = tmp_path / "ps1-headerless.csv.gz"
    native = dict.fromkeys(MODULE.PS1_STRM_COLUMNS, "-999")
    native.update(
        {
            "objID": "1",
            "uniquePspsOBid": "101",
            "raMean": "310.199525",
            "decMean": "72.8823272222",
            "class": "GALAXY",
            "z_phot": "0.03",
            "z_photErr": "0.01",
            "z_phot0": "0.031",
            "extrapolation_Class": "0",
            "extrapolation_Photoz": "0",
        }
    )
    payload = ",".join(native[column] for column in MODULE.PS1_STRM_COLUMNS).encode() + b"\n"
    with gzip.open(source, "wb") as handle:
        handle.write(payload)
    output = tmp_path / "selected.json.gz"
    result = MODULE.extract_ps1_strm(source, output)
    assert result["source_rows_scanned"] == 1
    with gzip.open(output, "rt") as handle:
        rows = json.load(handle)
    assert rows[0]["native"]["uniquePspsOBid"] == "101"
    assert rows[0]["native"]["prob_Galaxy"] == "-999"
    assert result["published_native_columns"] == list(MODULE.PS1_STRM_COLUMNS)
    assert result["canonical_encoding"] == "gzip-json"
