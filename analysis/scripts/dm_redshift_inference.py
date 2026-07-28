#!/usr/bin/env python
"""Diagnostic DM-redshift inference for the three events without host redshifts.

This does not create an established redshift. It evaluates

    DM_obs = DM_MW,disk + DM_MW,halo + DM_IGM(z) + DM_host,rest/(1+z)

using the same Milky-Way and TNG-300 IGM distributions as the sightline budget.
The foreground-halo census is set to zero because it is incomplete on these
sightlines, so the inferred redshift is an upper-biased diagnostic. Results are
reported under three explicit host-DM priors to expose prior sensitivity.
"""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass

import numpy as np
from scipy import integrate

import dm_budget_uncertainty as budget
from workspace import ANALYSIS_ROOT, manuscript_root

ROOT = manuscript_root()
BUDGET_DATA = ANALYSIS_ROOT / "campaigns" / "foregrounds" / "budget_table_data.json"
DM_CATALOG = ANALYSIS_ROOT / "dm-joint-phase-v2" / "manuscript_dm_catalog.csv"
OUT_JSON = ANALYSIS_ROOT / "scripts" / "dm_redshift_inference.json"
OUT_CSV = ANALYSIS_ROOT / "scripts" / "dm_redshift_inference.csv"

HOSTLESS = frozenset({"FRB 20221203A", "FRB 20230325C", "FRB 20240122A"})
HOST_PRIOR_MEDIANS = (50.0, 100.0, 200.0)
HOST_PRIOR_SIGMA_LN = 0.8
Z_GRID = np.linspace(0.01, 2.5, 250)
DX = 1.0
LIGHT_SPEED_KM_S = 299792.458
H0_KM_S_MPC = 67.66


@dataclass(frozen=True)
class HostlessSightline:
    name: str
    nickname: str
    dm_obs: float
    dm_mw: float


def load_hostless() -> tuple[HostlessSightline, ...]:
    with BUDGET_DATA.open(encoding="utf-8") as handle:
        rows = {row["burst"]: row for row in json.load(handle)["rows"]}
    with DM_CATALOG.open(newline="", encoding="utf-8") as handle:
        catalog = {row["tns"]: row for row in csv.DictReader(handle)}
    result = []
    for name in sorted(HOSTLESS):
        row = rows[name]
        if row["z"] is not None:
            raise ValueError(f"{name}: expected missing established redshift")
        result.append(
            HostlessSightline(
                name=name,
                nickname=catalog[name]["nick"],
                dm_obs=float(catalog[name]["adopted_dm"]),
                dm_mw=float(row["dm_mw"]),
            )
        )
    return tuple(result)


def _efunc(z: float) -> float:
    return math.sqrt(budget.OMEGA_M * (1.0 + z) ** 3 + budget.OMEGA_LAMBDA)


def _comoving_distance_mpc(z: float) -> float:
    value, _ = integrate.quad(lambda zp: 1.0 / _efunc(zp), 0.0, z)
    return LIGHT_SPEED_KM_S / H0_KM_S_MPC * value


def redshift_prior(z: float) -> float:
    """Broad source-rate prior: comoving volume, time dilation, soft z cutoff."""
    distance = _comoving_distance_mpc(z)
    return distance**2 / (_efunc(z) * (1.0 + z)) * math.exp(-z / 1.5)


def _likelihood(
    sightline: HostlessSightline,
    z: float,
    host_rest_median: float,
) -> float:
    disk_median = sightline.dm_mw - budget.DM_MW_HALO
    if disk_median <= 0.0:
        raise ValueError(f"{sightline.name}: non-positive Milky-Way disk column")
    disk = budget.lognormal_pdf(disk_median, budget.SIGMA_DISK_FRAC, dx=DX)
    halo = budget.lognormal_pdf(
        budget.DM_MW_HALO, budget.HALO_SIGMA_LN, dx=DX
    )
    igm = budget.igm_mixture_pdf(z, dx=DX, quadrature_order=32)
    host_observer = budget.lognormal_pdf(
        host_rest_median / (1.0 + z), HOST_PRIOR_SIGMA_LN, dx=DX
    )
    total = budget.convolve_pdfs((disk, halo, igm, host_observer))
    return float(np.interp(sightline.dm_obs, total.x, total.density, left=0.0, right=0.0))


def infer_one(
    sightline: HostlessSightline,
    host_rest_median: float,
) -> dict:
    density = np.array(
        [
            _likelihood(sightline, float(z), host_rest_median) * redshift_prior(float(z))
            for z in Z_GRID
        ]
    )
    norm = float(np.trapezoid(density, Z_GRID))
    if not math.isfinite(norm) or norm <= 0.0:
        raise ValueError(f"{sightline.name}: redshift posterior failed to normalize")
    density /= norm
    cdf = integrate.cumulative_trapezoid(density, Z_GRID, initial=0.0)
    cdf /= cdf[-1]
    q16, q50, q84 = np.interp((0.16, 0.50, 0.84), cdf, Z_GRID)
    return {
        "host_rest_median": host_rest_median,
        "z16": float(q16),
        "z50": float(q50),
        "z84": float(q84),
    }


def build_result() -> dict:
    rows = []
    for sightline in load_hostless():
        priors = [infer_one(sightline, median) for median in HOST_PRIOR_MEDIANS]
        fiducial = next(row for row in priors if row["host_rest_median"] == 100.0)
        rows.append(
            {
                "burst": sightline.name,
                "nickname": sightline.nickname,
                "dm_obs": sightline.dm_obs,
                "dm_mw": sightline.dm_mw,
                "fiducial": fiducial,
                "host_prior_sensitivity": priors,
            }
        )
    return {
        "status": "diagnostic_dm_redshift_estimate_not_established_redshift",
        "model": {
            "igm": "TNG-300 IGM marginal with f_IGM uncertainty",
            "host_rest_dm": f"lognormal sigma_ln={HOST_PRIOR_SIGMA_LN}",
            "host_rest_medians": list(HOST_PRIOR_MEDIANS),
            "redshift_prior": "comoving volume / (1+z) times exp(-z/1.5)",
            "foreground_halos": "zero floor; missing halos bias inferred z high",
            "z_grid": [float(Z_GRID[0]), float(Z_GRID[-1]), len(Z_GRID)],
        },
        "rows": rows,
    }


def main() -> int:
    result = build_result()
    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("burst", "nickname", "dm_obs", "dm_mw", "z16", "z50", "z84"),
        )
        writer.writeheader()
        for row in result["rows"]:
            writer.writerow(
                {
                    "burst": row["burst"],
                    "nickname": row["nickname"],
                    "dm_obs": row["dm_obs"],
                    "dm_mw": row["dm_mw"],
                    **{key: row["fiducial"][key] for key in ("z16", "z50", "z84")},
                }
            )
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
