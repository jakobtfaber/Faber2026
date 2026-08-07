"""Geometry-constrained joint CHIME/FRB and DSA-110 burst inference.

The public interface is :func:`fit_joint_event`. Callers provide two independent
``BandObservation`` objects plus the geometry and component hypotheses. The
implementation never stitches grids and never changes either observation.

Timing convention
-----------------
``ComponentWindow`` locates an observed component in its own product. A matched
CHIME/FRB--DSA-110 pair is replaced by one latent, unscattered geocentric arrival
time at 400 MHz. For instrument ``i`` and channel frequency ``nu`` the modeled
center is

    t_geo,400 + site_delay_i + clock_error_i
      + K_DM * (DM_absolute - DM_product,i) * (nu^-2 - 400^-2).

Thus the input product DM is a coordinate, not a second fitted DM. Unmatched
components retain band-local arrival times and cannot constrain geometry.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import math
import multiprocessing
import re
import sys
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray
from scipy.special import ndtri

from ._pulse_kernels import (
    gaussian_density,
    gaussian_exponential_density,
)

REFERENCE_FREQUENCY_MHZ = 400.0
K_DM_S_MHZ2 = 4148.808
_DM_IDENTITY_ATOL = 1.0e-9
_RESPONSE_NODE = np.array([-math.sqrt(3.0 / 5.0), 0.0, math.sqrt(3.0 / 5.0)])
_RESPONSE_WEIGHT = np.array([5.0, 8.0, 5.0]) / 18.0

Instrument = Literal["chime", "dsa"]
Morphology = Literal["gaussian", "scattering"]


@dataclass(frozen=True, slots=True)
class DispersionState:
    """Exactly-once dispersion accounting for one intensity product."""

    input_dm_pc_cm3: float
    coherent_correction_pc_cm3: float
    incoherent_correction_pc_cm3: float
    product_dm_pc_cm3: float
    mode: str

    def __post_init__(self) -> None:
        expected = (
            float(self.input_dm_pc_cm3)
            + float(self.coherent_correction_pc_cm3)
            + float(self.incoherent_correction_pc_cm3)
        )
        if not np.isclose(
            expected,
            float(self.product_dm_pc_cm3),
            rtol=0.0,
            atol=_DM_IDENTITY_ATOL,
        ):
            raise ValueError(
                "dispersion identity failed: input + coherent + incoherent must equal product DM"
            )
        if not self.mode:
            raise ValueError("dispersion mode is required")


@dataclass(slots=True)
class BandObservation:
    """One instrument's immutable fitting data on its own native grid."""

    instrument: Instrument
    waterfall: NDArray[np.floating]
    valid: NDArray[np.bool_]
    frequency_mhz: NDArray[np.floating]
    channel_width_mhz: NDArray[np.floating]
    noise_std: NDArray[np.floating]
    sample_interval_s: float
    time0_unix_ns: int
    reference_frequency_mhz: float
    dispersion: DispersionState
    input_sha256: dict[str, str] = field(default_factory=dict)
    _gain_whitened_data: NDArray[np.floating] = field(init=False, repr=False)
    _gain_inverse_noise: NDArray[np.floating] = field(init=False, repr=False)
    _gain_data_quadratic: NDArray[np.floating] = field(init=False, repr=False)
    _gain_log_constant: NDArray[np.floating] = field(init=False, repr=False)
    _kernel_time_s: NDArray[np.floating] = field(init=False, repr=False)
    _kernel_frequency_mhz: NDArray[np.floating] = field(init=False, repr=False)
    _kernel_dispersion_basis_s: NDArray[np.floating] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.waterfall = np.asarray(self.waterfall, dtype=float)
        self.valid = np.asarray(self.valid, dtype=bool)
        self.frequency_mhz = np.asarray(self.frequency_mhz, dtype=float)
        widths = np.asarray(self.channel_width_mhz, dtype=float)
        noise = np.asarray(self.noise_std, dtype=float)
        if self.instrument not in {"chime", "dsa"}:
            raise ValueError(f"unsupported instrument: {self.instrument!r}")
        if self.waterfall.ndim != 2:
            raise ValueError("waterfall must have shape (frequency, time)")
        if self.valid.shape != self.waterfall.shape:
            raise ValueError("valid mask must match the waterfall")
        nfreq = self.waterfall.shape[0]
        if self.frequency_mhz.shape != (nfreq,):
            raise ValueError("frequency_mhz must contain one center per row")
        if widths.ndim == 0:
            widths = np.full(nfreq, float(widths))
        if widths.shape != (nfreq,) or np.any(widths <= 0):
            raise ValueError("channel_width_mhz must be positive per row")
        if noise.ndim == 1:
            if noise.shape != (nfreq,):
                raise ValueError("row noise must contain one value per row")
            noise = np.broadcast_to(noise[:, None], self.waterfall.shape).copy()
        if noise.shape != self.waterfall.shape:
            raise ValueError("noise_std must be per-row or per-pixel")
        if not np.isclose(
            self.reference_frequency_mhz,
            REFERENCE_FREQUENCY_MHZ,
            rtol=0.0,
            atol=0.0,
        ):
            raise ValueError("joint timing requires a 400 MHz reference")
        if self.sample_interval_s <= 0:
            raise ValueError("sample_interval_s must be positive")
        if np.any(~np.isfinite(self.frequency_mhz)) or np.any(self.frequency_mhz <= 0):
            raise ValueError("frequency centers must be finite and positive")
        if not np.any(self.valid):
            raise ValueError("observation has no valid pixels")
        if np.any(~np.isfinite(self.waterfall[self.valid])):
            raise ValueError("valid waterfall pixels must be finite")
        if np.any(~np.isfinite(noise[self.valid])) or np.any(noise[self.valid] <= 0):
            raise ValueError("valid pixels require finite positive noise")
        self.channel_width_mhz = widths
        self.noise_std = noise
        safe_noise = np.where(self.valid, noise, 1.0)
        self._gain_whitened_data = np.where(
            self.valid, self.waterfall / safe_noise, 0.0
        )
        self._gain_inverse_noise = np.where(self.valid, 1.0 / safe_noise, 0.0)
        self._gain_data_quadratic = np.einsum(
            "ft,ft->f", self._gain_whitened_data, self._gain_whitened_data
        )
        self._gain_log_constant = (
            -0.5 * self.valid.sum(axis=1) * math.log(2.0 * math.pi)
            - np.where(self.valid, np.log(safe_noise), 0.0).sum(axis=1)
        )
        self._kernel_time_s = np.arange(self.waterfall.shape[1], dtype=float) * float(
            self.sample_interval_s
        )
        self._kernel_frequency_mhz = (
            self.frequency_mhz[:, None]
            + 0.5 * self.channel_width_mhz[:, None] * _RESPONSE_NODE
        )
        self._kernel_dispersion_basis_s = K_DM_S_MHZ2 * (
            self._kernel_frequency_mhz**-2 - REFERENCE_FREQUENCY_MHZ**-2
        )
        # The gain and kernel terms above are precomputed from these arrays;
        # freeze them so later mutation cannot desynchronize the cached terms.
        for array in (
            self.waterfall,
            self.valid,
            self.frequency_mhz,
            self.channel_width_mhz,
            self.noise_std,
        ):
            array.setflags(write=False)

    @property
    def time_s(self) -> NDArray[np.floating]:
        return self._kernel_time_s


