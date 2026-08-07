from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.verify_joint_fit_resolution_convergence import main, verify


def _sha(digit: str) -> str:
    return digit * 64


def _write(path: Path, value: dict) -> Path:
    path.write_text(json.dumps(value, indent=2) + "\n")
    return path


def _receipt(instrument: str, factor: int, output_sha256: str) -> dict:
    source_digit = "1" if instrument == "chime" else "2"
    return {
        "schema_version": 1,
        "status": "candidate_fit_grid_pending_resolution_review",
        "instrument": instrument,
        "source": {
            "path": f"/immutable/{instrument}.npz",
            "sha256": _sha(source_digit),
            "waterfall_sha256": _sha("3"),
            "valid_mask_sha256": _sha("4"),
            "frequency_grid_sha256": _sha("5"),
            "noise_sha256": _sha("6"),
            "time_axis_sha256": _sha("7"),
        },
        "settings": {
            "frequency_bin_factor": factor,
            "time_bin_factor": 1,
            "minimum_valid_fraction": 1.0,
            "frequency_contiguity_tolerance_mhz": 1.0e-9,
        },
        "proposal": {"arrays_and_settings_sha256": _sha("8")},
        "output": {
            "path": f"/fit/{instrument}-{factor}.npz",
            "sha256": output_sha256,
        },
    }


def _config(binding: str, factor: int, observation_hashes: dict[str, str]) -> dict:
    associations = [
        {
            "name": "c1d1",
            "matches": [
                {
                    "latent_id": "c1",
                    "chime_component_id": "chime_c1",
                    "dsa_component_id": "dsa_c1",
                }
            ],
        }
    ]
    return {
        "event": "injected",
        "event_binding_sha256": binding,
        "input_sha256": {
            "raw_chime_h5": _sha("a"),
            "accepted_chime_reference": _sha("b"),
            "raw_dsa_filterbank": _sha("c"),
            "accepted_dsa_reference": _sha("d"),
        },
        "chime": {"anchor_dm_pc_cm3": 491.28},
        "dsa": {
            "accepted_reference_dm_pc_cm3": 491.28,
            "input_dm_pc_cm3": 491.20,
            "input_dm_method": "inferred_raw_reference_row_timing",
            "input_dm_bound_source": "reviewed fixture",
            "reference_minus_raw_dm_pc_cm3": 0.08,
            "reference_minus_raw_dm_interval_pc_cm3": [0.07, 0.09],
        },
        "joint_fit": {
            "status": "ready",
            "geometry": {
                "source_icrs": "00h00m00s +00d00m00s",
                "epoch_mjd_utc": 60000.0,
                "site_delay_sigma_s": {"chime": 5.0e-7, "dsa": 5.0e-7},
                "clock_sigma_s": {"chime": 7.0e-4, "dsa": 7.0e-4},
            },
            "components": [
                {
                    "instrument": "chime",
                    "component_id": "chime_c1",
                    "center_sample": 10.0,
                    "half_width_samples": 4.0,
                    "width_bounds_s": [1.0e-5, 1.0e-3],
                },
                {
                    "instrument": "dsa",
                    "component_id": "dsa_c1",
                    "center_sample": 12.0,
                    "half_width_samples": 4.0,
                    "width_bounds_s": [1.0e-5, 1.0e-3],
                },
            ],
            "associations": associations,
            "dm_bounds_pc_cm3": [491.0, 491.5],
            "morphologies": ["gaussian", "scattering"],
            "scattering_tau_1ghz_bounds_s": [1.0e-6, 1.0e-2],
            "scattering_alpha_bounds": [2.0, 6.0],
            "gain_variance": 100.0,
            "maximum_projection_disagreement_s": 5.0e-7,
            "sampler": {
                "seed": 42,
                "nlive": 600,
                "dlogz": 0.5,
                "sample": "rwalk",
                "pool_size": 4,
                "resume": True,
            },
            "acceptance": {
                "maximum_reduced_residual_power": 2.0,
                "maximum_structured_residual_correlation": 0.2,
                "posterior_edge_fraction": 0.01,
                "maximum_prior_edge_mass": 0.05,
                "resolution_convergence_required": True,
                "maximum_resolution_dm_shift_combined_sigma": 0.5,
                "maximum_resolution_dm_shift_pc_cm3": 0.005,
                "maximum_resolution_toa_shift_combined_sigma": 0.5,
                "resolution_interval_width_ratio": [0.8, 1.25],
                "maximum_resolution_model_weight_l1_difference": 0.1,
            },
            "resolution": {
                "chime_fit_frequency_average_factor": factor,
                "chime_fit_time_average_factor": 1,
                "dsa_fit_frequency_average_factor": factor,
                "dsa_fit_time_average_factor": 1,
                "chime_fit_observation_sha256": observation_hashes["chime"],
                "dsa_fit_observation_sha256": observation_hashes["dsa"],
            },
        },
    }


