from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

import radio_pipeline.fitting.joint_burst as joint_module
from radio_pipeline.fitting._pulse_kernels import (
    gaussian_density,
    gaussian_exponential_density,
)
from radio_pipeline.fitting.joint_burst import (
    K_DM_S_MHZ2,
    AssociationHypothesis,
    BandObservation,
    ComponentMatch,
    ComponentWindow,
    DispersionState,
    FitSettings,
    GeometryConstraint,
    HypothesisFit,
    JointFitRequest,
    _checkpoint_identity,
    _layout,
    _log_likelihood,
    _mixture_edge_mass,
    _structured_residual_correlation,
    fit_joint_event,
)
from radio_pipeline.fitting.products import sha256_file, write_band_observation_product
from radio_pipeline.fitting.resolution import sample_time_axis_ns
from scattering.scat_analysis.burstfit import (
    analytic_gaussian_exp_convolution,
)
from scripts.fit_one_event_joint_burst import (
    _arrays_sha256,
    _load_locked_fit_observations,
    _require_accepted_status,
    _require_locked_array_identity,
    _require_locked_product_metadata,
)

EPOCH_NS = 1_700_000_000_000_000_000
TRUE_DM = 100.05
TRUE_TOA_S = 0.010


def _dispersion(product_dm: float, *, mode: str) -> DispersionState:
    if mode == "coherent_anchor":
        return DispersionState(0.0, product_dm, 0.0, product_dm, mode)
    return DispersionState(product_dm, 0.0, 0.0, product_dm, mode)


def _observation(
    instrument: str,
    frequency_mhz: np.ndarray,
    sample_interval_s: float,
    product_dm: float,
    site_delay_s: float,
) -> BandObservation:
    ntime = 180
    time = np.arange(ntime) * sample_interval_s
    center = (
        TRUE_TOA_S
        + site_delay_s
        + K_DM_S_MHZ2 * (TRUE_DM - product_dm) * (frequency_mhz**-2 - 400.0**-2)
    )
    width = 4.0e-4 * (frequency_mhz / 400.0) ** -0.2
    profile = gaussian_density(time, center, width)
    gains = np.linspace(8.0e-4, 1.2e-3, frequency_mhz.size)
    waterfall = gains[:, None] * profile
    noise = np.full_like(waterfall, 0.03)
    return BandObservation(
        instrument=instrument,
        waterfall=waterfall,
        valid=np.ones_like(waterfall, dtype=bool),
        frequency_mhz=frequency_mhz,
        channel_width_mhz=np.full(frequency_mhz.size, 0.1),
        noise_std=noise,
        sample_interval_s=sample_interval_s,
        time0_unix_ns=EPOCH_NS,
        reference_frequency_mhz=400.0,
        dispersion=_dispersion(
            product_dm,
            mode="coherent_anchor" if instrument == "chime" else "filterbank_input",
        ),
        input_sha256={"source": "a" * 64},
    )


def _request() -> JointFitRequest:
    chime_dt = 1.0e-4
    dsa_dt = 2.0e-4
    chime_delay = 1.0e-3
    dsa_delay = -2.0e-3
    chime = _observation(
        "chime",
        np.linspace(450.0, 750.0, 12),
        chime_dt,
        100.0,
        chime_delay,
    )
    dsa = _observation(
        "dsa",
        np.linspace(1300.0, 1500.0, 10),
        dsa_dt,
        100.1,
        dsa_delay,
    )
    return JointFitRequest(
        observations=(chime, dsa),
        geometry=GeometryConstraint(
            epoch_unix_ns=EPOCH_NS,
            source_icrs="12:00:00 +20:00:00",
            site_delay_s={"chime": chime_delay, "dsa": dsa_delay},
            site_delay_sigma_s={"chime": 1.0e-8, "dsa": 1.0e-8},
            clock_sigma_s={"chime": 1.0e-8, "dsa": 1.0e-8},
            projection_disagreement_s=1.0e-10,
        ),
        components=(
            ComponentWindow(
                "chime",
                "c1",
                (TRUE_TOA_S + chime_delay) / chime_dt,
                12.0,
                (2.0e-4, 8.0e-4),
                (-1.0, 1.0),
            ),
            ComponentWindow(
                "dsa",
                "d1",
                (TRUE_TOA_S + dsa_delay) / dsa_dt,
                8.0,
                (2.0e-4, 8.0e-4),
                (-1.0, 1.0),
            ),
        ),
        associations=(
            AssociationHypothesis(
                "c1-d1",
                (ComponentMatch("pulse1", "c1", "d1"),),
            ),
        ),
        settings=FitSettings(
            dm_bounds_pc_cm3=(99.8, 100.3),
            morphologies=("gaussian",),
            gain_variance=1.0e-4,
            seed=12,
            nlive=40,
            dlogz=1.0,
        ),
    )


