"""Hash-bound synthetic vertical slice for dual-band burst fitting."""

from __future__ import annotations

import hashlib
import importlib.metadata
import inspect
import json
import math
import os
import platform
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import jsonschema
import matplotlib.pyplot as plt
import numpy as np
from astropy.time import Time, TimeDelta
from matplotlib.backends.backend_pdf import PdfPages
from scipy.special import ndtr

from faber2026.burst_models import (
    JointFitResult,
    PosteriorSummary,
    fit_joint_event,
)
from faber2026.burst_models.kernels import (
    convolved_tail_upper_bound,
    dispersion_delay_s,
)
from studies.dualband_synthetic import SyntheticEvent, build_synthetic_event

_STAGES = ("observations", "fit", "verify", "review")
_CANONICAL_PRODUCTS = (
    "params.json",
    "posterior.npz",
    "model-products.npz",
    "provenance.json",
    "review-packet.pdf",
)


class WorkflowFailure(RuntimeError):
    """Structured fail-closed stage error."""

    def __init__(
        self,
        message: str,
        *,
        reason_codes: list[str],
        diagnostics: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.reason_codes = reason_codes
        self.diagnostics = diagnostics or {}


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    def convert(item: Any) -> Any:
        if isinstance(item, np.generic):
            return item.item()
        raise TypeError(f"cannot serialize {type(item).__name__}")

    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True, default=convert) + "\n"
    )
    os.replace(temporary, path)


def _load_configuration(event: str, repository_root: Path) -> dict[str, Any]:
    config_path = (
        repository_root
        / "analysis-configs"
        / "dualband-burst-models"
        / f"{event}.json"
    )
    schema_path = config_path.parent / "schema.json"
    configuration = json.loads(config_path.read_text())
    jsonschema.validate(configuration, json.loads(schema_path.read_text()))
    return configuration


def _environment_preflight(repository_root: Path) -> dict[str, Any]:
    installed = list(importlib.metadata.distributions())
    distributions = {
        distribution.metadata["Name"].lower(): distribution.version
        for distribution in installed
        if distribution.metadata["Name"]
    }
    forbidden = sorted(name for name in distributions if "flits" in name)
    forbidden_paths = sorted(path for path in sys.path if "flits" in path.lower())
    if forbidden or forbidden_paths:
        raise WorkflowFailure(
            "FLITS runtime contamination detected",
            reason_codes=["input-forbidden-flits-runtime"],
            diagnostics={
                "distributions": forbidden,
                "sys_path_entries": forbidden_paths,
            },
        )
    external_editables = []
    for distribution in installed:
        direct_url_text = distribution.read_text("direct_url.json")
        if not direct_url_text:
            continue
        direct_url = json.loads(direct_url_text)
        if not direct_url.get("dir_info", {}).get("editable"):
            continue
        url = direct_url.get("url", "")
        if repository_root.as_uri() not in url:
            external_editables.append(
                {
                    "name": distribution.metadata["Name"],
                    "url": url,
                }
            )
    if external_editables:
        raise WorkflowFailure(
            "external editable installation detected",
            reason_codes=["input-external-editable"],
            diagnostics={"distributions": external_editables},
        )
    import faber2026

    origin = Path(inspect.getfile(faber2026)).resolve()
    if repository_root not in origin.parents:
        raise WorkflowFailure(
            "faber2026 import does not originate in this checkout",
            reason_codes=["input-import-origin"],
            diagnostics={"origin": str(origin)},
        )
    dynesty_version = importlib.metadata.version("dynesty")
    if dynesty_version != "3.1.0":
        raise WorkflowFailure(
            "wrong Dynesty version",
            reason_codes=["input-sampler-version"],
            diagnostics={"measured": dynesty_version, "required": "3.1.0"},
        )
    required_python = (3, 12, 13)
    if sys.version_info[:3] != required_python:
        raise WorkflowFailure(
            "wrong Python version",
            reason_codes=["input-python-version"],
            diagnostics={
                "measured": ".".join(map(str, sys.version_info[:3])),
                "required": ".".join(map(str, required_python)),
            },
        )
    code = _git_identity(repository_root)
    if code["dirty"]:
        raise WorkflowFailure(
            "science execution requires a clean checkout",
            reason_codes=["input-dirty-checkout"],
            diagnostics={"dirty_paths": code["dirty_paths"]},
        )
    environment_manifest = {
        "python": sys.version,
        "platform": platform.platform(),
        "dynesty": dynesty_version,
        "faber2026_origin": str(origin),
        "flits_runtime": False,
        "code": code,
        "distributions": dict(sorted(distributions.items())),
    }
    environment_manifest["manifest_sha256"] = hashlib.sha256(
        _canonical_json(environment_manifest)
    ).hexdigest()
    return environment_manifest


def _git_identity(repository_root: Path) -> dict[str, Any]:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    dirty_paths = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    return {"commit": commit, "dirty": bool(dirty_paths), "dirty_paths": dirty_paths}


