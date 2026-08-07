"""Frozen census evidence for sightlines without established host redshifts.

This module never queries a catalog.  It records what the checked-in census
can support and fails closed where exact query receipts are absent.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import astropy.units as u
import pandas as pd
from astropy.coordinates import SkyCoord

from foregrounds.paths import DATA_DIR

BURSTS_CSV = DATA_DIR / "frozen_census" / "bursts.csv"
REGISTRY_CSV = DATA_DIR / "intervening_census_registry.csv"
PROVENANCE_CSV = DATA_DIR / "candidate_redshift_provenance.csv"
SOURCE_PAYLOADS_JSON = (
    DATA_DIR / "candidate_redshift_source_payloads_2026-07-22.json"
)
CROSS_REFERENCES_CSV = DATA_DIR / "expanded_catalog_cross_references.csv"
COVERAGE_CSV = DATA_DIR / "survey_coverage" / "all_12_sightlines.csv"
OUTPUT_DIR = DATA_DIR / "hostless_sightlines"
REQUIRED_SURVEYS = (
    "CLUSTERS",
    "DESI_DR8_NORTH",
    "GLADE+",
    "NED",
    "SDSS_DR12",
)


def _optional_float(value: object) -> float | None:
    return float(value) if pd.notna(value) and math.isfinite(float(value)) else None


def _sha256(path: Path | str) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_sha256(value: object) -> bool:
    text = str(value)
    return len(text) == 64 and all(char in "0123456789abcdef" for char in text)


def _value_sha256(value: object) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _same_optional_number(
    first: object,
    second: object,
    *,
    tolerance: float = 1e-12,
) -> bool:
    left = _optional_float(first)
    right = _optional_float(second)
    if left is None or right is None:
        return left is right
    return math.isclose(left, right, rel_tol=0.0, abs_tol=tolerance)


def build_hostless_census_receipt(
    *,
    bursts_csv: Path | str = BURSTS_CSV,
    registry_csv: Path | str = REGISTRY_CSV,
    provenance_csv: Path | str = PROVENANCE_CSV,
    source_payloads_json: Path | str = SOURCE_PAYLOADS_JSON,
    cross_references_csv: Path | str = CROSS_REFERENCES_CSV,
    coverage_csv: Path | str = COVERAGE_CSV,
) -> dict:
    """Return the deterministic hostless-sightline evidence receipt."""
    bursts = pd.read_csv(bursts_csv)
    hostless = bursts.loc[bursts["z_spec"].isna()].sort_values("nickname")
    hostless_names = set(hostless["nickname"].astype(str))

    registry = pd.read_csv(registry_csv, dtype={"obj": str})
    registry = registry.loc[registry["nickname"].isin(hostless_names)].copy()
    provenance = pd.read_csv(provenance_csv, dtype={"obj": str})
    provenance = provenance.loc[provenance["nickname"].isin(hostless_names)].copy()
    source_payloads = json.loads(Path(source_payloads_json).read_text())
    payload_entries = {
        str(entry["key"]): entry for entry in source_payloads["entries"]
    }
    if len(payload_entries) != len(source_payloads["entries"]):
        raise ValueError("candidate source payload contains duplicate keys")
    cross_refs = pd.read_csv(cross_references_csv, dtype={"object_id": str})
    cross_refs = cross_refs.loc[cross_refs["nickname"].isin(hostless_names)].copy()
    coverage = pd.read_csv(coverage_csv)
    coverage["nickname_key"] = coverage["nickname"].astype(str).str.lower()
    coverage = coverage.loc[coverage["nickname_key"].isin(hostless_names)].copy()

    expected_coverage = {
        (nickname, survey)
        for nickname in hostless_names
        for survey in REQUIRED_SURVEYS
    }
    observed_coverage = list(
        zip(coverage["nickname_key"], coverage["survey"], strict=True)
    )
    if len(observed_coverage) != len(set(observed_coverage)):
        raise ValueError("coverage contains duplicate sightline/survey rows")
    if set(observed_coverage) != expected_coverage:
        raise ValueError(
            "coverage must contain exactly one row for each hostless "
            "sightline and required survey"
        )

    burst_by_name = hostless.set_index("nickname")
    for row in coverage.itertuples(index=False):
        burst = burst_by_name.loc[row.nickname_key]
        covered_coord = SkyCoord(row.ra, row.dec, unit=(u.hourangle, u.deg))
        burst_coord = SkyCoord(float(burst.ra_deg), float(burst.dec_deg), unit=u.deg)
        if covered_coord.separation(burst_coord).arcsec > 0.1:
            raise ValueError(f"coverage coordinate drift for {row.nickname_key}")

    candidates: list[dict] = []
    for row in registry.sort_values(["nickname", "type", "obj"]).itertuples(index=False):
        prov = provenance.loc[
            (provenance["nickname"] == row.nickname)
            & (provenance["type"] == row.type)
            & (provenance["obj"] == row.obj)
        ]
        xref = cross_refs.loc[
            (cross_refs["nickname"] == row.nickname)
            & (cross_refs["type"] == row.type)
            & (cross_refs["object_id"] == row.obj)
        ]
        if len(prov) != 1 or len(xref) != 1:
            raise ValueError(
                f"candidate evidence is not one-to-one for "
                f"{row.nickname}/{row.type}/{row.obj}"
            )
        p = prov.iloc[0]
        x = xref.iloc[0]
        if not _is_sha256(p.source_row_sha256):
            raise ValueError(
                f"invalid candidate source hash for "
                f"{row.nickname}/{row.type}/{row.obj}"
            )
        payload_key = f"{row.nickname}|{row.type}|{row.obj}"
        payload_entry = payload_entries.get(payload_key)
        if payload_entry is None:
            raise ValueError(f"candidate source payload missing for {payload_key}")
        if _value_sha256(payload_entry["selected_row"]) != str(
            p.source_row_sha256
        ):
            raise ValueError(f"candidate source hash drift for {payload_key}")
        expected_query_hash = (
            "not_applicable"
            if payload_entry["query_response"] is None
            else _value_sha256(payload_entry["query_response"])
        )
        if expected_query_hash != str(p.query_response_sha256):
            raise ValueError(f"candidate query-response hash drift for {payload_key}")
        adopted_z = _optional_float(p.adopted_z)
        adopted_z_err = _optional_float(p.adopted_z_err)
        selected = payload_entry["selected_row"]
        source_z = _optional_float(selected.get("z_phot"))
        source_z_err = _optional_float(selected.get("z_photErr"))
        if source_z is not None and source_z <= 0:
            source_z = None
        if source_z_err is not None and source_z_err <= 0:
            source_z_err = None
        if not _same_optional_number(
            adopted_z,
            round(source_z, 4) if source_z is not None else None,
        ) or not _same_optional_number(
            adopted_z_err,
            round(source_z_err, 4) if source_z_err is not None else None,
        ):
            raise ValueError(f"adopted redshift drift for {payload_key}")
        if str(selected.get("objID")) != str(row.obj):
            raise ValueError(f"candidate source identity drift for {payload_key}")
        if str(selected.get("class")).upper() != str(row.classification).upper():
            raise ValueError(f"candidate classification drift for {payload_key}")
        if (
            not _same_optional_number(row.best_z, adopted_z)
            or not _same_optional_number(row.best_z_err, adopted_z_err)
            or not _same_optional_number(x.best_z, adopted_z)
            or not _same_optional_number(x.best_z_err, adopted_z_err)
            or not _same_optional_number(x.impact_kpc, row.impact_kpc)
            or str(x.classification).upper()
            != str(row.classification).upper()
        ):
            raise ValueError(f"candidate joined-field drift for {payload_key}")
        mass = _optional_float(x.m200c_msun)
        radius = _optional_float(x.r200c_kpc)
        model_fields_complete = (
            str(row.type) == "halo"
            and str(row.classification).upper() == "GALAXY"
            and adopted_z is not None
            and adopted_z_err is not None
            and adopted_z_err > 0
            and mass is not None
            and radius is not None
        )
        candidates.append(
            {
                "nickname": str(row.nickname),
                "type": str(row.type),
                "object_id": str(row.obj),
                "classification": str(row.classification),
                "impact_kpc": _optional_float(row.impact_kpc),
                "adopted_z": adopted_z,
                "adopted_z_err": adopted_z_err,
                "source_family": str(p.source_family),
                "source_disposition": str(p.source_disposition),
                "source_row_sha256": str(p.source_row_sha256),
                "m200c_msun": mass,
                "r200c_kpc": radius,
                "model_fields_complete": model_fields_complete,
                "science_admitted": False,
            }
        )

    candidate_counts = pd.Series(
        [row["nickname"] for row in candidates], dtype="object"
    ).value_counts()
    sightlines = []
    for row in hostless.itertuples(index=False):
        count = int(candidate_counts.get(row.nickname, 0))
        expected_count = int(row.n_foreground_halo + row.n_foreground_cluster)
        if count != expected_count:
            raise ValueError(
                f"legacy candidate count drift for {row.nickname}: "
                f"{count} != {expected_count}"
            )
        sightlines.append(
            {
                "nickname": str(row.nickname),
                "tns": str(row.tns),
                "ra_deg": float(row.ra_deg),
                "dec_deg": float(row.dec_deg),
                "legacy_candidate_count": count,
                "legacy_candidate_state": (
                    "present_unverified" if count else "empty_unverified"
                ),
                "foreground_free": False,
            }
        )

    coverage_rows = []
    for row in coverage.sort_values(["nickname_key", "survey"]).itertuples(
        index=False
    ):
        footprint_status = str(row.footprint_status)
        if footprint_status not in {"covered", "not_covered"}:
            raise ValueError(
                f"invalid footprint status for {row.nickname_key}/{row.survey}"
            )
        covered = footprint_status == "covered"
        footprint_source = str(row.footprint_source)
        if footprint_source == "all_sky_contract" and not covered:
            raise ValueError(
                f"all-sky footprint cannot exclude {row.nickname_key}/{row.survey}"
            )
        footprint_hash = (
            str(row.footprint_sha256)
            if pd.notna(row.footprint_sha256)
            else None
        )
        if (
            footprint_source.startswith("data/")
            and footprint_hash is not None
        ):
            footprint_path = DATA_DIR.parent / footprint_source
            if not footprint_path.is_file() or _sha256(footprint_path) != footprint_hash:
                raise ValueError(
                    f"footprint hash drift for {row.nickname_key}/{row.survey}"
                )
        footprint_ready = (
            footprint_source == "all_sky_contract"
            or (
                footprint_source != "unavailable"
                and footprint_hash is not None
                and _is_sha256(footprint_hash)
            )
        )
        if not covered and not footprint_ready:
            raise ValueError(
                f"unproven footprint exclusion for "
                f"{row.nickname_key}/{row.survey}"
            )
        coverage_rows.append(
            {
                "nickname": str(row.nickname_key),
                "survey": str(row.survey),
                "release": str(row.release),
                "footprint_status": footprint_status,
                "footprint_source": footprint_source,
                "footprint_sha256": footprint_hash,
                "footprint_evidence_ready": footprint_ready,
                "query_required": covered,
                "query_receipt_status": "missing" if covered else "not_required",
            }
        )
    return {
        "schema_version": 1,
        "source_files": {
            "candidate_redshift_provenance.csv": _sha256(provenance_csv),
            "candidate_redshift_source_payloads_2026-07-22.json": _sha256(
                source_payloads_json
            ),
            "expanded_catalog_cross_references.csv": _sha256(
                cross_references_csv
            ),
            "frozen_census/bursts.csv": _sha256(bursts_csv),
            "intervening_census_registry.csv": _sha256(registry_csv),
            "survey_coverage/all_12_sightlines.csv": _sha256(coverage_csv),
        },
        "status": "blocked",
        "sightlines": sightlines,
        "candidates": candidates,
        "coverage": coverage_rows,
        "blockers": [
            "exact_query_receipts_missing",
            "coverage_evidence_incomplete",
            "legacy_empty_result_is_not_a_verified_non_detection",
        ],
    }


def write_hostless_census_artifacts(
    output_dir: Path | str = OUTPUT_DIR,
) -> dict[str, str]:
    """Write deterministic JSON and CSV views; return their SHA-256 hashes."""
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    receipt = build_hostless_census_receipt()

    receipt_path = destination / "receipt.json"
    receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    pd.DataFrame(receipt["candidates"]).to_csv(
        destination / "candidates.csv", index=False, lineterminator="\n"
    )
    pd.DataFrame(receipt["coverage"]).to_csv(
        destination / "coverage.csv", index=False, lineterminator="\n"
    )
    return {
        name: _sha256(destination / name)
        for name in ("candidates.csv", "coverage.csv", "receipt.json")
    }
