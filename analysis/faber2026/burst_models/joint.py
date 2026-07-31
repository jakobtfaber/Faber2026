"""One shared dispersion measure and geocentric 400 MHz arrival-time model."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from functools import partial
from pathlib import Path

import jsonschema
import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.special import logsumexp, ndtri

from faber2026.observations import BandObservation

from .kernels import (
    REFERENCE_FREQUENCY_MHZ,
    dispersion_delay_s,
    exponentially_modified_gaussian,
    gaussian_density,
    gaussian_power_law_density,
    scattering_index,
)

_MORPHOLOGIES = {"gaussian", "emg", "powerlaw"}
_CHECKPOINT_MODEL_VERSION = "joint-burst-v1"
_CHECKPOINT_RECEIPT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["schema_version", "binding", "binding_sha256"],
    "properties": {
        "schema_version": {"const": "1.0.0"},
        "binding_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "binding": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "run_context", "model_version", "association", "morphology",
                "parameters", "prior_specs", "nlive", "dlogz"
            ],
            "properties": {
                "run_context": {
                    "type": "object", "additionalProperties": False,
                    "required": ["request_sha256", "environment_sha256", "schema_version", "model_version", "input_hashes"],
                    "properties": {
                        "request_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                        "environment_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                        "schema_version": {"const": "1.0.0"},
                        "model_version": {"const": _CHECKPOINT_MODEL_VERSION},
                        "input_hashes": {
                            "type": "object", "additionalProperties": False,
                            "required": ["chimefrb", "dsa110"],
                            "properties": {
                                instrument: {
                                    "type": "object", "minProperties": 1,
                                    "additionalProperties": {
                                        "type": "string", "pattern": "^sha256:[0-9a-f]{64}$"
                                    },
                                }
                                for instrument in ("chimefrb", "dsa110")
                            },
                        },
                    },
                },
                "model_version": {"const": _CHECKPOINT_MODEL_VERSION},
                "association": {"type": "string", "minLength": 1},
                "morphology": {"enum": sorted(_MORPHOLOGIES)},
                "parameters": {"type": "array", "minItems": 1},
                "prior_specs": {"type": "array", "minItems": 1},
                "nlive": {"type": "integer", "minimum": 20},
                "dlogz": {"type": "number", "exclusiveMinimum": 0},
            },
        },
    },
}


@dataclass(frozen=True, slots=True)
class GeometryConstraint:
    """Measured station delays relative to the geocenter."""

    reference_frequency_mhz: float
    epoch_unix_ns: int
    station_delays_s: Mapping[str, float]
    station_delay_uncertainties_s: Mapping[str, float]
    clock_uncertainties_s: Mapping[str, float]
    independent_projection_difference_s: float
    maximum_projection_difference_s: float

    def validate(self) -> None:
        if self.reference_frequency_mhz != REFERENCE_FREQUENCY_MHZ:
            raise ValueError("geometry must use the 400 MHz timing reference")
        if not isinstance(self.epoch_unix_ns, int):
            raise ValueError("geometry epoch must be an integer Unix nanosecond")
        for instrument in ("chimefrb", "dsa110"):
            if instrument not in self.station_delays_s:
                raise ValueError(f"missing {instrument} station delay")
            for uncertainties in (
                self.station_delay_uncertainties_s,
                self.clock_uncertainties_s,
            ):
                if instrument not in uncertainties or uncertainties[instrument] <= 0:
                    raise ValueError(f"missing positive {instrument} timing uncertainty")
        if (
            not np.isfinite(self.independent_projection_difference_s)
            or self.independent_projection_difference_s
            > self.maximum_projection_difference_s
        ):
            raise ValueError("independent geometry projections disagree")


@dataclass(frozen=True, slots=True)
class ComponentMatch:
    """One matched component across the two instrument detections."""

    latent_id: str
    chimefrb_component_id: str
    dsa110_component_id: str


@dataclass(frozen=True, slots=True)
class AssociationHypothesis:
    """One reviewed, one-to-one, order-preserving association."""

    association_id: str
    matches: tuple[ComponentMatch, ...]


@dataclass(frozen=True, slots=True)
class JointFitRequest:
    """Frozen scientific request for one association and morphology."""

    observations: tuple[BandObservation, BandObservation]
    geometry: GeometryConstraint
    component_ids: tuple[str, ...]
    band_component_ids: Mapping[str, tuple[str, ...]]
    associations: tuple[AssociationHypothesis, ...]
    morphology: str | tuple[str, ...]
    dm_bounds: tuple[float, float]
    toa_bounds_s: tuple[tuple[float, float], ...]
    width_bounds_s: tuple[tuple[float, float], ...]
    width_index_bounds: tuple[float, float]
    seed: int
    nlive: int
    dlogz: float
    scattering_tau_1ghz_bounds_s: tuple[float, float] = (1e-6, 0.02)
    beta_bounds: tuple[float, float] = (3.0, 4.0)
    maximum_failed_morphology_weight: float = 1e-6
    component_amplitude_bounds: tuple[float, float] = (1e-3, 1e3)
    checkpoint_directory: str | None = None
    checkpoint_identity: str | None = None
    checkpoint_context: Mapping[str, object] = field(default_factory=dict)
    band_component_toa_bounds_s: Mapping[
        str, Mapping[str, tuple[float, float]]
    ] = field(default_factory=dict)

    def validate(self) -> None:
        if len(self.observations) != 2:
            raise ValueError("exactly two band observations are required")
        if {item.instrument for item in self.observations} != {"chimefrb", "dsa110"}:
            raise ValueError("one CHIME/FRB and one DSA-110 observation are required")
        for observation in self.observations:
            observation.validate()
        self.geometry.validate()
        if not self.component_ids or len(set(self.component_ids)) != len(self.component_ids):
            raise ValueError("unique component identifiers are required")
        if not self.associations:
            raise ValueError("at least one association is required")
        association_ids = [item.association_id for item in self.associations]
        if len(set(association_ids)) != len(association_ids):
            raise ValueError("association identifiers must be unique")
        for instrument in ("chimefrb", "dsa110"):
            identifiers = self.band_component_ids.get(instrument, ())
            if not identifiers or len(set(identifiers)) != len(identifiers):
                raise ValueError("unique band component identifiers are required")
            windows = self.band_component_toa_bounds_s.get(instrument)
            if windows is None:
                continue
            if set(windows) != set(identifiers):
                raise ValueError("one native time window is required per band component")
            if any(
                len(bounds) != 2 or bounds[0] >= bounds[1]
                for bounds in windows.values()
            ):
                raise ValueError("band component time windows must increase")
        for association in self.associations:
            if not association.association_id or not association.matches:
                raise ValueError("association identity is required")
            latent_ids = [match.latent_id for match in association.matches]
            chime_ids = [
                match.chimefrb_component_id for match in association.matches
            ]
            dsa_ids = [match.dsa110_component_id for match in association.matches]
            if tuple(latent_ids) != self.component_ids:
                raise ValueError("association must name every latent component in order")
            for instrument, identifiers in (
                ("chimefrb", chime_ids),
                ("dsa110", dsa_ids),
            ):
                declared = self.band_component_ids[instrument]
                try:
                    indices = [declared.index(identifier) for identifier in identifiers]
                except ValueError as error:
                    raise ValueError("association names an unknown band component") from error
                if indices != sorted(indices) or len(indices) != len(set(indices)):
                    raise ValueError("association must be one-to-one and order-preserving")
        association_windows_required = len(self.associations) > 1 or any(
            set(self.band_component_ids[instrument])
            != {
                match.chimefrb_component_id
                if instrument == "chimefrb"
                else match.dsa110_component_id
                for match in association.matches
            }
            for association in self.associations
            for instrument in ("chimefrb", "dsa110")
        )
        if association_windows_required:
            for instrument in ("chimefrb", "dsa110"):
                if instrument not in self.band_component_toa_bounds_s:
                    raise ValueError(
                        "association fitting requires native component time windows"
                    )
        morphologies = (
            (self.morphology,)
            if isinstance(self.morphology, str)
            else self.morphology
        )
        if (
            not morphologies
            or len(set(morphologies)) != len(morphologies)
            or any(item not in _MORPHOLOGIES for item in morphologies)
        ):
            raise ValueError("unknown morphology")
        if len(self.toa_bounds_s) != len(self.component_ids):
            raise ValueError("one arrival-time bound is required per component")
        if len(self.width_bounds_s) != len(self.component_ids):
            raise ValueError("one width bound is required per component")
        bounds = (
            (self.dm_bounds,)
            + self.toa_bounds_s
            + self.width_bounds_s
            + (self.width_index_bounds,)
            + (self.component_amplitude_bounds,)
        )
        if any(not low < high for low, high in bounds):
            raise ValueError("all prior bounds must be ordered")
        if self.nlive < 20 or self.dlogz <= 0:
            raise ValueError("invalid nested-sampling controls")
        if not 0 <= self.maximum_failed_morphology_weight < 1:
            raise ValueError("invalid failed-morphology weight limit")
        if self.checkpoint_directory is not None and (
            not self.checkpoint_identity or not self.checkpoint_context
        ):
            raise ValueError("checkpoint identity is required for resumable inference")


@dataclass(frozen=True, slots=True)
class PosteriorSummary:
    median: float
    lower: float
    upper: float


@dataclass(frozen=True, slots=True)
class JointFitResult:
    status: str
    shared_dm: PosteriorSummary
    component_toas: tuple[PosteriorSummary, ...]
    parameter_names: tuple[str, ...]
    parameter_units: tuple[str, ...]
    samples: NDArray[np.floating]
    weights: NDArray[np.floating]
    sample_morphologies: NDArray[np.str_]
    sample_associations: NDArray[np.str_]
    log_evidence: float
    log_evidence_uncertainty: float
    maximum_not_on_boundary: bool
    prior_edge_mass_by_parameter: Mapping[str, float]
    morphology_weights: Mapping[str, float]
    morphology_statuses: Mapping[str, str]
    morphology_log_evidences: Mapping[str, float]
    morphology_log_evidence_uncertainties: Mapping[str, float]
    morphology_maximum_prior_edge_mass: Mapping[str, float]
    association_weights: Mapping[str, float]
    model_by_instrument: Mapping[str, NDArray[np.floating]]
    residual_by_instrument: Mapping[str, NDArray[np.floating]]


def _parameter_names(request: JointFitRequest) -> tuple[str, ...]:
    if not isinstance(request.morphology, str):
        raise ValueError("likelihood evaluation requires one morphology")
    names = ["absolute_dm"]
    names.extend(f"toa_400_s:{component}" for component in request.component_ids)
    names.extend(f"width_400_s:{component}" for component in request.component_ids)
    names.append("width_index")
    names.extend(
        (
            "timing_error_s:chimefrb",
            "timing_error_s:dsa110",
        )
    )
    if request.morphology != "gaussian":
        names.append("tau_1ghz_s")
    if request.morphology == "powerlaw":
        names.append("beta")
    association = request.associations[0]
    matched = {
        "chimefrb": {item.chimefrb_component_id for item in association.matches},
        "dsa110": {item.dsa110_component_id for item in association.matches},
    }
    for instrument in ("chimefrb", "dsa110"):
        for component in request.band_component_ids[instrument]:
            names.append(f"amplitude:{instrument}:{component}")
            if component not in matched[instrument]:
                names.extend(
                    (
                        f"local_toa_s:{instrument}:{component}",
                        f"local_width_s:{instrument}:{component}",
                    )
                )
    return tuple(names)


def _parameter_units(names: tuple[str, ...]) -> tuple[str, ...]:
    units = []
    for name in names:
        if name == "absolute_dm":
            units.append("pc cm-3")
        elif name == "width_index" or name == "beta":
            units.append("dimensionless")
        else:
            units.append("s")
    return tuple(units)


def _prior_specs(
    request: JointFitRequest,
) -> tuple[tuple[str, float, float], ...]:
    if not isinstance(request.morphology, str):
        raise ValueError("likelihood evaluation requires one morphology")
    specs: list[tuple[str, float, float]] = [
        ("uniform", *request.dm_bounds)
    ]
    specs.extend(("uniform", *bounds) for bounds in request.toa_bounds_s)
    specs.extend(("log_uniform", *bounds) for bounds in request.width_bounds_s)
    specs.append(("uniform", *request.width_index_bounds))
    for instrument in ("chimefrb", "dsa110"):
        sigma = math.hypot(
            request.geometry.station_delay_uncertainties_s[instrument],
            request.geometry.clock_uncertainties_s[instrument],
        )
        specs.append(("normal", 0.0, sigma))
    if request.morphology != "gaussian":
        specs.append(("log_uniform", *request.scattering_tau_1ghz_bounds_s))
    if request.morphology == "powerlaw":
        specs.append(("uniform", *request.beta_bounds))
    association = request.associations[0]
    matched = {
        "chimefrb": {item.chimefrb_component_id for item in association.matches},
        "dsa110": {item.dsa110_component_id for item in association.matches},
    }
    observations = {item.instrument: item for item in request.observations}
    for instrument in ("chimefrb", "dsa110"):
        observation = observations[instrument]
        for component in request.band_component_ids[instrument]:
            specs.append(("log_uniform", *request.component_amplitude_bounds))
            if component not in matched[instrument]:
                windows = request.band_component_toa_bounds_s.get(instrument, {})
                half_bin = 0.5 * observation.sample_interval_s
                local_bounds = windows.get(
                    component,
                    (
                        float(observation.times_s[0] - half_bin),
                        float(observation.times_s[-1] + half_bin),
                    ),
                )
                specs.extend(
                    (
                        ("uniform", *local_bounds),
                        ("log_uniform", *request.width_bounds_s[0]),
                    )
                )
    return tuple(specs)


def _unpack(
    request: JointFitRequest, parameters: ArrayLike
) -> tuple[
    float,
    NDArray[np.floating],
    NDArray[np.floating],
    float,
    dict[str, float],
    float,
    float,
]:
    values = np.asarray(parameters, dtype=float)
    if not isinstance(request.morphology, str):
        raise ValueError("likelihood evaluation requires one morphology")
    count = len(request.component_ids)
    dm = float(values[0])
    toas = values[1 : 1 + count]
    widths = values[1 + count : 1 + 2 * count]
    width_index = float(values[1 + 2 * count])
    cursor = 2 + 2 * count
    timing_errors = {
        "chimefrb": float(values[cursor]),
        "dsa110": float(values[cursor + 1]),
    }
    cursor += 2
    tau = 0.0
    beta = 4.0
    if request.morphology != "gaussian":
        tau = float(values[cursor])
        cursor += 1
    if request.morphology == "powerlaw":
        beta = float(values[cursor])
    return dm, toas, widths, width_index, timing_errors, tau, beta


def _component_profile(
    request: JointFitRequest,
    observation: BandObservation,
    parameters: ArrayLike,
) -> NDArray[np.floating]:
    if not isinstance(request.morphology, str):
        raise ValueError("likelihood evaluation requires one morphology")
    (
        dm,
        toas,
        widths,
        width_index,
        timing_errors,
        tau_1ghz,
        beta,
    ) = _unpack(request, parameters)
    frequency_nodes, frequency_weights = np.polynomial.legendre.leggauss(3)
    time_nodes, time_weights = np.polynomial.legendre.leggauss(3)
    frequencies = np.asarray(observation.frequencies_mhz)[None, :] + (
        0.5
        * frequency_nodes[:, None]
        * np.asarray(observation.channel_widths_mhz)[None, :]
    )
    centers = (
        toas[:, None, None]
        + request.geometry.station_delays_s[observation.instrument]
        + timing_errors[observation.instrument]
        - (
            observation.time_origin_unix_ns
            - request.geometry.epoch_unix_ns
        )
        * 1e-9
        - observation.dispersion.time_origin_correction_s
        + dispersion_delay_s(
            dm - observation.dispersion.product_dm, frequencies
        )[None, :, :]
    )
    width_by_frequency = widths[:, None, None] * (
        frequencies[None, :, :] / REFERENCE_FREQUENCY_MHZ
    ) ** width_index
    time = (
        np.asarray(observation.times_s)[None, :]
        + 0.5
        * observation.sample_interval_s
        * time_nodes[:, None]
    )[None, None, None, :, :]
    center = centers[:, :, :, None, None]
    sigma = width_by_frequency[:, :, :, None, None]
    if request.morphology == "gaussian":
        components = gaussian_density(time, center, sigma)
    elif request.morphology == "emg":
        tau = tau_1ghz * (frequencies / 1000.0) ** -4.0
        components = exponentially_modified_gaussian(
            time, center, sigma, tau[None, :, :, None, None]
        )
    else:
        alpha = scattering_index(beta)
        tau = tau_1ghz * (frequencies / 1000.0) ** -alpha
        components = gaussian_power_law_density(
            time,
            center,
            sigma,
            tau[None, :, :, None, None],
            beta,
        )
    weights = (
        0.25
        * frequency_weights[None, :, None, None, None]
        * time_weights[None, None, None, :, None]
    )
    profiles = np.sum(weights * components, axis=(1, 3))
    association = request.associations[0]
    matches = {
        "chimefrb": {
            item.latent_id: item.chimefrb_component_id
            for item in association.matches
        },
        "dsa110": {
            item.latent_id: item.dsa110_component_id
            for item in association.matches
        },
    }[observation.instrument]
    names = _parameter_names(request)
    parameter_map = dict(zip(names, np.asarray(parameters, dtype=float), strict=True))
    total = np.zeros_like(profiles[0])
    for index, latent_id in enumerate(request.component_ids):
        component_id = matches[latent_id]
        total += (
            parameter_map[
                f"amplitude:{observation.instrument}:{component_id}"
            ]
            * profiles[index]
        )
    matched_ids = set(matches.values())
    time_centers = np.asarray(observation.times_s)[None, :] + (
        0.5
        * observation.sample_interval_s
        * time_nodes[:, None]
    )
    for component_id in request.band_component_ids[observation.instrument]:
        if component_id in matched_ids:
            continue
        local = np.sum(
            0.5
            * time_weights[:, None]
            * gaussian_density(
                time_centers,
                parameter_map[
                    f"local_toa_s:{observation.instrument}:{component_id}"
                ],
                parameter_map[
                    f"local_width_s:{observation.instrument}:{component_id}"
                ],
            ),
            axis=0,
        )
        total += (
            parameter_map[
                f"amplitude:{observation.instrument}:{component_id}"
            ]
            * local[None, :]
        )
    return total


def _matched_component_windows_allow(
    request: JointFitRequest,
    parameters: ArrayLike,
) -> bool:
    """Require each declared match to occupy its reviewed native window."""

    _, toas, _, _, timing_errors, _, _ = _unpack(request, parameters)
    matched = request.associations[0].matches
    observations = {item.instrument: item for item in request.observations}
    for latent_index, match in enumerate(matched):
        for instrument, component_id in (
            ("chimefrb", match.chimefrb_component_id),
            ("dsa110", match.dsa110_component_id),
        ):
            observation = observations[instrument]
            center = (
                toas[latent_index]
                + request.geometry.station_delays_s[instrument]
                + timing_errors[instrument]
                - (
                    observation.time_origin_unix_ns
                    - request.geometry.epoch_unix_ns
                )
                * 1e-9
                - observation.dispersion.time_origin_correction_s
            )
            windows = request.band_component_toa_bounds_s.get(instrument)
            if windows is None:
                continue
            lower, upper = windows[component_id]
            if center < lower or center > upper:
                return False
    return True


def _gain_marginal_log_likelihood(
    data: NDArray[np.floating],
    model: NDArray[np.floating],
    valid: NDArray[np.bool_],
    noise_by_row: NDArray[np.floating],
    gain_prior_std: float,
) -> float:
    """Integrate channel amplitudes with a zero-mean normal prior."""

    total = 0.0
    prior_precision = gain_prior_std**-2
    for row in range(data.shape[0]):
        keep = valid[row]
        y = data[row, keep]
        m = model[row, keep]
        inverse_variance = noise_by_row[row] ** -2
        precision = prior_precision + inverse_variance * float(m @ m)
        linear = inverse_variance * float(m @ y)
        constant = inverse_variance * float(y @ y)
        total += -0.5 * (
            constant
            - linear**2 / precision
            + math.log(precision * gain_prior_std**2)
            + y.size * math.log(2.0 * math.pi * noise_by_row[row] ** 2)
        )
    return total


def _posterior_gain_model(
    data: NDArray[np.floating],
    model: NDArray[np.floating],
    valid: NDArray[np.bool_],
    noise_by_row: NDArray[np.floating],
    gain_prior_std: float,
) -> NDArray[np.floating]:
    """Return the posterior-mean channel-amplitude model used by diagnostics."""

    adjusted = np.zeros_like(model)
    prior_precision = gain_prior_std**-2
    for row in range(data.shape[0]):
        keep = valid[row]
        inverse_variance = noise_by_row[row] ** -2
        m = model[row, keep]
        precision = prior_precision + inverse_variance * float(m @ m)
        gain_mean = inverse_variance * float(m @ data[row, keep]) / precision
        adjusted[row] = gain_mean * model[row]
    return adjusted


def evaluate_log_likelihood(request: JointFitRequest, parameters: ArrayLike) -> float:
    """Evaluate the native-grid joint likelihood without modifying either band."""

    request.validate()
    if not isinstance(request.morphology, str):
        raise ValueError("likelihood evaluation requires one morphology")
    if not _matched_component_windows_allow(request, parameters):
        return -np.inf
    values = np.asarray(parameters, dtype=float)
    specs = _prior_specs(request)
    if values.shape != (len(specs),):
        raise ValueError("parameter vector has the wrong length")
    for value, (kind, first, second) in zip(values, specs, strict=True):
        if kind in {"uniform", "log_uniform"} and (
            value < first or value > second
        ):
            return -np.inf
    total = 0.0
    for observation in request.observations:
        model = _component_profile(request, observation, values)
        total += _gain_marginal_log_likelihood(
            np.asarray(observation.intensity),
            model,
            np.asarray(observation.valid_pixels),
            np.asarray(observation.noise_std),
            observation.gain_prior_std,
        )
    return float(total)


def _likelihood_for_request(
    parameters: ArrayLike, request: JointFitRequest
) -> float:
    """Pickle-safe Dynesty likelihood wrapper for checkpoint/restart."""

    return evaluate_log_likelihood(request, parameters)


def _prior_transform_for_specs(
    unit: NDArray[np.floating], specs: tuple[tuple[str, float, float], ...]
) -> NDArray[np.floating]:
    """Pickle-safe transform shared by uninterrupted and resumed fits."""

    transformed = []
    for value, (kind, first, second) in zip(unit, specs, strict=True):
        if kind == "uniform":
            transformed.append(first + value * (second - first))
        elif kind == "log_uniform":
            transformed.append(
                math.exp(math.log(first) + value * math.log(second / first))
            )
        else:
            transformed.append(
                first + second * ndtri(np.clip(value, 1e-12, 1.0 - 1e-12))
            )
    return np.asarray(transformed)


def _checkpoint_binding(
    request: JointFitRequest, specs: tuple[tuple[str, float, float], ...]
) -> dict[str, object]:
    """Bind a resumable sampler to its exact inference subproblem."""

    return {
        "run_context": dict(request.checkpoint_context),
        "model_version": _CHECKPOINT_MODEL_VERSION,
        "association": request.associations[0].association_id,
        "morphology": request.morphology,
        "parameters": list(_parameter_names(request)),
        "prior_specs": [list(spec) for spec in specs],
        "nlive": request.nlive,
        "dlogz": request.dlogz,
    }


def _checkpoint_identity(
    request: JointFitRequest, specs: tuple[tuple[str, float, float], ...]
) -> str:
    payload = _checkpoint_binding(request, specs)
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _checkpoint_receipt(
    request: JointFitRequest, specs: tuple[tuple[str, float, float], ...]
) -> dict[str, object]:
    binding = _checkpoint_binding(request, specs)
    receipt = {
        "schema_version": "1.0.0",
        "binding": binding,
        "binding_sha256": _checkpoint_identity(request, specs),
    }
    jsonschema.validate(receipt, _CHECKPOINT_RECEIPT_SCHEMA)
    return receipt


def _weighted_summary(values: NDArray[np.floating], weights: NDArray[np.floating]) -> PosteriorSummary:
    order = np.argsort(values)
    sorted_values = values[order]
    cumulative = np.cumsum(weights[order])
    cumulative /= cumulative[-1]
    lower, median, upper = np.interp([0.16, 0.5, 0.84], cumulative, sorted_values)
    return PosteriorSummary(float(median), float(lower), float(upper))


def _fit_one_morphology(request: JointFitRequest) -> JointFitResult:
    """Fit one declared morphology with deterministic nested sampling."""

    request.validate()
    if not isinstance(request.morphology, str):
        raise ValueError("one morphology is required")
    try:
        import dynesty
    except ImportError as error:
        raise RuntimeError("dynesty 3.1.0 is required for joint fitting") from error

    specs = _prior_specs(request)
    checkpoint_receipt = _checkpoint_receipt(request, specs)

    checkpoint_file = None
    if request.checkpoint_directory is not None:
        directory = Path(request.checkpoint_directory)
        directory.mkdir(parents=True, exist_ok=True)
        checkpoint_file = directory / (
            f"{request.associations[0].association_id}-{request.morphology}.pkl"
        )
    checkpoint_metadata = (
        checkpoint_file.with_suffix(".json") if checkpoint_file is not None else None
    )
    if checkpoint_file and checkpoint_file.exists():
        if checkpoint_metadata is None or not checkpoint_metadata.exists():
            raise RuntimeError("checkpoint identity receipt is missing")
        identity = json.loads(checkpoint_metadata.read_text())
        jsonschema.validate(identity, _CHECKPOINT_RECEIPT_SCHEMA)
        if identity != checkpoint_receipt:
            raise RuntimeError("checkpoint identity differs from this request")
        sampler = dynesty.utils.restore_sampler(str(checkpoint_file))
    else:
        if checkpoint_metadata and checkpoint_metadata.exists():
            raise RuntimeError("checkpoint identity receipt has no sampler")
        if checkpoint_metadata:
            checkpoint_metadata.write_text(
                json.dumps(
                    checkpoint_receipt,
                    sort_keys=True,
                )
                + "\n"
            )
        sampler = dynesty.NestedSampler(
            partial(_likelihood_for_request, request=request),
            partial(_prior_transform_for_specs, specs=specs),
            ndim=len(specs),
            nlive=request.nlive,
            rstate=np.random.default_rng(request.seed),
            sample="rwalk",
            bound="multi",
        )
    sampler.run_nested(
        dlogz=request.dlogz,
        print_progress=False,
        checkpoint_file=str(checkpoint_file) if checkpoint_file else None,
        checkpoint_every=30,
        resume=bool(checkpoint_file and checkpoint_file.exists()),
    )
    nested = sampler.results
    weights = np.exp(nested.logwt - nested.logz[-1])
    weights /= weights.sum()
    samples = np.asarray(nested.samples)
    summaries = tuple(_weighted_summary(samples[:, index], weights) for index in range(samples.shape[1]))
    edge_fraction = 0.01
    names = _parameter_names(request)
    edge_mass = {}
    for index, (name, (kind, first, second)) in enumerate(
        zip(names, specs, strict=True)
    ):
        if kind in {"uniform", "log_uniform"}:
            if kind == "log_uniform":
                coordinate = np.log(samples[:, index])
                low_coordinate = math.log(first)
                high_coordinate = math.log(second)
            else:
                coordinate = samples[:, index]
                low_coordinate = first
                high_coordinate = second
            span = high_coordinate - low_coordinate
            at_edge = (
                coordinate <= low_coordinate + edge_fraction * span
            ) | (coordinate >= high_coordinate - edge_fraction * span)
        else:
            at_edge = np.abs(samples[:, index] - first) >= 4.0 * second
        edge_mass[name] = float(np.sum(weights[at_edge]))
    maximum_not_on_boundary = all(mass <= 0.05 for mass in edge_mass.values())
    dm_summary = summaries[0]
    center = np.asarray([summary.median for summary in summaries])
    models = {}
    for observation in request.observations:
        raw_model = _component_profile(request, observation, center)
        models[observation.instrument] = _posterior_gain_model(
            np.asarray(observation.intensity),
            raw_model,
            np.asarray(observation.valid_pixels),
            np.asarray(observation.noise_std),
            observation.gain_prior_std,
        )
    residuals = {
        observation.instrument: np.asarray(observation.intensity)
        - models[observation.instrument]
        for observation in request.observations
    }
    status = (
        "provisional-owner-review" if maximum_not_on_boundary else "failed-inference"
    )
    count = len(request.component_ids)
    return JointFitResult(
        status=status,
        shared_dm=dm_summary,
        component_toas=summaries[1 : 1 + count],
        parameter_names=names,
        parameter_units=_parameter_units(names),
        samples=samples,
        weights=weights,
        sample_morphologies=np.full(samples.shape[0], request.morphology),
        sample_associations=np.full(
            samples.shape[0], request.associations[0].association_id
        ),
        log_evidence=float(nested.logz[-1]),
        log_evidence_uncertainty=float(nested.logzerr[-1]),
        maximum_not_on_boundary=maximum_not_on_boundary,
        prior_edge_mass_by_parameter=edge_mass,
        morphology_weights={request.morphology: 1.0},
        morphology_statuses={request.morphology: status},
        morphology_log_evidences={request.morphology: float(nested.logz[-1])},
        morphology_log_evidence_uncertainties={
            request.morphology: float(nested.logzerr[-1])
        },
        morphology_maximum_prior_edge_mass={
            request.morphology: max(edge_mass.values())
        },
        association_weights={request.associations[0].association_id: 1.0},
        model_by_instrument=models,
        residual_by_instrument=residuals,
    )


def _mixture_result(
    request: JointFitRequest,
    fits: list[JointFitResult],
) -> JointFitResult:
    log_evidences = np.asarray([fit.log_evidence for fit in fits])
    log_weights = log_evidences - logsumexp(log_evidences)
    model_weights = np.exp(log_weights)
    union_names = tuple(
        dict.fromkeys(
            name
            for fit in fits
            for name in fit.parameter_names
        )
    )
    sample_blocks = []
    weight_blocks = []
    for fit, model_weight in zip(fits, model_weights, strict=True):
        block = np.full((fit.samples.shape[0], len(union_names)), np.nan)
        for source, name in enumerate(fit.parameter_names):
            block[:, union_names.index(name)] = fit.samples[:, source]
        sample_blocks.append(block)
        weight_blocks.append(fit.weights * model_weight)
    samples = np.concatenate(sample_blocks)
    weights = np.concatenate(weight_blocks)
    weights /= weights.sum()
    dm_summary = _weighted_summary(samples[:, union_names.index("absolute_dm")], weights)
    component_toas = tuple(
        _weighted_summary(samples[:, union_names.index(f"toa_400_s:{component}")], weights)
        for component in request.component_ids
    )
    models = {
        observation.instrument: sum(
            model_weight * fit.model_by_instrument[observation.instrument]
            for fit, model_weight in zip(fits, model_weights, strict=True)
        )
        for observation in request.observations
    }
    residuals = {
        observation.instrument: np.asarray(observation.intensity)
        - models[observation.instrument]
        for observation in request.observations
    }
    edge_mass = {}
    for name in union_names:
        contributions = [
            model_weight * fit.prior_edge_mass_by_parameter[name]
            for fit, model_weight in zip(fits, model_weights, strict=True)
            if name in fit.prior_edge_mass_by_parameter
        ]
        edge_mass[name] = float(sum(contributions))
    failed_weight = sum(
        weight
        for weight, fit in zip(model_weights, fits, strict=True)
        if fit.status != "provisional-owner-review"
    )
    status_ok = (
        any(fit.status == "provisional-owner-review" for fit in fits)
        and failed_weight <= request.maximum_failed_morphology_weight
    )
    morphology_ids = tuple(dict.fromkeys(fit.sample_morphologies[0] for fit in fits))
    association_ids = tuple(dict.fromkeys(fit.sample_associations[0] for fit in fits))
    morphology_weights = {
        name: float(
            sum(
                weight
                for weight, fit in zip(model_weights, fits, strict=True)
                if fit.sample_morphologies[0] == name
            )
        )
        for name in morphology_ids
    }
    association_weights = {
        name: float(
            sum(
                weight
                for weight, fit in zip(model_weights, fits, strict=True)
                if fit.sample_associations[0] == name
            )
        )
        for name in association_ids
    }
    return JointFitResult(
        status="provisional-owner-review" if status_ok else "failed-inference",
        shared_dm=dm_summary,
        component_toas=component_toas,
        parameter_names=union_names,
        parameter_units=_parameter_units(union_names),
        samples=samples,
        weights=weights,
        sample_morphologies=np.concatenate(
            [
                np.full(fit.samples.shape[0], fit.sample_morphologies[0])
                for fit in fits
            ]
        ),
        sample_associations=np.concatenate(
            [fit.sample_associations for fit in fits]
        ),
        log_evidence=float(logsumexp(log_evidences) - math.log(len(fits))),
        log_evidence_uncertainty=float(
            math.sqrt(
                sum(
                    (weight * fit.log_evidence_uncertainty) ** 2
                    for weight, fit in zip(model_weights, fits, strict=True)
                )
            )
        ),
        maximum_not_on_boundary=status_ok,
        prior_edge_mass_by_parameter=edge_mass,
        morphology_weights=morphology_weights,
        morphology_statuses={
            morphology: (
                "provisional-owner-review"
                if any(
                    fit.status == "provisional-owner-review"
                    for fit in fits
                    if fit.sample_morphologies[0] == morphology
                )
                else "failed-inference"
            )
            for morphology in morphology_ids
        },
        morphology_log_evidences={
            morphology: float(
                logsumexp(
                    [
                        fit.log_evidence
                        for fit in fits
                        if fit.sample_morphologies[0] == morphology
                    ]
                )
                - math.log(
                    sum(
                        fit.sample_morphologies[0] == morphology
                        for fit in fits
                    )
                )
            )
            for morphology in morphology_ids
        },
        morphology_log_evidence_uncertainties={
            morphology: max(
                fit.log_evidence_uncertainty
                for fit in fits
                if fit.sample_morphologies[0] == morphology
            )
            for morphology in morphology_ids
        },
        morphology_maximum_prior_edge_mass={
            morphology: max(
                max(fit.prior_edge_mass_by_parameter.values())
                for fit in fits
                if fit.sample_morphologies[0] == morphology
            )
            for morphology in morphology_ids
        },
        association_weights=association_weights,
        model_by_instrument=models,
        residual_by_instrument=residuals,
    )


def fit_joint_event(request: JointFitRequest) -> JointFitResult:
    """Fit every association-morphology combination and mix by evidence."""

    request.validate()
    if isinstance(request.morphology, str) and len(request.associations) == 1:
        return _fit_one_morphology(request)
    morphologies = (
        (request.morphology,)
        if isinstance(request.morphology, str)
        else request.morphology
    )
    fits = [
        _fit_one_morphology(
            replace(request, associations=(association,), morphology=morphology)
        )
        for association in request.associations
        for morphology in morphologies
    ]
    return _mixture_result(request, fits)
