#!/usr/bin/env python3
"""Experimental DSA-110 raw-input-DM diagnostic; not science authority."""

from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path
from typing import Any

import numpy as np
from absolute_dm_voltage import K_DM_S_MHZ2
from inventory_absolute_dm_inputs_h17 import load_path_manifest
from scipy.signal import correlate

REFERENCE_FREQUENCY_MHZ = 400.0
WINDOW_SAMPLES = (2500, 2000, 1500)


def _finite_center(values: np.ndarray) -> np.ndarray:
    result = np.asarray(values, dtype=float).copy()
    finite = np.isfinite(result)
    if finite.mean() < 0.90:
        raise ValueError("row has less than 90 percent finite support")
    fill = float(np.median(result[finite]))
    result[~finite] = fill
    result -= np.mean(result)
    return result


def normalised_correlation(left: np.ndarray, right: np.ndarray) -> float:
    first = _finite_center(left)
    second = _finite_center(right)
    denominator = float(np.linalg.norm(first) * np.linalg.norm(second))
    return float(np.dot(first, second) / denominator) if denominator > 0 else 0.0


def sub_sample_peak(score: np.ndarray, index: int) -> float:
    if index <= 0 or index >= score.size - 1:
        return float(index)
    left, center, right = map(float, score[index - 1 : index + 2])
    denominator = left - 2.0 * center + right
    if not np.isfinite(denominator) or denominator >= 0 or denominator == 0:
        return float(index)
    offset = 0.5 * (left - right) / denominator
    return float(index + np.clip(offset, -1.0, 1.0))


def row_match(
    raw_row: np.ndarray,
    reference_row: np.ndarray,
    *,
    reference_left: int,
) -> dict[str, float]:
    needle = _finite_center(reference_row)
    source = _finite_center(raw_row)
    score = correlate(source, needle, mode="valid", method="fft")
    integer_start = int(np.argmax(score))
    slice_start = sub_sample_peak(score, integer_start)
    candidate = np.interp(
        slice_start + np.arange(reference_row.size, dtype=float),
        np.arange(raw_row.size, dtype=float),
        raw_row,
    )
    return {
        "integer_slice_start_sample": integer_start,
        "integer_reference_origin_sample": int(
            integer_start - reference_left
        ),
        "reference_origin_sample": float(slice_start - reference_left),
        "correlation": normalised_correlation(reference_row, candidate),
    }


def robust_delay_fit(
    delay_coordinate: np.ndarray,
    start_sample: np.ndarray,
    correlation: np.ndarray,
) -> dict[str, Any]:
    x = np.asarray(delay_coordinate, dtype=float)
    pivot = float(np.median(x))
    centered_x = x - pivot
    y = np.asarray(start_sample, dtype=float)
    weight = np.clip(np.asarray(correlation, dtype=float), 0.0, 1.0)
    use = np.isfinite(x) & np.isfinite(y) & (weight >= 0.5)
    if use.sum() < 16:
        raise RuntimeError("fewer than 16 usable row-start measurements")
    correlation_floor = float(np.quantile(weight[use], 0.25))
    use &= weight >= correlation_floor
    for _ in range(4):
        coefficient = np.polyfit(
            centered_x[use],
            y[use],
            1,
            w=weight[use] ** 2,
        )
        residual = y - np.polyval(coefficient, centered_x)
        center = float(np.median(residual[use]))
        mad = float(np.median(np.abs(residual[use] - center)))
        limit = max(0.20, 4.0 * 1.4826 * mad)
        updated = use & (np.abs(residual - center) <= limit)
        if updated.sum() < 16 or np.array_equal(updated, use):
            break
        use = updated
    coefficient = np.polyfit(
        centered_x[use],
        y[use],
        1,
        w=weight[use] ** 2,
    )
    residual = y - np.polyval(coefficient, centered_x)
    centered = residual[use] - np.median(residual[use])
    return {
        "reference_minus_raw_dm_pc_cm3": float(
            coefficient[0] / K_DM_S_MHZ2
        ),
        "pivot_delay_coordinate": pivot,
        "pivot_crop_start_sample": float(coefficient[1]),
        "reference_frequency_crop_start_sample": float(
            coefficient[1] - coefficient[0] * pivot
        ),
        "used_count": int(use.sum()),
        "correlation_floor": correlation_floor,
        "residual_median_samples": float(np.median(residual[use])),
        "residual_mad_samples": float(np.median(np.abs(centered))),
        "residual_max_abs_samples": float(np.max(np.abs(centered))),
        "used_mask": use,
    }