@dataclass(frozen=True, slots=True)
class GeometryConstraint:
    """Per-site geometric timing relative to the terrestrial geocenter."""

    epoch_unix_ns: int
    source_icrs: str
    site_delay_s: dict[str, float]
    site_delay_sigma_s: dict[str, float]
    clock_sigma_s: dict[str, float]
    projection_disagreement_s: float
    reference_frequency_mhz: float = REFERENCE_FREQUENCY_MHZ

    def __post_init__(self) -> None:
        if not np.isclose(
            self.reference_frequency_mhz,
            REFERENCE_FREQUENCY_MHZ,
            rtol=0.0,
            atol=0.0,
        ):
            raise ValueError("geometry constraint must use 400 MHz")
        for instrument in ("chime", "dsa"):
            if instrument not in self.site_delay_s:
                raise ValueError(f"missing {instrument} site delay")
            if instrument not in self.site_delay_sigma_s:
                raise ValueError(f"missing {instrument} geometric uncertainty")
            if instrument not in self.clock_sigma_s:
                raise ValueError(f"missing {instrument} clock uncertainty")
            combined = math.hypot(
                float(self.site_delay_sigma_s[instrument]),
                float(self.clock_sigma_s[instrument]),
            )
            if not np.isfinite(combined) or combined <= 0:
                raise ValueError(f"{instrument} needs a positive geometric/clock uncertainty")
        if not self.source_icrs:
            raise ValueError("source localization is required")
        if not np.isfinite(self.projection_disagreement_s):
            raise ValueError("projection disagreement must be finite")


@dataclass(frozen=True, slots=True)
class ComponentWindow:
    """Reviewed component support in one observation."""

    instrument: Instrument
    component_id: str
    center_sample: float
    half_width_samples: float
    width_bounds_s: tuple[float, float]
    width_index_bounds: tuple[float, float] = (-2.0, 2.0)

    def __post_init__(self) -> None:
        if self.instrument not in {"chime", "dsa"}:
            raise ValueError("component instrument must be chime or dsa")
        if not self.component_id:
            raise ValueError("component_id is required")
        if self.half_width_samples <= 0:
            raise ValueError("component time window must be positive")
        if not (0 < self.width_bounds_s[0] < self.width_bounds_s[1]):
            raise ValueError("component width bounds must be positive and ordered")
        if not self.width_index_bounds[0] < self.width_index_bounds[1]:
            raise ValueError("width-index bounds must be ordered")


@dataclass(frozen=True, slots=True)
class ComponentMatch:
    """One physical component represented in both observations."""

    latent_id: str
    chime_component_id: str
    dsa_component_id: str


@dataclass(frozen=True, slots=True)
class AssociationHypothesis:
    """A reviewed, one-to-one, order-preserving component mapping."""

    name: str
    matches: tuple[ComponentMatch, ...]

    def __post_init__(self) -> None:
        if not self.name or not self.matches:
            raise ValueError("association hypothesis needs a name and a match")
        for attribute in (
            "latent_id",
            "chime_component_id",
            "dsa_component_id",
        ):
            values = [getattr(match, attribute) for match in self.matches]
            if len(values) != len(set(values)):
                raise ValueError(f"association {attribute} values must be unique")


@dataclass(frozen=True, slots=True)
class FitSettings:
    """Priors, morphology ladder, and deterministic sampler controls."""

    dm_bounds_pc_cm3: tuple[float, float]
    morphologies: tuple[Morphology, ...] = ("gaussian", "scattering")
    scattering_tau_1ghz_bounds_s: tuple[float, float] = (1.0e-6, 5.0e-3)
    scattering_alpha_bounds: tuple[float, float] = (2.0, 6.0)
    gain_variance: float = 100.0
    seed: int = 0
    nlive: int = 600
    dlogz: float = 0.5
    sample: str = "rwalk"
    pool_size: int = 1
    checkpoint_dir: str | None = None
    resume: bool = False
    maximum_projection_disagreement_s: float = 5.0e-7
    maximum_reduced_residual_power: float = 2.0
    maximum_structured_residual_correlation: float = 0.2
    posterior_edge_fraction: float = 0.01
    maximum_prior_edge_mass: float = 0.05

    def __post_init__(self) -> None:
        if not self.dm_bounds_pc_cm3[0] < self.dm_bounds_pc_cm3[1]:
            raise ValueError("DM bounds must be ordered")
        if not self.morphologies or any(
            family not in {"gaussian", "scattering"} for family in self.morphologies
        ):
            raise ValueError("unknown or empty morphology ladder")
        if not (0 < self.scattering_tau_1ghz_bounds_s[0] < self.scattering_tau_1ghz_bounds_s[1]):
            raise ValueError("scattering-time bounds must be positive and ordered")
        if not (self.scattering_alpha_bounds[0] < self.scattering_alpha_bounds[1]):
            raise ValueError("scattering-index bounds must be ordered")
        if self.gain_variance <= 0 or self.nlive < 20 or self.dlogz <= 0:
            raise ValueError("invalid gain or sampler settings")
        if self.pool_size < 1:
            raise ValueError("pool_size must be positive")
        if self.resume and self.checkpoint_dir is None:
            raise ValueError("resume requires checkpoint_dir")
        if not 0 < self.posterior_edge_fraction < 0.5:
            raise ValueError("posterior edge fraction must lie between zero and 0.5")
        if not 0 < self.maximum_prior_edge_mass < 0.5:
            raise ValueError("prior-edge mass threshold must lie between zero and 0.5")
        if self.maximum_reduced_residual_power <= 0:
            raise ValueError("model-adequacy threshold must be positive")
        if not 0 < self.maximum_structured_residual_correlation < 1:
            raise ValueError("structured-residual threshold must lie between zero and one")


