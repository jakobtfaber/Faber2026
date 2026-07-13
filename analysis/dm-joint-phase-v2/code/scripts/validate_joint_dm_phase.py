#!/usr/bin/env python3
"""Held-out synthetic recovery matrix for the custom joint DM-phase fitter."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from dispersion.chime_dm import K_DM
from dispersion.dm_joint_phase import fit_surface, gaussian_joint_fit, phase_surface


def _injection(
    telescope: str,
    residual_dm: float,
    morphology: str,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, float]:
    rng = np.random.default_rng(seed)
    if telescope == "chime":
        frequency = np.linspace(400.2, 799.8, 128)
        dt_s = 5.12e-6
        width_s = 55e-6
        noise = 0.16
    else:
        frequency = np.linspace(1311.25, 1498.75, 192)
        dt_s = 32.768e-6
        width_s = 75e-6
        noise = 0.13
    time = np.arange(2048) * dt_s
    centre = 0.45 * time[-1]
    delay = K_DM * residual_dm * (frequency**-2 - frequency.max() ** -2)
    spectral = 0.65 + 0.35 * np.sin(2 * np.pi * (frequency - frequency.min()) / np.ptp(frequency) * 2.3) ** 2
    pulse = np.exp(-0.5 * ((time[None, :] - centre - delay[:, None]) / width_s) ** 2)
    if morphology == "double":
        pulse += 0.55 * np.exp(
            -0.5 * ((time[None, :] - centre - 2.8 * width_s - delay[:, None]) / (1.3 * width_s)) ** 2
        )
    waterfall = spectral[:, None] * pulse
    waterfall += noise * rng.standard_normal(waterfall.shape)
    return waterfall, frequency, dt_s


def run(output: Path, seeds: int = 3) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    residuals = (-0.42, 0.0, 0.37)
    for morphology in ("single", "double"):
        for injected in residuals:
            for seed in range(seeds):
                band_rows = {}
                for telescope in ("chime", "dsa"):
                    waterfall, frequency, dt_s = _injection(telescope, injected, morphology, seed + 100)
                    grid = np.arange(injected - 0.30, injected + 0.301, 0.01)
                    fit = fit_surface(
                        phase_surface(waterfall, frequency, dt_s, grid, high_hz=5000.0),
                        cutoff_candidates_hz=(500.0, 1000.0, 1500.0, 2500.0, 5000.0),
                    )
                    band_rows[telescope] = {
                        "dm": float(fit.dm),
                        "sigma": float(max(0.005, fit.sigma_jackknife)),
                        "error": float(fit.dm - injected),
                        "cutoff_hz": float(fit.cutoff_hz),
                    }
                joint = gaussian_joint_fit(
                    band_rows["chime"]["dm"], band_rows["chime"]["sigma"],
                    band_rows["dsa"]["dm"], band_rows["dsa"]["sigma"],
                )
                rows.append({
                    "morphology": morphology, "injected_dm": injected, "seed": seed,
                    "chime": band_rows["chime"], "dsa": band_rows["dsa"],
                    "joint": joint, "joint_error": float(joint["dm"] - injected),
                })
    summary = {}
    for label in ("chime", "dsa", "joint"):
        errors = np.asarray([
            row["joint_error"] if label == "joint" else row[label]["error"] for row in rows
        ])
        summary[label] = {
            "n": int(errors.size), "bias": float(np.mean(errors)),
            "rmse": float(np.sqrt(np.mean(errors**2))),
            "median_abs_error": float(np.median(np.abs(errors))),
            "max_abs_error": float(np.max(np.abs(errors))),
        }
    report = {"matrix": rows, "summary": summary}
    (output / "injection_recovery.json").write_text(json.dumps(report, indent=2) + "\n")

    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), constrained_layout=True, sharey=True)
    colors = {"single": "tab:blue", "double": "tab:orange"}
    for ax, label in zip(axes, ("chime", "dsa", "joint"), strict=True):
        for morphology in colors:
            subset = [row for row in rows if row["morphology"] == morphology]
            x = [row["injected_dm"] for row in subset]
            y = [row["joint_error"] if label == "joint" else row[label]["error"] for row in subset]
            ax.scatter(x, y, s=24, alpha=0.75, color=colors[morphology], label=morphology)
        ax.axhline(0, color="black", lw=0.8)
        ax.axhspan(-0.03, 0.03, color="0.5", alpha=0.12)
        stats = summary[label]
        ax.set_title(f"{label.upper()}\nbias={stats['bias']:+.4f}, RMSE={stats['rmse']:.4f}")
        ax.set_xlabel("injected residual DM")
    axes[0].set_ylabel("recovered - injected DM")
    axes[-1].legend(fontsize=8)
    fig.savefig(output / "injection_recovery.png", dpi=180)
    plt.close(fig)
    print(json.dumps(summary, indent=2))
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("results/dm_joint_phase_v2/validation"))
    parser.add_argument("--seeds", type=int, default=3)
    args = parser.parse_args()
    run(args.output, args.seeds)


if __name__ == "__main__":
    main()
