#!/usr/bin/env python3
"""Plot the fit-independent burst-energetics measurement path."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import yaml  # noqa: E402

from energetics.methods import dsa_beam  # noqa: E402
from energetics.methods.chime_beam import chime_sigma_jy, load_chime_sefd  # noqa: E402
from energetics.methods.flux_cal import (  # noqa: E402
    burst_epoch_position,
    dsa_beam_offset,
    dsa_pointing_dec,
    dsa_sigma_jy,
    load_dsa_sefd_beam,
)
from radio_pipeline.resources import path as resource_path  # noqa: E402
from scattering.scat_analysis.config_utils import load_telescope_block  # noqa: E402
from scattering.scat_analysis.pipeline.io import BurstDataset  # noqa: E402

BANDS = {
    "CHIME": ("chime", "CHIME/FRB", "#2878B5"),
    "DSA": ("dsa", "DSA-110", "#D55E00"),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def receipt_rows(path: Path, nickname: str) -> dict[str, dict[str, str]]:
    with path.open() as handle:
        rows = {
            row["band"]: row
            for row in csv.DictReader(handle)
            if row["nickname"].lower() == nickname.lower()
        }
    if set(rows) != set(BANDS):
        raise ValueError(f"{nickname}: expected CHIME and DSA receipt rows")
    return rows


def load_band(
    nickname: str,
    band: str,
    source: Path,
    dsa_beam_cube: Path,
) -> dict:
    telescope, label, color = BANDS[band]
    config_name = "johndoeII" if nickname.lower() == "johndoeii" else nickname
    config_path = (
        ROOT
        / "config"
        / "fits"
        / "scattering"
        / "bursts"
        / telescope
        / f"{config_name}_{telescope}.yaml"
    )
    config = yaml.safe_load(config_path.read_text())
    telescope_config = load_telescope_block(
        str(resource_path("scattering_telescopes.yaml")), telescope
    )
    dataset = BurstDataset(
        source,
        source,
        telescope=telescope_config,
        f_factor=int(config.get("f_factor", 1)),
        t_factor=int(config.get("t_factor", 1)),
        onpulse_crop=True,
        onpulse_thresh=3.0,
        onpulse_pad_factor=0.5,
    )
    if dataset.onpulse_crop_status != "applied":
        raise ValueError(f"{nickname} {band}: {dataset.onpulse_crop_status}")

    model = dataset.model
    noise = np.clip(model.noise_std, 1e-9, None)
    sn = model.data / noise[:, None]
    freq_hz = model.freq * 1e9
    dnu_hz = dataset.df_MHz * 1e6
    if band == "CHIME":
        sigma_jy = chime_sigma_jy(
            freq_hz,
            dnu_hz,
            load_chime_sefd(),
            dataset.dt_ms / 1e3,
            g=1.0,
        )
    else:
        _mjd, _ra, dec = burst_epoch_position(nickname)
        theta, phi = dsa_beam_offset(dec, dsa_pointing_dec(nickname))
        sigma_jy = dsa_sigma_jy(
            freq_hz,
            dnu_hz,
            load_dsa_sefd_beam(nickname),
            dataset.dt_ms / 1e3,
            theta,
            phi,
            lambda th, ph, freq: dsa_beam.beam_gain(th, ph, freq, path=dsa_beam_cube),
        )

    peak = int(np.nanargmax(np.nansum(sn, axis=0)))
    time_ms = (np.arange(sn.shape[1]) - peak) * dataset.dt_ms
    fluence_spectrum = sigma_jy * dataset.dt_ms * np.nansum(sn, axis=1)
    return {
        "label": label,
        "color": color,
        "source": source,
        "dataset": dataset,
        "sn": sn,
        "time_ms": time_ms,
        "freq_mhz": freq_hz / 1e6,
        "fluence_spectrum": fluence_spectrum,
        "fluence_jy_ms_hz": float(np.trapezoid(fluence_spectrum, freq_hz)),
    }


def draw_method_panel(ax, rows: dict[str, dict[str, str]], nickname: str) -> None:
    ax.axis("off")
    ax.text(0.0, 0.98, "Measurement chain", weight="bold", va="top")
    steps = [
        (
            0.86,
            r"$S_\nu(t)=\dfrac{({\rm S/N})_\nu(t)\,{\rm SEFD}_\nu}"
            r"{\sqrt{2\,\Delta\nu\,\Delta t}\,G_\nu}$",
        ),
        (0.66, r"$I_X=\int_{\nu_1^X}^{\nu_2^X}\!\int_{\rm on}S_\nu(t)\,dt\,d\nu$"),
        (
            0.46,
            r"$E_{\rm iso}=\dfrac{4\pi D_L^2(z)}{1+z}\left(I_C+I_D\right)$",
        ),
    ]
    for index, (y, text) in enumerate(steps):
        ax.text(
            0.04,
            y,
            text,
            fontsize=10,
            va="center",
            bbox={"boxstyle": "round,pad=0.35", "fc": "#F4F4F4", "ec": "#777777"},
        )
        if index < len(steps) - 1:
            ax.annotate(
                "",
                xy=(0.5, y - 0.11),
                xytext=(0.5, y - 0.04),
                arrowprops={"arrowstyle": "->", "color": "#555555"},
            )
    ax.text(
        0.04,
        0.29,
        "Window gate",
        weight="bold",
        color="#333333",
    )
    ax.text(
        0.04,
        0.245,
        r"$3$ thresholds $\times$ $3$ padding factors;"
        "\naccept only if every window succeeds and"
        "\nfluence spread is at most 10%.",
        fontsize=9,
        va="top",
    )
    statuses = (
        f"{nickname.capitalize()} example: "
        f"{float(rows['CHIME']['window_sensitivity_frac']):.1%} CHIME/FRB, "
        f"{float(rows['DSA']['window_sensitivity_frac']):.1%} DSA-110"
    )
    ax.text(0.04, 0.12, statuses, fontsize=8.5, color="#333333")
    ax.text(
        0.04,
        0.055,
        "Candidate only: calibration, correlated-noise,\nand visual-review gates remain pending.",
        fontsize=8.5,
        color="#9A3412",
        weight="bold",
    )
    ax.text(0.04, 0.005, "No fitted burst amplitude enters this chain.", fontsize=8.5)


def make_figure(
    nickname: str,
    receipt: Path,
    dsa_beam_cube: Path,
    output_stem: Path,
) -> None:
    rows = receipt_rows(receipt, nickname)
    bands = {
        band: load_band(nickname, band, Path(rows[band]["input_path"]), dsa_beam_cube)
        for band in BANDS
    }
    for band, item in bands.items():
        receipt_fluence = float(rows[band]["fluence_jy_ms_hz"])
        relative_error = abs(item["fluence_jy_ms_hz"] - receipt_fluence) / receipt_fluence
        if relative_error > 1e-10:
            raise ValueError(
                f"{nickname} {band}: plotted fluence disagrees with receipt "
                f"({relative_error:.3g} relative)"
            )

    plt.rcParams.update(
        {
            "font.size": 9,
            "axes.labelsize": 9,
            "axes.titlesize": 9,
            "axes.linewidth": 0.8,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "savefig.bbox": "tight",
        }
    )
    fig = plt.figure(figsize=(10.2, 6.6), constrained_layout=True)
    grid = fig.add_gridspec(3, 3, width_ratios=(1, 1, 1.05), height_ratios=(1.5, 0.7, 0.9))
    panel_axes: dict[str, list] = {"dynamic": [], "profile": [], "spectrum": []}

    for column, band in enumerate(("CHIME", "DSA")):
        item = bands[band]
        ax_dynamic = fig.add_subplot(grid[0, column])
        panel_axes["dynamic"].append(ax_dynamic)
        scale = np.nanpercentile(np.abs(item["sn"]), 99)
        image = ax_dynamic.imshow(
            item["sn"],
            origin="lower",
            aspect="auto",
            interpolation="nearest",
            extent=(
                item["time_ms"][0],
                item["time_ms"][-1],
                item["freq_mhz"][0],
                item["freq_mhz"][-1],
            ),
            cmap="RdBu_r",
            vmin=-scale,
            vmax=scale,
            rasterized=True,
        )
        ax_dynamic.set_ylabel(r"$\nu$ (MHz)")
        ax_dynamic.set_xlabel(r"$t-t_{\rm peak}$ (ms)")
        ax_dynamic.text(
            0.03,
            0.95,
            item["label"],
            transform=ax_dynamic.transAxes,
            va="top",
            weight="bold",
            color="white",
            bbox={"fc": "black", "alpha": 0.5, "ec": "none", "pad": 2},
        )
        ax_dynamic.text(
            0.98,
            0.03,
            "central window",
            transform=ax_dynamic.transAxes,
            ha="right",
            va="bottom",
            color="white",
            fontsize=8,
        )
        colorbar = fig.colorbar(image, ax=ax_dynamic, pad=0.01, fraction=0.046)
        colorbar.set_label("S/N")

        ax_profile = fig.add_subplot(grid[1, column])
        panel_axes["profile"].append(ax_profile)
        profile = np.nansum(item["sn"], axis=0)
        profile /= np.nanmax(profile)
        ax_profile.plot(item["time_ms"], profile, color=item["color"], lw=1.3)
        ax_profile.axhline(0, color="#777777", lw=0.6)
        ax_profile.fill_between(
            item["time_ms"], 0, profile, where=profile > 0, color=item["color"], alpha=0.2
        )
        ax_profile.set_xlabel(r"$t-t_{\rm peak}$ (ms)")
        ax_profile.set_ylabel("Normalized\nprofile")
        ax_profile.set_ylim(min(-0.15, float(np.nanmin(profile)) * 1.1), 1.08)

        ax_spectrum = fig.add_subplot(grid[2, column])
        panel_axes["spectrum"].append(ax_spectrum)
        ax_spectrum.step(
            item["freq_mhz"],
            item["fluence_spectrum"],
            where="mid",
            color=item["color"],
            lw=1.4,
        )
        ax_spectrum.fill_between(
            item["freq_mhz"],
            0,
            item["fluence_spectrum"],
            step="mid",
            color=item["color"],
            alpha=0.2,
        )
        ax_spectrum.set_xlabel(r"$\nu$ (MHz)")
        ax_spectrum.set_ylabel(r"$\int_{\rm on} S_\nu\,dt$" + "\n(Jy ms)")
        candidate = float(rows[band]["fluence_jy_ms_hz"])
        ax_spectrum.text(
            0.03,
            0.94,
            rf"$I={candidate / 1e9:.2f}\times10^9$ Jy ms Hz",
            transform=ax_spectrum.transAxes,
            va="top",
            fontsize=8.5,
        )

    method_ax = fig.add_subplot(grid[:, 2])
    draw_method_panel(method_ax, rows, nickname)

    ordered_axes = (
        panel_axes["dynamic"] + panel_axes["profile"] + panel_axes["spectrum"] + [method_ax]
    )
    for label, ax in zip(("a", "b", "c", "d", "e", "f", "g"), ordered_axes, strict=True):
        ax.text(
            -0.14,
            1.05,
            label,
            transform=ax.transAxes,
            fontsize=10,
            weight="bold",
            va="bottom",
        )

    output_stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_stem.with_suffix(".pdf"), dpi=300)
    plt.close(fig)

    provenance = {
        "schema_version": 1,
        "figure": [str(output_stem.with_suffix(".pdf"))],
        "status": "candidate_method_illustration_not_manuscript_admitted",
        "nickname": nickname,
        "receipt": str(receipt),
        "receipt_sha256": sha256(receipt),
        "producer": str(Path(__file__).resolve()),
        "producer_sha256": sha256(Path(__file__).resolve()),
        "dsa_beam_cube": str(dsa_beam_cube),
        "dsa_beam_cube_sha256": sha256(dsa_beam_cube),
        "bands": {
            band: {
                "input_path": rows[band]["input_path"],
                "input_sha256": sha256(Path(rows[band]["input_path"])),
                "window_status": rows[band]["window_status"],
                "window_sensitivity_frac": float(rows[band]["window_sensitivity_frac"]),
                "reconstructed_fluence_jy_ms_hz": bands[band]["fluence_jy_ms_hz"],
                "receipt_fluence_jy_ms_hz": float(rows[band]["fluence_jy_ms_hz"]),
                "calibration_status": rows[band]["calibration_status"],
                "noise_status": rows[band]["noise_status"],
                "review_status": rows[band]["review_status"],
            }
            for band in BANDS
        },
    }
    output_stem.with_suffix(".provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--nickname", default="zach")
    parser.add_argument(
        "--receipt",
        type=Path,
        default=HERE / "data_fluences.candidate.csv",
    )
    parser.add_argument("--dsa-beam-cube", type=Path, required=True)
    parser.add_argument(
        "--output-stem",
        type=Path,
        default=HERE / "figures" / "energetics-measurement-method",
    )
    args = parser.parse_args()
    make_figure(
        args.nickname.lower(),
        args.receipt.resolve(),
        args.dsa_beam_cube.resolve(),
        args.output_stem.resolve(),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
