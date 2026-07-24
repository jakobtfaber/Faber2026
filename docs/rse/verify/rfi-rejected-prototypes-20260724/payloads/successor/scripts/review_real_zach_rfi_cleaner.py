#!/usr/bin/env python3
"""Render a diagnostic-only comparison on Zach's observed CHIME/FRB burst.

Only the off-pulse training slice and the source columns required for the
padded, aligned display are loaded as numerical samples. The full file is
byte-read only for its checksum. This is a method comparison, not cleaner
validation.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import shutil
import sys
from pathlib import Path
from typing import Any

import numpy as np

SCRIPT_DIRECTORY = Path(__file__).resolve().parent
if str(SCRIPT_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIRECTORY))
from rfi_time_frequency_candidate import (  # noqa: E402
    ABSOLUTE_PIXEL_THRESHOLD,
    apply_pixel_mask,
)


STATUS = "diagnostic_only_real_event_method_comparison"
TRAINING = (55, 137)
DISPLAY = (197, 305)
ON_PULSE = (229, 273)
MAX_ALIGNMENT_SHIFT_BINS = 48
SOURCE_CONTEXT = (DISPLAY[0] - MAX_ALIGNMENT_SHIFT_BINS, DISPLAY[1])
DT_MS = 0.32768
NATIVE_DT_S = 2.56e-6
FRAME_CENTER_OFFSET_MS = 63.5 * 2.56e-3
K_DM_S_MHZ2 = 4.148808e3
COHERENT_DM = 262.4359033801
UPCHANNEL_FACTOR = 64
CHIME_TOP_EDGE_MHZ = 800.1953125
CHIME_COARSE_WIDTH_MHZ = 0.390625
EXPECTED = {
    "products/zach_chime_upchan.npy": "264f1e643f57012fce1385dcd7b6dfe6a12086f43eb1fa907be5540fb3359192",
    "products/zach_chime_freq.npy": "02c794745bd79ca235d1d3e18d46b2f43f7529616a5747ccab2a5db094a9cba2",
    "products/zach_chime_source_valid.npy": "b183f4aaed375ae78da8000cd5cb8bc3b8c4500c9ff23e56bb9555b0b85ba39e",
    "products/zach_chime_preprocessing_metadata.json": "badcba0e4a3152645b15a81c9f031a5c41c032b63a991d91240892f75c872f0e",
    "code/audit_chime_preprocessing_v2.py": "5df48f411c6d9f9ce59873b6ccb147de30e22fa8306b3543bb06632212340c83",
    "code/upchannelize_chime.py": "1825746445782cb2f36b806668241cfcd7e03a9c11531457b903d43974007b4e",
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
    """Read exactly the approved training and alignment-context columns."""
    if tuple(array.shape) != (65536, 437):
        raise ValueError(f"unexpected observed-array shape: {array.shape}")
    training = np.array(array[:, TRAINING[0] : TRAINING[1]], dtype=np.float32, copy=True)
    context = np.array(
        array[:, SOURCE_CONTEXT[0] : SOURCE_CONTEXT[1]], dtype=np.float32, copy=True
    )
    return training, context


def alignment_shifts(
    frequency_mhz: np.ndarray,
    coarse_ids: np.ndarray,
    fpga_count_by_id: dict[int, int | float],
    *,
    target_dm: float,
    native_dt_s: float,
    output_dt_s: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Return nonnegative output-bin shifts from H5 channel start times."""
    frequency = np.asarray(frequency_mhz, dtype=np.float64)
    identifiers = np.asarray(coarse_ids, dtype=np.int64)
    if frequency.shape != identifiers.shape:
        raise ValueError("frequency and coarse identifiers must have the same shape")
    if not np.isfinite(frequency).all() or np.any(frequency <= 0):
        raise ValueError("frequencies must be finite and positive")
    try:
        fpga = np.array([fpga_count_by_id[int(cid)] for cid in identifiers], dtype=np.float64)
    except KeyError as exc:
        raise ValueError(f"missing FPGA count for coarse channel {exc.args[0]}") from exc

    reference = int(np.argmax(frequency))
    offsets = (
        (fpga - fpga[reference]) * native_dt_s
        - K_DM_S_MHZ2
        * target_dm
        * (frequency**-2 - frequency[reference] ** -2)
    )
    offsets -= np.min(offsets)
    shifts = np.rint(offsets / output_dt_s).astype(np.int64)
    return shifts, offsets