@dataclass(frozen=True, slots=True)
class JointFitRequest:
    """Complete, hashable-in-spirit input to the joint fitting interface."""

    observations: tuple[BandObservation, BandObservation]
    geometry: GeometryConstraint
    components: tuple[ComponentWindow, ...]
    associations: tuple[AssociationHypothesis, ...]
    settings: FitSettings

    def __post_init__(self) -> None:
        if len(self.observations) != 2:
            raise ValueError("request requires exactly two observations")
        by_instrument = {observation.instrument for observation in self.observations}
        if by_instrument != {"chime", "dsa"}:
            raise ValueError("request requires exactly one CHIME and one DSA observation")
        if not self.components or not self.associations:
            raise ValueError("components and association hypotheses are required")
        known = {(component.instrument, component.component_id) for component in self.components}
        if len(known) != len(self.components):
            raise ValueError("component identifiers must be unique per instrument")
        for component in self.components:
            observation = _observation_by_instrument(self, component.instrument)
            if (
                not np.isfinite(component.center_sample)
                or component.center_sample - component.half_width_samples < 0
                or component.center_sample + component.half_width_samples
                > observation.waterfall.shape[1]
            ):
                raise ValueError("component window extends beyond its locked crop")
        for hypothesis in self.associations:
            chime_order = []
            dsa_order = []
            for match in hypothesis.matches:
                if ("chime", match.chime_component_id) not in known:
                    raise ValueError("association names an unknown CHIME component")
                if ("dsa", match.dsa_component_id) not in known:
                    raise ValueError("association names an unknown DSA component")
                chime_order.append(
                    _component_index(self.components, "chime", match.chime_component_id)
                )
                dsa_order.append(_component_index(self.components, "dsa", match.dsa_component_id))
            if chime_order != sorted(chime_order) or dsa_order != sorted(dsa_order):
                raise ValueError("component associations must preserve time order")
        latent_sets = [
            {match.latent_id for match in hypothesis.matches} for hypothesis in self.associations
        ]
        names = [hypothesis.name for hypothesis in self.associations]
        if len(names) != len(set(names)):
            raise ValueError("association hypothesis names must be unique")
        if any(values != latent_sets[0] for values in latent_sets[1:]):
            raise ValueError("every association must preserve the same latent component IDs")
        if (
            abs(self.geometry.projection_disagreement_s)
            > self.settings.maximum_projection_disagreement_s
        ):
            raise ValueError("independent geometric projections disagree")


@dataclass(slots=True)
class HypothesisFit:
    morphology: Morphology
    association: str
    parameter_names: tuple[str, ...]
    samples: NDArray[np.floating]
    sample_weights: NDArray[np.floating]
    log_evidence: float
    log_evidence_error: float
    diagnostics: dict[str, Any]


@dataclass(slots=True)
class JointFitResult:
    """Posterior runs plus evidence-weighted formal summaries."""

    runs: tuple[HypothesisFit, ...]
    run_weights: NDArray[np.floating]
    dm_pc_cm3: dict[str, float]
    geocentric_toa_unix_ns: dict[str, dict[str, float]]
    topocentric_toa_unix_ns: dict[str, dict[str, dict[str, float]]]
    model_products: dict[str, NDArray[np.floating]]
    status: str
    diagnostics: dict[str, Any]


@dataclass(frozen=True, slots=True)
class _Parameter:
    name: str
    kind: Literal["uniform", "log_uniform", "normal"]
    low: float
    high: float


@dataclass(frozen=True, slots=True)
class _RunLayout:
    parameters: tuple[_Parameter, ...]
    component_parameter_names: dict[tuple[str, str], tuple[str, str, str]]
    matched_toa_names: dict[str, str]
    timing_error_names: dict[str, str]


@dataclass(frozen=True, slots=True)
class _LogLikelihoodCallable:
    request: JointFitRequest
    layout: _RunLayout
    morphology: Morphology

    def __call__(self, theta: NDArray[np.floating]) -> float:
        return _log_likelihood(theta, self.request, self.layout, self.morphology)


@dataclass(frozen=True, slots=True)
class _PriorTransformCallable:
    layout: _RunLayout

    def __call__(self, unit: NDArray[np.floating]) -> NDArray[np.floating]:
        return _prior_transform(unit, self.layout)


def _component_index(
    components: tuple[ComponentWindow, ...],
    instrument: Instrument,
    component_id: str,
) -> int:
    ordered = sorted(
        (component for component in components if component.instrument == instrument),
        key=lambda component: component.center_sample,
    )
    return next(
        index for index, component in enumerate(ordered) if component.component_id == component_id
    )


def _observation_by_instrument(request: JointFitRequest, instrument: Instrument) -> BandObservation:
    return next(
        observation for observation in request.observations if observation.instrument == instrument
    )


def _component_by_key(
    request: JointFitRequest, instrument: Instrument, component_id: str
) -> ComponentWindow:
    return next(
        component
        for component in request.components
        if component.instrument == instrument and component.component_id == component_id
    )


def _component_geocentric_bounds(
    request: JointFitRequest, component: ComponentWindow
) -> tuple[float, float]:
    observation = _observation_by_instrument(request, component.instrument)
    center = (
        (observation.time0_unix_ns - request.geometry.epoch_unix_ns) * 1.0e-9
        + component.center_sample * observation.sample_interval_s
        - float(request.geometry.site_delay_s[component.instrument])
    )
    half_width = component.half_width_samples * observation.sample_interval_s
    return center - half_width, center + half_width


