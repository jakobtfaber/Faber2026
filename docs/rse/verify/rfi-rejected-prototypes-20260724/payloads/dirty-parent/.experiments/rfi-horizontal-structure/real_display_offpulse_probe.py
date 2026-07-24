#!/usr/bin/env python3
"""Probe display off-pulse row features against Zach residual diagnostics."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def mad_z(values: np.ndarray, use: np.ndarray) -> np.ndarray:
    selected = values[use]
    center = np.median(selected)
    spread = 1.4826 * np.median(np.abs(selected - center))
    result = np.zeros(values.shape)
    if spread > 0:
        result[use] = (values[use] - center) / spread
    return result


def iterative_mask(features: dict[str, np.ndarray], valid: np.ndarray, names: tuple[str, ...]) -> np.ndarray:
    rejected = np.zeros(valid.shape, dtype=bool)
    for _ in range(6):
        keep = valid & ~rejected
        newly = np.zeros(valid.shape, dtype=bool)
        for name in names:
            newly |= keep & (np.abs(mad_z(features[name], keep)) > 5.0)
        if not newly.any():
            break
        rejected |= newly
    return rejected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--review-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    review = load_module(args.review_root / "code/review_real_zach_rfi_cleaner.py", "review")

    observed = np.load(args.input_root / "products/zach_chime_upchan.npy", mmap_mode="r")
    training, context = review.load_allowed_slices(observed)
    del observed
    frequency = np.load(args.input_root / "products/zach_chime_freq.npy")
    source_valid = np.load(args.input_root / "products/zach_chime_source_valid.npy").astype(bool)
    metadata = json.loads((args.input_root / "products/zach_chime_preprocessing_metadata.json").read_text())
    result = review.apply_methods(
        training, context, source_valid, args.input_root / "code/audit_chime_preprocessing_v2.py"
    )
    coarse_ids, coarse_frequency = review.nominal_coarse_ids(frequency)
    fpga = {int(cid): int(count) for cid, count in zip(metadata["freq_id"], metadata["fpga_count"], strict=True)}
    shifts = np.zeros(frequency.size, dtype=np.int64)
    valid_shifts, _ = review.alignment_shifts(
        coarse_frequency[source_valid], coarse_ids[source_valid], fpga,
        target_dm=review.COHERENT_DM, native_dt_s=review.NATIVE_DT_S,
        output_dt_s=review.DT_MS * 1e-3,
    )
    shifts[source_valid] = valid_shifts
    aligned = review.align_nonwrapping(result["row_only_context"], shifts)
    candidate_aligned = review.align_nonwrapping(result["combined_context"], shifts)
    crop_start = review.DISPLAY[0] - review.SOURCE_CONTEXT[0]
    crop_stop = review.DISPLAY[1] - review.SOURCE_CONTEXT[0]
    display = aligned[:, crop_start:crop_stop]
    candidate_display = candidate_aligned[:, crop_start:crop_stop]
    on = (review.ON_PULSE[0] - review.DISPLAY[0], review.ON_PULSE[1] - review.DISPLAY[0])
    off = np.concatenate((display[:, : on[0]], display[:, on[1] :]), axis=1)
    candidate_off = np.concatenate(
        (candidate_display[:, : on[0]], candidate_display[:, on[1] :]), axis=1
    )
    pixel6_offpulse_hits = np.sum(
        np.isfinite(off) & ~np.isfinite(candidate_off), axis=1
    )
    valid = result["final_valid"] & np.all(np.isfinite(off), axis=1)
    centered = off - np.nanmean(off, axis=1, keepdims=True)
    denominator = np.nansum(centered**2, axis=1)
    lag1 = np.zeros(frequency.size)
    np.divide(
        np.nansum(centered[:, 1:] * centered[:, :-1], axis=1),
        denominator,
        out=lag1,
        where=denominator > 0,
    )
    features = {
        "mean": np.nanmean(off, axis=1),
        "standard_deviation": np.nanstd(off, axis=1),
        "lag1": lag1,
        "fourth_moment": np.nanmean(centered**4, axis=1),
        "maximum_absolute": np.nanmax(np.abs(off), axis=1),
    }
    local_z = {}
    for name, values in features.items():
        grouped = values.reshape(-1, 64)
        grouped_valid = valid.reshape(-1, 64)
        z = np.zeros(values.shape, dtype=float)
        for group in range(grouped.shape[0]):
            use = grouped_valid[group] & np.isfinite(grouped[group])
            if not np.any(use):
                continue
            center = np.median(grouped[group, use])
            spread = 1.4826 * np.median(np.abs(grouped[group, use] - center))
            if spread > 0:
                z[group * 64 : (group + 1) * 64] = (grouped[group] - center) / spread
        local_z[name] = z
    configurations = {
        "mean": ("mean",),
        "standard_deviation": ("standard_deviation",),
        "mean_standard_deviation": ("mean", "standard_deviation"),
        "mean_standard_deviation_lag1": ("mean", "standard_deviation", "lag1"),
        "all": tuple(features),
    }
    spectrum = np.load(args.review_root / "zach-1/reference_common_spectrum.npy")
    top = {}
    for label, low, high in (("600_650", 600, 650), ("700_750", 700, 750)):
        use = valid & np.isfinite(spectrum) & (frequency >= low) & (frequency < high)
        rows = np.flatnonzero(use)
        top[label] = rows[np.argsort(spectrum[rows])[::-1][:25]]
    masks = {name: iterative_mask(features, valid, names) for name, names in configurations.items()}
    threshold_masks = {
        f"maximum_absolute_ge_{threshold:g}": valid
        & (features["maximum_absolute"] >= threshold)
        for threshold in (5.0, 6.0, 7.0, 8.0, 10.0)
    }
    threshold_masks.update(
        {
            f"fourth_moment_ge_{threshold:g}": valid
            & (features["fourth_moment"] >= threshold)
            for threshold in (25.0, 50.0, 100.0, 250.0, 500.0)
        }
    )
    seed_rows = valid & (pixel6_offpulse_hits >= 1)
    seed_count_by_coarse = seed_rows.reshape(-1, 64).sum(axis=1)
    for threshold in (2, 3, 4, 5, 8):
        contaminated_coarse = np.repeat(seed_count_by_coarse >= threshold, 64)
        threshold_masks[
            f"pixel6_seed_rows_in_coarse_with_ge_{threshold}_seed_rows"
        ] = seed_rows & contaminated_coarse
        threshold_masks[
            f"full_coarse_with_ge_{threshold}_pixel6_seed_rows"
        ] = result["final_valid"] & contaminated_coarse
    threshold_masks.update(
        {
            f"pixel6_offpulse_hits_ge_{threshold}": valid
            & (pixel6_offpulse_hits >= threshold)
            for threshold in (1, 2, 3, 4)
        }
    )
    record = {
        "offpulse_display_columns": [[0, on[0]], [on[1], display.shape[1]]],
        "onpulse_excluded_columns": list(on),
        "valid_rows_with_complete_offpulse_support": int(valid.sum()),
        "feature_distributions": {
            name: {
                str(q): float(np.quantile(value[valid], q))
                for q in (0.5, 0.9, 0.99, 0.999, 1.0)
            }
            for name, value in features.items()
        },
        "configurations": {
            name: {
                "features": list(configurations[name]),
                "selected": int(mask.sum()),
                "selected_600_650": int(np.sum(mask & (frequency >= 600) & (frequency < 650))),
                "selected_700_750": int(np.sum(mask & (frequency >= 700) & (frequency < 750))),
                "top25_overlap_600_650": int(np.sum(mask[top["600_650"]])),
                "top25_overlap_700_750": int(np.sum(mask[top["700_750"]])),
            }
            for name, mask in masks.items()
        },
        "threshold_candidates": {
            name: {
                "selected": int(mask.sum()),
                "selected_600_650": int(np.sum(mask & (frequency >= 600) & (frequency < 650))),
                "selected_700_750": int(np.sum(mask & (frequency >= 700) & (frequency < 750))),
                "top25_overlap_600_650": int(np.sum(mask[top["600_650"]])),
                "top25_overlap_700_750": int(np.sum(mask[top["700_750"]])),
            }
            for name, mask in threshold_masks.items()
        },
        "top_residual_rows": {
            band: [
                {
                    "row": int(row),
                    "frequency_mhz": float(frequency[row]),
                    "spectrum": float(spectrum[row]),
                    **{key: float(value[row]) for key, value in features.items()},
                    **{
                        f"coarse_local_z_{key}": float(value[row])
                        for key, value in local_z.items()
                    },
                    "pixel6_offpulse_hits": int(pixel6_offpulse_hits[row]),
                    **{f"selected_{name}": bool(mask[row]) for name, mask in masks.items()},
                    **{
                        f"selected_{name}": bool(mask[row])
                        for name, mask in threshold_masks.items()
                        if name.startswith("pixel6_seed_rows_in_coarse")
                    },
                }
                for row in rows
            ]
            for band, rows in top.items()
        },
    }
    args.output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
