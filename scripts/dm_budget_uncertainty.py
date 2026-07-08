#!/usr/bin/env python
"""Forward-model the per-sightline DM_host posteriors and the FRB 20230307A
intracluster column, with physically motivated uncertainty propagation.

Referee blocking items B1 and B2. The point-estimate budget in
``budget_table.tex`` subtracts the *mean* of the highly skewed cosmological
DM distribution, which biases every host residual (Macquart et al. 2020; James
et al. 2022). Here we instead sample the full P(DM_cosmic | z) and the nuisance
priors on the Galactic disk, Galactic halo, and intervening columns, and report
DM_host as a posterior (p16/p50/p84) together with P(DM_host < 0) per sightline.

For the single R500-piercing cluster (FRB 20230307A) we bracket the mNFW column
against an X-ray/SZ-motivated beta-model (Cavaliere & Fusco-Femiano 1976; the
GNFW pressure calibration of Arnaud et al. 2010 motivates f_gas), propagating
M500 (richness-mass scatter), f_gas, and the core/slope shape.

Self-contained: numpy + scipy only. Point-estimate component inputs are taken
from the V5-cleared budget table; the physics of the *scatter* is added here.

Regenerate: python scripts/dm_budget_uncertainty.py
"""
from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np
from scipy import integrate, optimize

REPO = Path(__file__).resolve().parent.parent
OUT_CSV = REPO / "scripts" / "dm_budget_uncertainty.csv"
OUT_FIG = REPO / "figures" / "dm_host_posteriors.pdf"
OUT_FIG_PNG = REPO / "figures" / "dm_host_posteriors.png"

RNG = np.random.default_rng(20260707)
N_DRAW = 200_000

# --- Per-sightline point-estimate budget (V5-cleared budget_table.tex) ---------
# DM in pc cm^-3. DM_MW is disk(NE2025)+40 halo; we split the 40 back out below.
# Placeholder-z sightlines (freya/mahi/johndoeii) are excluded: no cosmic/host term.
DM_MW_HALO = 40.0
SIGHTLINES = [
    # name, z, DM_obs, DM_MW(disk+halo), DM_cosmic_mean, DM_int, mass
    ("FRB 20220207C", 0.043, 262, 111, 36, 70, "measured"),
    ("FRB 20220310F", 0.479, 462, 81, 427, 11, "assumed"),
    ("FRB 20220506D", 0.300, 397, 118, 262, 0, "none"),
    ("FRB 20221113A", 0.251, 411, 123, 217, 41, "measured"),
    ("FRB 20221203A", 0.510, 602, 117, 456, 84, "assumed"),
    ("FRB 20230307A", 0.271, 610, 74, 235, 241, "cluster"),
    ("FRB 20230913A", 0.302, 518, 110, 264, 41, "assumed"),
    ("FRB 20240203A", 0.074, 272, 111, 62, 0, "none"),
    ("FRB 20240229A", 0.287, 491, 74, 250, 0, "none"),
]

# --- Nuisance priors -----------------------------------------------------------
# Macquart cosmic-scatter amplitude: sigma_DM = F z^{-1/2}, F ~ 0.32 fiducial
# (Macquart 2020; James 2022 measure F ~ 0.3). We marginalize F over
# [0.25, 0.40] to carry the feedback uncertainty.
F_LO, F_HI = 0.25, 0.40
# Galactic disk (NE2025) fractional uncertainty: electron-density models are good
# to tens of percent along a sightline; 30% lognormal is a standard budget value.
SIGMA_DISK_FRAC = 0.30
# Galactic halo prior: 40 pc cm^-3 median, but the literature spans a factor ~2
# (Yamasaki-Totani 2020 ~43; Keating-Pen 2020 lower; Cook 2023).
# Lognormal, median 40, sigma_ln chosen so the 2sigma range ~ [20, 80].
HALO_SIGMA_LN = 0.35
# Intervening CGM column: mass/f_hot/concentration uncertainty. Measured-mass
# halos ~40% lognormal; assumed-mass ~factor-2 (0.5 dex-ish) lognormal.
INT_SIGMA_LN = {"measured": 0.40, "assumed": 0.69, "cluster": 0.30, "none": 0.0}