def _component_topocentric_bounds(
    request: JointFitRequest, component: ComponentWindow
) -> tuple[float, float]:
    observation = _observation_by_instrument(request, component.instrument)
    center = (
        observation.time0_unix_ns - request.geometry.epoch_unix_ns
    ) * 1.0e-9 + component.center_sample * observation.sample_interval_s
    half_width = component.half_width_samples * observation.sample_interval_s
    return center - half_width, center + half_width


def _intersect(left: tuple[float, float], right: tuple[float, float]) -> tuple[float, float]:
    bounds = max(left[0], right[0]), min(left[1], right[1])
    if not bounds[0] < bounds[1]:
        raise ValueError("matched component ToA windows do not overlap in geocentric time")
    return bounds


def _layout(
    request: JointFitRequest,
    hypothesis: AssociationHypothesis,
    morphology: Morphology,
) -> _RunLayout:
    parameters: list[_Parameter] = [
        _Parameter(
            "absolute_dm_pc_cm3",
            "uniform",
            *request.settings.dm_bounds_pc_cm3,
        )
    ]
    component_names: dict[tuple[str, str], tuple[str, str, str]] = {}
    matched_toa_names: dict[str, str] = {}
    matched_keys: set[tuple[str, str]] = set()
    for match in hypothesis.matches:
        chime = _component_by_key(request, "chime", match.chime_component_id)
        dsa = _component_by_key(request, "dsa", match.dsa_component_id)
        toa_name = f"toa_{match.latent_id}_s"
        width_name = f"width_{match.latent_id}_s"
        index_name = f"width_index_{match.latent_id}"
        toa_bounds = _intersect(
            _component_geocentric_bounds(request, chime),
            _component_geocentric_bounds(request, dsa),
        )
        width_bounds = (
            max(chime.width_bounds_s[0], dsa.width_bounds_s[0]),
            min(chime.width_bounds_s[1], dsa.width_bounds_s[1]),
        )
        if not width_bounds[0] < width_bounds[1]:
            raise ValueError("matched component width priors do not overlap")
        index_bounds = (
            max(chime.width_index_bounds[0], dsa.width_index_bounds[0]),
            min(chime.width_index_bounds[1], dsa.width_index_bounds[1]),
        )
        if not index_bounds[0] < index_bounds[1]:
            raise ValueError("matched component width-index priors do not overlap")
        parameters.extend(
            (
                _Parameter(toa_name, "uniform", *toa_bounds),
                _Parameter(width_name, "log_uniform", *width_bounds),
                _Parameter(index_name, "uniform", *index_bounds),
            )
        )
        names = toa_name, width_name, index_name
        component_names[("chime", chime.component_id)] = names
        component_names[("dsa", dsa.component_id)] = names
        matched_toa_names[match.latent_id] = toa_name
        matched_keys.update((("chime", chime.component_id), ("dsa", dsa.component_id)))

    for component in request.components:
        key = component.instrument, component.component_id
        if key in matched_keys:
            continue
        stem = f"{component.instrument}_{component.component_id}"
        toa_name = f"local_toa_{stem}_s"
        width_name = f"width_{stem}_s"
        index_name = f"width_index_{stem}"
        parameters.extend(
            (
                _Parameter(
                    toa_name,
                    "uniform",
                    *_component_topocentric_bounds(request, component),
                ),
                _Parameter(
                    width_name,
                    "log_uniform",
                    *component.width_bounds_s,
                ),
                _Parameter(
                    index_name,
                    "uniform",
                    *component.width_index_bounds,
                ),
            )
        )
        component_names[key] = toa_name, width_name, index_name

    timing_names: dict[str, str] = {}
    for instrument in ("chime", "dsa"):
        sigma = math.hypot(
            request.geometry.site_delay_sigma_s[instrument],
            request.geometry.clock_sigma_s[instrument],
        )
        name = f"timing_error_{instrument}_s"
        parameters.append(_Parameter(name, "normal", 0.0, sigma))
        timing_names[instrument] = name

    if morphology == "scattering":
        parameters.extend(
            (
                _Parameter(
                    "tau_1ghz_s",
                    "log_uniform",
                    *request.settings.scattering_tau_1ghz_bounds_s,
                ),
                _Parameter(
                    "scattering_alpha",
                    "uniform",
                    *request.settings.scattering_alpha_bounds,
                ),
            )
        )
    return _RunLayout(
        tuple(parameters),
        component_names,
        matched_toa_names,
        timing_names,
    )


def _prior_transform(unit: NDArray[np.floating], layout: _RunLayout) -> NDArray[np.floating]:
    output = np.empty(len(layout.parameters), dtype=float)
    for index, (value, parameter) in enumerate(zip(unit, layout.parameters, strict=True)):
        clipped = float(np.clip(value, 1.0e-12, 1.0 - 1.0e-12))
        if parameter.kind == "uniform":
            output[index] = parameter.low + clipped * (parameter.high - parameter.low)
        elif parameter.kind == "log_uniform":
            output[index] = math.exp(
                math.log(parameter.low)
                + clipped * (math.log(parameter.high) - math.log(parameter.low))
            )
        else:
            output[index] = parameter.low + parameter.high * float(ndtri(clipped))
    return output


def _values(theta: NDArray[np.floating], layout: _RunLayout) -> dict[str, float]:
    return {
        parameter.name: float(value)
        for parameter, value in zip(layout.parameters, theta, strict=True)
    }


