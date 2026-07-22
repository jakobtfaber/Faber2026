import hashlib
import gzip
import importlib.util
import io
import json
import math
from pathlib import Path
import shutil

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
            guard_path = Path("guard") / sightline / f"{service.key}.json"
            raw_sha = _write(tmp_path / raw_path, b"source_id,ra,dec\n")
            canonical = json.dumps([], separators=(",", ":")).encode()
            canonical_sha = _write(tmp_path / canonical_path, canonical)
            guard_sha = _write(tmp_path / guard_path, canonical)
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
                "guard_evidence_path": str(guard_path),
                "guard_evidence_sha256": guard_sha,
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
                kind = MODULE.COVERAGE_CONFIG[service.key]["kind"]
                method = {
                    "legacy_nexp": "legacy_dr10_official_nexp_positive_pixels",
                    "tap_polygon": "tap_polygon",
                    "stcs_polygon": "stcs_polygon",
                    "official_exposure_maps_required": "swift_official_exposure_maps",
                }.get(kind)
                if method:
                    cell["coverage_method"] = method
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


def test_packed_evidence_validates_without_loose_members(tmp_path):
    manifest = _complete_manifest(tmp_path)
    manifest_path = tmp_path / "corpus-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    result = MODULE.pack_evidence(tmp_path)
    assert result["member_count"] > 0
    for directory in ("raw", "canonical", "guard", "counts", "coverage"):
        shutil.rmtree(tmp_path / directory, ignore_errors=True)
    packed_manifest = json.loads(manifest_path.read_text())
    assert MODULE.validate_manifest(packed_manifest, tmp_path) == []
    bundle = tmp_path / packed_manifest["evidence_bundle_path"]
    bundle.write_bytes(bundle.read_bytes() + b"tamper")
    assert "evidence bundle SHA-256 mismatch" in MODULE.validate_manifest(
        packed_manifest, tmp_path
    )


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
    xmm_source, _ = MODULE.source_queries(by_key["xmm_newton_exposure"], "zach")
    assert "xmmssc" in xmm_source
    assert MODULE.coverage_queries(by_key["xmm_newton_exposure"], "zach") is None
    xmm_config = MODULE.COVERAGE_CONFIG["xmm_newton_exposure"]
    assert xmm_config["endpoint"] == "https://nxsa.esac.esa.int/tap-server/tap/sync"
    assert xmm_config["table"] == "xsa.v_public_observations"
    assert xmm_config["region_column"] == "footprint_fov"
    assert MODULE.coverage_queries(by_key["chandra_exposure"], "zach") is None
    assert MODULE.COVERAGE_CONFIG["chandra_exposure"]["table"] == "ivoa.ObsCore"
    assert MODULE.coverage_queries(by_key["swift_exposure"], "zach") is None
    assert MODULE.COVERAGE_CONFIG["swift_exposure"]["kind"] == "official_exposure_maps_required"


def test_xmm_exact_coverage_uses_only_xsa_route(tmp_path, monkeypatch):
    service = next(s for s in MODULE.SERVICES if s.key == "xmm_newton_exposure")
    requests = []

    def fake_fetch(request, timeout):
        requests.append(request)
        return b"observation_id,footprint_fov\n", {}, 200, "2026-07-22T12:00:00Z"

    monkeypatch.setattr(MODULE, "_fetch", fake_fetch)
    result = MODULE.exact_coverage(service, "zach", tmp_path, 10.0)
    assert result["coverage"] == "outside"
    assert len(requests) == 1
    assert requests[0].full_url == "https://nxsa.esac.esa.int/tap-server/tap/sync"
    assert b"xsa.v_public_observations" in requests[0].data
    assert b"footprint_fov" in requests[0].data
    assert b"xmmmaster" not in requests[0].data


