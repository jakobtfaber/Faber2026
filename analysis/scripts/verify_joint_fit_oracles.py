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
K_DM_S_MHZ2 = 4148.808
MINIMUM_RESIDUAL_PROFILE_CORRELATION = 0.50
MINIMUM_DSA_RESIDUAL_PROFILE_CORRELATION = 0.80
MINIMUM_DSA_RESIDUAL_ROW_CORRELATION = 0.80
MAXIMUM_PROFILE_PEAK_SEPARATION_SAMPLES = 8
MAXIMUM_DSA_PROFILE_PEAK_SEPARATION_SAMPLES = 2
MINIMUM_COMMON_VALID_PIXEL_FRACTION = 0.80


def _phase_coherence_score(
    values: np.ndarray,
    valid: np.ndarray,
    *,
    sample_interval_s: float,
    frequency_id: np.ndarray,
    cutoff_hz: float,
) -> tuple[float, int]:
    """Recompute the CHIME phase-coherence objective from saved pixels."""

    masked = np.where(valid, values, np.nan)
    finite_fraction = np.isfinite(masked).mean(axis=1)
    median = np.nanmedian(masked, axis=1)
    mad = np.nanmedian(np.abs(masked - median[:, None]), axis=1)
    sigma = 1.4826 * mad
    use_row = (finite_fraction >= 0.90) & np.isfinite(sigma) & (sigma > 0)
    if int(use_row.sum()) < 4:
        raise RuntimeError("CHIME numerical oracle has too few usable channels")
    identifiers = np.asarray(frequency_id)
    if identifiers.shape != (masked.shape[0],):
        raise RuntimeError("CHIME numerical oracle frequency identifiers changed")
    order = np.argsort(identifiers[use_row])
    standardized = np.nan_to_num(
        (masked[use_row] - median[use_row, None]) / sigma[use_row, None]
    )[order]
    spectrum = np.fft.rfft(standardized, axis=1)
    amplitude = np.abs(spectrum)
    phase = np.divide(
        spectrum,
        amplitude,
        out=np.zeros_like(spectrum),
        where=amplitude > np.finfo(float).tiny,
    )
    fluctuation_hz = np.fft.rfftfreq(
        standardized.shape[1], sample_interval_s
    )
    use_frequency = (fluctuation_hz >= 50.0) & (fluctuation_hz <= cutoff_hz)
    weight = fluctuation_hz[use_frequency] ** 2
    coherent = np.sum(phase[:, use_frequency], axis=0)
    return float(np.sum(np.abs(coherent) ** 2 * weight)), int(use_row.sum())


def _npz_array(path: Path, key: str) -> np.ndarray:
    with np.load(path, allow_pickle=False) as archive:
        if key not in archive.files:
            raise RuntimeError(f"numerical oracle product lacks {key}")
        return np.asarray(archive[key])