def _component_kernels(
    request: JointFitRequest,
    observation: BandObservation,
    layout: _RunLayout,
    values: dict[str, float],
    morphology: Morphology,
) -> NDArray[np.floating]:
    relative_time = (
        observation.time0_unix_ns - request.geometry.epoch_unix_ns
    ) * 1.0e-9 + observation._kernel_time_s
    evaluation_frequency = observation._kernel_frequency_mhz
    residual_dm = values["absolute_dm_pc_cm3"] - observation.dispersion.product_dm_pc_cm3
    dispersion_delay = residual_dm * observation._kernel_dispersion_basis_s
    timing_error = values[layout.timing_error_names[observation.instrument]]
    kernels = []
    ordered = sorted(
        (
            component
            for component in request.components
            if component.instrument == observation.instrument
        ),
        key=lambda component: component.center_sample,
    )
    for component in ordered:
        toa_name, width_name, index_name = layout.component_parameter_names[
            (component.instrument, component.component_id)
        ]
        matched = toa_name.startswith("toa_")
        if matched:
            center_400 = (
                values[toa_name]
                + request.geometry.site_delay_s[observation.instrument]
                + timing_error
            )
        else:
            # This nuisance ToA is expressed in the same relative epoch but does
            # not use geometry and therefore cannot constrain the station delay.
            center_400 = values[toa_name]
        center = center_400 + dispersion_delay
        width = (
            values[width_name]
            * (evaluation_frequency / REFERENCE_FREQUENCY_MHZ) ** values[index_name]
        )
        if morphology == "scattering":
            tau = values["tau_1ghz_s"] * (evaluation_frequency / 1000.0) ** (
                -values["scattering_alpha"]
            )
            evaluated = gaussian_exponential_density(
                relative_time,
                center.reshape(-1),
                width.reshape(-1),
                tau.reshape(-1),
            )
            evaluated = evaluated.reshape(
                observation.waterfall.shape[0],
                _RESPONSE_WEIGHT.size,
                relative_time.size,
            )
            kernel = (
                _RESPONSE_WEIGHT[0] * evaluated[:, 0]
                + _RESPONSE_WEIGHT[1] * evaluated[:, 1]
                + _RESPONSE_WEIGHT[2] * evaluated[:, 2]
            )
        else:
            kernel = np.zeros(
                (observation.waterfall.shape[0], relative_time.size), dtype=float
            )
            for node_index, weight in enumerate(_RESPONSE_WEIGHT):
                kernel += weight * gaussian_density(
                    relative_time,
                    center[:, node_index],
                    width[:, node_index],
                )
        kernels.append(kernel)
    return np.asarray(kernels, dtype=float)


def _gain_marginal_band(
    observation: BandObservation,
    kernels: NDArray[np.floating],
    gain_variance: float,
    *,
    return_model: bool = False,
) -> tuple[float, NDArray[np.floating] | None]:
    """Integrate channel/component gains under a fixed proper Gaussian prior."""

    ncomponent, nfrequency, _ = kernels.shape
    if ncomponent == 1:
        whitened_design = kernels[0] * observation._gain_inverse_noise
        gram = np.einsum("ft,ft->f", whitened_design, whitened_design)
        projection = np.einsum(
            "ft,ft->f", whitened_design, observation._gain_whitened_data
        )
        precision = gram + 1.0 / gain_variance
        if np.any(~np.isfinite(precision)) or np.any(precision <= 0):
            return -np.inf, None
        gains = projection / precision
        logdet = np.log1p(gain_variance * gram)
        if np.any(~np.isfinite(logdet)):
            return -np.inf, None
        quadratic = observation._gain_data_quadratic - projection * gains
        log_evidence = np.sum(
            -0.5 * quadratic - 0.5 * logdet + observation._gain_log_constant
        )
        if not return_model:
            return float(log_evidence), None
        model = np.full(observation.waterfall.shape, np.nan, dtype=float)
        evaluated = kernels[0] * gains[:, None]
        model[observation.valid] = evaluated[observation.valid]
        return float(log_evidence), model

    log_evidence = 0.0
    model = np.full(observation.waterfall.shape, np.nan, dtype=float)
    identity = np.eye(ncomponent)
    for row in range(nfrequency):
        use = observation.valid[row]
        if not np.any(use):
            continue
        data = observation.waterfall[row, use]
        noise = observation.noise_std[row, use]
        design = kernels[:, row, use].T
        whitened_data = data / noise
        whitened_design = design / noise[:, None]
        gram = whitened_design.T @ whitened_design
        projection = whitened_design.T @ whitened_data
        precision = gram + identity / gain_variance
        try:
            gains = np.linalg.solve(precision, projection)
        except np.linalg.LinAlgError:
            return -np.inf, None
        sign, logdet = np.linalg.slogdet(identity + gain_variance * gram)
        if sign <= 0:
            return -np.inf, None
        quadratic = float(whitened_data @ whitened_data - projection @ gains)
        log_evidence += (
            -0.5 * quadratic
            - 0.5 * float(logdet)
            - 0.5 * use.sum() * math.log(2.0 * math.pi)
            - float(np.log(noise).sum())
        )
        if return_model:
            model[row, use] = design @ gains
    return float(log_evidence), model if return_model else None


def _log_likelihood(
    theta: NDArray[np.floating],
    request: JointFitRequest,
    layout: _RunLayout,
    morphology: Morphology,
) -> float:
    values = _values(theta, layout)
    total = 0.0
    for observation in request.observations:
        kernels = _component_kernels(request, observation, layout, values, morphology)
        value, _ = _gain_marginal_band(
            observation,
            kernels,
            request.settings.gain_variance,
        )
        if not np.isfinite(value):
            return -1.0e300
        total += value
    return float(total)


def _weighted_quantiles(
    values: NDArray[np.floating],
    weights: NDArray[np.floating],
    quantiles: tuple[float, ...] = (0.16, 0.5, 0.84),
) -> NDArray[np.floating]:
    order = np.argsort(values)
    sorted_values = np.asarray(values)[order]
    sorted_weights = np.asarray(weights)[order]
    cumulative = np.cumsum(sorted_weights)
    cumulative /= cumulative[-1]
    return np.interp(quantiles, cumulative, sorted_values)