def _theta(request: JointFitRequest, dm: float) -> tuple[np.ndarray, object]:
    hypothesis = request.associations[0]
    layout = _layout(request, hypothesis, "gaussian")
    values = {
        "absolute_dm_pc_cm3": dm,
        "toa_pulse1_s": TRUE_TOA_S,
        "width_pulse1_s": 4.0e-4,
        "width_index_pulse1": -0.2,
        "timing_error_chime_s": 0.0,
        "timing_error_dsa_s": 0.0,
    }
    return np.asarray([values[item.name] for item in layout.parameters]), layout


def test_different_native_grids_share_one_absolute_dm_maximum() -> None:
    request = _request()
    truth, layout = _theta(request, TRUE_DM)
    low, _ = _theta(request, TRUE_DM - 0.12)
    high, _ = _theta(request, TRUE_DM + 0.12)
    truth_score = _log_likelihood(truth, request, layout, "gaussian")
    assert truth_score > _log_likelihood(low, request, layout, "gaussian")
    assert truth_score > _log_likelihood(high, request, layout, "gaussian")


@pytest.mark.parametrize(
    ("chime_dt", "dsa_dt", "chime_rows", "dsa_rows"),
    (
        (0.8e-4, 1.5e-4, 16, 14),
        (1.2e-4, 2.5e-4, 8, 7),
    ),
)
def test_locked_finer_and_coarser_grids_recover_same_dm_direction(
    chime_dt: float,
    dsa_dt: float,
    chime_rows: int,
    dsa_rows: int,
) -> None:
    request = _request()
    chime_delay = request.geometry.site_delay_s["chime"]
    dsa_delay = request.geometry.site_delay_s["dsa"]
    chime = _observation(
        "chime",
        np.linspace(450.0, 750.0, chime_rows),
        chime_dt,
        100.0,
        chime_delay,
    )
    dsa = _observation(
        "dsa",
        np.linspace(1300.0, 1500.0, dsa_rows),
        dsa_dt,
        100.1,
        dsa_delay,
    )
    varied = replace(
        request,
        observations=(chime, dsa),
        components=(
            replace(
                request.components[0],
                center_sample=(TRUE_TOA_S + chime_delay) / chime_dt,
            ),
            replace(
                request.components[1],
                center_sample=(TRUE_TOA_S + dsa_delay) / dsa_dt,
            ),
        ),
    )
    truth, layout = _theta(varied, TRUE_DM)
    low, _ = _theta(varied, TRUE_DM - 0.12)
    high, _ = _theta(varied, TRUE_DM + 0.12)
    truth_score = _log_likelihood(truth, varied, layout, "gaussian")
    assert truth_score > _log_likelihood(low, varied, layout, "gaussian")
    assert truth_score > _log_likelihood(high, varied, layout, "gaussian")


@pytest.mark.slow
def test_nested_sampler_recovers_injected_absolute_dm_and_toa() -> None:
    request = _request()
    request = replace(
        request,
        settings=replace(request.settings, nlive=20, dlogz=2.0),
    )
    result = fit_joint_event(request)
    assert result.status == "provisional_pending_owner_approval"
    assert result.dm_pc_cm3["median"] == pytest.approx(TRUE_DM, abs=0.003)
    toa = result.geocentric_toa_unix_ns["pulse1"]
    assert toa["median"] == pytest.approx(
        EPOCH_NS + TRUE_TOA_S * 1.0e9,
        abs=50_000.0,
    )
    assert set(result.topocentric_toa_unix_ns["pulse1"]) == {"chime", "dsa"}


