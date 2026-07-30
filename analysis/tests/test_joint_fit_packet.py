from __future__ import annotations

import json
from types import SimpleNamespace

import matplotlib.pyplot as plt
import numpy as np
import pytest

from radio_pipeline.fitting import DispersionState
from radio_pipeline.fitting.products import (
    sha256_file,
    write_band_observation_product,
)
from scripts.render_joint_fit_packet import _image, render


def test_packet_image_uses_nonuniform_channel_edges_and_row_order() -> None:
    observation = SimpleNamespace(
        waterfall=np.asarray([[3.0, 3.0], [2.0, 2.0], [1.0, 1.0]]),
        valid=np.ones((3, 2), dtype=bool),
        frequency_mhz=np.asarray([440.0, 420.0, 410.0]),
        channel_width_mhz=np.asarray([30.0, 10.0, 10.0]),
        sample_interval_s=1.0e-3,
    )
    figure, ax = plt.subplots()
    _image(ax, observation.waterfall, observation, "injected")

    mesh = ax.collections[0]
    np.testing.assert_allclose(
        mesh.get_coordinates()[:, 0, 1],
        [405.0, 415.0, 425.0, 455.0],
    )
    np.testing.assert_allclose(
        np.asarray(mesh.get_array()),
        [[1.0, 1.0], [2.0, 2.0], [3.0, 3.0]],
    )
    plt.close(figure)


def test_packet_image_renders_missing_frequency_gap_as_masked_cell() -> None:
    observation = SimpleNamespace(
        waterfall=np.asarray([[2.0, 2.0], [1.0, 1.0]]),
        valid=np.ones((2, 2), dtype=bool),
        frequency_mhz=np.asarray([430.0, 410.0]),
        channel_width_mhz=np.asarray([10.0, 10.0]),
        sample_interval_s=1.0e-3,
    )
    figure, ax = plt.subplots()
    _image(ax, observation.waterfall, observation, "gap")

    mesh = ax.collections[0]
    np.testing.assert_allclose(
        mesh.get_coordinates()[:, 0, 1],
        [405.0, 415.0, 425.0, 435.0],
    )
    rendered = np.ma.asarray(mesh.get_array())
    np.testing.assert_allclose(rendered[[0, 2]], [[1.0, 1.0], [2.0, 2.0]])
    assert np.ma.getmaskarray(rendered)[1].all()
    plt.close(figure)


