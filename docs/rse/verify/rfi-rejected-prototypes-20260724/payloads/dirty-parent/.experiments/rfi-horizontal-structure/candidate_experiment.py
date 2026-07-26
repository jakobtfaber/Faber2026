#!/usr/bin/env python3
"""Known-truth comparison for stationary intermittent horizontal RFI."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def add_intermittent_horizontal(case: dict, seed: int) -> None:
    """Add fixed-frequency, near-threshold segments across all time regions."""
    rng = np.random.default_rng(np.random.SeedSequence(seed, spawn_key=(11,)))
    valid = np.asarray(case["source_valid"], dtype=bool)
    occupied = np.any(case["component_masks"]["persistent_lines"], axis=1) | np.any(
        case["component_masks"]["coarse_comb"], axis=1
    )
    available = np.flatnonzero(valid & ~occupied)
    centers = available[np.linspace(0, available.size - 1, 18, dtype=int)]
    rows = []
    for center in centers:
        candidate = np.arange(max(0, center - 1), min(valid.size, center + 2))
        rows.extend(candidate[valid[candidate] & ~occupied[candidate]].tolist())
    rows = np.unique(rows)

    ntime = case["truth"].shape[1]
    fractions = ((0.05, 0.08), (0.17, 0.20), (0.34, 0.39), (0.50, 0.60), (0.79, 0.86))
    segments = [
        np.arange(int(round(start * ntime)), int(round(stop * ntime)))
        for start, stop in fractions
    ]
    values = np.zeros_like(case["truth"], dtype=np.float32)
    mask = np.zeros_like(case["truth"], dtype=bool)
    for row in rows:
        base = rng.uniform(3.4, 4.6)
        for segment_index, columns in enumerate(segments):
            phase = np.linspace(0.0, np.pi, columns.size, endpoint=True)
            envelope = 0.82 + 0.18 * np.sin(phase)
            amplitude = base * (0.92 + 0.04 * segment_index)
            values[row, columns] += (amplitude * envelope).astype(np.float32)
            mask[row, columns] = True

    case["raw"] += (case["bandpass_scale"][:, None] * values).astype(np.float32)
    case["rfi_standardized"] += values
    case["rfi_mask"] |= mask
    case["component_masks"]["intermittent_horizontal"] = mask
    case["parameters"]["rfi"]["intermittent_horizontal_rows"] = rows.tolist()
    case["parameters"]["rfi"]["intermittent_horizontal_segments"] = [
        [int(columns[0]), int(columns[-1] + 1)] for columns in segments
    ]
    case["parameters"]["rfi"]["intermittent_horizontal_amplitude_range"] = [3.4, 4.6]


def occupancy_rows(
    values: np.ndarray,
    row_valid: np.ndarray,
    training: tuple[int, int],
    *,
    threshold: float = 4.0,
    minimum_count: int = 2,
) -> np.ndarray:
    """Flag rows with repeated strong off-pulse excursions."""
    data = np.asarray(values, dtype=np.float64)
    valid = np.asarray(row_valid, dtype=bool)
    start, stop = training
    segment = data[:, start:stop]
    count = np.sum(np.isfinite(segment) & (np.abs(segment) >= threshold), axis=1)
    finite_count = np.sum(np.isfinite(segment), axis=1)
    return valid & (finite_count == stop - start) & (count >= minimum_count)


def robust_stat_rows(auto_module, values, row_valid, training) -> np.ndarray:
    """Apply the repository's off-pulse robust variability/correlation learner."""
    data = np.asarray(values, dtype=np.float64)
    valid = np.asarray(row_valid, dtype=bool)
    mask = ~np.isfinite(data) | ~valid[:, None]
    flagged, _ = auto_module.auto_flag(
        np.ma.MaskedArray(data, mask=mask),
        training,
        sigma=5.0,
        iters=6,
    )
    return valid & np.asarray(flagged, dtype=bool)


def predicted_mask(row_valid: np.ndarray, additional_rows: np.ndarray, shape) -> np.ndarray:
    rejected = ~np.asarray(row_valid, dtype=bool) | np.asarray(additional_rows, dtype=bool)
    return np.broadcast_to(rejected[:, None], shape)


