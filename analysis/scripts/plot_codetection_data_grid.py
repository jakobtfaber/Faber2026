"""Render Figure 1: a 12-panel grid of the joint CHIME/DSA observations.

For the eleven accepted joint fits, each panel uses the exact fit-delivery data
grid and CHIME-width crop stored beside the model in the jointmodel NPZ. The
Chromatica panel uses the same archival data-only exception as the triptych
producer. No model or residual values are drawn.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

from plot_codetection_triptych import (
    DATA_ROOT_DEFAULT,
    MANIFEST_DEFAULT,
    ROOT,
    bands_data_only,
    bands_from_npz,
    load_manifest,
)

OUT_DEFAULT = ROOT / "figures" / "codetection_data_grid"
GAP_FILL = "0.93"


def _finite_percentile(values: np.ndarray, percentile: float, default: float) -> float:
    finite = np.asarray(values, float)
    finite = finite[np.isfinite(finite)]
    return default if finite.size == 0 else float(np.percentile(finite, percentile))


def load_row_bands(row: dict, *, root: Path, data_root: Path):
    """Load the same observed arrays and crop used by the triptych left column."""
    if row.get("npz"):
        return bands_from_npz(root / row["npz"], row["nick"])
    return bands_data_only(data_root, row["nick"])


def draw_joint_waterfall(ax, bands, *, title: str) -> None:
    bands = sorted(bands, key=lambda band: band.frange[0])
    cmap = matplotlib.colormaps["magma"].copy()
    cmap.set_bad("white")
    for band in bands:
        data = np.asarray(band.data, float)
        lo = _finite_percentile(data, 1.0, -1.0)
        hi = _finite_percentile(data, 99.5, 1.0)
        if hi <= lo:
            hi = lo + 1.0
        ax.imshow(
            data,
            origin="lower",
            aspect="auto",
            interpolation="nearest",
            cmap=cmap,
            vmin=lo,
            vmax=hi,
            extent=(band.time_ms[0], band.time_ms[-1], *band.frange),
            rasterized=True,
        )
    for lower, upper in zip(bands[:-1], bands[1:], strict=False):
        if upper.frange[0] > lower.frange[1]:
            ax.add_patch(
                Rectangle(
                    (min(b.time_ms[0] for b in bands), lower.frange[1]),
                    max(b.time_ms[-1] for b in bands) - min(b.time_ms[0] for b in bands),
                    upper.frange[0] - lower.frange[1],
                    facecolor="white",
                    edgecolor="0.55",
                    hatch="////",
                    linewidth=0,
                    zorder=0.5,
                )
            )
    ax.set_xlim(min(b.time_ms[0] for b in bands), max(b.time_ms[-1] for b in bands))
    ax.set_ylim(min(b.frange[0] for b in bands), max(b.frange[1] for b in bands))
    ax.set_title(title, fontsize=9, pad=3)
    ax.tick_params(labelsize=7, direction="in", top=True, right=True)


def render_grid(rows: list[dict], *, root: Path, data_root: Path, out: Path, dpi: int) -> None:
    fig, axes = plt.subplots(3, 4, figsize=(13.2, 9.2), constrained_layout=True)
    for index, (ax, row) in enumerate(zip(axes.flat, rows, strict=True)):
        bands = load_row_bands(row, root=root, data_root=data_root)
        draw_joint_waterfall(ax, bands, title=row["tns"])
        if index // 4 == 2:
            ax.set_xlabel("Time (ms)", fontsize=8)
        if index % 4 == 0:
            ax.set_ylabel("Frequency (MHz)", fontsize=8)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out.with_suffix(".png"), dpi=dpi)
    fig.savefig(out.with_suffix(".pdf"))
    fig.savefig(out.with_suffix(".svg"))
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_DEFAULT)
    parser.add_argument("--data-root", type=Path, default=DATA_ROOT_DEFAULT)
    parser.add_argument("--out", type=Path, default=OUT_DEFAULT)
    parser.add_argument("--dpi", type=int, default=300)
    args = parser.parse_args()
    rows = load_manifest(args.manifest)
    render_grid(rows, root=ROOT, data_root=args.data_root, out=args.out, dpi=args.dpi)
    print(f"wrote {args.out.with_suffix('.pdf')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
