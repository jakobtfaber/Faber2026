"""Truth tests for the permanent dual-band burst-model interface."""

from __future__ import annotations

import multiprocessing
from dataclasses import replace
from functools import partial

import numpy as np
import pytest
from astropy import units as u
from astropy.constants import c, e, eps0, m_e
from scipy.integrate import quad, trapezoid
from scipy.special import logsumexp
from scipy.stats import exponnorm

from faber2026.burst_models import (
    AssociationHypothesis,
    ComponentMatch,
    GeometryConstraint,
    JointFitRequest,
    JointFitResult,
    PosteriorSummary,
    evaluate_log_likelihood,
    fit_joint_event,
)
from faber2026.burst_models.kernels import (
    K_DM_S_MHZ2,
    convolved_tail_upper_bound,
    dispersion_delay_s,
    exponentially_modified_gaussian,
    gaussian_density,
    gaussian_power_law_density,
    power_law_pbf,
    power_law_pbf_tail_mass_after,
    scattering_index,
)
from faber2026.observations import BandObservation, DispersionState
from studies.dualband_synthetic import build_synthetic_event


def _evaluate_payload(payload: tuple[JointFitRequest, np.ndarray]) -> float:
    return evaluate_log_likelihood(*payload)


def _observation(
    instrument: str,
    frequencies_mhz: np.ndarray,
    product_dm: float,
    station_delay_s: float,
    *,
    injected_dm: float = 491.25,
    geocentric_toa_s: float = 0.08,
) -> BandObservation:
    times_s = np.linspace(0.02, 0.14, 241)
    width_s = 0.002
    centers = (
        geocentric_toa_s
        + station_delay_s
        + dispersion_delay_s(injected_dm - product_dm, frequencies_mhz)
    )
    intensity = np.stack(
        [gaussian_density(times_s, center, width_s) for center in centers],
        axis=0,
    )
    noise_std = np.full(frequencies_mhz.size, 0.02 * intensity.max())
    return BandObservation(
        instrument=instrument,
        intensity=intensity,
        valid_pixels=np.ones_like(intensity, dtype=bool),
        frequencies_mhz=frequencies_mhz,
        channel_widths_mhz=np.full(frequencies_mhz.size, 1.0),
        times_s=times_s,
        sample_interval_s=float(np.diff(times_s).mean()),
        time_origin_utc="2026-01-01T00:00:00.000000000",
        time_origin_unix_ns=1767225600000000000,
        frequency_frame="topocentric",
        dispersion=DispersionState(
            voltage_dm=0.0,
            coherent_delta_dm=product_dm,
            residual_delta_dm=0.0,
            product_dm=product_dm,
            time_origin_correction_s=0.0,
        ),
        noise_std=noise_std,
        gain_prior_std=2.0,
        input_hashes={"synthetic": "sha256:" + "0" * 64},
    )


def _request() -> JointFitRequest:
    return JointFitRequest(
        observations=(
            _observation("chimefrb", np.linspace(430.0, 790.0, 12), 491.18, 0.0),
            _observation("dsa110", np.linspace(1310.0, 1490.0, 9), 491.31, 0.002),
        ),
        geometry=GeometryConstraint(
            reference_frequency_mhz=400.0,
            epoch_unix_ns=1767225600000000000,
            station_delays_s={"chimefrb": 0.0, "dsa110": 0.002},
            station_delay_uncertainties_s={"chimefrb": 1e-7, "dsa110": 1e-7},
            clock_uncertainties_s={"chimefrb": 1e-7, "dsa110": 1e-7},
            independent_projection_difference_s=2e-9,
            maximum_projection_difference_s=1e-8,
        ),
        component_ids=("component-1",),
        band_component_ids={
            "chimefrb": ("chime-component-1",),
            "dsa110": ("dsa-component-1",),
        },
        associations=(
            AssociationHypothesis(
                association_id="one-to-one",
                matches=(
                    ComponentMatch(
                        latent_id="component-1",
                        chimefrb_component_id="chime-component-1",
                        dsa110_component_id="dsa-component-1",
                    ),
                ),
            ),
        ),
        morphology="gaussian",
        dm_bounds=(491.1, 491.4),
        toa_bounds_s=((0.07, 0.09),),
        width_bounds_s=((0.001, 0.004),),
        width_index_bounds=(-0.2, 0.2),
        seed=42,
        nlive=80,
        dlogz=0.2,
    )