def macquart_pdf(delta: np.ndarray, sigma_dm: float, c0: float,
                 alpha: float = 3.0, beta: float = 3.0) -> np.ndarray:
    """Unnormalized cosmic-DM PDF P(Delta), Delta = DM_cosmic/<DM_cosmic>
    (Macquart 2020 functional form; McQuinn 2014 scatter)."""
    out = np.zeros_like(delta)
    m = delta > 0
    d = delta[m]
    out[m] = d ** (-beta) * np.exp(-((d ** (-alpha) - c0) ** 2) / (2.0 * alpha ** 2 * sigma_dm ** 2))
    return out


def _delta_grid(sigma_dm: float, alpha=3.0, beta=3.0):
    """Grid + C0 solved so E[Delta]=1; returns (grid, normalized pdf, cdf)."""
    grid = np.linspace(1e-3, 6.0, 4000)

    def mean_minus_one(c0):
        p = macquart_pdf(grid, sigma_dm, c0, alpha, beta)
        norm = np.trapezoid(p, grid)
        return np.trapezoid(grid * p, grid) / norm - 1.0

    c0 = optimize.brentq(mean_minus_one, -5.0, 5.0)
    p = macquart_pdf(grid, sigma_dm, c0, alpha, beta)
    p /= np.trapezoid(p, grid)
    cdf = integrate.cumulative_trapezoid(p, grid, initial=0.0)
    cdf /= cdf[-1]
    return grid, p, cdf


def sample_dm_cosmic(z: float, dm_cosmic_mean: float, n: int) -> np.ndarray:
    """Draw DM_cosmic from the physical P(DM_cosmic|z), marginalizing F."""
    fvals = RNG.uniform(F_LO, F_HI, n)
    out = np.empty(n)
    edges = np.linspace(F_LO, F_HI, 9)
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (fvals >= lo) & (fvals <= hi if hi >= F_HI else fvals < hi)
        if not m.any():
            continue
        fmid = 0.5 * (lo + hi)
        sigma_dm = fmid * z ** -0.5
        grid, _, cdf = _delta_grid(sigma_dm)
        u = RNG.uniform(0, 1, m.sum())
        delta = np.interp(u, cdf, grid)
        out[m] = delta * dm_cosmic_mean
    return out


def host_posterior(row):
    name, z, dm_obs, dm_mw, dm_cos_mean, dm_int, mass = row
    dm_disk = dm_mw - DM_MW_HALO
    disk = dm_disk * RNG.lognormal(-0.5 * SIGMA_DISK_FRAC ** 2, SIGMA_DISK_FRAC, N_DRAW)
    halo = DM_MW_HALO * RNG.lognormal(-0.5 * HALO_SIGMA_LN ** 2, HALO_SIGMA_LN, N_DRAW)
    cosmic = sample_dm_cosmic(z, dm_cos_mean, N_DRAW)
    s_int = INT_SIGMA_LN[mass]
    if dm_int > 0 and s_int > 0:
        interv = dm_int * RNG.lognormal(-0.5 * s_int ** 2, s_int, N_DRAW)
    else:
        interv = np.full(N_DRAW, float(dm_int))
    host = dm_obs - disk - halo - cosmic - interv
    p16, p50, p84 = np.percentile(host, [16, 50, 84])
    return {
        "name": name, "z": z,
        "dm_host_arith": dm_obs - dm_mw - dm_cos_mean - dm_int,  # old mean-subtraction
        "dm_host_p16": p16, "dm_host_p50": p50, "dm_host_p84": p84,
        "p_host_neg": float(np.mean(host < 0)),
        "samples": host,
    }


