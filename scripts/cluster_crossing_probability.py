"""Kulkarni S2: a-priori cluster-crossing probability for the codetected sample.

Predeclared record: docs/rse/specs/plan/plan-cluster-crossing-probability-2026-07-17.md
(pinned thresholds, z-vectors, quotability rule). Implements Phases 0-2.

Run:  uv run --project pipeline --frozen python scripts/cluster_crossing_probability.py
Emits scripts/cluster_crossing_probability.csv and
docs/rse/decks/budget/cluster-crossing-2026-07-17/crossing_probability.pdf.

N_exp = sum_i int_0^{z_i} dz (c/H) n_com(>M, z) * pi R500_proper(M,z)^2 * (1+z)^2
(the (1+z)^2 promotes the proper cross-section to comoving, matching the
comoving number density). Reported primary is the mass-integrated form
int dM (dn/dM) pi R500(M)^2 over M >= M_thresh, since heavier-than-threshold
clusters present larger cross-sections; the fixed-sigma variant is emitted too.

Mass function: Tinker et al. 2008 (ApJ 688, 709) at Delta_m(z) = 500/Omega_m(z),
i.e. the M500c definition the census registry uses, with their Table-2
coefficients interpolated in log Delta and their redshift evolution.
Alternative (quotability pair): Despali et al. 2016 (MNRAS 456, 2486) at
Delta=500c via their x = log10(Delta/Delta_vir) quadratics (coefficients
verified against the paper). Sheth-Tormen is emitted as a diagnostic row only:
its ~virial mass convention over-counts at a fixed M500c threshold by
construction, so it is excluded from the frozen 30% rule (recorded, not hidden).
Transfer function: Eisenstein & Hu 1998 (ApJ 496, 605) zero-baryon shape.
"""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

import numpy as np
from scipy import integrate, interpolate

ROOT = Path(__file__).resolve().parents[1]

# --- Pinned inputs (plan, Implementation Approach; tests machine-verify) ---
PINNED = {
    # cosmology: scripts/dm_budget_uncertainty.py budget values + S2-new P(k) pins
    "H0": 70.0,
    "Om0": 0.3,
    "sigma8": 0.81,
    "ns": 0.965,
    "Ob0": 0.048,
    # thresholds: registry row (intervening_census_registry.csv:23), never prose
    "m500_primary": 1.48e14,
    "m500_secondary": 1.0e14,
    # registry R500 anchor for the 500*rho_c convention
    "r500_anchor_mpc": 0.729,
    "z_anchor": 0.200,
}

# z-vectors (plan, pin 5). The Verdi propagation lane landed on main (PR #110)
# between charter and execution, so per the plan's Phase-3 TARGETS note the
# primary vector is pinned at the pipeline TARGETS precision (config.py; the
# z=1.0000 entries are the pipeline's no-z placeholder convention and are
# excluded). tests/test_cluster_crossing_probability.py ties this literal to
# the TARGETS source. The control is the frozen pre-Verdi manuscript set.
Z_PRIMARY = (0.0430, 0.4790, 0.3005, 0.2505, 0.2710, 0.3024, 0.0740, 0.2870, 0.5535)
Z_CONTROL = (0.043, 0.479, 0.300, 0.251, 0.510, 0.271, 0.302, 0.074, 0.287)

H0 = PINNED["H0"]
OM0 = PINNED["Om0"]
OL0 = 1.0 - OM0
H_KM_S_MPC = H0
C_KM_S = 299792.458
h = H0 / 100.0

# comoving mean matter density today, Msun/Mpc^3:
# rho_c0 = 2.775e11 h^2 Msun/Mpc^3
RHO_C0 = 2.775e11 * h * h
RHO_M0 = OM0 * RHO_C0
DELTA_C = 1.686


def efunc(z: float) -> float:
    return math.sqrt(OM0 * (1 + z) ** 3 + OL0)


