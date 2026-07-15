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
sheets. The TNG calibration is tabulated only for z >= 0.1; below that we continue
it along the Macquart relation rather than extrapolating the spline (see
``igm_lognormal_shape``).

Because this budget already carries identified intervening halos in the
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

Self-contained: numpy + scipy only (plus a frozen per-system intervening CSV
for the figure overlays). Point-estimate component inputs are taken from the
V5-cleared budget table; the physics of the *scatter* is added here.

DM_host here is the OBSERVER-FRAME residual (no 1+z factor); the rest-frame host
column is (1+z) larger and is tabulated alongside it in the manuscript. For the
six sightlines outside the deep-imaging footprints (UPPER_LIMIT below) the
foreground census is incomplete and DM_int is a floor; with the IGM-marginal
cosmic term (halos excluded), an undetected halo lands in the host residual, so
those DM_host are upper limits (dagger on the figure panel titles).

The figure is a 3x3 of peak-normalized PDFs per redshift-constrained sightline:
faded MW-disk / MW-halo / IGM / per-system intervening curves under a bold
P(DM_host). Tabulated host posteriors are unchanged (still use the
sightline-sum intervening draw).

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

# --- Per-sightline point-estimate budget ---------------------------------------
# DM in pc cm^-3. DM_MW is disk(NE2025)+40 halo; we split the 40 back out below.
# Placeholder-z sightlines (freya/mahi/johndoeii) are excluded: no cosmic/host term.
DM_MW_HALO = 40.0
SIGHTLINES = [
    # name, z, DM_obs, DM_MW(disk+halo), DM_cosmic_mean, DM_int, mass
    # DM_int is sourced ONLY from the V4-verified census registry
    # (pipeline/galaxies/foreground/data/intervening_census_registry.csv):
    # budget-eligible confirmed systems, deduplicated and carrying the
    # owner-adjudicated empirical masses + uniformly recomputed halo impact
    # parameters (census remediation 2026-07-15; see
    # pipeline/galaxies/foreground/data/census_masses/). The pre-2026-07-15
    # values for 20220207C (70), 20221113A (41), 20221203A (84), and
    # 20230913A (41) came from the revoked legacy results/{name}_galaxies.csv
    # lists through the registry-empty fallback bug; those sightlines have
    # zero budget-eligible systems in the registry.
    ("FRB 20220207C", 0.043, 262.361665, 111, 36, 0, "none"),
    ("FRB 20220310F", 0.479, 462.188773, 81, 427, 6, "measured"),
    ("FRB 20220506D", 0.300, 397.015535, 118, 262, 0, "none"),
    ("FRB 20221113A", 0.251, 411.435717, 123, 217, 0, "none"),
    ("FRB 20221203A", 0.510, 602.377821, 117, 456, 0, "none"),
    ("FRB 20230307A", 0.271, 610.289070, 74, 235, 243, "cluster"),
    ("FRB 20230913A", 0.302, 518.796993, 110, 264, 0, "none"),
    ("FRB 20240203A", 0.074, 272.638699, 111, 62, 26, "measured"),
    ("FRB 20240229A", 0.287, 491.207826, 74, 250, 117, "measured"),
]

# Sightlines outside the deep-imaging footprints (budget_table.tex note u): the
# intervening census is incomplete, so DM_int is a floor. With the IGM-marginal
# cosmic term (which excludes virialized halos), any undetected foreground halo
# is absorbed into the host residual -> DM_host is an UPPER LIMIT, flagged with a
# dagger on the figure panel titles.
UPPER_LIMIT = {
    "FRB 20220207C", "FRB 20220506D", "FRB 20221113A",
    "FRB 20221203A", "FRB 20230913A", "FRB 20240203A",
}

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
TNG_ZMIN = float(TNG_ZGRID[0])
TNG_ZMAX = float(TNG_ZGRID[-1])
_MU_IGM_SPL = interpolate.UnivariateSpline(TNG_ZGRID, TNG_MU_IGM, s=0)
_SIG_IGM_SPL = interpolate.UnivariateSpline(TNG_ZGRID, TNG_SIG_IGM, s=0)

