#!/usr/bin/env python3
"""Independent check of the Phineas owner-adjudicated foreground budget.

This module intentionally imports no project or astronomy packages.  It reads
the frozen CSV inputs, reimplements the geometry and published relations with
the Python standard library, and emits a machine-readable audit record.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


C_KM_S = 299_792.458
G_KPC_KM2_S2_MSUN = 4.300_917_270_036_28e-6
H0_KM_S_MPC = 67.66

# Planck 2018 values used by Astropy Planck18.  Massive neutrinos are treated
# as matter at these low redshifts; photons retain their (1+z)^4 scaling.
OMEGA_M = 0.30966
OMEGA_NU = 0.0014396743040845244
OMEGA_GAMMA = 5.402015137139353e-5
OMEGA_LAMBDA = 0.6888463055445441
OMEGA_B = 0.04897

MSUN_G = 1.988409870698051e33
KPC_CM = 3.085677581491367e21
PROTON_G = 1.67262192369e-24

# Inputs independently reviewed on 2026-07-22.  The validator must fail closed
# if a later pipeline checkout changes any source while preserving the same
# rounded budget total.
EXPECTED_INPUT_SHA256 = {
    "bursts": "204fb79727ff71f15269f3d5564215e34d8f027aedbd82719dfda162bdcfb644",
    "registry": "b45d698cde155427b272d0ead4c1a248303ef8c839ddcb84a0393adcdd1ae222",
    "masses": "3cea6b099d8238bea971e6289dfe5c729ac0da20470ae0678c9de558783d12a9",
    "duplicates": "336e4023dbf046762477c724e57365c29a3ecabb982f6978e635fb0d05d47e45",
    "overrides": "108a9ed842ec10c76ed281e87b58aca2c32bb2785fdcf2d2ef5082c809c76748",
    "method": "3df502e9244f8603f06336262e15d0f23aa6d52c858d4c4934fc1bbe741567bc",
    "budget": "e8ca970d48c06709ddc141182f5c61729f99ed1fa1f33cfbb00fdcd95111a90b",
}


def simpson(func, lo: float, hi: float, intervals: int = 8000) -> float:
    """Composite Simpson integral with a fixed, inspectable resolution."""
    if intervals <= 0 or intervals % 2:
        raise ValueError("intervals must be a positive even integer")
    if hi == lo:
        return 0.0
    step = (hi - lo) / intervals
    total = func(lo) + func(hi)
    for index in range(1, intervals):
        total += (4.0 if index % 2 else 2.0) * func(lo + index * step)
    return total * step / 3.0


def efunc(z: float) -> float:
    return math.sqrt(
        (OMEGA_M + OMEGA_NU) * (1.0 + z) ** 3
        + OMEGA_GAMMA * (1.0 + z) ** 4
        + OMEGA_LAMBDA
    )


def angular_diameter_distance_kpc(z: float) -> float:
    radial_mpc = C_KM_S / H0_KM_S_MPC * simpson(lambda value: 1.0 / efunc(value), 0.0, z)
    return radial_mpc * 1000.0 / (1.0 + z)


def luminosity_distance_kpc(z: float) -> float:
    return angular_diameter_distance_kpc(z) * (1.0 + z) ** 2


def angular_separation_rad(ra1: float, dec1: float, ra2: float, dec2: float) -> float:
    dec1_rad = math.radians(dec1)
    dec2_rad = math.radians(dec2)
    delta_dec = dec2_rad - dec1_rad
    delta_ra = math.radians(ra2 - ra1)
    haversine = (
        math.sin(delta_dec / 2.0) ** 2
        + math.cos(dec1_rad) * math.cos(dec2_rad) * math.sin(delta_ra / 2.0) ** 2
    )
    return 2.0 * math.asin(math.sqrt(haversine))


def impact_kpc(sight_ra: float, sight_dec: float, obj_ra: float, obj_dec: float, z: float) -> float:
    return angular_separation_rad(sight_ra, sight_dec, obj_ra, obj_dec) * angular_diameter_distance_kpc(z)


def moster_parameters(z: float, evolve_with_redshift: bool) -> tuple[float, float, float, float]:
    scale = z / (1.0 + z) if evolve_with_redshift else 0.0
    return (
        11.590 + 1.195 * scale,
        0.0351 - 0.0247 * scale,
        1.376 - 0.826 * scale,
        0.608 + 0.329 * scale,
    )


def moster_log_mstar(log_mhalo: float, z: float, evolve_with_redshift: bool) -> float:
    log_m1, normalization, beta, gamma = moster_parameters(z, evolve_with_redshift)
    ratio = 10.0 ** (log_mhalo - log_m1)
    stellar_fraction = 2.0 * normalization / (ratio ** (-beta) + ratio**gamma)
    return log_mhalo + math.log10(stellar_fraction)


def invert_moster(log_mstar: float, z: float, evolve_with_redshift: bool) -> float:
    low, high = 9.5, 16.0
    if not moster_log_mstar(low, z, evolve_with_redshift) < log_mstar < moster_log_mstar(
        high, z, evolve_with_redshift
    ):
        raise ValueError(f"stellar mass {log_mstar} is outside the Moster inversion bracket")
    for _ in range(100):
        middle = (low + high) / 2.0
        if moster_log_mstar(middle, z, evolve_with_redshift) < log_mstar:
            low = middle
        else:
            high = middle
    return (low + high) / 2.0


def r200c_kpc(log_mhalo: float, z: float) -> float:
    h_km_s_kpc = H0_KM_S_MPC * efunc(z) / 1000.0
    return (G_KPC_KM2_S2_MSUN * 10.0**log_mhalo / (100.0 * h_km_s_kpc**2)) ** (1.0 / 3.0)


def local_moster_slope(log_mhalo: float, z: float, evolve_with_redshift: bool) -> float:
    step = 1e-4
    upper = moster_log_mstar(log_mhalo + step, z, evolve_with_redshift)
    lower = moster_log_mstar(log_mhalo - step, z, evolve_with_redshift)
    return (upper - lower) / (2.0 * step)


def _critical_density_msun_kpc3(z: float) -> float:
    h_km_s_kpc = H0_KM_S_MPC * efunc(z) / 1000.0
    return 3.0 * h_km_s_kpc**2 / (8.0 * math.pi * G_KPC_KM2_S2_MSUN)


def _bryan_norman_rvir_kpc(mhalo_msun: float, z: float) -> float:
    dark_energy_fraction = OMEGA_LAMBDA / (
        OMEGA_LAMBDA + OMEGA_M * (1.0 + z) ** 3
    )
    delta_vir = (
        18.0 * math.pi**2
        - 82.0 * dark_energy_fraction
        - 39.0 * dark_energy_fraction**2
    )
    density = delta_vir * _critical_density_msun_kpc3(z)
    return (3.0 * mhalo_msun / (4.0 * math.pi * density)) ** (1.0 / 3.0)


def modified_nfw_dm(mhalo_msun: float, z: float, b_kpc: float) -> float:
    """Observer-frame modified-NFW electron column in pc cm^-3."""
    concentration = 7.67
    alpha = 2.0
    y0 = 2.0
    hot_fraction = 0.75
    rvir = _bryan_norman_rvir_kpc(mhalo_msun, z)
    if b_kpc >= rvir:
        return 0.0

    def shape(radius_kpc: float) -> float:
        y = concentration * radius_kpc / rvir
        return y ** (alpha - 1.0) / (y0 + y) ** (2.0 + alpha)

    norm_kpc3 = simpson(lambda radius: 4.0 * math.pi * radius**2 * shape(radius), 0.0, rvir)
    gas_mass_g = hot_fraction * (OMEGA_B / OMEGA_M) * mhalo_msun * MSUN_G
    density0_g_cm3 = gas_mass_g / (norm_kpc3 * KPC_CM**3)
    electrons_per_hydrogen = 1.1667
    mean_particle_mass_g = 1.33 * PROTON_G

    def electron_density(radius_kpc: float) -> float:
        return density0_g_cm3 * shape(radius_kpc) / mean_particle_mass_g * electrons_per_hydrogen

    half_path = math.sqrt(rvir**2 - b_kpc**2)
    column_kpc_cm3 = 2.0 * simpson(
        lambda distance: electron_density(math.hypot(b_kpc, distance)), 0.0, half_path
    )
    return column_kpc_cm3 * 1000.0 / (1.0 + z)


def predicted_mgii_width(b_kpc: float, log_mstar: float) -> float:
    normalization = 0.8 * min(max(10.0 ** (0.3 * (log_mstar - 10.5)), 0.2), 3.0)
    if b_kpc <= 50.0:
        return normalization * (b_kpc / 50.0) ** -1.7
    return normalization * (b_kpc / 50.0) ** -0.6


def passive_cool_dm(hot_dm: float, b_over_r200: float, b_kpc: float, log_mstar: float) -> float:
    mass_tilt = min(max(10.0 ** (0.15 * (log_mstar - 10.5)), 0.5), 1.5)
    covering_fraction = 0.3 * mass_tilt * math.exp(-b_over_r200 / 0.5)
    width = predicted_mgii_width(b_kpc, log_mstar)
    scale = 0.3 * (1.0 + 0.5 * math.tanh(width))
    return hot_dm * covering_fraction * scale


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def input_hash_status(paths: dict[str, Path]) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    """Return observed hashes and every mismatch from the reviewed inputs."""
    observed = {name: _sha256(path) for name, path in paths.items()}
    mismatches = {
        name: {"expected": EXPECTED_INPUT_SHA256[name], "observed": observed[name]}
        for name in EXPECTED_INPUT_SHA256
        if observed[name] != EXPECTED_INPUT_SHA256[name]
    }
    return observed, mismatches


def validate(pipeline_root: Path) -> dict:
    data = pipeline_root / "galaxies" / "foreground" / "data"
    paths = {
        "bursts": data / "frozen_census" / "bursts.csv",
        "registry": data / "intervening_census_registry.csv",
        "masses": data / "census_masses" / "halo_rvir_ADJUDICATED.csv",
        "duplicates": data / "census_masses" / "census_duplicates.csv",
        "overrides": data / "census_masses" / "mass_overrides.csv",
        "method": data / "census_masses" / "CGM_intersection_census_METHOD.md",
        "budget": pipeline_root / "galaxies" / "foreground" / "budget_table_data.json",
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing required files: " + ", ".join(missing))

    input_sha256, input_hash_mismatches = input_hash_status(paths)
    input_hashes_match = not input_hash_mismatches

    burst = next(row for row in _read_csv(paths["bursts"]) if row["nickname"].lower() == "phineas")
    sight_ra = float(burst["ra_deg"])
    sight_dec = float(burst["dec_deg"])
    host_z = float(burst["z_spec"])

    duplicate_rows = [
        row for row in _read_csv(paths["duplicates"]) if row["nickname"].lower() == "phineas"
    ]
    duplicate_objects = {row["duplicate_obj"] for row in duplicate_rows}

    registry_rows = [
        row
        for row in _read_csv(paths["registry"])
        if row["nickname"].lower() == "phineas"
        and row["final_verdict"] == "confirmed"
        and row["budget_eligible"] == "True"
        and float(row["best_z"]) < host_z
    ]
    halo_rows_before_dedup = [row for row in registry_rows if row["type"] == "halo"]
    physical_halos = [row for row in halo_rows_before_dedup if row["obj"] not in duplicate_objects]
    clusters = [row for row in registry_rows if row["type"] == "cluster"]

    masses = {
        (row["nickname"].lower(), row["obj"]): row
        for row in _read_csv(paths["masses"])
        if row["logM_adj"]
    }
    for row in _read_csv(paths["overrides"]):
        masses[(row["nickname"].lower(), row["obj"])] = row

    halo_results = []
    total_hot = 0.0
    total_cool = 0.0
    for row in physical_halos:
        mass_row = masses[("phineas", row["obj"])]
        log_mstar = float(mass_row["logM_adj"])
        z = float(row["best_z"])
        b_kpc = impact_kpc(
            sight_ra, sight_dec, float(row["ra_deg"]), float(row["dec_deg"]), z
        )
        log_mhalo_z0 = invert_moster(log_mstar, z, False)
        log_mhalo_evolving = invert_moster(log_mstar, z, True)
        r200_z0 = r200c_kpc(log_mhalo_z0, z)
        r200_evolving = r200c_kpc(log_mhalo_evolving, z)
        ratio_z0 = b_kpc / r200_z0
        ratio_evolving = b_kpc / r200_evolving
        hot_dm = modified_nfw_dm(10.0**log_mhalo_z0, z, b_kpc)
        cool_dm = passive_cool_dm(hot_dm, ratio_z0, b_kpc, log_mstar)
        total_hot += hot_dm
        total_cool += cool_dm

        threshold_log_mhalo = log_mhalo_z0 + 3.0 * math.log10(ratio_z0)
        slope = local_moster_slope(log_mhalo_z0, z, False)
        implied_sigma_log_mhalo = 0.15 / slope
        standardized_margin = (log_mhalo_z0 - threshold_log_mhalo) / implied_sigma_log_mhalo
        illustrative_probability = 0.5 * (1.0 + math.erf(standardized_margin / math.sqrt(2.0)))
        photoz_sensitivity = None
        z_error = float(row["best_z_err"])
        if z_error > 0.0 and mass_row.get("mass_source") == "ps1_taylor":
            central_luminosity_distance = luminosity_distance_kpc(z)
            photoz_sensitivity = {}
            for label, shifted_z in (("minus_one_sigma", z - z_error), ("plus_one_sigma", z + z_error)):
                shifted_log_mstar = log_mstar + 2.0 * math.log10(
                    luminosity_distance_kpc(shifted_z) / central_luminosity_distance
                )
                shifted_log_mhalo = invert_moster(shifted_log_mstar, shifted_z, True)
                shifted_b = impact_kpc(
                    sight_ra,
                    sight_dec,
                    float(row["ra_deg"]),
                    float(row["dec_deg"]),
                    shifted_z,
                )
                shifted_r200 = r200c_kpc(shifted_log_mhalo, shifted_z)
                photoz_sensitivity[label] = {
                    "z": shifted_z,
                    "log_mstar_same_observed_photometry": shifted_log_mstar,
                    "b_over_r200c_redshift_dependent_moster": shifted_b / shifted_r200,
                    "crosses": shifted_b <= shifted_r200,
                }
        stored_r200 = float(mass_row["R_vir_adj"])
        halo_results.append(
            {
                "object": row["obj"],
                "z": z,
                "z_error": z_error,
                "log_mstar": log_mstar,
                "impact_kpc": b_kpc,
                "owner_model": {
                    "log_mhalo": log_mhalo_z0,
                    "r200c_kpc": r200_z0,
                    "b_over_r200c": ratio_z0,
                    "crosses": ratio_z0 <= 1.0,
                    "hot_dm": hot_dm,
                    "cool_dm": cool_dm,
                    "stored_r200_fractional_difference": (r200_z0 - stored_r200) / stored_r200,
                },
                "redshift_dependent_moster": {
                    "log_mhalo": log_mhalo_evolving,
                    "r200c_kpc": r200_evolving,
                    "b_over_r200c": ratio_evolving,
                    "crosses": ratio_evolving <= 1.0,
                },
                "robustness": {
                    "log_mhalo_margin_to_crossing": log_mhalo_z0 - threshold_log_mhalo,
                    "local_dlogmstar_dlogmhalo": slope,
                    "sigma_log_mhalo_from_0p15_dex_intrinsic_stellar_scatter": implied_sigma_log_mhalo,
                    "illustrative_crossing_probability_intrinsic_scatter_only": illustrative_probability,
                    "photoz_one_sigma_same_observed_photometry": photoz_sensitivity,
                },
            }
        )

    if len(clusters) != 1:
        raise ValueError(f"expected one eligible Phineas cluster, found {len(clusters)}")
    cluster = clusters[0]
    cluster_m200 = 1.3 * float(cluster["m500_1e14msun"]) * 1e14
    cluster_hot_dm = modified_nfw_dm(cluster_m200, float(cluster["best_z"]), float(cluster["impact_kpc"]))
    total_hot += cluster_hot_dm
    total_dm = total_hot + total_cool

    with paths["budget"].open(encoding="utf-8") as handle:
        budget = json.load(handle)
    budget_row = next(row for row in budget["rows"] if row["burst"] == "FRB 20230307A")

    referenced_raw = data / "census_masses" / "halo_rvir_MEASURED_diagnostic.csv"
    max_r200_difference = max(
        abs(row["owner_model"]["stored_r200_fractional_difference"]) for row in halo_results
    )
    owner_arithmetic_reproduced = (
        input_hashes_match
        and
        len(halo_rows_before_dedup) == 8
        and len(duplicate_rows) == 3
        and len(physical_halos) == 5
        and round(total_dm) == int(budget_row["dm_int"])
        and max_r200_difference < 5e-4
    )
    fragile = next(row for row in halo_results if row["object"] == "194021777634832653")

    return {
        "validator": "standard-library clean-room implementation; no pipeline imports",
        "pipeline_root": str(pipeline_root.resolve()),
        "input_sha256": input_sha256,
        "expected_input_sha256": EXPECTED_INPUT_SHA256,
        "input_hashes_match": input_hashes_match,
        "input_hash_mismatches": input_hash_mismatches,
        "selection": {
            "confirmed_eligible_halo_rows_before_dedup": len(halo_rows_before_dedup),
            "duplicate_pairs_removed": len(duplicate_rows),
            "physical_halos_after_dedup": len(physical_halos),
            "eligible_clusters": len(clusters),
        },
        "halos": halo_results,
        "cluster": {
            "object": cluster["obj"],
            "m500_msun": float(cluster["m500_1e14msun"]) * 1e14,
            "m200_msun": cluster_m200,
            "impact_kpc": float(cluster["impact_kpc"]),
            "hot_dm": cluster_hot_dm,
        },
        "budget": {
            "hot_dm": total_hot,
            "cool_dm": total_cool,
            "total_dm": total_dm,
            "committed_rounded_dm": int(budget_row["dm_int"]),
            "rounded_total_matches": round(total_dm) == int(budget_row["dm_int"]),
        },
        "reproducibility": {
            "owner_arithmetic_reproduced": owner_arithmetic_reproduced,
            "referenced_raw_photometry_artifact_present": referenced_raw.is_file(),
            "referenced_raw_photometry_artifact": str(referenced_raw),
            "maximum_stored_r200_fractional_difference": max_r200_difference,
        },
        "validity": {
            "deterministic_implementation_valid": owner_arithmetic_reproduced,
            "scientific_point_classification_independently_valid": False,
            "reasons": [
                "the committed mass table omits the raw photometry needed to reproduce the stellar masses",
                "the owner calculation uses redshift-zero Moster parameters although the published relation evolves with redshift",
                "the hard crossing omits intrinsic relation, stellar-mass, and photometric-redshift uncertainty",
                (
                    "the canonical 832 crossing has only "
                    f"{fragile['robustness']['log_mhalo_margin_to_crossing']:.3f} dex halo-mass margin"
                ),
            ],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pipeline-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--expect-rounded-dm", type=int, default=243)
    args = parser.parse_args()

    result = validate(args.pipeline_root)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    if result["budget"]["committed_rounded_dm"] != args.expect_rounded_dm:
        return 2
    return 0 if result["reproducibility"]["owner_arithmetic_reproduced"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