def _request_hash(configuration: dict[str, Any], repository_root: Path) -> str:
    code_paths = sorted(
        list((repository_root / "faber2026").rglob("*.py"))
        + list((repository_root / "workflows").rglob("*.py"))
        + [
            repository_root / "studies" / "dualband_synthetic.py",
            repository_root / "scripts" / "run_dualband_burst_model.py",
            repository_root / "analysis-configs" / "dualband-burst-models" / "schema.json",
            repository_root
            / "analysis-configs"
            / "dualband-burst-models"
            / "params.schema.json",
            repository_root / "pyproject.toml",
            repository_root / "uv.lock",
            repository_root / ".python-version",
            repository_root / "Makefile",
        ]
    )
    digest = hashlib.sha256(_canonical_json(configuration))
    for path in code_paths:
        digest.update(path.relative_to(repository_root).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _save_observations(path: Path, event: SyntheticEvent) -> None:
    values: dict[str, Any] = {"truth_json": json.dumps(event.truth, sort_keys=True)}
    for observation in event.request.observations:
        prefix = observation.instrument
        values.update(
            {
                f"{prefix}_intensity": observation.intensity,
                f"{prefix}_valid_pixels": observation.valid_pixels,
                f"{prefix}_frequencies_mhz": observation.frequencies_mhz,
                f"{prefix}_channel_widths_mhz": observation.channel_widths_mhz,
                f"{prefix}_times_s": observation.times_s,
                f"{prefix}_noise_std": observation.noise_std,
            }
        )
    np.savez_compressed(path, **values)


def _save_fit(path: Path, result: JointFitResult) -> None:
    np.savez_compressed(
        path,
        samples=result.samples,
        weights=result.weights,
        parameter_names=np.asarray(result.parameter_names),
        parameter_units=np.asarray(result.parameter_units),
        sample_morphologies=result.sample_morphologies,
        sample_associations=result.sample_associations,
        log_evidence=result.log_evidence,
        log_evidence_uncertainty=result.log_evidence_uncertainty,
        maximum_not_on_boundary=result.maximum_not_on_boundary,
        prior_edge_mass_json=json.dumps(
            dict(result.prior_edge_mass_by_parameter), sort_keys=True
        ),
        morphology_weights_json=json.dumps(
            dict(result.morphology_weights), sort_keys=True
        ),
        morphology_statuses_json=json.dumps(
            dict(result.morphology_statuses), sort_keys=True
        ),
        morphology_log_evidences_json=json.dumps(
            dict(result.morphology_log_evidences), sort_keys=True
        ),
        morphology_log_evidence_uncertainties_json=json.dumps(
            dict(result.morphology_log_evidence_uncertainties), sort_keys=True
        ),
        morphology_maximum_prior_edge_mass_json=json.dumps(
            dict(result.morphology_maximum_prior_edge_mass), sort_keys=True
        ),
        association_weights_json=json.dumps(
            dict(result.association_weights), sort_keys=True
        ),
    )


def _save_model_products(
    path: Path,
    event: SyntheticEvent,
    result: JointFitResult,
) -> None:
    values: dict[str, Any] = {}
    for observation in event.request.observations:
        prefix = observation.instrument
        values[f"{prefix}_intensity"] = observation.intensity
        values[f"{prefix}_valid_pixels"] = observation.valid_pixels
        values[f"{prefix}_frequencies_mhz"] = observation.frequencies_mhz
        values[f"{prefix}_channel_widths_mhz"] = observation.channel_widths_mhz
        values[f"{prefix}_times_s"] = observation.times_s
        values[f"{prefix}_sample_interval_s"] = observation.sample_interval_s
        values[f"{prefix}_time_origin_utc"] = observation.time_origin_utc
        values[f"{prefix}_time_origin_unix_ns"] = observation.time_origin_unix_ns
        values[f"{prefix}_frequency_frame"] = observation.frequency_frame
        values[f"{prefix}_noise_std"] = observation.noise_std
        values[f"{prefix}_gain_prior_std"] = observation.gain_prior_std
        values[f"{prefix}_voltage_dm"] = observation.dispersion.voltage_dm
        values[f"{prefix}_coherent_delta_dm"] = (
            observation.dispersion.coherent_delta_dm
        )
        values[f"{prefix}_residual_delta_dm"] = (
            observation.dispersion.residual_delta_dm
        )
        values[f"{prefix}_product_dm"] = observation.dispersion.product_dm
        values[f"{prefix}_time_origin_correction_s"] = (
            observation.dispersion.time_origin_correction_s
        )
        values[f"{prefix}_input_hashes_json"] = json.dumps(
            dict(observation.input_hashes), sort_keys=True
        )
        values[f"{prefix}_model"] = result.model_by_instrument[prefix]
        values[f"{prefix}_residual"] = result.residual_by_instrument[prefix]
    np.savez_compressed(path, **values)


def _weighted_summary(
    values: np.ndarray, weights: np.ndarray
) -> PosteriorSummary:
    finite = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    values = values[finite]
    weights = weights[finite]
    weights = weights / weights.sum()
    order = np.argsort(values)
    cumulative = np.cumsum(weights[order])
    cumulative /= cumulative[-1]
    lower, median, upper = np.interp(
        [0.16, 0.5, 0.84], cumulative, values[order]
    )
    return PosteriorSummary(float(median), float(lower), float(upper))


def _dm_uncertainty_classes(
    result: JointFitResult,
    uncertainty_budget: dict[str, Any],
) -> dict[str, float]:
    names = list(result.parameter_names)
    dm = result.samples[:, names.index("absolute_dm")]
    timing = result.samples[
        :,
        [
            names.index("timing_error_s:chimefrb"),
            names.index("timing_error_s:dsa110"),
        ],
    ]
    weights = result.weights / result.weights.sum()
    total_mean = float(np.sum(weights * dm))
    group_means: list[float] = []
    group_weights: list[float] = []
    dm_within = np.zeros_like(dm)
    timing_within = np.zeros_like(timing)
    for morphology in result.morphology_weights:
        for association in result.association_weights:
            selected = (
                (result.sample_morphologies == morphology)
                & (result.sample_associations == association)
            )
            weight = float(np.sum(weights[selected]))
            if weight > 0:
                group_mean = float(np.sum(weights[selected] * dm[selected]) / weight)
                timing_mean = np.sum(
                    weights[selected, None] * timing[selected], axis=0
                ) / weight
                dm_within[selected] = dm[selected] - group_mean
                timing_within[selected] = timing[selected] - timing_mean
                group_means.append(group_mean)
                group_weights.append(weight)
    between_variance = float(
        sum(
            weight * (mean - total_mean) ** 2
            for mean, weight in zip(group_means, group_weights, strict=True)
        )
    )
    within_variance = float(np.sum(weights * dm_within**2))
    timing_covariance = (timing_within * weights[:, None]).T @ timing_within
    cross_covariance = np.sum(
        weights[:, None] * timing_within * dm_within[:, None], axis=0
    )
    explained = float(
        cross_covariance
        @ np.linalg.pinv(timing_covariance)
        @ cross_covariance
    )
    explained = min(max(explained, 0.0), within_variance)
    return {
        "statistical": math.sqrt(
            max(within_variance - explained, 0.0)
        ),
        "association_morphology": math.sqrt(max(between_variance, 0.0)),
        "calibration_resolution": float(
            uncertainty_budget["calibration_resolution_dm"]
        ),
        "geometry_clock": math.sqrt(explained),
        "intrinsic_lag": float(uncertainty_budget["intrinsic_lag_dm"]),
    }


def _utc_string(epoch_unix_ns: int, offset_s: float) -> str:
    seconds, nanoseconds = divmod(epoch_unix_ns, 1_000_000_000)
    time = Time(
        seconds,
        nanoseconds / 1e9,
        format="unix",
        scale="utc",
    )
    time += TimeDelta(offset_s, format="sec")
    time.precision = 9
    return str(time.isot)


def _load_fit(
    posterior_path: Path,
    model_path: Path,
    event: SyntheticEvent,
) -> JointFitResult:
    with np.load(posterior_path, allow_pickle=False) as posterior:
        samples = posterior["samples"]
        weights = posterior["weights"]
        parameter_names = tuple(str(item) for item in posterior["parameter_names"])
        parameter_units = tuple(str(item) for item in posterior["parameter_units"])
        sample_morphologies = posterior["sample_morphologies"]
        sample_associations = posterior["sample_associations"]
        summaries = tuple(
            _weighted_summary(samples[:, index], weights)
            for index in range(samples.shape[1])
        )
        log_evidence = float(posterior["log_evidence"])
        log_evidence_uncertainty = float(posterior["log_evidence_uncertainty"])
        maximum_not_on_boundary = bool(posterior["maximum_not_on_boundary"])
        prior_edge_mass = json.loads(str(posterior["prior_edge_mass_json"]))
        morphology_weights = json.loads(
            str(posterior["morphology_weights_json"])
        )
        morphology_statuses = json.loads(
            str(posterior["morphology_statuses_json"])
        )
        morphology_log_evidences = json.loads(
            str(posterior["morphology_log_evidences_json"])
        )
        morphology_log_evidence_uncertainties = json.loads(
            str(posterior["morphology_log_evidence_uncertainties_json"])
        )
        morphology_maximum_prior_edge_mass = json.loads(
            str(posterior["morphology_maximum_prior_edge_mass_json"])
        )
        association_weights = json.loads(
            str(posterior["association_weights_json"])
        )
    models: dict[str, np.ndarray] = {}
    residuals: dict[str, np.ndarray] = {}
    with np.load(model_path, allow_pickle=False) as products:
        for observation in event.request.observations:
            models[observation.instrument] = products[
                f"{observation.instrument}_model"
            ]
            residuals[observation.instrument] = products[
                f"{observation.instrument}_residual"
            ]
    component_count = len(event.request.component_ids)
    return JointFitResult(
        status=(
            "provisional-owner-review"
            if maximum_not_on_boundary
            else "failed-inference"
        ),
        shared_dm=summaries[0],
        component_toas=summaries[1 : 1 + component_count],
        parameter_names=parameter_names,
        parameter_units=parameter_units,
        samples=samples,
        weights=weights,
        sample_morphologies=sample_morphologies,
        sample_associations=sample_associations,
        log_evidence=log_evidence,
        log_evidence_uncertainty=log_evidence_uncertainty,
        maximum_not_on_boundary=maximum_not_on_boundary,
        prior_edge_mass_by_parameter=prior_edge_mass,
        morphology_weights=morphology_weights,
        morphology_statuses=morphology_statuses,
        morphology_log_evidences=morphology_log_evidences,
        morphology_log_evidence_uncertainties=(
            morphology_log_evidence_uncertainties
        ),
        morphology_maximum_prior_edge_mass=(
            morphology_maximum_prior_edge_mass
        ),
        association_weights=association_weights,
        model_by_instrument=models,
        residual_by_instrument=residuals,
    )


def _verification(
    event: SyntheticEvent,
    result: JointFitResult,
    configuration: dict[str, Any],
) -> dict[str, Any]:
    thresholds = configuration["verification"]
    truth = event.truth
    parameter_medians = {
        name: _weighted_summary(result.samples[:, index], result.weights).median
        for index, name in enumerate(result.parameter_names)
    }
    omitted_tail_mass = 0.0
    reduced_residual_powers = []
    lag_one_correlations = []
    valid_fractions = []
    # Every stored posterior sample participates. The bound intentionally uses
    # a conservative envelope across their coordinates, so covariance cannot
    # hide a crop-touching draw.
    sample_indices = np.arange(result.samples.shape[0])
    for observation in event.request.observations:
        frequencies = np.asarray(observation.frequencies_mhz)
        start = observation.times_s[0] - 0.5 * observation.sample_interval_s
        end = observation.times_s[-1] + 0.5 * observation.sample_interval_s
        for component in event.request.component_ids:
            names = list(result.parameter_names)
            toa_values = result.samples[:, names.index(f"toa_400_s:{component}")]
            width_values = result.samples[:, names.index(f"width_400_s:{component}")]
            dm_values = result.samples[:, names.index("absolute_dm")]
            index_values = result.samples[:, names.index("width_index")]
            timing_values = result.samples[
                :, names.index(f"timing_error_s:{observation.instrument}")
            ]
            centers = (
                toa_values[:, None]
                + event.request.geometry.station_delays_s[observation.instrument]
                + timing_values[:, None]
                - (
                    observation.time_origin_unix_ns
                    - event.request.geometry.epoch_unix_ns
                )
                * 1e-9
                - observation.dispersion.time_origin_correction_s
                + dispersion_delay_s(
                    dm_values[:, None] - observation.dispersion.product_dm,
                    frequencies[None, :],
                )
            )
            widths = width_values[:, None] * (
                frequencies[None, :] / 400.0
            ) ** index_values[:, None]
            early = ndtr((start - centers) / widths)
            finite_tau = (
                result.samples[:, names.index("tau_1ghz_s")]
                if "tau_1ghz_s" in names
                else np.array([])
            )
            if finite_tau.size == 0:
                late = ndtr(-(end - centers) / widths)
            else:
                tau_1ghz = float(np.nanmax(finite_tau[sample_indices]))
                beta = (
                    float(np.nanmin(result.samples[sample_indices, names.index("beta")]))
                    if "beta" in names
                    else 4.0
                )
                alpha = 2.0 * beta / (beta - 2.0)
                tau = tau_1ghz * (frequencies / 1000.0) ** -alpha
                late = np.asarray(
                    [
                        convolved_tail_upper_bound(
                            end - float(np.max(centers[:, index])),
                            float(np.max(widths[:, index])),
                            channel_tau,
                            beta,
                        )
                        for index, channel_tau in enumerate(tau)
                    ]
                )
            omitted_tail_mass = max(
                omitted_tail_mass,
                float(np.max(early)),
                float(np.max(late)),
            )
        # Band-local nuisance components are Gaussian.  They do not constrain
        # the geometry, but their fitted support must still be contained by
        # the reviewed crop.  NaNs are expected for samples from associations
        # where that component is matched rather than local.
        for component in event.request.band_component_ids[observation.instrument]:
            toa_name = f"local_toa_s:{observation.instrument}:{component}"
            width_name = f"local_width_s:{observation.instrument}:{component}"
            if toa_name not in names:
                continue
            local_toas = result.samples[:, names.index(toa_name)]
            local_widths = result.samples[:, names.index(width_name)]
            finite = np.isfinite(local_toas) & np.isfinite(local_widths)
            if not np.any(finite):
                continue
            omitted_tail_mass = max(
                omitted_tail_mass,
                float(np.max(ndtr((start - local_toas[finite]) / local_widths[finite]))),
                float(np.max(ndtr(-(end - local_toas[finite]) / local_widths[finite]))),
            )
        valid = np.asarray(observation.valid_pixels)
        standardized = (
            result.residual_by_instrument[observation.instrument]
            / observation.noise_std[:, None]
        )
        reduced_residual_powers.append(float(np.mean(standardized[valid] ** 2)))
        valid_fractions.append(float(np.mean(valid)))
        for row, keep in zip(standardized, valid, strict=True):
            pairs = keep[:-1] & keep[1:]
            if np.sum(pairs) > 2 and np.std(row[:-1][pairs]) > 0 and np.std(row[1:][pairs]) > 0:
                lag_one_correlations.append(
                    abs(float(np.corrcoef(row[:-1][pairs], row[1:][pairs])[0, 1]))
                )
    checks = {
        "shared-dm-recovery": {
            "measured": result.shared_dm.median,
            "truth": truth["absolute_dm"],
            "limit": thresholds["absolute_dm_error_max"],
        },
        "toa-recovery": {
            "measured": result.component_toas[0].median,
            "truth": truth["geocentric_toa_s"],
            "limit": thresholds["toa_error_s_max"],
        },
        "width-recovery": {
            "measured": parameter_medians["width_400_s:component-1"],
            "truth": truth["width_400_s"],
            "limit": thresholds["width_error_s_max"],
        },
        "width-index-recovery": {
            "measured": parameter_medians["width_index"],
            "truth": truth["width_index"],
            "limit": thresholds["width_index_error_max"],
        },
        "scattering-recovery": {
            "measured": parameter_medians.get("tau_1ghz_s", 0.0),
            "truth": truth["tau_1ghz_s"],
            "limit": thresholds["scattering_tau_error_s_max"],
        },
        "association-recovery": {
            "measured": result.association_weights[
                configuration["synthetic"]["truth_association_id"]
            ],
            "truth": 1.0,
            "limit": thresholds["maximum_incorrect_association_weight"],
        },
        "geometry-projection": {
            "measured": event.request.geometry.independent_projection_difference_s,
            "truth": 0.0,
            "limit": event.request.geometry.maximum_projection_difference_s,
        },
        "crop-tail-support": {
            "measured": omitted_tail_mass,
            "truth": 0.0,
            "limit": thresholds["maximum_omitted_tail_mass"],
        },
        "nested-evidence-uncertainty": {
            "measured": result.log_evidence_uncertainty,
            "truth": 0.0,
            "limit": thresholds["maximum_log_evidence_uncertainty"],
        },
        "reduced-residual-power": {
            "measured": max(reduced_residual_powers),
            "truth": 1.0,
            "limit": thresholds["maximum_reduced_residual_power"] - 1.0,
        },
        "structured-residual-correlation": {
            "measured": max(lag_one_correlations),
            "truth": 0.0,
            "limit": thresholds["maximum_structured_residual_correlation"],
        },
        "valid-sample-coverage": {
            "measured": min(valid_fractions),
            "truth": 1.0,
            "limit": 1.0 - thresholds["minimum_valid_sample_fraction"],
        },
        "prior-edge-mass": {
            "measured": max(result.prior_edge_mass_by_parameter.values()),
            "truth": 0.0,
            "limit": thresholds["maximum_prior_edge_mass"],
        },
        "failed-morphology-weight": {
            "measured": sum(
                result.morphology_weights[name]
                for name, status in result.morphology_statuses.items()
                if status != "provisional-owner-review"
            ),
            "truth": 0.0,
            "limit": event.request.maximum_failed_morphology_weight,
        },
        "uncertainty-evidence": {
            "measured": bool(configuration["uncertainty_budget"]["basis"]),
            "truth": True,
            "limit": "explicit reviewed basis required",
        },
    }
    for check in checks.values():
        if isinstance(check["limit"], str):
            check["passed"] = bool(check["measured"] is check["truth"])
        else:
            check["passed"] = bool(
                abs(check["measured"] - check["truth"]) <= check["limit"]
            )
    checks["posterior-boundary"] = {
        "measured": bool(result.maximum_not_on_boundary),
        "truth": True,
        "limit": "must be true",
        "passed": bool(result.maximum_not_on_boundary),
    }
    if not all(check["passed"] for check in checks.values()):
        failed = [name for name, check in checks.items() if not check["passed"]]
        raise WorkflowFailure(
            "synthetic scientific verification failed",
            reason_codes=[f"verification-{name}" for name in failed],
            diagnostics={"checks": checks},
        )
    return checks


def _render_review_packet(
    path: Path,
    event: SyntheticEvent,
    result: JointFitResult,
    checks: dict[str, Any],
    request_hash: str,
) -> None:
    with PdfPages(
        path,
        metadata={"CreationDate": None, "ModDate": None},
    ) as pdf:
        figure, axes = plt.subplots(
            3, 2, figsize=(9, 10), constrained_layout=True
        )
        for column, observation in enumerate(event.request.observations):
            instrument = observation.instrument
            extent = [
                observation.times_s[0] * 1000,
                observation.times_s[-1] * 1000,
                observation.frequencies_mhz[0],
                observation.frequencies_mhz[-1],
            ]
            panels = (
                (observation.intensity, "Data"),
                (result.model_by_instrument[instrument], "Model"),
                (result.residual_by_instrument[instrument], "Residual"),
            )
            for row, (image, label) in enumerate(panels):
                axes[row, column].imshow(
                    image,
                    aspect="auto",
                    origin="lower",
                    extent=extent,
                )
                axes[row, column].set_ylabel("Frequency (MHz)")
                axes[row, column].set_xlabel("Time from origin (ms)")
                axes[row, column].text(
                    0.02,
                    0.95,
                    f"{instrument} — {label}",
                    transform=axes[row, column].transAxes,
                    va="top",
                )
        pdf.savefig(figure)
        plt.close(figure)

        figure, axes = plt.subplots(
            2, 2, figsize=(9, 8), constrained_layout=True
        )
        dm_samples = result.samples[:, 0]
        axes[0, 0].hist(
            dm_samples,
            bins=40,
            weights=result.weights,
            histtype="step",
            color="black",
        )
        axes[0, 0].axvline(
            event.truth["absolute_dm"], color="tab:red", linestyle="--"
        )
        axes[0, 0].set_xlim(
            float(np.min(dm_samples)), float(np.max(dm_samples))
        )
        axes[0, 0].set_xlabel(r"Shared DM (pc cm$^{-3}$)")
        axes[0, 0].set_ylabel("Posterior density")

        delays_ms = np.asarray(
            [
                event.request.geometry.station_delays_s["chimefrb"],
                event.request.geometry.station_delays_s["dsa110"],
            ]
        ) * 1000
        geocentric_ms = result.component_toas[0].median * 1000
        topocentric_ms = geocentric_ms + delays_ms
        axes[0, 1].plot(
            delays_ms,
            geocentric_ms + delays_ms,
            color="0.5",
            linestyle="--",
        )
        axes[0, 1].scatter(
            delays_ms, topocentric_ms, color=("tab:orange", "tab:blue")
        )
        for name, x, y in zip(
            ("CHIME/FRB", "DSA-110"),
            delays_ms,
            topocentric_ms,
            strict=True,
        ):
            axes[0, 1].annotate(name, (x, y), xytext=(4, 4), textcoords="offset points")
        axes[0, 1].set_xlabel("Station delay from geocenter (ms)")
        axes[0, 1].set_ylabel("Topocentric 400 MHz arrival time (ms)")

        labels = list(result.morphology_weights) + list(result.association_weights)
        values = list(result.morphology_weights.values()) + list(
            result.association_weights.values()
        )
        axes[1, 0].bar(labels, values, color="0.5")
        axes[1, 0].set_ylim(0, 1.05)
        axes[1, 0].set_ylabel("Evidence weight")

        axes[1, 1].axis("off")
        lines = [
            f"Status: {result.status}",
            f"Request: {request_hash[:16]}…",
            f"DM: {result.shared_dm.median:.6f}",
            f"400 MHz ToA: {result.component_toas[0].median:.9f} s",
            f"ln Z: {result.log_evidence:.2f} ± {result.log_evidence_uncertainty:.2f}",
        ]
        lines.extend(
            f"{name}: {result.morphology_statuses[name]}, "
            f"ln Z={result.morphology_log_evidences[name]:.1f}"
            for name in result.morphology_weights
        )
        lines.extend(
            f"{name}: {'PASS' if check['passed'] else 'FAIL'}"
            for name, check in checks.items()
        )
        axes[1, 1].text(
            0.0, 1.0, "\n".join(lines), va="top", family="monospace", fontsize=8
        )
        pdf.savefig(figure)
        plt.close(figure)


def _write_failure(
    output_root: Path,
    event: str,
    request_hash: str,
    stage: str,
    error: Exception,
    last_valid_stage: str | None,
    run_directory: Path,
) -> None:
    reason_codes = getattr(error, "reason_codes", [f"{stage}-failed"])
    diagnostics = getattr(error, "diagnostics", {})
    artifacts = {
        path.name: _sha256(path)
        for path in sorted(run_directory.glob("*"))
        if path.is_file()
    }
    receipt = {
        "request_sha256": request_hash,
        "failed_stage": stage,
        "last_valid_stage": last_valid_stage,
        "reason_codes": reason_codes,
        "error_type": type(error).__name__,
        "message": str(error),
        "diagnostics": diagnostics,
        "last_valid_artifact_sha256": artifacts,
        "recorded_unix_ns": time.time_ns(),
    }
    identity = hashlib.sha256(_canonical_json(receipt)).hexdigest()
    directory = output_root / ".failed" / event / request_hash / identity
    directory.mkdir(parents=True, exist_ok=False)
    _write_json(directory / "failure-receipt.json", receipt)


def _validate_canonical(
    canonical: Path,
    request_hash: str,
    repository_root: Path,
    environment: dict[str, Any] | None = None,
) -> None:
    params = json.loads((canonical / "params.json").read_text())
    provenance = json.loads((canonical / "provenance.json").read_text())
    if (
        params["request_sha256"] != request_hash
        or provenance["request_sha256"] != request_hash
    ):
        raise WorkflowFailure(
            "canonical result belongs to a different request",
            reason_codes=["provenance-request-mismatch"],
        )
    if environment is not None:
        if (
            provenance["environment"]["manifest_sha256"]
            != environment["manifest_sha256"]
        ):
            raise WorkflowFailure(
                "canonical result environment differs from current environment",
                reason_codes=["provenance-environment-mismatch"],
            )
        if provenance["code"]["commit"] != environment["code"]["commit"]:
            raise WorkflowFailure(
                "canonical result commit differs from current checkout",
                reason_codes=["provenance-commit-mismatch"],
            )
    for name, identity in params["products"].items():
        if _sha256(canonical / name) != identity["sha256"]:
            raise WorkflowFailure(
                f"canonical product hash mismatch: {name}",
                reason_codes=["provenance-output-hash-mismatch"],
                diagnostics={"product": name},
            )
    jsonschema.validate(
        params,
        json.loads(
            (
                repository_root
                / "analysis-configs"
                / "dualband-burst-models"
                / "params.schema.json"
            ).read_text()
        ),
    )
    for name, expected in provenance["outputs"].items():
        if _sha256(canonical / name) != expected:
            raise WorkflowFailure(
                f"provenance output hash mismatch: {name}",
                reason_codes=["provenance-output-hash-mismatch"],
                diagnostics={"product": name},
            )
    acceptance = params.get("owner_acceptance")
    if acceptance is not None:
        receipt = canonical.parent.parent / acceptance["receipt_path"]
        if not receipt.exists() or _sha256(receipt) != acceptance["receipt_sha256"]:
            raise WorkflowFailure(
                "owner acceptance receipt is missing or changed",
                reason_codes=["provenance-owner-acceptance-mismatch"],
            )


def _validate_stage_product(
    product: Path,
    receipt: Path,
    request_hash: str,
    hash_field: str,
    environment_sha256: str | None = None,
) -> None:
    if not product.exists() and not receipt.exists():
        return
    if not product.exists() or not receipt.exists():
        raise WorkflowFailure(
            "partial stage output cannot be resumed",
            reason_codes=["provenance-partial-stage"],
        )
    identity = json.loads(receipt.read_text())
    if identity["request_sha256"] != request_hash:
        raise WorkflowFailure(
            "stage receipt belongs to another request",
            reason_codes=["provenance-stage-request-mismatch"],
        )
    if (
        environment_sha256 is not None
        and identity.get("environment_sha256") != environment_sha256
    ):
        raise WorkflowFailure(
            "stage receipt environment differs from current environment",
            reason_codes=["provenance-environment-mismatch"],
        )
    if identity[hash_field] != _sha256(product):
        raise WorkflowFailure(
            "stage product changed after receipt",
            reason_codes=["provenance-stage-hash-mismatch"],
            diagnostics={"product": product.name},
        )


def run_event(
    event: str,
    stage: str,
    repository_root: Path,
    output_root: Path,
) -> Path:
    """Run through one requested stage, resuming only hash-identical products."""

    if stage not in _STAGES:
        raise ValueError(f"unknown stage: {stage}")
    repository_root = repository_root.resolve()
    output_root = output_root.resolve()
    preflight_run = output_root / ".runs" / event / "preflight-unavailable"
    try:
        configuration = _load_configuration(event, repository_root)
        if configuration["source"]["kind"] != "synthetic":
            raise ValueError("Wave 1 admits only the synthetic source adapter")
        request_hash = _request_hash(configuration, repository_root)
        preflight_run = output_root / ".runs" / event / request_hash
        environment = _environment_preflight(repository_root)
    except Exception as error:
        _write_failure(
            output_root,
            event,
            preflight_run.name,
            "preflight",
            error,
            None,
            preflight_run,
        )
        raise
    canonical = output_root / "dualband-burst-models" / event
    if canonical.exists():
        _validate_canonical(
            canonical,
            request_hash,
            repository_root,
            environment,
        )
        return canonical

    run_directory = output_root / ".runs" / event / request_hash
    run_directory.mkdir(parents=True, exist_ok=True)
    event_data = build_synthetic_event(configuration)
    target_index = _STAGES.index(stage)
    current_stage = "observations"
    last_valid_stage = None
    try:
        observations_path = run_directory / "observations.npz"
        observations_receipt = run_directory / "observations-receipt.json"
        _validate_stage_product(
            observations_path,
            observations_receipt,
            request_hash,
            "output_sha256",
            environment["manifest_sha256"],
        )
        if target_index >= 0 and not observations_path.exists():
            _save_observations(observations_path, event_data)
            _write_json(
                observations_receipt,
                {
                    "request_sha256": request_hash,
                    "environment_sha256": environment["manifest_sha256"],
                    "output_sha256": _sha256(observations_path),
                },
            )
        last_valid_stage = "observations"
        if target_index == 0:
            return run_directory

        current_stage = "fit"
        fit_path = run_directory / "posterior.npz"
        model_path = run_directory / "model-products.npz"
        fit_receipt = run_directory / "fit-receipt.json"
        _validate_stage_product(
            fit_path,
            fit_receipt,
            request_hash,
            "posterior_sha256",
            environment["manifest_sha256"],
        )
        if fit_path.exists() != model_path.exists():
            raise WorkflowFailure(
                "partial fit products cannot be resumed",
                reason_codes=["provenance-partial-fit"],
            )
        if fit_path.exists() and model_path.exists():
            fit_identity = json.loads(fit_receipt.read_text())
            if fit_identity["model_products_sha256"] != _sha256(model_path):
                raise WorkflowFailure(
                    "model product changed after receipt",
                    reason_codes=["provenance-stage-hash-mismatch"],
                    diagnostics={"product": model_path.name},
                )
            result = _load_fit(fit_path, model_path, event_data)
        else:
            checkpoint_directory = run_directory / "checkpoints"
            result = fit_joint_event(
                replace(
                    event_data.request,
                    checkpoint_directory=str(checkpoint_directory),
                )
            )
            _save_fit(fit_path, result)
            _save_model_products(model_path, event_data, result)
            _write_json(
                fit_receipt,
                {
                    "request_sha256": request_hash,
                    "environment_sha256": environment["manifest_sha256"],
                    "posterior_sha256": _sha256(fit_path),
                    "model_products_sha256": _sha256(model_path),
                    "status": result.status,
                    "morphology_weights": dict(result.morphology_weights),
                    "morphology_statuses": dict(result.morphology_statuses),
                    "morphology_log_evidences": dict(
                        result.morphology_log_evidences
                    ),
                    "morphology_log_evidence_uncertainties": dict(
                        result.morphology_log_evidence_uncertainties
                    ),
                    "morphology_maximum_prior_edge_mass": dict(
                        result.morphology_maximum_prior_edge_mass
                    ),
                    "prior_edge_mass_by_parameter": dict(
                        result.prior_edge_mass_by_parameter
                    ),
                    "checkpoint_sha256": {
                        path.name: _sha256(path)
                        for path in sorted(checkpoint_directory.glob("*.pkl"))
                    },
                },
            )
        if result.status != "provisional-owner-review":
            raise WorkflowFailure(
                f"fit ended with status {result.status}",
                reason_codes=["inference-prior-boundary"],
                diagnostics={
                    "morphology_weights": dict(result.morphology_weights),
                    "morphology_statuses": dict(result.morphology_statuses),
                    "prior_edge_mass_by_parameter": dict(
                        result.prior_edge_mass_by_parameter
                    ),
                },
            )
        last_valid_stage = "fit"
        if target_index == 1:
            return run_directory

        current_stage = "verify"
        checks = _verification(event_data, result, configuration)
        _write_json(
            run_directory / "verification-receipt.json",
            {
                "request_sha256": request_hash,
                "environment_sha256": environment["manifest_sha256"],
                "checks": checks,
            },
        )
        last_valid_stage = "verify"
        if target_index == 2:
            return run_directory

        current_stage = "review"
        _render_review_packet(
            run_directory / "review-packet.pdf",
            event_data,
            result,
            checks,
            request_hash,
        )
        provenance = {
            "request_sha256": request_hash,
            "configuration_sha256": hashlib.sha256(
                _canonical_json(configuration)
            ).hexdigest(),
            "observation_product_sha256": _sha256(observations_path),
            "repository_root": str(repository_root),
            "source_kind": "synthetic",
            "environment": environment,
            "code": _git_identity(repository_root),
            "lock_sha256": _sha256(repository_root / "uv.lock"),
            "inputs": {
                observation.instrument: dict(observation.input_hashes)
                for observation in event_data.request.observations
            },
            "stage_receipts": {
                name: _sha256(run_directory / name)
                for name in (
                    "observations-receipt.json",
                    "fit-receipt.json",
                    "verification-receipt.json",
                )
            },
            "outputs": {
                name: _sha256(run_directory / name)
                for name in (
                    "posterior.npz",
                    "model-products.npz",
                    "review-packet.pdf",
                )
            },
        }
        _write_json(run_directory / "provenance.json", provenance)
        products = {}
        for name in (
            "posterior.npz",
            "model-products.npz",
            "provenance.json",
            "review-packet.pdf",
        ):
            products[name] = {"path": name, "sha256": _sha256(run_directory / name)}
        params = {
            "schema_version": "1.0.0",
            "event": configuration["event"],
            "request_sha256": request_hash,
            "status": "provisional-owner-review",
            "timing": {
                "reference_frequency_mhz": 400.0,
                "coordinate": "geocentric unscattered arrival time",
            },
            "shared_absolute_dm": {
                **asdict(result.shared_dm),
                "uncertainty_classes": _dm_uncertainty_classes(
                    result,
                    configuration["uncertainty_budget"],
                ),
            },
            "components": [
                {
                    "id": component,
                    "geocentric_toa_400_s": asdict(summary),
                    "geocentric_toa_400_utc": {
                        key: _utc_string(
                            event_data.request.geometry.epoch_unix_ns,
                            value,
                        )
                        for key, value in asdict(summary).items()
                    },
                    "chimefrb_toa_400_s": asdict(
                        _weighted_summary(
                            result.samples[:, result.parameter_names.index(
                                f"toa_400_s:{component}"
                            )]
                            + result.samples[:, result.parameter_names.index(
                                "timing_error_s:chimefrb"
                            )]
                            + event_data.request.geometry.station_delays_s[
                                "chimefrb"
                            ],
                            result.weights,
                        )
                    ),
                    "chimefrb_toa_400_utc": {
                        key: _utc_string(
                            event_data.request.geometry.epoch_unix_ns,
                            value,
                        )
                        for key, value in asdict(
                            _weighted_summary(
                                result.samples[
                                    :,
                                    result.parameter_names.index(
                                        f"toa_400_s:{component}"
                                    ),
                                ]
                                + result.samples[
                                    :,
                                    result.parameter_names.index(
                                        "timing_error_s:chimefrb"
                                    ),
                                ]
                                + event_data.request.geometry.station_delays_s[
                                    "chimefrb"
                                ],
                                result.weights,
                            )
                        ).items()
                    },
                    "dsa110_toa_400_s": asdict(
                        _weighted_summary(
                            result.samples[:, result.parameter_names.index(
                                f"toa_400_s:{component}"
                            )]
                            + result.samples[:, result.parameter_names.index(
                                "timing_error_s:dsa110"
                            )]
                            + event_data.request.geometry.station_delays_s[
                                "dsa110"
                            ],
                            result.weights,
                        )
                    ),
                    "dsa110_toa_400_utc": {
                        key: _utc_string(
                            event_data.request.geometry.epoch_unix_ns,
                            value,
                        )
                        for key, value in asdict(
                            _weighted_summary(
                                result.samples[
                                    :,
                                    result.parameter_names.index(
                                        f"toa_400_s:{component}"
                                    ),
                                ]
                                + result.samples[
                                    :,
                                    result.parameter_names.index(
                                        "timing_error_s:dsa110"
                                    ),
                                ]
                                + event_data.request.geometry.station_delays_s[
                                    "dsa110"
                                ],
                                result.weights,
                            )
                        ).items()
                    },
                }
                for component, summary in zip(
                    event_data.request.component_ids,
                    result.component_toas,
                    strict=True,
                )
            ],
            "model_parameters": {
                name: asdict(
                    _weighted_summary(
                        result.samples[:, index],
                        result.weights,
                    )
                )
                for index, name in enumerate(result.parameter_names)
                if name != "absolute_dm"
                and not name.startswith("toa_400_s:")
            },
            "morphology_weights": dict(result.morphology_weights),
            "morphology_statuses": dict(result.morphology_statuses),
            "morphology_log_evidences": dict(
                result.morphology_log_evidences
            ),
            "morphology_log_evidence_uncertainties": dict(
                result.morphology_log_evidence_uncertainties
            ),
            "association_weights": dict(result.association_weights),
            "verification": checks,
            "products": products,
        }
        _write_json(run_directory / "params.json", params)
        params_schema = json.loads(
            (
                repository_root
                / "analysis-configs"
                / "dualband-burst-models"
                / "params.schema.json"
            ).read_text()
        )
        jsonschema.validate(params, params_schema)
        publication = canonical.with_name(canonical.name + ".publishing")
        publication.parent.mkdir(parents=True, exist_ok=True)
        if publication.exists():
            shutil.rmtree(publication)
        publication.mkdir()
        for name in _CANONICAL_PRODUCTS:
            shutil.copy2(run_directory / name, publication / name)
        os.replace(publication, canonical)
        _validate_canonical(
            canonical,
            request_hash,
            repository_root,
            environment,
        )
        return canonical
    except Exception as error:
        _write_failure(
            output_root,
            event,
            request_hash,
            current_stage,
            error,
            last_valid_stage,
            run_directory,
        )
        raise


def promote_result(result_directory: Path, owner: str) -> None:
    """Record owner acceptance without changing inferred scientific products."""

    if not owner:
        raise ValueError("owner identity is required")
    params_path = result_directory / "params.json"
    params = json.loads(params_path.read_text())
    provenance = json.loads((result_directory / "provenance.json").read_text())
    repository_root = Path(provenance["repository_root"])
    _validate_canonical(
        result_directory,
        params["request_sha256"],
        repository_root,
    )
    if params["status"] != "provisional-owner-review":
        raise ValueError("only a provisional result can be accepted")
    if not all(item["passed"] for item in params["verification"].values()):
        raise ValueError("only a fully verified result can be accepted")
    scientific_hashes = {
        name: _sha256(result_directory / name)
        for name in ("posterior.npz", "model-products.npz")
    }
    promotion = {
        "request_sha256": params["request_sha256"],
        "owner": owner,
        "scientific_product_sha256": scientific_hashes,
        "pre_promotion_params_sha256": _sha256(params_path),
    }
    promotion["promotion_sha256"] = hashlib.sha256(
        _canonical_json(promotion)
    ).hexdigest()
    receipt_directory = (
        result_directory.parent.parent
        / ".acceptance"
        / result_directory.name
        / promotion["promotion_sha256"]
    )
    receipt_directory.mkdir(parents=True, exist_ok=False)
    _write_json(receipt_directory / "owner-acceptance.json", promotion)
    params["status"] = "accepted"
    params["owner_acceptance"] = {
        "owner": owner,
        "scientific_product_sha256": scientific_hashes,
        "receipt_path": str(
            receipt_directory.relative_to(result_directory.parent.parent)
            / "owner-acceptance.json"
        ),
        "receipt_sha256": _sha256(receipt_directory / "owner-acceptance.json"),
    }
    _write_json(params_path, params)
