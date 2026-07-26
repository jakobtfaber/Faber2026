#!/usr/bin/env python3
"""Throwaway comparison of row and time-frequency RFI masks."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
from scipy.ndimage import binary_propagation


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("rfi_prototype", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def dynamic_mask(values: np.ndarray, method: str) -> np.ndarray:
    data = np.asarray(values, dtype=np.float64)
    finite = np.isfinite(data)
    magnitude = np.abs(data)
    if method == "row_only":
        return np.zeros(data.shape, dtype=bool)
    if method == "clip6":
        return finite & (magnitude >= 6.0)
    if method == "grow6_4":
        seeds = finite & (magnitude >= 6.0)
        allowed = finite & (magnitude >= 4.0)
        return binary_propagation(
            seeds,
            structure=np.ones((3, 3), dtype=bool),
            mask=allowed,
        )
    raise ValueError(method)


def predicted_mask(row_valid: np.ndarray, dynamic: np.ndarray) -> np.ndarray:
    rejected_rows = np.broadcast_to(~np.asarray(row_valid, dtype=bool)[:, None], dynamic.shape)
    return rejected_rows | np.asarray(dynamic, dtype=bool)


def confusion(truth: np.ndarray, predicted: np.ndarray, valid: np.ndarray) -> dict[str, float | int]:
    use = np.broadcast_to(np.asarray(valid, dtype=bool), truth.shape)
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


def measure_candidate(module, case, row_result, mask):
    cleaned = np.asarray(row_result["cleaned"], dtype=np.float32).copy()
    cleaned[mask] = np.nan
    truth = np.asarray(case["truth"], dtype=np.float32).copy()
    truth[mask] = np.nan
    signal = np.asarray(case["signal"], dtype=np.float32).copy()
    signal[mask] = np.nan
    row_valid = row_result["final_valid"]
    freq = case["frequency_mhz"]
    cleaned_coarse, coarse_freq, counts = module.coarsen(cleaned, freq, row_valid)
    truth_coarse, _, _ = module.coarsen(truth, freq, row_valid)
    signal_coarse, _, _ = module.coarsen(signal, freq, row_valid)
    burst = tuple(case["parameters"]["windows"]["burst"])
    truth_measure = module.measure_summary(
        truth_coarse,
        coarse_freq,
        counts > 0,
        case["parameters"]["dt_ms"],
        burst,
        signal_coarse,
    )
    cleaned_measure = module.measure_summary(
        cleaned_coarse,
        coarse_freq,
        counts > 0,
        case["parameters"]["dt_ms"],
        burst,
        signal_coarse,
    )
    differences = {}
    for key, truth_value in truth_measure.items():
        cleaned_value = cleaned_measure.get(key)
        if truth_value is None or cleaned_value is None:
            differences[key] = None
        else:
            differences[key] = float(cleaned_value) - float(truth_value)
    return {
        "truth": truth_measure,
        "cleaned": cleaned_measure,
        "difference": differences,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--prototype-script", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    module = load_module(args.prototype_script)
    root = args.input_root
    frequency = np.load(root / "products/zach_chime_freq.npy")
    source_valid = np.load(root / "products/zach_chime_source_valid.npy").astype(bool)
    mean = np.load(root / "diagnostics/audit-v2/zach_bandpass_mean.npy")
    scale = np.load(root / "diagnostics/audit-v2/zach_bandpass_scale.npy")
    case = module.generate_case(
        frequency,
        source_valid,
        mean,
        scale,
        512,
        0.32768,
        module.SEED,
    )
    training = tuple(case["parameters"]["windows"]["training"])
    audit = root / "code/audit_chime_preprocessing_v2.py"
    contaminated = module.run_rejected_cleaner(case["raw"], source_valid, training, audit)
    raw_clean = (
        case["bandpass_mean"][:, None]
        + case["bandpass_scale"][:, None] * case["truth"]
    ).astype(np.float32)
    clean = module.run_rejected_cleaner(raw_clean, source_valid, training, audit)
    valid_pixels = np.broadcast_to(source_valid[:, None], case["rfi_mask"].shape)

    results = {}
    for method in ("row_only", "clip6", "grow6_4"):
        contaminated_dynamic = dynamic_mask(contaminated["cleaned"], method)
        contaminated_predicted = predicted_mask(
            contaminated["final_valid"], contaminated_dynamic
        )
        clean_dynamic = dynamic_mask(clean["cleaned"], method)
        clean_predicted = predicted_mask(clean["final_valid"], clean_dynamic)
        component_recall = {}
        for name, component in case["component_masks"].items():
            counts = confusion(component, contaminated_predicted, valid_pixels)
            component_recall[name] = counts["recall"]
        results[method] = {
            "contaminated": confusion(
                case["rfi_mask"], contaminated_predicted, valid_pixels
            ),
            "component_recall": component_recall,
            "clean_false_rejection_fraction": float(
                np.sum(valid_pixels & clean_predicted) / np.sum(valid_pixels)
            ),
            "additional_contaminated_pixels": int(contaminated_dynamic.sum()),
            "additional_clean_pixels": int(clean_dynamic.sum()),
            "measurements": measure_candidate(
                module,
                case,
                contaminated,
                contaminated_predicted,
            ),
        }

    payload = {
        "status": "throwaway_known_truth_experiment",
        "thresholds": {
            "clip6": {"absolute_seed": 6.0},
            "grow6_4": {"absolute_seed": 6.0, "absolute_growth": 4.0},
        },
        "results": results,
    }
    args.output.write_text(json.dumps(module._json_safe(payload), indent=2, sort_keys=True) + "\n")
    print(json.dumps(module._json_safe(payload), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