def test_xmm_footprint_overflow_fails_closed(tmp_path, monkeypatch):
    service = next(s for s in MODULE.SERVICES if s.key == "xmm_newton_exposure")
    overflow = b'''<?xml version="1.0"?>
<VOTABLE xmlns="http://www.ivoa.net/xml/VOTable/v1.3" version="1.3">
  <RESOURCE type="results">
    <INFO name = "QUERY_STATUS" value = "OVERFLOW" />
    <TABLE>
      <FIELD name="observation_id" datatype="char" arraysize="*" />
      <FIELD name="footprint_fov" datatype="char" arraysize="*" />
      <DATA><TABLEDATA></TABLEDATA></DATA>
    </TABLE>
  </RESOURCE>
</VOTABLE>'''
    assert MODULE.application_response_overflow(overflow)
    monkeypatch.setattr(
        MODULE,
        "_fetch",
        lambda request, timeout: (overflow, {}, 200, "2026-07-22T12:00:00Z"),
    )
    with pytest.raises(MODULE.CoverageUnavailable, match="OVERFLOW"):
        MODULE.exact_coverage(service, "zach", tmp_path, 10.0)


def test_non_overflow_zero_row_xmm_votable_is_outside(tmp_path, monkeypatch):
    service = next(s for s in MODULE.SERVICES if s.key == "xmm_newton_exposure")
    empty = b'''<?xml version="1.0"?>
<VOTABLE xmlns="http://www.ivoa.net/xml/VOTable/v1.3" version="1.3">
  <RESOURCE type="results">
    <INFO name = "QUERY_STATUS" value = "OK" />
    <TABLE>
      <FIELD name="observation_id" datatype="char" arraysize="*" />
      <FIELD name="footprint_fov" datatype="char" arraysize="*" />
      <DATA><TABLEDATA></TABLEDATA></DATA>
    </TABLE>
  </RESOURCE>
</VOTABLE>'''
    monkeypatch.setattr(
        MODULE, "_fetch", lambda request, timeout: (empty, {}, 200, "2026-07-22T12:00:00Z")
    )
    assert MODULE.exact_coverage(service, "zach", tmp_path, 10.0)["coverage"] == "outside"


def test_legacy_nexp_bundle_replays_offline_and_rejects_byte_tamper():
    import numpy as np
    from astropy.io import fits
    from astropy.wcs import WCS

    ra, dec = MODULE.SIGHTLINE_COORDS["zach"]
    wcs = WCS(naxis=2)
    wcs.wcs.crpix = [3.0, 3.0]
    wcs.wcs.cdelt = [-0.001, 0.001]
    wcs.wcs.crval = [ra, dec]
    wcs.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    data = np.zeros((5, 5), dtype=np.int16)
    data[2, 2] = 1
    handle = io.BytesIO()
    fits.PrimaryHDU(data=data, header=wcs.to_header()).writeto(handle)
    image = handle.getvalue()
    bundle = MODULE._legacy_nexp_bundle(
        b"brickname,ra1,ra2,dec1,dec2\n3101p728,0,0,0,0\n",
        {"3101p728/g.fits.fz": image},
    )
    assert MODULE.replay_legacy_nexp_bundle(bundle, ra, dec) == (True, 1)

    import tarfile

    with tarfile.open(fileobj=io.BytesIO(bundle), mode="r:") as archive:
        members = {
            member.name: archive.extractfile(member).read()
            for member in archive.getmembers()
            if member.isfile()
        }
    members["nexp/3101p728/g.fits.fz"] += b"tamper"
    tampered = MODULE._deterministic_tar(members)
    with pytest.raises(ValueError, match="byte hash mismatch"):
        MODULE.replay_legacy_nexp_bundle(tampered, ra, dec)


