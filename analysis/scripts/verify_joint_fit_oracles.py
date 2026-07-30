#!/usr/bin/env python3
"""Fail closed unless posterior-DM products pass both instrument oracles."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from one_event_workflow import load_config

from radio_pipeline.fitting import load_band_observation_product
from radio_pipeline.fitting.products import sha256_file

LABELS = ("lower", "median", "upper")


def _posterior_dm_quantiles(path: Path) -> np.ndarray:
    try:
        with np.load(path, allow_pickle=False) as posterior:
            run_weights = np.asarray(posterior["run_weights"], dtype=float)
            if (
                run_weights.ndim != 1
                or run_weights.size == 0
                or np.any(~np.isfinite(run_weights))
                or np.any(run_weights < 0)
                or float(run_weights.sum()) <= 0
            ):
                raise RuntimeError("posterior run weights are invalid")
            if not np.isclose(
                float(run_weights.sum()),
                1.0,
                rtol=0.0,
                atol=1.0e-8,
            ):
                raise RuntimeError("posterior run weights must sum to one")
            values = []
            weights = []
            for index, run_weight in enumerate(run_weights):
                names = list(posterior[f"run_{index}_parameter_names"])
                if names.count("absolute_dm_pc_cm3") != 1:
                    raise RuntimeError("posterior run lacks one absolute DM parameter")
                samples = np.asarray(posterior[f"run_{index}_samples"], dtype=float)
                sample_weights = np.asarray(
                    posterior[f"run_{index}_sample_weights"], dtype=float
                )
                if (
                    samples.ndim != 2
                    or samples.shape[0] == 0
                    or samples.shape[1] != len(names)
                    or sample_weights.shape != (samples.shape[0],)
                    or np.any(~np.isfinite(samples))
                    or np.any(~np.isfinite(sample_weights))
                    or np.any(sample_weights < 0)
                ):
                    raise RuntimeError("posterior samples or weights are invalid")
                if not np.isclose(
                    float(sample_weights.sum()),
                    1.0,
                    rtol=0.0,
                    atol=1.0e-8,
                ):
                    raise RuntimeError("posterior sample weights must sum to one")
                values.append(samples[:, names.index("absolute_dm_pc_cm3")])
                weights.append(sample_weights * float(run_weight))
    except (KeyError, OSError, ValueError) as exc:
        raise RuntimeError("posterior NPZ cannot be independently read") from exc
    combined_values = np.concatenate(values)
    combined_weights = np.concatenate(weights)
    total_weight = float(combined_weights.sum())
    if total_weight <= 0 or not np.isfinite(total_weight):
        raise RuntimeError("posterior combined weight is invalid")
    order = np.argsort(combined_values)
    sorted_values = combined_values[order]
    cumulative = np.cumsum(combined_weights[order]) / total_weight
    return np.interp((0.16, 0.5, 0.84), cumulative, sorted_values)


def verify(
    config: dict,
    *,
    fit_result_path: Path,
    chime_result_path: Path,
    dsa_result_path: Path,
    posterior_path: Path,
    model_path: Path,
    geometry_path: Path,
    chime_observation_path: Path,
    dsa_observation_path: Path,
) -> dict:
    fit = json.loads(fit_result_path.read_text())
    chime = json.loads(chime_result_path.read_text())
    dsa = json.loads(dsa_result_path.read_text())
    event = config["event"]
    binding = config["event_binding_sha256"]
    if fit["event"] != event or chime["burst"] != event or dsa["burst"] != event:
        raise ValueError("oracle inputs refer to different events")
    if any(value["event_binding_sha256"] != binding for value in (fit, chime, dsa)):
        raise ValueError("oracle input binding changed")
    if fit["status"] != "provisional_pending_owner_approval":
        raise RuntimeError("failed fit cannot enter physical oracle verification")

    expected_compact_products = {
        "posterior.npz": sha256_file(posterior_path),
        "model-products.npz": sha256_file(model_path),
    }
    if fit.get("compact_products") != expected_compact_products:
        raise RuntimeError("compact fit product changed after inference")
    expected_fit_inputs = {
        "geometry_constraint": sha256_file(geometry_path),
        "chime_observation": sha256_file(chime_observation_path),
        "dsa_observation": sha256_file(dsa_observation_path),
    }
    if fit.get("fit_inputs") != expected_fit_inputs:
        raise RuntimeError("fit input changed after inference")

    summary = fit["shared_absolute_dm_pc_cm3"]
    recorded = np.asarray([summary["lower"], summary["median"], summary["upper"]], dtype=float)
    expected = _posterior_dm_quantiles(posterior_path)
    if not np.allclose(expected, recorded, rtol=0.0, atol=1.0e-10):
        raise RuntimeError("posterior DM quantiles disagree with fit result")
    chime_oracle = chime["full_coherent_oracle"]
    actual_chime = np.asarray(chime_oracle["dm_pc_cm3"], dtype=float)
    if chime_oracle.get("role") != "joint_posterior_lower_median_upper":
        raise RuntimeError("CHIME oracle did not evaluate the joint posterior")
    if not np.allclose(actual_chime, expected, rtol=0.0, atol=1.0e-10):
        raise RuntimeError("CHIME coherent oracle DMs changed")
    if not chime_oracle.get("passed", False):
        raise RuntimeError("CHIME coherent oracle failed")
    if not chime.get("hybrid_method", {}).get("nonwrapping_fractional_sample_shifts", False):
        raise RuntimeError("CHIME non-wrapping processing identity is absent")
    expected_chime_hashes = {
        "raw_chime_h5": config["input_sha256"]["raw_chime_h5"],
        "accepted_chime_reference": config["input_sha256"]["accepted_chime_reference"],
    }
    chime_products = {}
    for label, target_dm in zip(LABELS, expected, strict=True):
        key = f"fully_coherent_posterior_{label}"
        receipt = chime["products"].get(key)
        if receipt is None:
            raise RuntimeError(f"CHIME oracle lacks {key}")
        product_path = Path(receipt["path"])
        product_sha256 = sha256_file(product_path)
        if receipt.get("sha256") != product_sha256:
            raise RuntimeError(f"CHIME {key} receipt hash changed")
        observation = load_band_observation_product(product_path)
        if observation.instrument != "chime":
            raise RuntimeError("CHIME oracle product has the wrong instrument")
        if not np.isclose(
            observation.dispersion.product_dm_pc_cm3,
            target_dm,
            rtol=0.0,
            atol=1.0e-10,
        ):
            raise RuntimeError(f"CHIME {key} DM changed")
        if observation.reference_frequency_mhz != 400.0:
            raise RuntimeError("CHIME oracle reference frequency changed")
        if observation.input_sha256 != expected_chime_hashes:
            raise RuntimeError("CHIME oracle input identity changed")
        state = observation.dispersion
        if (
            state.mode != "singlebeam_h5_fully_coherent"
            or not np.isclose(
                state.coherent_correction_pc_cm3,
                target_dm - state.input_dm_pc_cm3,
                rtol=0.0,
                atol=1.0e-10,
            )
            or state.incoherent_correction_pc_cm3 != 0.0
        ):
            raise RuntimeError("CHIME oracle is not a coherent-only rerun")
        chime_products[key] = {
            "path": str(product_path),
            "sha256": product_sha256,
            "product_dm_pc_cm3": target_dm,
            "input_dm_pc_cm3": observation.dispersion.input_dm_pc_cm3,
            "coherent_correction_pc_cm3": (observation.dispersion.coherent_correction_pc_cm3),
            "valid_pixel_count": int(observation.valid.sum()),
        }

    if not dsa.get("dedispersion", {}).get("nonwrapping_fractional_sample_interpolation", False):
        raise RuntimeError("DSA non-wrapping processing identity is absent")
    expected_dsa_hashes = {
        "raw_dsa_filterbank": config["input_sha256"]["raw_dsa_filterbank"],
        "accepted_dsa_reference": config["input_sha256"]["accepted_dsa_reference"],
    }
    dsa_products = {}
    for label, target_dm in zip(LABELS, expected, strict=True):
        key = f"posterior_{label}"
        receipt = dsa["products"].get(key)
        if receipt is None:
            raise RuntimeError(f"DSA oracle lacks {key}")
        product_path = Path(receipt["path"])
        product_sha256 = sha256_file(product_path)
        if receipt.get("sha256") != product_sha256:
            raise RuntimeError(f"DSA {key} receipt hash changed")
        observation = load_band_observation_product(product_path)
        if observation.instrument != "dsa":
            raise RuntimeError("DSA oracle product has the wrong instrument")
        if not np.isclose(
            observation.dispersion.product_dm_pc_cm3,
            target_dm,
            rtol=0.0,
            atol=1.0e-10,
        ):
            raise RuntimeError(f"DSA {key} DM changed")
        if observation.reference_frequency_mhz != 400.0:
            raise RuntimeError("DSA oracle reference frequency changed")
        if observation.input_sha256 != expected_dsa_hashes:
            raise RuntimeError("DSA oracle input identity changed")
        state = observation.dispersion
        if (
            state.mode != "audited_filterbank_state_plus_fractional_residual"
            or state.coherent_correction_pc_cm3 != 0.0
            or not np.isclose(
                state.incoherent_correction_pc_cm3,
                target_dm - state.input_dm_pc_cm3,
                rtol=0.0,
                atol=1.0e-10,
            )
        ):
            raise RuntimeError("DSA oracle is not exactly one residual correction")
        dsa_products[key] = {
            "path": str(product_path),
            "sha256": product_sha256,
            "product_dm_pc_cm3": target_dm,
            "input_dm_pc_cm3": observation.dispersion.input_dm_pc_cm3,
            "applied_residual_dm_pc_cm3": (observation.dispersion.incoherent_correction_pc_cm3),
            "valid_pixel_count": int(observation.valid.sum()),
        }
    if dsa.get("target_role") != "joint_posterior_lower_median_upper":
        raise RuntimeError("DSA oracle did not evaluate the joint posterior")

    return {
        "schema_version": 1,
        "status": "passed_pending_owner_visual_approval",
        "event": event,
        "event_binding_sha256": binding,
        "reference_frequency_mhz": 400.0,
        "posterior_dm_pc_cm3": dict(zip(LABELS, map(float, expected), strict=True)),
        "consumed_inputs": {
            "fit_result": sha256_file(fit_result_path),
            "posterior": sha256_file(posterior_path),
            "model_products": sha256_file(model_path),
            "geometry_constraint": sha256_file(geometry_path),
            "chime_fit_observation": sha256_file(chime_observation_path),
            "dsa_fit_observation": sha256_file(dsa_observation_path),
            "chime_posterior_observation": chime_products["fully_coherent_posterior_median"][
                "sha256"
            ],
            "dsa_posterior_observation": dsa_products["posterior_median"]["sha256"],
        },
        "chime": {
            "method": "full coherent singlebeam H5 rerun",
            "result_path": str(chime_result_path),
            "result_sha256": sha256_file(chime_result_path),
            "maximum_normalised_score_absolute_difference": chime_oracle[
                "maximum_normalised_score_absolute_difference"
            ],
            "absolute_peak_difference_pc_cm3": chime_oracle["absolute_peak_difference_pc_cm3"],
            "products": chime_products,
            "passed": True,
        },
        "dsa": {
            "method": "audited raw filterbank plus one non-wrapping residual correction",
            "result_path": str(dsa_result_path),
            "result_sha256": sha256_file(dsa_result_path),
            "products": dsa_products,
            "passed": True,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--fit-result", type=Path, required=True)
    parser.add_argument("--chime-result", type=Path, required=True)
    parser.add_argument("--dsa-result", type=Path, required=True)
    parser.add_argument("--posterior", type=Path, required=True)
    parser.add_argument("--model-products", type=Path, required=True)
    parser.add_argument("--geometry-constraint", type=Path, required=True)
    parser.add_argument("--chime-observation", type=Path, required=True)
    parser.add_argument("--dsa-observation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify(
        load_config(args.config),
        fit_result_path=args.fit_result,
        chime_result_path=args.chime_result,
        dsa_result_path=args.dsa_result,
        posterior_path=args.posterior,
        model_path=args.model_products,
        geometry_path=args.geometry_constraint,
        chime_observation_path=args.chime_observation,
        dsa_observation_path=args.dsa_observation,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