def _representative_diagnostics(
    request: JointFitRequest,
    run: HypothesisFit,
    layout: _RunLayout,
) -> dict[str, Any]:
    median = np.array(
        [
            _weighted_quantiles(run.samples[:, index], run.sample_weights)[1]
            for index in range(run.samples.shape[1])
        ]
    )
    values = _values(median, layout)
    bands = {}
    for observation in request.observations:
        kernels = _component_kernels(request, observation, layout, values, run.morphology)
        _, model = _gain_marginal_band(
            observation,
            kernels,
            request.settings.gain_variance,
            return_model=True,
        )
        assert model is not None
        residual = (
            observation.waterfall[observation.valid] - model[observation.valid]
        ) / observation.noise_std[observation.valid]
        bands[observation.instrument] = {
            "valid_pixel_count": int(residual.size),
            "reduced_residual_power": float(np.mean(residual**2)),
            "residual_mean": float(np.mean(residual)),
            "structured_frequency_time_correlation": (
                _structured_residual_correlation(observation, residual)
            ),
        }
    prior_rail = []
    prior_edge_mass = {}
    for index, parameter in enumerate(layout.parameters):
        if parameter.kind == "normal":
            continue
        sample_values = run.samples[:, index]
        if parameter.kind == "log_uniform":
            position = (np.log(sample_values) - math.log(parameter.low)) / (
                math.log(parameter.high) - math.log(parameter.low)
            )
        else:
            position = (sample_values - parameter.low) / (parameter.high - parameter.low)
        edge = (position <= request.settings.posterior_edge_fraction) | (
            position >= 1.0 - request.settings.posterior_edge_fraction
        )
        mass = float(np.sum(run.sample_weights[edge]))
        prior_edge_mass[parameter.name] = mass
        if mass > request.settings.maximum_prior_edge_mass:
            prior_rail.append(parameter.name)
    return {
        "bands": bands,
        "prior_rail_parameters": prior_rail,
        "prior_edge_mass": prior_edge_mass,
    }


def _structured_residual_correlation(
    observation: BandObservation,
    whitened_valid_residual: NDArray[np.floating],
) -> float:
    """Measure diagonal frequency-time structure without fitting it away."""

    frequency = observation.frequency_mhz
    time = np.arange(observation.waterfall.shape[1], dtype=float)
    frequency = (frequency - np.mean(frequency)) / np.std(frequency)
    time = (time - np.mean(time)) / np.std(time)
    selected = (frequency[:, None] * time[None, :])[observation.valid]
    residual = np.asarray(whitened_valid_residual, dtype=float)
    if np.std(residual) == 0 or np.std(selected) == 0:
        return 0.0
    return float(np.corrcoef(residual, selected)[0, 1])


def _representative_models(
    request: JointFitRequest,
    run: HypothesisFit,
    layout: _RunLayout,
) -> dict[str, NDArray[np.floating]]:
    median = np.array(
        [
            _weighted_quantiles(run.samples[:, index], run.sample_weights)[1]
            for index in range(run.samples.shape[1])
        ]
    )
    values = _values(median, layout)
    products = {}
    for observation in request.observations:
        kernels = _component_kernels(request, observation, layout, values, run.morphology)
        _, model = _gain_marginal_band(
            observation,
            kernels,
            request.settings.gain_variance,
            return_model=True,
        )
        assert model is not None
        products[f"{observation.instrument}_model"] = model
        products[f"{observation.instrument}_residual"] = observation.waterfall - model
        products[f"{observation.instrument}_valid"] = observation.valid
    return products


def _checkpoint_identity(
    request: JointFitRequest,
    hypothesis: AssociationHypothesis,
    morphology: Morphology,
) -> str:
    """Bind a resumable sampler to data, model, code, priors, and seed."""

    digest = hashlib.sha256(Path(__file__).read_bytes())
    digest.update(Path(__file__).with_name("_pulse_kernels.py").read_bytes())

    def update_text(value: object) -> None:
        digest.update(repr(value).encode("utf-8"))
        digest.update(b"\0")

    for observation in sorted(request.observations, key=lambda item: item.instrument):
        update_text(
            (
                observation.instrument,
                observation.sample_interval_s,
                observation.time0_unix_ns,
                observation.reference_frequency_mhz,
                observation.dispersion,
                sorted(observation.input_sha256.items()),
            )
        )
        for array in (
            observation.waterfall,
            observation.valid,
            observation.frequency_mhz,
            observation.channel_width_mhz,
            observation.noise_std,
        ):
            contiguous = np.ascontiguousarray(array)
            update_text((contiguous.dtype.str, contiguous.shape))
            digest.update(contiguous.view(np.uint8))
    update_text(request.geometry)
    update_text(request.components)
    update_text(hypothesis)
    update_text(morphology)
    sampler_identity = tuple(
        (item.name, getattr(request.settings, item.name))
        for item in fields(request.settings)
        if item.name not in {"checkpoint_dir", "resume", "pool_size"}
    )
    update_text(sampler_identity)
    update_text(
        (
            sys.version,
            importlib.metadata.version("dynesty"),
            importlib.metadata.version("numpy"),
            importlib.metadata.version("scipy"),
        )
    )
    return digest.hexdigest()[:20]


def _fit_one(
    request: JointFitRequest,
    hypothesis: AssociationHypothesis,
    morphology: Morphology,
) -> HypothesisFit:
    try:
        from dynesty import NestedSampler
    except ImportError as exc:  # pragma: no cover - exercised by runtime preflight
        raise RuntimeError(
            "dynesty is required; run through the locked project environment"
        ) from exc

    layout = _layout(request, hypothesis, morphology)
    checkpoint = None
    if request.settings.checkpoint_dir is not None:
        safe_name = re.sub(
            r"[^a-zA-Z0-9_.-]+",
            "_",
            f"{morphology}-{hypothesis.name}",
        )
        identity = _checkpoint_identity(request, hypothesis, morphology)
        checkpoint = Path(request.settings.checkpoint_dir) / f"{safe_name}-{identity}.save"
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
    pool = None
    try:
        if request.settings.pool_size > 1:
            context = multiprocessing.get_context("spawn")
            pool = context.Pool(request.settings.pool_size)
        restored = request.settings.resume and checkpoint is not None and checkpoint.is_file()
        if restored:
            sampler = NestedSampler.restore(str(checkpoint), pool=pool)
        else:
            sampler = NestedSampler(
                _LogLikelihoodCallable(request, layout, morphology),
                _PriorTransformCallable(layout),
                len(layout.parameters),
                nlive=request.settings.nlive,
                sample=request.settings.sample,
                rstate=np.random.default_rng(request.settings.seed),
                pool=pool,
                queue_size=request.settings.pool_size,
            )
        sampler.run_nested(
            dlogz=request.settings.dlogz,
            print_progress=False,
            checkpoint_file=str(checkpoint) if checkpoint is not None else None,
            resume=restored,
        )
    finally:
        if pool is not None:
            pool.close()
            pool.join()
    result = sampler.results
    log_weights = np.asarray(result.logwt, dtype=float) - float(result.logz[-1])
    sample_weights = np.exp(log_weights)
    sample_weights /= sample_weights.sum()
    fit = HypothesisFit(
        morphology=morphology,
        association=hypothesis.name,
        parameter_names=tuple(parameter.name for parameter in layout.parameters),
        samples=np.asarray(result.samples, dtype=float),
        sample_weights=sample_weights,
        log_evidence=float(result.logz[-1]),
        log_evidence_error=float(result.logzerr[-1]),
        diagnostics={},
    )
    fit.diagnostics = _representative_diagnostics(request, fit, layout)
    return fit


