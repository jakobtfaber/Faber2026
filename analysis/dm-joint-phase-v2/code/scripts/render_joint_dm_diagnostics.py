#!/usr/bin/env python3
"""Render auditable CHIME/DSA diagnostics for the joint DM-phase campaign."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw

from dispersion.dm_joint_phase import crop_on_pulse, normalise_channels
from dispersion.dm_power_analysis import (
    CHIME_DT_S,
    DSA_DT_S,
    _freq_grid_mhz,
    _orient_waterfall_to_ascending_frequency,
    shift_waterfall_residual_dm,
)


def _display_reduce(
    waterfall: np.ndarray, frequency: np.ndarray, *, max_chan: int = 256, max_time: int = 900
) -> tuple[np.ndarray, np.ndarray, int]:
    out = np.asarray(waterfall, dtype=float)
    freq = np.asarray(frequency, dtype=float)
    ff = max(1, out.shape[0] // max_chan)
    tf = max(1, out.shape[1] // max_time)
    nf = (out.shape[0] // ff) * ff
    nt = (out.shape[1] // tf) * tf
    out = np.nanmean(out[:nf].reshape(nf // ff, ff, out.shape[1]), axis=1)
    freq = np.nanmean(freq[:nf].reshape(nf // ff, ff), axis=1)
    out = np.nanmean(out[:, :nt].reshape(out.shape[0], nt // tf, tf), axis=2)
    return out, freq, tf


def _waterfall_panels(ax_in, ax_fit, band: dict) -> None:
    telescope = band["telescope"]
    raw = np.load(band["input_path"], mmap_mode="r")
    oriented = _orient_waterfall_to_ascending_frequency(raw, telescope)
    frequency = _freq_grid_mhz(telescope, oriented.shape[0])
    dt_s = CHIME_DT_S if telescope == "chime" else DSA_DT_S
    cropped, _crop, valid = crop_on_pulse(oriented, dt_s)
    freq = frequency[valid]
    z, valid2 = normalise_channels(cropped)
    freq = freq[valid2]
    residual = float(band["dm"] - band["product_dm"])
    corrected = shift_waterfall_residual_dm(z, freq, dt_s, residual, mode="zero_fill")
    shown_in, shown_freq, tf = _display_reduce(z, freq)
    shown_fit, _shown_freq2, _tf2 = _display_reduce(corrected, freq)
    peak = int(np.argmax(np.mean(np.clip(shown_fit, 0, None), axis=0)))
    time_ms = (np.arange(shown_fit.shape[1]) - peak) * dt_s * tf * 1e3
    extent = [time_ms[0], time_ms[-1], shown_freq.min(), shown_freq.max()]
    values = np.concatenate((shown_in.ravel(), shown_fit.ravel()))
    vmin, vmax = np.nanpercentile(values, (4, 99.6))
    for ax, image, title in (
        (ax_in, shown_in, f"{telescope.upper()} product DM {band['product_dm']:.4f}"),
        (ax_fit, shown_fit, f"best DM {band['dm']:.4f} +/- {band['sigma']:.4f}"),
    ):
        ax.imshow(
            image,
            origin="lower",
            aspect="auto",
            extent=extent,
            cmap="viridis",
            vmin=vmin,
            vmax=vmax,
            rasterized=True,
        )
        ax.axvline(0, color="white", alpha=0.55, lw=0.8)
        ax.set_title(title, fontsize=9)
        ax.set_xlabel("ms from fitted peak")
    ax_in.set_ylabel("MHz")


def _normalised_score(band: dict) -> tuple[np.ndarray, np.ndarray]:
    curve = band["selected_curve"]
    grid = np.asarray(curve["dm_grid"], dtype=float)
    score = np.asarray(curve["score"], dtype=float)
    span = float(np.nanmax(score) - np.nanmin(score))
    return grid, (score - np.nanmin(score)) / span if span > 0 else np.zeros_like(score)


def _quality(event: dict) -> tuple[str, list[str]]:
    reasons: list[str] = []
    for telescope in ("chime", "dsa"):
        band = event[telescope]
        curve = band["selected_curve"]
        grid = np.asarray(curve["dm_grid"])
        index = int(np.nanargmax(curve["score"]))
        if index < 2 or index > grid.size - 3:
            reasons.append(f"{telescope} peak near grid edge")
        if band["selected_resolution"]["cluster_size"] < 2:
            reasons.append(f"{telescope} resolution unstable")
    if abs(event["joint"]["chime_minus_dsa"]) > 0.15:
        reasons.append("band difference >0.15")
    if reasons:
        return "REVIEW", reasons
    if event["joint"]["between_band_sigma"] > 0:
        return "PASS_SYSTEMATIC", ["joint uncertainty includes between-band systematic"]
    return "PASS", []


def _event_figure(event: dict, output: Path) -> Path:
    fig = plt.figure(figsize=(15, 12), constrained_layout=True)
    gs = fig.add_gridspec(4, 4)
    _waterfall_panels(fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), event["chime"])
    _waterfall_panels(fig.add_subplot(gs[1, 0]), fig.add_subplot(gs[1, 1]), event["dsa"])

    ax_curve = fig.add_subplot(gs[0:2, 2:4])
    colors = {"chime": "tab:blue", "dsa": "tab:orange"}
    for telescope in ("chime", "dsa"):
        band = event[telescope]
        grid, score = _normalised_score(band)
        ax_curve.plot(grid, score, color=colors[telescope], label=telescope.upper())
        ax_curve.axvspan(
            band["dm"] - band["sigma"],
            band["dm"] + band["sigma"],
            color=colors[telescope],
            alpha=0.12,
        )
        ax_curve.axvline(band["dm"], color=colors[telescope], ls="--", lw=1)
    joint = event["joint"]
    ax_curve.axvline(joint["dm"], color="black", lw=1.4, label="joint")
    ax_curve.axvspan(
        joint["dm"] - joint["sigma"], joint["dm"] + joint["sigma"], color="black", alpha=0.08
    )
    ax_curve.set(title="Selected phase-coherence curves", xlabel="absolute DM (pc cm$^{-3}$)", ylabel="normalised score")
    ax_curve.legend()

    ax_cut = fig.add_subplot(gs[2, 0:2])
    for telescope in ("chime", "dsa"):
        curve = event[telescope]["selected_curve"]
        points = sorted((float(key), value) for key, value in curve["cutoff_peaks_absolute"].items())
        ax_cut.plot([p[0] for p in points], [p[1] for p in points], "o-", color=colors[telescope], label=telescope.upper())
        ax_cut.axhspan(
            event[telescope]["dm"] - event[telescope]["sigma"],
            event[telescope]["dm"] + event[telescope]["sigma"],
            color=colors[telescope], alpha=0.10,
        )
    ax_cut.set(title="Cutoff sensitivity (included in uncertainty)", xlabel="maximum fluctuation frequency (Hz)", ylabel="peak DM")
    ax_cut.legend()

    ax_res = fig.add_subplot(gs[2, 2])
    for telescope in ("chime", "dsa"):
        rows = event[telescope]["resolutions"]
        labels = [f"{r['frequency_factor']}x{r['time_factor']}" for r in rows]
        ax_res.plot(labels, [r["dm"] for r in rows], "o-", color=colors[telescope], label=telescope.upper())
    ax_res.set(title="Native-resolution stability", xlabel="frequency x time averaging", ylabel="peak DM")
    ax_res.tick_params(axis="x", rotation=25)

    ax_jack = fig.add_subplot(gs[2, 3])
    for telescope in ("chime", "dsa"):
        peaks = event[telescope]["selected_curve"]["jackknife_peaks_absolute"]
        ax_jack.hist(peaks, bins=7, histtype="step", lw=1.5, color=colors[telescope], label=telescope.upper())
    ax_jack.set(title="Leave-channel-block-out peaks", xlabel="DM", ylabel="count")
    ax_jack.legend(fontsize=8)

    ax_text = fig.add_subplot(gs[3, :])
    ax_text.axis("off")
    status, reasons = _quality(event)
    lines = [
        f"QUALITY {status}    joint DM = {joint['dm']:.5f} +/- {joint['sigma']:.5f} pc cm^-3",
        f"CHIME - DSA = {joint['chime_minus_dsa']:+.5f} +/- {joint['difference_sigma']:.5f} "
        f"({joint['tension_sigma']:.2f} sigma); between-band systematic tau = {joint['between_band_sigma']:.5f}",
    ]
    for telescope in ("chime", "dsa"):
        band = event[telescope]
        res = band["selected_resolution"]
        components = band["sigma_components"]
        lines.append(
            f"{telescope.upper()}: {band['valid_channels']} valid channels; selected {res['nchan']} x {res['ntime']}, "
            f"dt={1e6 * res['dt_s']:.3f} us, cutoff={res['cutoff_hz']:.0f} Hz; "
            f"sigma[jack,res,cut]=[{components['jackknife']:.4f}, {components['resolution']:.4f}, {components['cutoff']:.4f}]"
        )
    if reasons:
        lines.append("Review flags: " + "; ".join(reasons))
    else:
        lines.append("Checks passed: interior maxima, resolution stability, and CHIME/DSA agreement thresholds.")
    ax_text.text(0.01, 0.95, "\n".join(lines), va="top", family="monospace", fontsize=10)
    fig.suptitle(f"{event['burst']} - custom joint DM-phase audit", fontsize=15)
    path = output / f"{event['burst']}_joint_dm_diagnostic.png"
    fig.savefig(path, dpi=170)
    plt.close(fig)
    return path


def _contact_sheet(paths: list[Path], output: Path) -> None:
    thumbs = []
    for path in paths:
        image = Image.open(path).convert("RGB")
        image.thumbnail((760, 610))
        thumbs.append((path.stem, image.copy()))
    cols, pad, label = 2, 18, 30
    cell_w, cell_h = 760, 610
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w + (cols + 1) * pad, rows * (cell_h + label) + (rows + 1) * pad), "white")
    draw = ImageDraw.Draw(sheet)
    for index, (name, image) in enumerate(thumbs):
        row, col = divmod(index, cols)
        x = pad + col * (cell_w + pad)
        y = pad + row * (cell_h + label + pad)
        draw.text((x, y), name, fill="black")
        sheet.paste(image, (x, y + label))
    sheet.save(output, quality=92)


def render(results_path: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    events = json.loads(results_path.read_text())
    paths = [_event_figure(event, output) for event in events]
    _contact_sheet(paths, output / "all_events_contact_sheet.jpg")
    fields = [
        "burst", "chime_dm", "chime_sigma", "dsa_dm", "dsa_sigma", "joint_dm", "joint_sigma",
        "chime_minus_dsa", "tension_sigma", "between_band_sigma", "quality", "flags",
    ]
    rows = []
    for event in events:
        quality, reasons = _quality(event)
        rows.append({
            "burst": event["burst"], "chime_dm": event["chime"]["dm"], "chime_sigma": event["chime"]["sigma"],
            "dsa_dm": event["dsa"]["dm"], "dsa_sigma": event["dsa"]["sigma"], "joint_dm": event["joint"]["dm"],
            "joint_sigma": event["joint"]["sigma"], "chime_minus_dsa": event["joint"]["chime_minus_dsa"],
            "tension_sigma": event["joint"]["tension_sigma"], "between_band_sigma": event["joint"]["between_band_sigma"],
            "quality": quality, "flags": "; ".join(reasons),
        })
    with (output / "summary.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    lines = [
        "# Joint CHIME/DSA DM-phase results", "",
        "Each band was fitted independently at the finest native or near-native resolution that was stable across the resolution grid. The quoted band uncertainty is the maximum of the channel-block jackknife, resolution dependence, fluctuation-frequency-cutoff dependence, and a 0.005 pc cm^-3 numerical floor. The joint estimate is inverse-variance weighted when the bands are consistent and uses a fitted random-effects term when their difference exceeds the stated band errors.",
        "", "| Event | CHIME DM | DSA DM | Joint DM | CHIME-DSA | Status |", "|---|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['burst']} | {row['chime_dm']:.4f} +/- {row['chime_sigma']:.4f} | "
            f"{row['dsa_dm']:.4f} +/- {row['dsa_sigma']:.4f} | {row['joint_dm']:.4f} +/- {row['joint_sigma']:.4f} | "
            f"{row['chime_minus_dsa']:+.4f} | {row['quality']} |"
        )
    lines.extend([
        "", "`PASS_SYSTEMATIC` means both band maxima passed the fit-quality gates, while the shared uncertainty was widened by the measured between-band scatter. It is not a failed or unconstrained fit.",
        "", "See `all_events_contact_sheet.jpg`, the event-level PNGs, `../fits.json`, and `../validation/injection_recovery.json` for the full evidence.",
    ])
    (output / "summary.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=Path("results/dm_joint_phase_v2/fits.json"))
    parser.add_argument("--output", type=Path, default=Path("results/dm_joint_phase_v2/diagnostics"))
    args = parser.parse_args()
    render(args.results, args.output)


if __name__ == "__main__":
    main()