def confusion(truth: np.ndarray, predicted: np.ndarray, valid: np.ndarray) -> dict:
    use = np.broadcast_to(np.asarray(valid, dtype=bool)[:, None], truth.shape)
    actual = np.asarray(truth, dtype=bool)
    guess = np.asarray(predicted, dtype=bool)
    tp = int(np.sum(use & actual & guess))
    fp = int(np.sum(use & ~actual & guess))
    fn = int(np.sum(use & actual & ~guess))
    tn = int(np.sum(use & ~actual & ~guess))
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": tp / max(tp + fp, 1),
        "recall": tp / max(tp + fn, 1),
        "false_positive_fraction": fp / max(fp + tn, 1),
    }


def longest_true_run(values: np.ndarray) -> int:
    padded = np.pad(np.asarray(values, dtype=bool), (1, 1))
    edges = np.diff(padded.astype(np.int8))
    starts = np.flatnonzero(edges == 1)
    stops = np.flatnonzero(edges == -1)
    return int(np.max(stops - starts)) if starts.size else 0


def horizontal_completeness(truth: np.ndarray, predicted: np.ndarray) -> dict:
    contaminated_rows = np.flatnonzero(np.any(truth, axis=1))
    recalls = []
    longest_missed = []
    for row in contaminated_rows:
        actual = truth[row]
        recalls.append(float(np.sum(actual & predicted[row]) / np.sum(actual)))
        longest_missed.append(longest_true_run(actual & ~predicted[row]))
    return {
        "contaminated_rows": int(contaminated_rows.size),
        "minimum_row_recall": float(min(recalls)) if recalls else None,
        "median_row_recall": float(np.median(recalls)) if recalls else None,
        "fully_recovered_rows": int(np.sum(np.asarray(recalls) == 1.0)),
        "longest_surviving_run_bins": int(max(longest_missed)) if longest_missed else 0,
    }


def measurement_effects(module, case, row_result, additional_rows, seed) -> dict:
    row_valid = np.asarray(row_result["final_valid"], dtype=bool) & ~additional_rows
    cleaned = np.asarray(row_result["cleaned"], dtype=np.float32)
    frequency = case["frequency_mhz"]
    truth_coarse, coarse_frequency, counts = module.coarsen(case["truth"], frequency, row_valid)
    cleaned_coarse, _, _ = module.coarsen(cleaned, frequency, row_valid)
    signal_coarse, _, _ = module.coarsen(case["signal"], frequency, row_valid)
    burst = tuple(case["parameters"]["windows"]["burst"])
    truth_measure = module.measure_summary(
        truth_coarse, coarse_frequency, counts > 0, case["parameters"]["dt_ms"], burst, signal_coarse
    )
    cleaned_measure = module.measure_summary(
        cleaned_coarse, coarse_frequency, counts > 0, case["parameters"]["dt_ms"], burst, signal_coarse
    )
    uncertainties = module.bootstrap_uncertainties(
        signal_coarse,
        coarse_frequency,
        counts,
        case["parameters"]["dt_ms"],
        burst,
        seed,
        nrealizations=12,
    )
    effects = {}
    for name, truth_value in truth_measure.items():
        if name == "component_count":
            continue
        cleaned_value = cleaned_measure.get(name)
        uncertainty = uncertainties.get(name)
        if truth_value is None or cleaned_value is None or not uncertainty or uncertainty <= 0:
            effects[name] = None
        else:
            effects[name] = abs(float(cleaned_value) - float(truth_value)) / float(uncertainty)
    return {
        "effects_sigma": effects,
        "maximum_effect_sigma": max(value for value in effects.values() if value is not None),
        "component_count_stable": truth_measure["component_count"] == cleaned_measure["component_count"],
    }


def burst_support_loss(case: dict, base_valid: np.ndarray, additional_rows: np.ndarray) -> float:
    """Fraction of injected burst intensity removed only by the added row veto."""
    start, stop = case["parameters"]["windows"]["burst"]
    signal = np.abs(np.asarray(case["signal"], dtype=np.float64)[:, start:stop])
    denominator = np.sum(signal[np.asarray(base_valid, dtype=bool)])
    numerator = np.sum(signal[np.asarray(base_valid, dtype=bool) & additional_rows])
    return float(numerator / denominator) if denominator > 0 else float("nan")


