"""Deterministic registry-to-mNFW propagation authority.

Only budget-eligible, confirmed registry rows are admitted. Cross-catalog
duplicates are resolved by the adjudicated duplicate table before geometry or
dispersion calculations. Sky coordinates, not legacy physical impacts, define
the impact parameter at each redshift.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

from foregrounds.census.config import COSMO
from foregrounds.propagation import scattering_predict

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "foregrounds/census/data/intervening_census_registry.csv"
EXPANDED = ROOT / "foregrounds/census/data/expanded_catalog_cross_references.csv"
BURSTS = ROOT / "foregrounds/census/data/frozen_census/bursts.csv"
DUPLICATES = ROOT / "foregrounds/census/data/census_masses/census_duplicates.csv"
CROSSING_INPUT = ROOT / "scripts/phineas_halo_crossing_inputs.csv"
CROSSING_RESULT = ROOT / "scripts/phineas_halo_crossing_probability.json"
COMPATIBILITY_CSV = ROOT / "scripts/dm_budget_intervening_systems.csv"
OUTPUT_DIR = ROOT / "foregrounds/results/propagation"
SYSTEMS_JSON = OUTPUT_DIR / "intervening_systems.json"
RECEIPT_JSON = OUTPUT_DIR / "intervening_receipt.json"


@dataclass(frozen=True)
class System:
    tns: str
    nickname: str
    object: str
    kind: str
    mass_source: str
    model: str
    z: float
    z_sigma: float
    theta_arcsec: float
    impact_kpc: float
    mass_msun: float
    mass_sigma_dex: float | None
    dm_point: float | None
    uncertainty_flags: str


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def angular_separation(ra1: float, dec1: float, ra2: float, dec2: float) -> float:
    values = map(math.radians, (ra1, dec1, ra2, dec2))
    ra1r, dec1r, ra2r, dec2r = values
    haversine = (
        math.sin(0.5 * (dec2r - dec1r)) ** 2
        + math.cos(dec1r) * math.cos(dec2r) * math.sin(0.5 * (ra2r - ra1r)) ** 2
    )
    return 2.0 * math.asin(math.sqrt(min(1.0, max(0.0, haversine))))


def build_systems() -> tuple[tuple[System, ...], tuple[dict, ...]]:
    duplicate_to_canonical = {
        (row["nickname"], row["duplicate_obj"]): row["canonical_obj"] for row in _rows(DUPLICATES)
    }
    bursts = {row["nickname"]: row for row in _rows(BURSTS)}
    expanded = {(row["nickname"], row["object_id"]): row for row in _rows(EXPANDED)}
    crossing_objects = set(json.loads(CROSSING_RESULT.read_text())["halos"])
    systems: list[System] = []
    dispositions: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for row in _rows(REGISTRY):
        if row["budget_eligible"] != "True" or row["final_verdict"] != "confirmed":
            continue
        key = (row["nickname"], row["obj"])
        canonical = duplicate_to_canonical.get(key, row["obj"])
        if canonical != row["obj"]:
            dispositions.append(
                {
                    "nickname": row["nickname"],
                    "object": row["obj"],
                    "status": "deduplicated",
                    "canonical_object": canonical,
                }
            )
            continue
        identity = (row["tns"], canonical)
        if identity in seen:
            raise ValueError(f"duplicate admitted system {identity}")
        seen.add(identity)
        burst = bursts[row["nickname"]]
        theta = angular_separation(
            float(burst["ra_deg"]),
            float(burst["dec_deg"]),
            float(row["ra_deg"]),
            float(row["dec_deg"]),
        )
        z = float(row["best_z"])
        z_sigma = float(row["best_z_err"] or 0.0)
        impact = theta * COSMO.angular_diameter_distance(z).to_value("kpc")
        if row["type"] == "cluster":
            mass = float(row["m500_1e14msun"]) * 1e14
            dm = scattering_predict.dm_cluster_mnfw_model(mass, z, impact)
            system = System(
                row["tns"],
                row["nickname"],
                canonical,
                "cluster",
                "cluster_catalog",
                "cluster_conditional",
                z,
                z_sigma,
                math.degrees(theta) * 3600.0,
                impact,
                mass,
                0.20,
                float(dm) if dm is not None else None,
                "mass scatter modeled; profile choice conditional",
            )
        else:
            evidence = expanded.get((row["nickname"], canonical))
            if evidence is None or not evidence["m200c_msun"]:
                dispositions.append(
                    {
                        "nickname": row["nickname"],
                        "object": canonical,
                        "status": "omitted_missing_mass",
                    }
                )
                continue
            mass = float(evidence["m200c_msun"])
            dm = scattering_predict.dm_halo_mnfw(mass, z, impact)
            if canonical not in crossing_objects and (dm is None or dm <= 0.0):
                dispositions.append(
                    {
                        "nickname": row["nickname"],
                        "object": canonical,
                        "status": "omitted_no_central_mnfw_crossing",
                    }
                )
                continue
            system = System(
                row["tns"],
                row["nickname"],
                canonical,
                "galaxy",
                "measured",
                "probabilistic_crossing"
                if canonical in crossing_objects
                else "redshift_marginalized_lognormal",
                z,
                z_sigma,
                math.degrees(theta) * 3600.0,
                impact,
                mass,
                None,
                float(dm) if dm is not None else None,
                (
                    "photo-z and photometry propagated by crossing producer"
                    if canonical in crossing_objects
                    else "photo-z modeled; mass uncertainty unavailable; profile width assumed"
                ),
            )
        systems.append(system)
    systems.sort(key=lambda item: (item.tns, item.kind, item.object))
    return tuple(systems), tuple(dispositions)


FIELDS = tuple(System.__dataclass_fields__)


def _stable_system(system: System) -> dict:
    """Serialize beyond scientific precision, independent of math-library noise."""
    return {
        key: round(value, 9) if isinstance(value, float) else value
        for key, value in asdict(system).items()
    }


def render() -> dict[Path, str]:
    systems, dispositions = build_systems()
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    for system in systems:
        writer.writerow(_stable_system(system))
    csv_text = stream.getvalue()
    payload = {
        "schema_version": 1,
        "status": "diagnostic_not_science_admitted",
        "systems": [_stable_system(system) for system in systems],
        "dispositions": list(dispositions),
    }
    json_text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    outputs = {COMPATIBILITY_CSV: csv_text, SYSTEMS_JSON: json_text}
    receipt = {
        "schema_version": 1,
        "inputs": {
            str(path.relative_to(ROOT)): sha256(path)
            for path in (
                REGISTRY,
                EXPANDED,
                BURSTS,
                DUPLICATES,
                CROSSING_INPUT,
                CROSSING_RESULT,
            )
        },
        "outputs": {
            str(path.relative_to(ROOT)): hashlib.sha256(text.encode()).hexdigest()
            for path, text in outputs.items()
        },
        "producer": sha256(Path(__file__)),
        "checks": {
            "unique_system_identity": True,
            "coordinate_geometry": True,
            "registry_admission": "budget_eligible and confirmed",
        },
    }
    outputs[RECEIPT_JSON] = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    return outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    outputs = render()
    if args.check:
        drift = [
            path
            for path, expected in outputs.items()
            if not path.is_file() or path.read_text() != expected
        ]
        if drift:
            raise SystemExit("DRIFT: " + ", ".join(map(str, drift)))
        print(f"OK: {len(outputs)} propagation authority artifacts")
        return 0
    for path, text in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
