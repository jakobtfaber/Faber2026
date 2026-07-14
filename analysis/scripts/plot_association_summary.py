#!/usr/bin/env python
"""Generate the manuscript association-summary figure.

The four panels aggregate timing consistency, positional consistency, the new
phase-coherence DM comparison, and conservative chance-coincidence probability.
Run from the repository root with
``python scripts/plot_association_summary.py``.
"""

from __future__ import annotations

import csv
import json
import math
import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from association_diagnostics import class_aware_chance_probability  # noqa: E402

PIPELINE = ROOT / "pipeline"
PIPELINE_SOURCE = Path(os.environ.get("FABER2026_PIPELINE_SOURCE", PIPELINE))
REGISTRY = PIPELINE_SOURCE / "configs" / "bursts.yaml"
TOA_RESULTS = PIPELINE_SOURCE / "crossmatching" / "toa_crossmatch_results.json"
ASSOCIATION_REPORT = PIPELINE_SOURCE / "crossmatching" / "association_report.json"
OUT = ROOT / "figures" / "association_summary.pdf"
DM_CATALOG = ROOT / "analysis" / "dm-joint-phase-v2" / "manuscript_dm_catalog.csv"

CLOCK_MS = 1.0
DM_COLOR = "#0072B2"  # Okabe--Ito blue
POSITION_TIME_COLOR = "#D55E00"  # Okabe--Ito vermillion
ONE_SIGMA_COLOR = "0.78"
THREE_SIGMA_COLOR = "0.58"
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
    """Apply the manuscript's Computer Modern style without optional packages."""
    plt.rcParams.update(
        {
            "text.usetex": False,
            "font.family": "serif",
            "font.serif": ["cmr10", "Computer Modern Roman", "DejaVu Serif"],
            "mathtext.fontset": "cm",
            "axes.formatter.use_mathtext": True,
            "axes.unicode_minus": False,
            "font.size": 7.5,
            "axes.labelsize": 8.0,
            "axes.linewidth": 0.8,
            "legend.fontsize": 7.0,
            "pdf.fonttype": 42,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.04,
            "xtick.direction": "in",
            "xtick.labelsize": 7.0,
            "xtick.major.size": 3.5,
            "xtick.minor.visible": False,
            "xtick.top": True,
            "ytick.direction": "in",
            "ytick.labelsize": 7.0,
            "ytick.major.size": 3.5,
            "ytick.minor.visible": False,
            "ytick.right": True,
        }
    )


def load_rows() -> list[dict]:
    registry = yaml.safe_load(REGISTRY.read_text())["bursts"]
    toa = {name.lower(): row for name, row in json.loads(TOA_RESULTS.read_text()).items()}
    report = json.loads(ASSOCIATION_REPORT.read_text())
    assoc = {row["name"].lower(): row for row in report["bursts"]}
    with DM_CATALOG.open(newline="") as fh:
        dm_rows = {row["nick"].lower(): row for row in csv.DictReader(fh)}
    if set(dm_rows) != set(registry):
        raise ValueError("burst registry and verified-DM catalog rosters differ")

    rows = []
    for name, rec in registry.items():
        key = name.lower()
        trow, arow = toa[key], assoc[key]
        dm_row = dm_rows[key]
        residual = float(trow["measured_offset_ms"] - trow["geometric_delay_ms"])
        sigma = math.sqrt(
            float(trow.get("combined_dm_uncertainty_ms") or 0.0) ** 2
            + float(trow.get("fwhm_ms") or 0.0) ** 2
            + CLOCK_MS**2
        )
        dm_sigma = math.sqrt(
            float(dm_row["chime_sigma"]) ** 2
            + float(dm_row["dsa_sigma"]) ** 2
            + float(dm_row["between_band_sigma"]) ** 2
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
                "pcc": class_aware_chance_probability(
                    arow,
                    dm=float(dm_row["adopted_dm"]),
                    inputs=report["inputs"],
                ),
                "dm_constrained": arow["dm_agreement"]["consistent"] is not None,
                "dm_difference": float(dm_row["chime_minus_dsa"]),
                "dm_difference_sigma": dm_sigma,
            }
        )
    return sorted(rows, key=lambda row: row["mjd"])