def omega_m_z(z: float) -> float:
    return OM0 * (1 + z) ** 3 / efunc(z) ** 2


def rho_crit_z(z: float) -> float:
    """Proper critical density at z, Msun/Mpc^3."""
    return RHO_C0 * efunc(z) ** 2


def r500_proper_mpc(m500_msun: float, z: float) -> float:
    """R500 from M = (4/3) pi R^3 * 500 rho_c(z) -- the census 500c convention."""
    return (3.0 * m500_msun / (4.0 * math.pi * 500.0 * rho_crit_z(z))) ** (1.0 / 3.0)


# --- linear power spectrum (EH98 zero-baryon) and sigma(R, z) ---
def _t_eh98_nowiggle(k_hmpc: np.ndarray) -> np.ndarray:
    """Eisenstein & Hu 1998 zero-baryon transfer function; k in h/Mpc."""
    ob_frac = PINNED["Ob0"] / OM0
    theta = 2.7255 / 2.7  # CMB temperature
    # sound-horizon-scaled shape parameter with baryon suppression (EH98 eq. 30-31)
    alpha_gamma = 1 - 0.328 * math.log(431 * OM0 * h * h) * ob_frac + 0.38 * math.log(
        22.3 * OM0 * h * h
    ) * ob_frac**2
    s = 44.5 * math.log(9.83 / (OM0 * h * h)) / math.sqrt(
        1 + 10 * (PINNED["Ob0"] * h * h) ** 0.75
    )  # Mpc
    k_mpc = k_hmpc * h
    gamma_eff = OM0 * h * (alpha_gamma + (1 - alpha_gamma) / (1 + (0.43 * k_mpc * s) ** 4))
    q = k_hmpc * theta**2 / gamma_eff
    l0 = np.log(2 * math.e + 1.8 * q)
    c0 = 14.2 + 731.0 / (1 + 62.5 * q)
    return l0 / (l0 + c0 * q * q)


_K = np.logspace(-4, 3, 1200)  # h/Mpc
_PK_UNNORM = _K ** PINNED["ns"] * _t_eh98_nowiggle(_K) ** 2


def _sigma_unnorm(r_hmpc: float) -> float:
    x = _K * r_hmpc
    w = 3.0 * (np.sin(x) - x * np.cos(x)) / x**3
    integrand = _K**2 * _PK_UNNORM * w * w
    return math.sqrt(np.trapezoid(integrand, _K) / (2 * math.pi**2))


_SIGMA_NORM = PINNED["sigma8"] / _sigma_unnorm(8.0)


def growth_factor(z: float) -> float:
    """Linear growth D(z), D(0)=1 (standard flat-LCDM integral)."""

    def _d(zz: float) -> float:
        integrand = lambda zp: (1 + zp) / (OM0 * (1 + zp) ** 3 + OL0) ** 1.5
        val, _ = integrate.quad(integrand, zz, 1000.0, limit=200)
        return efunc(zz) * val

    return _d(z) / _d(0.0)


def sigma_r(r_mpc: float, z: float) -> float:
    """RMS top-hat fluctuation at proper-comoving radius r (Mpc, not h^-1)."""
    return _SIGMA_NORM * _sigma_unnorm(r_mpc * h) * growth_factor(z)


def _sigma_m(m_msun: float, z: float) -> float:
    r = (3.0 * m_msun / (4.0 * math.pi * RHO_M0)) ** (1.0 / 3.0)  # comoving Mpc
    return sigma_r(r, z)