@pytest.mark.slow
def test_multiprocessing_checkpoint_resume_preserves_posterior(tmp_path) -> None:
    request = _request()
    settings = replace(
        request.settings,
        morphologies=("gaussian",),
        nlive=20,
        dlogz=3.0,
        pool_size=2,
        checkpoint_dir=str(tmp_path),
        resume=False,
    )
    first = fit_joint_event(replace(request, settings=settings))
    assert list(tmp_path.glob("*.save"))
    resumed = fit_joint_event(replace(request, settings=replace(settings, resume=True)))
    assert resumed.dm_pc_cm3["median"] == pytest.approx(first.dm_pc_cm3["median"], abs=1.0e-12)
    assert resumed.geocentric_toa_unix_ns == (first.geocentric_toa_unix_ns)


def test_independent_residual_dm_identity_is_required() -> None:
    with pytest.raises(ValueError, match="dispersion identity"):
        DispersionState(100.0, 0.1, 0.2, 100.4, "bad")


def test_reference_frequency_and_uncertainty_fail_closed() -> None:
    request = _request()
    chime = request.observations[0]
    with pytest.raises(ValueError, match="400 MHz"):
        replace(chime, reference_frequency_mhz=600.0)
    with pytest.raises(ValueError, match="positive geometric/clock"):
        replace(
            request.geometry,
            site_delay_sigma_s={"chime": 0.0, "dsa": 1.0e-8},
            clock_sigma_s={"chime": 0.0, "dsa": 1.0e-8},
        )


def test_request_rejects_duplicate_observation_entries() -> None:
    request = _request()
    with pytest.raises(ValueError, match="exactly two observations"):
        replace(
            request,
            observations=request.observations + (request.observations[0],),
        )


def test_component_window_must_fit_locked_crop() -> None:
    request = _request()
    with pytest.raises(ValueError, match="locked crop"):
        replace(
            request,
            components=(
                replace(
                    request.components[0],
                    center_sample=1.0,
                    half_width_samples=5.0,
                ),
                request.components[1],
            ),
        )


def test_authoritative_frequency_and_support_identities_fail_on_drift() -> None:
    observation = _request().observations[0]
    resolution = {
        "chime_frequency_grid_sha256": _arrays_sha256(
            observation.frequency_mhz,
            observation.channel_width_mhz,
        ),
        "chime_valid_mask_sha256": _arrays_sha256(observation.valid),
    }
    _require_locked_array_identity(observation, resolution)
    with pytest.raises(ValueError, match="frequency grid"):
        _require_locked_array_identity(
            replace(
                observation,
                frequency_mhz=observation.frequency_mhz + 0.001,
            ),
            resolution,
        )
    changed_valid = observation.valid.copy()
    changed_valid[0, 0] = False
    with pytest.raises(ValueError, match="valid support"):
        _require_locked_array_identity(
            replace(observation, valid=changed_valid),
            resolution,
        )


def test_crop_origin_and_off_pulse_support_fail_on_drift() -> None:
    mask = np.zeros((2, 16), dtype=bool)
    mask[:, :4] = True
    waterfall = np.ones((2, 16))
    noise_std = np.full((2, 16), 2.0)
    time0_unix_ns = 1_700_000_000_000_000_123
    sample_interval_s = 1.0e-3
    time_axis_ns = sample_time_axis_ns(
        time0_unix_ns=time0_unix_ns,
        sample_interval_s=sample_interval_s,
        sample_count=waterfall.shape[1],
    )
    resolution = {
        "chime_time0_unix_ns": time0_unix_ns,
        "chime_off_pulse_mask_sha256": _arrays_sha256(mask),
        "chime_waterfall_sha256": _arrays_sha256(waterfall),
        "chime_noise_std_sha256": _arrays_sha256(noise_std),
        "chime_time_axis_sha256": _arrays_sha256(time_axis_ns),
    }
    product = {
        "time0_unix_ns": np.asarray(resolution["chime_time0_unix_ns"], dtype=np.int64),
        "noise_estimation_mask": mask,
        "waterfall": waterfall,
        "noise_std": noise_std,
        "sample_interval_s": np.asarray(sample_interval_s),
    }
    _require_locked_product_metadata(product, "chime", resolution)
    shifted = dict(product)
    shifted["time0_unix_ns"] = np.asarray(resolution["chime_time0_unix_ns"] + 1)
    with pytest.raises(ValueError, match="crop origin"):
        _require_locked_product_metadata(shifted, "chime", resolution)
    changed_mask = dict(product)
    changed_mask["noise_estimation_mask"] = np.roll(mask, 1, axis=1)
    with pytest.raises(ValueError, match="off-pulse"):
        _require_locked_product_metadata(changed_mask, "chime", resolution)


