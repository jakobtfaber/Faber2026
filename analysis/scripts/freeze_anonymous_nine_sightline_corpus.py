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
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import gzip
import hashlib
import io
import json
import math
import re
import sys
import tarfile
import time
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
ERASS1_WESTERN_L_MIN_DEG = 179.94423568
ERASS1_WESTERN_L_MAX_DEG = 359.94423568
ERASS1_CATALOG_AUTHORITY_URL = (
    "https://erosita.mpe.mpg.de/dr1/AllSkySurveyData_dr1/Catalogues_dr1/"
)
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


class EvidenceStore:
    """Read evidence from loose acquisition files or the deterministic bundle."""

    def __init__(self, root: Path, bundle_name: str | None = None):
        self.root = root
        self.bundle_path = root / (bundle_name or "evidence-bundle.tar.gz")
        self._archive = tarfile.open(self.bundle_path, "r:gz") if self.bundle_path.is_file() else None

    def close(self) -> None:
        if self._archive is not None:
            self._archive.close()

    def read(self, path: Path) -> bytes:
        if path.is_file():
            return path.read_bytes()
        if self._archive is None:
            raise FileNotFoundError(path)
        relative = path.resolve().relative_to(self.root.resolve()).as_posix()
        try:
            member = self._archive.getmember(relative)
        except KeyError as exc:
            raise FileNotFoundError(path) from exc
        extracted = self._archive.extractfile(member)
        if extracted is None:
            raise FileNotFoundError(path)
        return extracted.read()

    def sha256(self, path: Path) -> str:
        return sha256_bytes(self.read(path))

    def member_names(self) -> list[str]:
        if self._archive is None:
            return []
        return [member.name for member in self._archive.getmembers() if member.isfile()]


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
        "erass1_clusters_primary_v3_2",
        "eROSITA eRASS1 galaxy groups and clusters primary catalogue v3.2",
        "cluster_discovery",
        "bulk_full_catalog",
        ERASS1_CATALOG_AUTHORITY_URL + "BulbulE_DR1/",
        "erass1cl_main_v3.2.fits",
        True,
        "erass1cl_primary_v3.2.fits.tgz",
    ),
    Service(
        "xmm_newton_exposure",
        "5XMM-DR15 XMM-Newton Serendipitous Source Catalog",
        "exposure_first_xray",
        "tap",
        "https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync",
        "xmmssc",
    ),
    Service(
        "chandra_exposure",
        "Chandra Source Catalog v2.1.1",
        "exposure_first_xray",
        "tap",
        "https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync",
        "csc",
    ),
    Service(
        "swift_exposure",
        "Swift-XRT Living Point Source Catalog snapshot 2026-07-22",
        "exposure_first_xray",
        "tap",
        "https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync",
        "swiftlsxps",
    ),
)

QUERY_CONFIG = {
    "desi_dr1": {"ra": "mean_fiber_ra", "dec": "mean_fiber_dec", "ids": ("targetid",)},
    "sdss_dr19": {"ra": "ra", "dec": "dec", "ids": ("specObjID",)},
    "lamost_dr11": {"ra": "RAJ2000", "dec": "DEJ2000", "ids": ("ObsID",)},
    "legacy_dr10_photoz": {"ra": "match_ra", "dec": "match_dec", "ids": ("ls_id",)},
    "jplus_dr3": {"ra": "ALPHA_J2000", "dec": "DELTA_J2000", "ids": ("TILE_ID", "NUMBER")},
    "minijpas_pdr201912": {
        "ra": "ALPHA_J2000",
        "dec": "DELTA_J2000",
        "ids": ("TILE_ID", "NUMBER"),
    },
    "gaia_dr3": {"ra": "ra", "dec": "dec", "ids": ("source_id",)},
    "lotss_dr3": {"ra": "ra", "dec": "dec", "ids": ("source_name",)},
    "vlass_ql_epoch1": {"ra": "RAJ2000", "dec": "DEJ2000", "ids": ("CompName", "CompId")},
    "erass1_main_v1_2": {"ra": "ra", "dec": "dec", "ids": ("uid",)},
    "erass1_clusters_primary_v3_2": {
        "ra": "RA",
        "dec": "DEC",
        "ids": ("NAME",),
        "redshift": "BEST_Z",
    },
    "xmm_newton_exposure": {"ra": "ra", "dec": "dec", "ids": ("srcid",)},
    "chandra_exposure": {"ra": "ra", "dec": "dec", "ids": ("name",)},
    "swift_exposure": {"ra": "ra", "dec": "dec", "ids": ("source_number",)},
}

COVERAGE_CONFIG = {
    "legacy_dr10_photoz": {
        "table": "ls_dr10.tractor",
        "kind": "catalog",
    },
    "jplus_dr3": {
        "table": "ivoa.ObsCore",
        "kind": "region",
    },
    "minijpas_pdr201912": {
        "table": "ivoa.ObsCore",
        "kind": "region",
    },
    "erass1_main_v1_2": {
        "kind": "erass1_german_half",
        "authority": (
            "eROSITA-DE DR1 data-rights boundary: "
            "179.94423568 < Galactic longitude < 359.94423568 degrees"
        ),
        "authority_url": "https://erosita.mpe.mpg.de/dr1/",
    },
    "erass1_clusters_primary_v3_2": {
        "kind": "erass1_german_half",
        "authority": (
            "eROSITA-DE DR1 data-rights boundary: "
            "179.94423568 < Galactic longitude < 359.94423568 degrees"
        ),
        "authority_url": "https://erosita.mpe.mpg.de/dr1/",
    },
    "xmm_newton_exposure": {
        "table": "xmmmaster",
        "kind": "pointing",
        "radius_deg": 1.0,
    },
    "chandra_exposure": {
        "table": "chanmaster",
        "kind": "pointing",
        "radius_deg": 1.0,
    },
    "swift_exposure": {
        "table": "swiftmastr",
        "kind": "pointing",
        "radius_deg": 1.0,
    },
}


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


