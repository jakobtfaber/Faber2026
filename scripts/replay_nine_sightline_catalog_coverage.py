#!/usr/bin/env python3
"""Replay the nine-sightline foreground-catalog audit.

Offline mode is a standard-library-only, independent replay of registry scope,
verdict and budget arithmetic, duplicate separations, and the repaired
four-catalog status counts. Live mode additionally calls the existing pipeline
source adapters and compares their selected source identities and hashes with
the candidate-redshift ledger. That live check is deliberately labelled
non-independent: it reuses the adapters that created the ledger and is not the
expanded full-region search required by the Wayfinder ticket.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import platform
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

EXPECTED_INPUT_SHA256 = {
    "intervening_census_registry.csv": "8e1998fd41b42e982cb2cdf4967e69eb028df1037caa1cf061578bb6ec2cab97",
    "candidate_redshift_provenance.csv": "ccc8427786455d498bfd668c878ef0395fbb143a1f2f0939630e5fec68138803",
    "bursts.csv": "204fb79727ff71f15269f3d5564215e34d8f027aedbd82719dfda162bdcfb644",
    "foreground.csv": "38ed01ac7561eddcbd33500e2fabeeb4130c22c4fdca791967415656a4d0cd15",
    "foreground_validated.csv": "c18fa388cd421d6a90e65b77edceca00afe9c8a9e4cc7feb31a52f468c6e79d7",
    "foreground_final.csv": "ce14b474424efb5ff442c5206020609475ff7b0675aa370cb026a47cc8ff4766",
    "ps1_strm_resolution.csv": "f3dbb32e590f9d5b953919e6de2b9e9473b3ccda36492e7010ee0fd557daf8b7",
    "strm_catalog_rows.csv": "42e576a234ac9ab471b695e89b6f25c3ad6875e1914c8ccb3ee518739fd04870",
    "v4_extension.csv": "c3284c954040cfa0d9363944336118b30f33249ab30e81eeac010d7d7e3817ed",
    "census_duplicates.csv": "336e4023dbf046762477c724e57365c29a3ecabb982f6978e635fb0d05d47e45",
    "expanded_catalog_cross_references.csv": "17ef142bc5d57f0f1f42d11a397c084de2b9763fbb7543ce82e90e1a6d6ef727",
}

OBSERVED_RESPONSE_DRIFT_KEYS = [
    "casey/cluster/J112235.5+705438, 1239515",
    "phineas/cluster/J114928.5+712526, 1253366",
    "phineas/cluster/J114944.0+714348, 1253496",
    "phineas/cluster/J115128.2+713637, 1254415",
    "phineas/cluster/J115400.9+713320, 1255773",
    "phineas/cluster/J115436.9+713930, 1256077",
    "whitney/cluster/J085808.2+731234, 1161367",
]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _finite(value: str | None) -> bool:
    if value is None or value.strip() == "":
        return False
    try:
        return math.isfinite(float(value))
    except ValueError:
        return False


def _as_bool(value: str) -> bool:
    return value.strip().lower() == "true"


def _key(row: dict[str, str]) -> str:
    return f"{row['nickname']}/{row['type']}/{row['obj']}"


def _git_metadata(repo: Path) -> dict[str, Any]:
    def run(*args: str) -> str:
        result = subprocess.run(
            ["git", *args], cwd=repo, check=True, capture_output=True, text=True
        )
        return result.stdout.strip()

    status_lines = run("status", "--short").splitlines()

    def status_path(line: str) -> str:
        # Standard porcelain has two status columns plus a space. Some local
        # output filters compact a clean index column to ``M path``.
        if len(line) >= 3 and line[2] == " ":
            return line[3:]
        parts = line.split(maxsplit=1)
        return parts[1] if len(parts) == 2 else line

    return {
        "head": run("rev-parse", "HEAD"),
        "dirty_paths": [status_path(line) for line in status_lines],
    }


def _paths(pipeline_dir: Path) -> dict[str, Path]:
    data = pipeline_dir / "galaxies" / "foreground" / "data"
    frozen = data / "frozen_census"
    return {
        "intervening_census_registry.csv": data / "intervening_census_registry.csv",
        "candidate_redshift_provenance.csv": data / "candidate_redshift_provenance.csv",
        "bursts.csv": frozen / "bursts.csv",
        "foreground.csv": frozen / "foreground.csv",
        "foreground_validated.csv": frozen / "foreground_validated.csv",
        "foreground_final.csv": frozen / "foreground_final.csv",
        "ps1_strm_resolution.csv": frozen / "ps1_strm_resolution.csv",
        "strm_catalog_rows.csv": frozen / "strm_catalog_rows.csv",
        "v4_extension.csv": data / "census_extensions" / "v4_extension.csv",
        "census_duplicates.csv": data / "census_masses" / "census_duplicates.csv",
        "expanded_catalog_cross_references.csv": data / "expanded_catalog_cross_references.csv",
    }


def _replay_verdict(
    row: dict[str, str], strm_by_obj: dict[str, dict[str, str]]
) -> str:
    if not _finite(row["best_z"]):
        return "inconclusive"
    if row["obj"] in strm_by_obj:
        strm = strm_by_obj[row["obj"]]
        if strm["strm_class"] != "GALAXY" or strm["strm_extrapolated"] == "1.0":
            return "inconclusive"
    z = float(row["best_z"])
    host_z = float(row["host_z_spec"])
    source = row["best_z_source"]
    secure = any(name in source for name in ("DESI", "NED", "WHL12"))
    if secure or not _finite(row["best_z_err"]):
        return "confirmed" if z < host_z else "refuted"
    error = float(row["best_z_err"])
    if z + error < host_z:
        return "confirmed"
    if z - error > host_z:
        return "refuted"
    return "inconclusive"


def _replay_budget(row: dict[str, str], verdict: str) -> bool:
    if verdict != "confirmed":
        return False
    if row["type"] == "halo":
        return True
    return _finite(row["b_over_r500"]) and float(row["b_over_r500"]) <= 1.0


def _haversine_arcsec(a: dict[str, str], b: dict[str, str]) -> float:
    dec1 = math.radians(float(a["dec_deg"]))
    dec2 = math.radians(float(b["dec_deg"]))
    delta_ra = math.radians(float(b["ra_deg"]) - float(a["ra_deg"]))
    delta_dec = dec2 - dec1
    h = (
        math.sin(delta_dec / 2.0) ** 2
        + math.cos(dec1) * math.cos(dec2) * math.sin(delta_ra / 2.0) ** 2
    )
    return 2.0 * math.asin(math.sqrt(h)) * 206264.80624709636


def offline_replay(repo: Path, pipeline_dir: Path) -> tuple[dict[str, Any], bool]:
    paths = _paths(pipeline_dir)
    actual_hashes = {name: _sha256(path) for name, path in paths.items()}
    hash_mismatches = {
        name: {"expected": EXPECTED_INPUT_SHA256[name], "actual": digest}
        for name, digest in actual_hashes.items()
        if digest != EXPECTED_INPUT_SHA256[name]
    }

    registry_all = _read_csv(paths["intervening_census_registry.csv"])
    registry = [row for row in registry_all if _finite(row["host_z_spec"])]
    registry_by_key = {(row["nickname"], row["obj"]): row for row in registry}
    strm_by_obj = {
        row["obj"]: row for row in _read_csv(paths["ps1_strm_resolution.csv"])
    }

    verdict_rows = []
    for row in registry:
        replay_verdict = _replay_verdict(row, strm_by_obj)
        replay_budget = _replay_budget(row, replay_verdict)
        verdict_rows.append(
            {
                "key": _key(row),
                "verdict_match": replay_verdict == row["final_verdict"],
                "budget_match": replay_budget == _as_bool(row["budget_eligible"]),
            }
        )

    duplicates = []
    for duplicate in _read_csv(paths["census_duplicates.csv"]):
        left = registry_by_key[(duplicate["nickname"], duplicate["duplicate_obj"])]
        right = registry_by_key[(duplicate["nickname"], duplicate["canonical_obj"])]
        replay_sep = _haversine_arcsec(left, right)
        duplicates.append(
            {
                "key": (
                    f"{duplicate['nickname']}/{duplicate['duplicate_obj']}=>"
                    f"{duplicate['canonical_obj']}"
                ),
                "stored_sep_arcsec": float(duplicate["sep_arcsec"]),
                "replay_sep_arcsec": replay_sep,
                "rounded_separation_match": round(replay_sep, 2)
                == float(duplicate["sep_arcsec"]),
                "redshift_match": left["best_z"] == right["best_z"],
                "verdict_match": left["final_verdict"] == right["final_verdict"],
            }
        )

    ledger_all = _read_csv(paths["candidate_redshift_provenance.csv"])
    scoped_keys = {_key(row) for row in registry}
    ledger = [row for row in ledger_all if _key(row) in scoped_keys]
    adopted_ledger = [row for row in ledger if _finite(row["adopted_z"])]
    no_redshift_ledger = [row for row in ledger if not _finite(row["adopted_z"])]
    ledger_presence = {
        "scoped_rows": len(ledger),
        "adopted_redshift_rows": len(adopted_ledger),
        "no_adopted_redshift_rows": len(no_redshift_ledger),
        "adopted_rows_with_stable_id": sum(
            row["stable_source_id"] not in ("", "not_applicable") for row in adopted_ledger
        ),
        "adopted_rows_with_source_row_sha256": sum(
            row["source_row_sha256"] not in ("", "not_applicable")
            for row in adopted_ledger
        ),
        "independence": (
            "presence-only; source identities and hashes cannot be independently "
            "verified offline because raw source responses are not frozen"
        ),
    }

    expanded = [
        row
        for row in _read_csv(paths["expanded_catalog_cross_references.csv"])
        if row["nickname"] in {item["nickname"] for item in registry}
    ]
    catalog_counts = {
        catalog: dict(sorted(Counter(row[f"{catalog}_status"] for row in expanded).items()))
        for catalog in ("gsc242", "allwise", "catwise2020", "unwise")
    }

    verdict_counts = dict(sorted(Counter(row["final_verdict"] for row in registry).items()))
    result = {
        "mode": "offline",
        "runtime": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "randomness": "none",
            "accelerator": "none",
        },
        "code": _git_metadata(repo),
        "inputs_sha256": actual_hashes,
        "input_hash_mismatches": hash_mismatches,
        "scope": {
            "registry_rows_all": len(registry_all),
            "finite_host_redshift_rows": len(registry),
            "sightlines": sorted({row["nickname"] for row in registry}),
        },
        "candidate_ledger": ledger_presence,
        "verdict_budget": {
            "stored_verdict_counts": verdict_counts,
            "verdict_mismatches": [row["key"] for row in verdict_rows if not row["verdict_match"]],
            "budget_true": sum(_as_bool(row["budget_eligible"]) for row in registry),
            "budget_mismatches": [row["key"] for row in verdict_rows if not row["budget_match"]],
        },
        "duplicates": duplicates,
        "expanded_four_catalog_status_counts": catalog_counts,
        "search_contract": {
            "full_recorded_sightline_region_executable": False,
            "reason": (
                "the original frozen discovery cone or aperture was never recorded; "
                "there is no uniform full-region query definition to replay"
            ),
        },
    }
    ok = (
        not hash_mismatches
        and len(registry) == 50
        and len(ledger) == 50
        and len(adopted_ledger) == 44
        and len(no_redshift_ledger) == 6
        and not result["verdict_budget"]["verdict_mismatches"]
        and not result["verdict_budget"]["budget_mismatches"]
        and all(item["rounded_separation_match"] for item in duplicates)
        and all(item["redshift_match"] and item["verdict_match"] for item in duplicates)
        and len(expanded) == 50
    )
    result["ok"] = ok
    return result, ok


def live_identity_replay(pipeline_dir: Path) -> tuple[dict[str, Any], bool]:
    """Reuse ledger-producing adapters; this is an identity check, not an independent search."""
    module_path = pipeline_dir / "galaxies" / "foreground" / "freeze_candidate_redshift_provenance.py"
    spec = importlib.util.spec_from_file_location("candidate_source_freezer", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    pandas = module.pd
    registry = pandas.read_csv(module.REGISTRY)
    registry = registry[registry.host_z_spec.notna()]
    ledger = pandas.read_csv(module.OUT)
    ledger = ledger[ledger.nickname.isin(set(registry.nickname))]
    ledger_by_key = {
        (str(row.nickname), str(row.type), str(row.obj)): row
        for row in ledger.itertuples(index=False)
    }
    strm_rows = pandas.read_csv(module.STRM).to_dict("records")
    strm_by_obj = {str(row["objID"]): row for row in strm_rows}

    comparisons = []
    for row in registry.itertuples(index=False):
        key_tuple = (str(row.nickname), str(row.type), str(row.obj))
        key = "/".join(key_tuple)
        comparison: dict[str, Any] = {"key": key}
        try:
            actual = module._source_for(row, None, strm_by_obj)
            expected = ledger_by_key[key_tuple]
            for field in (
                "source_family",
                "source_release",
                "stable_source_id",
                "source_row_sha256",
                "query_response_sha256",
                "measurement_kind",
            ):
                comparison[f"{field}_match"] = str(actual[field]) == str(
                    getattr(expected, field)
                )
            comparison["status"] = "replayed"
        except Exception as exc:  # network/service errors must remain visible
            comparison["status"] = "error"
            comparison["error"] = f"{type(exc).__name__}: {exc}"
        comparisons.append(comparison)

    errors = [item for item in comparisons if item["status"] == "error"]
    adopted = [
        item
        for item in comparisons
        if ledger_by_key[tuple(item["key"].split("/", 2))].adopted_z
        == ledger_by_key[tuple(item["key"].split("/", 2))].adopted_z
    ]
    selected_identity_mismatches = [
        item["key"]
        for item in adopted
        if item["status"] == "replayed"
        and not all(
            item[field]
            for field in (
                "source_family_match",
                "source_release_match",
                "stable_source_id_match",
                "source_row_sha256_match",
                "measurement_kind_match",
            )
        )
    ]
    response_drifts = sorted(
        item["key"]
        for item in adopted
        if item["status"] == "replayed" and not item["query_response_sha256_match"]
    )
    match_counts = {
        field: sum(
            item["status"] == "replayed" and bool(item[field]) for item in adopted
        )
        for field in (
            "stable_source_id_match",
            "source_row_sha256_match",
            "query_response_sha256_match",
        )
    }
    result = {
        "mode": "live",
        "independence": (
            "not independent: reuses freeze_candidate_redshift_provenance.py adapters; "
            "does not execute the ticket's expanded full-region search"
        ),
        "calls": len(comparisons),
        "errors": errors,
        "adopted_redshift_rows": len(adopted),
        "adopted_row_match_counts": match_counts,
        "selected_identity_mismatches": selected_identity_mismatches,
        "response_hash_drifts": response_drifts,
        "observed_2026_07_22_response_hash_drifts": OBSERVED_RESPONSE_DRIFT_KEYS,
        "matches_observed_drift_set": response_drifts == OBSERVED_RESPONSE_DRIFT_KEYS,
    }
    ok = not errors and len(adopted) == 44 and not selected_identity_mismatches
    result["ok"] = ok
    return result, ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("offline", "live"), default="offline")
    parser.add_argument(
        "--pipeline-dir",
        type=Path,
        default=None,
        help="Pinned pipeline checkout; defaults to REPO/pipeline.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional JSON output path; stdout is always emitted.",
    )
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    pipeline_dir = (args.pipeline_dir or repo / "pipeline").resolve()
    if args.mode == "offline":
        result, ok = offline_replay(repo, pipeline_dir)
    else:
        result, ok = live_identity_replay(pipeline_dir)

    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    sys.stdout.write(payload)
    if args.output is not None:
        args.output.write_text(payload, encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