def _truth_parameters(request: JointFitRequest, dm: float = 491.25) -> np.ndarray:
    """One matched component with unit amplitudes in both native bands."""

    values = [dm, 0.08, 0.002, 0.0, 0.0, 0.0]
    for instrument in ("chimefrb", "dsa110"):
        values.extend(1.0 for _ in request.band_component_ids[instrument])
    return np.asarray(values)


def _fake_result(
    request: JointFitRequest,
    *,
    association_id: str,
) -> JointFitResult:
    models = {
        observation.instrument: np.zeros_like(observation.intensity)
        for observation in request.observations
    }
    names = (
        "absolute_dm",
        "toa_400_s:component-1",
        "width_400_s:component-1",
        "width_index",
        "timing_error_s:chimefrb",
        "timing_error_s:dsa110",
    )
    return JointFitResult(
        status="provisional-owner-review",
        shared_dm=PosteriorSummary(491.25, 491.24, 491.26),
        component_toas=(PosteriorSummary(0.08, 0.079, 0.081),),
        parameter_names=names,
        parameter_units=("pc cm-3", "s", "s", "dimensionless", "s", "s"),
        samples=np.array([[491.25, 0.08, 0.002, 0.0, 0.0, 0.0]]),
        weights=np.array([1.0]),
        sample_morphologies=np.array(["gaussian"]),
        sample_associations=np.array([association_id]),
        log_evidence=0.0,
        log_evidence_uncertainty=0.1,
        maximum_not_on_boundary=True,
        prior_edge_mass_by_parameter={name: 0.0 for name in names},
        morphology_weights={"gaussian": 1.0},
        morphology_statuses={"gaussian": "provisional-owner-review"},
        morphology_log_evidences={"gaussian": 0.0},
        morphology_log_evidence_uncertainties={"gaussian": 0.1},
        morphology_maximum_prior_edge_mass={"gaussian": 0.0},
        association_weights={association_id: 1.0},
        model_by_instrument=models,
        residual_by_instrument=models,
    )


def test_cold_plasma_delay_uses_400_mhz_reference_and_sign() -> None:
    frequencies = np.array([400.0, 800.0, 1400.0])
    delay = dispersion_delay_s(1.0, frequencies)
    expected = K_DM_S_MHZ2 * (frequencies**-2 - 400.0**-2)
    np.testing.assert_allclose(delay, expected, rtol=0.0, atol=1e-15)
    assert delay[0] == 0.0
    assert delay[1] < 0.0


def test_cold_plasma_constant_matches_independent_si_derivation() -> None:
    electron_column = (1 * u.pc / u.cm**3).to(1 / u.m**2)
    derived = (
        e.si**2
        / (8 * np.pi**2 * eps0 * m_e * c)
        * electron_column
    ).to(u.s * u.Hz**2)
    derived_s_mhz2 = derived.value * 1e-12
    assert K_DM_S_MHZ2 == pytest.approx(derived_s_mhz2, rel=5e-7)


def test_gaussian_and_exponential_kernels_are_normalized() -> None:
    gaussian_area = quad(lambda t: gaussian_density(t, 0.0, 0.003), -0.1, 0.1)[0]
    emg_area = quad(
        lambda t: exponentially_modified_gaussian(t, 0.0, 0.003, 0.007),
        -0.1,
        0.5,
    )[0]
    assert gaussian_area == pytest.approx(1.0, abs=1e-10)
    assert emg_area == pytest.approx(1.0, abs=1e-9)


def test_power_law_pbf_is_causal_normalized_and_has_physical_endpoint() -> None:
    beta = 11.0 / 3.0
    tau_s = 0.004
    area = quad(lambda t: power_law_pbf(t, tau_s, beta), 0.0, np.inf)[0]
    assert area == pytest.approx(1.0, abs=1e-9)
    assert power_law_pbf(-1e-6, tau_s, beta) == 0.0
    assert scattering_index(beta) == pytest.approx(4.4)

    time_s = np.linspace(0.0, 0.05, 200)
    np.testing.assert_allclose(
        power_law_pbf(time_s, tau_s, 4.0),
        np.exp(-time_s / tau_s) / tau_s,
        rtol=1e-12,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        power_law_pbf(time_s, tau_s, 3.999999),
        np.exp(-time_s / tau_s) / tau_s,
        rtol=2e-5,
        atol=1e-10,
    )


