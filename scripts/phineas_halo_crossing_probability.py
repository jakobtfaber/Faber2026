#!/usr/bin/env python3
"""Probabilistic virial crossing and foreground-DM model for Phineas.

The two boundary-sensitive halos are propagated from frozen Pan-STARRS Kron
photometry and Legacy Survey photometric-redshift errors.  A deterministic
scrambled Sobol sequence carries photometric errors, Taylor-mass calibration
scatter, Moster-relation intrinsic scatter, and halo-gas model scatter.  Halo
mass uses the redshift-dependent Moster et al. (2013) Table 1 relation.

The output is a zero-inflated DM distribution: non-foreground or non-crossing
draws contribute exactly zero; crossing draws carry the modified-NFW hot column
plus the existing cool-gas prior.  This module imports no pipeline code.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy import stats


INPUTS = Path(__file__).with_name("phineas_halo_crossing_inputs.csv")
DEFAULT_OUTPUT = Path(__file__).with_name("phineas_halo_crossing_probability.json")

HOST_Z = 0.271
SIGHT_RA_DEG = 177.7813333333
SIGHT_DEC_DEG = 71.6956388889

C_KM_S = 299_792.458
G_KPC_KM2_S2_MSUN = 4.300_917_270_036_28e-6
H0_KM_S_MPC = 67.66
OMEGA_M = 0.30966
OMEGA_NU = 0.0014396743040845244
OMEGA_GAMMA = 5.402015137139353e-5
OMEGA_LAMBDA = 0.6888463055445441
OMEGA_B = 0.04897

MSUN_G = 1.988409870698051e33
KPC_CM = 3.085677581491367e21
PROTON_G = 1.67262192369e-24

TAYLOR_CALIBRATION_SIGMA_DEX = 0.10
MOSTER_INTRINSIC_SIGMA_DEX = 0.15
CGM_PROFILE_SIGMA_LN = 0.40
SOBOL_SEED = 20260722
SOBOL_POWER = 18

MNFW_CONCENTRATION = 7.67
MNFW_ALPHA = 2.0
MNFW_Y0 = 2.0
MNFW_F_HOT = 0.75
MNFW_MEAN_PARTICLE_MASS = 1.33
MNFW_ELECTRONS_PER_H = 1.1667


@dataclass(frozen=True)
class HaloInput:
    object: str
    legacy_obj: str
    registry_ra_deg: float
    registry_dec_deg: float
    photometry_objid: str
    photometry_ra_deg: float
    photometry_dec_deg: float
    match_sep_arcsec: float
    z_mean: float
    z_sigma: float
    z_source_id: str
    z_query_sha256: str
    z_verification_sha256: str
    g_kron_mag: float
    g_kron_err: float
    i_kron_mag: float
    i_kron_err: float
    ps1_quality: int
    ps1_g_flags: int
    ps1_i_flags: int
    ps1_query_sha256: str
    ps1_row_sha256: str


@dataclass(frozen=True)
class HaloDraws:
    model_domain: np.ndarray
    foreground: np.ndarray
    r200c_crossing: np.ndarray
    crossing: np.ndarray
    dm: np.ndarray
    z: np.ndarray
    log_mstar: np.ndarray
    log_mhalo: np.ndarray
    b_over_r200c: np.ndarray
    b_over_rvir: np.ndarray


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@lru_cache(maxsize=1)
def load_inputs() -> dict[str, HaloInput]:
    with INPUTS.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 2:
        raise ValueError(f"expected two Phineas halo inputs, found {len(rows)}")
    result: dict[str, HaloInput] = {}
    for row in rows:
        halo = HaloInput(
            object=row["object"],
            legacy_obj=row["legacy_obj"],
            registry_ra_deg=float(row["registry_ra_deg"]),
            registry_dec_deg=float(row["registry_dec_deg"]),
            photometry_objid=row["photometry_objid"],
            photometry_ra_deg=float(row["photometry_ra_deg"]),
            photometry_dec_deg=float(row["photometry_dec_deg"]),
            match_sep_arcsec=float(row["match_sep_arcsec"]),
            z_mean=float(row["z_mean"]),
            z_sigma=float(row["z_sigma"]),
            z_source_id=row["z_source_id"],
            z_query_sha256=row["z_query_sha256"],
            z_verification_sha256=row["z_verification_sha256"],
            g_kron_mag=float(row["g_kron_mag"]),
            g_kron_err=float(row["g_kron_err"]),
            i_kron_mag=float(row["i_kron_mag"]),
            i_kron_err=float(row["i_kron_err"]),
            ps1_quality=int(row["ps1_quality"]),
            ps1_g_flags=int(row["ps1_g_flags"]),
            ps1_i_flags=int(row["ps1_i_flags"]),
            ps1_query_sha256=row["ps1_query_sha256"],
            ps1_row_sha256=row["ps1_row_sha256"],
        )
        if halo.object in result:
            raise ValueError(f"duplicate Phineas halo input {halo.object}")
        if halo.match_sep_arcsec > 0.2:
            raise ValueError(f"{halo.object}: photometry match exceeds 0.2 arcsec")
        if halo.ps1_quality < 50 or min(halo.g_kron_err, halo.i_kron_err) <= 0.0:
            raise ValueError(
                f"{halo.object}: invalid Pan-STARRS quality or uncertainty"
            )
        result[halo.object] = halo
    expected = {"194021777634832653", "983"}
    if set(result) != expected:
        raise ValueError(f"Phineas halo roster differs: {sorted(result)}")
    return result


def efunc(z: np.ndarray | float) -> np.ndarray | float:
    return np.sqrt(
        (OMEGA_M + OMEGA_NU) * (1.0 + z) ** 3
        + OMEGA_GAMMA * (1.0 + z) ** 4
        + OMEGA_LAMBDA
    )


@lru_cache(maxsize=1)
def _distance_grid() -> tuple[np.ndarray, np.ndarray]:
    z = np.linspace(0.0, HOST_Z + 5.0 * 0.0585, 20_001)
    inverse_e = 1.0 / efunc(z)
    dz = np.diff(z)
    radial_integral = np.concatenate(
        ([0.0], np.cumsum(0.5 * dz * (inverse_e[:-1] + inverse_e[1:])))
    )
    return z, radial_integral


def angular_diameter_distance_kpc(z: np.ndarray) -> np.ndarray:
    grid_z, radial_integral = _distance_grid()
    integral = np.interp(z, grid_z, radial_integral)
    return C_KM_S / H0_KM_S_MPC * integral * 1000.0 / (1.0 + z)


def luminosity_distance_pc(z: np.ndarray) -> np.ndarray:
    return angular_diameter_distance_kpc(z) * (1.0 + z) ** 2 * 1000.0


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


def central_log_mstar(halo: HaloInput) -> float:
    z = np.array([halo.z_mean])
    distance_modulus = 5.0 * np.log10(luminosity_distance_pc(z) / 10.0)
    return float(
        1.15
        + 0.70 * (halo.g_kron_mag - halo.i_kron_mag)
        - 0.4 * (halo.i_kron_mag - distance_modulus[0])
    )


def moster_log_mstar(log_mhalo: np.ndarray, z: np.ndarray) -> np.ndarray:
    scale = z / (1.0 + z)
    log_m1 = 11.590 + 1.195 * scale
    normalization = 0.0351 - 0.0247 * scale
    beta = 1.376 - 0.826 * scale
    gamma = 0.608 + 0.329 * scale
    ratio = 10.0 ** (log_mhalo - log_m1)
    stellar_fraction = 2.0 * normalization / (ratio ** (-beta) + ratio**gamma)
    return log_mhalo + np.log10(stellar_fraction)


def invert_moster(log_mstar: np.ndarray, z: np.ndarray) -> np.ndarray:
    low = np.full_like(log_mstar, 9.5)
    high = np.full_like(log_mstar, 16.0)
    lower_bound = moster_log_mstar(low, z)
    upper_bound = moster_log_mstar(high, z)
    if np.any((log_mstar <= lower_bound) | (log_mstar >= upper_bound)):
        raise ValueError(
            "a stellar-mass draw lies outside the Moster inversion bracket"
        )
    for _ in range(55):
        middle = 0.5 * (low + high)
        below = moster_log_mstar(middle, z) < log_mstar
        low = np.where(below, middle, low)
        high = np.where(below, high, middle)
    return 0.5 * (low + high)


def r200c_kpc(log_mhalo: np.ndarray, z: np.ndarray) -> np.ndarray:
    h_km_s_kpc = H0_KM_S_MPC * efunc(z) / 1000.0
    return (G_KPC_KM2_S2_MSUN * 10.0**log_mhalo / (100.0 * h_km_s_kpc**2)) ** (
        1.0 / 3.0
    )


def _bryan_norman_rvir_kpc(log_mhalo: np.ndarray, z: np.ndarray) -> np.ndarray:
    dark_energy_fraction = OMEGA_LAMBDA / (OMEGA_LAMBDA + OMEGA_M * (1.0 + z) ** 3)
    delta_vir = (
        18.0 * math.pi**2 - 82.0 * dark_energy_fraction - 39.0 * dark_energy_fraction**2
    )
    h_km_s_kpc = H0_KM_S_MPC * efunc(z) / 1000.0
    critical_density = 3.0 * h_km_s_kpc**2 / (8.0 * math.pi * G_KPC_KM2_S2_MSUN)
    return (3.0 * 10.0**log_mhalo / (4.0 * math.pi * delta_vir * critical_density)) ** (
        1.0 / 3.0
    )


@lru_cache(maxsize=1)
def _mnfw_quadrature() -> tuple[np.ndarray, np.ndarray, float]:
    nodes, weights = leggauss(64)
    nodes = 0.5 * (nodes + 1.0)
    weights = 0.5 * weights
    x_nodes, x_weights = leggauss(128)
    x_nodes = 0.5 * (x_nodes + 1.0)
    x_weights = 0.5 * x_weights

    def shape(radius_over_rvir: np.ndarray) -> np.ndarray:
        y = MNFW_CONCENTRATION * radius_over_rvir
        return y ** (MNFW_ALPHA - 1.0) / (MNFW_Y0 + y) ** (2.0 + MNFW_ALPHA)

    norm = float(4.0 * math.pi * np.sum(x_weights * x_nodes**2 * shape(x_nodes)))
    return nodes, weights, norm


def modified_nfw_dm(
    log_mhalo: np.ndarray,
    z: np.ndarray,
    impact_kpc: np.ndarray,
    profile_factor: np.ndarray,
) -> np.ndarray:
    rvir = _bryan_norman_rvir_kpc(log_mhalo, z)
    u = impact_kpc / rvir
    if np.any(u >= 1.0):
        raise ValueError("R200c crossing draw unexpectedly lies outside mNFW radius")
    nodes, weights, norm = _mnfw_quadrature()
    result = np.empty_like(u)
    for start in range(0, len(u), 8192):
        stop = min(start + 8192, len(u))
        uc = u[start:stop]
        half_path = np.sqrt(1.0 - uc**2)
        distance = half_path[:, None] * nodes[None, :]
        radius = np.sqrt(uc[:, None] ** 2 + distance**2)
        y = MNFW_CONCENTRATION * radius
        shape = y ** (MNFW_ALPHA - 1.0) / (MNFW_Y0 + y) ** (2.0 + MNFW_ALPHA)
        los_dimensionless = 2.0 * half_path * np.sum(weights * shape, axis=1)

        rv = rvir[start:stop]
        halo_mass = 10.0 ** log_mhalo[start:stop]
        gas_mass_g = MNFW_F_HOT * (OMEGA_B / OMEGA_M) * halo_mass * MSUN_G
        density0 = gas_mass_g / (rv**3 * KPC_CM**3 * norm)
        electron0 = (
            density0 / (MNFW_MEAN_PARTICLE_MASS * PROTON_G) * MNFW_ELECTRONS_PER_H
        )
        result[start:stop] = (
            electron0
            * rv
            * los_dimensionless
            * 1000.0
            / (1.0 + z[start:stop])
            * profile_factor[start:stop]
        )
    return result


def passive_cool_dm(
    hot_dm: np.ndarray,
    b_over_r200c: np.ndarray,
    impact_kpc: np.ndarray,
    log_mstar: np.ndarray,
) -> np.ndarray:
    mass_tilt = np.clip(10.0 ** (0.15 * (log_mstar - 10.5)), 0.5, 1.5)
    covering_fraction = 0.3 * mass_tilt * np.exp(-b_over_r200c / 0.5)
    mgii_normalization = 0.8 * np.clip(10.0 ** (0.3 * (log_mstar - 10.5)), 0.2, 3.0)
    width = np.where(
        impact_kpc <= 50.0,
        mgii_normalization * (impact_kpc / 50.0) ** -1.7,
        mgii_normalization * (impact_kpc / 50.0) ** -0.6,
    )
    scale = 0.3 * (1.0 + 0.5 * np.tanh(width))
    return hot_dm * covering_fraction * scale


def _normal_draws(n: int, seed: int, quasi: bool) -> np.ndarray:
    if quasi:
        power = int(round(math.log2(n)))
        if 2**power != n:
            raise ValueError("Sobol sample count must be a power of two")
        unit = stats.qmc.Sobol(d=6, scramble=True, seed=seed).random_base2(power)
        return stats.norm.ppf(np.clip(unit, 1e-12, 1.0 - 1e-12))
    return np.random.default_rng(seed).normal(size=(n, 6))


def simulate_halo(
    halo: HaloInput,
    *,
    n: int = 2**SOBOL_POWER,
    seed: int = SOBOL_SEED,
    quasi: bool = True,
) -> HaloDraws:
    normal = _normal_draws(n, seed, quasi)
    z = halo.z_mean + halo.z_sigma * normal[:, 0]
    valid_z = z > 0.0
    calculation_z = np.clip(z, 1e-5, HOST_Z + 5.0 * halo.z_sigma)
    g_mag = halo.g_kron_mag + halo.g_kron_err * normal[:, 1]
    i_mag = halo.i_kron_mag + halo.i_kron_err * normal[:, 2]
    distance_modulus = 5.0 * np.log10(luminosity_distance_pc(calculation_z) / 10.0)
    log_mstar = (
        1.15
        + 0.70 * (g_mag - i_mag)
        - 0.4 * (i_mag - distance_modulus)
        + TAYLOR_CALIBRATION_SIGMA_DEX * normal[:, 3]
    )
    relation_target = log_mstar - MOSTER_INTRINSIC_SIGMA_DEX * normal[:, 4]
    lower_relation = moster_log_mstar(np.full(n, 9.5), calculation_z)
    upper_relation = moster_log_mstar(np.full(n, 16.0), calculation_z)
    model_domain = (
        valid_z
        & (relation_target > lower_relation)
        & (relation_target < upper_relation)
    )
    # Draws outside the published inversion range are excluded from crossing.
    # A harmless in-range value keeps the vectorized inversion finite; these
    # entries can never contribute dispersion measure.
    safe_target = np.where(
        model_domain,
        relation_target,
        0.5 * (lower_relation + upper_relation),
    )
    log_mhalo = invert_moster(safe_target, calculation_z)

    separation = angular_separation_rad(
        SIGHT_RA_DEG,
        SIGHT_DEC_DEG,
        halo.registry_ra_deg,
        halo.registry_dec_deg,
    )
    impact = separation * angular_diameter_distance_kpc(calculation_z)
    r200 = r200c_kpc(log_mhalo, calculation_z)
    b_over_r200 = impact / r200
    rvir = _bryan_norman_rvir_kpc(log_mhalo, calculation_z)
    b_over_rvir = impact / rvir
    foreground = valid_z & (z < HOST_Z)
    r200c_crossing = foreground & model_domain & (b_over_r200 <= 1.0)
    crossing = foreground & model_domain & (b_over_rvir <= 1.0)

    dm = np.zeros(n, dtype=float)
    profile_factor = np.exp(CGM_PROFILE_SIGMA_LN * normal[crossing, 5])
    hot = modified_nfw_dm(
        log_mhalo[crossing],
        calculation_z[crossing],
        impact[crossing],
        profile_factor,
    )
    cool = passive_cool_dm(
        hot,
        b_over_r200[crossing],
        impact[crossing],
        log_mstar[crossing],
    )
    dm[crossing] = hot + cool
    return HaloDraws(
        model_domain=model_domain,
        foreground=foreground,
        r200c_crossing=r200c_crossing,
        crossing=crossing,
        dm=dm,
        z=z,
        log_mstar=log_mstar,
        log_mhalo=log_mhalo,
        b_over_r200c=b_over_r200,
        b_over_rvir=b_over_rvir,
    )


@lru_cache(maxsize=8)
def cached_draws(object_id: str, power: int = SOBOL_POWER) -> HaloDraws:
    halo = load_inputs()[object_id]
    object_seed = SOBOL_SEED + sum(ord(character) for character in object_id)
    return simulate_halo(halo, n=2**power, seed=object_seed, quasi=True)


def halo_dm_histogram(
    object_id: str,
    *,
    dx: float,
    power: int = SOBOL_POWER,
) -> tuple[float, np.ndarray]:
    if dx <= 0.0:
        raise ValueError("dx must be positive")
    dm = cached_draws(object_id, power).dm
    maximum = math.ceil(float(dm.max()) / dx) * dx
    edges = np.arange(-0.5 * dx, maximum + 1.5 * dx, dx)
    counts, _ = np.histogram(dm, bins=edges)
    density = counts.astype(float) / (len(dm) * dx)
    density.setflags(write=False)
    return 0.0, density


def _quantiles(values: np.ndarray) -> dict[str, float]:
    p16, p50, p84 = np.quantile(values, [0.16, 0.50, 0.84])
    return {"p16": float(p16), "p50": float(p50), "p84": float(p84)}


def summarize(object_id: str, *, power: int = SOBOL_POWER) -> dict:
    halo = load_inputs()[object_id]
    draws = cached_draws(object_id, power)
    conditional = draws.dm[draws.crossing]
    return {
        "object": object_id,
        "legacy_obj": halo.legacy_obj or None,
        "n_draws": len(draws.dm),
        "central_log_mstar": central_log_mstar(halo),
        "p_model_domain": float(draws.model_domain.mean()),
        "p_foreground": float(draws.foreground.mean()),
        "p_r200c_crossing": float(draws.r200c_crossing.mean()),
        "p_crossing": float(draws.crossing.mean()),
        "p_crossing_given_foreground": float(
            draws.crossing.sum() / draws.foreground.sum()
        ),
        "dm_mixture": {
            **_quantiles(draws.dm),
            "mean": float(draws.dm.mean()),
        },
        "dm_given_crossing": {
            **_quantiles(conditional),
            "mean": float(conditional.mean()),
        },
        "b_over_r200c": _quantiles(draws.b_over_r200c[draws.foreground]),
        "b_over_mnfw_rvir": _quantiles(draws.b_over_rvir[draws.foreground]),
    }


def build_result(*, power: int = SOBOL_POWER) -> dict:
    inputs = load_inputs()
    summaries = {object_id: summarize(object_id, power=power) for object_id in inputs}
    return {
        "status": "probabilistic_crossing_model",
        "model": {
            "sampler": "deterministic scrambled Sobol",
            "seed": SOBOL_SEED,
            "power": power,
            "draws_per_object": 2**power,
            "host_z": HOST_Z,
            "stellar_mass": "Taylor et al. 2011 Eq. 8 from Pan-STARRS Kron g/i",
            "stellar_mass_calibration_sigma_dex": TAYLOR_CALIBRATION_SIGMA_DEX,
            "halo_mass": "redshift-dependent Moster et al. 2013 Table 1",
            "moster_intrinsic_sigma_dex_in_log_mstar": MOSTER_INTRINSIC_SIGMA_DEX,
            "cgm_profile_sigma_ln": CGM_PROFILE_SIGMA_LN,
            "crossing_definition": "foreground z < host z and b <= the Bryan-Norman virial truncation radius used by the modified-NFW gas model",
            "r200c_definition": "reported as a census-geometry sensitivity, not used to truncate the gas column",
            "dm_definition": "zero outside crossing; modified-NFW hot plus cool prior inside",
        },
        "input_csv": f"scripts/{INPUTS.name}",
        "input_sha256": _sha256(INPUTS),
        "inputs": {key: asdict(value) for key, value in inputs.items()},
        "halos": summaries,
        "limitations": [
            "Legacy photo-z and Pan-STARRS magnitude errors are treated as independent because their covariance is unavailable.",
            "Taylor calibration scatter covers the empirical mass calibration; no object-specific spectral-energy-distribution k-correction is available.",
            "Moster fit-parameter covariance is not published in a directly usable matrix; intrinsic relation scatter is propagated instead.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--power", type=int, default=SOBOL_POWER)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = (
        json.dumps(build_result(power=args.power), indent=2, sort_keys=True) + "\n"
    )
    if args.check:
        if (
            not args.output.is_file()
            or args.output.read_text(encoding="utf-8") != rendered
        ):
            print(f"DRIFT: {args.output}")
            return 1
        print(f"OK: {args.output}")
        return 0
    args.output.write_text(rendered, encoding="utf-8")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