def cluster_projected_separation_mpc(separation_arcmin: float, redshift: float) -> float:
    """Return proper transverse separation under the ticket-13 Planck18 rule."""
    if not math.isfinite(redshift) or redshift <= 0:
        raise ValueError("cluster search geometry requires a finite positive redshift")
    from astropy.cosmology import Planck18
    import astropy.units as u

    theta = (separation_arcmin * u.arcmin).to_value(u.rad)
    return float(theta * Planck18.angular_diameter_distance(redshift).to_value(u.Mpc))


def cluster_admission_state(separation_arcmin: float, redshift: float) -> str:
    return "admitted" if cluster_projected_separation_mpc(separation_arcmin, redshift) <= 5.0 else "outside_query"


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
                        "release": "PS1-STRM HLSP v1",
                        "source_id": row["uniquePspsOBid"] or row["objID"],
                        "ra_deg": row_ra,
                        "dec_deg": row_dec,
                        "separation_arcmin": separation,
                        "admission_state": state,
                        "status": "matched",
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


def _check_hash(
    path: Path | None,
    expected: object,
    label: str,
    errors: list[str],
    store: EvidenceStore,
) -> None:
    if not isinstance(expected, str) or not SHA256_RE.fullmatch(expected):
        errors.append(f"{label} SHA-256 missing or malformed")
        return
    if path is None:
        errors.append(f"{label} bytes missing")
        return
    try:
        actual = store.sha256(path)
    except FileNotFoundError:
        errors.append(f"{label} bytes missing")
        return
    if actual != expected:
        errors.append(f"{label} SHA-256 mismatch")


def _read_canonical_rows(path: Path, store: EvidenceStore) -> list[dict]:
    stored = store.read(path)
    payload = gzip.decompress(stored) if path.suffix == ".gz" else stored
    rows = json.loads(payload)
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("canonical payload is not a list of records")
    return rows


def validate_manifest(manifest: dict, evidence_root: Path) -> list[str]:
    """Return all contract failures; an empty list is the only passing verdict."""
    errors: list[str] = []
    bundle_name = manifest.get("evidence_bundle_path")
    store = EvidenceStore(evidence_root, bundle_name if isinstance(bundle_name, str) else None)
    if isinstance(bundle_name, str):
        bundle_path = evidence_root / bundle_name
        expected_bundle_hash = manifest.get("evidence_bundle_sha256")
        if not bundle_path.is_file():
            errors.append("evidence bundle missing")
        elif not isinstance(expected_bundle_hash, str) or sha256_file(bundle_path) != expected_bundle_hash:
            errors.append("evidence bundle SHA-256 mismatch")
        member_names = store.member_names()
        if len(member_names) != manifest.get("evidence_bundle_member_count"):
            errors.append("evidence bundle member count mismatch")
        if len(member_names) != len(set(member_names)):
            errors.append("evidence bundle contains duplicate members")
        if any(Path(name).is_absolute() or ".." in Path(name).parts for name in member_names):
            errors.append("evidence bundle contains an unsafe member path")
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
            if (
                server_total is not None
                and isinstance(row_count, int)
                and isinstance(guard_count, int)
                and server_total != row_count + guard_count
                and service.role != "cluster_discovery"
            ):
                errors.append(f"{prefix}: server total does not equal admitted plus guard rows")

        raw_path = _safe_evidence_path(evidence_root, cell.get("raw_path"), f"{prefix}: raw", errors)
        canonical_path = _safe_evidence_path(
            evidence_root, cell.get("canonical_path"), f"{prefix}: canonical", errors
        )
        _check_hash(raw_path, cell.get("raw_sha256"), f"{prefix}: raw", errors, store)
        _check_hash(canonical_path, cell.get("canonical_sha256"), f"{prefix}: canonical", errors, store)
        if raw_path is not None and canonical_path is not None and raw_path == canonical_path:
            errors.append(f"{prefix}: raw and canonical evidence paths must differ")
        if canonical_path is not None:
            try:
                canonical_rows = _read_canonical_rows(canonical_path, store)
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                errors.append(f"{prefix}: canonical payload unreadable: {exc}")
                canonical_rows = []
            if isinstance(row_count, int) and len(canonical_rows) != row_count:
                errors.append(
                    f"{prefix}: canonical row count {len(canonical_rows)} does not equal manifest {row_count}"
                )
            previous_sort_key = None
            for row_index, row in enumerate(canonical_rows):
                label = f"{prefix}: canonical row {row_index}"
                if row.get("sightline") != key[0] or row.get("service") != key[1]:
                    errors.append(f"{label}: matrix identity mismatch")
                if row.get("release") != service.release:
                    errors.append(f"{label}: release mismatch")
                if row.get("status") != "matched":
                    errors.append(f"{label}: record status is not matched")
                if not str(row.get("source_id", "")).strip():
                    errors.append(f"{label}: stable source identifier missing")
                if not isinstance(row.get("native"), dict):
                    errors.append(f"{label}: native record missing")
                try:
                    row_ra = float(row["ra_deg"])
                    row_dec = float(row["dec_deg"])
                    recorded_separation = float(row["separation_arcmin"])
                    expected_separation = spherical_separation_arcmin(
                        SIGHTLINE_COORDS[key[0]][0],
                        SIGHTLINE_COORDS[key[0]][1],
                        row_ra,
                        row_dec,
                    )
                    if not math.isclose(recorded_separation, expected_separation, rel_tol=1e-12, abs_tol=1e-12):
                        errors.append(f"{label}: spherical separation mismatch")
                    if service.role == "cluster_discovery":
                        redshift = float(row["search_geometry_redshift"])
                        expected_projected = cluster_projected_separation_mpc(expected_separation, redshift)
                        if not math.isclose(
                            float(row["projected_separation_mpc"]),
                            expected_projected,
                            rel_tol=1e-12,
                            abs_tol=1e-12,
                        ):
                            errors.append(f"{label}: Planck18 projected separation mismatch")
                        if expected_projected > 5.0 or row.get("cosmology") != "Planck18":
                            errors.append(f"{label}: violates cluster search geometry")
                    else:
                        expected_state = admission_state(expected_separation)
                        if expected_state != "admitted" or row.get("admission_state") != "admitted":
                            errors.append(f"{label}: galaxy admission state mismatch")
                except (KeyError, TypeError, ValueError):
                    errors.append(f"{label}: invalid geometry fields")
                    continue
                sort_key = (recorded_separation, service.key, service.release, str(row["source_id"]))
                if previous_sort_key is not None and sort_key < previous_sort_key:
                    errors.append(f"{label}: canonical ordering is not deterministic")
                previous_sort_key = sort_key

        guard_path = _safe_evidence_path(
            evidence_root, cell.get("guard_evidence_path"), f"{prefix}: guard", errors
        )
        _check_hash(guard_path, cell.get("guard_evidence_sha256"), f"{prefix}: guard", errors, store)
        if guard_path is not None:
            try:
                guard_rows = _read_canonical_rows(guard_path, store)
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                errors.append(f"{prefix}: guard payload unreadable: {exc}")
                guard_rows = []
            if isinstance(guard_count, int) and len(guard_rows) != guard_count:
                errors.append(f"{prefix}: guard row count mismatch")
            for row_index, row in enumerate(guard_rows):
                label = f"{prefix}: guard row {row_index}"
                try:
                    separation = spherical_separation_arcmin(
                        SIGHTLINE_COORDS[key[0]][0], SIGHTLINE_COORDS[key[0]][1],
                        float(row["ra_deg"]), float(row["dec_deg"]),
                    )
                    if admission_state(separation) != "guard_ring" or row.get("admission_state") != "guard_ring":
                        errors.append(f"{label}: row is not in the guard ring")
                    if row.get("status") != "guard_only":
                        errors.append(f"{label}: status is not guard_only")
                except (KeyError, TypeError, ValueError):
                    errors.append(f"{label}: invalid geometry fields")

        if service.key in COVERAGE_CONFIG:
            if cell.get("coverage_checked") is not True:
                errors.append(f"{prefix}: required coverage not checked")
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
                store,
            )
        if isinstance(pagination, dict) and pagination.get("method") in {
            "count_verified_single_response",
            "complete_official_bulk_catalogue",
        }:
            if not isinstance(pagination.get("count_query"), str) or not pagination["count_query"].strip():
                errors.append(f"{prefix}: pagination count query missing")
            count_path = _safe_evidence_path(
                evidence_root,
                pagination.get("count_response_path"),
                f"{prefix}: count response",
                errors,
            )
            _check_hash(
                count_path,
                pagination.get("count_response_sha256"),
                f"{prefix}: count response",
                errors,
                store,
            )
    store.close()
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