# Low-z continuation below the TNG grid (z < 0.1). Two of the nine sightlines
# (z = 0.043, 0.074) lie below the tabulated range, where a cubic spline with
# scipy's default extrapolation is unconstrained: it flattens to a spurious
# DM_IGM(z->0) -> 25 pc cm^-3 floor and overestimates the median by ~30% at
# z = 0.043, enough to push DM_IGM above the total <DM_cos> = DM_IGM + DM_X.
# Instead we continue mu(z) along the Macquart relation's own redshift
# dependence, <DM_IGM(z)> propto int_0^z (1+z')/E(z') dz' (Macquart et al. 2020,
# Eq. 2; Deng & Zhang 2014), which vanishes linearly as z -> 0. Sanity: this
# scaling reproduces the tabulated mu increments to 1.5% over 0.1 < z < 0.3
# (ln[I(0.2)/I(0.1)] = 0.713 vs the tabulated 0.699), so it is continuous with,
# and consistent with, the calibration it extends.
# sigma is held at its grid-edge value: TNG does not constrain the IGM scatter
# below z = 0.1, and holding it fixed is the minimal assumption (the cubic
# extrapolation gave 0.360 at z = 0.043 vs 0.335 here -- a negligible difference
# next to the mu error it accompanied).
OMEGA_M, OMEGA_LAMBDA = 0.3111, 0.6889   # flat LCDM, Planck 2018 (TT,TE,EE+lowE+lensing)


def _macquart_integral(z: float) -> float:
    """int_0^z (1+z')/E(z') dz', the redshift dependence of <DM_IGM>."""
    val, _ = integrate.quad(
        lambda x: (1.0 + x) / math.sqrt(OMEGA_M * (1.0 + x) ** 3 + OMEGA_LAMBDA),
        0.0, z, limit=200,
    )
    return val


_MACQUART_I_ZMIN = _macquart_integral(TNG_ZMIN)


def igm_lognormal_shape(z: float):
    """TNG-calibrated (mu, sigma) of DM_IGM at redshift z, at f_IGM = f_IGM,TNG.

    Interpolates the tabulated grid for 0.1 <= z <= 5, and continues below the
    grid along the Macquart relation (see the note above). Raises above z = 5,
    where nothing constrains the calibration and no sightline in this budget
    lives."""
    if not 0.0 < z <= TNG_ZMAX:
        raise ValueError(
            f"z={z} outside the supported range (0, {TNG_ZMAX}]: the TNG-300 IGM "
            "calibration is tabulated on 0.1 <= z <= 5 and must not be extrapolated above it."
        )
    if z >= TNG_ZMIN:
        return float(_MU_IGM_SPL(z)), float(_SIG_IGM_SPL(z))
    mu = TNG_MU_IGM[0] + math.log(_macquart_integral(z) / _MACQUART_I_ZMIN)
    return mu, float(TNG_SIG_IGM[0])


def igm_lognormal_params(z: float, f_igm: float = FIGM_MED):
    """Log-normal (mu, sigma) of DM_IGM at redshift z, adjusted to f_igm.

    mu is the natural-log median; the f_igm rescaling shifts the log-mean by
    log(f_igm / f_igm,TNG) (Connor et al. 2025, Methods)."""
    mu, sigma = igm_lognormal_shape(z)
    return mu + np.log(f_igm / FIGM_TNG), sigma


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
    mu_tng, sigma = igm_lognormal_shape(z)
    mu = mu_tng + np.log(figm / FIGM_TNG)
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
    # Rest-frame host column: DM_host,rest = (1+z) DM_host,obs. (1+z) > 0 is a
    # monotone rescaling, so the rest-frame percentiles are the observer-frame
    # percentiles times (1+z) -- computed from the raw samples (not the rounded
    # integers) so the tabulated rest values are reproducible from this run.
    r16, r50, r84 = (1.0 + z) * np.percentile(host, [16, 50, 84])
    return {
        "name": name, "z": z, "mass": mass, "dm_int": dm_int,
        "dm_host_arith": dm_obs - dm_mw - dm_cos_mean - dm_int,  # old mean-subtraction
        "dm_host_p16": p16, "dm_host_p50": p50, "dm_host_p84": p84,
        "dm_host_rest_p16": r16, "dm_host_rest_p50": r50, "dm_host_rest_p84": r84,
        "p_host_neg": float(np.mean(host < 0)),
        "samples": host,
        "disk": disk, "halo": halo, "cosmic": cosmic, "interv": interv,
    }