def _mixture_quantiles(
    runs: list[HypothesisFit],
    run_weights: NDArray[np.floating],
    parameter_name: str,
) -> dict[str, float]:
    values = []
    weights = []
    for run, run_weight in zip(runs, run_weights, strict=True):
        if parameter_name not in run.parameter_names:
            continue
        index = run.parameter_names.index(parameter_name)
        values.append(run.samples[:, index])
        weights.append(run.sample_weights * float(run_weight))
    if not values:
        raise ValueError(f"parameter absent from every run: {parameter_name}")
    combined_values = np.concatenate(values)
    combined_weights = np.concatenate(weights)
    combined_weights /= combined_weights.sum()
    lower, median, upper = _weighted_quantiles(combined_values, combined_weights)
    return {
        "median": float(median),
        "lower": float(lower),
        "upper": float(upper),
        "error_minus": float(median - lower),
        "error_plus": float(upper - median),
    }


def _mixture_derived_quantiles(
    runs: list[HypothesisFit],
    run_weights: NDArray[np.floating],
    parameter_names: tuple[str, ...],
    transform,
) -> dict[str, float]:
    values = []
    weights = []
    for run, run_weight in zip(runs, run_weights, strict=True):
        if any(name not in run.parameter_names for name in parameter_names):
            continue
        columns = [run.samples[:, run.parameter_names.index(name)] for name in parameter_names]
        values.append(np.asarray(transform(*columns), dtype=float))
        weights.append(run.sample_weights * float(run_weight))
    if not values:
        raise ValueError("derived posterior parameters are absent from every run")
    combined_values = np.concatenate(values)
    combined_weights = np.concatenate(weights)
    combined_weights /= combined_weights.sum()
    lower, median, upper = _weighted_quantiles(combined_values, combined_weights)
    return {
        "median": float(median),
        "lower": float(lower),
        "upper": float(upper),
        "error_minus": float(median - lower),
        "error_plus": float(upper - median),
    }


def _absolute_time_summary(relative: dict[str, float], epoch_unix_ns: int) -> dict[str, int]:
    return {
        "median": epoch_unix_ns + round(relative["median"] * 1.0e9),
        "lower": epoch_unix_ns + round(relative["lower"] * 1.0e9),
        "upper": epoch_unix_ns + round(relative["upper"] * 1.0e9),
        "error_minus_ns": round(relative["error_minus"] * 1.0e9),
        "error_plus_ns": round(relative["error_plus"] * 1.0e9),
    }


def _dm_toa_covariance(
    runs: list[HypothesisFit],
    run_weights: NDArray[np.floating],
    toa_parameter: str,
) -> dict[str, float]:
    dm_values = []
    toa_values = []
    weights = []
    for run, run_weight in zip(runs, run_weights, strict=True):
        if toa_parameter not in run.parameter_names:
            continue
        dm_values.append(run.samples[:, run.parameter_names.index("absolute_dm_pc_cm3")])
        toa_values.append(run.samples[:, run.parameter_names.index(toa_parameter)])
        weights.append(run.sample_weights * float(run_weight))
    dm = np.concatenate(dm_values)
    toa = np.concatenate(toa_values)
    weight = np.concatenate(weights)
    weight /= weight.sum()
    dm_centered = dm - np.sum(weight * dm)
    toa_centered = toa - np.sum(weight * toa)
    covariance = float(np.sum(weight * dm_centered * toa_centered))
    dm_variance = float(np.sum(weight * dm_centered**2))
    toa_variance = float(np.sum(weight * toa_centered**2))
    denominator = math.sqrt(dm_variance * toa_variance)
    correlation = covariance / denominator if denominator > 0 else 0.0
    return {
        "covariance_pc_cm3_s": covariance,
        "correlation": float(correlation),
    }


def _edge_status(summary: dict[str, float], bounds: tuple[float, float], fraction: float) -> bool:
    margin = fraction * (bounds[1] - bounds[0])
    return bool(summary["median"] <= bounds[0] + margin or summary["median"] >= bounds[1] - margin)


def _mixture_edge_mass(
    runs: list[HypothesisFit],
    run_weights: NDArray[np.floating],
    parameter_name: str,
    bounds: tuple[float, float],
    fraction: float,
) -> float:
    lower = bounds[0] + fraction * (bounds[1] - bounds[0])
    upper = bounds[1] - fraction * (bounds[1] - bounds[0])
    mass = 0.0
    for run, run_weight in zip(runs, run_weights, strict=True):
        index = run.parameter_names.index(parameter_name)
        at_edge = (run.samples[:, index] <= lower) | (run.samples[:, index] >= upper)
        mass += float(run_weight) * float(np.sum(run.sample_weights[at_edge]))
    return mass