def render(rows: list[dict], output: Path = OUT) -> None:
    _apply_style()
    x = np.arange(len(rows))
    constrained = np.array([row["dm_constrained"] for row in rows])

    def plot_measured(ax: plt.Axes, values: np.ndarray) -> None:
        """Use one class encoding consistently in every diagnostic panel."""
        ax.scatter(
            x[constrained],
            values[constrained],
            color=DM_COLOR,
            s=30,
            edgecolor="white",
            linewidth=0.5,
            zorder=4,
        )
        ax.scatter(
            x[~constrained],
            values[~constrained],
            facecolor="white",
            edgecolor=POSITION_TIME_COLOR,
            s=30,
            linewidth=1.2,
            zorder=4,
        )

    fig, axes = plt.subplots(
        4,
        1,
        figsize=(7.1, 6.1),
        sharex=True,
        gridspec_kw={"height_ratios": [1.0, 0.9, 0.9, 1.0]},
    )
    fig.subplots_adjust(left=0.095, right=0.99, top=0.99, bottom=0.16, hspace=0.13)

    measured = np.array([row["measured_offset_ms"] for row in rows])
    geometric = np.array([row["geometric_delay_ms"] for row in rows])
    timing_sigma = np.array([row["timing_sigma_ms"] for row in rows])
    ax = axes[0]
    timing_ylim = (-14.0, 10.0)
    lower_3sigma = geometric - 3 * timing_sigma
    upper_3sigma = geometric + 3 * timing_sigma

    # These are event-specific acceptance intervals about the geometric null,
    # not errors on tau_geo.  Neutral grays avoid conflating uncertainty with
    # the blue/orange association classes.
    ax.vlines(
        x,
        lower_3sigma,
        upper_3sigma,
        color=THREE_SIGMA_COLOR,
        linewidth=0.8,
        zorder=1,
    )
    ax.vlines(
        x,
        geometric - timing_sigma,
        geometric + timing_sigma,
        color=ONE_SIGMA_COLOR,
        linewidth=4.5,
        zorder=2,
    )

    # Each diamond is an independent sky-position prediction.  Connecting
    # them would imply a temporal trend or meaningful interpolation.
    ax.scatter(x, geometric, color="0.12", marker="D", s=18, zorder=3)
    plot_measured(ax, measured)

    # The two broadest timing budgets exceed the useful display range.  Mark
    # truncation explicitly instead of allowing clipped lines to look finite.
    below = lower_3sigma < timing_ylim[0]
    above = upper_3sigma > timing_ylim[1]
    ax.scatter(
        x[below],
        np.full(np.count_nonzero(below), timing_ylim[0] + 0.35),
        marker="v",
        color=THREE_SIGMA_COLOR,
        s=14,
        linewidth=0,
        zorder=3,
    )
    ax.scatter(
        x[above],
        np.full(np.count_nonzero(above), timing_ylim[1] - 0.35),
        marker="^",
        color=THREE_SIGMA_COLOR,
        s=14,
        linewidth=0,
        zorder=3,
    )
    ax.axhline(0, color="0.80", lw=0.6, zorder=0)
    ax.set_ylim(*timing_ylim)
    ax.set_yticks([-10, -5, 0, 5, 10])
    ax.set_ylabel(r"Arrival-time offset, $\Delta t_{400}$ (ms)")
    ax.text(0.01, 0.92, r"(a)", transform=ax.transAxes)
    ax.scatter([], [], color="0.12", marker="D", s=18,
               label=r"$\tau_{\rm geo}$ prediction")
    ax.plot([], [], color=ONE_SIGMA_COLOR, linewidth=4.5, label=r"$1\sigma$ interval")
    ax.plot([], [], color=THREE_SIGMA_COLOR, linewidth=0.8, label=r"$3\sigma$ interval")
    ax.legend(loc="lower left", frameon=False, fontsize=6.5, ncol=3,
              handlelength=1.5, columnspacing=0.9)

    position = np.array([row["position_ratio"] for row in rows])
    ax = axes[1]
    ax.axhline(1, color="0.35", ls="--", lw=0.8)
    plot_measured(ax, position)
    ax.set_ylim(0, 1.08)
    ax.set_ylabel(r"$\theta/\theta_{\rm match}$")
    ax.text(0.01, 0.88, r"(b)", transform=ax.transAxes)

    dm_difference = np.array([row["dm_difference"] for row in rows])
    dm_difference_sigma = np.array([row["dm_difference_sigma"] for row in rows])
    ax = axes[2]
    ax.axhline(0, color="0.35", ls="--", lw=0.8)
    ax.errorbar(
        x,
        dm_difference,
        yerr=dm_difference_sigma,
        fmt="none",
        ecolor="0.55",
        elinewidth=0.8,
        capsize=1.8,
        zorder=2,
    )
    plot_measured(ax, dm_difference)
    ax.set_ylim(-0.16, 0.12)
    ax.set_ylabel(r"$\mathrm{DM}_{\rm C}-\mathrm{DM}_{\rm D}$" + "\n" + r"($\mathrm{pc\,cm^{-3}}$)")
    ax.text(0.01, 0.86, r"(c)", transform=ax.transAxes)

    pcc = np.array([row["pcc"] for row in rows])
    ax = axes[3]
    ax.axhline(1e-6, color="0.35", ls="--", lw=0.8)
    plot_measured(ax, pcc)
    ax.set_yscale("log")
    ax.set_ylim(1e-9, 1.25e-6)
    ax.set_ylabel(r"$P_{\rm cc}$")
    ax.text(0.01, 0.88, r"(d)", transform=ax.transAxes)
    ax.scatter([], [], color=DM_COLOR, edgecolor="white", linewidth=0.5,
               s=28, label="pre-specified DM term (8)")
    ax.scatter(
        [], [], facecolor="white", edgecolor=POSITION_TIME_COLOR,
        linewidth=1.2, s=28, label="position and timing only (4)",
    )
    ax.legend(loc="lower right", frameon=False, fontsize=7, ncol=2, handletextpad=0.4)

    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels([row["label"] for row in rows], rotation=38, ha="right")
    for ax in axes:
        ax.set_xlim(-0.55, len(rows) - 0.45)
        ax.grid(axis="x", color="0.92", lw=0.45)

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
