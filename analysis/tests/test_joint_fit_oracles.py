from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
import pytest

from radio_pipeline.fitting import DispersionState
from radio_pipeline.fitting.products import (
    sha256_file,
    write_band_observation_product,
)
from scripts.verify_joint_fit_oracles import verify


def _write_json(path, value) -> None:
    path.write_text(json.dumps(value))


def _fixture(tmp_path):
    event = "injected"
    binding = "a" * 64
    dms = {"lower": 99.9, "median": 100.0, "upper": 100.1}
    fit_path = tmp_path / "fit-result.json"
    _write_json(
        fit_path,
        {
            "status": "provisional_pending_owner_approval",
            "event": event,
            "event_binding_sha256": binding,
            "shared_absolute_dm_pc_cm3": dms,
        },
    )
    rng = np.random.default_rng(4)
    chime_products = {}
    for label, dm in dms.items():
        path = tmp_path / f"chime_fully_coherent_posterior_{label}.npz"
        receipt = write_band_observation_product(
            path,
            instrument="chime",
            waterfall=rng.normal(size=(4, 64)),
            valid=np.ones((4, 64), dtype=bool),
            frequency_mhz=np.linspace(400.0, 800.0, 4),
            channel_width_mhz=0.1,
            sample_interval_s=1.0e-5,
            time0_unix_ns=1_700_000_000_000_000_000,
            dispersion=DispersionState(
                0.0,
                dm,
                0.0,
                dm,
                "singlebeam_h5_fully_coherent",
            ),
            input_sha256={
                "raw_chime_h5": "c" * 64,
                "accepted_chime_reference": "d" * 64,
            },
        )
        chime_products[f"fully_coherent_posterior_{label}"] = {
            "path": str(path),
            "sha256": receipt["sha256"],
        }
    chime_path = tmp_path / "chime_hybrid_result.json"
    _write_json(
        chime_path,
        {
            "burst": event,
            "event_binding_sha256": binding,
            "hybrid_method": {"nonwrapping_fractional_sample_shifts": True},
            "full_coherent_oracle": {
                "role": "joint_posterior_lower_median_upper",
                "dm_pc_cm3": list(dms.values()),
                "passed": True,
                "maximum_normalised_score_absolute_difference": 0.01,
                "absolute_peak_difference_pc_cm3": 0.001,
            },
            "products": chime_products,
        },
    )
    products = {}
    for label, dm in dms.items():
        path = tmp_path / f"dsa_posterior_{label}.npz"
        receipt = write_band_observation_product(
            path,
            instrument="dsa",
            waterfall=rng.normal(size=(4, 64)),
            valid=np.ones((4, 64), dtype=bool),
            frequency_mhz=np.linspace(1300.0, 1500.0, 4),
            channel_width_mhz=1.0,
            sample_interval_s=1.0e-5,
            time0_unix_ns=1_700_000_000_000_000_000,
            dispersion=DispersionState(
                99.8,
                0.0,
                dm - 99.8,
                dm,
                "audited_filterbank_state_plus_fractional_residual",
            ),
            input_sha256={
                "raw_dsa_filterbank": "b" * 64,
                "accepted_dsa_reference": "e" * 64,
            },
        )
        products[f"posterior_{label}"] = {
            "path": str(path),
            "sha256": receipt["sha256"],
        }
    dsa_path = tmp_path / "dsa_hybrid_result.json"
    _write_json(
        dsa_path,
        {
            "burst": event,
            "event_binding_sha256": binding,
            "target_role": "joint_posterior_lower_median_upper",
            "dedispersion": {"nonwrapping_fractional_sample_interpolation": True},
            "products": products,
        },
    )
    config = {
        "event": event,
        "event_binding_sha256": binding,
        "input_sha256": {
            "raw_chime_h5": "c" * 64,
            "accepted_chime_reference": "d" * 64,
            "raw_dsa_filterbank": "b" * 64,
            "accepted_dsa_reference": "e" * 64,
        },
    }
    posterior_path = tmp_path / "posterior.npz"
    np.savez_compressed(
        posterior_path,
        run_weights=np.asarray([1.0]),
        run_0_parameter_names=np.asarray(["absolute_dm_pc_cm3"]),
        run_0_samples=np.asarray([[99.9], [100.0], [100.1], [100.2]]),
        run_0_sample_weights=np.asarray([0.16, 0.34, 0.34, 0.16]),
    )
    model_path = tmp_path / "model-products.npz"
    model_path.write_bytes(b"model")
    geometry_path = tmp_path / "geometry-constraint.json"
    geometry_path.write_text("{}")
    chime_fit_path = tmp_path / "chime-fit-observation.npz"
    dsa_fit_path = tmp_path / "dsa-fit-observation.npz"
    shutil.copyfile(
        chime_products["fully_coherent_posterior_median"]["path"], chime_fit_path
    )
    shutil.copyfile(products["posterior_median"]["path"], dsa_fit_path)
    support = {
        "posterior_path": posterior_path,
        "model_path": model_path,
        "geometry_path": geometry_path,
        "chime_observation_path": chime_fit_path,
        "dsa_observation_path": dsa_fit_path,
    }
    fit = json.loads(fit_path.read_text())
    fit["compact_products"] = {
        "posterior.npz": sha256_file(posterior_path),
        "model-products.npz": sha256_file(model_path),
    }
    fit["fit_inputs"] = {
        "geometry_constraint": sha256_file(geometry_path),
        "chime_observation": sha256_file(support["chime_observation_path"]),
        "dsa_observation": sha256_file(support["dsa_observation_path"]),
    }
    _write_json(fit_path, fit)
    return config, fit_path, chime_path, dsa_path, support