def _plausible_runs(
    runs: list[HypothesisFit],
    selected_index: int,
) -> tuple[list[HypothesisFit], NDArray[np.floating]]:
    """Return every hypothesis that remains numerically plausible.

    For each run, its optimistic evidence is ``logZ + error`` while every
    competitor uses ``logZ - error``. The run remains plausible when its
    resulting normalized evidence weight exceeds float64 resolution. The
    point-estimate winner is always retained. This is numerical, not a
    scientific posterior-mass threshold.
    """

    log_evidence = np.asarray([run.log_evidence for run in runs], dtype=float)
    errors = np.asarray([run.log_evidence_error for run in runs], dtype=float)
    if np.any(~np.isfinite(log_evidence)):
        raise ValueError("log evidences must be finite")
    if np.any(~np.isfinite(errors)) or np.any(errors < 0):
        raise ValueError("log evidence errors must be finite and nonnegative")
    upper_weights = np.empty(len(runs), dtype=float)
    for index in range(len(runs)):
        shifted = log_evidence - errors
        shifted[index] = log_evidence[index] + errors[index]
        relative = shifted - np.max(shifted)
        weights = np.exp(relative)
        upper_weights[index] = weights[index] / weights.sum()
    resolution = np.finfo(float).eps
    plausible = [
        run
        for index, run in enumerate(runs)
        if index == selected_index or upper_weights[index] > resolution
    ]
    return plausible, upper_weights


def fit_joint_event(request: JointFitRequest) -> JointFitResult:
    """Fit every declared morphology/association and combine their evidence.

    No file I/O occurs here. Workflow adapters own product loading, provenance,
    checkpointing, and rendering.
    """

    runs = [
        _fit_one(request, hypothesis, morphology)
        for morphology in request.settings.morphologies
        for hypothesis in request.associations
    ]
    log_evidence = np.asarray([run.log_evidence for run in runs])
    relative = log_evidence - np.max(log_evidence)
    run_weights = np.exp(relative)
    run_weights /= run_weights.sum()
    dm = _mixture_quantiles(runs, run_weights, "absolute_dm_pc_cm3")
    latent_ids = sorted(
        {match.latent_id for hypothesis in request.associations for match in hypothesis.matches}
    )
    geocentric_toas = {}
    topocentric_toas = {}
    covariance = {}
    for latent_id in latent_ids:
        parameter = f"toa_{latent_id}_s"
        summary = _mixture_quantiles(runs, run_weights, parameter)
        geocentric_toas[latent_id] = _absolute_time_summary(summary, request.geometry.epoch_unix_ns)
        topocentric_toas[latent_id] = {}
        for instrument in ("chime", "dsa"):
            derived = _mixture_derived_quantiles(
                runs,
                run_weights,
                (parameter, f"timing_error_{instrument}_s"),
                lambda toa, error, instrument=instrument: (
                    toa + request.geometry.site_delay_s[instrument] + error
                ),
            )
            topocentric_toas[latent_id][instrument] = _absolute_time_summary(
                derived, request.geometry.epoch_unix_ns
            )
        covariance[latent_id] = _dm_toa_covariance(runs, run_weights, parameter)
    median_at_edge = _edge_status(
        dm,
        request.settings.dm_bounds_pc_cm3,
        request.settings.posterior_edge_fraction,
    )
    edge_mass = _mixture_edge_mass(
        runs,
        run_weights,
        "absolute_dm_pc_cm3",
        request.settings.dm_bounds_pc_cm3,
        request.settings.posterior_edge_fraction,
    )
    edge = median_at_edge or (edge_mass > request.settings.maximum_prior_edge_mass)
    diagnostics = {
        "posterior_dm_at_edge": edge,
        "posterior_dm_median_at_edge": median_at_edge,
        "posterior_dm_edge_mass": edge_mass,
        "run_weights": {
            f"{run.morphology}:{run.association}": float(weight)
            for run, weight in zip(runs, run_weights, strict=True)
        },
        "reference_frequency_mhz": REFERENCE_FREQUENCY_MHZ,
        "separate_native_grids": True,
        "independent_band_centroids_allowed": False,
        "dm_toa_covariance": covariance,
    }
    best_index = int(np.argmax(run_weights))
    best_run = runs[best_index]
    best_hypothesis = next(
        hypothesis for hypothesis in request.associations if hypothesis.name == best_run.association
    )
    best_layout = _layout(request, best_hypothesis, best_run.morphology)
    plausible_runs, plausible_upper_weights = _plausible_runs(
        runs,
        best_index,
    )
    maximum_residual_power = max(
        float(band["reduced_residual_power"])
        for run in plausible_runs
        for band in run.diagnostics["bands"].values()
    )
    maximum_structured_correlation = max(
        abs(float(band["structured_frequency_time_correlation"]))
        for run in plausible_runs
        for band in run.diagnostics["bands"].values()
    )
    model_adequate = (
        maximum_residual_power <= request.settings.maximum_reduced_residual_power
        and maximum_structured_correlation
        <= request.settings.maximum_structured_residual_correlation
    )
    prior_railed = sorted(
        {name for run in plausible_runs for name in run.diagnostics["prior_rail_parameters"]}
    )
    diagnostics.update(
        {
            "maximum_reduced_residual_power": maximum_residual_power,
            "maximum_structured_residual_correlation": (maximum_structured_correlation),
            "model_adequate": model_adequate,
            "prior_rail_parameters": prior_railed,
            "plausible_runs": [
                f"{run.morphology}:{run.association}" for run in plausible_runs
            ],
            "plausible_run_upper_weights": {
                f"{run.morphology}:{run.association}": float(weight)
                for run, weight in zip(runs, plausible_upper_weights, strict=True)
            },
            "plausible_run_weight_resolution": float(np.finfo(float).eps),
            "fixed_valid_pixel_masks": True,
        }
    )
    if edge:
        status = "failed_dm_edge"
    elif prior_railed:
        status = "failed_prior_rail"
    elif not model_adequate:
        status = "failed_model_inadequate"
    else:
        status = "provisional_pending_owner_approval"
    return JointFitResult(
        runs=tuple(runs),
        run_weights=run_weights,
        dm_pc_cm3=dm,
        geocentric_toa_unix_ns=geocentric_toas,
        topocentric_toa_unix_ns=topocentric_toas,
        model_products=_representative_models(request, best_run, best_layout),
        status=status,
        diagnostics=diagnostics,
    )