# --- B2: FRB 20230307A intracluster column (mNFW vs beta-model) ----------------
MU_E = 1.17            # mean molecular weight per electron (fully ionized, X=0.75)
M_P = 1.67262192e-27   # kg
MSUN = 1.98847e30      # kg
KPC_PC = 1.0e3         # pc per kpc

# Wen-Han 2024 cluster J115120.4+714435 toward FRB 20230307A.
CL_M500 = 1.48e14      # Msun
CL_R500_KPC = 729.0    # kpc
CL_Z = 0.200
CL_B_KPC = 603.6       # impact parameter (b/R500 = 0.83)


def beta_model_dm(m500, r500_kpc, b_kpc, z, f_gas, rc_over_r500, beta):
    """Observer-frame intracluster DM from an isothermal beta-model.

    n_e(r) = n_e0 [1+(r/rc)^2]^{-3 beta/2}; n_e0 fixed by requiring the gas mass
    within R500 equal f_gas * M500. Chord integral at impact b, out to 3 R500.
    """
    KPC_M = 3.0856775814913673e19
    rc = rc_over_r500 * r500_kpc
    # Gas-mass normalization: M_gas(<R500) = f_gas M500 (integral in kpc^3).
    def shell(r):
        return 4.0 * math.pi * r ** 2 * (1.0 + (r / rc) ** 2) ** (-1.5 * beta)
    mass_integral_kpc3, _ = integrate.quad(shell, 0.0, r500_kpc, limit=200)
    m_gas_kg = f_gas * m500 * MSUN
    rho0 = m_gas_kg / (mass_integral_kpc3 * KPC_M ** 3)   # kg / m^3 at r=0
    ne0 = rho0 / (MU_E * M_P) / 1e6                       # electrons / cm^3
    # Chord integral: n_e (cm^-3) over path length; dl in kpc -> pc via KPC_PC.
    # Truncate the LOS at the virial radius R200 ~ 1.48 R500, matching the mNFW
    # truncation, so the cross-check compares profile shape, not path length.
    r_max = 1.48 * r500_kpc
    l_max = math.sqrt(max(r_max ** 2 - b_kpc ** 2, 0.0))
    def ne_los(l):
        r = math.hypot(b_kpc, l)
        return ne0 * (1.0 + (r / rc) ** 2) ** (-1.5 * beta)
    dm_kpc, _ = integrate.quad(ne_los, -l_max, l_max, limit=200)  # cm^-3 * kpc
    dm_rest = dm_kpc * KPC_PC                                     # pc cm^-3
    return dm_rest / (1.0 + z)                                    # observer frame


def cluster_column_range(n=40_000):
    """MC the beta-model column over M500, f_gas, and shape; report the range."""
    log_m500 = RNG.normal(math.log10(CL_M500), 0.20, n)   # 0.2 dex richness-mass scatter
    m500 = 10.0 ** log_m500
    r500 = CL_R500_KPC * (m500 / CL_M500) ** (1.0 / 3.0)  # R500 ~ M500^{1/3}
    f_gas = RNG.uniform(0.10, 0.16, n)          # X-ray/SZ cluster gas fractions
    rc_over = RNG.uniform(0.10, 0.30, n)        # core radius / R500
    beta = RNG.uniform(0.60, 0.75, n)           # beta-model slope
    dm = np.array([
        beta_model_dm(m500[i], r500[i], CL_B_KPC, CL_Z, f_gas[i], rc_over[i], beta[i])
        for i in range(n)
    ])
    return dm