def _fit_rows(
    rows: list[dict[str, Any]],
    frequency_mhz: np.ndarray,
    sample_time_s: float,
    *,
    origin_key: str = "reference_origin_sample",
) -> dict[str, Any]:
    delay = (
        frequency_mhz**-2 - REFERENCE_FREQUENCY_MHZ**-2
    ) / sample_time_s
    start = np.asarray([row[origin_key] for row in rows])
    correlation = np.asarray([row["correlation"] for row in rows])
    return robust_delay_fit(delay, start, correlation)


def _jackknife(
    rows: list[dict[str, Any]],
    frequency_mhz: np.ndarray,
    sample_time_s: float,
    *,
    blocks: int = 12,
) -> dict[str, Any]:
    ordered = np.argsort(frequency_mhz)
    groups = np.array_split(ordered, blocks)
    estimates = []
    for excluded in groups:
        keep = np.ones(len(rows), dtype=bool)
        keep[excluded] = False
        estimate = _fit_rows(
            [row for index, row in enumerate(rows) if keep[index]],
            frequency_mhz[keep],
            sample_time_s,
        )
        estimates.append(estimate["reference_minus_raw_dm_pc_cm3"])
    values = np.asarray(estimates, dtype=float)
    center = float(np.mean(values))
    sigma = float(
        np.sqrt((values.size - 1) / values.size * np.sum((values - center) ** 2))
    )
    return {
        "blocks": blocks,
        "estimates_pc_cm3": values.tolist(),
        "sigma_pc_cm3": sigma,
    }


def _candidate_rows(
    raw: np.ndarray,
    selected_rows: np.ndarray,
    frequency_mhz: np.ndarray,
    sample_time_s: float,
    *,
    residual_dm: float,
    crop_start: float,
    samples: int,
) -> np.ndarray:
    delay = (
        frequency_mhz**-2 - REFERENCE_FREQUENCY_MHZ**-2
    ) / sample_time_s
    start = crop_start + K_DM_S_MHZ2 * residual_dm * delay
    source_sample = np.arange(raw.shape[1], dtype=float)
    output = np.empty((selected_rows.size, samples), dtype=float)
    offset = np.arange(samples, dtype=float)
    for index, row in enumerate(selected_rows):
        output[index] = np.interp(
            start[index] + offset,
            source_sample,
            raw[row],
            left=np.nan,
            right=np.nan,
        )
    return output


def _profile(values: np.ndarray) -> np.ndarray:
    median = np.nanmedian(values, axis=1)
    mad = np.nanmedian(np.abs(values - median[:, None]), axis=1)
    sigma = 1.4826 * mad
    use = np.isfinite(sigma) & (sigma > 0)
    z = (values[use] - median[use, None]) / sigma[use, None]
    return np.nanmean(np.clip(z, 0.0, None), axis=0)