def test_posterior_oracles_require_full_coherent_chime_and_exact_dsa(tmp_path) -> None:
    config, fit_path, chime_path, dsa_path, support = _fixture(tmp_path)
    result = verify(
        config,
        fit_result_path=fit_path,
        chime_result_path=chime_path,
        dsa_result_path=dsa_path,
        **support,
    )
    assert result["status"] == "passed_pending_owner_visual_approval"
    assert result["chime"]["passed"] is True
    assert result["dsa"]["passed"] is True


def test_posterior_oracle_recomputes_dm_quantiles_from_npz(tmp_path) -> None:
    config, fit_path, chime_path, dsa_path, support = _fixture(tmp_path)
    posterior_path = support["posterior_path"]
    with np.load(posterior_path, allow_pickle=False) as posterior:
        payload = {key: posterior[key] for key in posterior.files}
    payload["run_0_samples"] = payload["run_0_samples"] + 1.0
    np.savez_compressed(posterior_path, **payload)
    fit = json.loads(fit_path.read_text())
    fit["compact_products"]["posterior.npz"] = sha256_file(posterior_path)
    _write_json(fit_path, fit)

    with pytest.raises(RuntimeError, match="posterior DM quantiles"):
        verify(
            config,
            fit_result_path=fit_path,
            chime_result_path=chime_path,
            dsa_result_path=dsa_path,
            **support,
        )


@pytest.mark.parametrize(
    "weight_key",
    ["run_weights", "run_0_sample_weights"],
)
def test_posterior_oracle_requires_normalized_weights(tmp_path, weight_key: str) -> None:
    config, fit_path, chime_path, dsa_path, support = _fixture(tmp_path)
    posterior_path = support["posterior_path"]
    with np.load(posterior_path, allow_pickle=False) as posterior:
        payload = {key: posterior[key] for key in posterior.files}
    payload[weight_key] = payload[weight_key] * 0.5
    np.savez_compressed(posterior_path, **payload)
    fit = json.loads(fit_path.read_text())
    fit["compact_products"]["posterior.npz"] = sha256_file(posterior_path)
    _write_json(fit_path, fit)

    with pytest.raises(RuntimeError, match="weights must sum to one"):
        verify(
            config,
            fit_result_path=fit_path,
            chime_result_path=chime_path,
            dsa_result_path=dsa_path,
            **support,
        )


def test_posterior_oracle_rejects_wrong_chime_dm(tmp_path) -> None:
    config, fit_path, chime_path, dsa_path, support = _fixture(tmp_path)
    chime = json.loads(chime_path.read_text())
    chime["full_coherent_oracle"]["dm_pc_cm3"][1] += 0.01
    _write_json(chime_path, chime)
    with pytest.raises(RuntimeError, match="CHIME coherent oracle DMs"):
        verify(
            config,
            fit_result_path=fit_path,
            chime_result_path=chime_path,
            dsa_result_path=dsa_path,
            **support,
        )


def test_posterior_oracle_rejects_false_processing_labels(tmp_path) -> None:
    config, fit_path, chime_path, dsa_path, support = _fixture(tmp_path)
    chime = json.loads(chime_path.read_text())
    receipt = chime["products"]["fully_coherent_posterior_median"]
    product_path = Path(receipt["path"])
    with np.load(product_path, allow_pickle=False) as product:
        payload = {key: product[key] for key in product.files}
    payload["dispersion_mode"] = np.asarray("not_coherent")
    np.savez_compressed(product_path, **payload)
    receipt["sha256"] = sha256_file(product_path)
    _write_json(chime_path, chime)
    with pytest.raises(RuntimeError, match="coherent-only"):
        verify(
            config,
            fit_result_path=fit_path,
            chime_result_path=chime_path,
            dsa_result_path=dsa_path,
            **support,
        )


def test_posterior_oracle_rejects_dsa_coherent_substitution(tmp_path) -> None:
    config, fit_path, chime_path, dsa_path, support = _fixture(tmp_path)
    dsa = json.loads(dsa_path.read_text())
    receipt = dsa["products"]["posterior_median"]
    product_path = Path(receipt["path"])
    with np.load(product_path, allow_pickle=False) as product:
        payload = {key: product[key] for key in product.files}
    payload["dispersion_mode"] = np.asarray("not_residual_only")
    np.savez_compressed(product_path, **payload)
    receipt["sha256"] = sha256_file(product_path)
    _write_json(dsa_path, dsa)
    with pytest.raises(RuntimeError, match="exactly one residual"):
        verify(
            config,
            fit_result_path=fit_path,
            chime_result_path=chime_path,
            dsa_result_path=dsa_path,
            **support,
        )


@pytest.mark.parametrize(
    ("path_key", "message"),
    [
        ("posterior_path", "compact fit product changed"),
        ("geometry_path", "fit input changed"),
        ("chime_observation_path", "fit input changed"),
        ("dsa_observation_path", "fit input changed"),
    ],
)
def test_posterior_oracle_rejects_postfit_tampering(
    tmp_path, path_key: str, message: str
) -> None:
    config, fit_path, chime_path, dsa_path, support = _fixture(tmp_path)
    with support[path_key].open("ab") as stream:
        stream.write(b"tampered-after-fit")
    with pytest.raises(RuntimeError, match=message):
        verify(
            config,
            fit_result_path=fit_path,
            chime_result_path=chime_path,
            dsa_result_path=dsa_path,
            **support,
        )