def main():
    print("=== B1: DM_host posteriors (forward-modeled) ===")
    print(f"{'burst':16s} {'z':>5s} {'arith':>7s} {'p16':>6s} {'p50':>6s} {'p84':>6s} {'P(<0)':>6s}")
    results = []
    for row in SIGHTLINES:
        r = host_posterior(row)
        results.append(r)
        print(f"{r['name']:16s} {r['z']:5.3f} {r['dm_host_arith']:7.0f} "
              f"{r['dm_host_p16']:6.0f} {r['dm_host_p50']:6.0f} {r['dm_host_p84']:6.0f} "
              f"{r['p_host_neg']:6.2f}")

    print("\n=== B2: FRB 20230307A intracluster column ===")
    dm_cl = cluster_column_range()
    p16, p50, p84 = np.percentile(dm_cl, [16, 50, 84])
    lo, hi = np.percentile(dm_cl, [2.5, 97.5])
    print(f"beta-model column: p50={p50:.0f}, [p16,p84]=[{p16:.0f},{p84:.0f}], "
          f"95% CI=[{lo:.0f},{hi:.0f}] pc cm^-3")
    print("mNFW central (pipeline, V5): ~160 pc cm^-3")
    span_lo = min(lo, 160)
    span_hi = max(hi, 160)
    print(f"combined plausible range (mNFW + beta-model systematic): "
          f"~{span_lo:.0f}-{span_hi:.0f} pc cm^-3")

    with OUT_CSV.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["burst", "z", "dm_host_arith", "dm_host_p16", "dm_host_p50",
                    "dm_host_p84", "p_host_negative"])
        for r in results:
            w.writerow([r["name"], r["z"], f"{r['dm_host_arith']:.0f}",
                        f"{r['dm_host_p16']:.0f}", f"{r['dm_host_p50']:.0f}",
                        f"{r['dm_host_p84']:.0f}", f"{r['p_host_neg']:.3f}"])
        w.writerow([])
        w.writerow(["cluster_beta_model_p16_p50_p84", f"{p16:.0f}", f"{p50:.0f}", f"{p84:.0f}"])
        w.writerow(["cluster_95CI_lo_hi", f"{lo:.0f}", f"{hi:.0f}"])
    print(f"\nwrote {OUT_CSV.relative_to(REPO)}")

    _make_figure(results, dm_cl)


def _make_figure(results, dm_cl):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(11, 4.2), gridspec_kw={"width_ratios": [2.4, 1]}
    )
    names = [r["name"].replace("FRB ", "") for r in results]
    y = np.arange(len(results))[::-1]
    p16 = np.array([r["dm_host_p16"] for r in results])
    p50 = np.array([r["dm_host_p50"] for r in results])
    p84 = np.array([r["dm_host_p84"] for r in results])
    arith = np.array([r["dm_host_arith"] for r in results])
    ax1.axvline(0, color="0.6", lw=1, ls="--")
    ax1.errorbar(p50, y, xerr=[p50 - p16, p84 - p50], fmt="o", color="#264653",
                 capsize=3, label="forward-modeled posterior (p16/p50/p84)")
    ax1.scatter(arith, y, marker="x", color="#e76f51", zorder=5,
                label="arithmetic mean-subtraction")
    ax1.set_yticks(y)
    ax1.set_yticklabels(names, fontsize=8)
    ax1.set_ylim(-0.6, len(results) - 0.4)
    ax1.set_xlabel(r"$\mathrm{DM_{host}}\ (\mathrm{pc\,cm^{-3}})$")
    ax1.set_title("Host dispersion: posterior vs. mean-subtraction")
    ax1.legend(fontsize=7, loc="lower right")

    ax2.hist(dm_cl, bins=60, color="#2a9d8f", alpha=0.8, density=True)
    ax2.axvline(160, color="#e76f51", lw=1.5, label="mNFW (pipeline)")
    ax2.set_xlabel(r"cluster $\mathrm{DM_{int}}\ (\mathrm{pc\,cm^{-3}})$")
    ax2.set_title("FRB 20230307A cluster\ncolumn (beta-model MC)", fontsize=9)
    ax2.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(OUT_FIG)
    fig.savefig(OUT_FIG_PNG, dpi=150)
    print(f"wrote {OUT_FIG.relative_to(REPO)}")


if __name__ == "__main__":
    main()
