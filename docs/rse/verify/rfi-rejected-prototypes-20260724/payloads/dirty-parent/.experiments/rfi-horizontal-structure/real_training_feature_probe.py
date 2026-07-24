#!/usr/bin/env python3
"""Probe training-only tail features against Zach diagnostic residuals.

Residual spectra are evaluation labels only. Candidate features and masks use
the frozen off-pulse training slice exclusively.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np


TRAINING = (55, 137)


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("audit", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def describe(values: np.ndarray) -> dict[str, float]:
    return {
        str(q): float(np.quantile(values, q))
        for q in (0.5, 0.9, 0.99, 0.999, 0.9999, 1.0)
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--review-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source = np.load(args.input_root / "products/zach_chime_upchan.npy", mmap_mode="r")
    training = np.array(source[:, TRAINING[0] : TRAINING[1]], dtype=np.float64)
    del source
    frequency = np.load(args.input_root / "products/zach_chime_freq.npy")
    source_valid = np.load(args.input_root / "products/zach_chime_source_valid.npy").astype(bool)
    audit = load_module(args.input_root / "code/audit_chime_preprocessing_v2.py")

    initial = audit._package_rfi_mask(
        training, source_valid, (0, training.shape[1]), threshold_mean=5.0, threshold_std=3.0
    )
    initial_valid = source_valid & ~initial
    mean, scale, model_valid = audit._bandpass_model(
        training, initial_valid, (0, training.shape[1])
    )
    normalized = audit._normalize(training, mean, scale, model_valid)
    post = audit._package_rfi_mask(
        normalized, model_valid, (0, training.shape[1]), threshold_mean=5.0, threshold_std=3.0
    )
    final_valid = model_valid & ~post
    normalized[~final_valid] = np.nan

    absolute = np.abs(normalized)
    features = {
        "maximum_absolute": np.nanmax(absolute, axis=1),
        "count_absolute_ge_3_5": np.sum(absolute >= 3.5, axis=1),
        "count_absolute_ge_4": np.sum(absolute >= 4.0, axis=1),
        "count_absolute_ge_4_5": np.sum(absolute >= 4.5, axis=1),
        "count_absolute_ge_5": np.sum(absolute >= 5.0, axis=1),
        "fourth_moment": np.nanmean(normalized**4, axis=1),
        "maximum_difference": np.nanmax(np.abs(np.diff(normalized, axis=1)), axis=1),
    }
    spectrum = np.load(args.review_root / "reference_common_spectrum.npy")
    intervals = {}
    for label, low, high in (("600_650", 600.0, 650.0), ("700_750", 700.0, 750.0)):
        use = final_valid & np.isfinite(spectrum) & (frequency >= low) & (frequency < high)
        rows = np.flatnonzero(use)
        order = rows[np.argsort(spectrum[rows])[::-1][:25]]
        intervals[label] = [
            {
                "row": int(row),
                "frequency_mhz": float(frequency[row]),
                "spectrum": float(spectrum[row]),
                **{name: float(value[row]) for name, value in features.items()},
            }
            for row in order
        ]

    valid_features = {
        name: describe(np.asarray(value[final_valid], dtype=float))
        for name, value in features.items()
    }
    candidates = {}
    for threshold in (4.0, 4.5, 5.0, 5.5, 6.0):
        mask = final_valid & (features["maximum_absolute"] >= threshold)
        candidates[f"maximum_absolute_ge_{threshold:g}"] = {
            "selected": int(mask.sum()),
            "selected_600_650": int(np.sum(mask & (frequency >= 600) & (frequency < 650))),
            "selected_700_750": int(np.sum(mask & (frequency >= 700) & (frequency < 750))),
            "top25_overlap_600_650": int(
                sum(mask[item["row"]] for item in intervals["600_650"])
            ),
            "top25_overlap_700_750": int(
                sum(mask[item["row"]] for item in intervals["700_750"])
            ),
        }
    args.output.write_text(
        json.dumps(
            {
                "training": list(TRAINING),
                "feature_distributions": valid_features,
                "top_residual_rows": intervals,
                "candidate_counts": candidates,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
