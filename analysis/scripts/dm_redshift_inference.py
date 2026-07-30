#!/usr/bin/env python
"""Coupled diagnostic DM-redshift inference for events without host redshifts.

This does not create an established redshift.  It evaluates the three declared
host-DM priors separately and, where a candidate has sufficient mass, geometry,
and redshift information, directly marginalizes its foreground/background state
with its positive dispersion column.  Photometric-redshift catastrophic failures
remain unmodeled and explicitly flagged.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import sys
from dataclasses import dataclass
from functools import cache, lru_cache
from pathlib import Path

import dm_budget_uncertainty as budget
import numpy as np
from scipy import integrate, stats
from workspace import ANALYSIS_ROOT

if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from foregrounds.census.config import COSMO
from foregrounds.census.hostless_sightlines import (
    OUTPUT_DIR as HOSTLESS_CENSUS_OUTPUT_DIR,
)
from foregrounds.census.hostless_sightlines import (
    build_hostless_census_receipt,
)
from foregrounds.propagation import scattering_predict
from foregrounds.propagation.dm_distributions import coarsening_quantile_shift
from foregrounds.propagation.dm_redshift import (
    CandidateForegroundDistribution,
    CandidateMixture,
    assert_tail_control,
    infer_coupled,
)

BUDGET_DATA = ANALYSIS_ROOT / "foregrounds" / "census" / "budget_table_data.json"
DM_CATALOG = ANALYSIS_ROOT / "dispersion" / "results" / "joint-phase" / "manuscript_dm_catalog.csv"
HOSTLESS_CENSUS_RECEIPT = HOSTLESS_CENSUS_OUTPUT_DIR / "receipt.json"
EXPANDED_CATALOG = (
    ANALYSIS_ROOT / "foregrounds" / "census" / "data" / "expanded_catalog_cross_references.csv"
)
RESULTS_DIR = ANALYSIS_ROOT / "foregrounds" / "results" / "dm_redshift"
RESULT_JSON = RESULTS_DIR / "posterior.json"
BASELINE_CSV = RESULTS_DIR / "baseline.csv"
COUPLED_CSV = RESULTS_DIR / "coupled.csv"
RECEIPT_JSON = RESULTS_DIR / "receipt.json"

# Compatibility surfaces consumed by the current table renderer.
OUT_JSON = ANALYSIS_ROOT / "scripts" / "dm_redshift_inference.json"
OUT_CSV = ANALYSIS_ROOT / "scripts" / "dm_redshift_inference.csv"

HOSTLESS = frozenset({"FRB 20221203A", "FRB 20230325C", "FRB 20240122A"})
HOST_PRIOR_MEDIANS = (50.0, 100.0, 200.0)
HOST_PRIOR_SIGMA_LN = 0.8
Z_GRID = np.linspace(0.01, 2.5, 250)
DX = 1.0
LIGHT_SPEED_KM_S = 299792.458
H0_KM_S_MPC = 67.66
CANDIDATE_DM_SIGMA_LN = 0.40
CANDIDATE_REDSHIFT_QUADRATURE_ORDER = 12
# Numerical libraries may differ in the eighth significant digit across SciPy
# versions. Six significant decimal digits preserve the reported redshift
# quantiles to better than 1e-6 while leaving a two-digit guard band above the
# largest observed cross-environment jitter.
SERIALIZED_FLOAT_SIGNIFICANT_DIGITS = 6
SERIALIZED_QUANTILE_SIGNIFICANT_DIGITS = 9
QUANTILE_FIELDS = frozenset({"z16", "z50", "z84"})


@dataclass(frozen=True)
class HostlessSightline:
    name: str
    nickname: str
    dm_obs: float
    dm_mw: float


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


@cache
def load_hostless_census_receipt() -> dict:
    """Require the authoritative builder and installed receipt to agree exactly."""
    built = build_hostless_census_receipt()
    installed = json.loads(HOSTLESS_CENSUS_RECEIPT.read_text(encoding="utf-8"))
    if built != installed:
        raise ValueError("hostless census receipt differs from its authoritative builder")
    return built


@cache
def _expanded_candidate_coordinates() -> dict[str, tuple[float, float]]:
    coordinates: dict[str, tuple[float, float]] = {}
    with EXPANDED_CATALOG.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            identifier = row["object_id"]
            if not row["ra_deg"] or not row["dec_deg"]:
                continue
            value = (float(row["ra_deg"]), float(row["dec_deg"]))
            if identifier in coordinates and coordinates[identifier] != value:
                raise ValueError(f"{identifier}: ambiguous coordinates in expanded catalog")
            coordinates[identifier] = value
    return coordinates


def _angular_separation_radians(
    ra1_deg: float,
    dec1_deg: float,
    ra2_deg: float,
    dec2_deg: float,
) -> float:
    """Stable great-circle separation."""
    ra1, dec1, ra2, dec2 = map(math.radians, (ra1_deg, dec1_deg, ra2_deg, dec2_deg))
    sine_dec = math.sin(0.5 * (dec2 - dec1))
    sine_ra = math.sin(0.5 * (ra2 - ra1))
    haversine = sine_dec**2 + math.cos(dec1) * math.cos(dec2) * sine_ra**2
    return 2.0 * math.asin(math.sqrt(min(1.0, max(0.0, haversine))))


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


@cache
def redshift_prior(z: float) -> float:
    """Broad source-rate prior: comoving volume, time dilation, soft z cutoff."""
    distance = _comoving_distance_mpc(z)
    return distance**2 / (_efunc(z) * (1.0 + z)) * math.exp(-z / 1.5)


@cache
def _likelihood(
    sightline: HostlessSightline,
    z: float,
    host_rest_median: float,
    active_candidates: tuple[CandidateForegroundDistribution, ...] = (),
) -> float:
    disk_median = sightline.dm_mw - budget.DM_MW_HALO
    if disk_median <= 0.0:
        raise ValueError(f"{sightline.name}: non-positive Milky-Way disk column")
    components = [
        budget.lognormal_pdf(disk_median, budget.SIGMA_DISK_FRAC, dx=DX),
        budget.lognormal_pdf(budget.DM_MW_HALO, budget.HALO_SIGMA_LN, dx=DX),
        budget.igm_mixture_pdf(z, dx=DX, quadrature_order=32),
        budget.lognormal_pdf(host_rest_median / (1.0 + z), HOST_PRIOR_SIGMA_LN, dx=DX),
    ]
    components.extend(_candidate_dm_pdf(candidate) for candidate in active_candidates)
    total = budget.convolve_pdfs(tuple(components))
    return float(np.interp(sightline.dm_obs, total.x, total.density, left=0.0, right=0.0))


def _candidate_dm_pdf(candidate: CandidateForegroundDistribution) -> budget.DiscretePDF:
    """Marginalize one halo-DM PDF over its conditional photo-z quadrature."""
    positive = [value for value in candidate.dm_medians if value is not None and value > 0.0]
    if not positive:
        return budget.delta_pdf(dx=DX)
    upper = max(
        stats.lognorm.ppf(
            1.0 - budget.TAIL_MASS,
            s=candidate.dm_sigma_ln,
            scale=median,
        )
        for median in positive
    )
    x = np.arange(0.0, math.ceil(upper / DX) * DX + 0.5 * DX, DX)
    density = np.zeros_like(x)
    for weight, median in zip(
        candidate.conditional_weights,
        candidate.dm_medians,
        strict=True,
    ):
        if median is None or median <= 0.0:
            density[0] += weight / DX
        else:
            density += weight * stats.lognorm.pdf(
                x,
                s=candidate.dm_sigma_ln,
                scale=median,
            )
    return budget.DiscretePDF(x0=0.0, dx=DX, density=density)


def load_candidate_mixtures(
    sightline: HostlessSightline,
) -> tuple[tuple[CandidateMixture, ...], tuple[dict, ...]]:
    """Build only candidate-specific models supported by the frozen census.

    A candidate is coupled only when its Gaussian photo-z, halo mass, and
    hash-bound sky coordinates are all available. Missing inputs and
    catastrophic photo-z behavior are flags, never silently replaced by an
    averaged prior. Angular separation is converted to physical impact and the
    mNFW column is evaluated at every photo-z quadrature node; a non-crossing
    node contributes an exact zero-DM point mass.
    """
    mixtures: list[CandidateMixture] = []
    flags: list[dict] = []
    receipt = load_hostless_census_receipt()
    sightline_row = next(
        row for row in receipt["sightlines"] if row["nickname"] == sightline.nickname
    )
    rows = [row for row in receipt["candidates"] if row["nickname"] == sightline.nickname]
    for row in rows:
        identifier = str(row["object_id"])
        required = ("adopted_z", "adopted_z_err", "m200c_msun", "impact_kpc")
        missing = [field for field in required if row.get(field) is None]
        if missing:
            flags.append(
                {
                    "identifier": identifier,
                    "status": "not_modeled_missing_inputs",
                    "missing": missing,
                    "science_admitted": bool(row["science_admitted"]),
                    "photo_z_catastrophic_failures": "unmodeled",
                }
            )
            continue
        z_mean = float(row["adopted_z"])
        z_sigma = float(row["adopted_z_err"])
        mass = float(row["m200c_msun"])
        coordinates = _expanded_candidate_coordinates().get(identifier)
        if coordinates is None:
            flags.append(
                {
                    "identifier": identifier,
                    "status": "not_modeled_missing_hash_bound_coordinates",
                    "science_admitted": bool(row["science_admitted"]),
                    "photo_z_catastrophic_failures": "unmodeled",
                }
            )
            continue
        theta = _angular_separation_radians(
            float(sightline_row["ra_deg"]),
            float(sightline_row["dec_deg"]),
            coordinates[0],
            coordinates[1],
        )
        if theta <= 0.0:
            raise ValueError(f"{identifier}: non-positive coordinate-derived separation")

        def dm_at_redshift(z: float, *, mass: float = mass, theta: float = theta) -> float | None:
            impact_kpc = theta * COSMO.angular_diameter_distance(z).to_value("kpc")
            return scattering_predict.dm_halo_mnfw(mass, z, impact_kpc)

        impact_at_mean = theta * COSMO.angular_diameter_distance(z_mean).to_value("kpc")
        mixtures.append(
            CandidateMixture(
                identifier=identifier,
                z_mean=z_mean,
                z_sigma=z_sigma,
                dm_sigma_ln=CANDIDATE_DM_SIGMA_LN,
                dm_at_redshift=dm_at_redshift,
                angular_separation_arcsec=math.degrees(theta) * 3600.0,
                geometry_source=(
                    "hostless receipt sightline coordinates + "
                    "expanded catalog candidate coordinates"
                ),
            )
        )
        flags.append(
            {
                "identifier": identifier,
                "status": "diagnostic_redshift_marginalized_model_not_science_admitted",
                "science_admitted": bool(row["science_admitted"]),
                "source_row_sha256": row["source_row_sha256"],
                "legacy_impact_kpc": float(row["impact_kpc"]),
                "coordinate_impact_at_photo_z_mean_kpc": impact_at_mean,
                "impact_geometry": "angular separation converted at every photo-z node",
                "photo_z_catastrophic_failures": "unmodeled",
            }
        )
    return tuple(mixtures), tuple(flags)


def infer_one(
    sightline: HostlessSightline,
    host_rest_median: float,
    candidates: tuple[CandidateMixture, ...] = (),
) -> dict:
    result = infer_coupled(
        Z_GRID,
        candidates=candidates,
        likelihood=lambda z, active: _likelihood(sightline, z, host_rest_median, active),
        redshift_prior=redshift_prior,
        candidate_quadrature_order=CANDIDATE_REDSHIFT_QUADRATURE_ORDER,
    )
    assert_tail_control(result)
    payload = result.as_dict()
    payload["host_rest_median"] = host_rest_median
    payload["grid_coarsening_max_quantile_shift"] = coarsening_quantile_shift(result.posterior)
    if payload["grid_coarsening_max_quantile_shift"] > 0.005:
        raise ValueError("redshift quantiles fail the alternate-node grid check")
    return payload


@lru_cache(maxsize=1)
def build_result() -> dict:
    rows = []
    for sightline in load_hostless():
        candidates, candidate_flags = load_candidate_mixtures(sightline)
        baseline = [infer_one(sightline, median) for median in HOST_PRIOR_MEDIANS]
        coupled = [infer_one(sightline, median, candidates) for median in HOST_PRIOR_MEDIANS]
        fiducial = next(row for row in baseline if row["host_rest_median"] == 100.0)
        coupled_fiducial = next(row for row in coupled if row["host_rest_median"] == 100.0)
        rows.append(
            {
                "burst": sightline.name,
                "nickname": sightline.nickname,
                "dm_obs": sightline.dm_obs,
                "dm_mw": sightline.dm_mw,
                "fiducial": {
                    key: fiducial[key] for key in ("host_rest_median", "z16", "z50", "z84")
                },
                "coupled_fiducial": {
                    key: coupled_fiducial[key]
                    for key in (
                        "host_rest_median",
                        "z16",
                        "z50",
                        "z84",
                        "candidate_foreground_probability",
                    )
                },
                "host_prior_sensitivity": [
                    {key: posterior[key] for key in ("host_rest_median", "z16", "z50", "z84")}
                    for posterior in baseline
                ],
                "candidate_models": [candidate.as_dict() for candidate in candidates],
                "candidate_flags": list(candidate_flags),
                "coupled_science_status": "diagnostic_not_science_admitted",
                "baseline": baseline,
                "coupled": coupled,
            }
        )
    return {
        "schema_version": 2,
        "status": "diagnostic_dm_redshift_estimate_not_established_redshift",
        "model": {
            "igm": "TNG-300 IGM marginal with f_IGM uncertainty",
            "host_rest_dm": f"lognormal sigma_ln={HOST_PRIOR_SIGMA_LN}",
            "host_rest_medians": list(HOST_PRIOR_MEDIANS),
            "host_prior_combination": "none; three conditional results retained",
            "redshift_prior": "comoving volume / (1+z) times exp(-z/1.5)",
            "candidate_coupling": (
                "direct finite foreground/background mixture integrated over "
                "truncated-Gaussian candidate photo-z"
            ),
            "candidate_dm": (
                "candidate-specific mNFW column marginalized jointly over "
                "conditional photo-z quadrature with sigma_ln=0.40; angular "
                "separation converted through angular-diameter distance at every "
                "node; no averaged missing-input prior"
            ),
            "impact_geometry_authority": (
                "coordinate-derived angular separation is authoritative because "
                "sky separation is redshift-independent and physical impact must "
                "be recomputed at each sampled redshift"
            ),
            "legacy_impact_disposition": (
                "legacy impact_kpc is retained in candidate flags for provenance "
                "but not used; it was evaluated at an earlier reference redshift "
                "and therefore can disagree after the adopted photo-z changes"
            ),
            "serialization_contract": (
                "posterior arrays and diagnostic scalars use six significant "
                "decimal digits; z16, z50, and z84 use nine"
            ),
            "photo_z_catastrophic_failures": "unmodeled_flag",
            "coupled_science_status": (
                "diagnostic only; source census candidates are not science admitted"
            ),
            "z_grid": [float(Z_GRID[0]), float(Z_GRID[-1]), len(Z_GRID)],
        },
        "rows": rows,
    }


def _summary_csv(result: dict, *, coupled: bool) -> str:
    stream = io.StringIO()
    fieldnames = (
        "burst",
        "nickname",
        "dm_obs",
        "dm_mw",
        "host_rest_median",
        "z16",
        "z50",
        "z84",
        "candidate_foreground_probability",
    )
    writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    key = "coupled" if coupled else "baseline"
    for row in result["rows"]:
        for posterior in row[key]:
            writer.writerow(
                {
                    "burst": row["burst"],
                    "nickname": row["nickname"],
                    "dm_obs": row["dm_obs"],
                    "dm_mw": row["dm_mw"],
                    "host_rest_median": posterior["host_rest_median"],
                    "z16": posterior["z16"],
                    "z50": posterior["z50"],
                    "z84": posterior["z84"],
                    "candidate_foreground_probability": json.dumps(
                        posterior["candidate_foreground_probability"],
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                }
            )
    return stream.getvalue()


def _legacy_csv(result: dict) -> str:
    stream = io.StringIO()
    fieldnames = ("burst", "nickname", "dm_obs", "dm_mw", "z16", "z50", "z84")
    writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
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
    return stream.getvalue()


def _canonicalize(value, *, field: str | None = None):
    """Quantize floating output above scientific precision for byte stability."""
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite output cannot be serialized")
        digits = (
            SERIALIZED_QUANTILE_SIGNIFICANT_DIGITS
            if field in QUANTILE_FIELDS
            else SERIALIZED_FLOAT_SIGNIFICANT_DIGITS
        )
        rounded = float(f"{value:.{digits}g}")
        return 0.0 if rounded == 0.0 else rounded
    if isinstance(value, dict):
        return {key: _canonicalize(item, field=key) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonicalize(item, field=field) for item in value]
    return value


def render_outputs() -> dict[Path, str]:
    result = _canonicalize(build_result())
    result_text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    outputs = {
        RESULT_JSON: result_text,
        BASELINE_CSV: _summary_csv(result, coupled=False),
        COUPLED_CSV: _summary_csv(result, coupled=True),
        OUT_JSON: result_text,
        OUT_CSV: _legacy_csv(result),
    }
    producer_paths = (
        Path(__file__),
        ANALYSIS_ROOT / "foregrounds" / "propagation" / "dm_redshift.py",
        ANALYSIS_ROOT / "foregrounds" / "propagation" / "dm_distributions.py",
    )
    receipt = {
        "schema_version": 1,
        "deterministic": True,
        "inputs": {
            str(path.relative_to(ANALYSIS_ROOT)): _sha256(path)
            for path in (
                BUDGET_DATA,
                DM_CATALOG,
                HOSTLESS_CENSUS_RECEIPT,
                EXPANDED_CATALOG,
            )
        },
        "producers": {
            str(path.relative_to(ANALYSIS_ROOT)): _sha256(path) for path in producer_paths
        },
        "outputs": {
            str(path.relative_to(ANALYSIS_ROOT)): _sha256_bytes(text.encode())
            for path, text in outputs.items()
        },
        "checks": {
            "complete_normalized_grids": True,
            "conditional_host_priors": list(HOST_PRIOR_MEDIANS),
            "candidate_state_mixture": "direct",
            "candidate_redshift_quadrature_order": CANDIDATE_REDSHIFT_QUADRATURE_ORDER,
            "serialized_float_significant_digits": SERIALIZED_FLOAT_SIGNIFICANT_DIGITS,
            "serialized_quantile_significant_digits": (SERIALIZED_QUANTILE_SIGNIFICANT_DIGITS),
            "photo_z_catastrophic_failures": "unmodeled_flag",
            "edge_mass_limit": 0.02,
            "alternate_node_quantile_shift_limit": 0.005,
        },
    }
    outputs[RECEIPT_JSON] = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    return outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="write or check the complete analysis-relative artifact tree under this directory",
    )
    args = parser.parse_args(argv)
    canonical_outputs = render_outputs()
    outputs = (
        {
            args.output_dir / path.relative_to(ANALYSIS_ROOT): text
            for path, text in canonical_outputs.items()
        }
        if args.output_dir is not None
        else canonical_outputs
    )
    if args.check:
        drift = [
            path
            for path, expected in outputs.items()
            if not path.is_file() or path.read_text(encoding="utf-8") != expected
        ]
        if drift:
            for path in drift:
                print(f"DRIFT: {path}", file=sys.stderr)
            return 1
        print(f"OK: {len(outputs)} DM-redshift artifacts")
        return 0
    for path, text in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
