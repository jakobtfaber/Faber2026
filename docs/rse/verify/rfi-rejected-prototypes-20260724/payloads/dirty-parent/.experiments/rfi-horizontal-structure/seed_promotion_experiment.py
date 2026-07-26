#!/usr/bin/env python3
"""Known-truth test for protected-offpulse seed-to-row promotion."""

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


def longest_true_run(values: np.ndarray) -> int:
    padded = np.pad(np.asarray(values, dtype=bool), (1, 1))
    edges = np.diff(padded.astype(np.int8))
    starts = np.flatnonzero(edges == 1)
    stops = np.flatnonzero(edges == -1)
    return int(np.max(stops - starts)) if starts.size else 0


def add_saturated_clusters(case: dict, seed: int) -> np.ndarray:
    """Add clustered and isolated saturated fine rows."""
    rng = np.random.default_rng(np.random.SeedSequence(seed, spawn_key=(23,)))
    valid = np.asarray(case["source_valid"], dtype=bool)
    groups = valid.reshape(-1, 64)
    available_groups = np.flatnonzero(groups.sum(axis=1) >= 16)
    chosen_groups = available_groups[
        np.linspace(0, available_groups.size - 1, 12, dtype=int)
    ]
    rows: list[int] = []
    for group in chosen_groups:
        candidates = np.flatnonzero(groups[group]) + group * 64
        rows.extend(candidates[np.linspace(0, candidates.size - 1, 7, dtype=int)])
    remaining_groups = np.setdiff1d(available_groups, chosen_groups)
    isolated_groups = remaining_groups[
        np.linspace(0, remaining_groups.size - 1, 6, dtype=int)
    ]
    for group in isolated_groups:
        candidates = np.flatnonzero(groups[group]) + group * 64
        rows.append(int(candidates[candidates.size // 2]))
    selected_rows = np.unique(rows)

    ntime = case["truth"].shape[1]
    training_stop = case["parameters"]["windows"]["training"][1]
    burst_start, burst_stop = case["parameters"]["windows"]["burst"]
    segments = (
        np.arange(training_stop + 12, training_stop + 22),
        np.arange(burst_start + 30, burst_start + 40),
        np.arange(burst_stop + 20, burst_stop + 30),
    )
    mask = np.zeros_like(case["truth"], dtype=bool)
    values = np.zeros_like(case["truth"], dtype=np.float32)
    for row in selected_rows:
        amplitude = rng.uniform(7.5, 9.0)
        for columns in segments:
            columns = columns[columns < ntime]
            values[row, columns] += amplitude
            mask[row, columns] = True
    case["raw"] += (case["bandpass_scale"][:, None] * values).astype(np.float32)
    case["rfi_standardized"] += values
    case["rfi_mask"] |= mask
    case["component_masks"]["saturated_coarse_clusters"] = mask
    return mask


def run(args: argparse.Namespace) -> dict:
    prototype = load_module("prototype", args.prototype_script)
    candidate = load_module("candidate", args.candidate_script)
    root = args.input_root
    frequency = np.load(root / "products/zach_chime_freq.npy")
    source_valid = np.load(root / "products/zach_chime_source_valid.npy").astype(bool)
    mean = np.load(root / "diagnostics/audit-v2/zach_bandpass_mean.npy")
    scale = np.load(root / "diagnostics/audit-v2/zach_bandpass_scale.npy")
    case = prototype.generate_case(
        frequency, source_valid, mean, scale, 512, 0.32768, args.seed
    )
    saturated_truth = add_saturated_clusters(case, args.seed)
    training = tuple(case["parameters"]["windows"]["training"])
    protected = tuple(case["parameters"]["windows"]["burst"])
    contaminated = prototype.run_rejected_cleaner(
        case["raw"], source_valid, training, args.audit_script
    )
    clean_raw = (
        case["bandpass_mean"][:, None]
        + case["bandpass_scale"][:, None] * case["truth"]
    ).astype(np.float32)
    clean = prototype.run_rejected_cleaner(
        clean_raw, source_valid, training, args.audit_script
    )
    selected, diagnostics = candidate.offpulse_seed_row_mask(
        contaminated["cleaned"], contaminated["final_valid"], protected
    )
    clean_selected, clean_diagnostics = candidate.offpulse_seed_row_mask(
        clean["cleaned"], clean["final_valid"], protected
    )
    predicted = np.broadcast_to(
        (~contaminated["final_valid"] | selected)[:, None], saturated_truth.shape
    )
    contaminated_rows = np.any(saturated_truth, axis=1)
    recovered_rows = np.all(~saturated_truth | predicted, axis=1) & contaminated_rows
    signal = np.abs(case["signal"][:, protected[0] : protected[1]])
    support = contaminated["final_valid"]
    lost = np.sum(signal[support & selected])
    total = np.sum(signal[support])
    residual = np.sum(np.abs(case["rfi_standardized"])[saturated_truth & ~predicted])
    injected = np.sum(np.abs(case["rfi_standardized"])[saturated_truth])
    return {
        "status": "throwaway_known_truth_offpulse_seed_promotion",
        "seed": args.seed,
        "protected_burst": list(protected),
        "configuration": {
            "pixel_threshold": candidate.SEED_PIXEL_THRESHOLD,
            "group_size": candidate.SEED_GROUP_SIZE,
            "minimum_seed_rows_per_group": candidate.MINIMUM_SEED_ROWS_PER_GROUP,
        },
        "injected_saturated_rows": int(contaminated_rows.sum()),
        "fully_recovered_saturated_rows": int(recovered_rows.sum()),
        "longest_surviving_saturated_run_bins": max(
            longest_true_run(saturated_truth[row] & ~predicted[row])
            for row in np.flatnonzero(contaminated_rows)
        ),
        "additional_contaminated_rows": int(selected.sum()),
        "additional_clean_rows": int(clean_selected.sum()),
        "burst_support_loss_fraction": float(lost / total),
        "residual_saturated_intensity_fraction": float(residual / injected),
        "diagnostics": {
            key: value
            for key, value in diagnostics.items()
            if not isinstance(value, np.ndarray)
        },
        "clean_diagnostics": {
            key: value
            for key, value in clean_diagnostics.items()
            if not isinstance(value, np.ndarray)
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--prototype-script", type=Path, required=True)
    parser.add_argument("--candidate-script", type=Path, required=True)
    parser.add_argument("--audit-script", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = run(args)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