# --- Tinker et al. 2008 f(sigma), Delta_m-interpolated (their Table 2) ---
_T08_DELTA = np.array([200, 300, 400, 600, 800, 1200, 1600, 2400, 3200])
_T08_A = np.array([0.186, 0.200, 0.212, 0.218, 0.248, 0.255, 0.260, 0.260, 0.260])
_T08_a = np.array([1.47, 1.52, 1.56, 1.61, 1.87, 2.13, 2.30, 2.53, 2.66])
_T08_b = np.array([2.57, 2.25, 2.05, 1.87, 1.59, 1.51, 1.46, 1.44, 1.41])
_T08_c = np.array([1.19, 1.27, 1.34, 1.45, 1.58, 1.80, 1.97, 2.24, 2.44])
_T08_INTERP = {
    name: interpolate.interp1d(np.log10(_T08_DELTA), vals, kind="cubic")
    for name, vals in (("A", _T08_A), ("a", _T08_a), ("b", _T08_b), ("c", _T08_c))
}


def _f_tinker08(sigma: np.ndarray, z: float) -> np.ndarray:
    delta_m = 500.0 / omega_m_z(z)
    ld = math.log10(min(delta_m, 3200.0))
    A0 = float(_T08_INTERP["A"](ld))
    a0 = float(_T08_INTERP["a"](ld))
    b0 = float(_T08_INTERP["b"](ld))
    c0 = float(_T08_INTERP["c"](ld))
    # Tinker08 redshift evolution (their eqs. 5-8), capped at z=3 per the paper
    zz = min(z, 3.0)
    A = A0 * (1 + zz) ** (-0.14)
    a = a0 * (1 + zz) ** (-0.06)
    alpha = 10 ** (-((0.75 / math.log10(delta_m / 75.0)) ** 1.2))
    b = b0 * (1 + zz) ** (-alpha)
    return A * ((sigma / b) ** (-a) + 1.0) * np.exp(-c0 / sigma**2)


def _f_sheth_tormen(sigma: np.ndarray, z: float) -> np.ndarray:
    # diagnostic only (NOT the quotability alternative): its ~virial mass
    # convention over-counts at a fixed M500c threshold by construction
    A, a, p = 0.3222, 0.707, 0.3
    nu = DELTA_C / sigma
    anu2 = a * nu * nu
    return A * math.sqrt(2 * a / math.pi) * nu * (1 + anu2 ** (-p)) * np.exp(-anu2 / 2.0)


def _delta_vir_bryan_norman(z: float) -> float:
    """Bryan & Norman 1998 virial overdensity wrt critical density (flat LCDM).

    Despali+16 used the Eke+96 numerical solution; BN98 agrees to <2%, well
    inside the fit scatter, and is the standard analytic stand-in.
    """
    d = omega_m_z(z) - 1.0
    return 18.0 * math.pi**2 + 82.0 * d - 39.0 * d * d


def _f_despali16(sigma: np.ndarray, z: float) -> np.ndarray:
    """Despali et al. 2016 (MNRAS 456, 2486) at Delta=500c: the quotability
    alternative. x = log10(500/Delta_vir(z)); their eq. 12-13 quadratics
    (verified against the paper 2026-07-17):
      a = 0.4332 x^2 + 0.2263 x + 0.7665
      p = -0.1151 x^2 + 0.2554 x + 0.2488
      A = -0.1362 x + 0.3292
    f(nu) = 2A (1 + nu'^-p) sqrt(nu'/2pi) exp(-nu'/2), nu = (dc/sigma)^2, nu' = a nu.
    """
    x = math.log10(500.0 / _delta_vir_bryan_norman(z))
    a = 0.4332 * x * x + 0.2263 * x + 0.7665
    p = -0.1151 * x * x + 0.2554 * x + 0.2488
    A = -0.1362 * x + 0.3292
    nu = (DELTA_C / sigma) ** 2
    nup = a * nu
    return 2.0 * A * (1.0 + nup ** (-p)) * np.sqrt(nup / (2.0 * math.pi)) * np.exp(-nup / 2.0)


_LNM_GRID = np.linspace(math.log(1e13), math.log(3e16), 400)


