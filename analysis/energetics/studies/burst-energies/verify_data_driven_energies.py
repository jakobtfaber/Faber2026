#!/usr/bin/env python3
"""Independent verifier for the fit-independent energy artifact."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path

import astropy.units as u
from astropy.cosmology import Planck18

CONVERSION = 1e-22
FORBIDDEN = {"c0", "gamma", "alpha", "beta", "tau", "fit", "posterior"}
EXPECTED_RESULTS = {
    "chromatica", "hamilton", "isha", "johndoeii",
    "oran", "phineas", "whitney", "zach",
}
EXPECTED_EXCLUDED = {"casey", "freya", "mahi", "wilhelm"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
REPO = Path(__file__).resolve().parents[3]


def verify(path: Path) -> None:
    artifact = json.loads(path.read_text())
    text_keys = " ".join(_walk_keys(artifact)).lower()
    found = sorted(word for word in FORBIDDEN if word in text_keys)
    if found:
        raise ValueError(f"fit-dependent fields present: {found}")
    receipt = Path(artifact["fluence_receipt"])
    if not receipt.is_file():
        raise ValueError(f"fluence receipt missing: {receipt}")
    if _sha256(receipt) != artifact["fluence_receipt_sha256"]:
        raise ValueError("fluence receipt SHA-256 mismatch")
    receipts = _load_receipts(receipt)
    roster = _load_roster()
    results = artifact["results"]
    dispositions = artifact["dispositions"]
    result_names = [row["nickname"] for row in results]
    excluded_names = [row["nickname"] for row in dispositions]
    if len(result_names) != len(set(result_names)) or set(result_names) != EXPECTED_RESULTS:
        raise ValueError("result roster mismatch or duplicate")
    if len(excluded_names) != len(set(excluded_names)) or set(excluded_names) != EXPECTED_EXCLUDED:
        raise ValueError("excluded roster mismatch or duplicate")
    for row in artifact["results"]:
        expected_meta = roster[row["nickname"]]
        _check_roster_metadata(row, expected_meta)
        if row["status"] != "calculated_not_manuscript_admitted":
            raise ValueError(f"invalid calculation status: {row['nickname']}")
        if set(row["bands"]) != {"CHIME", "DSA"}:
            raise ValueError(f"required bands missing: {row['nickname']}")
        z = float(row["redshift"])
        distance_m = Planck18.luminosity_distance(z).to(u.m).value
        prefactor = 4.0 * 3.141592653589793 * distance_m**2 * CONVERSION / (1.0 + z)
        expected = 0.0
        variance = 0.0
        for band, band_row in row["bands"].items():
            receipt_row = receipts[(row["nickname"], band)]
            for key in ("input_sha256", "calibration_sha256"):
                if band_row[key] != receipt_row[key] or not SHA256_RE.fullmatch(band_row[key]):
                    raise ValueError(f"{key} mismatch: {row['nickname']} {band}")
            if band_row["input_path"] != receipt_row["input_path"]:
                raise ValueError(f"input path mismatch: {row['nickname']} {band}")
            if band_row["calibration_paths"] != receipt_row["calibration_paths"]:
                raise ValueError(f"calibration paths mismatch: {row['nickname']} {band}")
            fluence = float(receipt_row["fluence_jy_ms_hz"])
            stat = float(receipt_row["stat_err_jy_ms_hz"])
            if not all(math.isfinite(value) and value > 0 for value in (fluence, stat)):
                raise ValueError(f"invalid receipt numeric: {row['nickname']} {band}")
            if abs(float(band_row["fluence_jy_ms_hz"]) - fluence) > 1e-12 * fluence:
                raise ValueError(f"fluence mismatch: {row['nickname']} {band}")
            if abs(float(band_row["stat_err_jy_ms_hz"]) - stat) > 1e-12 * stat:
                raise ValueError(f"statistical error mismatch: {row['nickname']} {band}")
            band_energy = prefactor * fluence
            if abs(float(band_row["energy_erg"]) - band_energy) > 1e-12 * band_energy:
                raise ValueError(f"band energy mismatch: {row['nickname']} {band}")
            expected += band_energy
            variance += (prefactor * stat) ** 2
        if abs(expected - row["energy_erg"]) > 1e-12 * expected:
            raise ValueError(f"energy mismatch: {row['nickname']}")
        expected_stat = variance**0.5
        if abs(expected_stat - row["stat_err_erg"]) > 1e-12 * expected_stat:
            raise ValueError(f"statistical error mismatch: {row['nickname']}")
    for row in dispositions:
        _check_roster_metadata(row, roster[row["nickname"]])
        if row["status"] != "excluded":
            raise ValueError(f"invalid exclusion status: {row['nickname']}")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_receipts(path: Path) -> dict[tuple[str, str], dict]:
    rows = {}
    with path.open() as handle:
        for row in csv.DictReader(handle):
            key = (row["nickname"].lower(), row["band"])
            if key in rows:
                raise ValueError(f"duplicate receipt: {key}")
            if key[0] not in EXPECTED_RESULTS or key[1] not in {"CHIME", "DSA"}:
                raise ValueError(f"unexpected accepted receipt: {key}")
            for field in (
                "window_status", "calibration_status", "noise_status", "review_status"
            ):
                if row[field] != "accepted":
                    raise ValueError(f"receipt not accepted: {key} {field}")
            sensitivity = float(row["window_sensitivity_frac"])
            if not math.isfinite(sensitivity) or not 0 <= sensitivity <= 0.10:
                raise ValueError(f"invalid window sensitivity: {key}")
            input_path = Path(row["input_path"])
            if not input_path.is_file() or _sha256(input_path) != row["input_sha256"]:
                raise ValueError(f"input file missing or SHA-256 mismatch: {key}")
            calibration_paths = [Path(item) for item in row["calibration_paths"].split(";")]
            if (
                not calibration_paths
                or not all(item.is_file() for item in calibration_paths)
                or _calibration_sha256(calibration_paths) != row["calibration_sha256"]
            ):
                raise ValueError(f"calibration files missing or SHA-256 mismatch: {key}")
            rows[key] = row
    expected = {(nick, band) for nick in EXPECTED_RESULTS for band in ("CHIME", "DSA")}
    if set(rows) != expected:
        raise ValueError("accepted receipt roster/bands incomplete")
    return rows


def _calibration_sha256(paths: list[Path]) -> str:
    hasher = hashlib.sha256()
    for path in paths:
        hasher.update(path.name.encode())
        hasher.update(bytes.fromhex(_sha256(path)))
    return hasher.hexdigest()


def _load_roster() -> dict[str, dict]:
    sample = EXPECTED_RESULTS | EXPECTED_EXCLUDED
    roster = {
        nick: {
            "nickname": nick, "redshift": None, "measurement_kind": "missing",
            "redshift_source": None, "eligible": False,
            "exclusion_reason": "no spectroscopic host redshift",
        }
        for nick in sample
    }
    frozen = (
        REPO
        / "foregrounds"
        / "census"
        / "data"
        / "frozen_census"
    )
    with (frozen / "law2024_host_redshift_extract.csv").open() as handle:
        for source in csv.DictReader(handle):
            nick = source["mapped_nickname"].lower()
            roster[nick].update(
                redshift=float(source["adopted_redshift"]),
                measurement_kind=source["measurement_kind"],
                redshift_source="Law2024 Table 3",
                eligible=source["measurement_kind"] == "spectroscopic",
                exclusion_reason="",
            )
    published = {"zach", "whitney", "oran", "isha", "phineas"}
    provisional = {"johndoeii", "hamilton", "chromatica"}
    with (frozen / "verdi2025_host_redshift_extract.csv").open() as handle:
        for source in csv.DictReader(handle):
            nick = source["mapped_nickname"].lower()
            if not source["redshift"]:
                continue
            if nick == "casey":
                kind = "photometric"
            elif nick in provisional:
                kind = "spectroscopic_provisional"
            elif nick in published:
                kind = "spectroscopic"
            else:
                raise ValueError(f"unadjudicated redshift source: {nick}")
            roster[nick].update(
                redshift=float(source["redshift"]),
                measurement_kind=kind,
                redshift_source="Verdi et al. owner-adopted draft extract",
                eligible=kind != "photometric",
                exclusion_reason="" if kind != "photometric" else "photometric redshift only",
            )
    return roster


def _check_roster_metadata(row: dict, expected: dict) -> None:
    for key in (
        "nickname", "redshift", "measurement_kind", "redshift_source",
        "eligible", "exclusion_reason",
    ):
        if row.get(key) != expected[key]:
            raise ValueError(f"roster metadata mismatch: {row['nickname']} {key}")


def _walk_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path)
    args = parser.parse_args()
    verify(args.artifact)
    print(f"verified {args.artifact}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