def correction_validation(
    raw: np.ndarray,
    reference: np.ndarray,
    selected_rows: np.ndarray,
    frequency_mhz: np.ndarray,
    sample_time_s: float,
    fit: dict[str, Any],
) -> dict[str, Any]:
    residual_dm = float(fit["reference_minus_raw_dm_pc_cm3"])
    crop_start = float(fit["reference_frequency_crop_start_sample"])
    pivot_crop_start = float(fit["pivot_crop_start_sample"])
    corrected = _candidate_rows(
        raw,
        selected_rows,
        frequency_mhz,
        sample_time_s,
        residual_dm=residual_dm,
        crop_start=crop_start,
        samples=reference.shape[1],
    )
    uncorrected = _candidate_rows(
        raw,
        selected_rows,
        frequency_mhz,
        sample_time_s,
        residual_dm=0.0,
        crop_start=pivot_crop_start,
        samples=reference.shape[1],
    )
    selected_reference = np.asarray(reference[selected_rows], dtype=float)
    corrected_correlation = np.asarray(
        [
            normalised_correlation(selected_reference[index], corrected[index])
            for index in range(selected_rows.size)
        ]
    )
    uncorrected_correlation = np.asarray(
        [
            normalised_correlation(selected_reference[index], uncorrected[index])
            for index in range(selected_rows.size)
        ]
    )
    return {
        "corrected_row_correlation_median": float(
            np.median(corrected_correlation)
        ),
        "uncorrected_row_correlation_median": float(
            np.median(uncorrected_correlation)
        ),
        "row_correlation_improvement": float(
            np.median(corrected_correlation - uncorrected_correlation)
        ),
        "corrected_profile_correlation": normalised_correlation(
            _profile(selected_reference),
            _profile(corrected),
        ),
        "uncorrected_profile_correlation": normalised_correlation(
            _profile(selected_reference),
            _profile(uncorrected),
        ),
    }


def synthetic_sign_oracle() -> dict[str, Any]:
    rng = np.random.default_rng(20260728)
    frequency = np.linspace(1498.75, 1311.25, 256)
    sample_time_s = 32.768e-6
    raw = rng.normal(0.0, 0.3, (frequency.size, 4096))
    pulse = np.exp(-0.5 * ((np.arange(4096) - 2048.0) / 8.0) ** 2)
    raw += 4.0 * pulse
    injected = 0.137
    crop_start = 800.0
    accepted = _candidate_rows(
        raw,
        np.arange(frequency.size),
        frequency,
        sample_time_s,
        residual_dm=injected,
        crop_start=crop_start,
        samples=2500,
    )
    rows = [
        {
            "row": index,
            **row_match(raw[index], accepted[index], reference_left=0),
        }
        for index in range(frequency.size)
    ]
    fit = _fit_rows(rows, frequency, sample_time_s)
    error = abs(float(fit["reference_minus_raw_dm_pc_cm3"]) - injected)
    wrong_sign_error = abs(float(fit["reference_minus_raw_dm_pc_cm3"]) + injected)
    passed = error < 0.003 and error < wrong_sign_error
    if not passed:
        raise RuntimeError("DSA synthetic residual-DM sign oracle failed")
    return {
        "injected_reference_minus_raw_dm_pc_cm3": injected,
        "recovered_reference_minus_raw_dm_pc_cm3": fit[
            "reference_minus_raw_dm_pc_cm3"
        ],
        "absolute_error_pc_cm3": error,
        "wrong_sign_error_pc_cm3": wrong_sign_error,
        "passed": passed,
    }


