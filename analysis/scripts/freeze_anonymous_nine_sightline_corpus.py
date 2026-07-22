#!/usr/bin/env python3
"""Fail-closed contract and preflight for the anonymous nine-sightline corpus.

This command does not change catalog, redshift, budget, trust, or manuscript
authority.  It defines the required service matrix, freezes small live service
preflight responses, and validates a completed acquisition manifest.  A corpus
is complete only when every required cell has byte-level provenance and no
unresolved, truncated, or overflowed response.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple


SCHEMA_VERSION = "faber2026.anonymous-nine-sightline-corpus.v1"
FROZEN_INPUT_SHA256 = "204fb79727ff71f15269f3d5564215e34d8f027aedbd82719dfda162bdcfb644"
GALAXY_RADIUS_ARCMIN = 15.0
GUARD_RADIUS_ARCMIN = 15.1
SIGHTLINE_NAMES = (
    "zach",
    "whitney",
    "oran",
    "isha",
    "wilhelm",
    "phineas",
    "hamilton",
    "chromatica",
    "casey",
)
SIGHTLINE_COORDS = {
    "zach": (310.199525, 72.8823272222),
    "whitney": (134.7205, 73.4908333333),
    "oran": (318.0448333333, 72.8272777778),
    "isha": (71.411, 70.3073888889),
    "wilhelm": (315.1295416667, 72.0375611111),
    "phineas": (177.7813333333, 71.6956388889),
    "hamilton": (305.0371666667, 70.7927666667),
    "chromatica": (312.619125, 73.9),
    "casey": (169.9835417, 70.67622222),
}
TERMINAL_STATUSES = {"matched", "unmatched", "outside_footprint", "ambiguous"}
UNRESOLVED_STATUSES = {"access_denied", "query_error"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
PS1_STRM_COLUMNS = (
    "objID",
    "uniquePspsOBid",
    "raMean",
    "decMean",
    "l",
    "b",
    "class",
    "prob_Galaxy",
    "prob_Star",
    "prob_QSO",
    "extrapolation_Class",
    "cellDistance_Class",
    "cellID_Class",
    "z_phot",
    "z_photErr",
    "z_phot0",
    "extrapolation_Photoz",
    "cellDistance_Photoz",
    "cellID_Photoz",
)
PS1_STRM_README_URL = (
    "https://archive.stsci.edu/hlsps/ps1-strm/"
    "hlsp_ps1-strm_ps1_gpc1_all_multi_v1_readme.txt"
)
PS1_STRM_SOURCE_URL = (
    "https://archive.stsci.edu/hlsps/ps1-strm/"
    "hlsp_ps1-strm_ps1_gpc1_p69-p77_multi_v1_cat.csv.gz"
)


class Service(NamedTuple):
    key: str
    release: str
    role: str
    transport: str
    endpoint: str
    table: str
    anonymous_cone: bool = True
    bulk_object: str = ""


SERVICES = (
    Service(
        "desi_dr1",
        "DESI DR1 iron zcatalog v1",
        "discovery_spectroscopy",
        "tap",
        "https://datalab.noirlab.edu/tap/sync",
        "desi_dr1.zpix",
    ),
    Service(
        "sdss_dr19",
        "SDSS DR19 SpecObj",
        "discovery_spectroscopy",
        "skyserver_sql",
        "https://skyserver.sdss.org/dr19/SkyServerWS/SearchTools/SqlSearch",
        "SpecObj",
    ),
    Service(
        "lamost_dr11",
        "LAMOST DR11 LRS General Catalog V/162/dr11l",
        "discovery_spectroscopy",
        "tap",
        "https://tapvizier.cds.unistra.fr/TAPVizieR/tap/sync",
        "V/162/dr11l",
    ),
    Service(
        "legacy_dr10_photoz",
        "DESI Legacy Imaging Surveys DR10 photo_z",
        "discovery_photometric_redshift",
        "tap",
        "https://datalab.noirlab.edu/tap/sync",
        "ls_dr10.photo_z + ls_dr10.tractor",
    ),
    Service(
        "ps1_strm_v1",
        "PS1-STRM HLSP v1",
        "discovery_photometric_redshift",
        "bulk_or_authenticated_casjobs",
        "https://archive.stsci.edu/hlsps/ps1-strm/",
        "HLSP_PS1_STRM.catalogRecordRowStore",
        False,
        "hlsp_ps1-strm_ps1_gpc1_p69-p77_multi_v1_cat.csv.gz",
    ),
    Service(
        "jplus_dr3",
        "J-PLUS DR3",
        "coverage_then_photometry",
        "tap",
        "https://archive.cefca.es/catalogues/vo/tap/jplus-dr3/sync",
        "jplus.MagABDualObj",
    ),
    Service(
        "minijpas_pdr201912",
        "miniJPAS PDR201912",
        "coverage_then_photometry",
        "tap",
        "https://archive.cefca.es/catalogues/vo/tap/minijpas-pdr201912/sync",
        "minijpas.MagABDualObj",
    ),
    Service(
        "gaia_dr3",
        "Gaia DR3 gaia_source",
        "classification_enrichment",
        "tap",
        "https://gea.esac.esa.int/tap-server/tap/sync",
        "gaiadr3.gaia_source",
    ),
    Service(
        "lotss_dr3",
        "LoTSS DR3 main_sources",
        "classification_enrichment",
        "tap",
        "https://vo.astron.nl/tap/sync",
        "lotss_dr3.main_sources",
    ),
    Service(
        "vlass_ql_epoch1",
        "CIRADA VLASS Quick Look Epoch 1 component catalog",
        "classification_enrichment",
        "tap",
        "https://tapvizier.cds.unistra.fr/TAPVizieR/tap/sync",
        "J/ApJS/255/30/comp",
    ),
    Service(
        "erass1_main_v1_2",
        "eROSITA eRASS1 Main catalog v1.2",
        "coverage_then_classification",
        "simple_cone_search",
        "https://erosita.mpe.mpg.de/erodat/catalogue/SCS",
        "DR1_Main",
    ),
    Service(
        "xmm_newton_exposure",
        "HEASARC XMMMASTER current snapshot",
        "exposure_first_xray",
        "tap",
        "https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync",
        "xmmmaster",
    ),
    Service(
        "chandra_exposure",
        "HEASARC CHANMASTER current snapshot",
        "exposure_first_xray",
        "tap",
        "https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync",
        "chanmaster",
    ),
    Service(
        "swift_exposure",
        "HEASARC SWIFTMASTR current snapshot",
        "exposure_first_xray",
        "tap",
        "https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync",
        "swiftmastr",
    ),
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def required_cell_keys() -> set[tuple[str, str]]:
    return {(sightline, service.key) for sightline in SIGHTLINE_NAMES for service in SERVICES}


def admission_state(separation_arcmin: float) -> str:
    """Classify using unrounded separation and inclusive contract boundaries."""
    if separation_arcmin <= GALAXY_RADIUS_ARCMIN:
        return "admitted"
    if separation_arcmin <= GUARD_RADIUS_ARCMIN:
        return "guard_ring"
    return "outside_query"


def spherical_separation_arcmin(ra1: float, dec1: float, ra2: float, dec2: float) -> float:
    ra1_rad, dec1_rad, ra2_rad, dec2_rad = map(math.radians, (ra1, dec1, ra2, dec2))
    delta_ra = ra2_rad - ra1_rad
    delta_dec = dec2_rad - dec1_rad
    hav = (
        math.sin(delta_dec / 2.0) ** 2
        + math.cos(dec1_rad) * math.cos(dec2_rad) * math.sin(delta_ra / 2.0) ** 2
    )
    return math.degrees(2.0 * math.asin(math.sqrt(min(1.0, max(0.0, hav))))) * 60.0


def extract_ps1_strm(source: Path, output: Path, expected_size: int | None = None) -> dict:
    """Stream-filter the official high-declination PS1-STRM bulk shard."""
    actual_size = source.stat().st_size
    if expected_size is not None and actual_size != expected_size:
        raise ValueError(f"PS1-STRM shard truncated: expected {expected_size} bytes, found {actual_size}")
    radius_deg = GUARD_RADIUS_ARCMIN / 60.0
    bounding_boxes = {}
    for name, (ra, dec) in SIGHTLINE_COORDS.items():
        ra_halfwidth = radius_deg / max(math.cos(math.radians(dec)), 1e-12)
        bounding_boxes[name] = (ra, dec, ra_halfwidth)

    selected = []
    rows_scanned = 0
    with gzip.open(source, "rt", encoding="utf-8", newline="") as handle:
        first_line = handle.readline()
        first_values = next(csv.reader([first_line]))
        has_header = first_values == list(PS1_STRM_COLUMNS)
        if not has_header:
            handle.seek(0)
        reader = csv.DictReader(handle, fieldnames=PS1_STRM_COLUMNS)
        required_columns = {
            "objID",
            "uniquePspsOBid",
            "raMean",
            "decMean",
            "class",
            "z_phot",
            "z_photErr",
            "z_phot0",
            "extrapolation_Class",
            "extrapolation_Photoz",
        }
        available = set(reader.fieldnames or ())
        missing = sorted(required_columns - available)
        if missing:
            raise ValueError(f"PS1-STRM shard missing native columns: {', '.join(missing)}")
        for row in reader:
            rows_scanned += 1
            try:
                row_ra = float(row["raMean"])
                row_dec = float(row["decMean"])
            except (TypeError, ValueError):
                continue
            for sightline, (center_ra, center_dec, ra_halfwidth) in bounding_boxes.items():
                delta_ra = abs((row_ra - center_ra + 180.0) % 360.0 - 180.0)
                if abs(row_dec - center_dec) > radius_deg or delta_ra > ra_halfwidth:
                    continue
                separation = spherical_separation_arcmin(center_ra, center_dec, row_ra, row_dec)
                state = admission_state(separation)
                if state == "outside_query":
                    continue
                selected.append(
                    {
                        "sightline": sightline,
                        "service": "ps1_strm_v1",
                        "source_id": row["uniquePspsOBid"] or row["objID"],
                        "ra_deg": row_ra,
                        "dec_deg": row_dec,
                        "separation_arcmin": separation,
                        "admission_state": state,
                        "native": row,
                    }
                )
    selected.sort(key=lambda row: (row["sightline"], row["separation_arcmin"], row["source_id"]))
    output.parent.mkdir(parents=True, exist_ok=True)
    canonical = json.dumps(selected, indent=2, sort_keys=True, allow_nan=False).encode() + b"\n"
    stored_canonical = gzip.compress(canonical, mtime=0) if output.suffix == ".gz" else canonical
    output.write_bytes(stored_canonical)
    return {
        "service": "ps1_strm_v1",
        "release": "PS1-STRM HLSP v1",
        "source_url": PS1_STRM_SOURCE_URL,
        "published_schema_url": PS1_STRM_README_URL,
        "published_native_columns": list(PS1_STRM_COLUMNS),
        "source_path": str(source),
        "source_size_bytes": actual_size,
        "source_sha256": sha256_file(source),
        "source_rows_scanned": rows_scanned,
        "selected_rows": len(selected),
        "guard_ring_rows": sum(row["admission_state"] == "guard_ring" for row in selected),
        "canonical_path": str(output),
        "canonical_encoding": "gzip-json" if output.suffix == ".gz" else "json",
        "canonical_sha256": sha256_bytes(stored_canonical),
        "exact_query": (
            "stream all rows from official p69-p77 shard; retain unrounded exact spherical "
            "separation <= 15.1 arcmin for each frozen burst center; admit <= 15.0 arcmin"
        ),
        "completed_at_utc": utc_now(),
    }


def _safe_evidence_path(root: Path, value: object, label: str, errors: list[str]) -> Path | None:
    if not isinstance(value, str) or not value:
        errors.append(f"{label} missing")
        return None
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        errors.append(f"{label} must be a relative contained path")
        return None
    path = root / relative
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        errors.append(f"{label} escapes evidence root")
        return None
    return path


def _check_hash(path: Path | None, expected: object, label: str, errors: list[str]) -> None:
    if not isinstance(expected, str) or not SHA256_RE.fullmatch(expected):
        errors.append(f"{label} SHA-256 missing or malformed")
        return
    if path is None or not path.is_file():
        errors.append(f"{label} bytes missing")
        return
    actual = sha256_file(path)
    if actual != expected:
        errors.append(f"{label} SHA-256 mismatch")


def validate_manifest(manifest: dict, evidence_root: Path) -> list[str]:
    """Return all contract failures; an empty list is the only passing verdict."""
    errors: list[str] = []
    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema version mismatch")
    if manifest.get("input_sha256") != FROZEN_INPUT_SHA256:
        errors.append("input SHA-256 does not match frozen burst-center authority")

    raw_cells = manifest.get("cells")
    if not isinstance(raw_cells, list):
        return errors + ["cells must be a list"]

    cells: dict[tuple[str, str], dict] = {}
    for index, cell in enumerate(raw_cells):
        if not isinstance(cell, dict):
            errors.append(f"cell {index} is not an object")
            continue
        key = (str(cell.get("sightline", "")), str(cell.get("service", "")))
        if key in cells:
            errors.append(f"duplicate matrix cell {key[0]}/{key[1]}")
        cells[key] = cell

    required = required_cell_keys()
    for sightline, service in sorted(required - set(cells)):
        errors.append(f"missing matrix cell {sightline}/{service}")
    for sightline, service in sorted(set(cells) - required):
        errors.append(f"unexpected matrix cell {sightline}/{service}")

    service_by_key = {service.key: service for service in SERVICES}
    for key in sorted(required & set(cells)):
        cell = cells[key]
        prefix = f"{key[0]}/{key[1]}"
        service = service_by_key[key[1]]
        for field, expected in (
            ("release", service.release),
            ("role", service.role),
            ("endpoint", service.endpoint),
        ):
            if cell.get(field) != expected:
                errors.append(f"{prefix}: {field} does not match frozen service authority")

        status = cell.get("status")
        if status in UNRESOLVED_STATUSES:
            errors.append(f"{prefix}: unresolved status {status}")
        elif status not in TERMINAL_STATUSES:
            errors.append(f"{prefix}: invalid status {status}")
        if cell.get("coverage") not in {"inside", "outside", "not_applicable"}:
            errors.append(f"{prefix}: coverage state missing or invalid")
        if not isinstance(cell.get("exact_query"), str) or not cell["exact_query"].strip():
            errors.append(f"{prefix}: exact query missing")
        retrieved_at = cell.get("retrieved_at_utc")
        try:
            if not isinstance(retrieved_at, str) or not retrieved_at.endswith("Z"):
                raise ValueError
            parsed_retrieval = datetime.fromisoformat(retrieved_at.replace("Z", "+00:00"))
            if parsed_retrieval.utcoffset() != timezone.utc.utcoffset(parsed_retrieval):
                raise ValueError
        except ValueError:
            errors.append(f"{prefix}: retrieval time missing or invalid")
        native_columns = cell.get("native_columns")
        if not isinstance(native_columns, list) or not native_columns:
            errors.append(f"{prefix}: native columns missing")

        row_count = cell.get("row_count")
        guard_count = cell.get("guard_ring_count")
        if not isinstance(row_count, int) or row_count < 0:
            errors.append(f"{prefix}: row count missing or invalid")
        if not isinstance(guard_count, int) or guard_count < 0:
            errors.append(f"{prefix}: guard-ring count missing or invalid")
        elif isinstance(row_count, int) and guard_count > row_count:
            errors.append(f"{prefix}: guard-ring count exceeds row count")
        if status in {"unmatched", "outside_footprint"} and row_count != 0:
            errors.append(f"{prefix}: {status} cell has rows")
        if status == "matched" and row_count == 0:
            errors.append(f"{prefix}: matched cell has no rows")

        pagination = cell.get("pagination")
        if not isinstance(pagination, dict):
            errors.append(f"{prefix}: pagination evidence missing")
        else:
            if pagination.get("complete") is not True:
                errors.append(f"{prefix}: pagination incomplete")
            if pagination.get("overflow") is not False:
                errors.append(f"{prefix}: response overflow")
            if not isinstance(pagination.get("pages"), int) or pagination["pages"] < 1:
                errors.append(f"{prefix}: pagination pages missing or invalid")
            server_total = pagination.get("server_total")
            if server_total is not None and isinstance(row_count, int) and server_total != row_count:
                errors.append(f"{prefix}: server total does not equal frozen row count")

        raw_path = _safe_evidence_path(evidence_root, cell.get("raw_path"), f"{prefix}: raw", errors)
        canonical_path = _safe_evidence_path(
            evidence_root, cell.get("canonical_path"), f"{prefix}: canonical", errors
        )
        _check_hash(raw_path, cell.get("raw_sha256"), f"{prefix}: raw", errors)
        _check_hash(canonical_path, cell.get("canonical_sha256"), f"{prefix}: canonical", errors)
        if raw_path is not None and canonical_path is not None and raw_path == canonical_path:
            errors.append(f"{prefix}: raw and canonical evidence paths must differ")

        if service.role == "exposure_first_xray":
            if cell.get("coverage_checked") is not True:
                errors.append(f"{prefix}: exposure coverage not checked")
            coverage_path = _safe_evidence_path(
                evidence_root,
                cell.get("coverage_evidence_path"),
                f"{prefix}: exposure coverage",
                errors,
            )
            _check_hash(
                coverage_path,
                cell.get("coverage_evidence_sha256"),
                f"{prefix}: exposure coverage",
                errors,
            )
    return errors


def _tap_probe_query(service: Service) -> str:
    table = service.table
    if service.key == "legacy_dr10_photoz":
        table = "ls_dr10.photo_z"
    if "/" in table:
        table = f'"{table}"'
    return f"SELECT TOP 1 * FROM {table}"


def application_response_error(body: bytes) -> str | None:
    """Detect protocol errors that some services return with HTTP 200."""
    normalized = body[:65536].upper().replace(b"'", b'"')
    if b"QUERY_STATUS" in normalized and b'VALUE="ERROR"' in normalized:
        return "TAP query status ERROR"
    return None


def _probe_request(service: Service) -> urllib.request.Request:
    if service.transport == "tap":
        output_format = "votable" if "heasarc.gsfc.nasa.gov" in service.endpoint else "csv"
        params = urllib.parse.urlencode(
            {
                "REQUEST": "doQuery",
                "LANG": "ADQL",
                "FORMAT": output_format,
                "QUERY": _tap_probe_query(service),
            }
        )
        return urllib.request.Request(f"{service.endpoint}?{params}")
    if service.transport == "skyserver_sql":
        params = urllib.parse.urlencode(
            {"cmd": "SELECT TOP 1 specObjID,ra,dec,z,zErr,zWarning,class FROM SpecObj", "format": "csv"}
        )
        return urllib.request.Request(f"{service.endpoint}?{params}")
    if service.transport == "simple_cone_search":
        params = urllib.parse.urlencode(
            {"CAT": service.table, "RA": 310.199525, "DEC": 72.8823272222, "SR": 0.001, "VERB": 3}
        )
        return urllib.request.Request(f"{service.endpoint}?{params}")
    if service.transport == "bulk_or_authenticated_casjobs":
        return urllib.request.Request(service.endpoint + service.bulk_object, method="HEAD")
    raise ValueError(f"unsupported transport: {service.transport}")


def run_preflight(output_dir: Path, timeout: float) -> dict:
    raw_root = output_dir / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    entries = []
    for service in SERVICES:
        request = _probe_request(service)
        retrieved = utc_now()
        status = "query_error"
        http_status = None
        headers: dict[str, str] = {}
        body = b""
        error = None
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                http_status = response.status
                headers = {key.lower(): value for key, value in response.headers.items()}
                body = response.read()
                protocol_error = application_response_error(body)
                if protocol_error:
                    status = "query_error"
                    error = protocol_error
                else:
                    status = "reachable" if service.anonymous_cone else "bulk_reachable_no_anonymous_cone"
        except urllib.error.HTTPError as exc:
            http_status = exc.code
            headers = {key.lower(): value for key, value in exc.headers.items()}
            body = exc.read()
            status = "access_denied" if exc.code in {401, 403} else "query_error"
            error = f"HTTP {exc.code}"
        except (urllib.error.URLError, TimeoutError) as exc:
            error = str(exc)

        if request.get_method() == "HEAD":
            body = json.dumps(headers, sort_keys=True, separators=(",", ":")).encode()
        raw_path = raw_root / f"{service.key}.bin"
        raw_path.write_bytes(body)
        entries.append(
            {
                "service": service.key,
                "release": service.release,
                "role": service.role,
                "transport": service.transport,
                "endpoint": service.endpoint,
                "table": service.table,
                "request_url": request.full_url,
                "request_method": request.get_method(),
                "retrieved_at_utc": retrieved,
                "http_status": http_status,
                "status": status,
                "anonymous_cone": service.anonymous_cone,
                "raw_path": str(raw_path.relative_to(output_dir)),
                "raw_sha256": sha256_bytes(body),
                "response_bytes": len(body),
                "content_length": headers.get("content-length"),
                "error": error,
            }
        )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "purpose": "service capability preflight only; not a completed query corpus",
        "generated_at_utc": utc_now(),
        "complete_corpus": False,
        "required_sightlines": list(SIGHTLINE_NAMES),
        "required_services": [service.key for service in SERVICES],
        "entries": entries,
    }
    manifest_path = output_dir / "service-preflight.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate", help="validate a completed corpus manifest")
    validate.add_argument("manifest", type=Path)
    validate.add_argument("--evidence-root", type=Path)
    preflight = subparsers.add_parser("preflight", help="freeze small live service capability responses")
    preflight.add_argument("--output-dir", type=Path, required=True)
    preflight.add_argument("--timeout", type=float, default=30.0)
    extract_ps1 = subparsers.add_parser("extract-ps1", help="stream-filter the official PS1-STRM shard")
    extract_ps1.add_argument("--input", type=Path, required=True)
    extract_ps1.add_argument("--output", type=Path, required=True)
    extract_ps1.add_argument("--manifest", type=Path, required=True)
    extract_ps1.add_argument("--expected-size", type=int, default=4_650_535_027)
    args = parser.parse_args()

    if args.command == "validate":
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        root = args.evidence_root or args.manifest.parent
        errors = validate_manifest(manifest, root)
        if errors:
            for error in errors:
                print(f"FAIL: {error}", file=sys.stderr)
            return 1
        print("PASS: all 126 service-sightline cells satisfy the frozen corpus contract")
        return 0

    if args.command == "preflight":
        manifest = run_preflight(args.output_dir, args.timeout)
        reachable = sum(entry["status"] == "reachable" for entry in manifest["entries"])
        blocked = len(manifest["entries"]) - reachable
        print(f"Preflight: {reachable} anonymous query routes reachable; {blocked} unresolved or non-cone routes")
        return 1 if blocked else 0

    result = extract_ps1_strm(args.input, args.output, args.expected_size)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"PS1-STRM: scanned {result['source_rows_scanned']} rows; "
        f"selected {result['selected_rows']} within guard cones"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