def test_power_law_tail_bound_matches_independent_quadrature() -> None:
    tau_s = 0.004
    beta = 11.0 / 3.0
    for cutoff_s in (0.002, 0.02, 0.2):
        numerical = quad(
            lambda time: power_law_pbf(time, tau_s, beta),
            cutoff_s,
            np.inf,
        )[0]
        assert power_law_pbf_tail_mass_after(
            cutoff_s, tau_s, beta
        ) == pytest.approx(numerical, abs=1e-9)


def test_convolved_tail_bound_contains_independent_emg_tail() -> None:
    sigma_s = 0.002
    tau_s = 0.008
    for cutoff_s in (0.01, 0.04, 0.12):
        exact = exponnorm.sf(
            cutoff_s,
            tau_s / sigma_s,
            loc=0.0,
            scale=sigma_s,
        )
        bound = convolved_tail_upper_bound(
            cutoff_s,
            sigma_s,
            tau_s,
            beta=4.0,
        )
        assert exact <= bound
        assert bound <= 1.0


def test_power_law_convolution_reaches_exact_emg_endpoint() -> None:
    time_s = np.linspace(-0.01, 0.06, 101)
    expected = exponentially_modified_gaussian(
        time_s,
        center_s=0.01,
        sigma_s=0.002,
        tau_s=0.006,
    )
    actual = gaussian_power_law_density(
        time_s,
        center_s=0.01,
        sigma_s=0.002,
        tau_s=0.006,
        beta=4.0,
    )
    np.testing.assert_allclose(actual, expected, rtol=0.0, atol=0.0)


def test_power_law_convolution_is_stable_near_emg_endpoint() -> None:
    time_s = np.linspace(-0.005, 0.02, 20_001)
    actual = gaussian_power_law_density(
        time_s,
        center_s=0.0,
        sigma_s=0.0005,
        tau_s=0.000001,
        beta=3.999999,
    )
    expected = exponentially_modified_gaussian(
        time_s,
        center_s=0.0,
        sigma_s=0.0005,
        tau_s=0.000001,
    )
    assert trapezoid(actual, time_s) == pytest.approx(1.0, abs=1e-10)
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-8)


def test_power_law_convolution_matches_independent_adaptive_quadrature() -> None:
    beta = 11.0 / 3.0
    sigma_s = 0.0015
    tau_s = 0.003
    for time_s in (-0.002, 0.0, 0.004, 0.02):
        expected = quad(
            lambda lag, evaluation_time=time_s: gaussian_density(
                evaluation_time - lag,
                center_s=0.0,
                sigma_s=sigma_s,
            )
            * power_law_pbf(lag, tau_s, beta),
            0.0,
            np.inf,
            epsabs=1e-9,
        )[0]
        actual = gaussian_power_law_density(
            time_s,
            center_s=0.0,
            sigma_s=sigma_s,
            tau_s=tau_s,
            beta=beta,
        )
        assert actual == pytest.approx(expected, rel=2e-4, abs=1e-8)


def test_observation_rejects_double_dedispersion_and_wrong_reference() -> None:
    request = _request()
    bad_state = replace(
        request.observations[0].dispersion,
        residual_delta_dm=0.01,
    )
    bad_observation = replace(request.observations[0], dispersion=bad_state)
    with pytest.raises(ValueError, match="exactly-once dispersion"):
        replace(request, observations=(bad_observation, request.observations[1])).validate()

    bad_geometry = replace(request.geometry, reference_frequency_mhz=600.0)
    with pytest.raises(ValueError, match="400 MHz"):
        replace(request, geometry=bad_geometry).validate()


def test_time_origin_correction_is_explicitly_applied_once() -> None:
    request = _request()
    truth = _truth_parameters(request)
    shifted = replace(
        request.observations[0],
        dispersion=replace(
            request.observations[0].dispersion,
            time_origin_correction_s=0.004,
        ),
    )
    assert evaluate_log_likelihood(request, truth) > evaluate_log_likelihood(
        replace(request, observations=(shifted, request.observations[1])),
        truth,
    )


def test_width_and_scattering_priors_are_log_uniform() -> None:
    from faber2026.burst_models.joint import _prior_specs

    request = replace(_request(), morphology="emg")
    kinds = [kind for kind, _, _ in _prior_specs(request)]
    assert kinds[2] == "log_uniform"
    assert kinds[-1] == "log_uniform"


def test_valid_mask_controls_nonfinite_pixels_but_not_invalid_noise() -> None:
    request = _request()
    observation = request.observations[0]
    intensity = observation.intensity.copy()
    valid = observation.valid_pixels.copy()
    intensity[0, 0] = np.nan
    valid[0, 0] = False
    replace(observation, intensity=intensity, valid_pixels=valid).validate()
    valid[0, 0] = True
    with pytest.raises(ValueError, match="valid intensity"):
        replace(observation, intensity=intensity, valid_pixels=valid).validate()


