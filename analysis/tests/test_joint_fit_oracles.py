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
from scripts.one_event_hybrid_dm import score_crop
from scripts.verify_joint_fit_oracles import verify


def _write_json(path, value) -> None:
    path.write_text(json.dumps(value))


def _apply_residual(
    waterfall: np.ndarray,
    frequency_mhz: np.ndarray,
    sample_interval_s: float,
    residual_dm_pc_cm3: float,
) -> np.ndarray:
    sample = np.arange(waterfall.shape[1], dtype=float)
    shift = (
        -4148.808
        * residual_dm_pc_cm3
        * (frequency_mhz**-2 - 400.0**-2)
        / sample_interval_s
    )
    return np.asarray(
        [
            np.interp(sample - row_shift, sample, row, left=np.nan, right=np.nan)
            for row, row_shift in zip(waterfall, shift, strict=True)
        ]
    )


def _burst_waterfall(
    rng: np.random.Generator,
    frequency_mhz: np.ndarray,
    ntime: int,
) -> np.ndarray:
    sample = np.arange(ntime, dtype=float)
    noise = rng.normal(scale=0.25, size=(frequency_mhz.size, ntime))
    pulse = np.exp(-0.5 * ((sample - 0.52 * ntime) / 3.0) ** 2)
    spectrum = 1.0 + 0.25 * np.sin(np.linspace(0.0, np.pi, frequency_mhz.size))
    return noise + 5.0 * spectrum[:, None] * pulse[None, :]


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
    sample_interval_s = 1.0e-3
    chime_frequency = np.linspace(400.0, 800.0, 20)
    chime_anchor_waterfall = _burst_waterfall(rng, chime_frequency, 256)
    chime_products = {}
    chime_rows = []
    for label, dm in dms.items():
        path = tmp_path / f"chime_fully_coherent_posterior_{label}.npz"
        waterfall = _apply_residual(
            chime_anchor_waterfall,
            chime_frequency,
            sample_interval_s,
            dm - dms["median"],
        )
        frequency_id = np.arange(20)
        receipt = write_band_observation_product(
            path,
            instrument="chime",
            waterfall=waterfall,
            valid=np.isfinite(waterfall),
            frequency_mhz=chime_frequency,
            channel_width_mhz=0.1,
            sample_interval_s=sample_interval_s,
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
            extra={
                "fine_frequency_id": frequency_id,
                "residual_shift_frequency_mhz": chime_frequency,
            },
        )
        chime_rows.append(
            score_crop(waterfall, sample_interval_s, frequency_id=frequency_id)
        )
        chime_products[f"fully_coherent_posterior_{label}"] = {
            "path": str(path),
            "sha256": receipt["sha256"],
        }
    with np.load(
        chime_products["fully_coherent_posterior_median"]["path"],
        allow_pickle=False,
    ) as anchor_product:
        stored_chime_anchor = np.asarray(anchor_product["waterfall"], dtype=float)
    chime_hybrid_rows = []
    for dm in dms.values():
        hybrid = _apply_residual(
            stored_chime_anchor,
            chime_frequency,
            sample_interval_s,
            dm - dms["median"],
        )
        chime_hybrid_rows.append(
            score_crop(hybrid, sample_interval_s, frequency_id=np.arange(20))
        )
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
                "selected_cutoff_hz": 2500.0,
                "hybrid_rows": chime_hybrid_rows,
                "fully_coherent_rows": chime_rows,
                "hybrid_normalised_score": (
                    np.asarray(
                        [row["score"]["2500.0"] for row in chime_hybrid_rows]
                    )
                    / chime_hybrid_rows[1]["score"]["2500.0"]
                ).tolist(),
                "fully_coherent_normalised_score": (
                    np.asarray([row["score"]["2500.0"] for row in chime_rows])
                    / chime_rows[1]["score"]["2500.0"]
                ).tolist(),
                "passed": True,
                "maximum_normalised_score_absolute_difference": 0.01,
                "normalised_curve_tolerance": 0.1,
                "absolute_peak_difference_pc_cm3": 0.001,
            },
            "products": chime_products,
        },
    )
    products = {}
    dsa_frequency = np.linspace(1300.0, 1500.0, 12)
    dsa_anchor_waterfall = _burst_waterfall(rng, dsa_frequency, 256)
    for label, dm in dms.items():
        path = tmp_path / f"dsa_posterior_{label}.npz"
        waterfall = _apply_residual(
            dsa_anchor_waterfall,
            dsa_frequency,
            sample_interval_s,
            dm - dms["median"],
        )
        receipt = write_band_observation_product(
            path,
            instrument="dsa",
            waterfall=waterfall,
            valid=np.isfinite(waterfall),
            frequency_mhz=dsa_frequency,
            channel_width_mhz=1.0,
            sample_interval_s=sample_interval_s,
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
        "chime": {
            "gates": {
                "oracle_normalised_curve_max_abs_difference": 0.1,
            }
        },
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


def test_posterior_oracle_rejects_target_support_loss(tmp_path) -> None:
    config, fit_path, chime_path, dsa_path, support = _fixture(tmp_path)
    dsa = json.loads(dsa_path.read_text())
    receipt = dsa["products"]["posterior_lower"]
    product_path = Path(receipt["path"])
    with np.load(product_path, allow_pickle=False) as product:
        payload = {key: product[key] for key in product.files}
    payload["pixel_valid"] = np.asarray(payload["pixel_valid"], dtype=bool)
    payload["pixel_valid"][4:] = False
    payload["noise_estimation_mask"] = np.asarray(
        payload["noise_estimation_mask"], dtype=bool
    )
    payload["noise_estimation_mask"][4:] = False
    payload["waterfall"] = np.asarray(payload["waterfall"])
    payload["waterfall"][4:] = np.nan
    np.savez_compressed(product_path, **payload)
    receipt["sha256"] = sha256_file(product_path)
    _write_json(dsa_path, dsa)
    with pytest.raises(RuntimeError, match="numerical residual correction"):
        verify(
            config,
            fit_result_path=fit_path,
            chime_result_path=chime_path,
            dsa_result_path=dsa_path,
            **support,
        )


def test_posterior_oracle_rejects_mutable_upstream_tolerance(tmp_path) -> None:
    config, fit_path, chime_path, dsa_path, support = _fixture(tmp_path)
    chime = json.loads(chime_path.read_text())
    chime["full_coherent_oracle"]["normalised_curve_tolerance"] = 1.0e9
    _write_json(chime_path, chime)
    with pytest.raises(RuntimeError, match="reviewed configuration"):
        verify(
            config,
            fit_result_path=fit_path,
            chime_result_path=chime_path,
            dsa_result_path=dsa_path,
            **support,
        )


def test_posterior_oracle_rejects_random_arrays_with_forged_metadata(tmp_path) -> None:
    config, fit_path, chime_path, dsa_path, support = _fixture(tmp_path)
    chime = json.loads(chime_path.read_text())
    rng = np.random.default_rng(912)
    for receipt in chime["products"].values():
        product_path = Path(receipt["path"])
        with np.load(product_path, allow_pickle=False) as product:
            payload = {key: product[key] for key in product.files}
        payload["waterfall"] = rng.normal(size=payload["waterfall"].shape).astype(np.float32)
        np.savez_compressed(product_path, **payload)
        receipt["sha256"] = sha256_file(product_path)
    _write_json(chime_path, chime)

    with pytest.raises(RuntimeError, match="numerical"):
        verify(
            config,
            fit_result_path=fit_path,
            chime_result_path=chime_path,
            dsa_result_path=dsa_path,
            **support,
        )


def test_posterior_oracle_rejects_dsa_pixels_unrelated_to_declared_residual(
    tmp_path,
) -> None:
    config, fit_path, chime_path, dsa_path, support = _fixture(tmp_path)
    dsa = json.loads(dsa_path.read_text())
    rng = np.random.default_rng(614)
    for receipt in dsa["products"].values():
        product_path = Path(receipt["path"])
        with np.load(product_path, allow_pickle=False) as product:
            payload = {key: product[key] for key in product.files}
        payload["waterfall"] = rng.normal(size=payload["waterfall"].shape).astype(np.float32)
        np.savez_compressed(product_path, **payload)
        receipt["sha256"] = sha256_file(product_path)
    _write_json(dsa_path, dsa)

    with pytest.raises(RuntimeError, match="DSA numerical residual"):
        verify(
            config,
            fit_result_path=fit_path,
            chime_result_path=chime_path,
            dsa_result_path=dsa_path,
            **support,
        )


def test_posterior_oracle_rejects_wrong_sign_dsa_pixels_with_correct_labels(
    tmp_path,
) -> None:
    config, fit_path, chime_path, dsa_path, support = _fixture(tmp_path)
    dsa = json.loads(dsa_path.read_text())
    anchor_path = support["dsa_observation_path"]
    with np.load(anchor_path, allow_pickle=False) as anchor_product:
        anchor = np.asarray(anchor_product["waterfall"], dtype=float)
        frequency = np.asarray(anchor_product["frequency_mhz"], dtype=float)
        sample_interval_s = float(anchor_product["sample_interval_s"])
        anchor_dm = float(anchor_product["product_dm_pc_cm3"])
    receipt = dsa["products"]["posterior_lower"]
    product_path = Path(receipt["path"])
    with np.load(product_path, allow_pickle=False) as product:
        payload = {key: product[key] for key in product.files}
        target_dm = float(product["product_dm_pc_cm3"])
    wrong_sign = _apply_residual(
        anchor,
        frequency,
        sample_interval_s,
        -(target_dm - anchor_dm),
    ).astype(np.float32)
    payload["waterfall"] = wrong_sign
    payload["pixel_valid"] = np.asarray(payload["pixel_valid"], dtype=bool) & np.isfinite(
        wrong_sign
    )
    payload["noise_estimation_mask"] = (
        np.asarray(payload["noise_estimation_mask"], dtype=bool) & payload["pixel_valid"]
    )
    np.savez_compressed(product_path, **payload)
    receipt["sha256"] = sha256_file(product_path)
    _write_json(dsa_path, dsa)

    with pytest.raises(RuntimeError, match="DSA numerical residual"):
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