def load_intervening_systems():
    """Per-system census point columns (frozen CSV from foreground_unified)."""
    path = REPO / "scripts" / "dm_budget_intervening_systems.csv"
    by_tns: dict[str, list[dict]] = {}
    if not path.exists():
        return by_tns
    with path.open() as f:
        for row in csv.DictReader(f):
            tns = row["tns"]
            by_tns.setdefault(tns, []).append({
                "kind": row["kind"],
                "mass_source": row["mass_source"],
                "dm_point": float(row["dm_point"]),
                "impact_kpc": float(row["impact_kpc"]),
            })
    return by_tns


def sample_system_column(dm_point: float, mass_source: str, n: int) -> np.ndarray:
    """Lognormal smear of a census point column; sigma matches INT_SIGMA_LN family."""
    if dm_point <= 0:
        return np.zeros(n)
    if mass_source == "cluster_catalog":
        key = "cluster"
    elif mass_source in ("measured", "glade_catalog"):
        # GLADE catalog masses are measured-mass priors (σ_ln=0.40), same as SIGHTLINES.
        key = "measured"
    else:
        key = "assumed"
    s = INT_SIGMA_LN[key]
    if s <= 0:
        return np.full(n, dm_point)
    return dm_point * RNG.lognormal(-0.5 * s ** 2, s, n)


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
    # mNFW column carried in the budget (intervening census point for the
    # J115120.4+714435 cluster; = DM_int - galaxy columns for FRB 20230307A).
    mnfw_central = 184.0
    print(f"mNFW central (budget census point): ~{mnfw_central:.0f} pc cm^-3")
    span_lo = min(lo, mnfw_central)
    span_hi = max(hi, mnfw_central)
    print(f"combined plausible range (mNFW + beta-model systematic): "
          f"~{span_lo:.0f}-{span_hi:.0f} pc cm^-3")

    with OUT_CSV.open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["burst", "z", "dm_host_arith", "dm_host_p16", "dm_host_p50",
                    "dm_host_p84", "p_host_negative",
                    "dm_host_rest_p16", "dm_host_rest_p50", "dm_host_rest_p84"])
        for r in results:
            w.writerow([r["name"], r["z"], f"{r['dm_host_arith']:.0f}",
                        f"{r['dm_host_p16']:.0f}", f"{r['dm_host_p50']:.0f}",
                        f"{r['dm_host_p84']:.0f}", f"{r['p_host_neg']:.3f}",
                        f"{r['dm_host_rest_p16']:.0f}", f"{r['dm_host_rest_p50']:.0f}",
                        f"{r['dm_host_rest_p84']:.0f}"])
        w.writerow([])
        w.writerow(["cluster_beta_model_p16_p50_p84", f"{p16:.0f}", f"{p50:.0f}", f"{p84:.0f}"])
        w.writerow(["cluster_95CI_lo_hi", f"{lo:.0f}", f"{hi:.0f}"])
    print(f"\nwrote {OUT_CSV.relative_to(REPO)}")

    # LaTeX-ready rows for tab:host-forward-model (observer & rest frame), so the
    # appendix table is transcribed from this run rather than hand-computed. Each
    # frame's interval is the difference of its own rounded percentiles, so
    # median + upper = the tabulated rounded p84 by construction.
    print("\n=== tab:host-forward-model rows (obs | rest) ===")
    for r in results:
        o50, o16, o84 = round(r["dm_host_p50"]), round(r["dm_host_p16"]), round(r["dm_host_p84"])
        s50, s16, s84 = (round(r["dm_host_rest_p50"]), round(r["dm_host_rest_p16"]),
                         round(r["dm_host_rest_p84"]))
        print(f"{r['name']} & ${r['z']:.3f}$ & "
              f"${o50}^{{+{o84 - o50}}}_{{-{o50 - o16}}}$ & "
              f"${s50}^{{+{s84 - s50}}}_{{-{s50 - s16}}}$ & ${r['p_host_neg']:.2f}$ \\\\")


    _make_figure(results)


