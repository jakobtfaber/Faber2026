#!/usr/bin/env python3
"""Render a fine-frequency Zach atlas for an explicit manual zap list."""

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


def coarsen_selected(
    values: np.ndarray,
    frequency_mhz: np.ndarray,
    row_valid: np.ndarray,
    use: np.ndarray,
    factor: int = 8,
) -> tuple[np.ndarray, np.ndarray]:
    rows = np.flatnonzero(use)
    rows = rows[: rows.size - rows.size % factor]
    data = values[rows].reshape(-1, factor, values.shape[1])
    valid = row_valid[rows].reshape(-1, factor)
    masked = np.where(valid[:, :, None], data, np.nan)
    count = np.sum(np.isfinite(masked), axis=1)
    summed = np.nansum(masked, axis=1)
    coarse = np.full(summed.shape, np.nan)
    np.divide(summed, count, out=coarse, where=count > 0)
    frequency = np.mean(frequency_mhz[rows].reshape(-1, factor), axis=1)
    return coarse, frequency


def write_review_bundle(
    path: Path,
    *,
    dynamic_spectrum: np.ndarray,
    frequency_mhz: np.ndarray,
    row_valid: np.ndarray,
    time_ms: np.ndarray,
    off_mean: np.ndarray,
    off_standard_deviation: np.ndarray,
    on_spectrum: np.ndarray,
    metadata: dict,
) -> None:
    """Write the full-resolution arrays needed by the local manual reviewer."""
    dynamic = np.asarray(dynamic_spectrum)
    frequency = np.asarray(frequency_mhz, dtype=float)
    valid = np.asarray(row_valid, dtype=bool)
    time = np.asarray(time_ms, dtype=float)
    row_arrays = tuple(
        np.asarray(values)
        for values in (off_mean, off_standard_deviation, on_spectrum)
    )
    if dynamic.ndim != 2:
        raise ValueError("dynamic spectrum must be two-dimensional")
    if frequency.shape != (dynamic.shape[0],) or valid.shape != frequency.shape:
        raise ValueError("frequency and row-valid arrays must match dynamic rows")
    if time.shape != (dynamic.shape[1],):
        raise ValueError("time axis must match dynamic columns")
    if any(values.shape != frequency.shape for values in row_arrays):
        raise ValueError("row measures must match the frequency axis")
    if metadata.get("schema_version") != 1:
        raise ValueError("unsupported review-bundle schema")
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        dynamic_spectrum=np.asarray(dynamic, dtype=np.float32),
        frequency_mhz=frequency,
        row_valid=valid,
        time_ms=time,
        off_mean=np.asarray(row_arrays[0], dtype=np.float64),
        off_standard_deviation=np.asarray(row_arrays[1], dtype=np.float64),
        on_spectrum=np.asarray(row_arrays[2], dtype=np.float64),
        metadata_json=np.asarray(json.dumps(metadata, sort_keys=True)),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--review-script", type=Path, required=True)
    parser.add_argument("--output-svg", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-bundle", type=Path)
    parser.add_argument("--frequency-low-mhz", type=float, default=700.0)
    parser.add_argument("--frequency-high-mhz", type=float, default=750.0)
    args = parser.parse_args()
    if (
        args.frequency_low_mhz >= args.frequency_high_mhz
        or (args.frequency_high_mhz - args.frequency_low_mhz) % 5.0 != 0
    ):
        raise ValueError("frequency interval must be positive and divisible by 5 MHz")
    review = load_module(args.review_script)
    input_hashes = review.verify_inputs(args.input_root)

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
    aligned = review.align_nonwrapping(result["reference_context"], shifts)
    crop_start = review.DISPLAY[0] - review.SOURCE_CONTEXT[0]
    crop_stop = review.DISPLAY[1] - review.SOURCE_CONTEXT[0]
    display = aligned[:, crop_start:crop_stop]
    on = (
        review.ON_PULSE[0] - review.DISPLAY[0],
        review.ON_PULSE[1] - review.DISPLAY[0],
    )
    off = np.concatenate((display[:, : on[0]], display[:, on[1] :]), axis=1)
    off_mean = np.nanmean(off, axis=1)
    off_standard_deviation = np.nanstd(off, axis=1)
    review_valid = result["reference_valid"]
    on_spectrum = review.integrated_spectrum(display, review_valid, on)
    if args.output_bundle is not None:
        write_review_bundle(
            args.output_bundle,
            dynamic_spectrum=display,
            frequency_mhz=frequency,
            row_valid=review_valid,
            time_ms=np.arange(display.shape[1], dtype=float) * review.DT_MS,
            off_mean=off_mean,
            off_standard_deviation=off_standard_deviation,
            on_spectrum=on_spectrum,
            metadata={
                "schema_version": 1,
                "event": "zach",
                "instrument": "chime-frb",
                "frequency_axis_sha256": input_hashes[
                    "products/zach_chime_freq.npy"
                ],
                "source_product_sha256": input_hashes[
                    "products/zach_chime_upchan.npy"
                ],
                "source_valid_sha256": input_hashes[
                    "products/zach_chime_source_valid.npy"
                ],
                "protected_on_pulse": list(on),
                "display_columns": list(review.DISPLAY),
                "input_hashes": input_hashes,
                "review_script_sha256": review.sha256(args.review_script),
                "atlas_script_sha256": review.sha256(Path(__file__)),
                "container_digest": "chimefrb/baseband-analysis@sha256:f510909d892d0d5224c982c590cbe80967a49a59b79c396ab72bb710105c4c41",
            },
        )

    import matplotlib as mpl
    import matplotlib.pyplot as plt

    mpl.rcParams.update(
        {
            "font.size": 8,
            "axes.titlesize": 9,
            "axes.labelsize": 8,
            "svg.hashsalt": "faber2026-zach-manual-zap-atlas",
        }
    )
    bands = [
        (low, low + 5.0)
        for low in np.arange(args.frequency_low_mhz, args.frequency_high_mhz, 5.0)
    ]
    fig, axes = plt.subplots(
        len(bands),
        3,
        figsize=(13, 28),
        gridspec_kw={"width_ratios": (3.2, 1.2, 1.2)},
        constrained_layout=True,
    )
    fig.suptitle(
        (
            "Zach CHIME/FRB manual-zap atlas — bandpass only; no RFI zaps "
            f"applied; {args.frequency_low_mhz:g}–{args.frequency_high_mhz:g} MHz"
        ),
        color="#9c1c1c",
        fontsize=11,
    )
    cmap = mpl.colormaps["RdBu_r"].copy()
    cmap.set_bad("0.76")
    on_span = (on[0] * review.DT_MS, on[1] * review.DT_MS)
    band_records = []
    for row, (low, high) in enumerate(bands):
        use = (frequency >= low) & (frequency < high)
        coarse, coarse_frequency = coarsen_selected(
            display, frequency, review_valid, use
        )
        finite = coarse[np.isfinite(coarse)]
        limit = max(0.5, float(np.percentile(np.abs(finite), 99.5)))
        ax_dynamic, ax_off, ax_on = axes[row]
        image = ax_dynamic.imshow(
            np.ma.masked_invalid(coarse),
            origin="lower",
            aspect="auto",
            extent=(0.0, display.shape[1] * review.DT_MS, low, high),
            cmap=cmap,
            vmin=-limit,
            vmax=limit,
            interpolation="nearest",
        )
        ax_dynamic.axvspan(*on_span, color="gold", alpha=0.08, lw=0)
        ax_dynamic.set_ylabel("Frequency (MHz)")
        ax_dynamic.set_title(f"{low:.0f}–{high:.0f} MHz dynamic spectrum")
        ax_dynamic.set_xlabel("Aligned relative time (ms)")

        valid_rows = use & review_valid
        ax_off.plot(off_mean[valid_rows], frequency[valid_rows], lw=0.5, label="mean")
        ax_off.plot(
            off_standard_deviation[valid_rows],
            frequency[valid_rows],
            lw=0.5,
            label="standard deviation",
        )
        ax_off.set_ylim(low, high)
        ax_off.set_title("Off-pulse row measures")
        ax_off.set_xlabel("Standardized units")
        ax_off.legend(frameon=False, fontsize=6)

        ax_on.plot(on_spectrum[valid_rows], frequency[valid_rows], lw=0.5, color="black")
        ax_on.set_ylim(low, high)
        ax_on.set_title("On-pulse spectrum")
        ax_on.set_xlabel("Standardized intensity sum")
        band_records.append(
            {
                "interval_mhz": [low, high],
                "fine_rows": int(np.sum(use)),
                "bandpass_retained_rows": int(np.sum(valid_rows)),
                "display_limit": limit,
            }
        )
    fig.colorbar(image, ax=axes[:, 0], label="Standardized intensity", shrink=0.25)
    fig.savefig(
        args.output_svg,
        format="svg",
        metadata={"Date": None, "Creator": "Faber2026"},
        bbox_inches="tight",
        pad_inches=0.05,
    )
    plt.close(fig)
    args.output_svg.write_text(
        "\n".join(line.rstrip() for line in args.output_svg.read_text().splitlines())
        + "\n"
    )
    args.output_json.write_text(
        json.dumps(
            {
                "status": "development_only_manual_zap_atlas",
                "event": "zach",
                "instrument": "CHIME/FRB",
                "manual_zaps_applied": False,
                "coherent_dm_pc_cm3": review.COHERENT_DM,
                "protected_on_pulse": list(on),
                "display_columns": list(review.DISPLAY),
                "frequency_coarsening_factor": 8,
                "frequency_interval_mhz": [
                    args.frequency_low_mhz,
                    args.frequency_high_mhz,
                ],
                "bands": band_records,
                "provenance": {
                    "input_hashes": input_hashes,
                    "review_script_sha256": review.sha256(args.review_script),
                    "atlas_script_sha256": review.sha256(Path(__file__)),
                    "container_digest": "chimefrb/baseband-analysis@sha256:f510909d892d0d5224c982c590cbe80967a49a59b79c396ab72bb710105c4c41",
                },
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