def test_legacy_coverage_manifest_artifact_contains_every_fits_byte(tmp_path, monkeypatch):
    import numpy as np
    from astropy.io import fits
    from astropy.wcs import WCS

    service = next(s for s in MODULE.SERVICES if s.key == "legacy_dr10_photoz")
    ra, dec = MODULE.SIGHTLINE_COORDS["zach"]
    wcs = WCS(naxis=2)
    wcs.wcs.crpix = [2.0, 2.0]
    wcs.wcs.cdelt = [-0.001, 0.001]
    wcs.wcs.crval = [ra, dec]
    wcs.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    data = np.zeros((3, 3), dtype=np.int16)
    data[1, 1] = 1
    image_handle = io.BytesIO()
    fits.PrimaryHDU(data=data, header=wcs.to_header()).writeto(image_handle)
    image = image_handle.getvalue()
    brick = b"brickname,ra1,ra2,dec1,dec2\n3101p728,309,311,72,73\n"
    responses = iter([brick, image, image, image, image])
    monkeypatch.setattr(
        MODULE,
        "_fetch",
        lambda request, timeout: (next(responses), {}, 200, "2026-07-22T12:00:00Z"),
    )
    result = MODULE._legacy_nexp_coverage(
        service, "zach", tmp_path, 10.0, MODULE.COVERAGE_CONFIG[service.key]
    )
    artifact = tmp_path / result["coverage_evidence_path"]
    assert hashlib.sha256(artifact.read_bytes()).hexdigest() == result["coverage_evidence_sha256"]
    assert result["coverage_fits_member_count"] == 4
    assert MODULE.replay_legacy_nexp_bundle(gzip.decompress(artifact.read_bytes()), ra, dec) == (True, 4)


def test_legacy_and_erass_coverage_routes_are_explicit():
    by_key = {service.key: service for service in MODULE.SERVICES}
    assert MODULE.coverage_queries(by_key["legacy_dr10_photoz"], "zach") is None
    assert MODULE.COVERAGE_CONFIG["legacy_dr10_photoz"]["kind"] == "legacy_nexp"
    assert MODULE.COVERAGE_CONFIG["legacy_dr10_photoz"]["image_root"].startswith("https://portal.nersc.gov/")
    assert MODULE.COVERAGE_CONFIG["erass1_main_v1_2"]["kind"] == "erass1_german_half"
    assert MODULE.COVERAGE_CONFIG["erass1_clusters_primary_v3_2"]["kind"] == "erass1_german_half"
    assert MODULE.ERASS1_WESTERN_L_MIN_DEG == 179.94423568
    assert MODULE.ERASS1_WESTERN_L_MAX_DEG == 359.94423568


def test_csc_stcs_polygon_overlap_is_exact_at_cone_boundary():
    center_ra, center_dec = MODULE.SIGHTLINE_COORDS["zach"]
    crossing = (
        f"POLYGON ICRS {center_ra-0.01} {center_dec-0.01} "
        f"{center_ra+0.01} {center_dec-0.01} {center_ra} {center_dec+0.01}"
    )
    distant = "POLYGON ICRS 10 0 11 0 10 1"
    assert MODULE._exact_stcs_intersects_cone(crossing, center_ra, center_dec)
    assert not MODULE._exact_stcs_intersects_cone(distant, center_ra, center_dec)

    def tiny_polygon(radial_arcsec):
        dec = center_dec + radial_arcsec / 3600.0
        half_dec = 0.1 / 3600.0
        half_ra = half_dec / math.cos(math.radians(dec))
        return (
            f"POLYGON ICRS {center_ra-half_ra} {dec-half_dec} "
            f"{center_ra+half_ra} {dec-half_dec} {center_ra+half_ra} {dec+half_dec} "
            f"{center_ra-half_ra} {dec+half_dec}"
        )

    guard_arcsec = MODULE.GUARD_RADIUS_ARCMIN * 60.0
    # 15 arcmin + 5 arcsec is outside admission but still inside the 15.1-arcmin
    # acquisition guard cone; a pixelized MOC must not decide this boundary.
    assert MODULE._exact_stcs_intersects_cone(tiny_polygon(15.0 * 60.0 + 5.0), center_ra, center_dec)
    assert MODULE._exact_stcs_intersects_cone(tiny_polygon(guard_arcsec - 1.0), center_ra, center_dec)
    assert not MODULE._exact_stcs_intersects_cone(tiny_polygon(guard_arcsec + 5.0), center_ra, center_dec)