def _dndlnm(z: float, fit: str = "tinker08") -> np.ndarray:
    """Comoving dn/dlnM (Mpc^-3) on _LNM_GRID."""
    m = np.exp(_LNM_GRID)
    sig = np.array([_sigma_m(mm, z) for mm in m])
    lnsig_inv = -np.log(sig)
    dlns_dlnm = np.gradient(lnsig_inv, _LNM_GRID)
    f = {"tinker08": _f_tinker08, "despali16": _f_despali16, "st": _f_sheth_tormen}[fit](sig, z)
    return f * (RHO_M0 / m) * dlns_dlnm  # dn/dlnM = f * rho/M * dlnsig^-1/dlnM


def n_gt_m(m_thresh: float, z: float, fit: str = "tinker08") -> float:
    """Comoving number density of halos above M (M500c for tinker08), Mpc^-3."""
    dn = _dndlnm(z, fit)
    mask = _LNM_GRID >= math.log(m_thresh)
    return float(np.trapezoid(dn[mask], _LNM_GRID[mask]))


def _cross_section_com(z: float, m_thresh: float, fit: str, mass_integrated: bool) -> float:
    """n * sigma product (comoving Mpc^-1 per unit path), cross-section comoving."""
    if mass_integrated:
        dn = _dndlnm(z, fit)
        mask = _LNM_GRID >= math.log(m_thresh)
        m = np.exp(_LNM_GRID[mask])
        sig_geom = np.array([math.pi * r500_proper_mpc(mm, z) ** 2 for mm in m])
        return float(np.trapezoid(dn[mask] * sig_geom, _LNM_GRID[mask])) * (1 + z) ** 2
    n = n_gt_m(m_thresh, z, fit)
    return n * math.pi * r500_proper_mpc(m_thresh, z) ** 2 * (1 + z) ** 2


def n_cross_sightline(
    z_host: float, m_thresh: float, fit: str = "tinker08", mass_integrated: bool = True, nz: int = 25
) -> float:
    """Expected crossings within R500 of >= m_thresh clusters along one sightline."""
    zg = np.linspace(1e-4, z_host, nz)
    integrand = [
        (C_KM_S / (H_KM_S_MPC * efunc(z))) * _cross_section_com(z, m_thresh, fit, mass_integrated)
        for z in zg
    ]
    return float(np.trapezoid(integrand, zg))


def n_cross_total(z_vec, m_thresh: float, fit: str = "tinker08", mass_integrated: bool = True):
    per = [n_cross_sightline(z, m_thresh, fit, mass_integrated) for z in z_vec]
    return float(sum(per)), per


def quotability(results: dict) -> tuple[str, float]:
    """Frozen rule: quotable iff every variant is within 30% of the primary,
    and every variant lies in the [0.01, 1] sanity band."""
    primary = results["primary"]
    variants = [v for k, v in results.items() if k != "primary"]
    if any(not (0.01 <= v <= 1.0) for v in list(results.values())):
        return "sanity-audit", primary
    spread = max(abs(v - primary) / primary for v in variants)
    return ("quotable" if spread <= 0.30 else "spread"), spread


