#!/usr/bin/env python
"""Forward-model the per-sightline DM_host posteriors and the FRB 20230307A
intracluster column, with physically motivated uncertainty propagation.

Referee blocking items B1 and B2. The point-estimate budget in
``budget_table.tex`` subtracts the *mean* of the highly skewed cosmological
DM distribution, which biases every host residual (Macquart et al. 2020; James
et al. 2022). Here we instead sample the full P(DM_cosmic | z) and the nuisance
priors on the Galactic disk, Galactic halo, and intervening columns, and report
DM_host as a posterior (p16/p50/p84) together with P(DM_host < 0) per sightline.

The diffuse cosmic term is modeled as the IGM column DM_IGM ~ LogNormal(mu(z),
sigma(z)), with mu(z) and sigma(z) the redshift-dependent log-normal parameters
of a bivariate (IGM, halo) fit to a mock FRB survey in IllustrisTNG-300 by
Walker et al. (2024); we adopt the tabulated values (columns [A, mu_X, mu_IGM,
sig_X, sig_IGM, rho]) via the reproduction package of Connor et al. (2025,
arXiv:2409.16952; tng_params_new.npy), whose analysis uses this calibration and
fits f_IGM to the DSA-110 + literature FRB sample. This supersedes the earlier
Macquart P(Delta) form with fixed sigma_DM = F z^{-1/2}: Connor et al. (2025)
show sigma_DM does NOT follow the z^{-1/2} halo-Poisson scaling, and that the
diffuse scatter is dominated by non-Poissonian intersection of IGM filaments and
sheets. Because this budget already carries identified intervening halos in the
separate DM_int census term, we map our cosmic term onto the *IGM* marginal
(DM_IGM, gas outside virialized halos, f_IGM = 0.76 from Connor et al. 2025)
rather than the total DM_cos = DM_IGM + DM_X; using DM_cos would double-count the
census halos. The halo-Poisson sigma_DM = F z^{-1/2} form overstated the diffuse
width by ~3x (CV ~60-80% vs ~20-37% here), which is exactly the halo scatter that
DM_int handles here.

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
from scipy import integrate, interpolate

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
# Diffuse cosmic (IGM) column: Connor et al. (2025) fit the IGM baryon fraction
# f_IGM = 0.76 (+0.10/-0.11) from the DSA-110 + literature FRB sample. We
# marginalize f_IGM over this (asymmetric-normal, clipped to (0, 0.98]) to carry
# the feedback/partition uncertainty; it shifts the IGM log-mean by
# log(f_IGM / f_IGM,TNG). The redshift-dependent log-normal shape (mu, sigma) is
# fixed to the TNG-300 calibration below.
FIGM_MED, FIGM_SIG_LO, FIGM_SIG_HI = 0.76, 0.11, 0.10
FIGM_TNG = 0.797          # TNG-300 baseline f_IGM in Connor et al. calibration
FIGM_CLIP = (0.30, 0.98)  # keep draws physical (f_IGM + f_X <= 1)
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


# --- TNG-300 IGM log-normal calibration (Walker et al. 2024) -------------------
# Bivariate (IGM, halo) log-normal fit to a mock FRB survey in IllustrisTNG-300
# by Walker et al. (2024); tabulated in the Connor et al. (2025) reproduction
# package (tng_params_new.npy), columns [A, mu_X, mu_IGM, sig_X, sig_IGM, rho] at
# the 12 snapshot redshifts below. We use the IGM marginal (mu_IGM, sig_IGM)
# only, since identified intervening halos (the DM_X / halo term of the bivariate
# model) are already carried by this budget's separate DM_int census. Values
# reproduced verbatim so the script stays self-contained (numpy + scipy only);
# regenerate from the .npy if the calibration is updated.
TNG_ZGRID = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0])
TNG_MU_IGM = np.array([4.37380909, 5.07264111, 5.4962193, 5.80209722, 6.04344301,
                       6.40614181, 6.78312432, 7.19849362, 7.48250248, 7.86255147,
                       8.11920163, 8.30542453])
TNG_SIG_IGM = np.array([0.33479241, 0.29198339, 0.25434913, 0.22449515, 0.20123352,
                        0.17974651, 0.16545537, 0.14851468, 0.13239113, 0.11009793,
                        0.09384749, 0.08155763])
_MU_IGM_SPL = interpolate.UnivariateSpline(TNG_ZGRID, TNG_MU_IGM, s=0)
_SIG_IGM_SPL = interpolate.UnivariateSpline(TNG_ZGRID, TNG_SIG_IGM, s=0)


def igm_lognormal_params(z: float, f_igm: float = FIGM_MED):
    """Log-normal (mu, sigma) of DM_IGM at redshift z, adjusted to f_igm.

    mu is the natural-log median; the f_igm rescaling shifts the log-mean by
    log(f_igm / f_igm,TNG) (Connor et al. 2025, Methods)."""
    mu = float(_MU_IGM_SPL(z)) + np.log(f_igm / FIGM_TNG)
    sigma = float(_SIG_IGM_SPL(z))
    return mu, sigma


def _draw_figm(n: int) -> np.ndarray:
    """f_IGM draws: two-sided normal (0.76 +0.10/-0.11), clipped to physical."""
    u = RNG.normal(0.0, 1.0, n)
    scale = np.where(u < 0.0, FIGM_SIG_LO, FIGM_SIG_HI)
    return np.clip(FIGM_MED + u * scale, *FIGM_CLIP)


def sample_dm_cosmic(z: float, dm_cosmic_mean: float, n: int) -> np.ndarray:
    """Draw the diffuse cosmic (IGM) column from the Walker et al. (2024)
    TNG-calibrated LogNormal(mu(z), sigma(z)), marginalizing f_IGM (Connor 2025).

    ``dm_cosmic_mean`` (the old Macquart point estimate) is retained in the
    SIGHTLINES table for provenance but is NOT used to set the scale: the scale
    now comes from the TNG log-median mu(z), rescaled by the sampled f_IGM."""
    figm = _draw_figm(n)
    mu = float(_MU_IGM_SPL(z)) + np.log(figm / FIGM_TNG)
    sigma = float(_SIG_IGM_SPL(z))
    out = RNG.lognormal(mu, sigma)
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