def _summary(median: float, half_width: float) -> dict[str, float]:
    return {
        "lower": median - half_width,
        "median": median,
        "upper": median + half_width,
    }


def _fit(
    binding: str,
    observation_hashes: dict[str, str],
    *,
    dm_median: float,
    dm_half_width: float,
    toa_median_ns: int,
    toa_half_width_ns: int,
    run_weights: dict[str, float],
) -> dict:
    return {
        "schema_version": 1,
        "status": "provisional_pending_owner_approval",
        "event": "injected",
        "event_binding_sha256": binding,
        "reference_frequency_mhz": 400.0,
        "shared_absolute_dm_pc_cm3": _summary(dm_median, dm_half_width),
        "geocentric_unscattered_toa_unix_ns": {"c1": _summary(toa_median_ns, toa_half_width_ns)},
        "diagnostics": {
            "model_adequate": True,
            "maximum_reduced_residual_power": 1.1,
            "maximum_structured_residual_correlation": 0.05,
            "run_weights": run_weights,
        },
        "fit_inputs": {
            "geometry_constraint": _sha("9"),
            "chime_observation": observation_hashes["chime"],
            "dsa_observation": observation_hashes["dsa"],
        },
        "provenance_code_sha256": {
            "joint_burst": _sha("1"),
            "products": _sha("2"),
            "pulse_kernels": _sha("3"),
            "runner": _sha("4"),
        },
    }


def _fixture(tmp_path: Path) -> dict[str, Path]:
    coarse_hashes = {"chime": _sha("e"), "dsa": _sha("f")}
    fine_hashes = {"chime": _sha("0"), "dsa": _sha("1")}
    weights_coarse = {"gaussian:c1d1": 0.55, "scattering:c1d1": 0.45}
    weights_fine = {"gaussian:c1d1": 0.52, "scattering:c1d1": 0.48}
    values = {
        "coarse_config": _config(_sha("2"), 16, coarse_hashes),
        "fine_config": _config(_sha("3"), 8, fine_hashes),
        "coarse_fit": _fit(
            _sha("2"),
            coarse_hashes,
            dm_median=491.280,
            dm_half_width=0.010,
            toa_median_ns=1_700_000_000_000_000_000,
            toa_half_width_ns=1_000_000,
            run_weights=weights_coarse,
        ),
        "fine_fit": _fit(
            _sha("3"),
            fine_hashes,
            dm_median=491.282,
            dm_half_width=0.011,
            toa_median_ns=1_700_000_000_000_300_000,
            toa_half_width_ns=1_100_000,
            run_weights=weights_fine,
        ),
        "coarse_chime_receipt": _receipt("chime", 16, coarse_hashes["chime"]),
        "coarse_dsa_receipt": _receipt("dsa", 16, coarse_hashes["dsa"]),
        "fine_chime_receipt": _receipt("chime", 8, fine_hashes["chime"]),
        "fine_dsa_receipt": _receipt("dsa", 8, fine_hashes["dsa"]),
    }
    return {name: _write(tmp_path / f"{name}.json", value) for name, value in values.items()}


def _verify(paths: dict[str, Path]) -> dict:
    return verify(
        coarse_fit_result_path=paths["coarse_fit"],
        fine_fit_result_path=paths["fine_fit"],
        coarse_config_path=paths["coarse_config"],
        fine_config_path=paths["fine_config"],
        coarse_receipt_paths={
            "chime": paths["coarse_chime_receipt"],
            "dsa": paths["coarse_dsa_receipt"],
        },
        fine_receipt_paths={
            "chime": paths["fine_chime_receipt"],
            "dsa": paths["fine_dsa_receipt"],
        },
    )


def test_resolution_convergence_passes_and_records_hash_bound_metrics(tmp_path) -> None:
    report = _verify(_fixture(tmp_path))
    assert report["status"] == "passed"
    assert report["passed"] is True
    assert report["frequency_average_factors"] == {
        "coarse": {"chime": 16, "dsa": 16},
        "fine": {"chime": 8, "dsa": 8},
    }
    assert report["dm"]["absolute_median_delta_pc_cm3"] == pytest.approx(0.002)
    assert report["dm"]["interval_width_ratio"] == pytest.approx(20.0 / 22.0)
    assert report["toas"]["c1"]["absolute_median_delta_ns"] == 300_000
    assert report["run_weight_l1"] == pytest.approx(0.06)
    assert all(len(value) == 64 for value in report["input_sha256"].values())


def test_resolution_convergence_uses_configured_nondefault_threshold(tmp_path) -> None:
    paths = _fixture(tmp_path)
    for key in ("coarse_config", "fine_config"):
        config = json.loads(paths[key].read_text())
        config["joint_fit"]["acceptance"][
            "maximum_resolution_dm_shift_pc_cm3"
        ] = 0.001
        _write(paths[key], config)
    report = _verify(paths)
    assert report["status"] == "failed"
    assert report["thresholds"]["dm_absolute_pc_cm3"] == 0.001
    assert "shared_dispersion_measure" in report["failures"]