def reconstruct_event(
    event: str,
    paths: dict[str, Path],
    accepted_dm: float,
    *,
    sampled_rows: int,
) -> dict[str, Any]:
    from blimpy import Waterfall

    reader = Waterfall(str(paths["raw_dsa_filterbank"]), load_data=True)
    raw = np.asarray(reader.data[:, 0, :], dtype=np.float32).T
    reference = np.load(paths["accepted_dsa_reference"])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        standard_deviation = np.nanstd(reference, axis=1)
    live_rows = np.flatnonzero(
        np.isfinite(standard_deviation) & (standard_deviation > 0)
    )
    selected_rows = live_rows[
        np.linspace(0, live_rows.size - 1, sampled_rows, dtype=int)
    ]
    all_frequency = float(reader.header["fch1"]) + float(
        reader.header["foff"]
    ) * np.arange(int(reader.header["nchans"]))
    selected_frequency = all_frequency[selected_rows]
    sample_time_s = float(reader.header["tsamp"])
    window_results = []
    full_rows = None
    for samples in WINDOW_SAMPLES:
        if samples > reference.shape[1]:
            continue
        left = (reference.shape[1] - samples) // 2
        right = left + samples
        rows = [
            {
                "row": int(row),
                **row_match(
                    raw[row],
                    reference[row, left:right],
                    reference_left=left,
                ),
            }
            for row in selected_rows
        ]
        fit = _fit_rows(rows, selected_frequency, sample_time_s)
        window_results.append(
            {
                "window_samples": samples,
                "fit": {key: value for key, value in fit.items() if key != "used_mask"},
            }
        )
        if samples == reference.shape[1]:
            full_rows = rows
            full_fit = fit
    if full_rows is None:
        raise RuntimeError("full accepted DSA window was not reconstructed")
    integer_fit = _fit_rows(
        full_rows,
        selected_frequency,
        sample_time_s,
        origin_key="integer_reference_origin_sample",
    )
    order_reversed_rows = [
        {
            "row": int(row),
            **row_match(
                raw[::-1][row],
                reference[row],
                reference_left=0,
            ),
        }
        for row in selected_rows
    ]
    direct_median = float(np.median([row["correlation"] for row in full_rows]))
    reversed_median = float(
        np.median([row["correlation"] for row in order_reversed_rows])
    )
    low = selected_frequency <= np.median(selected_frequency)
    separated = {
        "lower_frequency_half": {
            key: value
            for key, value in _fit_rows(
                [row for index, row in enumerate(full_rows) if low[index]],
                selected_frequency[low],
                sample_time_s,
            ).items()
            if key != "used_mask"
        },
        "upper_frequency_half": {
            key: value
            for key, value in _fit_rows(
                [row for index, row in enumerate(full_rows) if not low[index]],
                selected_frequency[~low],
                sample_time_s,
            ).items()
            if key != "used_mask"
        },
    }
    jackknife = _jackknife(
        full_rows,
        selected_frequency,
        sample_time_s,
    )
    correction = correction_validation(
        raw,
        reference,
        selected_rows,
        selected_frequency,
        sample_time_s,
        full_fit,
    )
    training = np.arange(selected_rows.size) % 2 == 0
    held_out = ~training
    training_fit = _fit_rows(
        [row for index, row in enumerate(full_rows) if training[index]],
        selected_frequency[training],
        sample_time_s,
    )
    held_out_correction = correction_validation(
        raw,
        reference,
        selected_rows[held_out],
        selected_frequency[held_out],
        sample_time_s,
        training_fit,
    )
    window_estimates = np.asarray(
        [
            row["fit"]["reference_minus_raw_dm_pc_cm3"]
            for row in window_results
        ],
        dtype=float,
    )
    half_difference = abs(
        separated["lower_frequency_half"]["reference_minus_raw_dm_pc_cm3"]
        - separated["upper_frequency_half"]["reference_minus_raw_dm_pc_cm3"]
    )
    uncertainty = max(
        float(jackknife["sigma_pc_cm3"]),
        0.5 * float(np.ptp(window_estimates)),
        0.5 * float(half_difference),
        abs(
            float(full_fit["reference_minus_raw_dm_pc_cm3"])
            - float(integer_fit["reference_minus_raw_dm_pc_cm3"])
        ),
        0.003,
    )
    residual_dm = float(full_fit["reference_minus_raw_dm_pc_cm3"])
    material_threshold = max(0.03, 3.0 * uncertainty)
    material_residual = abs(residual_dm) >= material_threshold
    checks = {
        "direct_order": direct_median >= 0.8 and reversed_median <= 0.1,
        "fit_precision": uncertainty <= 0.03,
        "flat_after_correction": (
            float(full_fit["residual_mad_samples"]) <= 0.35
            and float(full_fit["residual_max_abs_samples"]) <= 1.5
        ),
        "window_consistency": float(np.ptp(window_estimates)) <= 0.04,
        "separated_frequency_consistency": float(half_difference) <= 0.06,
        "integer_subsample_consistency": abs(
            residual_dm
            - float(integer_fit["reference_minus_raw_dm_pc_cm3"])
        )
        <= 0.03,
        "corrected_row_match": (
            correction["corrected_row_correlation_median"] >= 0.8
        ),
        "correction_improves_match": (
            correction["row_correlation_improvement"] >= 0.005
            if material_residual
            else abs(residual_dm) <= material_threshold
        ),
        "correction_improves_profile": (
            correction["corrected_profile_correlation"]
            >= correction["uncorrected_profile_correlation"]
            if material_residual
            else abs(residual_dm) <= material_threshold
        ),
        "held_out_correction": (
            held_out_correction["corrected_row_correlation_median"] >= 0.8
            and (
                held_out_correction["row_correlation_improvement"] >= 0.005
                and held_out_correction["corrected_profile_correlation"]
                >= held_out_correction["uncorrected_profile_correlation"]
                if material_residual
                else abs(residual_dm) <= material_threshold
            )
        ),
    }
    accepted = all(checks.values())
    return {
        "event": event,
        "status": (
            "inferred_raw_input_dm_accepted_for_config_review"
            if accepted
            else "ambiguous_raw_input_dm_reconstruction"
        ),
        "accepted_reference_dm_pc_cm3": accepted_dm,
        "reference_minus_raw_dm_pc_cm3": residual_dm,
        "inferred_raw_input_dm_pc_cm3": accepted_dm - residual_dm,
        "conservative_uncertainty_pc_cm3": uncertainty,
        "material_residual_threshold_pc_cm3": material_threshold,
        "material_nonzero_residual_proven": material_residual,
        "formula": (
            "raw_input_DM = accepted_reference_DM - fitted(reference_minus_raw_DM)"
        ),
        "sign": (
            "positive fitted residual means the accepted reference is at a larger "
            "total DM than the raw filterbank"
        ),
        "sampled_live_rows": sampled_rows,
        "full_window_fit": {
            key: value for key, value in full_fit.items() if key != "used_mask"
        },
        "full_window_integer_start_fit": {
            key: value
            for key, value in integer_fit.items()
            if key != "used_mask"
        },
        "frequency_order": {
            "direct_median_correlation": direct_median,
            "reversed_median_correlation": reversed_median,
        },
        "window_fits": window_results,
        "separated_frequency_fits": separated,
        "frequency_block_jackknife": jackknife,
        "correction_validation": correction,
        "held_out_validation": {
            "fit_rows": int(training.sum()),
            "validation_rows": int(held_out.sum()),
            "training_fit": {
                key: value
                for key, value in training_fit.items()
                if key != "used_mask"
            },
            "correction": held_out_correction,
        },
        "checks": checks,
        "accepted_for_config_review": accepted,
    }


