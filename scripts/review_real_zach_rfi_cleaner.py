#!/usr/bin/env python3
"""Render a diagnostic-only comparison on Zach's observed CHIME/FRB burst.

Only the public training slice and configured burst slice are loaded as
numerical samples. The full file is byte-read only for its checksum. This is a
method comparison, not cleaner validation.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import shutil
from pathlib import Path
from typing import Any

import numpy as np


STATUS = "diagnostic_only_real_event_method_comparison"
TRAINING = (55, 137)
BURST = (232, 248)
DT_MS = 0.32768
FRAME_CENTER_OFFSET_MS = 63.5 * 2.56e-3
EXPECTED = {
    "products/zach_chime_upchan.npy": "974551c7386cb5dd77b0572be133a57f6c8faf6be40357cb197d787c259f541e",
    "products/zach_chime_freq.npy": "02c794745bd79ca235d1d3e18d46b2f43f7529616a5747ccab2a5db094a9cba2",
    "products/zach_chime_source_valid.npy": "b183f4aaed375ae78da8000cd5cb8bc3b8c4500c9ff23e56bb9555b0b85ba39e",
    "products/zach_chime_preprocessing_metadata.json": "bdc588557c7f8750e8714b6267569a7741b03994590c7cc9beabe21c482dca65",
    "code/audit_chime_preprocessing_v2.py": "5df48f411c6d9f9ce59873b6ccb147de30e22fa8306b3543bb06632212340c83",
}
EXPECTED_REJECTED_OUTPUTS = {
    "initial_rfi_rows.npy": "e584179a2a81ad35a6f59f0f11bde4a371d8de3582446f726664497ec37dc0d1",
    "combined_mean.npy": "472a58567d60221dd8fa2f91eb3fd855f7893cc28dff112b52c911c04900b753",
    "combined_scale.npy": "e3082210b0ec2d49ed86517446f662b56f01ab14ec03b3903cb890cbaf30027c",
    "post_bandpass_rfi_rows.npy": "f2fc48dde70bb20c891dcf189e22c5783dac63dbc4757a439b48402a32bfbaff",
    "final_valid.npy": "17dc89ce9c0ccd51713b0bba4d45e0442106cf846c0dbd36b316cb9ee0a581f8",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_inputs(root: Path) -> dict[str, str]:
    found = {}
    for relative, expected in EXPECTED.items():
        path = root / relative
        actual = sha256(path)
        if actual != expected:
            raise ValueError(f"input hash mismatch for {relative}: {actual}")
        found[relative] = actual
    return found


def load_allowed_slices(array: Any) -> tuple[np.ndarray, np.ndarray]:
    """Read exactly the approved training and burst columns."""
    if tuple(array.shape) != (65536, 437):
        raise ValueError(f"unexpected observed-array shape: {array.shape}")
    training = np.array(array[:, TRAINING[0] : TRAINING[1]], dtype=np.float32, copy=True)
    burst = np.array(array[:, BURST[0] : BURST[1]], dtype=np.float32, copy=True)
    return training, burst


def _load_audit(path: Path):
    spec = importlib.util.spec_from_file_location("exact_audit_v2", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def apply_methods(
    training: np.ndarray,
    burst: np.ndarray,
    source_valid: np.ndarray,
    audit_path: Path,
) -> dict[str, np.ndarray]:
    """Learn both methods on training only, then apply them to the burst."""
    audit = _load_audit(audit_path)
    compact = np.concatenate((training, burst), axis=1)
    compact_training = (0, training.shape[1])

    reference_mean, reference_scale, reference_valid = audit._bandpass_model(
        compact, source_valid, compact_training
    )
    reference = audit._normalize(
        compact, reference_mean, reference_scale, reference_valid
    )

    initial = audit._package_rfi_mask(
        compact,
        source_valid,
        compact_training,
        threshold_mean=5.0,
        threshold_std=3.0,
    )
    initial_valid = source_valid & ~initial
    combined_mean, combined_scale, model_valid = audit._bandpass_model(
        compact, initial_valid, compact_training
    )
    combined = audit._normalize(compact, combined_mean, combined_scale, model_valid)
    post = audit._package_rfi_mask(
        combined,
        model_valid,
        compact_training,
        threshold_mean=5.0,
        threshold_std=3.0,
    )
    final_valid = model_valid & ~post
    combined[~final_valid] = np.nan

    burst_start = training.shape[1]
    return {
        "reference_burst": np.asarray(reference[:, burst_start:], dtype=np.float32),
        "combined_burst": np.asarray(combined[:, burst_start:], dtype=np.float32),
        "reference_mean": reference_mean,
        "reference_scale": reference_scale,
        "reference_valid": reference_valid,
        "initial_rfi_rows": initial,
        "combined_mean": combined_mean,
        "combined_scale": combined_scale,
        "model_valid": model_valid,
        "post_bandpass_rfi_rows": post,
        "final_valid": final_valid,
    }


def coarsen(
    values: np.ndarray,
    frequency_mhz: np.ndarray,
    valid_rows: np.ndarray,
    factor: int = 64,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    values = np.asarray(values, dtype=np.float64)
    frequency = np.asarray(frequency_mhz, dtype=np.float64)
    valid = np.asarray(valid_rows, dtype=bool)
    groups = values.shape[0] // factor
    grouped = values.reshape(groups, factor, values.shape[1])
    grouped_valid = valid.reshape(groups, factor)
    finite = np.isfinite(grouped) & grouped_valid[:, :, None]
    counts_time = finite.sum(axis=1)
    sums = np.where(finite, grouped, 0.0).sum(axis=1)
    coarse = np.full((groups, values.shape[1]), np.nan)
    np.divide(sums, counts_time, out=coarse, where=counts_time > 0)
    row_counts = grouped_valid.sum(axis=1)
    freq_sum = np.where(grouped_valid, frequency.reshape(groups, factor), 0.0).sum(axis=1)
    coarse_frequency = np.full(groups, np.nan)
    np.divide(freq_sum, row_counts, out=coarse_frequency, where=row_counts > 0)
    return coarse, coarse_frequency, row_counts


def time_profile(values: np.ndarray, valid_rows: np.ndarray) -> np.ndarray:
    valid = np.asarray(valid_rows, dtype=bool)
    return np.nanmean(np.asarray(values, dtype=np.float64)[valid], axis=0)


def broad_band_sums(
    values: np.ndarray, frequency_mhz: np.ndarray, valid_rows: np.ndarray
) -> tuple[list[str], list[float | None]]:
    spectrum = np.nansum(np.asarray(values, dtype=np.float64), axis=1)
    labels, sums = [], []
    for low in range(400, 800, 50):
        use = valid_rows & (frequency_mhz >= low) & (frequency_mhz < low + 50)
        labels.append(f"{low}–{low + 50}")
        sums.append(float(np.nanmean(spectrum[use])) if np.any(use) else None)
    return labels, sums


def make_figure(
    path: Path,
    frequency_mhz: np.ndarray,
    source_valid: np.ndarray,
    result: dict[str, np.ndarray],
    bands: dict[str, Any],
) -> None:
    import matplotlib as mpl
    import matplotlib.pyplot as plt

    mpl.rcParams.update(
        {
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "legend.fontsize": 8,
            "svg.hashsalt": "faber2026-real-zach-rfi-review",
        }
    )
    final_valid = result["final_valid"]
    reference = result["reference_burst"]
    combined = result["combined_burst"]
    reference_common = reference.copy()
    reference_common[~final_valid] = np.nan

    ref_coarse, coarse_frequency, _ = coarsen(reference, frequency_mhz, source_valid)
    common_coarse, _, common_counts = coarsen(reference_common, frequency_mhz, final_valid)
    combined_coarse, _, _ = coarsen(combined, frequency_mhz, final_valid)
    method_difference = combined_coarse - common_coarse

    time_centers = FRAME_CENTER_OFFSET_MS + np.arange(BURST[0], BURST[1]) * DT_MS
    extent = [
        time_centers[0] - DT_MS / 2,
        time_centers[-1] + DT_MS / 2,
        float(np.nanmin(coarse_frequency)),
        float(np.nanmax(coarse_frequency)),
    ]
    comparable = np.concatenate(
        [ref_coarse[np.isfinite(ref_coarse)], combined_coarse[np.isfinite(combined_coarse)]]
    )
    limit = max(0.5, float(np.percentile(np.abs(comparable), 99.5)))
    diff_finite = method_difference[np.isfinite(method_difference)]
    difference_limit = max(0.05, float(np.percentile(np.abs(diff_finite), 99.5)))
    cmap = mpl.colormaps["RdBu_r"].copy()
    cmap.set_bad("0.76")

    fig = plt.figure(figsize=(15, 8.2), constrained_layout=True)
    grid = fig.add_gridspec(2, 3, height_ratios=(1.15, 0.85))
    top = [
        (ref_coarse, "Bandpass only — full measured support"),
        (common_coarse, "Bandpass only — cleaner-retained support"),
        (combined_coarse, "Rejected cleaner — same retained support"),
    ]
    images = []
    top_axes = []
    for column, (data, title) in enumerate(top):
        ax = fig.add_subplot(grid[0, column])
        top_axes.append(ax)
        image = ax.imshow(
            np.ma.masked_invalid(data),
            origin="lower",
            aspect="auto",
            extent=extent,
            cmap=cmap,
            vmin=-limit,
            vmax=limit,
            interpolation="nearest",
        )
        images.append(image)
        ax.set_title(title)
        ax.set_xlabel("Relative product time (ms)")
        if column == 0:
            ax.set_ylabel("Frequency (MHz)")
    fig.colorbar(images[0], ax=top_axes, label="Standardized intensity", shrink=0.8)

    ax_profile = fig.add_subplot(grid[1, 0])
    ax_profile.plot(time_centers, time_profile(reference, source_valid), label="bandpass only, full", lw=1.2)
    ax_profile.plot(time_centers, time_profile(reference_common, final_valid), label="bandpass only, retained", lw=1.2)
    ax_profile.plot(time_centers, time_profile(combined, final_valid), label="rejected cleaner, retained", lw=1.2)
    ax_profile.set_title("Frequency-averaged burst profile")
    ax_profile.set_xlabel("Relative product time (ms)")
    ax_profile.set_ylabel("Mean standardized intensity")
    ax_profile.legend(frameon=False)

    ax_bands = fig.add_subplot(grid[1, 1])
    x = np.arange(len(bands["labels"]))
    width = 0.26
    for offset, key, label in (
        (-width, "reference_full", "bandpass only, full"),
        (0.0, "reference_common", "bandpass only, retained"),
        (width, "combined_common", "rejected cleaner, retained"),
    ):
        values = np.array([np.nan if v is None else v for v in bands[key]])
        ax_bands.bar(x + offset, values, width, label=label)
    ax_bands.set_xticks(x, bands["labels"], rotation=45, ha="right")
    ax_bands.set_title("Burst sum by fixed 50-MHz band")
    ax_bands.set_xlabel("Frequency range (MHz)")
    ax_bands.set_ylabel("Mean standardized sum")
    ax_bands.legend(frameon=False)

    ax_difference = fig.add_subplot(grid[1, 2])
    difference_image = ax_difference.imshow(
        np.ma.masked_invalid(method_difference),
        origin="lower",
        aspect="auto",
        extent=extent,
        cmap=cmap,
        vmin=-difference_limit,
        vmax=difference_limit,
        interpolation="nearest",
    )
    ax_difference.set_title("Difference is zero on retained rows; gray = not retained")
    ax_difference.set_xlabel("Relative product time (ms)")
    ax_difference.set_ylabel("Frequency (MHz)")
    fig.colorbar(difference_image, ax=ax_difference, label="Difference", shrink=0.8)

    fig.savefig(path, format="svg", metadata={"Date": None, "Creator": "Faber2026"})
    plt.close(fig)
    path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")


def _save_arrays(output_dir: Path, result: dict[str, np.ndarray]) -> dict[str, str]:
    hashes = {}
    for key in (
        "reference_mean",
        "reference_scale",
        "reference_valid",
        "initial_rfi_rows",
        "combined_mean",
        "combined_scale",
        "model_valid",
        "post_bandpass_rfi_rows",
        "final_valid",
    ):
        path = output_dir / f"{key}.npy"
        np.save(path, result[key])
        hashes[path.name] = sha256(path)
    return hashes


def run(args: argparse.Namespace) -> dict[str, Any]:
    root = args.input_root.resolve()
    output = args.output_dir.resolve()
    if output.exists():
        raise FileExistsError(output)
    inputs = verify_inputs(root)
    output.mkdir(parents=True)

    observed = np.load(root / "products/zach_chime_upchan.npy", mmap_mode="r")
    training, burst = load_allowed_slices(observed)
    del observed
    frequency = np.load(root / "products/zach_chime_freq.npy")
    source_valid = np.load(root / "products/zach_chime_source_valid.npy").astype(bool)
    result = apply_methods(
        training,
        burst,
        source_valid,
        root / "code/audit_chime_preprocessing_v2.py",
    )

    reference = result["reference_burst"]
    reference_common = reference.copy()
    reference_common[~result["final_valid"]] = np.nan
    labels, reference_full_bands = broad_band_sums(reference, frequency, source_valid)
    _, reference_common_bands = broad_band_sums(reference_common, frequency, result["final_valid"])
    _, combined_common_bands = broad_band_sums(
        result["combined_burst"], frequency, result["final_valid"]
    )
    bands = {
        "labels": labels,
        "reference_full": reference_full_bands,
        "reference_common": reference_common_bands,
        "combined_common": combined_common_bands,
    }
    common = result["final_valid"][:, None] & np.isfinite(reference_common)
    common_difference = result["combined_burst"][common] - reference_common[common]

    figure = output / "real_zach_rfi_method_comparison.svg"
    make_figure(figure, frequency, source_valid, result, bands)
    array_hashes = _save_arrays(output, result)
    for name, expected in EXPECTED_REJECTED_OUTPUTS.items():
        if array_hashes[name] != expected:
            raise ValueError(f"rejected-cleaner artifact mismatch for {name}")
    script_copy = output / Path(__file__).name
    shutil.copy2(Path(__file__).resolve(), script_copy)
    record = {
        "status": STATUS,
        "warning": "Observed event with no known truth; this does not validate the cleaner.",
        "event": "zach",
        "instrument": "CHIME/FRB",
        "approved_observed_slices_half_open": {"training": list(TRAINING), "burst": list(BURST)},
        "observed_columns_read": [list(TRAINING), list(BURST)],
        "time_axis": {
            "label": "relative product time",
            "cadence_ms": DT_MS,
            "frame_center_formula": "(128*j + 63.5) * 2.56 microseconds",
            "absolute_arrival_time_status": "uncertified",
        },
        "provisional_dedispersion_measure_pc_cm3": 262.368,
        "dedispersion_measure_status": "not adopted",
        "methods": {
            "reference": "bandpass mean and sample standard deviation learned on training without RFI mask",
            "rejected_cleaner": [
                "package RFI row mask on training",
                "bandpass mean and sample standard deviation on surviving training rows",
                "normalize",
                "second package RFI row mask on normalized training",
            ],
            "package_threshold_mean": 5.0,
            "package_threshold_standard_deviation": 3.0,
        },
        "support": {
            "source_valid_rows": int(source_valid.sum()),
            "bandpass_only_valid_rows": int(result["reference_valid"].sum()),
            "cleaner_final_valid_rows": int(result["final_valid"].sum()),
            "additional_measured_rows_removed": int(
                np.sum(source_valid & ~result["final_valid"])
            ),
            "cleaner_retained_fraction_of_source": float(
                result["final_valid"].sum() / source_valid.sum()
            ),
        },
        "method_comparison": {
            "common_support_values_equal": bool(
                np.array_equal(result["combined_burst"][common], reference_common[common])
            ),
            "maximum_absolute_common_support_difference": float(
                np.max(np.abs(common_difference))
            ),
            "interpretation": "On retained rows, the methods are identical; the cleaner changes only row support.",
        },
        "broad_frequency_sums": bands,
        "provenance": {
            "input_hashes": inputs,
            "source_h5": "/data/Faber2026/data/chime-frb/zach/singlebeam_210456524.h5",
            "source_h5_sha256": "215079a689c18b50a4b2cd8003529e34d531a326be677a86187be02e47d0f1a9",
            "container_digest": args.container_digest,
            "container_image_id": args.container_image_id,
            "pipeline_revision": args.pipeline_revision,
            "script_sha256": sha256(script_copy),
            "python": platform.python_version(),
            "numpy": np.__version__,
            "array_hashes": array_hashes,
            "rejected_cleaner_outputs_match_prior_audit": True,
            "baseband_analysis_version": "1.9.0",
            "baseband_analysis_revision": "e08df9dacc49e1007f28759b7edca71c7b8e5273",
            "command": (
                "python /review/code/review_real_zach_rfi_cleaner.py "
                "--input-root /evidence --output-dir /review/run-N"
            ),
        },
    }
    json_path = output / "real_zach_rfi_method_comparison.json"
    json_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    checksums = output / "SHA256SUMS"
    paths = sorted(p for p in output.iterdir() if p.name != "SHA256SUMS")
    checksums.write_text("\n".join(f"{sha256(path)}  {path.name}" for path in paths) + "\n")
    return record


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--container-digest",
        default="chimefrb/baseband-analysis@sha256:f510909d892d0d5224c982c590cbe80967a49a59b79c396ab72bb710105c4c41",
    )
    parser.add_argument(
        "--container-image-id",
        default="sha256:8c903ec6a5a836e8a97fe3468fd3ee02177c220ead84e6d1d25e8f41b735db4b",
    )
    parser.add_argument(
        "--pipeline-revision", default="ab6af1f713496abd2ff2d71bf11edf4100871e94"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    run(parse_args(argv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