def _fractional_residual_shift(
    values: np.ndarray,
    valid: np.ndarray,
    *,
    frequency_mhz: np.ndarray,
    sample_interval_s: float,
    residual_dm_pc_cm3: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Apply an independent non-wrapping residual correction."""

    data = np.asarray(values, dtype=float)
    mask = np.asarray(valid, dtype=bool)
    frequency = np.asarray(frequency_mhz, dtype=float)
    if data.ndim != 2 or mask.shape != data.shape or frequency.shape != (data.shape[0],):
        raise RuntimeError("numerical residual oracle dimensions changed")
    if (
        sample_interval_s <= 0
        or np.any(~np.isfinite(frequency))
        or np.any(frequency <= 0)
    ):
        raise RuntimeError("numerical residual oracle coordinates changed")
    shift_samples = (
        -K_DM_S_MHZ2
        * float(residual_dm_pc_cm3)
        * (frequency**-2 - 400.0**-2)
        / float(sample_interval_s)
    )
    sample = np.arange(data.shape[1], dtype=float)
    shifted = np.full(data.shape, np.nan, dtype=float)
    shifted_support = np.zeros(data.shape, dtype=bool)
    for row, shift in enumerate(shift_samples):
        coordinate = sample - shift
        shifted[row] = np.interp(
            coordinate,
            sample,
            data[row],
            left=np.nan,
            right=np.nan,
        )
        shifted_support[row] = (
            np.interp(
                coordinate,
                sample,
                mask[row].astype(float),
                left=0.0,
                right=0.0,
            )
            >= 1.0 - 1.0e-12
        )
    return shifted, shifted_support & np.isfinite(shifted)


def _standardize_rows(values: np.ndarray, valid: np.ndarray) -> np.ndarray:
    masked = np.where(valid, values, np.nan)
    median = np.nanmedian(masked, axis=1)
    mad = np.nanmedian(np.abs(masked - median[:, None]), axis=1)
    scale = 1.4826 * mad
    usable = np.isfinite(scale) & (scale > 0)
    output = np.full(masked.shape, np.nan, dtype=float)
    output[usable] = (masked[usable] - median[usable, None]) / scale[usable, None]
    return output


def _residual_numerical_agreement(
    anchor,
    target,
    *,
    shift_frequency_mhz: np.ndarray,
    residual_dm_pc_cm3: float,
) -> dict[str, float]:
    """Compare saved target pixels with an independently shifted anchor."""

    if (
        anchor.waterfall.shape != target.waterfall.shape
        or not np.array_equal(anchor.frequency_mhz, target.frequency_mhz)
        or anchor.sample_interval_s != target.sample_interval_s
        or anchor.time0_unix_ns != target.time0_unix_ns
    ):
        raise RuntimeError("numerical residual oracle grid changed")
    predicted, predicted_valid = _fractional_residual_shift(
        anchor.waterfall,
        anchor.valid,
        frequency_mhz=shift_frequency_mhz,
        sample_interval_s=anchor.sample_interval_s,
        residual_dm_pc_cm3=residual_dm_pc_cm3,
    )
    common = predicted_valid & target.valid
    predicted_z = _standardize_rows(predicted, common)
    target_z = _standardize_rows(target.waterfall, common)
    row_correlation = []
    for row in range(common.shape[0]):
        use = common[row] & np.isfinite(predicted_z[row]) & np.isfinite(target_z[row])
        if int(use.sum()) < 16:
            continue
        correlation = float(np.corrcoef(predicted_z[row, use], target_z[row, use])[0, 1])
        if np.isfinite(correlation):
            row_correlation.append(correlation)
    if len(row_correlation) < 4:
        raise RuntimeError("numerical residual oracle has too few comparable rows")
    time_support = np.sum(common, axis=0)
    use_time = time_support >= max(4, int(0.5 * np.max(time_support)))
    predicted_sum = np.nansum(np.where(common, predicted_z, np.nan), axis=0)
    target_sum = np.nansum(np.where(common, target_z, np.nan), axis=0)
    predicted_profile = np.divide(
        predicted_sum,
        time_support,
        out=np.full(time_support.shape, np.nan, dtype=float),
        where=time_support > 0,
    )
    target_profile = np.divide(
        target_sum,
        time_support,
        out=np.full(time_support.shape, np.nan, dtype=float),
        where=time_support > 0,
    )
    profile_correlation = float(
        np.corrcoef(predicted_profile[use_time], target_profile[use_time])[0, 1]
    )
    predicted_peak = int(np.nanargmax(np.where(use_time, predicted_profile, np.nan)))
    target_peak = int(np.nanargmax(np.where(use_time, target_profile, np.nan)))
    return {
        "median_row_correlation": float(np.median(row_correlation)),
        "profile_correlation": profile_correlation,
        "profile_peak_separation_samples": float(abs(predicted_peak - target_peak)),
        "predicted_valid_pixel_retention": float(common.sum() / predicted_valid.sum()),
        "target_valid_pixel_retention": float(common.sum() / target.valid.sum()),
    }


def _require_residual_agreement(instrument: str, agreement: dict[str, float]) -> None:
    profile_minimum = (
        MINIMUM_DSA_RESIDUAL_PROFILE_CORRELATION
        if instrument == "DSA"
        else MINIMUM_RESIDUAL_PROFILE_CORRELATION
    )
    peak_maximum = (
        MAXIMUM_DSA_PROFILE_PEAK_SEPARATION_SAMPLES
        if instrument == "DSA"
        else MAXIMUM_PROFILE_PEAK_SEPARATION_SAMPLES
    )
    if not all(np.isfinite(value) for value in agreement.values()):
        raise RuntimeError(f"{instrument} numerical residual correction is non-finite")
    if (
        (
            instrument == "DSA"
            and agreement["median_row_correlation"]
            < MINIMUM_DSA_RESIDUAL_ROW_CORRELATION
        )
        or agreement["profile_correlation"] < profile_minimum
        or agreement["profile_peak_separation_samples"] > peak_maximum
        or agreement["predicted_valid_pixel_retention"]
        < MINIMUM_COMMON_VALID_PIXEL_FRACTION
        or agreement["target_valid_pixel_retention"]
        < MINIMUM_COMMON_VALID_PIXEL_FRACTION
    ):
        raise RuntimeError(f"{instrument} numerical residual correction disagrees with pixels")


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
    selected_cutoff_hz = float(chime_oracle["selected_cutoff_hz"])
    stored_rows = chime_oracle.get("fully_coherent_rows")
    if not isinstance(stored_rows, list) or len(stored_rows) != len(LABELS):
        raise RuntimeError("CHIME numerical oracle rows are absent")
    stored_hybrid_rows = chime_oracle.get("hybrid_rows")
    if not isinstance(stored_hybrid_rows, list) or len(stored_hybrid_rows) != len(LABELS):
        raise RuntimeError("CHIME numerical hybrid rows are absent")
    if not chime.get("hybrid_method", {}).get("nonwrapping_fractional_sample_shifts", False):
        raise RuntimeError("CHIME non-wrapping processing identity is absent")
    expected_chime_hashes = {
        "raw_chime_h5": config["input_sha256"]["raw_chime_h5"],
        "accepted_chime_reference": config["input_sha256"]["accepted_chime_reference"],
    }
    chime_anchor = load_band_observation_product(chime_observation_path)
    if (
        chime_anchor.instrument != "chime"
        or chime_anchor.reference_frequency_mhz != 400.0
        or chime_anchor.input_sha256 != expected_chime_hashes
    ):
        raise RuntimeError("CHIME fit observation identity changed")
    chime_shift_frequency = _npz_array(
        chime_observation_path, "residual_shift_frequency_mhz"
    )
    chime_products = {}
    recomputed_scores = []
    recomputed_hybrid_scores = []
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
        frequency_id = _npz_array(product_path, "fine_frequency_id")
        score, usable_channels = _phase_coherence_score(
            observation.waterfall,
            observation.valid,
            sample_interval_s=observation.sample_interval_s,
            frequency_id=frequency_id,
            cutoff_hz=selected_cutoff_hz,
        )
        stored_score = float(
            stored_rows[len(recomputed_scores)]["score"][str(selected_cutoff_hz)]
        )
        if not np.isclose(score, stored_score, rtol=2.0e-5, atol=1.0e-6):
            raise RuntimeError("CHIME numerical objective does not match saved pixels")
        recomputed_scores.append(score)
        numerical_agreement = _residual_numerical_agreement(
            chime_anchor,
            observation,
            shift_frequency_mhz=chime_shift_frequency,
            residual_dm_pc_cm3=target_dm - chime_anchor.dispersion.product_dm_pc_cm3,
        )
        _require_residual_agreement("CHIME", numerical_agreement)
        predicted, predicted_valid = _fractional_residual_shift(
            chime_anchor.waterfall,
            chime_anchor.valid,
            frequency_mhz=chime_shift_frequency,
            sample_interval_s=chime_anchor.sample_interval_s,
            residual_dm_pc_cm3=target_dm - chime_anchor.dispersion.product_dm_pc_cm3,
        )
        predicted_score, predicted_usable_channels = _phase_coherence_score(
            predicted,
            predicted_valid,
            sample_interval_s=chime_anchor.sample_interval_s,
            frequency_id=_npz_array(chime_observation_path, "fine_frequency_id"),
            cutoff_hz=selected_cutoff_hz,
        )
        recomputed_hybrid_scores.append(predicted_score)
        chime_products[key] = {
            "path": str(product_path),
            "sha256": product_sha256,
            "product_dm_pc_cm3": target_dm,
            "input_dm_pc_cm3": observation.dispersion.input_dm_pc_cm3,
            "coherent_correction_pc_cm3": (observation.dispersion.coherent_correction_pc_cm3),
            "valid_pixel_count": int(observation.valid.sum()),
            "recomputed_objective": score,
            "recomputed_usable_channel_count": usable_channels,
            "recomputed_hybrid_objective": predicted_score,
            "recomputed_hybrid_usable_channel_count": predicted_usable_channels,
            "numerical_residual_agreement": numerical_agreement,
        }
    recomputed_scores_array = np.asarray(recomputed_scores, dtype=float)
    recomputed_normalised = recomputed_scores_array / recomputed_scores_array[1]
    stored_normalised = np.asarray(
        chime_oracle["fully_coherent_normalised_score"], dtype=float
    )
    if not np.allclose(
        recomputed_normalised,
        stored_normalised,
        rtol=2.0e-5,
        atol=2.0e-5,
    ):
        raise RuntimeError("CHIME numerical objective curve does not match saved pixels")
    recomputed_hybrid_array = np.asarray(recomputed_hybrid_scores, dtype=float)
    recomputed_hybrid_normalised = recomputed_hybrid_array / recomputed_hybrid_array[1]
    stored_hybrid_normalised = np.asarray(
        chime_oracle["hybrid_normalised_score"], dtype=float
    )
    hybrid_curve_difference = float(
        np.max(np.abs(recomputed_hybrid_normalised - stored_hybrid_normalised))
    )
    hybrid_curve_tolerance = float(
        config["chime"]["gates"]["oracle_normalised_curve_max_abs_difference"]
    )
    if not np.isclose(
        float(chime_oracle["normalised_curve_tolerance"]),
        hybrid_curve_tolerance,
        rtol=0.0,
        atol=0.0,
    ):
        raise RuntimeError("CHIME oracle tolerance differs from reviewed configuration")
    if hybrid_curve_difference > hybrid_curve_tolerance:
        raise RuntimeError("CHIME numerical hybrid objective curve disagrees with anchor pixels")
    coherent_hybrid_curve_difference = float(
        np.max(np.abs(recomputed_normalised - recomputed_hybrid_normalised))
    )
    if coherent_hybrid_curve_difference > hybrid_curve_tolerance:
        raise RuntimeError("CHIME coherent and hybrid objective curves disagree")

    if not dsa.get("dedispersion", {}).get("nonwrapping_fractional_sample_interpolation", False):
        raise RuntimeError("DSA non-wrapping processing identity is absent")
    expected_dsa_hashes = {
        "raw_dsa_filterbank": config["input_sha256"]["raw_dsa_filterbank"],
        "accepted_dsa_reference": config["input_sha256"]["accepted_dsa_reference"],
    }
    dsa_anchor = load_band_observation_product(dsa_observation_path)
    if (
        dsa_anchor.instrument != "dsa"
        or dsa_anchor.reference_frequency_mhz != 400.0
        or dsa_anchor.input_sha256 != expected_dsa_hashes
    ):
        raise RuntimeError("DSA fit observation identity changed")
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
        numerical_agreement = _residual_numerical_agreement(
            dsa_anchor,
            observation,
            shift_frequency_mhz=dsa_anchor.frequency_mhz,
            residual_dm_pc_cm3=target_dm - dsa_anchor.dispersion.product_dm_pc_cm3,
        )
        _require_residual_agreement("DSA", numerical_agreement)
        dsa_products[key] = {
            "path": str(product_path),
            "sha256": product_sha256,
            "product_dm_pc_cm3": target_dm,
            "input_dm_pc_cm3": observation.dispersion.input_dm_pc_cm3,
            "applied_residual_dm_pc_cm3": (observation.dispersion.incoherent_correction_pc_cm3),
            "valid_pixel_count": int(observation.valid.sum()),
            "numerical_residual_agreement": numerical_agreement,
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
            "recomputed_normalised_score": recomputed_normalised.tolist(),
            "recomputed_hybrid_normalised_score": (
                recomputed_hybrid_normalised.tolist()
            ),
            "maximum_recomputed_hybrid_curve_difference": hybrid_curve_difference,
            "maximum_coherent_hybrid_curve_difference": (
                coherent_hybrid_curve_difference
            ),
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