def test_association_must_be_one_to_one_and_order_preserving() -> None:
    request = _request()
    invalid = AssociationHypothesis(
        association_id="reversed",
        matches=(
            ComponentMatch("a", "chime-a", "dsa-b"),
            ComponentMatch("b", "chime-b", "dsa-a"),
        ),
    )
    with pytest.raises(ValueError, match="order-preserving"):
        replace(
            request,
            component_ids=("a", "b"),
            band_component_ids={
                "chimefrb": ("chime-a", "chime-b"),
                "dsa110": ("dsa-a", "dsa-b"),
            },
            associations=(invalid,),
            toa_bounds_s=((0.05, 0.07), (0.08, 0.1)),
            width_bounds_s=((0.001, 0.004), (0.001, 0.004)),
        ).validate()


def test_two_declared_associations_are_evidence_marginalized() -> None:
    from faber2026.burst_models.joint import _mixture_result

    request = _request()
    alternate = replace(
        request.associations[0],
        association_id="same-physical-map-reviewed-again",
    )
    request = replace(
        request,
        associations=(request.associations[0], alternate),
        morphology=("gaussian",),
    )
    first = _fake_result(request, association_id="one-to-one")
    second = _fake_result(
        request,
        association_id="same-physical-map-reviewed-again",
    )
    mixture = _mixture_result(request, [first, second])
    assert mixture.association_weights == {
        "one-to-one": pytest.approx(0.5),
        "same-physical-map-reviewed-again": pytest.approx(0.5),
    }


def _synthetic_parameter_vector(request: JointFitRequest) -> np.ndarray:
    from faber2026.burst_models.joint import _parameter_names

    values = {
        "absolute_dm": 491.25,
        "toa_400_s:matched-component": 0.08,
        "width_400_s:matched-component": 0.002,
        "width_index": 0.0,
        "timing_error_s:chimefrb": 0.0,
        "timing_error_s:dsa110": 0.0,
        "tau_1ghz_s": 0.0003,
        "beta": 3.6666666666666665,
        "amplitude:chimefrb:chime-component-1": 1.0,
        "amplitude:chimefrb:chime-component-2": 0.6,
        "amplitude:dsa110:dsa-component-1": 1.0,
        "local_toa_s:chimefrb:chime-component-1": 0.125,
        "local_width_s:chimefrb:chime-component-1": 0.002,
        "local_toa_s:chimefrb:chime-component-2": 0.125,
        "local_width_s:chimefrb:chime-component-2": 0.002,
    }
    return np.asarray([values[name] for name in _parameter_names(request)])


def test_association_and_unmatched_nuisance_components_change_likelihood() -> None:
    import json
    from pathlib import Path

    configuration = json.loads(
        (Path(__file__).parents[1] / "analysis-configs/dualband-burst-models/synthetic.json").read_text()
    )
    event = build_synthetic_event(configuration)
    correct = replace(
        event.request,
        morphology="emg",
        associations=(event.request.associations[0],),
    )
    wrong = replace(
        event.request,
        morphology="emg",
        associations=(event.request.associations[1],),
    )
    assert evaluate_log_likelihood(correct, _synthetic_parameter_vector(correct)) > (
        evaluate_log_likelihood(wrong, _synthetic_parameter_vector(wrong))
    )
    no_nuisance = replace(
        correct,
        band_component_ids={
            "chimefrb": ("chime-component-1",),
            "dsa110": ("dsa-component-1",),
        },
    )
    assert evaluate_log_likelihood(correct, _synthetic_parameter_vector(correct)) > (
        evaluate_log_likelihood(no_nuisance, _synthetic_parameter_vector(no_nuisance))
    )


def test_powerlaw_injection_uses_and_constrains_truth_beta() -> None:
    import json
    from pathlib import Path

    from faber2026.burst_models.joint import _parameter_names

    configuration = json.loads(
        (Path(__file__).parents[1] / "analysis-configs/dualband-burst-models/synthetic.json").read_text()
    )
    configuration["synthetic"]["injected_morphology"] = "powerlaw"
    event = build_synthetic_event(configuration)
    request = replace(
        event.request,
        morphology="powerlaw",
        associations=(event.request.associations[0],),
    )
    truth = _synthetic_parameter_vector(request)
    wrong_beta = truth.copy()
    wrong_beta[list(_parameter_names(request)).index("beta")] = 3.05
    assert evaluate_log_likelihood(request, truth) > evaluate_log_likelihood(
        request, wrong_beta
    )