@pytest.mark.parametrize("mutation", ["dispersion_metadata", "extra_bytes"])
def test_direct_fit_rejects_fit_observation_file_drift(tmp_path, mutation) -> None:
    paths = {}
    observations = _request().observations
    for observation in observations:
        path = tmp_path / f"{observation.instrument}.npz"
        write_band_observation_product(
            path,
            instrument=observation.instrument,
            waterfall=observation.waterfall,
            valid=observation.valid,
            frequency_mhz=observation.frequency_mhz,
            channel_width_mhz=observation.channel_width_mhz,
            sample_interval_s=observation.sample_interval_s,
            time0_unix_ns=observation.time0_unix_ns,
            dispersion=observation.dispersion,
            input_sha256=dict(observation.input_sha256),
        )
        paths[observation.instrument] = path
    resolution = {
        f"{instrument}_fit_observation_sha256": sha256_file(path)
        for instrument, path in paths.items()
    }
    target = paths["dsa"]
    if mutation == "dispersion_metadata":
        with np.load(target, allow_pickle=False) as archive:
            payload = {name: archive[name] for name in archive.files}
        payload["product_dm_pc_cm3"] = np.asarray(
            float(payload["product_dm_pc_cm3"]) + 0.001
        )
        np.savez_compressed(target, **payload)
    else:
        with target.open("ab") as handle:
            handle.write(b"unexpected trailing bytes")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        _load_locked_fit_observations(
            {"resolution": resolution},
            paths["chime"],
            paths["dsa"],
        )


def test_association_must_be_order_preserving() -> None:
    request = _request()
    chime2 = replace(request.components[0], component_id="c2", center_sample=130.0)
    dsa2 = replace(request.components[1], component_id="d2", center_sample=70.0)
    with pytest.raises(ValueError, match="preserve time order"):
        replace(
            request,
            components=request.components + (chime2, dsa2),
            associations=(
                AssociationHypothesis(
                    "crossed",
                    (
                        ComponentMatch("p1", "c1", "d2"),
                        ComponentMatch("p2", "c2", "d1"),
                    ),
                ),
            ),
        )


def test_association_mixture_requires_stable_latent_identity() -> None:
    request = _request()
    with pytest.raises(ValueError, match="same latent component IDs"):
        replace(
            request,
            associations=(
                request.associations[0],
                AssociationHypothesis(
                    "renamed",
                    (ComponentMatch("another_pulse", "c1", "d1"),),
                ),
            ),
        )


def test_association_hypothesis_names_must_be_unique() -> None:
    request = _request()
    with pytest.raises(ValueError, match="names must be unique"):
        replace(
            request,
            associations=(
                request.associations[0],
                request.associations[0],
            ),
        )


def test_unmatched_component_prior_stays_topocentric() -> None:
    request = _request()
    extra = ComponentWindow(
        "chime",
        "local",
        140.0,
        3.0,
        (2.0e-4, 8.0e-4),
    )
    layout = _layout(
        replace(request, components=request.components + (extra,)),
        request.associations[0],
        "gaussian",
    )
    parameter = next(item for item in layout.parameters if item.name == "local_toa_chime_local_s")
    expected_center = 140.0 * request.observations[0].sample_interval_s
    assert (parameter.low + parameter.high) / 2.0 == pytest.approx(expected_center)


def test_matched_width_priors_must_overlap() -> None:
    request = _request()
    incompatible = replace(request.components[1], width_bounds_s=(9.0e-4, 1.1e-3))
    with pytest.raises(ValueError, match="width priors do not overlap"):
        _layout(
            replace(
                request,
                components=(request.components[0], incompatible),
            ),
            request.associations[0],
            "gaussian",
        )


