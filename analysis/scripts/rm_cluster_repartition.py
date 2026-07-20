"""Kulkarni Thread 1: RM re-partition and intracluster B-field bound (FRB 20230307A).

Predeclared record: docs/rse/specs/plan/plan-rm-cluster-bfield-repartition-2026-07-17.md
(frozen materiality rule, literature selection criteria, both-owners gate).
This module implements Phases 0-2: pin verification, the negligibility-field
algebra, the literature comparison, and the conditional re-partition MC.

Run:  uv run --project pipeline --frozen python scripts/rm_cluster_repartition.py
Emits scripts/rm_cluster_repartition.json and
docs/rse/decks/thread1-2026-07-17/rm_repartition_sensitivity.pdf.

Physics: RM = 0.812 * B_par * DM_rest (rad m^-2, B in uG, DM in pc cm^-3;
Han 2017 ARA&A convention, reciprocal of the companion's B = 1.232 RM/DM).
A screen at z contributes RM_rest/(1+z)^2 to the observed RM, while the
budget's cluster columns are observer-frame (DM_rest/(1+z)), so
RM_cl(obs) = 0.812 * DM_cl(obs) / (1+z_cl) per uG of coherent field.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

# --- Pinned inputs (every value machine-verified by tests/test_rm_cluster_repartition.py) ---
PINNED = {
    # pipeline/galaxies/foreground/data/intervening_census_registry.csv:23
    # (J115120.4+714435 / Wen+ 1254337, the phineas cluster row)
    "m500_1e14": 1.48,
    "b_kpc": 603.6,
    "b_over_r500": 0.83,
    "r500_mpc": 0.729,
    "z_cl": 0.200,
    "z_host": 0.271,
    # scripts/dm_budget_uncertainty.csv:12-13 (origin/main e8c08cc8; observer frame)
    "dm_cl_beta_p16_p50_p84": (137.0, 200.0, 265.0),
    "dm_cl_95ci": (84.0, 328.0),
    # sections/appendix.tex fig:clusters_icm caption (carried mNFW central)
    "dm_cl_mnfw_central": 184.0,
    # codetections_polarization/main.tex:165 (tb:host_props, 2026-07-17 draft)
    "rm_obs": -473.49,
    "rm_obs_err": 0.09,
    "rm_host": -756.0,
    "rm_host_err": 15.0,
    "dm_host": 464.0,
    "dm_host_err_hi": 56.0,
    "dm_host_err_lo": 130.0,
    "b_host_mug": -2.0,
    # codetections_polarization/main.tex:146 (their MC prior)
    "rm_igm_sigma": 6.0,
}

Z_CL = PINNED["z_cl"]
Z_HOST = PINNED["z_host"]
K_RM = 0.812  # rad m^-2 per (uG * pc cm^-3), rest frame

# Their host-frame sigma(RM_host)=15 expressed at the observer: the materiality
# yardstick of the frozen rule (plan, Implementation Approach).
SIGMA_RM_OBS = PINNED["rm_host_err"] / (1.0 + Z_HOST) ** 2

# Foreground (Galactic) RM prior recovered by closure on the companion's own MC
# medians (plan Phase 2 substitution: the Hutschenreuter map value is not
# fetchable offline). Median: RM_obs - RM_host/(1+z_host)^2 with RM_IGM median 0.
# Width: their 15 (host frame) -> 9.29 obs, minus the IGM (6) and RM_obs (0.09)
# variances in quadrature.
RM_MW_CLOSURE = PINNED["rm_obs"] - PINNED["rm_host"] / (1.0 + Z_HOST) ** 2
RM_MW_SIGMA = math.sqrt(
    SIGMA_RM_OBS**2 - PINNED["rm_igm_sigma"] ** 2 - PINNED["rm_obs_err"] ** 2
)


def rm_per_microgauss_obs(dm_cl_obs: float) -> float:
    """Observed-frame cluster RM per uG of coherent field, from the observer-frame column.

    RM_rest = K_RM * B * DM_rest = K_RM * B * DM_obs*(1+z_cl); observed
    RM = RM_rest/(1+z_cl)^2 -> K_RM * DM_obs / (1+z_cl) = 0.6767 * DM_obs.
    """
    return K_RM * dm_cl_obs / (1.0 + Z_CL)


def b_negligibility(dm_cl_obs: float) -> float:
    """Coherent field (uG) at which the cluster term equals their 1-sigma RM_host error."""
    return SIGMA_RM_OBS / rm_per_microgauss_obs(dm_cl_obs)


# --- Phase 1: literature outskirt-RM comparison (frozen criteria, plan v1.0) ---
# Criteria: peer-reviewed; statistical (>=10 background/embedded sightlines) or
# mass-matched RM-calibrated simulation; reports RM vs normalized impact
# parameter covering b/R500 in [0.6, 1.0]; >=3 independent studies.
# Values verified against the published articles on 2026-07-17 (A&A full-text
# for Osinga 2025 and Boehringer 2016; Anderson 2021 via the MeerKAT Fornax IV
# summary of its ASKAP grid). Local-universe values; the (1+z_cl)^-2 dilution
# is applied to our predicted contribution at the z=0.2 screen.
#
# 2026-07-17 Undermind sweep (criteria UNCHANGED; additions + per-study value
# corrections only, each re-verified against the paper full text):
#   * Boehringer 0.5-1.0 r500: the paper's own text (144+/-43) and Table 1
#     (Galactic-corrected 112+/-43, uncorrected 114+/-43) disagree; the
#     tabulated Galactic-corrected value is adopted. 144 -> 112.
#   * The prior "Osinga 2022+2025" entry conflated the 2022 depolarization
#     paper (per-source sigma_RM fits, not a population excess -> rejected
#     below) with the 2024/25 RM-scatter paper. The 2024/25 paper tabulates
#     our exact bin for BACKGROUND sources (the FRB's class): 51+/-6
#     rest-frame, replacing the beyond-R500 floor of 28.
#   * Values are entered as published with the RM frame noted per study
#     (v1.0 convention); only Osinga is rest-frame, all others observed-frame
#     at z_cl <= 0.05 (<=10% effect, small vs the study-to-study spread).
LITERATURE = {
    "admitted": [
        {
            "study": "Boehringer, Chon & Kronberg 2016 (A&A 596, A22; CLASSIX)",
            "n_sightlines": 1722,
            "mass_range_1e14": (0.02, 19.1),
            "bin": "0.5-1.0 r500",
            "sigma_rm_local": 112.0,
            "sigma_rm_local_err": 43.0,
            "note": "Table 1 Galactic-corrected (verified 2026-07-17); the running text prints 144+/-43 for the same bin -- internal discrepancy recorded, table adopted; mixed member/background sources, signal weighted toward luminous systems (158+/-34 vs 62+/-11 luminosity halves)",
        },
        {
            "study": "Osinga et al. 2024/25 (A&A, arXiv:2408.07178; 124 Planck clusters)",
            "n_sightlines": 363,
            "mass_range_1e14": (2.0, 15.0),
            "bin": "0.5-1.0 R500, background sources, cluster rest frame (their Table 2)",
            "sigma_rm_local": 51.0,
            "sigma_rm_local_err": 6.0,
            "note": "direct tabulated bin for the FRB-relevant background class (all-source 127+/-30, embedded 219+/-59, outside control 28+/-5); mean mass 5.7e14 (only 15/124 below 3e14) -> ABOVE-target bracket; supersedes the v1.0 beyond-R500 floor of 28",
        },
        {
            "study": "Anderson et al. 2021 (Fornax, ASKAP/POSSUM grid)",
            "n_sightlines": 76,
            "mass_range_1e14": (0.6, 0.6),
            "bin": "within 360 kpc ~ 0.8 R500 (r200=0.7 Mpc); 76 polarized sources inside 1 deg",
            "sigma_rm_local": 17.0,
            "sigma_rm_local_err": 2.4,
            "system": "fornax",
            "note": "16.8+/-2.4 quadrature excess (bootstrap 95%), M~6e13 BELOW target (conservative); enhancement asymmetric (merger axis); same physical system as Loi 2025 -- collapsed to one Fornax vote per the plan v1.3 adjudication",
        },
        {
            "study": "Khadir et al. 2025 (A3581, ApJ 997, 214; arXiv:2511.18532)",
            "n_sightlines": 111,
            "mass_range_1e14": (2.15, 2.15),
            "bin": "moving-bin corrected profile across 0.6-1.0 R500 (their Fig. 2b; figure estimate)",
            "sigma_rm_local": 8.0,
            "sigma_rm_local_err": 3.0,
            "note": "figure-estimated 5-12 across the bin (10-12 @0.6, 5-7 @0.8, 8-10 @1.0 R500); control 7.0+/-1.3 subtracted in quadrature; background-only; M500=2.15e14 just above the 1.7e14 target cap (nearest-mass single-cluster profile in the set); observed frame (z=0.022, <5%)",
        },
        {
            "study": "Loi et al. 2025 (MeerKAT Fornax IV, A&A 694, A125; arXiv:2501.05519)",
            "n_sightlines": 503,
            "mass_range_1e14": (0.5, 0.5),
            "bin": "outer annuli 400-510 kpc ~ 0.86-1.10 R500 via R_vir=705 kpc, R500~0.66 R_vir (external conversion)",
            "sigma_rm_local": 11.5,
            "sigma_rm_local_err": 1.5,
            "system": "fornax",
            "note": "outer plateau ~13 raw minus the authors' ~6 non-cluster floor in quadrature -> ~11.5 cluster-attributable; densest RM grid (80/deg^2), background-only; SAME SYSTEM as Anderson 2021 -- collapsed to one Fornax vote per the plan v1.3 adjudication; observed frame (z~0.005)",
        },
        {
            "study": "Alonso-Lopez et al. 2025 (Shapley SC core, A&A; arXiv:2511.14377)",
            "n_sightlines": 34,
            "mass_range_1e14": (0.5, 9.8),
            "bin": "cluster regions, nearest-object d/r500 in 0.3-1.8 (printed aggregate; profile flattens beyond ~0.7 r500)",
            "sigma_rm_local": 27.2,
            "sigma_rm_local_err": 5.0,
            "note": "printed cluster-regions excess 27.20+/-4.97 after off-target subtraction (SSC total 30.52+/-4.55); includes below-target SC1329 (0.5e14) and near-target SC1327 (2.0e14); overlapping halos / supercluster geometry -- not an isolated-halo profile; observed frame (z=0.048, ~10%)",
        },
    ],
    "rejected": [
        {"study": "Clarke, Kronberg & Boehringer 2001", "reason": "no normalized-radius profile; sightlines concentrated inside ~0.6 R500-equivalent"},
        {"study": "Bonafede et al. 2010 (Coma)", "reason": "7 sightlines < 10 (criteria minimum)"},
        {"study": "Govoni et al. 2017 (A194)", "reason": "few extended sources in one cluster, < 10 sightlines"},
        {"study": "Stuardi et al. 2021 (A2345)", "reason": "single-cluster relic study, < 10 sightlines; no [0.6,1.0] profile"},
        {"study": "Anderson et al. 2024 (POSSUM groups, MNRAS)", "reason": "0-2 splashback-radius aperture (~0-4 R200c) mixes radii far inside and outside the target bin -- neither extractable nor one-sided-boundable at 0.6-1.0 R500; K-band group-halo masses with no M500 convention"},
        {"study": "Osinga et al. 2022 (A&A 665, A71; depolarization)", "reason": "per-source Faraday-dispersion fits, not a population cluster-induced sigma_RM radial measurement (was conflated into the v1.0 Osinga entry; split out 2026-07-17)"},
        {"study": "Kim, Kronberg & Tribble 1991", "reason": "Abell-radius bins only (R_A=3 h50^-1 Mpc), no modern mass or R500/R200 convention; mixed member/background classes (same class of defect as Clarke 2001)"},
    ],
}


def rm_lit_obs() -> float:
    """Median admitted local sigma_RM at ~0.6-1.0 R500, diluted to the z=0.2 screen.

    One system, one vote (plan v1.3 adjudication, owner-delegated 2026-07-17):
    entries sharing a "system" key collapse to their mean before the median,
    so the two Fornax studies (Anderson 2021, Loi 2025) contribute a single
    value. With the current set the median is 27.2 regardless of whether the
    collapse takes the mean, Anderson alone, or Loi alone -- recorded in the
    plan so the choice cannot be mistaken for tuning.
    """
    by_system: dict[str, list[float]] = {}
    for s in LITERATURE["admitted"]:
        by_system.setdefault(s.get("system", s["study"]), []).append(s["sigma_rm_local"])
    vals = sorted(float(np.mean(v)) for v in by_system.values())
    med = float(np.median(vals))
    return med / (1.0 + Z_CL) ** 2


def classify(rm_lit: float) -> str:
    """Frozen materiality rule (plan v1.0): thresholds are NOT tunable here."""
    if rm_lit >= 2.0 * SIGMA_RM_OBS:
        return "material"
    if rm_lit < SIGMA_RM_OBS:
        return "null"
    return "marginal"


# --- Phase 2: conditional re-partition MC ---
_POOL_CACHE: dict[int, np.ndarray] = {}


def _cluster_pool(size: int) -> np.ndarray:
    """One deterministic draw from the budget's truncated beta-model MC.

    dm_budget_uncertainty seeds its module RNG (20260707) at import; the first
    cluster_column_range call in a process is therefore deterministic. Cached so
    repeated repartition_mc calls in one process reuse the same pool.
    """
    if size not in _POOL_CACHE:
        import dm_budget_uncertainty as dbu

        if not hasattr(dbu, "CL_M500_XRAY_UL"):
            raise RuntimeError(
                "dm_budget_uncertainty lacks CL_M500_XRAY_UL - run from origin/main >= 56cf4c4e"
            )
        _POOL_CACHE[size] = np.asarray(dbu.cluster_column_range(n=size))
    return _POOL_CACHE[size]


def _two_sided(rng: np.random.Generator, med: float, s_hi: float, s_lo: float, n: int) -> np.ndarray:
    """Asymmetric (split-normal) draw with median `med`, upper/lower 1-sigma widths."""
    lo = med - np.abs(rng.normal(0.0, s_lo, n))
    hi = med + np.abs(rng.normal(0.0, s_hi, n))
    pick_hi = rng.random(n) < 0.5  # equal mass on each side keeps the median at `med`
    return np.where(pick_hi, hi, lo)


B_CL_GRID = (0.0, 0.1, -0.1, 0.25, -0.25, 0.5, -0.5, 1.0, -1.0)


def repartition_mc(
    b_cl_grid=B_CL_GRID, n: int = 10_000, seed: int = 20260707, pool_size: int = 4000
) -> dict:
    """Re-partition table: their RM budget + one cluster term, scanned over B_cl.

    Mirrors the companion MC structure (10^4 trials; Gaussian RM_obs; Gaussian
    Galactic prior [closure substitution]; RM_IGM ~ N(0,6)) with
    RM_cl(obs) = K_RM * B_cl * DM_cl(obs)/(1+z_cl), DM_cl bootstrapped from the
    budget's truncated-prior beta-model pool. Emits, per B_cl:
      - rm_host (host frame) percentiles,
      - b_host under their published DM_host ("as-published") and under the
        cluster-corrected DM_host = DM_host - DM_cl(obs)*(1+z_host),
      - the implied RM_cl(obs) band.
    """
    pool = _cluster_pool(pool_size)
    rng = np.random.default_rng(seed)
    out = {}
    for b_cl in b_cl_grid:
        dm_cl = rng.choice(pool, size=n, replace=True)
        rm_obs = rng.normal(PINNED["rm_obs"], PINNED["rm_obs_err"], n)
        rm_mw = rng.normal(RM_MW_CLOSURE, RM_MW_SIGMA, n)
        rm_igm = rng.normal(0.0, PINNED["rm_igm_sigma"], n)
        rm_cl_obs = K_RM * b_cl * dm_cl / (1.0 + Z_CL)
        rm_host = (rm_obs - rm_mw - rm_igm - rm_cl_obs) * (1.0 + Z_HOST) ** 2

        dm_host_pub = _two_sided(
            rng, PINNED["dm_host"], PINNED["dm_host_err_hi"], PINNED["dm_host_err_lo"], n
        )
        dm_host_corr = dm_host_pub - dm_cl * (1.0 + Z_HOST)

        def _b(rm, dm):
            ok = dm > 0
            b = np.full(n, np.nan)
            b[ok] = 1.232 * rm[ok] / dm[ok]
            return b, float(np.mean(~ok))

        b_pub, f_neg_pub = _b(rm_host, dm_host_pub)
        b_corr, f_neg_corr = _b(rm_host, dm_host_corr)

        pct = lambda a: [float(x) for x in np.nanpercentile(a, [16, 50, 84])]
        out[b_cl] = {
            "rm_cl_obs_p16_p50_p84": pct(rm_cl_obs) if b_cl != 0.0 else [0.0, 0.0, 0.0],
            "rm_host_p16_p50_p84": pct(rm_host),
            "rm_host_p50": float(np.nanpercentile(rm_host, 50)),
            "b_host_pub_p16_p50_p84": pct(b_pub),
            "b_host_p50": float(np.nanpercentile(b_pub, 50)),
            "b_host_corr_p16_p50_p84": pct(b_corr),
            "frac_dm_host_nonpos_pub": f_neg_pub,
            "frac_dm_host_nonpos_corr": f_neg_corr,
        }
    return out


def make_figure(mc: dict, path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    grid = sorted(mc.keys())
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 3.8), constrained_layout=True)

    def band(ax, key, color, label):
        p16 = [mc[b][key][0] for b in grid]
        p50 = [mc[b][key][1] for b in grid]
        p84 = [mc[b][key][2] for b in grid]
        ax.fill_between(grid, p16, p84, alpha=0.25, color=color)
        ax.plot(grid, p50, "o-", color=color, label=label)

    band(axes[0], "rm_host_p16_p50_p84", "C0", "host frame")
    axes[0].axhline(PINNED["rm_host"], ls="--", c="k", lw=0.8)
    axes[0].set_ylabel(r"RM$_{\rm host}$ (rad m$^{-2}$)")
    axes[0].set_title("re-partitioned host RM")

    band(axes[1], "b_host_pub_p16_p50_p84", "C1", "DM$_{host}$ as published")
    band(axes[1], "b_host_corr_p16_p50_p84", "C3", "DM$_{host}$ cluster-corrected")
    axes[1].axhline(PINNED["b_host_mug"], ls="--", c="k", lw=0.8)
    axes[1].set_ylabel(r"$\langle B_{\parallel,\rm host}\rangle$ ($\mu$G)")
    axes[1].legend(fontsize=7)
    axes[1].set_title("host field")

    band(axes[2], "rm_cl_obs_p16_p50_p84", "C2", "cluster term")
    for s in (1.0, 2.0):
        axes[2].axhline(s * SIGMA_RM_OBS, ls=":", c="gray", lw=0.8)
        axes[2].axhline(-s * SIGMA_RM_OBS, ls=":", c="gray", lw=0.8)
    axes[2].set_ylabel(r"RM$_{\rm cl}^{\rm obs}$ (rad m$^{-2}$)")
    axes[2].set_title(r"implied cluster RM (dotted: 1,2$\sigma_{\rm RM}^{\rm obs}$)")

    for ax in axes:
        ax.set_xlabel(r"$\langle B_{\parallel,\rm cl}\rangle$ ($\mu$G)")
        ax.grid(alpha=0.2)
    fig.suptitle(
        "FRB 20230307A RM re-partition vs. assumed intracluster field "
        f"(DM$_{{\\rm cl}}$ from the truncated-prior MC; $b/R_{{500}}=0.83$)",
        fontsize=9,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)


def main() -> int:
    neg_table = {
        str(dm): {
            "rm_per_uG_obs": round(rm_per_microgauss_obs(dm), 1),
            "b_neg_uG": round(b_negligibility(dm), 3),
        }
        for dm in (84.0, 184.0, 200.0, 328.0)
    }
    rm_lit = rm_lit_obs()
    verdict = classify(rm_lit)
    mc = repartition_mc()

    artifact = {
        "plan": "docs/rse/specs/plan/plan-rm-cluster-bfield-repartition-2026-07-17.md",
        "pinned": {k: v for k, v in PINNED.items()},
        "sigma_rm_obs": round(SIGMA_RM_OBS, 3),
        "thresholds_obs": {"material_ge": round(2 * SIGMA_RM_OBS, 2), "null_lt": round(SIGMA_RM_OBS, 2)},
        "rm_mw_closure_substitution": {
            "median": round(RM_MW_CLOSURE, 3),
            "sigma": round(RM_MW_SIGMA, 3),
            "note": "Galactic RM prior recovered by closure on the companion's MC medians (map not fetchable offline)",
        },
        "negligibility_table": neg_table,
        "literature": LITERATURE,
        "rm_lit_obs": round(rm_lit, 2),
        "classification": verdict,
        "repartition_mc": {str(k): v for k, v in mc.items()},
        "mc_config": {"n": 10_000, "seed": 20260707, "pool_size": 4000, "b_cl_grid": list(B_CL_GRID)},
    }
    out = ROOT / "scripts" / "rm_cluster_repartition.json"
    out.write_text(json.dumps(artifact, indent=1, sort_keys=True) + "\n")
    make_figure(mc, ROOT / "docs/rse/decks/thread1-2026-07-17/rm_repartition_sensitivity.pdf")

    print(f"sigma_RM(obs) yardstick : {SIGMA_RM_OBS:.2f} rad/m^2")
    print(f"RM_lit (obs, diluted)   : {rm_lit:.2f} rad/m^2  -> classification: {verdict.upper()}")
    for dm, row in neg_table.items():
        print(f"  DM_cl={dm:>6} pc/cm^3 : RM/B={row['rm_per_uG_obs']:6.1f}  B_neg={row['b_neg_uG']:.3f} uG")
    row0 = mc[0.0]
    print(f"zero-cluster corner     : RM_host p50 = {row0['rm_host_p50']:.1f} (companion: -756)")
    print(f"                          B_host p50  = {row0['b_host_p50']:.2f} (companion: -2.0)")
    print(f"artifact: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