def test_nonzero_injected_time_origin_is_recovered_with_its_observation() -> None:
    import json
    from pathlib import Path

    configuration = json.loads(
        (Path(__file__).parents[1] / "analysis-configs/dualband-burst-models/synthetic.json").read_text()
    )
    event = build_synthetic_event(configuration)
    request = replace(
        event.request,
        morphology="emg",
        associations=(event.request.associations[0],),
    )
    truth = _synthetic_parameter_vector(request)
    dsa = request.observations[1]
    wrong_dsa = replace(
        dsa,
        time_origin_unix_ns=dsa.time_origin_unix_ns - 50_000_000,
        time_origin_utc="2026-01-01T00:00:00.000000000",
    )
    wrong = replace(request, observations=(request.observations[0], wrong_dsa))
    assert evaluate_log_likelihood(request, truth) > evaluate_log_likelihood(wrong, truth)


def test_shared_dm_likelihood_recovers_injected_truth_on_unlike_grids() -> None:
    request = _request()
    truth = _truth_parameters(request)
    low = truth.copy()
    low[0] -= 0.025
    high = truth.copy()
    high[0] += 0.025
    assert evaluate_log_likelihood(request, truth) > evaluate_log_likelihood(request, low)
    assert evaluate_log_likelihood(request, truth) > evaluate_log_likelihood(request, high)


def test_dispersion_delay_broadcasts_posterior_dm_samples() -> None:
    delays = dispersion_delay_s(
        np.array([[491.2], [491.3]]),
        np.array([[430.0, 790.0]]),
    )
    assert delays.shape == (2, 2)
    assert delays[0, 0] != delays[1, 0]


def test_wrong_geometric_sign_is_rejected_by_dual_band_likelihood() -> None:
    request = _request()
    truth = _truth_parameters(request)
    wrong_geometry = replace(
        request.geometry,
        station_delays_s={"chimefrb": 0.0, "dsa110": -0.002},
    )
    wrong_request = replace(request, geometry=wrong_geometry)
    assert evaluate_log_likelihood(request, truth) > evaluate_log_likelihood(
        wrong_request, truth
    )


def test_serial_and_process_parallel_likelihoods_are_identical() -> None:
    request = _request()
    points = []
    for dm in np.linspace(491.15, 491.35, 12):
        points.append(_truth_parameters(request, dm))
    serial = [evaluate_log_likelihood(request, point) for point in points]
    context = multiprocessing.get_context("spawn")
    with context.Pool(2) as pool:
        parallel = pool.map(_evaluate_payload, [(request, point) for point in points])
    np.testing.assert_array_equal(parallel, serial)


def test_rejected_zero_weight_morphology_does_not_block_valid_mixture() -> None:
    from faber2026.burst_models.joint import _mixture_result

    request = replace(_request(), morphology=("gaussian", "emg"))
    models = {
        observation.instrument: np.zeros_like(observation.intensity)
        for observation in request.observations
    }
    common = dict(
        shared_dm=PosteriorSummary(491.25, 491.24, 491.26),
        component_toas=(PosteriorSummary(0.08, 0.079, 0.081),),
        parameter_names=(
            "absolute_dm",
            "toa_400_s:component-1",
            "width_400_s:component-1",
            "width_index",
            "timing_error_s:chimefrb",
            "timing_error_s:dsa110",
        ),
        parameter_units=(
            "pc cm-3",
            "s",
            "s",
            "dimensionless",
            "s",
            "s",
        ),
        samples=np.array([[491.25, 0.08, 0.002, 0.0, 0.0, 0.0]]),
        weights=np.array([1.0]),
        sample_associations=np.array(["one-to-one"]),
        log_evidence_uncertainty=0.1,
        maximum_not_on_boundary=True,
        prior_edge_mass_by_parameter={
            "absolute_dm": 0.0,
            "toa_400_s:component-1": 0.0,
            "width_400_s:component-1": 0.0,
            "width_index": 0.0,
            "timing_error_s:chimefrb": 0.0,
            "timing_error_s:dsa110": 0.0,
        },
        association_weights={"one-to-one": 1.0},
        model_by_instrument=models,
        residual_by_instrument=models,
    )
    failed = JointFitResult(
        status="failed-inference",
        log_evidence=-100.0,
        morphology_weights={"gaussian": 1.0},
        morphology_statuses={"gaussian": "failed-inference"},
        morphology_log_evidences={"gaussian": -100.0},
        morphology_log_evidence_uncertainties={"gaussian": 0.1},
        morphology_maximum_prior_edge_mass={"gaussian": 1.0},
        sample_morphologies=np.array(["gaussian"]),
        **common,
    )
    valid = JointFitResult(
        status="provisional-owner-review",
        log_evidence=0.0,
        morphology_weights={"emg": 1.0},
        morphology_statuses={"emg": "provisional-owner-review"},
        morphology_log_evidences={"emg": 0.0},
        morphology_log_evidence_uncertainties={"emg": 0.1},
        morphology_maximum_prior_edge_mass={"emg": 0.0},
        sample_morphologies=np.array(["emg"]),
        **common,
    )
    mixture = _mixture_result(request, [failed, valid])
    assert mixture.status == "provisional-owner-review"
    assert mixture.morphology_weights["gaussian"] < 1e-40