def test_checkpoint_identity_changes_with_data_and_priors() -> None:
    request = _request()
    original = _checkpoint_identity(request, request.associations[0], "gaussian")
    changed_data = replace(
        request.observations[0],
        waterfall=request.observations[0].waterfall + 1.0e-8,
    )
    changed_request = replace(
        request,
        observations=(changed_data, request.observations[1]),
    )
    changed_prior = replace(
        request,
        settings=replace(request.settings, dm_bounds_pc_cm3=(99.7, 100.3)),
    )
    assert (
        _checkpoint_identity(changed_request, changed_request.associations[0], "gaussian")
        != original
    )
    assert (
        _checkpoint_identity(changed_prior, changed_prior.associations[0], "gaussian") != original
    )


def test_edge_mass_detects_boundary_posterior_with_interior_median() -> None:
    run = HypothesisFit(
        morphology="gaussian",
        association="one",
        parameter_names=("absolute_dm_pc_cm3",),
        samples=np.asarray([[0.001], [0.5], [0.999]]),
        sample_weights=np.asarray([0.1, 0.8, 0.1]),
        log_evidence=0.0,
        log_evidence_error=0.1,
        diagnostics={},
    )
    assert _mixture_edge_mass(
        [run], np.asarray([1.0]), "absolute_dm_pc_cm3", (0.0, 1.0), 0.01
    ) == pytest.approx(0.2)


def test_failed_fit_status_exits_fail_closed() -> None:
    with pytest.raises(RuntimeError, match="failed_dm_edge"):
        _require_accepted_status("failed_dm_edge")


def test_structured_frequency_time_residual_is_detected() -> None:
    observation = _request().observations[0]
    frequency = observation.frequency_mhz
    time = np.arange(observation.waterfall.shape[1], dtype=float)
    frequency = (frequency - frequency.mean()) / frequency.std()
    time = (time - time.mean()) / time.std()
    residual = (frequency[:, None] * time[None, :])[observation.valid]
    assert _structured_residual_correlation(observation, residual) == pytest.approx(1.0)


def test_association_evidence_selects_or_preserves_ambiguity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request()
    second_chime = replace(
        request.components[0],
        component_id="c2",
        center_sample=request.components[0].center_sample + 3.0,
    )
    associations = (
        request.associations[0],
        AssociationHypothesis(
            "c2-d1",
            (ComponentMatch("pulse1", "c2", "d1"),),
        ),
    )
    request = replace(
        request,
        components=request.components + (second_chime,),
        associations=associations,
    )
    evidence = {"c1-d1": 4.0, "c2-d1": 0.0}

    def fake_fit(request, hypothesis, morphology):
        layout = _layout(request, hypothesis, morphology)
        sample = []
        for parameter in layout.parameters:
            if parameter.kind == "normal":
                sample.append(0.0)
            elif parameter.kind == "log_uniform":
                sample.append(np.sqrt(parameter.low * parameter.high))
            else:
                sample.append((parameter.low + parameter.high) / 2.0)
        return HypothesisFit(
            morphology=morphology,
            association=hypothesis.name,
            parameter_names=tuple(parameter.name for parameter in layout.parameters),
            samples=np.asarray([sample]),
            sample_weights=np.asarray([1.0]),
            log_evidence=evidence[hypothesis.name],
            log_evidence_error=0.1,
            diagnostics={
                "bands": {
                    instrument: {
                        "reduced_residual_power": 1.0,
                        "structured_frequency_time_correlation": 0.0,
                    }
                    for instrument in ("chime", "dsa")
                },
                "prior_rail_parameters": [],
            },
        )

    monkeypatch.setattr(joint_module, "_fit_one", fake_fit)
    selected = fit_joint_event(request)
    assert selected.diagnostics["run_weights"]["gaussian:c1-d1"] > 0.98

    evidence["c1-d1"] = 0.0
    ambiguous = fit_joint_event(request)
    assert ambiguous.diagnostics["run_weights"] == pytest.approx(
        {"gaussian:c1-d1": 0.5, "gaussian:c2-d1": 0.5}
    )