def nominal_coarse_ids(frequency_mhz: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Map nominal fine-channel centres to CHIME coarse identifiers/centres."""
    frequency = np.asarray(frequency_mhz, dtype=np.float64)
    fine_width = CHIME_COARSE_WIDTH_MHZ / UPCHANNEL_FACTOR
    fine_ids = np.rint((CHIME_TOP_EDGE_MHZ - frequency) / fine_width - 0.5).astype(
        np.int64
    )
    coarse_ids = fine_ids // UPCHANNEL_FACTOR
    coarse_frequency = 800.0 - coarse_ids * CHIME_COARSE_WIDTH_MHZ
    return coarse_ids, coarse_frequency


def infer_time0_schedule_dm(
    freq_ids: np.ndarray, fpga_counts: np.ndarray, native_dt_s: float
) -> tuple[float, float, float]:
    """Fit the H5 cutout-start schedule to the cold-plasma delay law."""
    ids = np.asarray(freq_ids, dtype=np.int64)
    counts = np.asarray(fpga_counts, dtype=np.float64)
    frequency = 800.0 - ids * CHIME_COARSE_WIDTH_MHZ
    x = frequency**-2
    reference = int(np.argmax(frequency))
    x_centered = x - x[reference]
    y_centered = (counts - counts[reference]) * native_dt_s
    slope, intercept = np.polyfit(x_centered, y_centered, 1)
    residual = y_centered - (slope * x_centered + intercept)
    return (
        float(slope / K_DM_S_MHZ2),
        float(np.std(residual) * 1e6),
        float(np.max(np.abs(residual)) * 1e6),
    )


def align_nonwrapping(values: np.ndarray, shifts: np.ndarray) -> np.ndarray:
    """Place each row on a common output grid; shifted-in samples remain NaN."""
    data = np.asarray(values)
    row_shifts = np.asarray(shifts, dtype=np.int64)
    if data.ndim != 2 or row_shifts.shape != (data.shape[0],):
        raise ValueError("values must be 2D with one shift per row")
    normalized = row_shifts - np.min(row_shifts)
    output = np.full(
        (data.shape[0], data.shape[1] + int(np.max(normalized))),
        np.nan,
        dtype=np.result_type(data.dtype, np.float32),
    )
    for shift in np.unique(normalized):
        rows = np.flatnonzero(normalized == shift)
        columns = np.arange(int(shift), int(shift) + data.shape[1])
        output[rows[:, None], columns[None, :]] = data[rows]
    return output


def restrict_to_finite_support(values: np.ndarray, support_values: np.ndarray) -> np.ndarray:
    """Copy values and retain only pixels finite in the support array."""
    data = np.asarray(values)
    support = np.asarray(support_values)
    if data.shape != support.shape:
        raise ValueError("values and support values must have the same shape")
    output = np.array(data, copy=True, dtype=np.result_type(data.dtype, np.float32))
    output[~np.isfinite(support)] = np.nan
    return output


def _load_audit(path: Path):
    spec = importlib.util.spec_from_file_location("exact_audit_v2", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def apply_methods(
    training: np.ndarray,
    context: np.ndarray,
    source_valid: np.ndarray,
    audit_path: Path,
) -> dict[str, np.ndarray]:
    """Learn both methods on training only, then apply them to display context."""
    audit = _load_audit(audit_path)
    compact = np.concatenate((training, context), axis=1)
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
    candidate, time_frequency_mask = apply_pixel_mask(combined, final_valid)

    context_start = training.shape[1]
    return {
        "reference_context": np.asarray(reference[:, context_start:], dtype=np.float32),
        "row_only_context": np.asarray(combined[:, context_start:], dtype=np.float32),
        "combined_context": np.asarray(candidate[:, context_start:], dtype=np.float32),
        "time_frequency_mask_context": np.asarray(
            time_frequency_mask[:, context_start:], dtype=bool
        ),
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


def integrated_spectrum(
    values: np.ndarray, valid_rows: np.ndarray, window: tuple[int, int]
) -> np.ndarray:
    """Time-integrated standardized spectrum on a fixed half-open window."""
    data = np.asarray(values, dtype=np.float64)
    valid = np.asarray(valid_rows, dtype=bool)
    start, stop = window
    if not 0 <= start < stop <= data.shape[1]:
        raise ValueError("spectrum window lies outside the display")
    spectrum = np.nansum(data[:, start:stop], axis=1)
    spectrum[~valid] = np.nan
    return spectrum


def median_spread_outlier(
    spectrum: np.ndarray,
    frequency_mhz: np.ndarray,
    valid_rows: np.ndarray,
    interval_mhz: tuple[float, float] = (700.0, 750.0),
) -> dict[str, float | int]:
    """Summarize the largest retained spectral value in a fixed band."""
    values = np.asarray(spectrum, dtype=np.float64)
    frequency = np.asarray(frequency_mhz, dtype=np.float64)
    valid = np.asarray(valid_rows, dtype=bool)
    low, high = interval_mhz
    use = valid & np.isfinite(values) & (frequency >= low) & (frequency < high)
    selected = values[use]
    if selected.size == 0:
        raise ValueError("no finite spectrum values in requested interval")
    center = float(np.median(selected))
    spread = float(1.4826 * np.median(np.abs(selected - center)))
    maximum = float(np.max(selected))
    score = float((maximum - center) / spread) if spread > 0 else float("inf")
    indices = np.flatnonzero(use)
    maximum_index = int(indices[np.argmax(values[indices])])
    return {
        "count": int(selected.size),
        "median": center,
        "median_based_spread": spread,
        "maximum": maximum,
        "maximum_frequency_mhz": float(frequency[maximum_index]),
        "maximum_spread_units_above_median": score,
        "rows_above_100": int(np.sum(selected > 100.0)),
    }


def coarsen_mask_fraction(
    mask: np.ndarray,
    row_valid: np.ndarray,
    factor: int = 64,
) -> np.ndarray:
    """Return rejected fine-row fraction per coarse channel and time bin."""
    pixels = np.asarray(mask, dtype=bool)
    valid = np.asarray(row_valid, dtype=bool)
    if pixels.ndim != 2 or valid.shape != (pixels.shape[0],):
        raise ValueError("mask must be 2D with one row-valid value per row")
    if pixels.shape[0] % factor:
        raise ValueError("frequency dimension is not divisible by factor")
    grouped = pixels.reshape(-1, factor, pixels.shape[1])
    valid_group = valid.reshape(-1, factor)
    denominator = np.maximum(valid_group.sum(axis=1), 1)[:, None]
    return np.sum(grouped & valid_group[:, :, None], axis=1) / denominator


def broad_band_summary(
    spectrum: np.ndarray, frequency_mhz: np.ndarray, valid_rows: np.ndarray
) -> tuple[list[str], list[float | None]]:
    labels, means = [], []
    for low in range(400, 800, 50):
        use = valid_rows & (frequency_mhz >= low) & (frequency_mhz < low + 50)
        labels.append(f"{low}–{low + 50}")
        means.append(float(np.nanmean(spectrum[use])) if np.any(use) else None)
    return labels, means


def fixed_band_peak_bins(
    values: np.ndarray, frequency_mhz: np.ndarray, valid_rows: np.ndarray
) -> dict[str, int | None]:
    peaks: dict[str, int | None] = {}
    for low in range(400, 800, 50):
        label = f"{low}–{low + 50}"
        use = valid_rows & (frequency_mhz >= low) & (frequency_mhz < low + 50)
        if not np.any(use):
            peaks[label] = None
            continue
        profile = np.nanmean(values[use], axis=0)
        peaks[label] = int(np.nanargmax(profile)) if np.isfinite(profile).any() else None
    return peaks


def make_figure(
    path: Path,
    frequency_mhz: np.ndarray,
    source_valid: np.ndarray,
    result: dict[str, np.ndarray],
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
    reference = result["reference_display"]
    row_only = result["row_only_display"]
    candidate = result["combined_display"]

    ref_coarse, coarse_frequency, _ = coarsen(reference, frequency_mhz, source_valid)
    row_only_coarse, _, _ = coarsen(row_only, frequency_mhz, final_valid)
    candidate_coarse, _, _ = coarsen(candidate, frequency_mhz, final_valid)
    time_centers = (np.arange(reference.shape[1]) + 0.5) * DT_MS
    extent = [
        0.0,
        reference.shape[1] * DT_MS,
        float(np.nanmin(coarse_frequency)),
        float(np.nanmax(coarse_frequency)),
    ]
    comparable = np.concatenate(
        [ref_coarse[np.isfinite(ref_coarse)], candidate_coarse[np.isfinite(candidate_coarse)]]
    )
    limit = max(0.5, float(np.percentile(np.abs(comparable), 99.5)))
    cmap = mpl.colormaps["RdBu_r"].copy()
    cmap.set_bad("0.76")
    on_local = (ON_PULSE[0] - DISPLAY[0], ON_PULSE[1] - DISPLAY[0])
    on_span = (on_local[0] * DT_MS, on_local[1] * DT_MS)

    fig = plt.figure(figsize=(15, 8.2), constrained_layout=True)
    fig.suptitle(
        "REJECTED DEVELOPMENT CANDIDATE — failed synthetic preservation limits; not valid for science use",
        color="#9c1c1c",
        fontsize=10,
    )
    grid = fig.add_gridspec(2, 3, height_ratios=(1.15, 0.85))
    top = [
        (ref_coarse, "Bandpass only — full measured support"),
        (row_only_coarse, "Package row-mask output"),
        (candidate_coarse, "Pixel-6 candidate output — rejected"),
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
        ax.set_xlabel("Aligned relative time (ms)")
        ax.axvspan(*on_span, color="gold", alpha=0.08, lw=0)
        if column == 0:
            ax.set_ylabel("Frequency (MHz)")
    fig.colorbar(images[0], ax=top_axes, label="Standardized intensity", shrink=0.8)

    ax_profile = fig.add_subplot(grid[1, 0])
    ax_profile.plot(time_centers, time_profile(reference, source_valid), label="bandpass only, full", lw=1.2)
    ax_profile.plot(time_centers, time_profile(row_only, final_valid), label="package row mask", lw=1.2)
    ax_profile.plot(
        time_centers,
        time_profile(candidate, final_valid),
        label="Pixel 6 — rejected",
        lw=1.2,
    )
    ax_profile.axvspan(*on_span, color="gold", alpha=0.12, lw=0)
    ax_profile.set_title("Frequency-averaged burst profile")
    ax_profile.set_xlabel("Aligned relative time (ms)")
    ax_profile.set_ylabel("Mean standardized intensity")
    ax_profile.legend(frameon=False)

    ax_spectrum = fig.add_subplot(grid[1, 1])
    ax_spectrum.plot(
        frequency_mhz,
        result["reference_full_spectrum"],
        label="bandpass only, full",
        lw=0.38,
        alpha=0.85,
    )
    ax_spectrum.plot(
        frequency_mhz,
        result["reference_common_spectrum"],
        label="package row mask",
        lw=0.55,
    )
    ax_spectrum.plot(
        frequency_mhz,
        result["combined_common_spectrum"],
        label="Pixel 6 — rejected",
        lw=0.55,
        alpha=0.8,
    )
    ax_spectrum.set_xlim(400, 800)
    ax_spectrum.set_title("Time-integrated on-pulse spectrum")
    ax_spectrum.set_xlabel("Frequency (MHz)")
    ax_spectrum.set_ylabel("Standardized intensity sum")
    ax_spectrum.legend(frameon=False)

    ax_mask = fig.add_subplot(grid[1, 2])
    mask_fraction = coarsen_mask_fraction(
        result["time_frequency_mask_display"], final_valid
    )
    mask_image = ax_mask.imshow(
        mask_fraction,
        origin="lower",
        aspect="auto",
        extent=extent,
        cmap="magma_r",
        vmin=0.0,
        vmax=max(0.01, float(np.percentile(mask_fraction, 99.5))),
        interpolation="nearest",
    )
    ax_mask.axvspan(*on_span, color="cyan", alpha=0.08, lw=0)
    ax_mask.set_title("Pixel-6 rejected fine-row fraction")
    ax_mask.set_xlabel("Aligned relative time (ms)")
    ax_mask.set_ylabel("Frequency (MHz)")
    fig.colorbar(mask_image, ax=ax_mask, label="Rejected fraction")

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
        "alignment_shifts",
        "alignment_offsets_s",
        "time_frequency_mask_display",
        "reference_full_spectrum",
        "reference_common_spectrum",
        "combined_common_spectrum",
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
    training, context = load_allowed_slices(observed)
    del observed
    frequency = np.load(root / "products/zach_chime_freq.npy")
    source_valid = np.load(root / "products/zach_chime_source_valid.npy").astype(bool)
    metadata = json.loads(
        (root / "products/zach_chime_preprocessing_metadata.json").read_text()
    )
    if not np.isclose(metadata["dm_pc_cm3"], COHERENT_DM, rtol=0, atol=1e-10):
        raise ValueError("input product was not coherently dedispersed at the H5 power DM")
    result = apply_methods(
        training,
        context,
        source_valid,
        root / "code/audit_chime_preprocessing_v2.py",
    )

    coarse_ids, coarse_frequency = nominal_coarse_ids(frequency)
    fpga_count_by_id = {
        int(cid): int(count)
        for cid, count in zip(metadata["freq_id"], metadata["fpga_count"], strict=True)
    }
    shifts = np.zeros(frequency.size, dtype=np.int64)
    offsets = np.full(frequency.size, np.nan)
    valid_shifts, valid_offsets = alignment_shifts(
        coarse_frequency[source_valid],
        coarse_ids[source_valid],
        fpga_count_by_id,
        target_dm=COHERENT_DM,
        native_dt_s=NATIVE_DT_S,
        output_dt_s=DT_MS * 1e-3,
    )
    shifts[source_valid] = valid_shifts
    offsets[source_valid] = valid_offsets
    if int(np.max(valid_shifts)) != MAX_ALIGNMENT_SHIFT_BINS:
        raise ValueError(
            f"alignment span changed: {np.max(valid_shifts)} != {MAX_ALIGNMENT_SHIFT_BINS} bins"
        )

    crop_start = DISPLAY[0] - SOURCE_CONTEXT[0]
    crop_stop = DISPLAY[1] - SOURCE_CONTEXT[0]

    def align_and_crop(values: np.ndarray) -> np.ndarray:
        aligned = align_nonwrapping(values, shifts)
        cropped = aligned[:, crop_start:crop_stop]
        if cropped.shape[1] != DISPLAY[1] - DISPLAY[0]:
            raise ValueError("aligned display has the wrong width")
        return cropped

    result["reference_display"] = align_and_crop(result["reference_context"])
    result["row_only_display"] = align_and_crop(result["row_only_context"])
    result["combined_display"] = align_and_crop(result["combined_context"])
    result["time_frequency_mask_display"] = (
        np.isfinite(result["row_only_display"])
        & ~np.isfinite(result["combined_display"])
    )
    result["alignment_shifts"] = shifts
    result["alignment_offsets_s"] = offsets
    reference = result["reference_display"]
    row_only = result["row_only_display"]
    candidate = result["combined_display"]
    on_local = (ON_PULSE[0] - DISPLAY[0], ON_PULSE[1] - DISPLAY[0])
    result["reference_full_spectrum"] = integrated_spectrum(
        reference, source_valid, on_local
    )
    result["reference_common_spectrum"] = integrated_spectrum(
        row_only, result["final_valid"], on_local
    )
    result["combined_common_spectrum"] = integrated_spectrum(
        candidate, result["final_valid"], on_local
    )
    labels, reference_full_bands = broad_band_summary(
        result["reference_full_spectrum"], frequency, source_valid
    )
    _, reference_common_bands = broad_band_summary(
        result["reference_common_spectrum"], frequency, result["final_valid"]
    )
    _, combined_common_bands = broad_band_summary(
        result["combined_common_spectrum"], frequency, result["final_valid"]
    )
    bands = {
        "labels": labels,
        "reference_full": reference_full_bands,
        "reference_common": reference_common_bands,
        "combined_common": combined_common_bands,
    }
    common = result["final_valid"][:, None] & np.isfinite(candidate)
    row_only_common = restrict_to_finite_support(row_only, candidate)
    common_difference = candidate[common] - row_only_common[common]
    row_outlier = median_spread_outlier(
        result["reference_common_spectrum"],
        frequency,
        result["final_valid"],
    )
    candidate_outlier = median_spread_outlier(
        result["combined_common_spectrum"],
        frequency,
        result["final_valid"],
    )
    peak_bins = fixed_band_peak_bins(reference, frequency, source_valid)
    finite_peaks = [value for value in peak_bins.values() if value is not None]
    schedule_dm, schedule_rms_us, schedule_max_us = infer_time0_schedule_dm(
        np.asarray(metadata["freq_id"]),
        np.asarray(metadata["fpga_count"]),
        NATIVE_DT_S,
    )

    figure = output / "real_zach_rfi_method_comparison.svg"
    make_figure(figure, frequency, source_valid, result)
    array_hashes = _save_arrays(output, result)
    script_copy = output / Path(__file__).name
    shutil.copy2(Path(__file__).resolve(), script_copy)
    candidate_source = Path(apply_pixel_mask.__code__.co_filename).resolve()
    candidate_copy = output / candidate_source.name
    shutil.copy2(candidate_source, candidate_copy)
    record = {
        "status": STATUS,
        "warning": "Observed event with no known truth; this does not validate the cleaner.",
        "supersedes": {
            "commit": "bd149c00",
            "reason": "The prior figure used a scintillation sub-window and treated column index as a shared time axis.",
        },
        "event": "zach",
        "instrument": "CHIME/FRB",
        "observed_slices_half_open": {
            "training": list(TRAINING),
            "alignment_source": list(SOURCE_CONTEXT),
            "aligned_display": list(DISPLAY),
            "on_pulse_integration": list(ON_PULSE),
        },
        "observed_sample_columns_loaded": [list(TRAINING), list(SOURCE_CONTEXT)],
        "time_axis": {
            "label": "aligned relative time",
            "cadence_ms": DT_MS,
            "frame_center_formula": "(128*j + 63.5) * 2.56 microseconds",
            "alignment_formula": "(fpga_count-fpga_ref)*2.56 us - K_DM*DM*(nu^-2-nu_ref^-2)",
            "alignment_is_nonwrapping": True,
            "alignment_offset_range_ms": [
                float(np.nanmin(valid_offsets) * 1e3),
                float(np.nanmax(valid_offsets) * 1e3),
            ],
            "alignment_shift_range_bins": [
                int(np.min(valid_shifts)),
                int(np.max(valid_shifts)),
            ],
            "time0_schedule_dm_pc_cm3": schedule_dm,
            "time0_schedule_fit_residual_rms_us": schedule_rms_us,
            "time0_schedule_fit_residual_max_us": schedule_max_us,
            "absolute_arrival_time_status": "uncertified",
        },
        "coherent_dedispersion_measure_pc_cm3": COHERENT_DM,
        "coherent_dm_source": "source H5 tiedbeam_power.DM_coherent",
        "dedispersion_measure_status": "product-specific; not a manuscript adoption",
        "window_validation": {
            "documented_on_pulse_envelope_ms": 14.21,
            "selected_on_pulse_width_ms": (ON_PULSE[1] - ON_PULSE[0]) * DT_MS,
            "display_width_ms": (DISPLAY[1] - DISPLAY[0]) * DT_MS,
            "left_padding_ms": (ON_PULSE[0] - DISPLAY[0]) * DT_MS,
            "right_padding_ms": (DISPLAY[1] - ON_PULSE[1]) * DT_MS,
            "fixed_band_peak_bins_in_display": peak_bins,
            "fixed_band_peak_spread_bins": max(finite_peaks) - min(finite_peaks),
            "fixed_band_peak_spread_ms": (max(finite_peaks) - min(finite_peaks))
            * DT_MS,
        },
        "methods": {
            "reference": "bandpass mean and sample standard deviation learned on training without RFI mask",
            "package_row_mask": [
                "package RFI row mask on training",
                "bandpass mean and sample standard deviation on surviving training rows",
                "normalize",
                "second package RFI row mask on normalized training",
            ],
            "time_frequency_candidate": {
                "operation": "mask finite normalized pixels with absolute value at least threshold",
                "threshold": ABSOLUTE_PIXEL_THRESHOLD,
                "ordering": "after package row masks and bandpass normalization",
                "replacement": "none; rejected pixels are NaN",
                "status": "development-only; fails some synthetic preservation limits",
            },
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
            "time_frequency_rejected_display_pixels": int(
                result["time_frequency_mask_display"].sum()
            ),
            "time_frequency_retained_display_fraction": float(
                1.0
                - result["time_frequency_mask_display"].sum()
                / max(np.isfinite(row_only).sum(), 1)
            ),
        },
        "method_comparison": {
            "common_support_values_equal": bool(
                np.array_equal(candidate[common], row_only_common[common])
            ),
            "maximum_absolute_common_support_difference": float(
                np.max(np.abs(common_difference))
            ),
            "interpretation": "On retained pixels, Pixel 6 leaves package-normalized values unchanged and changes only explicit support.",
            "row_only_700_750_mhz_outlier": row_outlier,
            "pixel6_700_750_mhz_outlier": candidate_outlier,
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
            "candidate_module_sha256": sha256(candidate_copy),
            "python": platform.python_version(),
            "numpy": np.__version__,
            "array_hashes": array_hashes,
            "baseband_analysis_version": "1.9.0",
            "baseband_analysis_revision": "e08df9dacc49e1007f28759b7edca71c7b8e5273",
            "upchannel_command": (
                "python -c 'import staged worker; set TARGETS[\"zach\"][\"dm\"]=262.4359033801; "
                "recover_target(\"zach\", ..., time_shift=False)'"
            ),
            "review_command": (
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