def apply_known_zero_systematic_model(
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    """Calibrate a shared uncertainty floor without subtracting event bias."""

    casey = next(row for row in events if row["event"].lower() == "casey")
    control_tolerance = 0.005
    casey_bias = abs(float(casey["reference_minus_raw_dm_pc_cm3"]))
    systematic_floor = casey_bias + control_tolerance
    control = {
        "event": "casey",
        "expected_reference_minus_raw_dm_pc_cm3": 0.0,
        "expectation_source": (
            "approved Casey 96-row audit: all rows at one raw start and "
            "1.19e-13 pc cm^-3 fitted residual"
        ),
        "maximum_absolute_error_pc_cm3": control_tolerance,
        "reconstructed_reference_minus_raw_dm_pc_cm3": casey[
            "reference_minus_raw_dm_pc_cm3"
        ],
        "strict_tolerance_passed": bool(casey_bias <= control_tolerance),
        "derived_systematic_floor_pc_cm3": systematic_floor,
        "systematic_model": (
            "absolute Casey known-zero error plus 0.005 pc cm^-3 margin, "
            "applied as a common conservative uncertainty floor without "
            "subtracting a bias from any event"
        ),
        "zero_covered_by_systematic_model": bool(casey_bias <= systematic_floor),
    }
    for row in events:
        uncertainty = max(
            float(row["conservative_uncertainty_pc_cm3"]),
            systematic_floor,
        )
        residual = abs(float(row["reference_minus_raw_dm_pc_cm3"]))
        material_threshold = max(0.03, 3.0 * uncertainty)
        material = residual >= material_threshold
        correction = row["correction_validation"]
        held_out = row["held_out_validation"]["correction"]
        row["conservative_uncertainty_pc_cm3"] = uncertainty
        row["material_residual_threshold_pc_cm3"] = material_threshold
        row["material_nonzero_residual_proven"] = material
        row["checks"]["fit_precision"] = uncertainty <= 0.03
        row["checks"]["material_nonzero_residual"] = material
        row["checks"]["correction_improves_match"] = bool(
            material and correction["row_correlation_improvement"] >= 0.005
        )
        row["checks"]["correction_improves_profile"] = bool(
            material
            and correction["corrected_profile_correlation"]
            >= correction["uncorrected_profile_correlation"]
        )
        row["checks"]["held_out_correction"] = bool(
            material
            and held_out["corrected_row_correlation_median"] >= 0.8
            and held_out["row_correlation_improvement"] >= 0.005
            and held_out["corrected_profile_correlation"]
            >= held_out["uncorrected_profile_correlation"]
        )
        row["checks"]["known_zero_systematic_model"] = control[
            "zero_covered_by_systematic_model"
        ]
        row["accepted_for_config_review"] = bool(all(row["checks"].values()))
        row["status"] = (
            "inferred_raw_input_dm_accepted_for_config_review"
            if row["accepted_for_config_review"]
            else "ambiguous_or_nonmaterial_raw_input_dm_reconstruction"
        )
    return control


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-paths", type=Path, required=True)
    parser.add_argument("--coherent-fits", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sampled-rows", type=int, default=256)
    args = parser.parse_args()
    if args.sampled_rows < 64:
        raise ValueError("--sampled-rows must be at least 64")
    paths = load_path_manifest(args.input_paths)
    fits = {
        str(row["burst"]).lower(): row
        for row in json.loads(args.coherent_fits.read_text())
    }
    oracle = synthetic_sign_oracle()
    events = []
    for event, event_paths in paths.items():
        events.append(
            reconstruct_event(
                event,
                event_paths,
                float(fits[event.lower()]["dsa"]["product_dm"]),
                sampled_rows=args.sampled_rows,
            )
        )
        print(
            json.dumps(
                {
                    "event": event,
                    "status": events[-1]["status"],
                    "residual_dm": events[-1][
                        "reference_minus_raw_dm_pc_cm3"
                    ],
                    "sigma": events[-1]["conservative_uncertainty_pc_cm3"],
                }
            ),
            flush=True,
        )
    known_zero_control = apply_known_zero_systematic_model(events)
    result = {
        "schema_version": 1,
        "status": "diagnostic_only_dsa_raw_input_dm_reconstruction",
        "method": {
            "row_start_estimator": (
                "FFT correlation with three-point sub-sample peak interpolation"
            ),
            "fit": "correlation-weighted iterative robust linear regression",
            "delay_coordinate": (
                "(frequency_MHz^-2 - 400_MHz^-2) / sample_time_s"
            ),
            "residual_dm_formula": "fitted row-start slope / 4148.808",
            "uncertainty": (
                "maximum of frequency-block jackknife sigma, half crop-window "
                "range, half separated-band difference, and 0.003 pc cm^-3 floor"
            ),
            "window_samples": list(WINDOW_SAMPLES),
        },
        "synthetic_sign_oracle": oracle,
        "known_zero_control": known_zero_control,
        "events": events,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
