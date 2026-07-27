#!/usr/bin/env python3
"""Independently replay the frozen anonymous and protected catalog corpora.

This module deliberately does not import either producer. Astropy and NumPy are
used only to replay frozen native FITS/WCS coverage evidence.
It verifies frozen bytes, exact-cone admission, terminal cell states, protected
WISE identity ambiguity, and the fail-closed CADC/CFIS receipt.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import os
import re
import subprocess
import tarfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ANON = Path("docs/rse/specs/evidence/nine-sightline-anonymous-catalog-corpus-2026-07-22")
PROTECTED = Path("docs/rse/specs/evidence/protected-nine-sightline-2026-07-22")
CADC = Path("docs/rse/specs/evidence/cadc-cfis-access-2026-07-22")
EXPECTED_PIPELINE_COMMIT = "2463289015a8ffe0d6934e1c2206c9b49eeda345"
EXPECTED_REGISTRY_INPUT_SHA256 = {
    "intervening_census_registry.csv": "96bfd32302b00df943ba998ba3bf6557f3d8c06d882079cad1a5c9846d47d06a",
    "candidate_redshift_provenance.csv": "0a2ba35f3dd7dfdcc855d4d589e062c08e5788e135970802cb7b7b798c47afe7",
    "census_duplicates.csv": "336e4023dbf046762477c724e57365c29a3ecabb982f6978e635fb0d05d47e45",
    "ps1_strm_resolution.csv": "18947acafc02b9781c4ac9612b9570d02eedd46c0115c9f73b5f3d79ec2c354e",
}
EXPECTED_ANONYMOUS_MANIFEST_SHA256 = "14321fb328e372b8df0537d9a445dec2ab1376c4b258dabaf92116152eb023a5"
EXPECTED_ANONYMOUS_BUNDLE_SHA256 = "fed672e29c1d84ffd09f93de2487a1337fb722c02bd5dc718f7f97c1e593d32d"
EXPECTED_PROTECTED_MANIFEST_SHA256 = "43af38cc4e996b7890ea0858ef5a760c124e877825dc8866bc4221d3d02b347f"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _finite(value: str | None) -> bool:
    if value is None or not value.strip():
        return False
    try:
        return math.isfinite(float(value))
    except ValueError:
        return False


def _replay_verdict(
    row: dict[str, str], provenance: dict[str, str],
    strm_by_obj: dict[str, dict[str, str]],
) -> str:
    if not _finite(row["best_z"]):
        return "inconclusive"
    if row["obj"] in strm_by_obj:
        strm = strm_by_obj[row["obj"]]
        if strm["strm_class"] != "GALAXY" or strm["strm_extrapolated"] == "1.0":
            return "inconclusive"
    redshift = float(row["best_z"])
    host = float(row["host_z_spec"])
    secure = provenance["measurement_kind"] in ("spectroscopic", "catalog_cluster")
    if secure:
        return "confirmed" if redshift < host else "refuted"
    if not _finite(row["best_z_err"]):
        return "inconclusive"
    error = float(row["best_z_err"])
    if redshift + error < host:
        return "confirmed"
    if redshift - error > host:
        return "refuted"
    return "inconclusive"


def replay_registry(pipeline_dir: Path, errors: list[str]) -> dict[str, Any]:
    data = pipeline_dir / "galaxies/foreground/data"
    registry_path = data / "intervening_census_registry.csv"
    provenance_path = data / "candidate_redshift_provenance.csv"
    duplicate_path = data / "census_masses/census_duplicates.csv"
    strm_path = data / "frozen_census/ps1_strm_resolution.csv"
    paths = (registry_path, provenance_path, duplicate_path, strm_path)
    for path in paths:
        if not path.is_file():
            errors.append(f"registry replay input missing: {path}")
            return {"available": False}
    registry_all = _read_csv(registry_path)
    registry = [row for row in registry_all if _finite(row["host_z_spec"])]
    registry_names = {row["nickname"].casefold() for row in registry}
    strm = {row["obj"]: row for row in _read_csv(strm_path)}
    provenance = _read_csv(provenance_path)
    provenance_by_key = {
        (row["nickname"], row["type"], row["obj"]): row for row in provenance
    }
    verdict_mismatches: list[str] = []
    budget_mismatches: list[str] = []
    by_identity = {(row["nickname"], row["obj"]): row for row in registry}
    for row in registry:
        key = (row["nickname"], row["type"], row["obj"])
        source = provenance_by_key.get(key)
        if source is None:
            errors.append(f"missing candidate provenance: {'/'.join(key)}")
            continue
        verdict = _replay_verdict(row, source, strm)
        if verdict != row["final_verdict"]:
            verdict_mismatches.append(f"{row['nickname']}/{row['type']}/{row['obj']}")
        budget = verdict == "confirmed" and (
            row["type"] == "halo" or (_finite(row["b_over_r500"]) and float(row["b_over_r500"]) <= 1)
        )
        if budget != (row["budget_eligible"].casefold() == "true"):
            budget_mismatches.append(f"{row['nickname']}/{row['type']}/{row['obj']}")
    duplicates = []
    for item in _read_csv(duplicate_path):
        left = by_identity[(item["nickname"], item["duplicate_obj"])]
        right = by_identity[(item["nickname"], item["canonical_obj"])]
        separation = angular_separation_arcmin(
            float(left["ra_deg"]), float(left["dec_deg"]),
            float(right["ra_deg"]), float(right["dec_deg"]),
        ) * 60
        matches = round(separation, 2) == float(item["sep_arcsec"])
        if not matches:
            errors.append(f"duplicate separation mismatch: {item['nickname']}/{item['duplicate_obj']}")
        duplicates.append({"nickname": item["nickname"], "separation_arcsec": separation, "matches": matches})
    registry_keys = {(row["nickname"], row["type"], row["obj"]) for row in registry_all}
    provenance_keys = {(row["nickname"], row["type"], row["obj"]) for row in provenance}
    if provenance_keys != registry_keys:
        errors.append("candidate provenance identities do not match all registry rows")
    if verdict_mismatches:
        errors.append(f"stored verdict mismatches: {verdict_mismatches}")
    if budget_mismatches:
        errors.append(f"stored budget mismatches: {budget_mismatches}")
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=pipeline_dir, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    input_sha256 = {path.name: sha256_file(path) for path in paths}
    if head != EXPECTED_PIPELINE_COMMIT:
        errors.append(f"pipeline commit mismatch: expected {EXPECTED_PIPELINE_COMMIT}, got {head}")
    for name, expected in EXPECTED_REGISTRY_INPUT_SHA256.items():
        if input_sha256[name] != expected:
            errors.append(
                f"registry replay input SHA-256 mismatch: {name}: "
                f"expected {expected}, got {input_sha256[name]}"
            )
    return {
        "available": True,
        "pipeline_commit": head,
        "input_sha256": input_sha256,
        "rows": len(registry_all),
        "finite_host_rows": len(registry),
        "sightlines": sorted(registry_names),
        "provenance_rows": len(provenance),
        "verdict_mismatches": verdict_mismatches,
        "budget_mismatches": budget_mismatches,
        "duplicate_checks": duplicates,
    }


def angular_separation_arcmin(ra1: float, dec1: float, ra2: float, dec2: float) -> float:
    dec1r, dec2r = math.radians(dec1), math.radians(dec2)
    dra = math.radians(ra2 - ra1)
    ddec = dec2r - dec1r
    value = math.sin(ddec / 2) ** 2 + math.cos(dec1r) * math.cos(dec2r) * math.sin(dra / 2) ** 2
    return math.degrees(2 * math.asin(min(1.0, math.sqrt(value)))) * 60


def check_separation(row: dict[str, Any], label: str, *, admitted: bool, errors: list[str]) -> None:
    separation = float(row["separation_arcmin"])
    if admitted:
        if row.get("admission_state") != "admitted":
            errors.append(f"{label}: canonical row is not marked admitted")
        if separation > 15.0:
            errors.append(f"{label}: admitted separation exceeds 15 arcmin")
    elif not (15.0 < separation <= 15.1):
        errors.append(f"{label}: guard separation is not in (15.0, 15.1] arcmin")


def check_anonymous_geometry(
    row: dict[str, Any], label: str, *, center: tuple[float, float],
    admitted: bool, errors: list[str]
) -> None:
    replayed = angular_separation_arcmin(
        center[0], center[1], float(row["ra_deg"]), float(row["dec_deg"])
    )
    if not math.isclose(replayed, float(row["separation_arcmin"]), rel_tol=0, abs_tol=1e-9):
        errors.append(f"{label}: stored separation disagrees with coordinates")
        return
    independent = dict(row)
    independent["separation_arcmin"] = replayed
    check_separation(independent, label, admitted=admitted, errors=errors)


def _center_from_query(query: str) -> tuple[float, float] | None:
    patterns = (
        r"CIRCLE\('ICRS',\s*([0-9.+-]+),\s*([0-9.+-]+),",
        r"q3c_radial_query\([^,]+,[^,]+,\s*([0-9.+-]+),\s*([0-9.+-]+),",
        r"[?&]RA=([0-9.+-]+)&DEC=([0-9.+-]+)",
        r"fGetNearbySpecObjEq\(\s*([0-9.+-]+),\s*([0-9.+-]+),",
        r"frozen ICRS center \(([0-9.+-]+),\s*([0-9.+-]+)\)",
    )
    for pattern in patterns:
        match = re.search(pattern, query)
        if match:
            return float(match.group(1)), float(match.group(2))
    return None


def check_protected_rectangle(
    *, sql: str, bounds: dict[str, float], center: tuple[float, float],
    label: str, errors: list[str]
) -> None:
    match = re.search(
        r"raMean\s*>=\s*([0-9.+-]+).*?raMean\s*<=\s*([0-9.+-]+).*?"
        r"decMean\s*>=\s*([0-9.+-]+).*?decMean\s*<=\s*([0-9.+-]+)",
        sql, re.DOTALL,
    )
    expected = (bounds["ra_min"], bounds["ra_max"], bounds["dec_min"], bounds["dec_max"])
    if match is None or any(
        not math.isclose(float(value), target, rel_tol=0, abs_tol=1e-12)
        for value, target in zip(match.groups(), expected)
    ):
        errors.append(f"{label}: SQL bounds disagree with manifest bounding box")
        return
    # Dense boundary replay independently checks rectangle containment.
    ra0, dec0 = map(math.radians, center)
    radius = math.radians(15.0 / 60.0)
    for bearing_deg in range(360):
        bearing = math.radians(bearing_deg)
        dec = math.asin(
            math.sin(dec0) * math.cos(radius)
            + math.cos(dec0) * math.sin(radius) * math.cos(bearing)
        )
        ra = ra0 + math.atan2(
            math.sin(bearing) * math.sin(radius) * math.cos(dec0),
            math.cos(radius) - math.sin(dec0) * math.sin(dec),
        )
        ra_deg, dec_deg = math.degrees(ra) % 360, math.degrees(dec)
        if not (bounds["ra_min"] <= ra_deg <= bounds["ra_max"] and bounds["dec_min"] <= dec_deg <= bounds["dec_max"]):
            errors.append(f"{label}: manifest rectangle does not contain the 15-arcminute cone")
            return


def protected_row_separation(
    row: dict[str, Any], *, center: tuple[float, float], label: str, errors: list[str]
) -> float:
    row_center = (float(row["center_ra_deg"]), float(row["center_dec_deg"]))
    if any(
        not math.isclose(value, expected, rel_tol=0, abs_tol=1e-12)
        for value, expected in zip(row_center, center)
    ):
        errors.append(f"{label}: CSV center disagrees with manifest center")
    return angular_separation_arcmin(
        center[0], center[1], float(row["raMean"]), float(row["decMean"])
    )


def shared_wise_groups(rows: list[dict[str, Any]]) -> dict[str, tuple[str, ...]]:
    identities: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        if float(row["separation_arcmin"]) <= 15.0:
            identities[str(row["cntr"])].add(str(row["objID"]))
    return {
        key: tuple(sorted(values))
        for key, values in identities.items()
        if len(values) > 1
    }


def _json_member(archive: tarfile.TarFile, path: str) -> tuple[bytes, list[dict[str, Any]]]:
    handle = archive.extractfile(path)
    if handle is None:
        raise KeyError(path)
    compressed = handle.read()
    payload = json.loads(gzip.decompress(compressed))
    if not isinstance(payload, list):
        raise TypeError(f"{path}: expected a JSON list")
    return compressed, payload


def _tar_bodies(payload: bytes) -> dict[str, bytes]:
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:") as archive:
        members = [member for member in archive.getmembers() if member.isfile()]
        names = [member.name for member in members]
        if len(names) != len(set(names)) or any(Path(name).is_absolute() or ".." in Path(name).parts for name in names):
            raise ValueError("unsafe or duplicate nested evidence member")
        return {member.name: archive.extractfile(member).read() for member in members}


def _votable_rows(payload: bytes) -> list[dict[str, str]]:
    root = ET.fromstring(payload)
    statuses = [
        element.attrib.get("value", "").upper()
        for element in root.iter()
        if element.tag.endswith("INFO") and element.attrib.get("name", "").upper() == "QUERY_STATUS"
    ]
    if not statuses or any(status != "OK" for status in statuses):
        raise ValueError(f"VOTable query status is not complete OK: {statuses}")
    fields = [element.attrib.get("name", "") for element in root.iter() if element.tag.endswith("FIELD")]
    rows = []
    for tr in (element for element in root.iter() if element.tag.endswith("TR")):
        values = [(td.text or "") for td in tr if td.tag.endswith("TD")]
        rows.append(dict(zip(fields, values)))
    return rows


def _unit_vector(ra_deg: float, dec_deg: float) -> tuple[float, float, float]:
    ra, dec = math.radians(ra_deg), math.radians(dec_deg)
    return math.cos(dec) * math.cos(ra), math.cos(dec) * math.sin(ra), math.sin(dec)


def _dot(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _norm(a) -> float:
    return math.sqrt(_dot(a, a))


def _angular(a, b) -> float:
    return math.atan2(_norm(_cross(a, b)), max(-1.0, min(1.0, _dot(a, b))))


def _point_in_polygon(point, vertices) -> bool:
    tangents = []
    for vertex in vertices:
        projected = tuple(vertex[i] - _dot(point, vertex) * point[i] for i in range(3))
        length = _norm(projected)
        if length < 1e-15:
            return True
        tangents.append(tuple(value / length for value in projected))
    winding = sum(
        math.atan2(_dot(point, _cross(first, second)), _dot(first, second))
        for first, second in zip(tangents, tangents[1:] + tangents[:1])
    )
    return abs(winding) > math.pi


def _point_arc_distance(point, first, second) -> float:
    arc = _angular(first, second)
    best = min(_angular(point, first), _angular(point, second))
    normal = _cross(first, second)
    length = _norm(normal)
    if length < 1e-15:
        return best
    normal = tuple(value / length for value in normal)
    projected = tuple(point[i] - _dot(point, normal) * normal[i] for i in range(3))
    length = _norm(projected)
    if length < 1e-15:
        return best
    candidate = tuple(value / length for value in projected)
    for candidate in (candidate, tuple(-value for value in candidate)):
        if abs(_angular(first, candidate) + _angular(candidate, second) - arc) < 1e-10:
            best = min(best, _angular(point, candidate))
    return best


def _stcs_intersects(stcs: str, center: tuple[float, float]) -> bool:
    point = _unit_vector(*center)
    radius = math.radians(15.1 / 60)
    for chunk in re.split(r"\bPOLYGON\b", stcs, flags=re.IGNORECASE)[1:]:
        numbers = [float(value) for value in re.findall(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?", chunk)]
        vertices = [_unit_vector(numbers[index], numbers[index + 1]) for index in range(0, len(numbers), 2)]
        if _point_in_polygon(point, vertices):
            return True
        if any(_angular(point, vertex) <= radius for vertex in vertices):
            return True
        if any(_point_arc_distance(point, first, second) <= radius for first, second in zip(vertices, vertices[1:] + vertices[:1])):
            return True
    return False


def _positive_fits_pixels(
    bodies: dict[str, bytes], center: tuple[float, float], prefix: str,
    compressed: bool, radius_arcmin: float,
) -> int:
    import numpy as np
    import astropy.units as u
    from astropy.coordinates import SkyCoord
    from astropy.io import fits
    from astropy.wcs import WCS

    target = SkyCoord(center[0] * u.deg, center[1] * u.deg)
    count = 0
    for name, body in bodies.items():
        if not name.startswith(prefix):
            continue
        content = gzip.decompress(body) if compressed else body
        with fits.open(io.BytesIO(content), memmap=False) as hdus:
            hdu = next(item for item in hdus if getattr(item, "data", None) is not None)
            yy, xx = np.nonzero(np.asarray(hdu.data) > 0)
            if len(xx):
                sky = WCS(hdu.header).pixel_to_world(xx, yy)
                count += int(np.count_nonzero(sky.separation(target) <= radius_arcmin * u.arcmin))
    return count


def replay_coverage_evidence(method: str, compressed: bytes, center: tuple[float, float]) -> tuple[bool, int]:
    payload = gzip.decompress(compressed)
    if method == "legacy_dr9_official_sia_nexp_positive_pixels":
        bodies = _tar_bodies(payload)
        metadata = json.loads(bodies["metadata.json"])
        if metadata.get("format") != "faber2026.legacy-dr9-sia-nexp-replay.v1":
            raise ValueError("legacy coverage format mismatch")
        count = _positive_fits_pixels(bodies, center, "nexp/", compressed=False, radius_arcmin=15.1)
        return count > 0, count
    if method == "swift_lsxps_native_wcs_positive_pixels":
        bodies = _tar_bodies(payload)
        metadata = json.loads(bodies["metadata.json"])
        if metadata.get("format") != "faber2026.swift-lsxps-exposure-replay.v1":
            raise ValueError("Swift coverage format mismatch")
        response = json.loads(bodies["query.response.json"])
        if response.get("NumRows") != len(response.get("Results", [])):
            raise ValueError("Swift coverage response incomplete")
        count = _positive_fits_pixels(
            bodies, center, "maps/", compressed=True,
            radius_arcmin=float(metadata["coverage_radius_arcmin"]),
        )
        return count > 0, count
    if method == "tap_polygon":
        rows = _votable_rows(payload)
        return bool(rows), len(rows)
    if method == "stcs_polygon":
        count_marker = b"FABER2026-COUNT-BYTES\n"
        rows_marker = b"FABER2026-ROWS-BYTES\n"
        if not payload.startswith(count_marker):
            raise ValueError("Chandra count framing missing")
        offset = len(count_marker)
        count_length = int.from_bytes(payload[offset:offset + 8], "big")
        count_body = payload[offset + 8:offset + 8 + count_length]
        remainder = payload[offset + 8 + count_length:]
        if not remainder.startswith(rows_marker):
            raise ValueError("Chandra rows framing missing")
        expected = int(next(iter(_votable_rows(count_body)[0].values())))
        rows = _votable_rows(remainder[len(rows_marker):])
        if len(rows) != expected:
            raise ValueError("Chandra coverage table incomplete")
        region_key = next(key for key in rows[0] if "region" in key.casefold()) if rows else ""
        matches = sum(_stcs_intersects(row[region_key], center) for row in rows)
        return matches > 0, matches
    raise ValueError(f"unsupported coverage method: {method}")


def replay_anonymous(root: Path, errors: list[str]) -> dict[str, Any]:
    directory = root / ANON
    manifest_path = directory / "corpus-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    bundle_path = directory / manifest["evidence_bundle_path"]
    if sha256_file(bundle_path) != manifest["evidence_bundle_sha256"]:
        errors.append("anonymous evidence bundle SHA-256 mismatch")
    if sha256_file(manifest_path) != EXPECTED_ANONYMOUS_MANIFEST_SHA256:
        errors.append("anonymous manifest differs from independently reviewed revision")
    if sha256_file(bundle_path) != EXPECTED_ANONYMOUS_BUNDLE_SHA256:
        errors.append("anonymous bundle differs from independently reviewed revision")

    admitted = guard = 0
    states: Counter[str] = Counter()
    sightlines: set[str] = set()
    centers: dict[str, tuple[float, float]] = {}
    checked_paths: set[str] = set()
    coverage_replayed = 0
    member_count = 0
    with tarfile.open(bundle_path, "r:gz") as archive:
        members = {member.name for member in archive.getmembers() if member.isfile()}
        member_count = len(members)
        if len(members) != manifest["evidence_bundle_member_count"]:
            errors.append("anonymous evidence bundle member count mismatch")
        for cell in manifest["cells"]:
            label = f"{cell['sightline']}/{cell['service']}"
            sightlines.add(cell["sightline"])
            states[cell["status"]] += 1
            parsed_center = _center_from_query(cell["exact_query"])
            if parsed_center is not None:
                previous = centers.setdefault(cell["sightline"], parsed_center)
                if previous != parsed_center:
                    errors.append(f"{label}: inconsistent sightline center in exact query")
            method = cell.get("coverage_method")
            if method in {
                "legacy_dr9_official_sia_nexp_positive_pixels",
                "swift_lsxps_native_wcs_positive_pixels",
                "tap_polygon",
                "stcs_polygon",
            }:
                center = centers.get(cell["sightline"])
                if center is None:
                    errors.append(f"{label}: no center for independent coverage replay")
                else:
                    handle = archive.extractfile(cell["coverage_evidence_path"])
                    evidence = handle.read() if handle is not None else b""
                    try:
                        inside, coverage_count = replay_coverage_evidence(method, evidence, center)
                        coverage_replayed += 1
                        expected_inside = cell["coverage"] == "inside"
                        if inside != expected_inside:
                            errors.append(f"{label}: independent coverage state mismatch")
                        if coverage_count != cell["coverage_row_count"]:
                            errors.append(f"{label}: independent coverage count mismatch")
                    except Exception as exc:
                        errors.append(f"{label}: coverage replay failed: {type(exc).__name__}: {exc}")
            expected_state = {
                "inside": "matched" if cell["row_count"] else "unmatched",
                "outside": "outside_footprint",
                "not_applicable": "matched" if cell["row_count"] else "unmatched",
            }[cell["coverage"]]
            if cell["status"] != expected_state:
                errors.append(f"{label}: terminal state disagrees with coverage and row count")
            if not cell["pagination"]["complete"] or cell["pagination"]["overflow"]:
                errors.append(f"{label}: pagination is incomplete or overflowed")

            for path_key, hash_key in (
                ("canonical_path", "canonical_sha256"),
                ("guard_evidence_path", "guard_evidence_sha256"),
                ("raw_path", "raw_sha256"),
                ("coverage_evidence_path", "coverage_evidence_sha256"),
            ):
                path = cell.get(path_key)
                digest = cell.get(hash_key)
                if not path or not digest or path in checked_paths:
                    continue
                checked_paths.add(path)
                try:
                    handle = archive.extractfile(path)
                    data = handle.read() if handle is not None else b""
                except KeyError:
                    data = b""
                if not data:
                    errors.append(f"{label}: missing evidence member {path}")
                elif sha256_bytes(data) != digest:
                    errors.append(f"{label}: SHA-256 mismatch for {path}")

            try:
                canonical_bytes, canonical_rows = _json_member(archive, cell["canonical_path"])
            except Exception as exc:
                errors.append(f"{label}: canonical evidence unreadable: {type(exc).__name__}: {exc}")
                canonical_bytes, canonical_rows = b"", []
            try:
                _, guard_rows = _json_member(archive, cell["guard_evidence_path"])
            except Exception as exc:
                errors.append(f"{label}: guard evidence unreadable: {type(exc).__name__}: {exc}")
                guard_rows = []
            if sha256_bytes(canonical_bytes) != cell["canonical_sha256"]:
                errors.append(f"{label}: canonical hash mismatch")
            if len(canonical_rows) != cell["row_count"]:
                errors.append(f"{label}: canonical row count mismatch")
            if len(guard_rows) != cell["guard_ring_count"]:
                errors.append(f"{label}: guard row count mismatch")
            for index, row in enumerate(canonical_rows):
                center = centers.get(cell["sightline"])
                if center is None:
                    errors.append(f"{label}: cannot independently recover sightline center")
                    break
                check_anonymous_geometry(row, f"{label}/canonical/{index}", center=center, admitted=True, errors=errors)
            for index, row in enumerate(guard_rows):
                center = centers.get(cell["sightline"])
                if center is None:
                    errors.append(f"{label}: cannot independently recover sightline center")
                    break
                check_anonymous_geometry(row, f"{label}/guard/{index}", center=center, admitted=False, errors=errors)
            admitted += len(canonical_rows)
            guard += len(guard_rows)

    return {
        "manifest_sha256": sha256_file(manifest_path),
        "bundle_sha256": sha256_file(bundle_path),
        "bundle_members": member_count,
        "cells": len(manifest["cells"]),
        "sightlines": sorted(sightlines),
        "sightline_centers": {
            name: {"ra_deg": value[0], "dec_deg": value[1]}
            for name, value in sorted(centers.items())
        },
        "admitted_rows": admitted,
        "guard_only_rows": guard,
        "states": dict(sorted(states.items())),
        "coverage_cells_independently_replayed": coverage_replayed,
    }


def replay_protected(root: Path, errors: list[str]) -> dict[str, Any]:
    directory = root / PROTECTED
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if sha256_file(manifest_path) != EXPECTED_PROTECTED_MANIFEST_SHA256:
        errors.append("protected manifest differs from independently reviewed revision")
    raw_total = exact_total = guard_total = group_total = ambiguous_total = 0
    sightlines: set[str] = set()
    identities: dict[str, dict[str, Any]] = {}
    for sightline in manifest["sightlines"]:
        nickname = sightline["nickname"]
        sightlines.add(nickname)
        identities[nickname] = {
            "ra_deg": float(sightline["ra_deg"]),
            "dec_deg": float(sightline["dec_deg"]),
            "tns": sightline["tns"],
        }
        csv_path = directory / sightline["response_file"]
        sql_path = directory / sightline["sql_file"]
        manifest_center = (float(sightline["ra_deg"]), float(sightline["dec_deg"]))
        if sha256_file(csv_path) != sightline["response_sha256"]:
            errors.append(f"{nickname}: protected CSV SHA-256 mismatch")
        if sha256_file(sql_path) != sightline["sql_sha256"]:
            errors.append(f"{nickname}: protected SQL SHA-256 mismatch")
        sql = sql_path.read_text(encoding="utf-8")
        check_protected_rectangle(
            sql=sql,
            bounds=sightline["bounding_box"],
            center=manifest_center,
            label=nickname,
            errors=errors,
        )
        with csv_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
            if len(reader.fieldnames or []) != sightline["response_audit"]["native_column_count"] + 3:
                errors.append(f"{nickname}: protected native-column count mismatch")
        exact_rows: list[dict[str, Any]] = []
        for row in rows:
            if not (
                sightline["bounding_box"]["ra_min"] <= float(row["raMean"]) <= sightline["bounding_box"]["ra_max"]
                and sightline["bounding_box"]["dec_min"] <= float(row["decMean"]) <= sightline["bounding_box"]["dec_max"]
            ):
                errors.append(f"{nickname}: raw protected row lies outside manifest rectangle")
            separation = protected_row_separation(
                row, center=manifest_center, label=nickname, errors=errors
            )
            row["separation_arcmin"] = separation
            if separation <= 15.0:
                exact_rows.append(row)
        groups = shared_wise_groups(exact_rows)
        expected_groups = {
            str(group["cntr"]): tuple(sorted(str(value) for value in group["objIDs"]))
            for group in sightline["response_audit"]["shared_wise_identifier_groups"]
        }
        if groups != expected_groups:
            errors.append(f"{nickname}: shared WISE identity groups do not replay")
        audit = sightline["response_audit"]
        if len(rows) != audit["raw_row_count"] or len(exact_rows) != audit["exact_cone_row_count"]:
            errors.append(f"{nickname}: protected exact-cone counts do not replay")
        if len(rows) - len(exact_rows) != audit["guard_only_row_count"]:
            errors.append(f"{nickname}: protected guard count does not replay")
        if audit["shared_wise_identity_state"] != "ambiguous":
            errors.append(f"{nickname}: shared WISE groups are not marked ambiguous")
        raw_total += len(rows)
        exact_total += len(exact_rows)
        guard_total += len(rows) - len(exact_rows)
        group_total += len(groups)
        ambiguous_total += len(expected_groups)
    return {
        "manifest_sha256": sha256_file(manifest_path),
        "sightlines": sorted(sightlines),
        "sightline_identities": identities,
        "raw_rows": raw_total,
        "exact_cone_rows": exact_total,
        "guard_only_rows": guard_total,
        "shared_wise_identifier_groups": group_total,
        "ambiguous_shared_wise_groups": ambiguous_total,
    }


def replay_cadc(root: Path, errors: list[str]) -> dict[str, Any]:
    directory = root / CADC
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    for path_key, hash_key in (
        ("query_file", "query_sha256"),
        ("response_file", "response_sha256"),
        ("vospace_handshake_file", "vospace_handshake_sha256"),
    ):
        if sha256_file(directory / manifest[path_key]) != manifest[hash_key]:
            errors.append(f"CADC/CFIS {path_key} SHA-256 mismatch")
    if manifest["status"] != "access_denied" or not manifest["authenticated"]:
        errors.append("CADC/CFIS receipt is not authenticated access_denied")
    return {"status": manifest["status"], "http_status": manifest["http_status"]}


def _default_pipeline_dir(root: Path) -> Path:
    configured = os.environ.get("FOREGROUND_PIPELINE_REPO")
    if configured:
        return Path(configured).expanduser().resolve()
    candidates = (
        root.parent / "dsa110-FLITS-ticket16-read",
        root.parent / "pipeline",
        root.parent / "Faber2026" / "pipeline",
    )
    for candidate in candidates:
        if candidate.is_dir():
            head = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=candidate,
                check=False, capture_output=True, text=True,
            ).stdout.strip()
            if head == EXPECTED_PIPELINE_COMMIT:
                return candidate
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return candidates[-1]


def replay(root: Path, pipeline_dir: Path | None = None) -> dict[str, Any]:
    errors: list[str] = []
    anonymous = replay_anonymous(root, errors)
    protected = replay_protected(root, errors)
    cadc = replay_cadc(root, errors)
    def collision_safe(names: list[str], source: str) -> dict[str, str]:
        groups: dict[str, list[str]] = defaultdict(list)
        for name in names:
            groups[name.casefold()].append(name)
        collisions = {key: values for key, values in groups.items() if len(values) != 1}
        if collisions:
            errors.append(f"{source} sightline case-fold collisions: {collisions}")
        return {key: values[0] for key, values in groups.items() if len(values) == 1}

    anonymous_names = collision_safe(anonymous["sightlines"], "anonymous")
    protected_names = collision_safe(protected["sightlines"], "protected")
    if anonymous_names.keys() != protected_names.keys():
        errors.append(
            "sightline roster mismatch: "
            f"anonymous-only={sorted(anonymous_names.keys() - protected_names.keys())}; "
            f"protected-only={sorted(protected_names.keys() - anonymous_names.keys())}"
        )
    aliases = {
        anonymous_names[key]: protected_names[key]
        for key in anonymous_names.keys() & protected_names.keys()
        if anonymous_names[key] != protected_names[key]
    }
    for key in anonymous_names.keys() & protected_names.keys():
        anonymous_identity = anonymous["sightline_centers"][anonymous_names[key]]
        protected_identity = protected["sightline_identities"][protected_names[key]]
        if not protected_identity["tns"].startswith("FRB "):
            errors.append(f"{protected_names[key]}: protected TNS identity missing")
        if any(
            not math.isclose(anonymous_identity[field], protected_identity[field], rel_tol=0, abs_tol=1e-10)
            for field in ("ra_deg", "dec_deg")
        ):
            errors.append(f"{key}: cross-corpus sightline coordinates disagree")
    if pipeline_dir is None:
        pipeline_dir = _default_pipeline_dir(root)
    registry = replay_registry(pipeline_dir, errors)
    return {
        "schema_version": 1,
        "independence": "separate replay using Python, Astropy, and NumPy; no producer modules imported",
        "anonymous": anonymous,
        "protected": protected,
        "cadc_cfis": cadc,
        "roster_case_aliases": aliases,
        "registry_replay": registry,
        "errors": errors,
        "ok": not errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--pipeline-dir", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = replay(root, args.pipeline_dir)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    print(payload, end="")
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