def _fit_with_rejected_candidate(
    monkeypatch: pytest.MonkeyPatch,
    rejected_log_evidence: float,
    rejected_log_evidence_error: float = 0.1,
):
    request = _request()
    second_chime = replace(
        request.components[0],
        component_id="c2",
        center_sample=request.components[0].center_sample + 3.0,
    )
    request = replace(
        request,
        components=request.components + (second_chime,),
        associations=(
            request.associations[0],
            AssociationHypothesis(
                "rejected",
                (ComponentMatch("pulse1", "c2", "d1"),),
            ),
        ),
    )

    def fake_fit(request, hypothesis, morphology):
        layout = _layout(request, hypothesis, morphology)
        sample = []
        for parameter in layout.parameters:
            if parameter.kind == "normal":
                sample.append(0.0)
            elif parameter.kind == "log_uniform":
                sample.append(np.sqrt(parameter.low * parameter.high))
            else:
                sample.append((parameter.low + parameter.high) / 2.0)
        rejected = hypothesis.name == "rejected"
        return HypothesisFit(
            morphology=morphology,
            association=hypothesis.name,
            parameter_names=tuple(parameter.name for parameter in layout.parameters),
            samples=np.asarray([sample]),
            sample_weights=np.asarray([1.0]),
            log_evidence=rejected_log_evidence if rejected else 10.0,
            log_evidence_error=rejected_log_evidence_error if rejected else 0.1,
            diagnostics={
                "bands": {
                    instrument: {
                        "reduced_residual_power": 99.0 if rejected else 1.0,
                        "structured_frequency_time_correlation": 0.0,
                    }
                    for instrument in ("chime", "dsa")
                },
                "prior_rail_parameters": ["rejected_only"] if rejected else [],
            },
        )

    monkeypatch.setattr(joint_module, "_fit_one", fake_fit)
    return fit_joint_event(request)


def test_negligible_candidate_diagnostics_do_not_poison_mixture(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = _fit_with_rejected_candidate(monkeypatch, rejected_log_evidence=-100.0)

    assert selected.status == "provisional_pending_owner_approval"
    assert selected.diagnostics["maximum_reduced_residual_power"] == 1.0
    assert selected.diagnostics["prior_rail_parameters"] == []


def test_equal_weight_candidate_diagnostics_remain_plausible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = _fit_with_rejected_candidate(monkeypatch, rejected_log_evidence=10.0)

    assert selected.status == "failed_prior_rail"
    assert selected.diagnostics["maximum_reduced_residual_power"] == 99.0
    assert selected.diagnostics["prior_rail_parameters"] == ["rejected_only"]


def test_four_point_nine_percent_candidate_remains_plausible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rejected_log_evidence = 10.0 + np.log(0.049 / 0.951)
    selected = _fit_with_rejected_candidate(
        monkeypatch,
        rejected_log_evidence=rejected_log_evidence,
    )

    assert selected.status == "failed_prior_rail"
    assert selected.diagnostics["prior_rail_parameters"] == ["rejected_only"]


def test_large_evidence_error_keeps_low_point_weight_candidate_plausible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = _fit_with_rejected_candidate(
        monkeypatch,
        rejected_log_evidence=-100.0,
        rejected_log_evidence_error=100.0,
    )

    assert selected.status == "failed_prior_rail"
    assert selected.diagnostics["prior_rail_parameters"] == ["rejected_only"]


@pytest.mark.parametrize("error", [-0.1, np.nan, np.inf])
def test_invalid_log_evidence_error_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    error: float,
) -> None:
    with pytest.raises(ValueError, match="evidence errors"):
        _fit_with_rejected_candidate(
            monkeypatch,
            rejected_log_evidence=-100.0,
            rejected_log_evidence_error=error,
        )


def test_exponential_kernel_matches_legacy_kernel() -> None:
    time = np.linspace(-0.003, 0.008, 256)
    center = np.array([0.0, 0.0004])
    sigma = np.array([0.0003, 0.0005])
    tau = np.array([0.0007, 0.0011])
    new = gaussian_exponential_density(time, center, sigma, tau)
    old = analytic_gaussian_exp_convolution(
        time,
        center[:, None],
        sigma[:, None],
        tau[:, None],
    )
    np.testing.assert_allclose(new, old, rtol=2.0e-12, atol=1.0e-12)