def _adql_table(table: str) -> str:
    return f'"{table}"' if "/" in table else table


def _cone_predicate(
    ra_column: str,
    dec_column: str,
    ra: float,
    dec: float,
    radius_deg: float,
    *,
    include_frame: bool = True,
) -> str:
    frame = "'ICRS'," if include_frame else ""
    return (
        f"1=CONTAINS(POINT({frame}{ra_column},{dec_column}),"
        f"CIRCLE({frame}{ra:.12f},{dec:.12f},{radius_deg:.12f}))"
    )


def _datalab_cone_predicate(ra_column: str, dec_column: str, ra: float, dec: float, radius_deg: float) -> str:
    return (
        f"q3c_radial_query({ra_column},{dec_column},{ra:.12f},{dec:.12f},{radius_deg:.12f})='t'"
    )


def source_queries(service: Service, sightline: str) -> tuple[str, str]:
    """Return the exact row and count queries for one frozen cell."""
    ra, dec = SIGHTLINE_COORDS[sightline]
    radius_deg = GUARD_RADIUS_ARCMIN / 60.0
    config = QUERY_CONFIG[service.key]
    if service.transport == "bulk_full_catalog":
        source = (
            f"GET {service.endpoint}{service.bulk_object}; read every row from {service.table}; "
            f"for frozen ICRS center ({ra:.12f},{dec:.12f}), retain exactly rows with finite "
            "positive BEST_Z and theta * Planck18.angular_diameter_distance(BEST_Z) <= 5 proper Mpc"
        )
        return source, "complete official bulk catalogue; no server-side row limit"
    if service.transport == "simple_cone_search":
        params = urllib.parse.urlencode(
            {"CAT": service.table, "RA": f"{ra:.12f}", "DEC": f"{dec:.12f}", "SR": f"{radius_deg:.12f}", "VERB": 3}
        )
        return f"{service.endpoint}?{params}", "SCS response completeness from QUERY_STATUS/no OVERFLOW"
    if service.key == "sdss_dr19":
        nearby = f"dbo.fGetNearbySpecObjEq({ra:.12f},{dec:.12f},{GUARD_RADIUS_ARCMIN:.12f})"
        source = (
            "SELECT s.*, n.distance AS query_distance_arcmin FROM SpecObj AS s "
            f"JOIN {nearby} AS n ON s.specObjID=n.specObjID"
        )
        count = (
            "SELECT COUNT(*) AS row_total FROM SpecObj AS s "
            f"JOIN {nearby} AS n ON s.specObjID=n.specObjID"
        )
        return source, count
    if service.key == "legacy_dr10_photoz":
        joined = "ls_dr10.photo_z AS p JOIN ls_dr10.tractor AS t ON p.ls_id=t.ls_id"
        predicate = _datalab_cone_predicate("t.ra", "t.dec", ra, dec, radius_deg)
        source = (
            "SELECT p.*, t.ra AS match_ra, t.dec AS match_dec, t.type AS tractor_type, "
            "t.maskbits, t.fitbits, t.ref_cat, t.ref_id "
            f"FROM {joined} WHERE {predicate}"
        )
        return source, f"SELECT COUNT(*) AS row_total FROM {joined} WHERE {predicate}"
    table = _adql_table(service.table)
    if "datalab.noirlab.edu" in service.endpoint:
        predicate = _datalab_cone_predicate(config["ra"], config["dec"], ra, dec, radius_deg)
    else:
        predicate = _cone_predicate(config["ra"], config["dec"], ra, dec, radius_deg)
    return f"SELECT * FROM {table} WHERE {predicate}", f"SELECT COUNT(*) AS row_total FROM {table} WHERE {predicate}"


