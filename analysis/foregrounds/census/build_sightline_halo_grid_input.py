"""Build the fail-closed twelve-sightline Figure 3 review input."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from foregrounds.census.census_registry import load_census_duplicates
from foregrounds.paths import ANALYSIS_ROOT, DATA_DIR

EXPANDED_CSV = DATA_DIR / "expanded_catalog_cross_references.csv"
OUTPUT_CSV = DATA_DIR / "sightline_halo_grid.csv"
OUTPUT_RECEIPT = DATA_DIR / "sightline_halo_grid.receipt.json"
BURSTS_CSV = DATA_DIR / "frozen_census" / "bursts.csv"
COVERAGE_CSV = DATA_DIR / "survey_coverage" / "all_12_sightlines.csv"
HOSTLESS_RECEIPT = DATA_DIR / "hostless_sightlines" / "receipt.json"
DM_Z_POSTERIOR = ANALYSIS_ROOT / "foregrounds" / "results" / "dm_redshift" / "posterior.json"
DM_Z_RECEIPT = ANALYSIS_ROOT / "foregrounds" / "results" / "dm_redshift" / "receipt.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _coverage_fields(
    nickname: str,
    coverage: pd.DataFrame,
    hostless_coverage: list[dict],
) -> dict[str, str]:
    rows = coverage[coverage["nickname"].str.lower() == nickname].sort_values("survey")
    summary = "; ".join(
        f"{row.survey}:{row.footprint_status}" for row in rows.itertuples(index=False)
    )
    outside = sorted(rows.loc[rows.footprint_status == "not_covered", "survey"].astype(str))
    incomplete = sorted(
        rows.loc[
            rows.footprint_source.astype(str).eq("unavailable"),
            "survey",
        ].astype(str)
    )
    limitations = []
    if outside:
        limitations.append(f"outside footprint: {', '.join(outside)}")
    if incomplete:
        limitations.append(f"footprint evidence incomplete: {', '.join(incomplete)}")
    query_missing = sorted(
        str(row["survey"])
        for row in hostless_coverage
        if str(row["nickname"]).lower() == nickname
        and row["query_receipt_status"] == "missing"
    )
    return {
        "coverage_summary": summary,
        "coverage_limitations": "; ".join(limitations),
        "query_limitations": (
            f"exact query receipts missing: {', '.join(query_missing)}"
            if query_missing
            else ""
        ),
    }


def validate_frame(frame: pd.DataFrame) -> None:
    """Reject any input that could promote diagnostic information."""
    hosts = frame[frame.row_kind == "host"]
    systems = frame[frame.row_kind == "system"]
    if len(hosts) != 12 or not hosts.nickname.is_unique:
        raise ValueError("Figure 3 input must contain twelve unique host rows")
    if set(hosts.redshift_class) != {"established", "inferred_dm_z"}:
        raise ValueError("host redshift classes must be established or inferred_dm_z")
    inferred = hosts[hosts.redshift_class == "inferred_dm_z"]
    if set(inferred.nickname) != {"freya", "mahi", "wilhelm"}:
        raise ValueError("the inferred-redshift roster must be Freya, Mahi, and Wilhelm")
    if not (
        inferred.frb_z_lower.notna().all()
        and inferred.frb_z.notna().all()
        and inferred.frb_z_upper.notna().all()
        and (inferred.frb_z_lower < inferred.frb_z).all()
        and (inferred.frb_z < inferred.frb_z_upper).all()
    ):
        raise ValueError("every inferred host requires a full ordered redshift interval")
    if not inferred.frb_posterior_sha256.astype(str).str.fullmatch(r"[0-9a-f]{64}").all():
        raise ValueError("every inferred host requires the exact posterior SHA-256")
    if not inferred.frb_redshift_basis.astype(str).str.contains("coupled").all():
        raise ValueError("every inferred host requires the coupled DM-redshift basis")
    if not inferred.coverage_limitations.astype(bool).all():
        raise ValueError("every inferred host requires explicit coverage limitations")
    if not inferred.query_limitations.astype(bool).all():
        raise ValueError("every inferred host requires explicit query limitations")
    if hosts.empty_sightline_claim.astype(bool).any():
        raise ValueError("Figure 3 must never claim a sightline is foreground-free")

    allowed = {"confirmed_system", "probabilistic_candidate"}
    if not set(systems.evidence_class) <= allowed:
        raise ValueError("system evidence class is undeclared")
    candidates = systems[systems.evidence_class == "probabilistic_candidate"]
    if candidates.candidate_science_admitted.astype(bool).any():
        raise ValueError("a probabilistic candidate was promoted to science-admitted")
    if candidates.budget_eligible.astype(bool).any():
        raise ValueError("a probabilistic candidate was promoted into the DM budget")
    confirmed = systems[systems.evidence_class == "confirmed_system"]
    if not confirmed.final_verdict.astype(str).eq("confirmed").all():
        raise ValueError("a confirmed display row lacks a confirmed census verdict")


def build_frame() -> pd.DataFrame:
    catalog = pd.read_csv(EXPANDED_CSV, dtype={"object_id": str})
    catalog["nickname"] = catalog["nickname"].str.lower()
    bursts = pd.read_csv(BURSTS_CSV)
    coverage = pd.read_csv(COVERAGE_CSV)
    hostless = json.loads(HOSTLESS_RECEIPT.read_text(encoding="utf-8"))
    posterior = json.loads(DM_Z_POSTERIOR.read_text(encoding="utf-8"))
    posterior_receipt = json.loads(DM_Z_RECEIPT.read_text(encoding="utf-8"))
    posterior_hash = _sha256(DM_Z_POSTERIOR)
    recorded_hash = posterior_receipt["outputs"][
        "foregrounds/results/dm_redshift/posterior.json"
    ]
    if posterior_hash != recorded_hash:
        raise ValueError("DM-redshift posterior differs from its reproduction receipt")
    if posterior["status"] != "diagnostic_dm_redshift_estimate_not_established_redshift":
        raise ValueError("DM-redshift posterior is not explicitly diagnostic")

    posterior_rows = {str(row["nickname"]).lower(): row for row in posterior["rows"]}
    hostless_candidates = {
        (str(row["nickname"]).lower(), str(row["object_id"])): row
        for row in hostless["candidates"]
    }
    duplicates = set(load_census_duplicates())
    records: list[dict] = []

    for _, burst in bursts.iterrows():
        nick = str(burst.nickname).lower()
        group = catalog[catalog.nickname == nick]
        established_z = pd.to_numeric(burst.z_spec, errors="coerce")
        inferred = not np.isfinite(established_z)
        if inferred:
            dm_row = posterior_rows[nick]
            estimate = dm_row["coupled_fiducial"]
            host_z = float(estimate["z50"])
            z_lower = float(estimate["z16"])
            z_upper = float(estimate["z84"])
            basis = (
                "diagnostic coupled DM-redshift posterior; "
                "host-rest median 100 pc cm^-3"
            )
            posterior_status = str(posterior["status"])
            census_status = str(hostless["status"])
        else:
            host_z = float(established_z)
            z_lower = host_z
            z_upper = host_z
            basis = "established spectroscopic host redshift"
            posterior_status = ""
            census_status = "established_host_redshift"

        coverage_fields = _coverage_fields(
            nick,
            coverage,
            hostless["coverage"] if inferred else [],
        )
        common = {
            "nickname": nick,
            "frb_name": str(burst.tns),
            "frb_z": host_z,
            "frb_z_lower": z_lower,
            "frb_z_upper": z_upper,
            "redshift_class": "inferred_dm_z" if inferred else "established",
            "frb_redshift_basis": basis,
            "frb_posterior_sha256": posterior_hash if inferred else "",
            "frb_posterior_status": posterior_status,
            "frb_ra_deg": float(burst.ra_deg),
            "frb_dec_deg": float(burst.dec_deg),
            **coverage_fields,
            "census_status": census_status,
            "empty_sightline_claim": False,
        }
        records.append(
            {
                **common,
                "row_kind": "host",
                "evidence_class": "host",
                "object_id": None,
                "system_type": None,
                "final_verdict": None,
                "system_z": None,
                "system_z_lower": None,
                "system_z_upper": None,
                "candidate_foreground_probability": None,
                "candidate_science_admitted": False,
                "candidate_ra_deg": None,
                "candidate_dec_deg": None,
                "impact_kpc": None,
                "mass_msun": None,
                "radius_kpc": None,
                "radius_definition": None,
                "geometry_status": "host_roster",
                "budget_eligible": False,
            }
        )

        if inferred:
            candidate_probability = dm_row["coupled_fiducial"][
                "candidate_foreground_probability"
            ]
            for (candidate_nick, object_id), candidate in sorted(
                hostless_candidates.items()
            ):
                if candidate_nick != nick:
                    continue
                source = group[group.object_id.astype(str) == object_id]
                if len(source) != 1:
                    raise ValueError(f"{nick}/{object_id}: expanded-catalog row is not unique")
                row = source.iloc[0]
                z = candidate["adopted_z"]
                zerr = candidate["adopted_z_err"]
                complete = all(
                    candidate.get(field) is not None
                    for field in ("adopted_z", "adopted_z_err", "m200c_msun", "r200c_kpc")
                ) and pd.notna(row.impact_kpc)
                records.append(
                    {
                        **common,
                        "row_kind": "system",
                        "evidence_class": "probabilistic_candidate",
                        "object_id": object_id,
                        "system_type": str(candidate["type"]),
                        "final_verdict": str(row.final_verdict),
                        "system_z": z,
                        "system_z_lower": max(0.0, float(z) - float(zerr))
                        if z is not None and zerr is not None
                        else None,
                        "system_z_upper": float(z) + float(zerr)
                        if z is not None and zerr is not None
                        else None,
                        "candidate_foreground_probability": candidate_probability.get(object_id),
                        "candidate_science_admitted": bool(candidate["science_admitted"]),
                        "candidate_ra_deg": float(row.ra_deg),
                        "candidate_dec_deg": float(row.dec_deg),
                        "impact_kpc": float(row.impact_kpc) if pd.notna(row.impact_kpc) else None,
                        "mass_msun": candidate["m200c_msun"] if complete else None,
                        "radius_kpc": candidate["r200c_kpc"] if complete else None,
                        "radius_definition": "R200c" if complete else None,
                        "geometry_status": "pass" if complete else "missing_sourced_geometry",
                        "budget_eligible": False,
                    }
                )
            continue

        for _, row in group.iterrows():
            key = (nick, str(row.object_id))
            if row.final_verdict != "confirmed" or key in duplicates:
                continue
            z = pd.to_numeric(row.best_z, errors="coerce")
            mass = radius = np.nan
            radius_definition = None
            geometry_status = "pass"
            if not np.isfinite(z) or float(z) <= 0 or float(z) >= host_z:
                geometry_status = "invalid_foreground_redshift"
            elif row.type == "halo":
                mass = pd.to_numeric(row.m200c_msun, errors="coerce")
                radius = pd.to_numeric(row.r200c_kpc, errors="coerce")
                radius_definition = "R200c"
            else:
                mass500 = pd.to_numeric(row.m500_1e14msun, errors="coerce")
                radius500 = pd.to_numeric(row.r500_mpc, errors="coerce")
                mass = float(mass500) * 1.0e14 if np.isfinite(mass500) else np.nan
                radius = float(radius500) * 1.0e3 if np.isfinite(radius500) else np.nan
                radius_definition = "R500c_catalog"
            if geometry_status == "pass" and (
                not np.isfinite(mass)
                or not np.isfinite(radius)
                or float(mass) <= 0
                or float(radius) <= 0
            ):
                geometry_status = "missing_sourced_geometry"
            records.append(
                {
                    **common,
                    "row_kind": "system",
                    "evidence_class": "confirmed_system",
                    "object_id": str(row.object_id),
                    "system_type": str(row.type),
                    "final_verdict": str(row.final_verdict),
                    "system_z": float(z) if np.isfinite(z) else None,
                    "system_z_lower": float(z) if np.isfinite(z) else None,
                    "system_z_upper": float(z) if np.isfinite(z) else None,
                    "candidate_foreground_probability": None,
                    "candidate_science_admitted": True,
                    "candidate_ra_deg": float(row.ra_deg),
                    "candidate_dec_deg": float(row.dec_deg),
                    "impact_kpc": float(row.impact_kpc) if pd.notna(row.impact_kpc) else None,
                    "mass_msun": float(mass) if np.isfinite(mass) else None,
                    "radius_kpc": float(radius) if np.isfinite(radius) else None,
                    "radius_definition": radius_definition,
                    "geometry_status": geometry_status,
                    "budget_eligible": bool(row.budget_eligible),
                }
            )
    frame = pd.DataFrame(records)
    validate_frame(frame)
    return frame


def _write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", newline="") as handle:
            handle.write(text)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def build(path: Path = OUTPUT_CSV) -> Path:
    frame = build_frame()
    csv_text = frame.to_csv(index=False, lineterminator="\n")
    _write_atomic(path, csv_text)
    receipt = {
        "schema_version": 1,
        "status": "validated_review_candidate_input",
        "manuscript_promotion": "blocked_pending_owner_visual_approval",
        "inputs": {
            str(source.relative_to(ANALYSIS_ROOT)): _sha256(source)
            for source in (
                EXPANDED_CSV,
                BURSTS_CSV,
                COVERAGE_CSV,
                HOSTLESS_RECEIPT,
                DM_Z_POSTERIOR,
                DM_Z_RECEIPT,
            )
        },
        "output": {
            str(path.relative_to(ANALYSIS_ROOT)): hashlib.sha256(
                csv_text.encode("utf-8")
            ).hexdigest()
        },
        "facts": {
            "sightlines": 12,
            "established_redshifts": 9,
            "inferred_redshifts": 3,
            "empty_sightline_claims": 0,
        },
    }
    _write_atomic(OUTPUT_RECEIPT, json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    return path


def main() -> None:
    print(build())


if __name__ == "__main__":
    main()