# Manuscript figure palette — matches sightline_budget.make_budget_figure /
# galaxies/v2_0/systems_figures.py.
_MW_COLOR = "#4A90E2"
_HALO_COLOR = "#7FB3E8"
_COSMIC_COLOR = "#9B59B6"
_INTERV_COLOR = "#F5A623"
_HOST_COLOR = "#D0021B"
_DARK_BLUE = "#1B365D"


def _apply_manuscript_style() -> None:
    """Same style stack as scripts/plot_codetection_gallery.py / flits.plotting.

    SciencePlots ``["science", "notebook"]`` plus the FLITS Computer-Modern
    overrides (no TeX binary required). Falls back to ``pipeline/matplotlibrc``
    if SciencePlots is unavailable.
    """
    import matplotlib.pyplot as plt

    try:
        import sys

        pipe = str(REPO / "pipeline")
        if pipe not in sys.path:
            sys.path.insert(0, pipe)
        from flits.plotting import use_flits_style

        use_flits_style()
        return
    except Exception:
        pass
    try:
        import scienceplots  # noqa: F401

        plt.style.use(["science", "notebook"])
    except Exception:
        import matplotlib

        rc = REPO / "pipeline" / "matplotlibrc"
        if rc.exists():
            matplotlib.rc_file(str(rc))
    plt.rcParams["text.usetex"] = False
    plt.rcParams["font.family"] = "serif"
    plt.rcParams["font.serif"] = ["cmr10"]
    plt.rcParams["mathtext.fontset"] = "cm"
    plt.rcParams["axes.formatter.use_mathtext"] = True
    plt.rcParams["axes.unicode_minus"] = False


def _kde_1d(samples: np.ndarray, x: np.ndarray) -> np.ndarray:
    """Gaussian KDE on a fixed grid; falls back to a histogram if degenerate."""
    s = np.asarray(samples, dtype=float)
    s = s[np.isfinite(s)]
    if s.size < 50:
        hist, edges = np.histogram(s, bins=40, density=True, range=(x[0], x[-1]))
        centers = 0.5 * (edges[:-1] + edges[1:])
        return np.interp(x, centers, hist, left=0.0, right=0.0)
    std = float(np.std(s))
    if std <= 0.0:
        y = np.zeros_like(x)
        y[np.argmin(np.abs(x - float(np.median(s))))] = 1.0
        return y
    bw = max(1.06 * std * s.size ** (-0.2), 2.0)
    if s.size > 12_000:
        s = RNG.choice(s, size=12_000, replace=False)
    z = (x[None, :] - s[:, None]) / bw
    return np.exp(-0.5 * z * z).mean(axis=0) / (bw * math.sqrt(2.0 * math.pi))


def _peak_norm(dens: np.ndarray) -> np.ndarray:
    m = float(dens.max()) if dens.size else 0.0
    return dens / m if m > 0 else dens