def coverage_queries(service: Service, sightline: str) -> tuple[str, str] | None:
    config = COVERAGE_CONFIG.get(service.key)
    if config is None:
        return None
    if config["kind"] == "erass1_german_half":
        return None
    ra, dec = SIGHTLINE_COORDS[sightline]
    table = config["table"]
    if config["kind"] == "region":
        predicate = (
            f"1=INTERSECTS(s_region,CIRCLE('ICRS',{ra:.12f},{dec:.12f},"
            f"{GUARD_RADIUS_ARCMIN / 60.0:.12f}))"
        )
    elif config["kind"] == "catalog":
        predicate = _datalab_cone_predicate("ra", "dec", ra, dec, GUARD_RADIUS_ARCMIN / 60.0)
    else:
        predicate = _cone_predicate("ra", "dec", ra, dec, float(config["radius_deg"]))
    return f"SELECT * FROM {table} WHERE {predicate}", f"SELECT COUNT(*) AS row_total FROM {table} WHERE {predicate}"


def _fetch(request: urllib.request.Request, timeout: float, attempts: int = 4) -> tuple[bytes, dict, int, str]:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            retrieved = utc_now()
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read()
                protocol_error = application_response_error(body)
                if protocol_error:
                    raise RuntimeError(protocol_error)
                return body, dict(response.headers.items()), response.status, retrieved
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            last_error = exc
            if isinstance(exc, urllib.error.HTTPError) and exc.code < 500 and exc.code != 429:
                break
            if attempt + 1 < attempts:
                time.sleep(2**attempt)
    raise RuntimeError(f"request failed after {attempts} attempts: {last_error}")


def _tap_request(service: Service, query: str) -> urllib.request.Request:
    output_format = "votable" if "heasarc.gsfc.nasa.gov" in service.endpoint else "csv"
    data = urllib.parse.urlencode(
        {
            "REQUEST": "doQuery",
            "LANG": "ADQL",
            "FORMAT": output_format,
            "MAXREC": 1_000_000,
            "QUERY": query,
        }
    ).encode()
    return urllib.request.Request(service.endpoint, data=data)


def _request_for_query(service: Service, query: str) -> urllib.request.Request:
    if service.transport == "tap":
        return _tap_request(service, query)
    if service.transport == "skyserver_sql":
        params = urllib.parse.urlencode({"cmd": query, "format": "csv"})
        return urllib.request.Request(f"{service.endpoint}?{params}")
    raise ValueError(f"query transport not supported for {service.key}: {service.transport}")


def _parse_erass1_cluster_archive(body: bytes, expected_member: str) -> tuple[list[str], list[dict]]:
    """Read the complete official cluster FITS member from its frozen tarball."""
    from astropy.table import Table

    with tarfile.open(fileobj=io.BytesIO(body), mode="r:gz") as archive:
        members = [member for member in archive.getmembers() if member.isfile()]
        matches = [member for member in members if Path(member.name).name == expected_member]
        if len(matches) != 1:
            raise ValueError(f"expected one {expected_member} member, found {len(matches)}")
        extracted = archive.extractfile(matches[0])
        if extracted is None:
            raise ValueError(f"could not read {expected_member}")
        fits_bytes = extracted.read()
    table = Table.read(io.BytesIO(fits_bytes), format="fits")
    columns = list(table.colnames)
    rows = [{column: _json_scalar(row[column]) for column in columns} for row in table]
    return columns, rows


def _json_scalar(value):
    try:
        import numpy as np

        if np.ma.is_masked(value):
            return None
        if isinstance(value, np.generic):
            value = value.item()
    except ImportError:
        pass
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def parse_response_rows(body: bytes) -> tuple[list[str], list[dict]]:
    """Parse CSV or VOTable while raw response bytes remain separately frozen."""
    if application_response_error(body):
        raise ValueError(application_response_error(body))
    if body.lstrip().startswith(b"<"):
        from astropy.io.votable import parse_single_table

        table = parse_single_table(io.BytesIO(body)).to_table(use_names_over_ids=True)
        columns = list(table.colnames)
        rows = [{column: _json_scalar(row[column]) for column in columns} for row in table]
        return columns, rows
    text_lines = body.decode("utf-8-sig").splitlines()
    data_lines = [line for line in text_lines if line.strip() and not line.startswith("#")]
    if not data_lines:
        return ["empty_response"], []
    reader = csv.DictReader(data_lines)
    columns = list(reader.fieldnames or [])
    return columns, [dict(row) for row in reader]


def _row_total(body: bytes) -> int:
    _, rows = parse_response_rows(body)
    if len(rows) != 1 or len(rows[0]) != 1:
        raise ValueError("count query did not return one scalar row")
    value = next(iter(rows[0].values()))
    return int(value)


