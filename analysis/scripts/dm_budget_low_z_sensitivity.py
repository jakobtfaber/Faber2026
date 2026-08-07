#!/usr/bin/env python3
"""Benchmark the two z < 0.1 dispersion budgets against newer models.

This is a sensitivity analysis, not the fiducial manuscript model. It compares:

1. the current Walker/Connor diffuse-IGM continuation;
2. a hybrid that replaces the first 120 Mpc with the sightline-specific diffuse
   IGM map from Huang et al. (2025, ``pyhesdm``), while retaining the current
   statistical model for the remaining path; and
3. the total-cosmic continuous TNG300 rays from Konietzka et al. (2025).

The Konietzka model already contains intervening halos, so its host posterior
omits the budget's explicit intervening-halo term. The hybrid retains that term
because ``pyhesdm`` exposes the diffuse IGM separately from halos.

External inputs:

- pyhesdm 0.1.6 wheel: https://pypi.org/project/pyhesdm/0.1.6/
- continuous TNG catalog: https://ralfkonietzka.github.io/fast-radio-bursts/ray-tracing-catalogs/

Run from the manuscript checkout::

    python analysis/scripts/dm_budget_low_z_sensitivity.py \
      --pyhesdm-wheel /path/to/pyhesdm-0.1.6-py3-none-any.whl \
      --konietzka-catalog /path/to/Konietzka2025_DMmap_continuous_v1.hdf5
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import zipfile
from pathlib import Path

import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy import integrate, optimize, stats

import dm_budget_uncertainty as dbu


OUTPUT = Path(__file__).with_suffix(".json")
PYHESDM_FIGM = 0.8
LOCAL_DISTANCE_MPC = 120.0
H0_KM_S_MPC = 67.66
C_KM_S = 299792.458

# ICRS positions used by the foreground and Milky-Way analyses.
LOW_Z_COORDS = {
    "FRB 20220207C": (310.1995, 72.8823),
    "FRB 20240203A": (312.6191, 73.9000),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def comoving_distance_mpc(z: float) -> float:
    integral, _ = integrate.quad(
        lambda x: 1.0
        / math.sqrt(dbu.OMEGA_M * (1.0 + x) ** 3 + dbu.OMEGA_LAMBDA),
        0.0,
        z,
    )
    return C_KM_S / H0_KM_S_MPC * integral


def redshift_at_comoving_distance(distance_mpc: float) -> float:
    return float(
        optimize.brentq(
            lambda z: comoving_distance_mpc(z) - distance_mpc,
            0.0,
            0.2,
        )
    )


def figm_nodes_weights(order: int = dbu.IGM_QUADRATURE_ORDER):
    """Quadrature for the exact clipped asymmetric f_IGM prior."""
    nodes, base_weights = leggauss(order)
    u_low = (dbu.FIGM_CLIP[0] - dbu.FIGM_MED) / dbu.FIGM_SIG_LO
    u_high = (dbu.FIGM_CLIP[1] - dbu.FIGM_MED) / dbu.FIGM_SIG_HI

    def interval(a: float, b: float, scale: float):
        u = 0.5 * (b - a) * nodes + 0.5 * (a + b)
        weights = 0.5 * (b - a) * base_weights * stats.norm.pdf(u)
        return dbu.FIGM_MED + u * scale, weights

    figm_lo, weights_lo = interval(u_low, 0.0, dbu.FIGM_SIG_LO)
    figm_hi, weights_hi = interval(0.0, u_high, dbu.FIGM_SIG_HI)
    figm = np.concatenate(
        ([dbu.FIGM_CLIP[0]], figm_lo, figm_hi, [dbu.FIGM_CLIP[1]])
    )
    weights = np.concatenate(
        ([stats.norm.cdf(u_low)], weights_lo, weights_hi, [stats.norm.sf(u_high)])
    )
    return figm, weights / weights.sum()


def weighted_pdf_mixture(weighted_pdfs) -> dbu.DiscretePDF:
    """Place grid-aligned PDFs on one support and mix them."""
    weighted_pdfs = tuple(weighted_pdfs)
    dx = weighted_pdfs[0][1].dx
    x0 = min(pdf.x0 for _, pdf in weighted_pdfs)
    x1 = max(pdf.x[-1] for _, pdf in weighted_pdfs)
    size = int(round((x1 - x0) / dx)) + 1
    density = np.zeros(size)
    for weight, pdf in weighted_pdfs:
        if not math.isclose(pdf.dx, dx, abs_tol=1e-12):
            raise ValueError("mixture PDFs must share a grid spacing")
        start = int(round((pdf.x0 - x0) / dx))
        density[start : start + pdf.density.size] += weight * pdf.density
    return dbu.DiscretePDF(x0=x0, dx=dx, density=density)


def pyhesdm_igm_at_120_mpc(wheel: Path, ra_deg: float, dec_deg: float):
    """Read the diffuse-IGM mean and reconstruction scatter from the wheel."""
    import healpy as hp
    import pandas as pd
    from astropy.coordinates import SkyCoord

    with zipfile.ZipFile(wheel) as archive:
        means = pd.read_csv(
            io.BytesIO(archive.read("pyhesdm/dmigm_layers_8Mpc.csv"))
        )
        stds = pd.read_csv(
            io.BytesIO(archive.read("pyhesdm/dmigm_std_layers_8Mpc.csv"))
        )
    if means.shape != stds.shape or means.shape[0] != 12 * 64**2:
        raise ValueError("unexpected pyhesdm map dimensions")
    coordinate = SkyCoord(ra_deg, dec_deg, unit="deg", frame="icrs").galactic
    pixel = int(
        hp.ang2pix(
            64,
            np.pi / 2.0 - coordinate.b.radian,
            coordinate.l.radian,
            nest=False,
        )
    )
    return {
        "galactic_l_deg": float(coordinate.l.deg),
        "galactic_b_deg": float(coordinate.b.deg),
        "healpix_pixel": pixel,
        "mean_at_figm_0p8": float(means.iloc[pixel, -1]),
        "std_at_figm_0p8": float(stds.iloc[pixel, -1]),
    }


def hybrid_igm_pdf(
    z_source: float,
    local_mean_at_figm_0p8: float,
    local_std_at_figm_0p8: float,
    *,
    dx: float = dbu.GRID_DX,
) -> tuple[dbu.DiscretePDF, float, float]:
    """Replace the generic first 120 Mpc with the pyhesdm diffuse sightline.

    The remaining path retains the current lognormal shape and is scaled by the
    fraction of the Macquart integral beyond 120 Mpc. The same f_IGM draw scales
    both segments, preserving their shared baryon-fraction uncertainty.
    """
    z_local = redshift_at_comoving_distance(LOCAL_DISTANCE_MPC)
    if z_source <= z_local:
        raise ValueError("source must lie beyond the pyhesdm volume")
    remainder_fraction = 1.0 - dbu._macquart_integral(z_local) / dbu._macquart_integral(  # noqa: SLF001
        z_source
    )
    mu_full, sigma_ln = dbu.igm_lognormal_shape(z_source)
    figm, weights = figm_nodes_weights()
    components = []
    for value, weight in zip(figm, weights):
        local_scale = value / PYHESDM_FIGM
        local = dbu.normal_pdf(
            local_mean_at_figm_0p8 * local_scale,
            local_std_at_figm_0p8 * local_scale,
            dx=dx,
        )
        remainder_median = (
            math.exp(mu_full) * value / dbu.FIGM_TNG * remainder_fraction
        )
        remainder = dbu.lognormal_pdf(remainder_median, sigma_ln, dx=dx)
        components.append((float(weight), dbu.convolve_pdfs((local, remainder))))
    return weighted_pdf_mixture(components), z_local, remainder_fraction


def interpolate_catalog_rays(redshifts, dm_values, target_z: float) -> np.ndarray:
    """Linearly interpolate every catalog ray to the exact source redshift."""
    redshifts = np.asarray(redshifts, dtype=float)
    if dm_values.shape[0] != redshifts.size:
        raise ValueError("expected DMvalues axes to be redshift by ray")
    upper = int(np.searchsorted(redshifts, target_z))
    if upper == 0 or upper == redshifts.size:
        raise ValueError("target redshift is outside the catalog")
    lower = upper - 1
    fraction = (target_z - redshifts[lower]) / (
        redshifts[upper] - redshifts[lower]
    )
    return np.asarray(
        (1.0 - fraction) * dm_values[lower, :] + fraction * dm_values[upper, :],
        dtype=float,
    )


def empirical_pdf(samples, *, dx: float = dbu.GRID_DX) -> dbu.DiscretePDF:
    samples = np.asarray(samples, dtype=float)
    if samples.ndim != 1 or samples.size == 0 or np.any(samples < 0):
        raise ValueError("samples must be a non-empty non-negative vector")
    x1 = math.ceil(float(samples.max()) / dx) * dx
    edges = np.arange(-0.5 * dx, x1 + 1.5 * dx, dx)
    counts, _ = np.histogram(samples, bins=edges)
    return dbu.DiscretePDF(x0=0.0, dx=dx, density=counts / (samples.size * dx))


def konietzka_pdf(catalog: Path, z: float):
    import h5py

    with h5py.File(catalog, "r") as handle:
        redshifts = handle["redshifts"][:]
        rays = interpolate_catalog_rays(redshifts, handle["DMvalues"], z)
    return empirical_pdf(rays), rays


def host_summary(
    row: dbu.Sightline,
    cosmic: dbu.DiscretePDF,
    *,
    include_explicit_intervening: bool,
) -> dict[str, float]:
    disk = dbu.lognormal_pdf(row.dm_mw - dbu.DM_MW_HALO, dbu.SIGMA_DISK_FRAC)
    halo = dbu.lognormal_pdf(dbu.DM_MW_HALO, dbu.HALO_SIGMA_LN)
    components = [disk, halo, cosmic]
    if include_explicit_intervening:
        components.extend(
            dbu.lognormal_pdf(system.dm_point, dbu._system_sigma(system.mass_source))  # noqa: SLF001
            for system in row.intervening_systems
        )
    foreground = dbu.convolve_pdfs(tuple(components))
    host = dbu.host_pdf_from_foreground(foreground, row.dm_obs)
    q16, q50, q84 = (dbu.pdf_quantile(host, q) for q in (0.16, 0.5, 0.84))
    return {
        "p16": q16,
        "p50": q50,
        "p84": q84,
        "p_host_negative": dbu.pdf_cdf_at(host, 0.0),
    }


def pdf_quantiles(pdf: dbu.DiscretePDF) -> dict[str, float]:
    return {
        label: dbu.pdf_quantile(pdf, probability)
        for label, probability in (("p16", 0.16), ("p50", 0.5), ("p84", 0.84))
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pyhesdm-wheel", type=Path, required=True)
    parser.add_argument("--konietzka-catalog", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args(argv)
    for path in (args.pyhesdm_wheel, args.konietzka_catalog):
        if not path.is_file():
            parser.error(f"missing input: {path}")

    rows = {row.name: row for row in dbu.load_sightlines() if row.z < 0.1}
    if set(rows) != set(LOW_Z_COORDS):
        raise ValueError(f"unexpected low-redshift roster: {sorted(rows)}")

    report = {
        "schema_version": 1,
        "date_checked": "2026-07-22",
        "inputs": {
            "pyhesdm": {
                "version": "0.1.6",
                "sha256": sha256(args.pyhesdm_wheel),
                "url": "https://pypi.org/project/pyhesdm/0.1.6/",
            },
            "konietzka": {
                "filename": args.konietzka_catalog.name,
                "sha256": sha256(args.konietzka_catalog),
                "url": "https://ralfkonietzka.github.io/fast-radio-bursts/ray-tracing-catalogs/",
            },
        },
        "method": {
            "hybrid": (
                "pyhesdm diffuse IGM from 3.4 to 120 Mpc plus the current "
                "Walker/Connor diffuse distribution scaled to the remaining "
                "Macquart-integral path; common f_IGM draw; explicit known halos retained"
            ),
            "konietzka": (
                "raw continuous-TNG total-cosmic rays interpolated to the source "
                "redshift; explicit known halos omitted to prevent double counting"
            ),
        },
        "sightlines": [],
    }

    for name, row in rows.items():
        ra_deg, dec_deg = LOW_Z_COORDS[name]
        local = pyhesdm_igm_at_120_mpc(args.pyhesdm_wheel, ra_deg, dec_deg)
        hybrid, z_local, remainder_fraction = hybrid_igm_pdf(
            row.z,
            local["mean_at_figm_0p8"],
            local["std_at_figm_0p8"],
        )
        k_pdf, k_rays = konietzka_pdf(args.konietzka_catalog, row.z)
        current_igm = dbu.igm_mixture_pdf(row.z)
        current_host = dbu.host_distribution(row)
        current_summary = {
            key: current_host[key]
            for key in ("dm_host_p16", "dm_host_p50", "dm_host_p84", "p_host_neg")
        }
        current_summary = {
            "p16": current_summary["dm_host_p16"],
            "p50": current_summary["dm_host_p50"],
            "p84": current_summary["dm_host_p84"],
            "p_host_negative": current_summary["p_host_neg"],
        }
        hybrid_host = host_summary(
            row, hybrid, include_explicit_intervening=True
        )
        konietzka_host = host_summary(
            row, k_pdf, include_explicit_intervening=False
        )
        distance_mpc = comoving_distance_mpc(row.z)
        adopted_scale = dbu.FIGM_MED / PYHESDM_FIGM
        report["sightlines"].append(
            {
                "burst": name,
                "redshift": row.z,
                "ra_deg": ra_deg,
                "dec_deg": dec_deg,
                "comoving_distance_mpc": distance_mpc,
                "local_path_fraction": LOCAL_DISTANCE_MPC / distance_mpc,
                "pyhesdm": {
                    **local,
                    "mean_at_adopted_figm": local["mean_at_figm_0p8"]
                    * adopted_scale,
                    "std_at_adopted_figm": local["std_at_figm_0p8"]
                    * adopted_scale,
                    "model_end_redshift": z_local,
                    "statistical_remainder_fraction": remainder_fraction,
                },
                "cosmic_dm": {
                    "current_diffuse_igm": pdf_quantiles(current_igm),
                    "pyhesdm_hybrid_diffuse_igm": pdf_quantiles(hybrid),
                    "konietzka_total_cosmic": {
                        "p16": float(np.quantile(k_rays, 0.16)),
                        "p50": float(np.quantile(k_rays, 0.5)),
                        "p84": float(np.quantile(k_rays, 0.84)),
                    },
                },
                "host_dm_observer_frame": {
                    "current": current_summary,
                    "pyhesdm_hybrid": hybrid_host,
                    "konietzka_total_cosmic": konietzka_host,
                },
                "host_median_shift": {
                    "pyhesdm_minus_current": hybrid_host["p50"]
                    - current_summary["p50"],
                    "konietzka_minus_current": konietzka_host["p50"]
                    - current_summary["p50"],
                },
            }
        )

    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(f"wrote {args.output}")
    for row in report["sightlines"]:
        hosts = row["host_dm_observer_frame"]
        print(row["burst"])
        for model, result in hosts.items():
            print(
                f"  {model:26s} p16/p50/p84="
                f"{result['p16']:.1f}/{result['p50']:.1f}/{result['p84']:.1f}, "
                f"P(<0)={result['p_host_negative']:.3f}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
