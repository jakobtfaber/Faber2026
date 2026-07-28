"""Pure, fit-independent energetics calculation and roster loading."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from pathlib import Path

import astropy.units as u
from astropy.cosmology import Planck18

JY_MS_HZ_TO_ERG_M2 = 1e-22
PLACEHOLDER_Z = 1.0
SAMPLE = (
    "casey", "chromatica", "freya", "hamilton", "isha", "johndoeii",
    "mahi", "oran", "phineas", "whitney", "wilhelm", "zach",
)
PUBLISHED_SPECTROSCOPIC = {"zach", "whitney", "oran", "isha", "phineas"}
PROVISIONAL_SPECTROSCOPIC = {"johndoeii", "hamilton", "chromatica"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def calibration_sha256(paths: list[Path]) -> str:
    hasher = hashlib.sha256()
    for path in paths:
        hasher.update(path.name.encode())
        hasher.update(bytes.fromhex(sha256(path)))
    return hasher.hexdigest()


def load_energy_roster(repo: Path) -> dict[str, dict]:
    """Load the 12-event roster from frozen redshift-source extracts."""
    frozen = repo / "campaigns" / "foregrounds" / "data" / "frozen_census"
    roster = {
        nick: {
            "nickname": nick,
            "redshift": None,
            "measurement_kind": "missing",
            "redshift_source": None,
            "eligible": False,
            "exclusion_reason": "no spectroscopic host redshift",
        }
        for nick in SAMPLE
    }
    with (frozen / "law2024_host_redshift_extract.csv").open() as handle:
        for row in csv.DictReader(handle):
            nick = row["mapped_nickname"].lower()
            roster[nick].update(
                redshift=float(row["adopted_redshift"]),
                measurement_kind=row["measurement_kind"],
                redshift_source="Law2024 Table 3",
                eligible=row["measurement_kind"] == "spectroscopic",
                exclusion_reason="",
            )
    with (frozen / "verdi2025_host_redshift_extract.csv").open() as handle:
        for row in csv.DictReader(handle):
            nick = row["mapped_nickname"].lower()
            if not row["redshift"]:
                continue
            if nick == "casey":
                kind = "photometric"
            elif nick in PROVISIONAL_SPECTROSCOPIC:
                kind = "spectroscopic_provisional"
            elif nick in PUBLISHED_SPECTROSCOPIC:
                kind = "spectroscopic"
            else:
                raise ValueError(f"redshift kind not adjudicated for {nick}")
            roster[nick].update(
                redshift=float(row["redshift"]),
                measurement_kind=kind,
                redshift_source="Verdi et al. owner-adopted draft extract",
                eligible=kind != "photometric",
                exclusion_reason="" if kind != "photometric" else "photometric redshift only",
            )
    return roster


def energy_erg(fluence_jy_ms_hz: float, redshift: float) -> float:
    distance_m = Planck18.luminosity_distance(redshift).to(u.m).value
    return (
        4.0
        * 3.141592653589793
        * distance_m**2
        * fluence_jy_ms_hz
        * JY_MS_HZ_TO_ERG_M2
        / (1.0 + redshift)
    )


def load_accepted_fluences(path: Path) -> dict[tuple[str, str], dict]:
    required = {
        "nickname", "band", "fluence_jy_ms_hz", "stat_err_jy_ms_hz",
        "window_status", "window_sensitivity_frac", "calibration_status",
        "noise_status", "review_status", "input_sha256", "calibration_sha256",
        "input_path", "calibration_paths",
    }
    rows = {}
    with path.open() as handle:
        reader = csv.DictReader(handle)
        missing = required - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"fluence receipt missing columns: {sorted(missing)}")
        for row in reader:
            nick = row["nickname"].lower()
            band = row["band"]
            if nick not in SAMPLE:
                raise ValueError(f"fluence receipt has unknown event: {nick}")
            if band not in {"CHIME", "DSA"}:
                raise ValueError(f"fluence receipt has unknown band: {band}")
            key = (nick, band)
            if key in rows:
                raise ValueError(f"duplicate fluence receipt: {key}")
            numeric = {
                field: float(row[field])
                for field in (
                    "fluence_jy_ms_hz",
                    "stat_err_jy_ms_hz",
                    "window_sensitivity_frac",
                )
            }
            failures = []
            if not all(math.isfinite(value) for value in numeric.values()):
                failures.append("non-finite numeric field")
            if numeric["fluence_jy_ms_hz"] <= 0 or numeric["stat_err_jy_ms_hz"] <= 0:
                failures.append("fluence and statistical error must be positive")
            if row["window_status"] != "accepted":
                failures.append(f"window={row['window_status']}")
            if numeric["window_sensitivity_frac"] < 0 or numeric["window_sensitivity_frac"] > 0.10:
                failures.append("window sensitivity > 0.10")
            if row["calibration_status"] != "accepted":
                failures.append(f"calibration={row['calibration_status']}")
            if row["noise_status"] != "accepted":
                failures.append(f"noise={row['noise_status']}")
            if row["review_status"] != "accepted":
                failures.append(f"review={row['review_status']}")
            for field in ("input_sha256", "calibration_sha256"):
                if not SHA256_RE.fullmatch(row[field]):
                    failures.append(f"invalid {field}")
            input_path = Path(row["input_path"])
            calibration_paths = [Path(item) for item in row["calibration_paths"].split(";")]
            if not input_path.is_file() or sha256(input_path) != row["input_sha256"]:
                failures.append("input file missing or SHA-256 mismatch")
            if (
                not calibration_paths
                or not all(item.is_file() for item in calibration_paths)
                or calibration_sha256(calibration_paths) != row["calibration_sha256"]
            ):
                failures.append("calibration files missing or SHA-256 mismatch")
            if failures:
                raise ValueError(f"{key} not accepted: {', '.join(failures)}")
            rows[key] = row
    return rows


def build_artifact(repo: Path, fluence_path: Path) -> dict:
    roster = load_energy_roster(repo)
    fluences = load_accepted_fluences(fluence_path)
    expected_keys = {
        (nick, band)
        for nick, meta in roster.items()
        if meta["eligible"]
        for band in ("CHIME", "DSA")
    }
    extra = set(fluences) - expected_keys
    if extra:
        raise ValueError(f"accepted receipt contains ineligible/extra bands: {sorted(extra)}")
    results, dispositions = [], []
    for nick in SAMPLE:
        meta = roster[nick]
        if not meta["eligible"]:
            dispositions.append({**meta, "status": "excluded"})
            continue
        bands = []
        for band in ("CHIME", "DSA"):
            key = (nick, band)
            if key not in fluences:
                raise ValueError(f"eligible event missing accepted {band} fluence: {nick}")
            bands.append(fluences[key])
        z = float(meta["redshift"])
        band_rows = {}
        variance = 0.0
        for band, row in zip(("CHIME", "DSA"), bands, strict=True):
            fluence = float(row["fluence_jy_ms_hz"])
            stat = float(row["stat_err_jy_ms_hz"])
            e = energy_erg(fluence, z)
            band_rows[band] = {
                "fluence_jy_ms_hz": fluence,
                "stat_err_jy_ms_hz": stat,
                "energy_erg": e,
                "input_sha256": row["input_sha256"],
                "calibration_sha256": row["calibration_sha256"],
                "input_path": row["input_path"],
                "calibration_paths": row["calibration_paths"],
            }
            variance += energy_erg(stat, z) ** 2
        results.append(
            {
                **meta,
                "status": "calculated_not_manuscript_admitted",
                "bands": band_rows,
                "energy_erg": sum(v["energy_erg"] for v in band_rows.values()),
                "stat_err_erg": variance**0.5,
            }
        )
    return {
        "schema_version": 1,
        "estimator": "direct calibrated per-channel on-pulse fluence; no fitted parameters",
        "fluence_receipt": str(fluence_path),
        "fluence_receipt_sha256": sha256(fluence_path),
        "results": results,
        "dispositions": dispositions,
    }


def dump_artifact(artifact: dict, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2) + "\n")