def run(args: argparse.Namespace) -> dict:
    module = load_module("rfi_prototype", args.prototype_script)
    auto_module = load_module("auto_rfi_flag", args.auto_rfi_script)
    root = args.input_root
    frequency = np.load(root / "products/zach_chime_freq.npy")
    source_valid = np.load(root / "products/zach_chime_source_valid.npy").astype(bool)
    mean = np.load(root / "diagnostics/audit-v2/zach_bandpass_mean.npy")
    scale = np.load(root / "diagnostics/audit-v2/zach_bandpass_scale.npy")
    case = module.generate_case(frequency, source_valid, mean, scale, 512, 0.32768, args.seed)
    add_intermittent_horizontal(case, args.seed)
    training = tuple(case["parameters"]["windows"]["training"])
    audit = root / "code/audit_chime_preprocessing_v2.py"
    contaminated = module.run_rejected_cleaner(case["raw"], source_valid, training, audit)
    clean_raw = (
        case["bandpass_mean"][:, None] + case["bandpass_scale"][:, None] * case["truth"]
    ).astype(np.float32)
    clean = module.run_rejected_cleaner(clean_raw, source_valid, training, audit)

    contaminated_candidates = {
        "package_row_only": np.zeros(source_valid.shape, dtype=bool),
        "robust_stats": robust_stat_rows(
            auto_module, contaminated["cleaned"], contaminated["final_valid"], training
        ),
        "tail_occupancy": occupancy_rows(
            contaminated["cleaned"], contaminated["final_valid"], training
        ),
    }
    contaminated_candidates["union"] = (
        contaminated_candidates["robust_stats"] | contaminated_candidates["tail_occupancy"]
    )
    clean_candidates = {
        "package_row_only": np.zeros(source_valid.shape, dtype=bool),
        "robust_stats": robust_stat_rows(auto_module, clean["cleaned"], clean["final_valid"], training),
        "tail_occupancy": occupancy_rows(clean["cleaned"], clean["final_valid"], training),
    }
    clean_candidates["union"] = clean_candidates["robust_stats"] | clean_candidates["tail_occupancy"]

    valid_pixels = np.broadcast_to(source_valid[:, None], case["rfi_mask"].shape)
    horizontal = case["component_masks"]["intermittent_horizontal"]
    results = {}
    for name, rows in contaminated_candidates.items():
        predicted = predicted_mask(contaminated["final_valid"], rows, case["rfi_mask"].shape)
        clean_predicted = predicted_mask(
            clean["final_valid"], clean_candidates[name], case["rfi_mask"].shape
        )
        total_rfi = np.sum(np.abs(case["rfi_standardized"])[case["rfi_mask"]])
        residual_rfi = np.sum(
            np.abs(case["rfi_standardized"])[case["rfi_mask"] & ~predicted]
        )
        results[name] = {
            "additional_contaminated_rows": int(rows.sum()),
            "additional_clean_rows": int(clean_candidates[name].sum()),
            "additional_clean_row_fraction": float(
                clean_candidates[name].sum() / max(clean["final_valid"].sum(), 1)
            ),
            "added_row_veto_burst_support_loss_fraction": burst_support_loss(
                case, contaminated["final_valid"], rows
            ),
            "mask": confusion(case["rfi_mask"], predicted, source_valid),
            "intermittent_horizontal": horizontal_completeness(horizontal, predicted),
            "residual_rfi_intensity_fraction": float(residual_rfi / total_rfi),
            "clean_false_rejection_fraction": float(
                np.sum(valid_pixels & clean_predicted) / np.sum(valid_pixels)
            ),
            "measurements": measurement_effects(module, case, contaminated, rows, args.seed),
        }

    return {
        "status": "throwaway_known_truth_horizontal_structure_experiment",
        "seed": args.seed,
        "parameters": {
            "training": list(training),
            "occupancy_absolute_threshold": 4.0,
            "occupancy_minimum_count": 2,
            "robust_stats_sigma": 5.0,
            "robust_stats_iterations": 6,
            "experiment_bootstrap_realizations": 12,
            "intermittent_horizontal": case["parameters"]["rfi"],
        },
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--prototype-script", type=Path, required=True)
    parser.add_argument("--auto-rfi-script", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = run(args)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