def _archive_bytes(path: Path, response: bytes) -> tuple[str, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    stored = gzip.compress(response, mtime=0)
    path.write_bytes(stored)
    return sha256_bytes(stored), sha256_bytes(response)


def _write_canonical(path: Path, rows: list[dict]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    canonical = json.dumps(rows, sort_keys=True, separators=(",", ":"), allow_nan=False).encode() + b"\n"
    stored = gzip.compress(canonical, mtime=0)
    path.write_bytes(stored)
    return sha256_bytes(stored)


def _lookup(row: dict, column: str):
    if column in row:
        return row[column]
    lowered = {key.lower(): key for key in row}
    key = lowered.get(column.lower())
    return row.get(key) if key else None


def _normalize_rows(
    service: Service, sightline: str, native_rows: list[dict]
) -> tuple[list[dict], list[dict], list[str]]:
    config = QUERY_CONFIG[service.key]
    center_ra, center_dec = SIGHTLINE_COORDS[sightline]
    normalized = []
    guard_rows = []
    defects = []
    for index, native in enumerate(native_rows):
        try:
            row_ra = float(_lookup(native, config["ra"]))
            row_dec = float(_lookup(native, config["dec"]))
            if not (math.isfinite(row_ra) and math.isfinite(row_dec) and -90.0 <= row_dec <= 90.0):
                raise ValueError
        except (TypeError, ValueError):
            defects.append(f"row {index}: invalid coordinates")
            continue
        id_values = [_lookup(native, column) for column in config["ids"]]
        if any(value in {None, ""} for value in id_values):
            defects.append(f"row {index}: missing stable source identifier")
            continue
        separation = spherical_separation_arcmin(center_ra, center_dec, row_ra, row_dec)
        if service.role == "cluster_discovery":
            try:
                redshift = float(_lookup(native, config["redshift"]))
                state = cluster_admission_state(separation, redshift)
            except (TypeError, ValueError):
                defects.append(f"row {index}: cluster_search_geometry_unresolved")
                continue
            if state == "outside_query":
                continue
            projected_mpc = cluster_projected_separation_mpc(separation, redshift)
        else:
            state = admission_state(separation)
            if state == "outside_query":
                defects.append(f"row {index}: service returned row beyond guard cone ({separation})")
                continue
            projected_mpc = None
        record = {
                "sightline": sightline,
                "service": service.key,
                "release": service.release,
                "source_id": "/".join(str(value) for value in id_values),
                "ra_deg": row_ra,
                "dec_deg": row_dec,
                "separation_arcmin": separation,
                "admission_state": state,
                "status": "matched" if state == "admitted" else "guard_only",
                "native": native,
                **(
                    {
                        "search_geometry_redshift": redshift,
                        "search_geometry_redshift_source": (
                            f"{service.key}/{service.release}/{'/'.join(str(value) for value in id_values)}"
                        ),
                        "projected_separation_mpc": projected_mpc,
                        "cosmology": "Planck18",
                    }
                    if service.role == "cluster_discovery"
                    else {}
                ),
            }
        (guard_rows if state == "guard_ring" else normalized).append(record)
    normalized.sort(key=lambda row: (row["separation_arcmin"], service.key, service.release, row["source_id"]))
    guard_rows.sort(key=lambda row: (row["separation_arcmin"], service.key, service.release, row["source_id"]))
    return normalized, guard_rows, defects


def _fragment_valid(cell: dict, root: Path, service: Service) -> bool:
    if cell.get("status") not in TERMINAL_STATUSES:
        return False
    if cell.get("release") != service.release or cell.get("endpoint") != service.endpoint:
        return False
    if service.key in COVERAGE_CONFIG and cell.get("coverage_checked") is not True:
        return False
    for path_key, hash_key in (
        ("raw_path", "raw_sha256"),
        ("canonical_path", "canonical_sha256"),
        ("guard_evidence_path", "guard_evidence_sha256"),
    ):
        path = root / str(cell.get(path_key, ""))
        if not path.is_file() or sha256_file(path) != cell.get(hash_key):
            return False
    coverage_path = cell.get("coverage_evidence_path")
    if coverage_path:
        path = root / coverage_path
        if not path.is_file() or sha256_file(path) != cell.get("coverage_evidence_sha256"):
            return False
    return True


def _failure_cell(service: Service, sightline: str, root: Path, query: str, error: Exception) -> dict:
    payload = json.dumps({"error": str(error), "query": query}, sort_keys=True).encode() + b"\n"
    raw_path = Path("raw") / sightline / f"{service.key}.error.json.gz"
    raw_sha, response_sha = _archive_bytes(root / raw_path, payload)
    canonical_path = Path("canonical") / sightline / f"{service.key}.json.gz"
    canonical_sha = _write_canonical(root / canonical_path, [])
    guard_path = Path("guard") / sightline / f"{service.key}.json.gz"
    guard_sha = _write_canonical(root / guard_path, [])
    return {
        "sightline": sightline,
        "service": service.key,
        "release": service.release,
        "role": service.role,
        "endpoint": service.endpoint,
        "exact_query": query,
        "retrieved_at_utc": utc_now(),
        "coverage": "not_applicable",
        "status": "query_error",
        "raw_path": str(raw_path),
        "raw_sha256": raw_sha,
        "response_sha256": response_sha,
        "canonical_path": str(canonical_path),
        "canonical_sha256": canonical_sha,
        "native_columns": ["unavailable"],
        "row_count": 0,
        "guard_ring_count": 0,
        "guard_evidence_path": str(guard_path),
        "guard_evidence_sha256": guard_sha,
        "pagination": {"method": "failed", "complete": False, "overflow": False, "pages": 0, "row_limit": 1_000_000, "server_total": None},
        "error": str(error),
    }


def _outside_coverage_cell(
    service: Service,
    sightline: str,
    root: Path,
    source_query: str,
    coverage_exact_query: str,
    coverage_count: int,
    coverage_path: Path,
    coverage_sha: str,
) -> dict:
    skip = json.dumps(
        {"source_query_executed": False, "reason": "outside frozen coverage evidence"},
        sort_keys=True,
    ).encode() + b"\n"
    raw_path = Path("raw") / sightline / f"{service.key}.skipped.json.gz"
    raw_sha, response_sha = _archive_bytes(root / raw_path, skip)
    canonical_path = Path("canonical") / sightline / f"{service.key}.json.gz"
    canonical_sha = _write_canonical(root / canonical_path, [])
    guard_path = Path("guard") / sightline / f"{service.key}.json.gz"
    guard_sha = _write_canonical(root / guard_path, [])
    return {
        "sightline": sightline,
        "service": service.key,
        "release": service.release,
        "role": service.role,
        "endpoint": service.endpoint,
        "exact_query": source_query,
        "retrieved_at_utc": utc_now(),
        "coverage": "outside",
        "status": "outside_footprint",
        "raw_path": str(raw_path),
        "raw_sha256": raw_sha,
        "response_sha256": response_sha,
        "canonical_path": str(canonical_path),
        "canonical_sha256": canonical_sha,
        "native_columns": ["coverage_only"],
        "row_count": 0,
        "guard_ring_count": 0,
        "guard_evidence_path": str(guard_path),
        "guard_evidence_sha256": guard_sha,
        "pagination": {
            "method": "coverage_skip",
            "complete": True,
            "overflow": False,
            "pages": 1,
            "row_limit": 1_000_000,
            "server_total": 0,
        },
        "coverage_checked": True,
        "coverage_exact_query": coverage_exact_query,
        "coverage_row_count": coverage_count,
        "coverage_evidence_path": str(coverage_path),
        "coverage_evidence_sha256": coverage_sha,
    }


def acquire_cell(service: Service, sightline: str, root: Path, timeout: float, resume: bool) -> dict:
    fragment = root / "cells" / service.key / f"{sightline}.json"
    if resume and fragment.is_file():
        existing = json.loads(fragment.read_text(encoding="utf-8"))
        if _fragment_valid(existing, root, service):
            return existing
    source_query, count_query = source_queries(service, sightline)
    try:
        coverage = "not_applicable"
        coverage_checked = False
        coverage_path = None
        coverage_sha = None
        coverage_count = None
        coverage_exact_query = None
        coverage_config = COVERAGE_CONFIG.get(service.key)
        if coverage_config and coverage_config["kind"] == "erass1_german_half":
            from astropy.coordinates import SkyCoord
            import astropy.units as u

            center_ra, center_dec = SIGHTLINE_COORDS[sightline]
            galactic_l = float(SkyCoord(center_ra * u.deg, center_dec * u.deg).galactic.l.deg)
            inside = ERASS1_WESTERN_L_MIN_DEG < galactic_l < ERASS1_WESTERN_L_MAX_DEG
            coverage_record = {
                "authority": coverage_config["authority"],
                "authority_url": coverage_config["authority_url"],
                "center_ra_deg": center_ra,
                "center_dec_deg": center_dec,
                "galactic_longitude_deg": galactic_l,
                "rule": (
                    f"{ERASS1_WESTERN_L_MIN_DEG} < Galactic longitude < "
                    f"{ERASS1_WESTERN_L_MAX_DEG} degrees"
                ),
                "inside": inside,
            }
            coverage_bytes = json.dumps(coverage_record, sort_keys=True).encode() + b"\n"
            coverage_path = Path("coverage") / sightline / f"{service.key}.json.gz"
            coverage_sha, _ = _archive_bytes(root / coverage_path, coverage_bytes)
            coverage_checked = True
            coverage_count = int(inside)
            coverage = "inside" if inside else "outside"
            coverage_exact_query = coverage_record["rule"]
            if not inside:
                cell = _outside_coverage_cell(
                    service,
                    sightline,
                    root,
                    source_query,
                    coverage_exact_query,
                    coverage_count,
                    coverage_path,
                    coverage_sha,
                )
                fragment.parent.mkdir(parents=True, exist_ok=True)
                fragment.write_text(json.dumps(cell, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                return cell
        coverage_pair = coverage_queries(service, sightline)
        if coverage_pair:
            coverage_query, coverage_count_query = coverage_pair
            coverage_exact_query = coverage_query
            count_body, _, _, _ = _fetch(_tap_request(service, coverage_count_query), timeout)
            coverage_count = _row_total(count_body)
            coverage_body, _, _, _ = _fetch(_tap_request(service, coverage_query), timeout)
            _, coverage_rows = parse_response_rows(coverage_body)
            if len(coverage_rows) != coverage_count:
                raise RuntimeError(
                    f"coverage count mismatch: server {coverage_count}, response {len(coverage_rows)}"
                )
            coverage_path = Path("coverage") / sightline / f"{service.key}.votable.gz"
            coverage_sha, _ = _archive_bytes(root / coverage_path, coverage_body)
            coverage_checked = True
            coverage = "inside" if coverage_count else "outside"
            if not coverage_count:
                cell = _outside_coverage_cell(
                    service,
                    sightline,
                    root,
                    source_query,
                    coverage_exact_query,
                    coverage_count,
                    coverage_path,
                    coverage_sha,
                )
                fragment.parent.mkdir(parents=True, exist_ok=True)
                fragment.write_text(json.dumps(cell, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                return cell

        if service.transport == "simple_cone_search":
            source_body, _, _, retrieved = _fetch(urllib.request.Request(source_query), timeout)
            native_columns, native_rows = parse_response_rows(source_body)
            server_total = len(native_rows)
            count_body = json.dumps(
                {"protocol": "SCS", "query_status": "complete", "row_total": server_total},
                sort_keys=True,
            ).encode() + b"\n"
        elif service.transport == "bulk_full_catalog":
            request = urllib.request.Request(service.endpoint + service.bulk_object)
            source_body, _, _, retrieved = _fetch(request, timeout)
            native_columns, native_rows = _parse_erass1_cluster_archive(source_body, service.table)
            server_total = len(native_rows)
            count_body = json.dumps(
                {
                    "protocol": "official_complete_bulk_catalogue",
                    "row_total": server_total,
                    "source_url": service.endpoint + service.bulk_object,
                },
                sort_keys=True,
            ).encode() + b"\n"
        else:
            count_body, _, _, _ = _fetch(_request_for_query(service, count_query), timeout)
            server_total = _row_total(count_body)
            source_body, _, _, retrieved = _fetch(_request_for_query(service, source_query), timeout)
            native_columns, native_rows = parse_response_rows(source_body)
        count_path = Path("counts") / sightline / f"{service.key}.response.gz"
        count_sha, count_response_sha = _archive_bytes(root / count_path, count_body)
        if b'VALUE="OVERFLOW"' in source_body.upper().replace(b"'", b'"'):
            raise RuntimeError("service response declared overflow")
        raw_path = Path("raw") / sightline / f"{service.key}.response.gz"
        raw_sha, response_sha = _archive_bytes(root / raw_path, source_body)
        normalized, guard_rows, defects = _normalize_rows(service, sightline, native_rows)
        canonical_path = Path("canonical") / sightline / f"{service.key}.json.gz"
        canonical_sha = _write_canonical(root / canonical_path, normalized)
        guard_path = Path("guard") / sightline / f"{service.key}.json.gz"
        guard_sha = _write_canonical(root / guard_path, guard_rows)
        count_mismatch = server_total != len(native_rows)
        status = "query_error" if defects or count_mismatch else ("matched" if normalized else "unmatched")
        cell = {
            "sightline": sightline,
            "service": service.key,
            "release": service.release,
            "role": service.role,
            "endpoint": service.endpoint,
            "exact_query": source_query,
            "retrieved_at_utc": retrieved,
            "coverage": coverage,
            "status": status,
            "raw_path": str(raw_path),
            "raw_sha256": raw_sha,
            "response_sha256": response_sha,
            "canonical_path": str(canonical_path),
            "canonical_sha256": canonical_sha,
            "native_columns": native_columns or ["empty_response"],
            "row_count": len(normalized),
            "guard_ring_count": len(guard_rows),
            "guard_evidence_path": str(guard_path),
            "guard_evidence_sha256": guard_sha,
            "pagination": {
                "method": (
                    "complete_official_bulk_catalogue"
                    if service.transport == "bulk_full_catalog"
                    else "count_verified_single_response"
                ),
                "complete": not count_mismatch,
                "overflow": count_mismatch,
                "pages": 1,
                "row_limit": 1_000_000,
                "server_total": server_total,
                "count_query": count_query,
                "count_response_path": str(count_path),
                "count_response_sha256": count_sha,
                "count_uncompressed_sha256": count_response_sha,
            },
            "defects": defects,
        }
        if coverage_pair:
            cell.update(
                coverage_checked=coverage_checked,
                coverage_exact_query=coverage_exact_query,
                coverage_row_count=coverage_count,
                coverage_evidence_path=str(coverage_path),
                coverage_evidence_sha256=coverage_sha,
            )
        fragment.parent.mkdir(parents=True, exist_ok=True)
        fragment.write_text(json.dumps(cell, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return cell
    except Exception as exc:
        cell = _failure_cell(service, sightline, root, source_query, exc)
        fragment.parent.mkdir(parents=True, exist_ok=True)
        fragment.write_text(json.dumps(cell, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return cell


def _ps1_cells(root: Path) -> list[dict]:
    service = next(service for service in SERVICES if service.key == "ps1_strm_v1")
    extraction = json.loads((root / "ps1-strm-extract.json").read_text(encoding="utf-8"))
    canonical_path = Path(extraction["canonical_path"])
    if not (root / canonical_path).is_file():
        canonical_path = canonical_path.resolve().relative_to(root.resolve())
    store = EvidenceStore(root)
    try:
        canonical_bytes = store.read(root / canonical_path)
    finally:
        store.close()
    if sha256_bytes(canonical_bytes) != extraction["canonical_sha256"]:
        raise RuntimeError("PS1 canonical snapshot hash mismatch")
    rows = json.loads(gzip.decompress(canonical_bytes))
    head_path = Path("raw") / "ps1_strm_v1.bin"
    head_sha = sha256_file(root / head_path)
    cells = []
    for sightline in SIGHTLINE_NAMES:
        all_selected = [row for row in rows if row["sightline"] == sightline]
        selected = [row for row in all_selected if row["admission_state"] == "admitted"]
        guard_rows = [row for row in all_selected if row["admission_state"] == "guard_ring"]
        for row in selected:
            row.setdefault("release", service.release)
            row.setdefault("status", "matched")
        for row in guard_rows:
            row.setdefault("release", service.release)
            row["status"] = "guard_only"
        sightline_canonical_path = Path("canonical") / sightline / "ps1_strm_v1.json.gz"
        sightline_canonical_sha = _write_canonical(root / sightline_canonical_path, selected)
        guard_path = Path("guard") / sightline / "ps1_strm_v1.json.gz"
        guard_sha = _write_canonical(root / guard_path, guard_rows)
        cells.append(
            {
                "sightline": sightline,
                "service": service.key,
                "release": service.release,
                "role": service.role,
                "endpoint": service.endpoint,
                "exact_query": extraction["exact_query"],
                "retrieved_at_utc": extraction["completed_at_utc"],
                "coverage": "not_applicable",
                "status": "matched" if selected else "unmatched",
                "raw_path": str(head_path),
                "raw_sha256": head_sha,
                "response_sha256": extraction["source_sha256"],
                "canonical_path": str(sightline_canonical_path),
                "canonical_sha256": sightline_canonical_sha,
                "native_columns": extraction["published_native_columns"],
                "row_count": len(selected),
                "guard_ring_count": len(guard_rows),
                "guard_evidence_path": str(guard_path),
                "guard_evidence_sha256": guard_sha,
                "pagination": {
                    "method": "complete_official_declination_shard_stream",
                    "complete": True,
                    "overflow": False,
                    "pages": 1,
                    "row_limit": None,
                    "server_total": len(selected) + len(guard_rows),
                },
                "source_size_bytes": extraction["source_size_bytes"],
                "source_sha256": extraction["source_sha256"],
                "source_rows_scanned": extraction["source_rows_scanned"],
            }
        )
    return cells


def acquire_corpus(output_dir: Path, timeout: float, workers: int, resume: bool) -> tuple[dict, list[str]]:
    services = [service for service in SERVICES if service.key != "ps1_strm_v1"]
    futures = {}
    cells = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for service in services:
            for sightline in SIGHTLINE_NAMES:
                future = executor.submit(acquire_cell, service, sightline, output_dir, timeout, resume)
                futures[future] = (service.key, sightline)
        for future in as_completed(futures):
            service_key, sightline = futures[future]
            cell = future.result()
            cells.append(cell)
            print(f"{service_key}/{sightline}: {cell['status']} ({cell['row_count']} rows)", flush=True)
    cells.extend(_ps1_cells(output_dir))
    cells.sort(key=lambda cell: (cell["sightline"], cell["service"]))
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "input_path": "pipeline/galaxies/foreground/data/frozen_census/bursts.csv",
        "input_sha256": FROZEN_INPUT_SHA256,
        "generated_at_utc": utc_now(),
        "cells": cells,
    }
    manifest_path = output_dir / "corpus-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest, validate_manifest(manifest, output_dir)


def pack_evidence(output_dir: Path) -> dict:
    """Pack loose byte evidence deterministically without changing member bytes."""
    member_paths = []
    for directory in ("raw", "canonical", "guard", "counts", "coverage"):
        root = output_dir / directory
        if root.is_dir():
            member_paths.extend(path for path in root.rglob("*") if path.is_file())
    member_paths.sort(key=lambda path: path.relative_to(output_dir).as_posix())
    if not member_paths:
        raise ValueError("no loose evidence files found to pack")

    bundle_path = output_dir / "evidence-bundle.tar.gz"
    temporary = output_dir / "evidence-bundle.tar.gz.tmp"
    with temporary.open("wb") as raw_handle:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw_handle, mtime=0) as gzip_handle:
            with tarfile.open(fileobj=gzip_handle, mode="w", format=tarfile.PAX_FORMAT) as archive:
                for path in member_paths:
                    info = archive.gettarinfo(
                        str(path), arcname=path.relative_to(output_dir).as_posix()
                    )
                    info.uid = 0
                    info.gid = 0
                    info.uname = ""
                    info.gname = ""
                    info.mtime = 0
                    with path.open("rb") as handle:
                        archive.addfile(info, handle)
    temporary.replace(bundle_path)

    manifest_path = output_dir / "corpus-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["evidence_bundle_path"] = bundle_path.name
    manifest["evidence_bundle_sha256"] = sha256_file(bundle_path)
    manifest["evidence_bundle_member_count"] = len(member_paths)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "bundle_path": str(bundle_path),
        "bundle_sha256": manifest["evidence_bundle_sha256"],
        "member_count": len(member_paths),
    }


def repair_admission_evidence(output_dir: Path) -> dict:
    """Separate legacy guard rows from admitted canonical rows in-place."""
    manifest_path = output_dir / "corpus-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    store = EvidenceStore(output_dir, manifest.get("evidence_bundle_path"))
    admitted_total = 0
    guard_total = 0
    try:
        for cell in manifest["cells"]:
            canonical_path = Path(cell["canonical_path"])
            rows = _read_canonical_rows(output_dir / canonical_path, store)
            if cell["role"] == "cluster_discovery":
                admitted = rows
                guard_rows = []
            else:
                admitted = [row for row in rows if row.get("admission_state") == "admitted"]
                guard_rows = [row for row in rows if row.get("admission_state") == "guard_ring"]
            for row in admitted:
                row["status"] = "matched"
            for row in guard_rows:
                row["status"] = "guard_only"
            cell["canonical_sha256"] = _write_canonical(output_dir / canonical_path, admitted)
            guard_path = Path("guard") / cell["sightline"] / f"{cell['service']}.json.gz"
            cell["guard_evidence_path"] = str(guard_path)
            cell["guard_evidence_sha256"] = _write_canonical(output_dir / guard_path, guard_rows)
            cell["row_count"] = len(admitted)
            cell["guard_ring_count"] = len(guard_rows)
            if cell["status"] in {"matched", "unmatched"}:
                cell["status"] = "matched" if admitted else "unmatched"
            admitted_total += len(admitted)
            guard_total += len(guard_rows)
    finally:
        store.close()
    for key in ("evidence_bundle_path", "evidence_bundle_sha256", "evidence_bundle_member_count"):
        manifest.pop(key, None)
    manifest["admission_contract"] = "canonical rows use exact inclusive separation <=15.0 arcmin"
    manifest["guard_contract"] = "15.0 < separation <=15.1 arcmin; evidence only, never matched"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"admitted_rows": admitted_total, "guard_rows": guard_total}


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
    acquire = subparsers.add_parser("acquire", help="freeze all 126 service-sightline cells")
    acquire.add_argument("--output-dir", type=Path, required=True)
    acquire.add_argument("--timeout", type=float, default=120.0)
    acquire.add_argument("--workers", type=int, default=4)
    acquire.add_argument("--no-resume", action="store_true")
    pack = subparsers.add_parser("pack", help="pack loose evidence into one deterministic bundle")
    pack.add_argument("--output-dir", type=Path, required=True)
    repair_admission = subparsers.add_parser(
        "repair-admission", help="move legacy 15.0-15.1 arcmin rows into guard evidence"
    )
    repair_admission.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "validate":
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        root = args.evidence_root or args.manifest.parent
        errors = validate_manifest(manifest, root)
        if errors:
            for error in errors:
                print(f"FAIL: {error}", file=sys.stderr)
            return 1
        print(f"PASS: all {len(manifest['cells'])} service-sightline cells satisfy the frozen corpus contract")
        return 0

    if args.command == "preflight":
        manifest = run_preflight(args.output_dir, args.timeout)
        reachable = sum(entry["status"] == "reachable" for entry in manifest["entries"])
        blocked = len(manifest["entries"]) - reachable
        print(f"Preflight: {reachable} anonymous query routes reachable; {blocked} unresolved or non-cone routes")
        return 1 if blocked else 0

    if args.command == "acquire":
        manifest, errors = acquire_corpus(args.output_dir, args.timeout, args.workers, not args.no_resume)
        if errors:
            print(
                f"FAIL: {len(errors)} corpus-contract error(s) across {len(manifest['cells'])} cells",
                file=sys.stderr,
            )
            for error in errors:
                print(f"FAIL: {error}", file=sys.stderr)
            return 1
        print(f"PASS: all {len(manifest['cells'])} cells satisfy the frozen corpus contract")
        return 0

    if args.command == "pack":
        result = pack_evidence(args.output_dir)
        print(
            f"Packed {result['member_count']} evidence files; SHA-256 {result['bundle_sha256']}"
        )
        return 0

    if args.command == "repair-admission":
        result = repair_admission_evidence(args.output_dir)
        print(f"Admitted {result['admitted_rows']} rows; isolated {result['guard_rows']} guard rows")
        return 0

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
