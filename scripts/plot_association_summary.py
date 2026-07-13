#!/usr/bin/env python
"""Generate the manuscript association-summary figure.

The three panels aggregate the same diagnostics shown burst-by-burst in the
appendix cards: timing consistency, positional consistency, and conservative
chance-coincidence probability.  Run from the repository root with
``python scripts/plot_association_summary.py``.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from association_diagnostics import class_aware_chance_probability

PIPELINE = ROOT / "pipeline"
REGISTRY = PIPELINE / "configs" / "bursts.yaml"
TOA_RESULTS = PIPELINE / "crossmatching" / "toa_crossmatch_results.json"
ASSOCIATION_REPORT = PIPELINE / "crossmatching" / "association_report.json"
OUT = ROOT / "figures" / "association_summary.pdf"

CLOCK_MS = 1.0
TNS = {
    "zach": "20220207C",
    "whitney": "20220310F",
    "oran": "20220506D",
    "isha": "20221113A",
    "wilhelm": "20221203A",
    "phineas": "20230307A",
    "freya": "20230325A",
    "johndoeii": "20230814B",
    "hamilton": "20230913A",
    "mahi": "20240122A",
    "chromatica": "20240203A",
    "casey": "20240229A",
}


def _apply_style() -> None:
    try:
        sys.path.insert(0, str(PIPELINE))
        from flits.plotting import use_flits_style

        use_flits_style()
    except (ImportError, ModuleNotFoundError):
        plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})
    plt.rcParams.update(
        {
            "font.size": 8,
            "axes.labelsize": 8,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "axes.linewidth": 0.7,
            "xtick.direction": "in",
            "ytick.direction": "in",
        }
    )


def load_rows() -> list[dict]:
    registry = yaml.safe_load(REGISTRY.read_text())["bursts"]
    toa = {name.lower(): row for name, row in json.loads(TOA_RESULTS.read_text()).items()}
    report = json.loads(ASSOCIATION_REPORT.read_text())
    assoc = {row["name"].lower(): row for row in report["bursts"]}
    rows = []
    for name, rec in registry.items():
        key = name.lower()
        trow, arow = toa[key], assoc[key]
        residual = float(trow["measured_offset_ms"] - trow["geometric_delay_ms"])
        sigma = math.sqrt(
            float(trow.get("combined_dm_uncertainty_ms") or 0.0) ** 2
            + float(trow.get("fwhm_ms") or 0.0) ** 2
            + CLOCK_MS**2
        )
        rows.append(
            {
                "name": key,
                "mjd": float(rec["mjd"]),
                "label": TNS[key],
                "measured_offset_ms": float(trow["measured_offset_ms"]),
                "geometric_delay_ms": float(trow["geometric_delay_ms"]),
                "timing_sigma_ms": sigma,
                "timing_z": residual / sigma,
                "position_ratio": float(arow["position"]["separation_deg"])
                / float(arow["position"]["radius_deg"]),
                "pcc": class_aware_chance_probability(arow, report["inputs"]),
                "dm_constrained": arow["dm_agreement"]["consistent"] is not None,
            }
        )
    return sorted(rows, key=lambda row: row["mjd"])


def render(rows: list[dict], output: Path = OUT) -> None:
    _apply_style()
    x = np.arange(len(rows))
    constrained = np.array([row["dm_constrained"] for row in rows])
    colors = np.where(constrained, "#2563eb", "#d97706")

    fig, axes = plt.subplots(
        3,
        1,
        figsize=(7.2, 5.25),
        sharex=True,
        gridspec_kw={"height_ratios": [1.0, 1.0, 1.08]},
    )
    fig.subplots_adjust(left=0.105, right=0.985, top=0.975, bottom=0.19, hspace=0.16)

    measured = np.array([row["measured_offset_ms"] for row in rows])
    geometric = np.array([row["geometric_delay_ms"] for row in rows])
    timing_sigma = np.array([row["timing_sigma_ms"] for row in rows])
    ax = axes[0]
    ax.vlines(
        x,
        geometric - 3 * timing_sigma,
        geometric + 3 * timing_sigma,
        color="0.65",
        linewidth=0.8,
        zorder=1,
    )
    ax.vlines(
        x,
        geometric - timing_sigma,
        geometric + timing_sigma,
        color="#93c5fd",
        linewidth=5.0,
        alpha=0.75,
        zorder=2,
    )
    ax.plot(x, geometric, color="0.15", linewidth=0.7, marker="D", markersize=2.8, zorder=3)
    ax.scatter(x, measured, c=colors, s=30, edgecolor="white", linewidth=0.5, zorder=4)
    ax.axhline(0, color="0.80", lw=0.6, zorder=0)
    ax.set_ylim(-13, 11)
    ax.set_yticks([-10, -5, 0, 5, 10])
    ax.set_ylabel("CHIME$-$DSA offset at 400 MHz (ms)")
    ax.text(
        0.01,
        0.91,
        r"(a)  12/12 measured offsets within event-specific $3\sigma$",
        transform=ax.transAxes,
    )
    ax.plot([], [], color="0.15", marker="D", markersize=2.8, linewidth=0.7,
            label="predicted geometry")
    ax.plot([], [], color="#93c5fd", linewidth=5.0, alpha=0.75, label=r"$\pm1\sigma$")
    ax.plot([], [], color="0.65", linewidth=0.8, label=r"$\pm3\sigma$")
    ax.legend(loc="lower left", frameon=False, fontsize=6.5, ncol=3,
              handlelength=1.5, columnspacing=0.9)

    position = np.array([row["position_ratio"] for row in rows])
    ax = axes[1]
    ax.axhspan(0, 1, color="#dcfce7", alpha=0.70, zorder=0)
    ax.axhline(1, color="0.35", ls="--", lw=0.8)
    ax.scatter(x, position, c=colors, s=30, edgecolor="white", linewidth=0.5, zorder=3)
    ax.set_ylim(0, 1.08)
    ax.set_ylabel(r"Separation / match radius")
    ax.text(0.01, 0.86, "(b)  12/12 positionally consistent", transform=ax.transAxes)

    pcc = np.array([row["pcc"] for row in rows])
    ax = axes[2]
    ax.axhline(1e-6, color="0.35", ls="--", lw=0.8)
    for i, row in enumerate(rows):
        if row["dm_constrained"]:
            ax.scatter(i, row["pcc"], color="#2563eb", s=30, edgecolor="white", linewidth=0.5)
        else:
            ax.scatter(
                i,
                row["pcc"],
                facecolor="white",
                edgecolor="#d97706",
                linewidth=1.2,
                s=30,
            )
    ax.set_yscale("log")
    ax.set_ylim(1e-9, 1.25e-6)
    ax.set_ylabel(r"Chance probability $P_{\rm cc}$")
    ax.text(0.01, 0.88, r"(c)  12/12 below $10^{-6}$", transform=ax.transAxes)
    ax.scatter([], [], color="#2563eb", s=28, label="DM + position + timing (8)")
    ax.scatter(
        [], [], facecolor="white", edgecolor="#d97706", linewidth=1.2, s=28,
        label="position + timing (4)",
    )
    ax.legend(loc="lower right", frameon=False, fontsize=7, ncol=2, handletextpad=0.4)

    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels([row["label"] for row in rows], rotation=38, ha="right")
    axes[-1].set_xlabel("FRB")
    for ax in axes:
        ax.set_xlim(-0.55, len(rows) - 0.45)
        ax.grid(axis="x", color="0.90", lw=0.5)

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    rows = load_rows()
    render(rows)
    print(
        f"wrote {OUT} ({len(rows)} bursts; "
        f"max |timing|={max(abs(row['timing_z']) for row in rows):.2f} sigma; "
        f"max position/radius={max(row['position_ratio'] for row in rows):.2f}; "
        f"max Pcc={max(row['pcc'] for row in rows):.3e})"
    )


if __name__ == "__main__":
    main()