def test_gain_marginalization_matches_direct_numerical_integration() -> None:
    from faber2026.burst_models.joint import (
        _gain_marginal_log_likelihood,
        _posterior_gain_model,
    )

    data = np.array([[0.2, 1.1, 0.4]])
    model = np.array([[0.1, 0.9, 0.3]])
    noise = np.array([0.2])
    gain_prior_std = 0.3
    analytic = _gain_marginal_log_likelihood(
        data,
        model,
        np.ones_like(data, dtype=bool),
        noise,
        gain_prior_std,
    )

    gain_grid = np.linspace(-1.0, 3.0, 200_001)
    log_data = (
        -0.5 * np.sum(((data[0] - gain_grid[:, None] * model[0]) / noise[0]) ** 2, axis=1)
        - data.shape[1] * np.log(np.sqrt(2.0 * np.pi) * noise[0])
    )
    log_prior = (
        -0.5 * (gain_grid / gain_prior_std) ** 2
        - np.log(np.sqrt(2.0 * np.pi) * gain_prior_std)
    )
    step = gain_grid[1] - gain_grid[0]
    numerical = logsumexp(log_data + log_prior) + np.log(step)
    assert analytic == pytest.approx(numerical, abs=1e-8)
    density = np.exp(log_data + log_prior - logsumexp(log_data + log_prior))
    posterior_mean = float(np.sum(gain_grid * density))
    adjusted = _posterior_gain_model(
        data,
        model,
        np.ones_like(data, dtype=bool),
        noise,
        gain_prior_std,
    )
    np.testing.assert_allclose(adjusted, posterior_mean * model, rtol=2e-5)


@pytest.mark.slow
def test_nested_fit_recovers_shared_dm_and_geocentric_toa() -> None:
    result = fit_joint_event(_request())
    assert result.status == "provisional-owner-review"
    assert result.shared_dm.median == pytest.approx(491.25, abs=0.01)
    assert result.component_toas[0].median == pytest.approx(0.08, abs=0.001)
    assert result.maximum_not_on_boundary


@pytest.mark.slow
def test_checkpoint_resume_preserves_completed_inference(tmp_path) -> None:
    import dynesty

    from faber2026.burst_models.joint import (
        _likelihood_for_request,
        _prior_specs,
        _prior_transform_for_specs,
    )

    request = replace(
        _request(),
        nlive=20,
        dlogz=0.5,
        checkpoint_directory=str(tmp_path / "checkpoints"),
    )
    checkpoint = tmp_path / "checkpoints" / "one-to-one-gaussian.pkl"
    checkpoint.parent.mkdir()
    specs = _prior_specs(request)
    interrupted = dynesty.NestedSampler(
        partial(_likelihood_for_request, request=request),
        partial(_prior_transform_for_specs, specs=specs),
        ndim=len(specs),
        nlive=request.nlive,
        rstate=np.random.default_rng(request.seed),
        sample="rwalk",
        bound="multi",
    )
    for _ in interrupted.sample(dlogz=request.dlogz, save_bounds=True):
        if interrupted.ncall >= 100:
            break
    interrupted.save(str(checkpoint))
    resumed = fit_joint_event(request)
    uninterrupted = fit_joint_event(replace(request, checkpoint_directory=None))
    np.testing.assert_array_equal(resumed.samples, uninterrupted.samples)
    np.testing.assert_array_equal(resumed.weights, uninterrupted.weights)
    assert resumed.log_evidence == uninterrupted.log_evidence