def test_chandra_requires_server_count_and_complete_response(tmp_path, monkeypatch):
    service = next(s for s in MODULE.SERVICES if s.key == "chandra_exposure")
    count = b"row_total\n1\n"
    rows = b'obs_id,s_region\none,"POLYGON ICRS 10 0 11 0 10 1"\n'
    requests = []

    def fake_fetch(request, timeout):
        requests.append(request)
        return (count if len(requests) == 1 else rows), {}, 200, "2026-07-22T12:00:00Z"

    monkeypatch.setattr(MODULE, "_fetch", fake_fetch)
    result = MODULE.exact_coverage(service, "zach", tmp_path, 10.0)
    assert result["coverage"] == "outside"
    assert len(requests) == 2
    assert b"COUNT%28%2A%29" in requests[0].data
    assert b"SELECT+obs_id%2Cs_region" in requests[1].data


def test_chandra_count_mismatch_and_overflow_fail_closed(tmp_path, monkeypatch):
    service = next(s for s in MODULE.SERVICES if s.key == "chandra_exposure")
    count = b"row_total\n2\n"
    rows = b'obs_id,s_region\none,"POLYGON ICRS 10 0 11 0 10 1"\n'
    responses = iter((count, rows))
    monkeypatch.setattr(
        MODULE, "_fetch", lambda request, timeout: (next(responses), {}, 200, "2026-07-22T12:00:00Z")
    )
    with pytest.raises(MODULE.CoverageUnavailable, match="incomplete"):
        MODULE.exact_coverage(service, "zach", tmp_path, 10.0)

    overflow = b'<INFO name="QUERY_STATUS" value="OVERFLOW"/>'
    responses = iter((b"row_total\n1\n", overflow))
    with pytest.raises(MODULE.CoverageUnavailable, match="OVERFLOW"):
        MODULE.exact_coverage(service, "zach", tmp_path, 10.0)


def test_proxy_coverage_methods_fail_closed(tmp_path):
    manifest = _complete_manifest(tmp_path)
    for key in ("legacy_dr10_photoz", "xmm_newton_exposure", "chandra_exposure"):
        cell = next(c for c in manifest["cells"] if c["service"] == key)
        cell.pop("coverage_method", None)
    swift = next(c for c in manifest["cells"] if c["service"] == "swift_exposure")
    swift.pop("coverage_method", None)
    errors = MODULE.validate_manifest(manifest, tmp_path)
    assert sum("exact official coverage method missing or superseded" in e for e in errors) == 3
    assert any("Swift terminal state lacks exact official exposure-map evidence" in e for e in errors)


def test_normalization_is_geometry_first_and_fails_bad_identity():
    service = next(service for service in MODULE.SERVICES if service.key == "gaia_dr3")
    rows, guard_rows, defects = MODULE._normalize_rows(
        service,
        "zach",
        [
            {"source_id": "1", "ra": "310.199525", "dec": "72.8823272222", "quality": "bad"},
            {"source_id": "", "ra": "310.199525", "dec": "72.8823272222"},
            {"source_id": "3", "ra": "10", "dec": "0"},
        ],
    )
    assert len(rows) == 1
    assert guard_rows == []
    assert rows[0]["native"]["quality"] == "bad"
    assert any("missing stable source identifier" in defect for defect in defects)
    assert any("beyond guard cone" in defect for defect in defects)


def test_normalization_separates_guard_rows_from_admitted_corpus():
    service = next(service for service in MODULE.SERVICES if service.key == "gaia_dr3")
    center_ra, center_dec = MODULE.SIGHTLINE_COORDS["zach"]
    guard_dec = center_dec + 15.05 / 60.0
    admitted, guard, defects = MODULE._normalize_rows(
        service,
        "zach",
        [
            {"source_id": "inside", "ra": center_ra, "dec": center_dec},
            {"source_id": "guard", "ra": center_ra, "dec": guard_dec},
        ],
    )
    assert defects == []
    assert [row["source_id"] for row in admitted] == ["inside"]
    assert [row["source_id"] for row in guard] == ["guard"]
    assert admitted[0]["status"] == "matched"
    assert guard[0]["status"] == "guard_only"


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