def test_review_packet_regenerates_as_pdf_only(tmp_path) -> None:
    rng = np.random.default_rng(8)
    product_paths = {}
    for instrument, frequency, channel_width in (
        (
            "chime",
            np.asarray([410.0, 430.0, 470.0, 530.0]),
            np.asarray([20.0, 20.0, 60.0, 60.0]),
        ),
        (
            "dsa",
            np.asarray([1310.0, 1340.0, 1400.0, 1490.0]),
            np.asarray([30.0, 30.0, 90.0, 90.0]),
        ),
    ):
        path = tmp_path / f"{instrument}.npz"
        write_band_observation_product(
            path,
            instrument=instrument,
            waterfall=rng.normal(size=(4, 64)),
            valid=np.ones((4, 64), dtype=bool),
            frequency_mhz=frequency,
            channel_width_mhz=channel_width,
            sample_interval_s=1.0e-5,
            time0_unix_ns=1_700_000_000_000_000_000,
            dispersion=DispersionState(0.0, 100.0, 0.0, 100.0, "injected"),
            input_sha256={"source": "a" * 64},
        )
        product_paths[instrument] = path
    fit_path = tmp_path / "fit-result.json"
    fit_path.write_text(
        json.dumps(
            {
                "status": "provisional_pending_owner_approval",
                "event": "injected",
                "shared_absolute_dm_pc_cm3": {
                    "median": 100.0,
                    "error_plus": 0.01,
                    "error_minus": 0.01,
                },
                "diagnostics": {
                    "posterior_dm_at_edge": False,
                    "model_adequate": True,
                    "run_weights": {"gaussian:one": 1.0},
                },
            }
        )
    )
    parameter_names = np.asarray(
        [
            "absolute_dm_pc_cm3",
            "timing_error_chime_s",
            "timing_error_dsa_s",
        ]
    )
    samples = np.column_stack(
        (
            np.linspace(99.98, 100.02, 32),
            np.linspace(-1.0e-6, 1.0e-6, 32),
            np.zeros(32),
        )
    )
    posterior_path = tmp_path / "posterior.npz"
    np.savez_compressed(
        posterior_path,
        run_weights=np.asarray([1.0]),
        run_0_parameter_names=parameter_names,
        run_0_samples=samples,
        run_0_sample_weights=np.full(32, 1.0 / 32.0),
    )
    model_path = tmp_path / "model-products.npz"
    np.savez_compressed(
        model_path,
        chime_model=np.zeros((4, 64)),
        chime_residual=np.zeros((4, 64)),
        dsa_model=np.zeros((4, 64)),
        dsa_residual=np.zeros((4, 64)),
    )
    geometry_path = tmp_path / "geometry-constraint.json"
    geometry_path.write_text(json.dumps({"projection_disagreement_s": 1.0e-9}))
    oracle_path = tmp_path / "oracle-verification.json"
    oracle_path.write_text(
        json.dumps(
            {
                "status": "passed_pending_owner_visual_approval",
                "consumed_inputs": {
                    "fit_result": sha256_file(fit_path),
                    "posterior": sha256_file(posterior_path),
                    "model_products": sha256_file(model_path),
                    "geometry_constraint": sha256_file(geometry_path),
                    "chime_fit_observation": sha256_file(product_paths["chime"]),
                    "dsa_fit_observation": sha256_file(product_paths["dsa"]),
                    "chime_posterior_observation": sha256_file(product_paths["chime"]),
                    "dsa_posterior_observation": sha256_file(product_paths["dsa"]),
                },
            }
        )
    )
    convergence_path = tmp_path / "resolution-convergence.json"
    convergence_inputs = {"coarse_fit_result": fit_path}
    for name in (
        "fine_fit_result",
        "coarse_config",
        "fine_config",
        "coarse_chime_receipt",
        "coarse_dsa_receipt",
        "fine_chime_receipt",
        "fine_dsa_receipt",
    ):
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps({"name": name}))
        convergence_inputs[name] = path
    convergence_hashes = {
        name: sha256_file(path) for name, path in convergence_inputs.items()
    }
    convergence_path.write_text(
        json.dumps(
            {
                "status": "passed",
                "passed": True,
                "event": "injected",
                "input_sha256": convergence_hashes,
            }
        )
    )
    output = tmp_path / "review-packet.pdf"
    render(
        chime_path=product_paths["chime"],
        dsa_path=product_paths["dsa"],
        chime_posterior_path=product_paths["chime"],
        dsa_posterior_path=product_paths["dsa"],
        fit_result_path=fit_path,
        posterior_path=posterior_path,
        model_path=model_path,
        geometry_path=geometry_path,
        oracle_path=oracle_path,
        resolution_convergence_path=convergence_path,
        resolution_convergence_inputs=convergence_inputs,
        output=output,
    )
    assert output.read_bytes().startswith(b"%PDF-")
    assert not list(tmp_path.glob("*.svg"))
    assert not list(tmp_path.glob("*.png"))
    convergence_path.write_text(json.dumps({"status": "failed", "passed": False}))
    with pytest.raises(RuntimeError, match="fit-resolution convergence"):
        render(
            chime_path=product_paths["chime"],
            dsa_path=product_paths["dsa"],
            chime_posterior_path=product_paths["chime"],
            dsa_posterior_path=product_paths["dsa"],
            fit_result_path=fit_path,
            posterior_path=posterior_path,
            model_path=model_path,
            geometry_path=geometry_path,
            oracle_path=oracle_path,
            resolution_convergence_path=convergence_path,
            resolution_convergence_inputs=convergence_inputs,
            output=output,
        )
    convergence_path.write_text(
        json.dumps(
            {
                "status": "passed",
                "passed": True,
                "event": "injected",
                "input_sha256": {"coarse_fit_result": sha256_file(fit_path)},
            }
        )
    )
    with pytest.raises(RuntimeError, match="input binding is incomplete"):
        render(
            chime_path=product_paths["chime"],
            dsa_path=product_paths["dsa"],
            chime_posterior_path=product_paths["chime"],
            dsa_posterior_path=product_paths["dsa"],
            fit_result_path=fit_path,
            posterior_path=posterior_path,
            model_path=model_path,
            geometry_path=geometry_path,
            oracle_path=oracle_path,
            resolution_convergence_path=convergence_path,
            resolution_convergence_inputs=convergence_inputs,
            output=output,
        )
    convergence_path.write_text(
        json.dumps(
            {
                "status": "passed",
                "passed": True,
                "event": "injected",
                "input_sha256": convergence_hashes,
            }
        )
    )
    fit_path.write_text("{}")
    with pytest.raises(RuntimeError, match="fit_result"):
        render(
            chime_path=product_paths["chime"],
            dsa_path=product_paths["dsa"],
            chime_posterior_path=product_paths["chime"],
            dsa_posterior_path=product_paths["dsa"],
            fit_result_path=fit_path,
            posterior_path=posterior_path,
            model_path=model_path,
            geometry_path=geometry_path,
            oracle_path=oracle_path,
            resolution_convergence_path=convergence_path,
            resolution_convergence_inputs=convergence_inputs,
            output=output,
        )


def test_review_packet_rejects_non_pdf_output(tmp_path) -> None:
    with pytest.raises(ValueError, match=r"\.pdf extension"):
        render(
            chime_path=tmp_path / "unused",
            dsa_path=tmp_path / "unused",
            chime_posterior_path=tmp_path / "unused",
            dsa_posterior_path=tmp_path / "unused",
            fit_result_path=tmp_path / "unused",
            posterior_path=tmp_path / "unused",
            model_path=tmp_path / "unused",
            geometry_path=tmp_path / "unused",
            oracle_path=tmp_path / "unused",
            resolution_convergence_path=tmp_path / "unused",
            resolution_convergence_inputs={},
            output=tmp_path / "review-packet.svg",
        )
