#!/usr/bin/env python3
"""Probe protected off-pulse moderate-amplitude occupancy on real Zach data."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("real_zach_review", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--review-script", type=Path, required=True)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    review = load_module(args.review_script)
    observed = np.load(args.input_root / "products/zach_chime_upchan.npy", mmap_mode="r")
    training, context = review.load_allowed_slices(observed)
    del observed
    frequency = np.load(args.input_root / "products/zach_chime_freq.npy")
    source_valid = np.load(
        args.input_root / "products/zach_chime_source_valid.npy"
    ).astype(bool)
    metadata = json.loads(
        (args.input_root / "products/zach_chime_preprocessing_metadata.json").read_text()
    )
    result = review.apply_methods(
        training,
        context,
        source_valid,
        args.input_root / "code/audit_chime_preprocessing_v2.py",
    )
    coarse_ids, coarse_frequency = review.nominal_coarse_ids(frequency)
    fpga = {
        int(coarse_id): int(count)
        for coarse_id, count in zip(
            metadata["freq_id"], metadata["fpga_count"], strict=True
        )
    }
    shifts = np.zeros(frequency.size, dtype=np.int64)
    shifts[source_valid], _ = review.alignment_shifts(
        coarse_frequency[source_valid],
        coarse_ids[source_valid],
        fpga,
        target_dm=review.COHERENT_DM,
        native_dt_s=review.NATIVE_DT_S,
        output_dt_s=review.DT_MS * 1e-3,
    )
    aligned = review.align_nonwrapping(result["row_only_context"], shifts)
    crop_start = review.DISPLAY[0] - review.SOURCE_CONTEXT[0]
    crop_stop = review.DISPLAY[1] - review.SOURCE_CONTEXT[0]
    display = aligned[:, crop_start:crop_stop]
    on = (
        review.ON_PULSE[0] - review.DISPLAY[0],
        review.ON_PULSE[1] - review.DISPLAY[0],
    )
    off = np.concatenate((display[:, : on[0]], display[:, on[1] :]), axis=1)
    final_valid = np.load(args.candidate_root / "final_valid.npy").astype(bool)
    candidate_valid = np.load(args.candidate_root / "candidate_valid.npy").astype(bool)

    off_mean = np.nanmean(off, axis=1)
    off_standard_deviation = np.nanstd(off, axis=1)
    local_features = {}
    for name, values in {
        "off_mean": off_mean,
        "off_standard_deviation": off_standard_deviation,
    }.items():
        local_z = np.full(values.shape, np.nan)
        for start in range(0, values.size, 64):
            stop = start + 64
            use = final_valid[start:stop] & np.isfinite(values[start:stop])
            if not np.any(use):
                continue
            center = np.median(values[start:stop][use])
            spread = 1.4826 * np.median(np.abs(values[start:stop][use] - center))
            if spread > 0:
                local_z[start:stop] = (values[start:stop] - center) / spread
        local_features[name] = local_z

    thresholds = (2.5, 3.0, 3.5, 4.0)
    diagnostics = {}
    for threshold in thresholds:
        extreme = np.isfinite(off) & (np.abs(off) >= threshold)
        denominator = max(int(final_valid.sum()), 1)
        broadband = np.sum(extreme & final_valid[:, None], axis=0) / denominator > 0.05
        protected_extreme = extreme[:, ~broadband]
        hits = np.sum(protected_extreme, axis=1)
        diagnostics[str(threshold)] = {
            "broadband_columns_excluded": int(broadband.sum()),
            "hit_count_quantiles": {
                str(q): float(np.quantile(hits[final_valid], q))
                for q in (0.5, 0.9, 0.99, 0.999, 1.0)
            },
            "selected_counts": {
                str(minimum_hits): int(np.sum(final_valid & (hits >= minimum_hits)))
                for minimum_hits in (2, 3, 4, 5, 6, 8)
            },
            "selected_counts_surviving_composite": {
                str(minimum_hits): int(np.sum(candidate_valid & (hits >= minimum_hits)))
                for minimum_hits in (2, 3, 4, 5, 6, 8)
            },
            "rows_700_750_surviving_composite": [
                {
                    "row": int(row),
                    "frequency_mhz": float(frequency[row]),
                    "hits": int(hits[row]),
                    "maximum_absolute": float(np.nanmax(np.abs(off[row, ~broadband]))),
                }
                for row in np.flatnonzero(
                    candidate_valid
                    & (frequency >= 700.0)
                    & (frequency < 750.0)
                    & (hits >= 2)
                )[np.argsort(
                    hits[
                        candidate_valid
                        & (frequency >= 700.0)
                        & (frequency < 750.0)
                        & (hits >= 2)
                    ]
                )[::-1]][:100]
            ],
        }
    diagnostics["local_feature_outliers"] = {}
    for low, high in ((700.0, 750.0), (730.0, 734.0), (745.0, 750.0)):
        band = candidate_valid & (frequency >= low) & (frequency < high)
        rows = np.flatnonzero(band)
        ordering = np.argsort(
            np.maximum(
                np.abs(local_features["off_mean"][rows]),
                np.abs(local_features["off_standard_deviation"][rows]),
            )
        )[::-1]
        diagnostics["local_feature_outliers"][f"{low:g}_{high:g}"] = [
            {
                "row": int(row),
                "frequency_mhz": float(frequency[row]),
                "off_mean": float(off_mean[row]),
                "off_standard_deviation": float(off_standard_deviation[row]),
                "local_z_off_mean": float(local_features["off_mean"][row]),
                "local_z_off_standard_deviation": float(
                    local_features["off_standard_deviation"][row]
                ),
            }
            for row in rows[ordering[:50]]
        ]
    args.output.write_text(json.dumps(diagnostics, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
