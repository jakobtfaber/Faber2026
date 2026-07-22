#!/usr/bin/env python
"""Forward-model the per-sightline DM_host posteriors and the FRB 20230307A
intracluster column, with physically motivated uncertainty propagation.

Referee blocking items B1 and B2. The point-estimate budget in
``budget_table.tex`` subtracts the *mean* of the highly skewed cosmological
DM distribution, which biases every host residual (Macquart et al. 2020; James
et al. 2022). Here we instead convolve the full P(DM_cosmic | z) and the nuisance
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

Self-contained: numpy + scipy only. Point-estimate component inputs are joined
from the current budget SSOT, exact adopted-DM catalog, and per-system census.

DM_host here is the OBSERVER-FRAME residual (no 1+z factor); the rest-frame host
column is (1+z) larger and is tabulated alongside it in the manuscript. For the
six sightlines outside the deep-imaging footprints (UPPER_LIMIT below) the
foreground census is incomplete and DM_int is a floor; with the IGM-marginal
cosmic term (halos excluded), an undetected halo lands in the host residual, so
those DM_host are upper limits (dagger on the figure panel titles).

The figure is a 3x3 of peak-normalized PDFs per redshift-constrained sightline:
faded MW-disk / MW-halo / IGM / per-system intervening curves under a bold
P(DM_host). Most curves are direct numerical PDFs. The two boundary-sensitive
Phineas halos use a fixed, deterministic Sobol integration; no kernel-density
estimate enters the host results or figure.

Regenerate: python scripts/dm_budget_uncertainty.py
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy import integrate, interpolate, signal, stats

import phineas_halo_crossing_probability as phineas_crossing

REPO = Path(__file__).resolve().parent.parent
OUT_CSV = REPO / "scripts" / "dm_budget_uncertainty.csv"
OUT_FIG = REPO / "figures" / "dm_host_posteriors.pdf"
OUT_FIG_PNG = REPO / "figures" / "dm_host_posteriors.png"
BUDGET_DATA = REPO / "pipeline" / "galaxies" / "foreground" / "budget_table_data.json"
DM_CATALOG = REPO / "analysis" / "dm-joint-phase-v2" / "manuscript_dm_catalog.csv"
SYSTEMS_CSV = REPO / "scripts" / "dm_budget_intervening_systems.csv"

RNG = np.random.default_rng(20260707)
GRID_DX = 0.1
TAIL_MASS = 1e-10
IGM_QUADRATURE_ORDER = 64

# --- Per-sightline point-estimate budget ---------------------------------------
# DM in pc cm^-3. DM_MW is disk(NE2025)+40 halo; we split the 40 back out below.
# Placeholder-z sightlines (freya/mahi/wilhelm) are excluded: no cosmic/host term.
DM_MW_HALO = 40.0


@dataclass(frozen=True)
class InterveningSystem:
    object: str
    kind: str
    mass_source: str
    model: str
    dm_point: float
    impact_kpc: float


@dataclass(frozen=True)
class Sightline:
    name: str
    z: float
    dm_obs: float
    dm_obs_sigma: float
    dm_mw: float
    dm_cos_mean: float
    dm_int: float
    intervening_systems: tuple[InterveningSystem, ...]


@dataclass(frozen=True)
class DiscretePDF:
    """A uniformly sampled, normalized probability density."""

    x0: float
    dx: float
    density: np.ndarray

    def __post_init__(self) -> None:
        density = np.asarray(self.density, dtype=float)
        if density.ndim != 1 or density.size == 0:
            raise ValueError("density must be a non-empty one-dimensional array")
        if not math.isfinite(self.dx) or self.dx <= 0:
            raise ValueError("dx must be finite and positive")
        if not np.all(np.isfinite(density)):
            raise ValueError("density must be finite")
        if float(density.min()) < -1e-12:
            raise ValueError("density contains negative values")
        density = np.clip(density, 0.0, None)
        norm = float(density.sum() * self.dx)
        if not math.isfinite(norm) or norm <= 0:
            raise ValueError("density must have positive finite integral")
        density = density / norm
        density.setflags(write=False)
        object.__setattr__(self, "density", density)

    @property
    def x(self) -> np.ndarray:
        return self.x0 + self.dx * np.arange(self.density.size)


# Sightlines outside the deep-imaging footprints (budget_table.tex note u): the
# intervening census is incomplete, so DM_int is a floor. With the IGM-marginal
# cosmic term (which excludes virialized halos), any undetected foreground halo
# is absorbed into the host residual -> DM_host is an UPPER LIMIT, flagged with a
# dagger on the figure panel titles.
UPPER_LIMIT = {
    "FRB 20220207C",
    "FRB 20220506D",
    "FRB 20221113A",
    "FRB 20230814B",
    "FRB 20230913A",
    "FRB 20240203A",
}

# --- Nuisance priors -----------------------------------------------------------
# Diffuse cosmic (IGM) column: Connor et al. (2025) fit the IGM baryon fraction
# f_IGM = 0.76 (+0.10/-0.11) from the DSA-110 + literature FRB sample. We
# marginalize f_IGM over this (asymmetric-normal, clipped to (0, 0.98]) to carry
# the feedback/partition uncertainty; it shifts the IGM log-mean by
# log(f_IGM / f_IGM,TNG). The redshift-dependent log-normal shape (mu, sigma) is
# fixed to the TNG-300 calibration below.
FIGM_MED, FIGM_SIG_LO, FIGM_SIG_HI = 0.76, 0.11, 0.10
FIGM_TNG = 0.797  # TNG-300 baseline f_IGM in Connor et al. calibration
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
TNG_MU_IGM = np.array(
    [
        4.37380909,
        5.07264111,
        5.4962193,
        5.80209722,
        6.04344301,
        6.40614181,
        6.78312432,
        7.19849362,
        7.48250248,
        7.86255147,
        8.11920163,
        8.30542453,
    ]
)
TNG_SIG_IGM = np.array(
    [
        0.33479241,
        0.29198339,
        0.25434913,
        0.22449515,
        0.20123352,
        0.17974651,
        0.16545537,
        0.14851468,
        0.13239113,
        0.11009793,
        0.09384749,
        0.08155763,
    ]
)
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
OMEGA_M, OMEGA_LAMBDA = 0.3111, 0.6889  # flat LCDM, Planck 2018 (TT,TE,EE+lowE+lensing)


def _macquart_integral(z: float) -> float:
    """int_0^z (1+z')/E(z') dz', the redshift dependence of <DM_IGM>."""
    val, _ = integrate.quad(
        lambda x: (1.0 + x) / math.sqrt(OMEGA_M * (1.0 + x) ** 3 + OMEGA_LAMBDA),
        0.0,
        z,
        limit=200,
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


def normal_pdf(
    mean: float, sigma: float, *, dx: float = GRID_DX, tail_mass: float = TAIL_MASS
) -> DiscretePDF:
    """Discretize a normal density on a symmetric tail-bounded grid."""
    if sigma <= 0:
        raise ValueError("sigma must be positive")
    q = stats.norm.ppf(1.0 - tail_mass / 2.0)
    x0 = math.floor((mean - q * sigma) / dx) * dx
    x1 = math.ceil((mean + q * sigma) / dx) * dx
    x = np.arange(x0, x1 + 0.5 * dx, dx)
    return DiscretePDF(x0=x0, dx=dx, density=stats.norm.pdf(x, loc=mean, scale=sigma))


def lognormal_pdf(
    median: float,
    sigma_ln: float,
    *,
    dx: float = GRID_DX,
    tail_mass: float = TAIL_MASS,
) -> DiscretePDF:
    """Discretize a lognormal whose quoted point value is its median."""
    if median <= 0 or sigma_ln <= 0:
        raise ValueError("median and sigma_ln must be positive")
    x1 = (
        math.ceil(stats.lognorm.ppf(1.0 - tail_mass, s=sigma_ln, scale=median) / dx)
        * dx
    )
    x = np.arange(0.0, x1 + 0.5 * dx, dx)
    density = stats.lognorm.pdf(x, s=sigma_ln, scale=median)
    return DiscretePDF(x0=0.0, dx=dx, density=density)


def delta_pdf(value: float = 0.0, *, dx: float = GRID_DX) -> DiscretePDF:
    """Represent an exact grid-aligned point mass for convolution bookkeeping."""
    grid_value = round(value / dx) * dx
    if not math.isclose(value, grid_value, abs_tol=1e-12):
        raise ValueError("delta value must be aligned to the PDF grid")
    return DiscretePDF(x0=grid_value, dx=dx, density=np.array([1.0 / dx]))


def igm_mixture_pdf(
    z: float,
    *,
    dx: float = GRID_DX,
    tail_mass: float = TAIL_MASS,
    quadrature_order: int = IGM_QUADRATURE_ORDER,
) -> DiscretePDF:
    """Marginalize the TNG lognormal over the clipped asymmetric f_IGM prior.

    Gauss-Legendre quadrature is applied separately to each smooth side of the
    asymmetric prior. The probability clipped onto each physical endpoint is
    included exactly as a point mass in f_IGM.
    """
    if quadrature_order < 2:
        raise ValueError("quadrature_order must be at least 2")
    nodes, base_weights = leggauss(quadrature_order)
    u_low = (FIGM_CLIP[0] - FIGM_MED) / FIGM_SIG_LO
    u_high = (FIGM_CLIP[1] - FIGM_MED) / FIGM_SIG_HI

    def interval(a: float, b: float, scale: float) -> tuple[np.ndarray, np.ndarray]:
        u = 0.5 * (b - a) * nodes + 0.5 * (a + b)
        weights = 0.5 * (b - a) * base_weights * stats.norm.pdf(u)
        return FIGM_MED + u * scale, weights

    figm_lo, weights_lo = interval(u_low, 0.0, FIGM_SIG_LO)
    figm_hi, weights_hi = interval(0.0, u_high, FIGM_SIG_HI)
    figm = np.concatenate(([FIGM_CLIP[0]], figm_lo, figm_hi, [FIGM_CLIP[1]]))
    weights = np.concatenate(
        ([stats.norm.cdf(u_low)], weights_lo, weights_hi, [stats.norm.sf(u_high)])
    )
    weights = weights / weights.sum()
    mu_tng, sigma_ln = igm_lognormal_shape(z)
    medians = np.exp(mu_tng) * figm / FIGM_TNG
    upper = max(
        stats.lognorm.ppf(1.0 - tail_mass, s=sigma_ln, scale=float(median))
        for median in medians
    )
    x1 = math.ceil(upper / dx) * dx
    x = np.arange(0.0, x1 + 0.5 * dx, dx)
    density = np.zeros_like(x)
    for weight, median in zip(weights, medians):
        density += weight * stats.lognorm.pdf(x, s=sigma_ln, scale=median)
    return DiscretePDF(x0=0.0, dx=dx, density=density)


def convolve_pdfs(pdfs: list[DiscretePDF] | tuple[DiscretePDF, ...]) -> DiscretePDF:
    """Convolve independent PDFs, preserving density units and normalization."""
    if not pdfs:
        raise ValueError("at least one PDF is required")
    dx = pdfs[0].dx
    if any(not math.isclose(pdf.dx, dx, rel_tol=0.0, abs_tol=1e-12) for pdf in pdfs):
        raise ValueError("all PDFs must share the same dx")
    density = pdfs[0].density.copy()
    for pdf in pdfs[1:]:
        density = signal.fftconvolve(density, pdf.density, mode="full") * dx
        density = np.clip(density, 0.0, None)
    return DiscretePDF(x0=sum(pdf.x0 for pdf in pdfs), dx=dx, density=density)


def host_pdf_from_foreground(foreground: DiscretePDF, dm_obs: float) -> DiscretePDF:
    """Reflect total foreground about measured DM: host = observed - foreground."""
    return DiscretePDF(
        x0=dm_obs - foreground.x[-1],
        dx=foreground.dx,
        density=foreground.density[::-1],
    )


def pdf_quantile(pdf: DiscretePDF, probability: float) -> float:
    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability must lie in [0, 1]")
    cdf = np.cumsum(pdf.density) * pdf.dx
    return float(np.interp(probability, cdf, pdf.x, left=pdf.x[0], right=pdf.x[-1]))


def pdf_cdf_at(pdf: DiscretePDF, value: float) -> float:
    cdf = np.cumsum(pdf.density) * pdf.dx
    return float(np.interp(value, pdf.x, cdf, left=0.0, right=1.0))


def _system_sigma(mass_source: str) -> float:
    if mass_source == "cluster_catalog":
        return INT_SIGMA_LN["cluster"]
    if mass_source in {"measured", "glade_catalog"}:
        return INT_SIGMA_LN["measured"]
    return INT_SIGMA_LN["assumed"]


def system_pdf(system: InterveningSystem, *, dx: float) -> DiscretePDF:
    """Return the adopted per-system distribution."""
    if system.model == "fixed_lognormal":
        return lognormal_pdf(system.dm_point, _system_sigma(system.mass_source), dx=dx)
    if system.model == "probabilistic_crossing":
        if not system.object:
            raise ValueError("probabilistic crossing system lacks an object identifier")
        x0, density = phineas_crossing.halo_dm_histogram(system.object, dx=dx)
        return DiscretePDF(x0=x0, dx=dx, density=density)
    raise ValueError(f"unknown intervening-system model: {system.model}")


def load_intervening_systems() -> dict[str, tuple[InterveningSystem, ...]]:
    """Load the current per-system census columns used by the budget."""
    by_tns: dict[str, list[InterveningSystem]] = {}
    with SYSTEMS_CSV.open(newline="") as handle:
        for row in csv.DictReader(handle):
            by_tns.setdefault(row["tns"], []).append(
                InterveningSystem(
                    object=row["object"],
                    kind=row["kind"],
                    mass_source=row["mass_source"],
                    model=row["model"],
                    dm_point=float(row["dm_point"]),
                    impact_kpc=float(row["impact_kpc"]),
                )
            )
    return {name: tuple(systems) for name, systems in by_tns.items()}


def load_sightlines() -> tuple[Sightline, ...]:
    """Join the budget SSOT, exact adopted-DM catalog, and system census."""
    with BUDGET_DATA.open() as handle:
        budget = json.load(handle)
    with DM_CATALOG.open(newline="") as handle:
        catalog = {row["tns"]: row for row in csv.DictReader(handle)}
    systems = load_intervening_systems()
    rows: list[Sightline] = []
    for row in budget["rows"]:
        if not isinstance(row["z"], (int, float)):
            continue
        name = row["burst"]
        if name not in catalog:
            raise ValueError(f"budget sightline {name} missing from adopted-DM catalog")
        sightline_systems = systems.get(name, ())
        dm_int = float(row["dm_int"])
        if dm_int == 0.0 and sightline_systems:
            raise ValueError(
                f"{name}: zero budget DM_int but census systems are present"
            )
        if dm_int > 0.0 and round(sum(s.dm_point for s in sightline_systems)) != dm_int:
            raise ValueError(
                f"{name}: per-system columns do not reproduce budget DM_int"
            )
        cat = catalog[name]
        rows.append(
            Sightline(
                name=name,
                z=float(row["z"]),
                dm_obs=float(cat["adopted_dm"]),
                dm_obs_sigma=float(cat["adopted_sigma"]),
                dm_mw=float(row["dm_mw"]),
                dm_cos_mean=float(row["dm_cos"]),
                dm_int=dm_int,
                intervening_systems=sightline_systems,
            )
        )
    extra_systems = set(systems) - {row.name for row in rows}
    if extra_systems:
        raise ValueError(
            f"intervening systems lack modeled sightlines: {sorted(extra_systems)}"
        )
    if len(rows) != 9:
        raise ValueError(
            f"expected 9 redshift-constrained sightlines, found {len(rows)}"
        )
    return tuple(rows)


def host_distribution(row: Sightline, *, dx: float = GRID_DX) -> dict:
    """Build a host-DM PDF by deterministic convolution of independent terms."""
    dm_disk = row.dm_mw - DM_MW_HALO
    if dm_disk <= 0:
        raise ValueError(f"{row.name}: non-positive MW disk column")
    disk = lognormal_pdf(dm_disk, SIGMA_DISK_FRAC, dx=dx)
    halo = lognormal_pdf(DM_MW_HALO, HALO_SIGMA_LN, dx=dx)
    cosmic = igm_mixture_pdf(row.z, dx=dx)
    system_pdfs = tuple(system_pdf(system, dx=dx) for system in row.intervening_systems)
    interv = convolve_pdfs(system_pdfs) if system_pdfs else delta_pdf(dx=dx)
    foreground = convolve_pdfs((disk, halo, cosmic, interv))
    host = host_pdf_from_foreground(foreground, row.dm_obs)
    p16, p50, p84 = (
        pdf_quantile(host, probability) for probability in (0.16, 0.5, 0.84)
    )
    r16, r50, r84 = ((1.0 + row.z) * value for value in (p16, p50, p84))
    int16, int50, int84 = (
        pdf_quantile(interv, probability) for probability in (0.16, 0.5, 0.84)
    )
    arithmetic_dm_int = (
        int50
        if any(
            system.model == "probabilistic_crossing"
            for system in row.intervening_systems
        )
        else row.dm_int
    )
    return {
        "name": row.name,
        "z": row.z,
        "dm_int": row.dm_int,
        "dm_int_p16": int16,
        "dm_int_p50": int50,
        "dm_int_p84": int84,
        "dm_host_arith": row.dm_obs - row.dm_mw - row.dm_cos_mean - arithmetic_dm_int,
        "dm_host_p16": p16,
        "dm_host_p50": p50,
        "dm_host_p84": p84,
        "dm_host_rest_p16": r16,
        "dm_host_rest_p50": r50,
        "dm_host_rest_p84": r84,
        "p_host_neg": pdf_cdf_at(host, 0.0),
        "host_pdf": host,
        "disk_pdf": disk,
        "halo_pdf": halo,
        "cosmic_pdf": cosmic,
        "interv_pdf": interv,
        "system_pdfs": system_pdfs,
    }


def sample_host_for_validation(
    row: Sightline,
    *,
    n: int,
    seed: int,
    prior_centering: str = "median",
) -> np.ndarray:
    """Independent Monte Carlo oracle; never used for published products.

    ``prior_centering='median'`` samples the adopted model. The legacy option
    reproduces the old mean-preserving lognormal factor and is retained only to
    separate the prior-definition correction from the numerical-method change.
    """
    if prior_centering not in {"median", "legacy_mean"}:
        raise ValueError("prior_centering must be 'median' or 'legacy_mean'")
    rng = np.random.default_rng(seed)

    def lognormal(median: float, sigma_ln: float) -> np.ndarray:
        mu = 0.0 if prior_centering == "median" else -0.5 * sigma_ln**2
        return median * rng.lognormal(mu, sigma_ln, n)

    disk = lognormal(row.dm_mw - DM_MW_HALO, SIGMA_DISK_FRAC)
    mw_halo = lognormal(DM_MW_HALO, HALO_SIGMA_LN)
    u = rng.normal(size=n)
    scale = np.where(u < 0.0, FIGM_SIG_LO, FIGM_SIG_HI)
    figm = np.clip(FIGM_MED + u * scale, *FIGM_CLIP)
    mu_tng, sigma_ln = igm_lognormal_shape(row.z)
    cosmic = rng.lognormal(mu_tng + np.log(figm / FIGM_TNG), sigma_ln)
    intervening = np.zeros(n)
    for index, system in enumerate(row.intervening_systems):
        if system.model == "fixed_lognormal":
            intervening += lognormal(system.dm_point, _system_sigma(system.mass_source))
        elif system.model == "probabilistic_crossing":
            halo_input = phineas_crossing.load_inputs()[system.object]
            draws = phineas_crossing.simulate_halo(
                halo_input,
                n=n,
                seed=seed + 10_000 + index,
                quasi=False,
            )
            intervening += draws.dm
        else:
            raise ValueError(f"unknown intervening-system model: {system.model}")
    return row.dm_obs - disk - mw_halo - cosmic - intervening


# --- B2: FRB 20230307A intracluster column (mNFW vs beta-model) ----------------
MU_E = 1.17  # mean molecular weight per electron (fully ionized, X=0.75)
M_P = 1.67262192e-27  # kg
MSUN = 1.98847e30  # kg
KPC_PC = 1.0e3  # pc per kpc

# Wen-Han 2024 cluster J115120.4+714435 toward FRB 20230307A.
CL_M500 = 1.48e14  # Msun
CL_R500_KPC = 729.0  # kpc
CL_Z = 0.200
CL_B_KPC = 603.6  # impact parameter (b/R500 = 0.83)
# RASS non-detection mass cap (owner-adjudicated conservative endpoint,
# ECF=1.2e-11): L_X(0.1-2.4 keV) < 9.1e43 erg/s at z=0.200 through the MCXC
# L500-M500 relation. Truncates the richness-mass prior's upper tail.
# docs/rse/specs/experiment-cluster-xray-sz-mass-bound-2026-07-17.md
CL_M500_XRAY_UL = 1.67e14  # Msun


def beta_model_dm(m500, r500_kpc, b_kpc, z, f_gas, rc_over_r500, beta):
    """Observer-frame intracluster DM from an isothermal beta-model.

    n_e(r) = n_e0 [1+(r/rc)^2]^{-3 beta/2}; n_e0 fixed by requiring the gas mass
    within R500 equal f_gas * M500. Chord integral at impact b, out to 3 R500.
    """
    KPC_M = 3.0856775814913673e19
    rc = rc_over_r500 * r500_kpc

    # Gas-mass normalization: M_gas(<R500) = f_gas M500 (integral in kpc^3).
    def shell(r):
        return 4.0 * math.pi * r**2 * (1.0 + (r / rc) ** 2) ** (-1.5 * beta)

    mass_integral_kpc3, _ = integrate.quad(shell, 0.0, r500_kpc, limit=200)
    m_gas_kg = f_gas * m500 * MSUN
    rho0 = m_gas_kg / (mass_integral_kpc3 * KPC_M**3)  # kg / m^3 at r=0
    ne0 = rho0 / (MU_E * M_P) / 1e6  # electrons / cm^3
    # Chord integral: n_e (cm^-3) over path length; dl in kpc -> pc via KPC_PC.
    # Truncate the LOS at the virial radius R200 ~ 1.48 R500, matching the mNFW
    # truncation, so the cross-check compares profile shape, not path length.
    r_max = 1.48 * r500_kpc
    l_max = math.sqrt(max(r_max**2 - b_kpc**2, 0.0))

    def ne_los(los_kpc):
        r = math.hypot(b_kpc, los_kpc)
        return ne0 * (1.0 + (r / rc) ** 2) ** (-1.5 * beta)

    dm_kpc, _ = integrate.quad(ne_los, -l_max, l_max, limit=200)  # cm^-3 * kpc
    dm_rest = dm_kpc * KPC_PC  # pc cm^-3
    return dm_rest / (1.0 + z)  # observer frame


def cluster_column_range(n=40_000):
    """MC the beta-model column over M500, f_gas, and shape; report the range.

    The 0.2 dex richness-mass prior is truncated above at the RASS X-ray
    upper limit (CL_M500_XRAY_UL): non-detection excludes the prior's upper
    tail, so masses above the cap are redrawn from the allowed range
    (one-sided truncated lognormal).
    """
    log_cap = math.log10(CL_M500_XRAY_UL)
    log_m500 = RNG.normal(math.log10(CL_M500), 0.20, n)  # 0.2 dex richness-mass scatter
    over = log_m500 > log_cap
    while over.any():
        log_m500[over] = RNG.normal(math.log10(CL_M500), 0.20, int(over.sum()))
        over = log_m500 > log_cap
    m500 = 10.0**log_m500
    r500 = CL_R500_KPC * (m500 / CL_M500) ** (1.0 / 3.0)  # R500 ~ M500^{1/3}
    f_gas = RNG.uniform(0.10, 0.16, n)  # X-ray/SZ cluster gas fractions
    rc_over = RNG.uniform(0.10, 0.30, n)  # core radius / R500
    beta = RNG.uniform(0.60, 0.75, n)  # beta-model slope
    dm = np.array(
        [
            beta_model_dm(
                m500[i], r500[i], CL_B_KPC, CL_Z, f_gas[i], rc_over[i], beta[i]
            )
            for i in range(n)
        ]
    )
    return dm


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-inputs", action="store_true", help="validate joined inputs and exit"
    )
    args = parser.parse_args(argv)
    sightlines = load_sightlines()
    if args.check_inputs:
        print(f"validated {len(sightlines)} sightlines and their per-system columns")
        return 0

    print("=== B1: DM_host posteriors (deterministic convolution) ===")
    print(
        f"{'burst':16s} {'z':>5s} {'arith':>7s} {'p16':>6s} {'p50':>6s} {'p84':>6s} {'P(<0)':>6s}"
    )
    results = []
    for row in sightlines:
        r = host_distribution(row)
        results.append(r)
        print(
            f"{r['name']:16s} {r['z']:5.3f} {r['dm_host_arith']:7.0f} "
            f"{r['dm_host_p16']:6.0f} {r['dm_host_p50']:6.0f} {r['dm_host_p84']:6.0f} "
            f"{r['p_host_neg']:6.2f}"
        )

    print("\n=== B2: FRB 20230307A intracluster column ===")
    dm_cl = cluster_column_range()
    p16, p50, p84 = np.percentile(dm_cl, [16, 50, 84])
    lo, hi = np.percentile(dm_cl, [2.5, 97.5])
    print(
        f"beta-model column: p50={p50:.0f}, [p16,p84]=[{p16:.0f},{p84:.0f}], "
        f"95% CI=[{lo:.0f},{hi:.0f}] pc cm^-3"
    )
    mnfw_central = 184.0
    print(f"mNFW central (budget census point): ~{mnfw_central:.0f} pc cm^-3")
    span_lo = min(lo, mnfw_central)
    span_hi = max(hi, mnfw_central)
    print(
        f"combined plausible range (mNFW + beta-model systematic): "
        f"~{span_lo:.0f}-{span_hi:.0f} pc cm^-3"
    )

    with OUT_CSV.open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(
            [
                "burst",
                "z",
                "dm_host_arith",
                "dm_int_p16",
                "dm_int_p50",
                "dm_int_p84",
                "dm_host_p16",
                "dm_host_p50",
                "dm_host_p84",
                "p_host_negative",
                "dm_host_rest_p16",
                "dm_host_rest_p50",
                "dm_host_rest_p84",
            ]
        )
        for r in results:
            w.writerow(
                [
                    r["name"],
                    r["z"],
                    f"{r['dm_host_arith']:.0f}",
                    f"{r['dm_int_p16']:.0f}",
                    f"{r['dm_int_p50']:.0f}",
                    f"{r['dm_int_p84']:.0f}",
                    f"{r['dm_host_p16']:.0f}",
                    f"{r['dm_host_p50']:.0f}",
                    f"{r['dm_host_p84']:.0f}",
                    f"{r['p_host_neg']:.3f}",
                    f"{r['dm_host_rest_p16']:.0f}",
                    f"{r['dm_host_rest_p50']:.0f}",
                    f"{r['dm_host_rest_p84']:.0f}",
                ]
            )
        w.writerow([])
        w.writerow(
            ["cluster_beta_model_p16_p50_p84", f"{p16:.0f}", f"{p50:.0f}", f"{p84:.0f}"]
        )
        w.writerow(["cluster_95CI_lo_hi", f"{lo:.0f}", f"{hi:.0f}"])
    print(f"\nwrote {OUT_CSV.relative_to(REPO)}")

    # LaTeX-ready rows for tab:host-forward-model (observer & rest frame), so the
    # appendix table is transcribed from this run rather than hand-computed. Each
    # frame's interval is the difference of its own rounded percentiles, so
    # median + upper = the tabulated rounded p84 by construction.
    print("\n=== tab:host-forward-model rows (obs | rest) ===")
    for r in results:
        o50, o16, o84 = (
            round(r["dm_host_p50"]),
            round(r["dm_host_p16"]),
            round(r["dm_host_p84"]),
        )
        s50, s16, s84 = (
            round(r["dm_host_rest_p50"]),
            round(r["dm_host_rest_p16"]),
            round(r["dm_host_rest_p84"]),
        )
        print(
            f"{r['name']} & ${r['z']:.3f}$ & "
            f"${o50}^{{+{o84 - o50}}}_{{-{o50 - o16}}}$ & "
            f"${s50}^{{+{s84 - s50}}}_{{-{s50 - s16}}}$ & ${r['p_host_neg']:.2f}$ \\\\"
        )

    _make_figure(results)
    return 0


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
    plt.rcParams.update(
        {
            "font.size": 7,
            "axes.labelsize": 7,
            "axes.titlesize": 7,
            "xtick.labelsize": 6,
            "ytick.labelsize": 6,
            "legend.fontsize": 6,
            "axes.linewidth": 0.6,
            "xtick.direction": "in",
            "ytick.direction": "in",
        }
    )

    n = len(results)
    ncols, nrows = 3, 3
    fig, axes = plt.subplots(
        nrows,
        ncols,
        figsize=(7.3, 6.4),
        layout="constrained",
    )
    axes = np.asarray(axes).ravel()

    legend_handles = [
        Line2D([0], [0], color=_HOST_COLOR, lw=1.5, label=r"$P(\mathrm{DM_{host}})$"),
        Line2D([0], [0], color=_MW_COLOR, lw=0.8, alpha=0.35, label="MW ISM (disk)"),
        Line2D([0], [0], color=_HALO_COLOR, lw=0.8, alpha=0.35, label="MW halo"),
        Line2D([0], [0], color=_COSMIC_COLOR, lw=0.8, alpha=0.35, label="cosmic / IGM"),
        Line2D(
            [0],
            [0],
            color=_INTERV_COLOR,
            lw=0.7,
            alpha=0.30,
            label="intervening system(s)",
        ),
        Line2D(
            [0],
            [0],
            color=_DARK_BLUE,
            lw=0.8,
            ls="--",
            alpha=0.45,
            label="intervening sightline sum",
        ),
    ]

    for i, r in enumerate(results):
        ax = axes[i]

        parts = [
            r["host_pdf"],
            r["disk_pdf"],
            r["halo_pdf"],
            r["cosmic_pdf"],
            r["interv_pdf"],
            *r["system_pdfs"],
        ]
        x_lo = min(pdf_quantile(pdf, 0.01) for pdf in parts)
        x_hi = max(pdf_quantile(pdf, 0.99) for pdf in parts)
        pad = 0.06 * max(x_hi - x_lo, 1.0)
        x_lo, x_hi = x_lo - pad, x_hi + pad
        x = np.linspace(x_lo, x_hi, 360)

        def density_on_plot_grid(pdf):
            return np.interp(x, pdf.x, pdf.density, left=0.0, right=0.0)

        def plot_faded(pdf, color, lw=0.8, ls="-"):
            dens = _peak_norm(density_on_plot_grid(pdf))
            ax.plot(x, dens, color=color, lw=lw, ls=ls, alpha=0.28, zorder=2)
            ax.fill_between(x, 0.0, dens, color=color, alpha=0.04, zorder=1)

        plot_faded(r["disk_pdf"], _MW_COLOR)
        plot_faded(r["halo_pdf"], _HALO_COLOR)
        plot_faded(r["cosmic_pdf"], _COSMIC_COLOR)

        for j, pdf in enumerate(r["system_pdfs"]):
            dens = _peak_norm(density_on_plot_grid(pdf))
            a = 0.22 + 0.05 * (j % 3)
            ax.plot(x, dens, color=_INTERV_COLOR, lw=0.7, alpha=a, zorder=2)
            ax.fill_between(x, 0.0, dens, color=_INTERV_COLOR, alpha=0.03, zorder=1)

        if r["dm_int"] > 0:
            dens_int = _peak_norm(density_on_plot_grid(r["interv_pdf"]))
            ax.plot(
                x, dens_int, color=_DARK_BLUE, lw=0.8, ls="--", alpha=0.40, zorder=3
            )

        dens_h = _peak_norm(density_on_plot_grid(r["host_pdf"]))
        ax.plot(x, dens_h, color=_HOST_COLOR, lw=1.5, zorder=5)
        ax.fill_between(x, 0.0, dens_h, color=_HOST_COLOR, alpha=0.22, zorder=4)
        ax.axvline(0.0, color="0.55", lw=0.5, ls=":", zorder=0)
        ax.axvline(
            r["dm_host_p50"], color=_HOST_COLOR, lw=0.6, ls="--", alpha=0.7, zorder=4
        )

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
        handles=legend_handles,
        loc="outside lower center",
        ncol=3,
        frameon=False,
    )
    fig.savefig(OUT_FIG, bbox_inches="tight")
    fig.savefig(OUT_FIG_PNG, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT_FIG.relative_to(REPO)}")


if __name__ == "__main__":
    raise SystemExit(main())
