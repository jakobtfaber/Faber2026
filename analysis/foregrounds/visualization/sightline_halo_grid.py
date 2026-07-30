#!/usr/bin/env python3
"""Per-sightline foreground-halo grid, in the style of Khrykin et al. 2024
(FLIMFLAM DR1, arXiv:2402.00505) Figure 4.

One panel per co-detection FRB sightline. Each foreground halo (z < z_frb) is
drawn at (redshift, signed projected impact parameter), as an open gray circle
whose radius is the halo's projected virial radius (R200, delta_def=200 in the
catalog) converted to kpc, with a filled marker colored by log10(M_halo/Msun).
A black spiral-galaxy glyph marks the FRB host at (z_frb, 0); the horizontal
line is the sightline.

The y coordinate is the true projected offset of the halo from the sightline,
signed by the declination difference (halo north of the FRB is +), so halos
spread above and below the sightline as in the reference figure -- the catalog
stores only the unsigned impact parameter b_kpc, which we use for the magnitude
and R_vir geometry and sign by sky position.

Data: the checked-in ``foregrounds/census/data/sightline_halo_grid.csv``. All
twelve sightlines are shown. Diagnostic DM-redshift intervals and unadmitted
foreground candidates are visually distinct from established host redshifts and
confirmed systems.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Ellipse
from matplotlib.path import Path as MplPath

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from foregrounds.census.build_sightline_halo_grid_input import validate_frame  # noqa: E402

# Deterministic style regardless of run location. matplotlib auto-loads the
# repository matplotlibrc (serif/CM fonts, savefig.bbox=tight, ...) only when the
# process starts in its directory, which made both fonts and output
# size cwd-dependent. Load that rc explicitly by path so every run gets the
# same fonts, then re-pin the save geometry: 'standard' (not 'tight') is
# required here because tight re-lays-out the axes after the display-space
# circle radii were computed against the drawn geometry, distorting the R200
# circles. (Passing bbox_inches=None to savefig does NOT override the rc.)
_RC = os.path.join(_REPO, "matplotlibrc")
if os.path.exists(_RC):
    matplotlib.rc_file(_RC)
plt.rcParams["savefig.bbox"] = "standard"
plt.rcParams["savefig.pad_inches"] = 0.05
DEFAULT_RESULTS_DIR = os.path.join(_REPO, "results")
DEFAULT_OUT_DIR = os.path.join(
    _REPO,
    "figure_review",
    "artifacts",
    "staging",
    "fig3_halo_grid",
    "figures",
)
MANUSCRIPT_FIGURES_DIR = Path(_REPO).parent / "figures"
CANONICAL_INPUT = Path(_REPO) / "foregrounds" / "census" / "data" / "sightline_halo_grid.csv"
CANONICAL_RECEIPT = CANONICAL_INPUT.with_suffix(".receipt.json")

# Colorbar range for log10(M_halo/Msun). Tuned to the recovered halo population
# (bulk 11-13.2, tail to 14.4) so magma's full sweep is used instead of pinning
# most halos into one hue; the massive cluster still saturates the bright end.
MASS_MIN, MASS_MAX = 11.0, 14.0
# magma matches the burst dynamic-spectrum waterfalls (codetection_plots
# water_cmap default), keeping the manuscript's figure palette consistent.
CMAP = "magma"
Y_LIM = 600.0  # impact parameter axis half-range, kpc


def _contributor_mask(frame: pd.DataFrame) -> pd.Series:
    """Return a Boolean mask for optional budget-contributor annotations."""
    if "budget_contributor" not in frame:
        return pd.Series(False, index=frame.index, dtype=bool)
    return frame["budget_contributor"].map(
        lambda value: value is True
        or value == 1
        or (isinstance(value, str) and value.strip().lower() in {"1", "true"})
    )


def _load(halo_csv: str):
    """Return validated drawable systems and metadata for all twelve panels."""
    df = pd.read_csv(halo_csv)
    validate_frame(df)
    hosts = df[df["row_kind"] == "host"].drop_duplicates("frb_name")
    roster = {
        str(row.frb_name): row._asdict()
        for row in hosts.sort_values("nickname").itertuples(index=False)
    }

    fg = df[
        (df["row_kind"] == "system") & (df["geometry_status"] == "pass")
    ].copy()
    fg = fg[
        fg["system_z"].notna()
        & fg["impact_kpc"].notna()
        & fg["mass_msun"].notna()
        & fg["radius_kpc"].notna()
    ]
    fg = fg[fg["frb_name"].isin(roster)].copy()
    # Signed projected offset: magnitude = b_kpc, sign from declination diff.
    ddec = fg["candidate_dec_deg"].to_numpy(float) - fg["frb_dec_deg"].to_numpy(float)
    fg["b_signed"] = np.where(ddec >= 0, 1.0, -1.0) * fg["impact_kpc"].to_numpy(float)
    fg["logM"] = np.log10(fg["mass_msun"].astype(float))
    return fg, roster


CLUSTER_MASS = 1.0e14  # M200 threshold for "cluster" (vs galaxy-scale halo)


def _galaxy_path(incl=0.30, bulge_r=0.42, n=64):
    """Inclined-disk 'mini galaxy' glyph as a single filled Path.

    An ellipse of aspect `incl` (inclined disk) tilted 25 deg, with a round
    central bulge that PROTRUDES beyond the disk minor axis (bulge_r > incl):
    the classic edge-on-galaxy silhouette. The protrusion is load-bearing --
    a bulge hidden inside the same-color disk renders as a plain tilted
    ellipse, which in this figure shares a silhouette class with the R200
    halo Ellipse patches it must be distinguished from. This reads instantly
    as a galaxy at ~12 px raster, where a filled two-arm spiral collapses
    into an ambiguous S/yin-yang shape. Normalized to unit max extent so
    scatter's `s` scales it like a builtin marker.
    """
    t = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    tilt = np.deg2rad(25.0)
    ct, st = np.cos(tilt), np.sin(tilt)
    # Disk ellipse (semi-axes 1.0 x incl), rotated by tilt.
    dx, dy = np.cos(t), incl * np.sin(t)
    disk = np.column_stack([dx * ct - dy * st, dx * st + dy * ct])
    disk = np.vstack([disk, disk[0]])  # closing vertex for CLOSEPOLY
    # Central bulge: protrudes above/below the disk plane.
    bulge = MplPath.circle((0.0, 0.0), bulge_r)
    verts = [disk, bulge.vertices]
    codes = [
        [MplPath.MOVETO] + [MplPath.LINETO] * (len(disk) - 2) + [MplPath.CLOSEPOLY],
        list(bulge.codes),
    ]
    p = MplPath(np.vstack(verts), np.concatenate(codes).astype(np.uint8))
    m = np.abs(p.vertices).max()
    return MplPath(p.vertices / m, p.codes)


GALAXY_MARKER = _galaxy_path()


def _crossing_mask(sub: pd.DataFrame) -> np.ndarray:
    """The cluster-scale halo the sightline pierces within R200.

    The manuscript's budget cut retains a single such system across the whole
    sample -- the massive cluster in the FRB 20230307A field. We emphasize
    exactly that: strict R200 intersection AND cluster mass (M200 > 1e14). Lower-
    mass strict intersections are galaxy halos already carried in the galaxy
    budget, so they are not singled out here.
    """
    cluster = sub["system_type"].astype(str).eq("cluster").to_numpy()
    intersects = sub["impact_kpc"].astype(float).to_numpy() <= sub["radius_kpc"].astype(float).to_numpy()
    return cluster & intersects


def _diagnostic_limitations(metadata: dict) -> str:
    """Return compact panel text while retaining every recorded limitation."""
    query = str(metadata["query_limitations"]).replace(
        "exact query receipts missing: ", "missing queries: "
    )
    coverage = str(metadata["coverage_limitations"]).replace(
        "outside footprint: ", "coverage gaps: "
    ).replace("footprint evidence incomplete: ", "missing footprint: ")
    return "diagnostic only\n" + query + "\n" + coverage.replace("; ", "\n")


def make_grid(halo_csv: str):
    fg, roster = _load(halo_csv)
    # All twelve panels, ordered by their established or diagnostic central z.
    order = sorted(roster, key=lambda key: float(roster[key]["frb_z"]))
    n = len(order)
    ncols = 3
    nrows = math.ceil(n / ncols)

    ink = "#22252b"       # near-black ink for text/spines (softer than pure black)
    faint = "#9aa0a8"     # secondary gray
    sightline_c = "#3a3f47"
    corridor_c = "#eef0f3"  # faint shaded impact corridor

    # Wider-than-tall panels keep the whole 5x2 grid short enough that the
    # figure* + its long caption fit one manuscript page (a taller grid overflows
    # and sends latexmk into an output dead-cycle loop).
    fig, axes = plt.subplots(
        nrows, ncols, figsize=(12.0, 2.15 * nrows), sharex=True, sharey=True,
    )
    axes = np.atleast_1d(axes).ravel()
    fig.subplots_adjust(top=0.86, bottom=0.09, left=0.105, right=0.985,
                        hspace=0.42, wspace=0.08)

    norm = plt.Normalize(vmin=MASS_MIN, vmax=MASS_MAX)
    # magma matches the burst waterfalls; drop the near-black bottom so low-mass
    # points read on white, and reuse the same ramp to tint the R200 disks.
    base = plt.get_cmap(CMAP)
    cmap = ListedColormap(base(np.linspace(0.18, 1.0, 256)))

    z_max = max(float(row["frb_z_upper"]) for row in roster.values())
    x_hi = 0.05 * math.ceil((z_max + 0.02) / 0.05)

    for _i, (ax, name) in enumerate(zip(axes, order, strict=False)):
        metadata = roster[name]
        z_frb = float(metadata["frb_z"])
        inferred = metadata["redshift_class"] == "inferred_dm_z"
        # Faint impact corridor (|b| < 300 kpc), a soft depth band around the LOS.
        ax.axhspan(-300, 300, color=corridor_c, zorder=0)
        ax.axhline(0.0, color=sightline_c, lw=0.9, zorder=1)

        if inferred:
            z_lower = float(metadata["frb_z_lower"])
            z_upper = float(metadata["frb_z_upper"])
            ax.axvspan(z_lower, z_upper, color="#3977a8", alpha=0.09, zorder=0)
            ax.errorbar(
                [z_frb],
                [0.0],
                xerr=[[z_frb - z_lower], [z_upper - z_frb]],
                fmt="none",
                ecolor="#3977a8",
                elinewidth=1.4,
                capsize=3,
                zorder=5,
            )
            ax.scatter(
                [z_frb],
                [0.0],
                marker=GALAXY_MARKER,
                s=680,
                facecolors="white",
                edgecolors="#245b83",
                linewidths=1.3,
                zorder=6,
            )
            z_label = (
                r"$z_{\rm DM}=$"
                f"{z_frb:.3f}\n[{z_lower:.3f}, {z_upper:.3f}]"
            )
            ax.text(
                0.98, 0.035, _diagnostic_limitations(metadata),
                transform=ax.transAxes,
                fontsize=5.4,
                color="#245b83",
                va="bottom",
                ha="right",
                linespacing=1.15,
                zorder=7,
            )
        else:
            ax.scatter([z_frb], [0.0], marker=GALAXY_MARKER, s=900, color="white",
                       edgecolors="none", zorder=5)
            ax.scatter([z_frb], [0.0], marker=GALAXY_MARKER, s=680, color=ink,
                       edgecolors="none", zorder=6)
            z_label = r"$z_{\rm spec}=$" + f"{z_frb:.4f}"

        # Title in a translucent chip so it stays legible over any halo disk.
        ax.text(0.025, 0.93,
                f"{name}\n{z_label}",
                transform=ax.transAxes, fontsize=9.8, color=ink,
                va="top", ha="left", linespacing=1.4,
                bbox=dict(boxstyle="round,pad=0.32", facecolor="white",
                          edgecolor="none", alpha=0.78), zorder=7)

        ax.set_xlim(0.0, x_hi)
        ax.set_ylim(-Y_LIM, Y_LIM)
        ax.set_yticks([-500, -250, 0, 250, 500])
        ax.yaxis.set_minor_locator(mticker.MultipleLocator(125))
        ax.xaxis.set_major_locator(mticker.MultipleLocator(0.1))
        ax.xaxis.set_minor_locator(mticker.MultipleLocator(0.05))
        # Lighter frame: keep left/bottom, drop top/right. Ticks stay dark and
        # inward on every panel so the redshift / impact-parameter scale is
        # readable even on interior panels (labels remain edge-only via sharex/y).
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(ink)
            ax.spines[side].set_linewidth(0.9)
        ax.tick_params(which="major", direction="in", length=4.5, width=0.9,
                       color=ink, labelcolor=ink, labelsize=9.5,
                       top=False, right=False)
        ax.tick_params(which="minor", direction="in", length=2.5, width=0.7,
                       color=ink, top=False, right=False)

    # Halo markers drawn after limits are fixed so R200 disks are round in
    # display space (600 kpc on y vs ~0.5 in z on x is a ~10^5 scale mismatch;
    # a data-unit circle would collapse to a vertical sliver -- we size the disk
    # by R200 on y and map that same pixel radius back through the x scale).
    fig.canvas.draw()
    for ax, name in zip(axes, order, strict=False):
        bbox = ax.get_window_extent()
        x0, x1 = ax.get_xlim()
        y0, y1 = ax.get_ylim()
        x_per_px = (x1 - x0) / bbox.width
        y_per_px = (y1 - y0) / bbox.height
        sub = fg[fg["frb_name"] == name].reset_index(drop=True)
        confirmed = sub[sub["evidence_class"] == "confirmed_system"].reset_index(drop=True)
        candidates = sub[
            sub["evidence_class"] == "probabilistic_candidate"
        ].reset_index(drop=True)
        cross = _crossing_mask(confirmed)
        # Draw largest disks first so small halos sit on top (readability).
        draw_order = confirmed["radius_kpc"].astype(float).fillna(0).argsort()[::-1]
        for idx in draw_order:
            row = confirmed.iloc[idx]
            r_kpc = float(row.get("radius_kpc", float("nan")))
            y = float(row["b_signed"])
            x = float(row["system_z"])
            col = cmap(norm(row["logM"]))
            is_cross = bool(cross[idx])
            if math.isfinite(r_kpc) and r_kpc > 0:
                r_px = r_kpc / y_per_px
                w, h = 2.0 * r_px * x_per_px, 2.0 * r_px * y_per_px
                # Soft mass-tinted fill = the halo's extent; thin edge for shape.
                ax.add_patch(Ellipse((x, y), w, h, facecolor=col, alpha=0.14,
                                     edgecolor="none", zorder=2))
                ax.add_patch(Ellipse((x, y), w, h, fill=False,
                                     edgecolor=col if not is_cross else ink,
                                     lw=1.4 if is_cross else 0.7,
                                     alpha=0.9 if is_cross else 0.55, zorder=3))
            # Center marker; crossing cluster gets a ring (keyed in the legend).
            if is_cross:
                ax.scatter([x], [y], s=90, facecolors="none", edgecolors=ink,
                           linewidths=1.1, zorder=6)
            ax.scatter([x], [y], c=[col], s=26, edgecolors=ink,
                       linewidths=0.4, zorder=4)
        for _, row in candidates.iterrows():
            x = float(row["system_z"])
            y = float(row["b_signed"])
            lower = float(row["system_z_lower"])
            upper = float(row["system_z_upper"])
            probability = float(row["candidate_foreground_probability"])
            ax.errorbar(
                [x],
                [y],
                xerr=[[x - lower], [upper - x]],
                fmt="D",
                markersize=4.4,
                markerfacecolor="white",
                markeredgecolor="#176f9f",
                ecolor="#176f9f",
                elinewidth=0.9,
                capsize=2,
                alpha=0.9,
                zorder=6,
            )
            ax.annotate(
                rf"$P_{{\rm fg}}={probability:.2f}$",
                (x, y),
                xytext=(4, 4),
                textcoords="offset points",
                fontsize=6.4,
                color="#176f9f",
                zorder=7,
            )
        if sub.empty and roster[name]["redshift_class"] == "established":
            ax.text(
                0.5,
                0.52,
                "no systems plotted\nnot a foreground-free claim",
                transform=ax.transAxes,
                ha="center",
                va="center",
                fontsize=7.5,
                color=faint,
            )

    for ax in axes[n:]:
        ax.set_visible(False)

    legend_handles = [
        Line2D(
            [],
            [],
            marker=GALAXY_MARKER,
            markersize=9,
            markerfacecolor=ink,
            markeredgecolor=ink,
            linestyle="none",
            label="established host",
        ),
        Line2D(
            [],
            [],
            marker=GALAXY_MARKER,
            markersize=9,
            markerfacecolor="white",
            markeredgecolor="#245b83",
            linestyle="none",
            label="diagnostic dispersion-measure redshift",
        ),
        Line2D(
            [],
            [],
            marker="o",
            markersize=5,
            markerfacecolor=cmap(norm(12.5)),
            markeredgecolor=ink,
            linestyle="none",
            label="confirmed foreground system",
        ),
        Line2D(
            [],
            [],
            marker="D",
            markersize=5,
            markerfacecolor="white",
            markeredgecolor="#176f9f",
            linestyle="none",
            label="unadmitted candidate",
        ),
        Line2D(
            [],
            [],
            marker="o",
            markersize=7,
            markerfacecolor="none",
            markeredgecolor=ink,
            linestyle="none",
            label="cluster crossing",
        ),
    ]
    fig.legend(
        handles=legend_handles,
        loc="upper left",
        bbox_to_anchor=(0.105, 0.985),
        ncol=2,
        frameon=False,
        fontsize=8.1,
        handletextpad=0.5,
        columnspacing=1.3,
    )

    # Single shared axis labels (supxlabel/supylabel) instead of per-panel labels:
    # the panels are short, so a per-panel rotated y-label would span the panel
    # height and collide with the neighbor's ticks.
    fig.supylabel("impact parameter  [kpc]", fontsize=12.5, color=ink, x=0.035)
    fig.supxlabel("redshift", fontsize=12.5, color=ink, y=0.045)

    # Bottom-most VISIBLE panel in each column still needs its x-tick LABELS on
    # (sharex hides them; the odd panel count means the legend replaced a slot).
    for col in range(ncols):
        col_idx = [i for i in range(n) if i % ncols == col]
        if col_idx:
            axes[max(col_idx)].tick_params(axis="x", labelbottom=True)

    # Horizontal colorbar, spanning the plot width, ticks on top.
    sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])
    cax = fig.add_axes([0.63, 0.946, 0.32, 0.014])
    cbar = fig.colorbar(sm, cax=cax, orientation="horizontal")
    cbar.ax.xaxis.set_ticks_position("top")
    cbar.ax.xaxis.set_label_position("top")
    cbar.outline.set_edgecolor(faint)
    cbar.outline.set_linewidth(0.6)
    cbar.ax.tick_params(colors=faint, labelcolor=ink, labelsize=9.5, width=0.6)
    cbar.set_label(r"$\log_{10}\,(M_{\mathrm{halo}}/M_\odot)$", fontsize=11.5,
                   color=ink, labelpad=6)

    return fig


def main():
    import argparse

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--halo-csv", required=True)
    p.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    p.add_argument(
        "--review-candidate",
        action="store_true",
        help="write a provenance-bound review candidate; never promote it",
    )
    args = p.parse_args()

    out_dir = Path(args.out_dir).resolve()
    if out_dir == MANUSCRIPT_FIGURES_DIR.resolve():
        p.error("manuscript figures are promotion targets, not generator outputs")
    if args.review_candidate:
        if out_dir != Path(DEFAULT_OUT_DIR).resolve():
            p.error("review candidates may only be written to the declared staging directory")
        halo_path = Path(args.halo_csv).resolve()
        if halo_path != CANONICAL_INPUT.resolve():
            p.error("review candidates require the canonical Figure 3 input")
        input_hash = hashlib.sha256(halo_path.read_bytes()).hexdigest()
        input_receipt = json.loads(CANONICAL_RECEIPT.read_text(encoding="utf-8"))
        recorded_hash = input_receipt["output"][
            "foregrounds/census/data/sightline_halo_grid.csv"
        ]
        if input_hash != recorded_hash:
            p.error("canonical Figure 3 input differs from its reproduction receipt")
    out_dir.mkdir(parents=True, exist_ok=True)
    fig = make_grid(args.halo_csv)
    outputs: dict[str, str] = {}
    for ext in ("pdf", "svg", "png"):
        path = out_dir / f"sightline_halo_grid.{ext}"
        # Save geometry is pinned at import (savefig.bbox='standard') so the
        # output is identical from any working directory. Matplotlib otherwise
        # inserts the current time into each PDF, so omit both PDF timestamps.
        metadata = {"CreationDate": None, "ModDate": None} if ext == "pdf" else None
        fig.savefig(path, metadata=metadata)
        outputs[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        print(f"wrote {path}")
    plt.close(fig)
    if args.review_candidate:
        try:
            input_display = str(halo_path.relative_to(Path(_REPO)))
        except ValueError:
            input_display = str(halo_path)
        provenance_dir = out_dir.parent / "provenance"
        provenance_dir.mkdir(parents=True, exist_ok=True)
        receipt = {
            "schema_version": 1,
            "status": "review_candidate_generated",
            "manuscript_promotion": "blocked_pending_owner_visual_approval",
            "input": {
                "path": input_display,
                "sha256": input_hash,
                "receipt": str(CANONICAL_RECEIPT.relative_to(Path(_REPO))),
                "receipt_sha256": hashlib.sha256(CANONICAL_RECEIPT.read_bytes()).hexdigest(),
            },
            "outputs": outputs,
            "manuscript_target": "figures/sightline_halo_grid.pdf",
        }
        receipt_path = provenance_dir / "figure3-candidate.json"
        receipt_path.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"wrote {receipt_path}")


if __name__ == "__main__":
    main()