@pytest.mark.parametrize(
    ("mutation", "match"),
    [
        (
            lambda values: values["fine_config"]["input_sha256"].__setitem__(
                "raw_dsa_filterbank", _sha("e")
            ),
            "raw input hashes",
        ),
        (
            lambda values: values["fine_config"]["joint_fit"]["sampler"].__setitem__("seed", 43),
            "model, priors, or sampler",
        ),
        (
            lambda values: values["fine_fit"].__setitem__("status", "failed_dm_edge"),
            "provisional accepted",
        ),
        (
            lambda values: values["fine_fit"]["diagnostics"].__setitem__("model_adequate", False),
            "model adequacy",
        ),
        (
            lambda values: values["coarse_config"]["joint_fit"]["resolution"].__setitem__(
                "chime_fit_time_average_factor", 2
            ),
            "time averaging factors",
        ),
        (
            lambda values: values["fine_config"]["joint_fit"]["resolution"].__setitem__(
                "dsa_fit_frequency_average_factor", 4
            ),
            "exactly twice",
        ),
    ],
)
def test_identity_status_factor_and_model_gates_fail_closed(tmp_path, mutation, match) -> None:
    paths = _fixture(tmp_path)
    values = {name: json.loads(path.read_text()) for name, path in paths.items()}
    mutation(values)
    for name, value in values.items():
        _write(paths[name], value)
    with pytest.raises(ValueError, match=match):
        _verify(paths)


def test_receipts_must_bind_config_factor_source_and_fit_input(tmp_path) -> None:
    paths = _fixture(tmp_path)
    receipt = json.loads(paths["fine_chime_receipt"].read_text())
    receipt["output"]["sha256"] = _sha("7")
    _write(paths["fine_chime_receipt"], receipt)
    with pytest.raises(ValueError, match="fit observation hash"):
        _verify(paths)


def test_coarse_and_fine_scientific_code_hashes_must_match(tmp_path) -> None:
    paths = _fixture(tmp_path)
    fine = json.loads(paths["fine_fit"].read_text())
    fine["provenance_code_sha256"]["joint_burst"] = _sha("f")
    _write(paths["fine_fit"], fine)
    with pytest.raises(ValueError, match="different scientific code"):
        _verify(paths)


@pytest.mark.parametrize(
    ("target", "path", "value"),
    [
        ("fine_fit", ("shared_absolute_dm_pc_cm3", "median"), 491.286),
        (
            "fine_fit",
            ("geocentric_unscattered_toa_unix_ns", "c1", "median"),
            1_700_000_000_001_000_000,
        ),
        ("fine_fit", ("shared_absolute_dm_pc_cm3", "lower"), 491.280),
        ("fine_fit", ("diagnostics", "run_weights", "gaussian:c1d1"), 0.40),
    ],
)
def test_convergence_thresholds_emit_failed_report(tmp_path, target, path, value) -> None:
    paths = _fixture(tmp_path)
    payload = json.loads(paths[target].read_text())
    cursor = payload
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = value
    if path[:2] == ("diagnostics", "run_weights"):
        payload["diagnostics"]["run_weights"]["scattering:c1d1"] = 0.60
    _write(paths[target], payload)
    report = _verify(paths)
    assert report["status"] == "failed"
    assert report["passed"] is False
    assert report["failures"]


def test_cli_writes_failure_report_and_returns_nonzero(tmp_path) -> None:
    paths = _fixture(tmp_path)
    fit = json.loads(paths["fine_fit"].read_text())
    fit["shared_absolute_dm_pc_cm3"]["median"] = 491.290
    _write(paths["fine_fit"], fit)
    output = tmp_path / "convergence.json"
    arguments = [
        "--coarse-fit-result",
        str(paths["coarse_fit"]),
        "--fine-fit-result",
        str(paths["fine_fit"]),
        "--coarse-config",
        str(paths["coarse_config"]),
        "--fine-config",
        str(paths["fine_config"]),
        "--coarse-chime-receipt",
        str(paths["coarse_chime_receipt"]),
        "--coarse-dsa-receipt",
        str(paths["coarse_dsa_receipt"]),
        "--fine-chime-receipt",
        str(paths["fine_chime_receipt"]),
        "--fine-dsa-receipt",
        str(paths["fine_dsa_receipt"]),
        "--output",
        str(output),
    ]
    assert main(arguments) == 1
    report = json.loads(output.read_text())
    assert report["status"] == "failed"
    assert report["passed"] is False


def test_input_config_is_never_modified(tmp_path) -> None:
    paths = _fixture(tmp_path)
    before = {name: path.read_bytes() for name, path in paths.items()}
    assert _verify(paths)["passed"]
    assert {name: path.read_bytes() for name, path in paths.items()} == before
