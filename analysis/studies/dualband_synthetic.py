"""Deterministic synthetic observation generator for Wave 1 validation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.stats import exponnorm, norm

from faber2026.burst_models import (
    AssociationHypothesis,
    ComponentMatch,
    GeometryConstraint,
    JointFitRequest,
)
from faber2026.burst_models.kernels import (
    dispersion_delay_s,
    gaussian_power_law_density,
)
from faber2026.observations import BandObservation, DispersionState


@dataclass(frozen=True, slots=True)
class SyntheticEvent:
    request: JointFitRequest
    truth: dict[str, Any]


def _input_hash(specification: dict[str, Any], instrument: str) -> str:
    payload = json.dumps(
        {"specification": specification, "instrument": instrument},
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def build_synthetic_event(configuration: dict[str, Any]) -> SyntheticEvent:
    """Generate unlike grids on their declared native sampling grids."""

    synthetic = configuration["synthetic"]
    truth = synthetic["truth"]
    geometry_spec = configuration["geometry"]
    geometry = GeometryConstraint(
        reference_frequency_mhz=geometry_spec["reference_frequency_mhz"],
        epoch_unix_ns=geometry_spec["epoch_unix_ns"],
        station_delays_s=geometry_spec["station_delays_s"],
        station_delay_uncertainties_s=geometry_spec[
            "station_delay_uncertainties_s"
        ],
        clock_uncertainties_s=geometry_spec["clock_uncertainties_s"],
        independent_projection_difference_s=geometry_spec[
            "independent_projection_difference_s"
        ],
        maximum_projection_difference_s=geometry_spec[
            "maximum_projection_difference_s"
        ],
    )
    rng = np.random.default_rng(synthetic["noise_seed"])
    observations = []
    for instrument, grid in synthetic["grids"].items():
        frequencies = np.linspace(
            grid["frequency_low_mhz"],
            grid["frequency_high_mhz"],
            grid["frequency_channels"],
        )
        times = np.arange(grid["time_samples"], dtype=float) * grid["sample_interval_s"]
        product_dm = grid["product_dm"]
        origin_offset_s = grid["time_origin_offset_s"]
        channel_width = (
            grid["frequency_high_mhz"] - grid["frequency_low_mhz"]
        ) / frequencies.size
        frequency_nodes, frequency_weights = np.polynomial.legendre.leggauss(5)
        time_low = times - 0.5 * grid["sample_interval_s"]
        time_high = times + 0.5 * grid["sample_interval_s"]
        rows = []
        for frequency in frequencies:
            profile = np.zeros_like(times)
            for node, weight in zip(
                frequency_nodes, frequency_weights, strict=True
            ):
                subfrequency = frequency + 0.5 * channel_width * node
                center = (
                    truth["geocentric_toa_s"]
                    + geometry.station_delays_s[instrument]
                    - origin_offset_s
                    + dispersion_delay_s(
                        truth["absolute_dm"] - product_dm,
                        subfrequency,
                    )
                )
                width = truth["width_400_s"] * (
                    subfrequency / 400.0
                ) ** truth["width_index"]
                if synthetic["injected_morphology"] == "gaussian":
                    bin_mass = norm.cdf(time_high, loc=center, scale=width) - norm.cdf(
                        time_low, loc=center, scale=width
                    )
                elif synthetic["injected_morphology"] == "emg":
                    tau = truth["tau_1ghz_s"] * (
                        subfrequency / 1000.0
                    ) ** -4.0
                    shape = tau / width
                    bin_mass = exponnorm.cdf(
                        time_high, shape, loc=center, scale=width
                    ) - exponnorm.cdf(
                        time_low, shape, loc=center, scale=width
                    )
                else:
                    beta = truth["beta"]
                    alpha = 2.0 * beta / (beta - 2.0)
                    tau = truth["tau_1ghz_s"] * (
                        subfrequency / 1000.0
                    ) ** -alpha
                    bin_mass = (
                        gaussian_power_law_density(
                            times,
                            center_s=center,
                            sigma_s=width,
                            tau_s=tau,
                            beta=beta,
                        )
                        * grid["sample_interval_s"]
                    )
                profile += (
                    truth["matched_amplitudes"][instrument]
                    * 0.5
                    * weight
                    * bin_mass
                    / grid["sample_interval_s"]
                )
            for local in truth["local_components"].get(instrument, []):
                local_mass = norm.cdf(
                    time_high,
                    loc=local["toa_s"],
                    scale=local["width_s"],
                ) - norm.cdf(
                    time_low,
                    loc=local["toa_s"],
                    scale=local["width_s"],
                )
                profile += (
                    local["amplitude"]
                    * local_mass
                    / grid["sample_interval_s"]
                )
            rows.append(profile)
        noiseless = np.stack(rows)
        noise_std = np.full(frequencies.size, grid["noise_std"])
        intensity = noiseless + rng.normal(
            0.0, noise_std[:, None], size=noiseless.shape
        )
        observations.append(
            BandObservation(
                instrument=instrument,
                intensity=intensity,
                valid_pixels=np.ones_like(intensity, dtype=bool),
                frequencies_mhz=frequencies,
                channel_widths_mhz=np.full(
                    frequencies.size,
                    channel_width,
                ),
                times_s=times,
                sample_interval_s=grid["sample_interval_s"],
                time_origin_utc=grid["time_origin_utc"],
                time_origin_unix_ns=geometry.epoch_unix_ns
                + round(origin_offset_s * 1e9),
                frequency_frame="topocentric",
                dispersion=DispersionState(
                    voltage_dm=0.0,
                    coherent_delta_dm=product_dm,
                    residual_delta_dm=0.0,
                    product_dm=product_dm,
                    time_origin_correction_s=0.0,
                ),
                noise_std=noise_std,
                gain_prior_std=grid["gain_prior_std"],
                input_hashes={"synthetic": _input_hash(synthetic, instrument)},
            )
        )
    fit = configuration["fit"]
    request = JointFitRequest(
        observations=tuple(observations),
        geometry=geometry,
        component_ids=tuple(fit["component_ids"]),
        band_component_ids={
            instrument: tuple(identifiers)
            for instrument, identifiers in fit["band_component_ids"].items()
        },
        associations=tuple(
            AssociationHypothesis(
                association_id=association["association_id"],
                matches=tuple(
                    ComponentMatch(**match) for match in association["matches"]
                ),
            )
            for association in fit["associations"]
        ),
        morphology=tuple(fit["morphologies"]),
        dm_bounds=tuple(fit["dm_bounds"]),
        toa_bounds_s=tuple(tuple(item) for item in fit["toa_bounds_s"]),
        width_bounds_s=tuple(tuple(item) for item in fit["width_bounds_s"]),
        width_index_bounds=tuple(fit["width_index_bounds"]),
        scattering_tau_1ghz_bounds_s=tuple(fit["scattering_tau_1ghz_bounds_s"]),
        beta_bounds=tuple(fit["beta_bounds"]),
        seed=fit["seed"],
        nlive=fit["nlive"],
        dlogz=fit["dlogz"],
        maximum_failed_morphology_weight=fit[
            "maximum_failed_morphology_weight"
        ],
        component_amplitude_bounds=tuple(fit["component_amplitude_bounds"]),
    )
    request.validate()
    return SyntheticEvent(request=request, truth=dict(truth))