def main() -> int:
    m1 = PINNED["m500_primary"]
    m2 = PINNED["m500_secondary"]

    results = {
        "primary": n_cross_total(Z_PRIMARY, m1)[0],
        "z_control": n_cross_total(Z_CONTROL, m1)[0],
        "alt_fit_despali16": n_cross_total(Z_PRIMARY, m1, fit="despali16")[0],
    }
    st_diag = n_cross_total(Z_PRIMARY, m1, fit="st")[0]
    verdict, spread = quotability(results)

    total_p, per_p = n_cross_total(Z_PRIMARY, m1)
    total_1e14, per_1e14 = n_cross_total(Z_PRIMARY, m2)
    total_fixed = n_cross_total(Z_PRIMARY, m1, mass_integrated=False)[0]
    tertiary_12 = total_p + 3 * n_cross_sightline(float(np.median(Z_PRIMARY)), m1)

    out = ROOT / "scripts" / "cluster_crossing_probability.csv"
    with out.open("w", newline="") as fh:
        fh.write(
            f"# Kulkarni S2 (plan-cluster-crossing-probability-2026-07-17). "
            f"Quotability verdict: {verdict} (max variant spread {spread:.2f}, rule <=0.30)\n"
        )
        w = csv.writer(fh)
        w.writerow(["quantity", "value"])
        w.writerow(["N_exp_primary_verdi_tinker08_ge1.48e14", f"{results['primary']:.4f}"])
        w.writerow(["N_exp_control_zset", f"{results['z_control']:.4f}"])
        w.writerow(["N_exp_alt_fit_despali16", f"{results['alt_fit_despali16']:.4f}"])
        w.writerow(["N_exp_ST_diagnostic_overcounts_by_construction", f"{st_diag:.4f}"])
        w.writerow(["N_exp_ge1.0e14", f"{total_1e14:.4f}"])
        w.writerow(["N_exp_fixed_sigma_variant", f"{total_fixed:.4f}"])
        w.writerow(["N_exp_12sightline_tertiary", f"{tertiary_12:.4f}"])
        w.writerow(["n_gt_1.48e14_z0.2_Mpc-3", f"{n_gt_m(m1, 0.2):.3e}"])
        w.writerow(["n_gt_1.0e14_z0.2_Mpc-3", f"{n_gt_m(m2, 0.2):.3e}"])
        for z, n in zip(Z_PRIMARY, per_p):
            w.writerow([f"per_sightline_z={z}", f"{n:.5f}"])

    # record figure
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.5, 3.8), constrained_layout=True)
    m_grid = np.logspace(14, 15.2, 25)
    ax1.loglog(m_grid, [n_cross_total(Z_PRIMARY, m)[0] for m in m_grid], "C0-")
    for m, ls, lab in ((m1, "--", "registry 1.48e14"), (m2, ":", "1.0e14")):
        ax1.axvline(m, ls=ls, c="k", lw=0.8)
    ax1.set_xlabel(r"$M_{500c}$ threshold ($M_\odot$)")
    ax1.set_ylabel(r"$N_{\rm exp}$ (9 sightlines)")
    ax1.grid(alpha=0.2, which="both")
    ax1.set_title("expected crossings vs. mass threshold")
    order = np.argsort(Z_PRIMARY)
    ax2.bar(range(9), np.array(per_p)[order], color="C0")
    ax2.set_xticks(range(9))
    ax2.set_xticklabels([f"{Z_PRIMARY[i]:.3g}" for i in order], rotation=45, fontsize=7)
    ax2.set_xlabel("host z (Verdi-standard set)")
    ax2.set_ylabel(r"per-sightline $N_{\rm exp}$ ($\geq1.48\times10^{14}$)")
    ax2.grid(alpha=0.2, axis="y")
    ax2.set_title(f"total = {total_p:.3f} ({verdict})")
    fig_path = ROOT / "docs/rse/decks/budget/cluster-crossing-2026-07-17/crossing_probability.pdf"
    fig_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(fig_path)
    plt.close(fig)

    print(f"n(>1.48e14 M500c, z=0.2) = {n_gt_m(m1, 0.2):.3e} Mpc^-3")
    print(f"N_exp primary (Verdi, T08, >=1.48e14, mass-integrated): {results['primary']:.4f}")
    print(f"  control z-set : {results['z_control']:.4f}")
    print(f"  Despali16 alt : {results['alt_fit_despali16']:.4f}")
    print(f"  ST diagnostic : {st_diag:.4f} (over-counts by construction; excluded from the rule)")
    print(f"  >=1.0e14      : {total_1e14:.4f}   fixed-sigma: {total_fixed:.4f}   12-sl tertiary: {tertiary_12:.4f}")
    print(f"quotability: {verdict.upper()} (max spread {spread:.2f}, rule <= 0.30)")
    print(f"csv: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