def _make_figure(results):
    """One panel per sightline: faded component PDFs under bold P(DM_host)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    _apply_manuscript_style()
    # Dense 3x3 at true manuscript width: same shrunk-type overrides as
    # scripts/plot_codetection_gallery.py (render(), rcParams block).
    plt.rcParams.update({
        "font.size": 7,
        "axes.labelsize": 7,
        "axes.titlesize": 7,
        "xtick.labelsize": 6,
        "ytick.labelsize": 6,
        "legend.fontsize": 6,
        "axes.linewidth": 0.6,
        "xtick.direction": "in",
        "ytick.direction": "in",
    })

    systems_by_tns = load_intervening_systems()

    n = len(results)
    ncols, nrows = 3, 3
    fig, axes = plt.subplots(
        nrows, ncols, figsize=(7.3, 6.4), layout="constrained",
    )
    axes = np.asarray(axes).ravel()

    legend_handles = [
        Line2D([0], [0], color=_HOST_COLOR, lw=1.5, label=r"$P(\mathrm{DM_{host}})$"),
        Line2D([0], [0], color=_MW_COLOR, lw=0.8, alpha=0.35, label="MW ISM (disk)"),
        Line2D([0], [0], color=_HALO_COLOR, lw=0.8, alpha=0.35, label="MW halo"),
        Line2D([0], [0], color=_COSMIC_COLOR, lw=0.8, alpha=0.35, label="cosmic / IGM"),
        Line2D([0], [0], color=_INTERV_COLOR, lw=0.7, alpha=0.30,
               label="intervening system(s)"),
        Line2D([0], [0], color=_DARK_BLUE, lw=0.8, ls="--", alpha=0.45,
               label="intervening sightline sum"),
    ]

    for i, r in enumerate(results):
        ax = axes[i]

        sys_rows = systems_by_tns.get(r["name"], [])
        sys_draws = [
            sample_system_column(s["dm_point"], s["mass_source"], N_DRAW)
            for s in sys_rows
        ]

        parts = [r["samples"], r["disk"], r["halo"], r["cosmic"], r["interv"], *sys_draws]
        pooled = np.concatenate([p[np.isfinite(p)] for p in parts if len(p)])
        x_lo, x_hi = np.percentile(pooled, [1.0, 99.0])
        pad = 0.06 * max(x_hi - x_lo, 1.0)
        x_lo, x_hi = x_lo - pad, x_hi + pad
        x = np.linspace(x_lo, x_hi, 360)

        def plot_faded(samples, color, lw=0.8, ls="-"):
            dens = _peak_norm(_kde_1d(samples, x))
            ax.plot(x, dens, color=color, lw=lw, ls=ls, alpha=0.28, zorder=2)
            ax.fill_between(x, 0.0, dens, color=color, alpha=0.04, zorder=1)

        plot_faded(r["disk"], _MW_COLOR)
        plot_faded(r["halo"], _HALO_COLOR)
        plot_faded(r["cosmic"], _COSMIC_COLOR)

        for j, draws in enumerate(sys_draws):
            dens = _peak_norm(_kde_1d(draws, x))
            a = 0.22 + 0.05 * (j % 3)
            ax.plot(x, dens, color=_INTERV_COLOR, lw=0.7, alpha=a, zorder=2)
            ax.fill_between(x, 0.0, dens, color=_INTERV_COLOR, alpha=0.03, zorder=1)

        if r["dm_int"] > 0:
            dens_int = _peak_norm(_kde_1d(r["interv"], x))
            ax.plot(x, dens_int, color=_DARK_BLUE, lw=0.8, ls="--", alpha=0.40, zorder=3)

        dens_h = _peak_norm(_kde_1d(r["samples"], x))
        ax.plot(x, dens_h, color=_HOST_COLOR, lw=1.5, zorder=5)
        ax.fill_between(x, 0.0, dens_h, color=_HOST_COLOR, alpha=0.22, zorder=4)
        ax.axvline(0.0, color="0.55", lw=0.5, ls=":", zorder=0)
        ax.axvline(r["dm_host_p50"], color=_HOST_COLOR, lw=0.6, ls="--", alpha=0.7, zorder=4)

        short = r["name"].replace("FRB ", "")
        dagger = r"$\dagger$" if r["name"] in UPPER_LIMIT else ""
        ax.set_title(f"{short}{dagger}  ($z={r['z']:.3f}$)", pad=3)
        ax.set_xlim(x_lo, x_hi)
        ax.set_ylim(0.0, 1.18)
        ax.set_yticks([0.0, 0.5, 1.0])
        if i >= n - ncols:
            ax.set_xlabel(r"DM (pc cm$^{-3}$)")
        if i % ncols == 0:
            ax.set_ylabel(r"$\hat{p}$")

    for j in range(n, nrows * ncols):
        axes[j].set_visible(False)

    fig.legend(
        handles=legend_handles, loc="outside lower center", ncol=3, frameon=False,
    )
    fig.savefig(OUT_FIG, bbox_inches="tight")
    fig.savefig(OUT_FIG_PNG, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT_FIG.relative_to(REPO)}")


if __name__ == "__main__":
    main()
