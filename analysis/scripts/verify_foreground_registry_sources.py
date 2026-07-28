#!/usr/bin/env python3
"""Offline, source-level replay of the 52-row foreground registry.

This verifier intentionally imports no census producer or adjudication code.
It reads only frozen source payloads, owner-approved host evidence, and the
production CSV files at the pinned consolidated-analysis commit.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
import io
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any


EXPECTED_ANALYSIS_COMMIT = "1512b15ed1403d42fd12962e77690c18dd3eab09"
EXPECTED_PIPELINE_COMMIT = EXPECTED_ANALYSIS_COMMIT


def read_csv_text(text: str) -> list[dict[str, str]]:
    with io.StringIO(text, newline="") as handle:
        return list(csv.DictReader(handle))


def git_text(repo: Path, commit: str, path: str) -> tuple[str, str]:
    blob = subprocess.run(["git", "rev-parse", f"{commit}:{path}"], cwd=repo,
                          check=True, capture_output=True, text=True).stdout.strip()
    text = subprocess.run(["git", "show", f"{commit}:{path}"], cwd=repo,
                          check=True, capture_output=True, text=True).stdout
    return text, blob


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def finite(value: str | None) -> bool:
    try:
        return bool(value and value.strip()) and math.isfinite(float(value))
    except ValueError:
        return False


def separation_arcsec(ra1: float, dec1: float, ra2: float, dec2: float) -> float:
    dec1r, dec2r = math.radians(dec1), math.radians(dec2)
    dra = math.radians(ra2 - ra1)
    ddec = dec2r - dec1r
    value = (
        math.sin(ddec / 2) ** 2
        + math.cos(dec1r) * math.cos(dec2r) * math.sin(dra / 2) ** 2
    )
    return math.degrees(2 * math.asin(min(1.0, math.sqrt(value)))) * 3600


def rounded_source_match(local: str, source: str) -> bool:
    quantum = Decimal(1).scaleb(Decimal(local).as_tuple().exponent)
    return Decimal(source).quantize(quantum, rounding=ROUND_HALF_UP) == Decimal(local)


def source_fields(family: str, selected: dict[str, Any]) -> tuple[str, str, str, str]:
    """Return source id, redshift, uncertainty, and coordinate field names."""
    if family == "Legacy Survey/Zhou21":
        return f"ls_id:{selected['ls_id']}", "z_phot_mean", "z_phot_std", "ra,dec"
    if family == "DESI":
        return f"targetid:{selected['targetid']}", "z", "zerr", "mean_fiber_ra,mean_fiber_dec"
    if family == "PS1-STRM":
        return f"objID:{selected['objID']}", "z_phot", "z_photErr", "raMean,decMean"
    if family == "NED":
        row = selected["object_result"]
        return f"ned_name:{row['Object Name']}", "Redshift", "", "RA,DEC"
    if family == "WHL12":
        return f"recno:{selected['recno']};WHL:{selected['WHL']}", "zph", "", "RAJ2000,DEJ2000"
    raise ValueError(f"unsupported source family: {family}")


def selected_object(family: str, selected: dict[str, Any]) -> dict[str, Any]:
    return selected["object_result"] if family == "NED" else selected


def derived_measurement_kind(family: str, selected: dict[str, Any]) -> str:
    if family in {"Legacy Survey/Zhou21", "PS1-STRM"}:
        return "photometric"
    if family == "DESI":
        if selected.get("zwarn") != 0:
            raise ValueError("DESI source is not quality-admitted")
        return "spectroscopic"
    if family == "NED":
        flag = str(selected["object_result"].get("Redshift Flag") or "")
        return "photometric" if flag.startswith("P") else "unknown"
    if family == "WHL12":
        return "catalog_cluster"
    raise ValueError(f"unsupported source family: {family}")


def replay_verdict(row: dict[str, str], source: dict[str, str], strm: dict[str, dict[str, str]]) -> str:
    if not finite(row["best_z"]) or not finite(row["host_z_spec"]):
        return "inconclusive"
    if row["obj"] in strm:
        item = strm[row["obj"]]
        if item["class"] != "GALAXY" or item["extrapolation_Photoz"] == "1":
            return "inconclusive"
    z, host = float(row["best_z"]), float(row["host_z_spec"])
    if source["measurement_kind"] in {"spectroscopic", "catalog_cluster"}:
        return "confirmed" if z < host else "refuted"
    if not finite(row["best_z_err"]):
        return "inconclusive"
    error = float(row["best_z_err"])
    if z + error < host:
        return "confirmed"
    if z - error > host:
        return "refuted"
    return "inconclusive"


def verify(root: Path, pipeline: Path, *, analysis_commit: str = EXPECTED_ANALYSIS_COMMIT,
           pipeline_commit: str = EXPECTED_PIPELINE_COMMIT) -> dict[str, Any]:
    errors: list[str] = []
    census = "foregrounds/studies/census/data"
    specs = {
        "registry": (pipeline, f"{census}/intervening_census_registry.csv"),
        "provenance": (pipeline, f"{census}/candidate_redshift_provenance.csv"),
        "payloads": (pipeline, f"{census}/candidate_redshift_source_payloads_2026-07-22.json"),
        "strm": (pipeline, f"{census}/frozen_census/strm_catalog_rows.csv"),
        "duplicates": (pipeline, f"{census}/census_masses/census_duplicates.csv"),
        "extensions": (pipeline, f"{census}/census_extensions/v4_extension.csv"),
        "verdi": (root, "docs/rse/specs/evidence/verdi-host-redshifts-2026-07-22/verdi_host_redshift_comparison.csv"),
        "law": (root, "docs/rse/specs/evidence/law2024-zach-whitney-host-redshifts-2026-07-22/host_redshift_rows.csv"),
        "connor": (root, "docs/rse/specs/evidence/connor2025-whitney-host-redshift-2026-07-22/host_redshift_row.csv"),
    }
    texts, blobs = {}, {}
    for name, (repo, relpath) in specs.items():
        commit = pipeline_commit if repo == pipeline else analysis_commit
        text, blob = git_text(repo, commit, relpath)
        texts[name], blobs[name] = text, blob
        worktree = repo / relpath
        if not worktree.is_file() or worktree.read_text() != text:
            errors.append(f"tracked input differs from pinned blob: {name}")

    registry = read_csv_text(texts["registry"])
    provenance = read_csv_text(texts["provenance"])
    provenance_by_key = {(r["nickname"], r["type"], r["obj"]): r for r in provenance}
    payload = json.loads(texts["payloads"])
    payload_by_key = {tuple(e["key"].split("|", 2)): e for e in payload["entries"]}
    strm = {r["objID"]: r for r in read_csv_text(texts["strm"])}
    extensions = {(r["nickname"], r["type"], r["obj"]): r for r in read_csv_text(texts["extensions"])}
    if len(registry) != 52 or len(provenance_by_key) != 52 or len(payload_by_key) != 52:
        errors.append("registry, provenance ledger, and payload must each contain 52 unique rows")

    verdi = {r["nickname"].casefold(): r for r in read_csv_text(texts["verdi"])}
    law = {r["nickname"].casefold(): r for r in read_csv_text(texts["law"])}
    connor = {
        r["name"].casefold(): {
            "frb_identifier": r["tns_name"],
            "published_redshift": r["redshift"],
        }
        for r in read_csv_text(texts["connor"])
    }

    row_results: list[dict[str, Any]] = []
    for row in registry:
        key = (row["nickname"], row["type"], row["obj"])
        label = "/".join(key)
        source = provenance_by_key.get(key)
        frozen = payload_by_key.get(key)
        row_errors: list[str] = []
        if source is None or frozen is None:
            row_errors.append("missing candidate provenance row or payload")
            continue

        selected, response = frozen["selected_row"], frozen["query_response"]
        expected_row_hash = "not_applicable" if selected is None else sha256_json(selected)
        expected_response_hash = "not_applicable" if response is None else sha256_json(response)
        if source["source_row_sha256"] != expected_row_hash:
            row_errors.append("candidate source-row hash mismatch")
        if source["query_response_sha256"] != expected_response_hash:
            row_errors.append("candidate query-response hash mismatch")

        coordinate_separation = None
        candidate_source_status = "verified"
        if finite(row["best_z"]):
            if selected is None:
                row_errors.append("adopted candidate redshift lacks frozen source row")
            else:
                family = source["source_family"]
                stable_id, zfield, efield, coord_fields = source_fields(family, selected)
                native = selected_object(family, selected)
                kind = derived_measurement_kind(family, selected)
                if source["measurement_kind"] != kind:
                    row_errors.append("measurement kind differs from frozen source semantics")
                if source["stable_source_id"] != stable_id:
                    row_errors.append("stable candidate identifier mismatch")
                if abs(float(source["adopted_z"]) - float(native[zfield])) > 5e-4:
                    row_errors.append("adopted candidate redshift differs from frozen source")
                if source["adopted_z"] != row["best_z"]:
                    row_errors.append("candidate ledger and registry redshifts differ")
                if efield and finite(row["best_z_err"]):
                    if not rounded_source_match(row["best_z_err"], str(native[efield])):
                        row_errors.append("candidate uncertainty differs from frozen source")
                if source["adopted_z_err"] != row["best_z_err"]:
                    row_errors.append("candidate ledger and registry uncertainties differ")
                if efield and not finite(row["best_z_err"]):
                    row_errors.append("source reports uncertainty but adopted uncertainty is blank")
                if not efield and finite(row["best_z_err"]):
                    row_errors.append("adopted uncertainty lacks source support")
                if family == "NED":
                    detail = selected["redshift_record"]
                    no_unc = "no unc" in str(detail.get("Unc. Significance", "")).lower()
                    if not no_unc or source["source_reported_z_err"]:
                        row_errors.append("NED uncertainty-unavailable semantics mismatch")
                elif source["source_reported_z_err"]:
                    # In this pinned schema LS, DESI, STRM, and WHL native
                    # uncertainties are bound through selected_row and
                    # adopted_z_err (when available), not duplicated here.
                    row_errors.append("source-reported uncertainty metadata violates family contract")
                ra_field, dec_field = coord_fields.split(",")
                coordinate_separation = separation_arcsec(
                    float(row["ra_deg"]), float(row["dec_deg"]),
                    float(native[ra_field]), float(native[dec_field]),
                )
                limit = 120.0 if family == "WHL12" else 90.0 if row["type"] == "cluster" else 5.0
                if coordinate_separation > limit:
                    row_errors.append("candidate source position exceeds selection radius")
                if response:
                    for response_field in ("rows", "region_rows", "redshift_rows"):
                        if response_field in response and response[response_field] != sorted(
                            response[response_field], key=canonical_json
                        ):
                            row_errors.append("frozen query rows are not deterministically ordered")
        elif row["best_z_source"] == "PS1-STRM":
            native = strm.get(row["obj"])
            if native is None or native["objID"] != row["obj"]:
                row_errors.append("redshiftless PS1-STRM identity missing")
            else:
                coordinate_separation = separation_arcsec(
                    float(row["ra_deg"]), float(row["dec_deg"]),
                    float(native["raMean"]), float(native["decMean"]),
                )
                if coordinate_separation > 5:
                    row_errors.append("redshiftless PS1-STRM position mismatch")
                if native["z_phot"] != "-999.0" or native["class"] != "UNSURE":
                    row_errors.append("redshiftless PS1-STRM semantics mismatch")
                if selected is None:
                    row_errors.append("redshiftless PS1-STRM payload row missing")
                else:
                    for field in ("raMean", "decMean", "prob_Galaxy", "z_phot", "z_photErr", "z_phot0"):
                        if not math.isclose(
                            float(selected[field]), float(native[field]), rel_tol=0, abs_tol=1e-12
                        ):
                            row_errors.append(f"redshiftless PS1-STRM payload differs: {field}")
                    if (
                        str(selected["objID"]) != row["obj"]
                        or selected["class"] != native["class"]
                        or str(selected["extrapolation_Photoz"]) != native["extrapolation_Photoz"]
                    ):
                        row_errors.append("redshiftless PS1-STRM payload identity differs")
                if (
                    source["source_family"] != "PS1-STRM"
                    or source["stable_source_id"] != f"objID:{row['obj']}"
                    or source["measurement_kind"] != "no_trustworthy_redshift"
                    or source["source_disposition"] != "identity_verified_no_catalog_redshift"
                    or source["adopted_z"]
                    or source["adopted_z_err"]
                ):
                    row_errors.append("redshiftless PS1-STRM ledger semantics mismatch")
                candidate_source_status = "verified_identity_only_no_redshift"
        else:
            extension = extensions.get(key)
            if extension is None:
                row_errors.append("redshiftless extension identity missing")
            elif selected is None or response is None:
                row_errors.append("manual extension lacks frozen authoritative source rows")
            else:
                designation = row["obj"].removeprefix("WISEA ")
                if (
                    source["source_family"] != "AllWISE"
                    or source["stable_source_id"] != f"AllWISE:{designation}"
                    or source["measurement_kind"] != "identity_only"
                    or source["source_disposition"] != "identity_verified_catalog_has_no_redshift"
                    or source["adopted_z"]
                    or source["adopted_z_err"]
                ):
                    row_errors.append("manual extension identity-ledger semantics mismatch")
                if selected.get("AllWISE") != designation or selected.get("catalog_id") != designation:
                    row_errors.append("manual extension AllWISE designation mismatch")
                coordinate_separation = separation_arcsec(
                    float(row["ra_deg"]), float(row["dec_deg"]),
                    float(selected["match_ra_deg"]), float(selected["match_dec_deg"]),
                )
                if coordinate_separation > 3:
                    row_errors.append("manual extension AllWISE position mismatch")
                if (
                    response.get("service") != "CDS VizieR"
                    or response.get("table") != "II/328/allwise"
                    or selected not in response.get("rows", [])
                ):
                    row_errors.append("manual extension AllWISE query payload mismatch")
            candidate_source_status = "verified_identity_only_no_redshift"

        nickname = row["nickname"].casefold()
        host = connor.get(nickname) or law.get(nickname) or verdi.get(nickname)
        host_status = "verified"
        host_source_z = ""
        if host is None:
            host_status = "missing_host_source"
            row_errors.append("host has no authoritative source row")
        elif nickname in connor or nickname in law:
            host_source_z = host["published_redshift"]
            if host["frb_identifier"] != row["tns"]:
                host_status = "host_identifier_mismatch"
                row_errors.append("host FRB identifier differs from Law source")
            elif not rounded_source_match(row["host_z_spec"], host_source_z):
                host_status = "host_redshift_mismatch"
                row_errors.append("host redshift differs from Law source at registry precision")
            elif row["host_z_spec"] != host_source_z:
                host_status = "verified_rounded_to_registry_precision"
        else:
            host_source_z = host["current_draft_redshift"]
            local_tns = row["tns"].removeprefix("FRB ")
            if host["verdi_frb_id"] != local_tns:
                host_status = "host_identifier_alias_requires_adjudication"
                row_errors.append("local and Verdi FRB identifiers are not adjudicated")
            if finite(row["host_z_spec"]) and not finite(host_source_z):
                host_status = "authoritative_host_redshift_blank"
                row_errors.append("registry host redshift is absent from approved Verdi row")
            elif finite(row["host_z_spec"]) and not rounded_source_match(row["host_z_spec"], host_source_z):
                host_status = "host_redshift_mismatch"
                row_errors.append("registry host redshift differs from approved Verdi row")
            elif not finite(row["host_z_spec"]) and finite(host_source_z):
                host_status = "registry_host_redshift_blank"
                row_errors.append("approved Verdi host redshift is absent from registry")

        verdict_source = dict(source)
        if selected is not None and finite(row["best_z"]):
            verdict_source["measurement_kind"] = derived_measurement_kind(source["source_family"], selected)
        verdict = replay_verdict(row, verdict_source, strm)
        source_host_verdict = None
        if finite(host_source_z):
            source_host_row = dict(row)
            source_host_row["host_z_spec"] = host_source_z
            source_host_verdict = replay_verdict(source_host_row, verdict_source, strm)
        if verdict != row["final_verdict"]:
            row_errors.append("stored verdict does not replay")
        budget = verdict == "confirmed" and (
            row["type"] == "halo"
            or (finite(row["b_over_r500"]) and float(row["b_over_r500"]) <= 1)
        )
        if budget != (row["budget_eligible"].casefold() == "true"):
            row_errors.append("stored budget flag does not replay")

        row_results.append({
            "key": label,
            "candidate_source_status": candidate_source_status,
            "candidate_coordinate_separation_arcsec": coordinate_separation,
            "host_source": (
                "Connor et al. 2025" if nickname in connor
                else "Law et al. 2024" if nickname in law
                else "approved Verdi current table"
            ),
            "host_source_redshift": host_source_z,
            "host_status": host_status,
            "replayed_verdict": verdict,
            "authoritative_host_replayed_verdict": source_host_verdict,
            "stored_verdict": row["final_verdict"],
            "replayed_budget_eligible": budget,
            "stored_budget_eligible": row["budget_eligible"].casefold() == "true",
            "discrepancies": sorted(set(row_errors)),
            "source_verified": not row_errors,
        })

    by_identity = {(r["nickname"], r["obj"]): r for r in registry}
    duplicate_results = []
    duplicate_rows = read_csv_text(texts["duplicates"])
    expected_duplicate_mappings = {
        ("casey", "795", "192821699728654764"),
        ("casey", "824", "192821700026167542"),
        ("casey", "827", "192831699797402822"),
        ("phineas", "832", "194021777634832653"),
        ("phineas", "1153", "194041777780157594"),
        ("phineas", "1190", "194051777813062524"),
        ("whitney", "1472", "196191347354360083"),
    }
    actual_duplicate_mappings = {
        (r["nickname"], r["duplicate_obj"], r["canonical_obj"]) for r in duplicate_rows
    }
    if len(duplicate_rows) != 7 or actual_duplicate_mappings != expected_duplicate_mappings:
        errors.append("duplicate mapping set differs from the exact seven-row contract")
    for item in duplicate_rows:
        left = by_identity[(item["nickname"], item["duplicate_obj"])]
        right = by_identity[(item["nickname"], item["canonical_obj"])]
        actual = separation_arcsec(
            float(left["ra_deg"]), float(left["dec_deg"]),
            float(right["ra_deg"]), float(right["dec_deg"]),
        )
        ok = (
            round(actual, 2) == float(item["sep_arcsec"])
            and left["best_z"] == right["best_z"]
            and left["final_verdict"] == right["final_verdict"]
            and (item["nickname"], left["type"], left["obj"]) in provenance_by_key
            and (item["nickname"], right["type"], right["obj"]) in provenance_by_key
        )
        if not ok:
            errors.append(f"duplicate replay mismatch: {item['nickname']}/{item['duplicate_obj']}")
        duplicate_results.append({
            "nickname": item["nickname"], "duplicate_obj": item["duplicate_obj"],
            "canonical_obj": item["canonical_obj"], "separation_arcsec": actual, "ok": ok,
        })

    discrepancy_rows = [r for r in row_results if r["discrepancies"]]
    host_statuses = Counter(r["host_status"] for r in row_results)
    candidate_statuses = Counter(r["candidate_source_status"] for r in row_results)
    verdict_mismatches = [r["key"] for r in row_results if r["replayed_verdict"] != r["stored_verdict"]]
    budget_mismatches = [r["key"] for r in row_results if r["replayed_budget_eligible"] != r["stored_budget_eligible"]]
    authoritative_host_verdict_changes = [
        r["key"] for r in row_results
        if r["authoritative_host_replayed_verdict"] is not None
        and r["authoritative_host_replayed_verdict"] != r["stored_verdict"]
    ]
    if len(row_results) != 52:
        errors.append(f"only {len(row_results)} rows replayed")
    if verdict_mismatches or budget_mismatches:
        errors.append("stored verdict or budget arithmetic mismatch")

    return {
        "schema_version": 1,
        "analysis_base_commit": analysis_commit,
        "pipeline_commit": pipeline_commit,
        "independence": "standard-library offline replay; no pipeline producer or adjudicator imported",
        "input_blobs": blobs,
        "input_sha256": {name: hashlib.sha256(text.encode()).hexdigest() for name, text in texts.items()},
        "rows": len(row_results),
        "source_verified_rows": sum(r["source_verified"] for r in row_results),
        "rows_with_discrepancies": len(discrepancy_rows),
        "host_status_counts": dict(sorted(host_statuses.items())),
        "candidate_status_counts": dict(sorted(candidate_statuses.items())),
        "verdict_mismatches": verdict_mismatches,
        "budget_mismatches": budget_mismatches,
        "authoritative_host_verdict_changes": authoritative_host_verdict_changes,
        "duplicate_checks": duplicate_results,
        "row_results": row_results,
        "errors": errors,
        "gate_pass": not errors and not discrepancy_rows,
        "disposition": "pass" if not errors and not discrepancy_rows else "fail_closed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pipeline-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--pipeline-commit", default=EXPECTED_PIPELINE_COMMIT)
    parser.add_argument("--analysis-commit", default=EXPECTED_ANALYSIS_COMMIT)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = verify(
        root,
        args.pipeline_dir.resolve(),
        analysis_commit=args.analysis_commit,
        pipeline_commit=args.pipeline_commit,
    )
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    return 0 if result["gate_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
