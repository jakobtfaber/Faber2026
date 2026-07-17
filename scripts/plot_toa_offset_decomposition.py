#!/usr/bin/env python
"""Decompose the CHIME-DSA arrival offset into geometric pedestal + residual.

Reproduces figures/toa_offset_decomposition.pdf (fig:toa-offset-decomposition,
sec:toa). For each of the twelve co-detections the measured 400-MHz arrival
offset (``measured_offset_ms``, the adopted model-t0 offset once the pipeline pin
carries the ToA definition switch) is split as

    offset = geometric_delay + residual,

where ``geometric_delay_ms`` is the predicted DRAO--OVRO inter-site delay for the
source direction. The sources cluster in declination near CHIME transit, so the
geometric term is a near-constant pedestal (~-2.17 ms, CHIME ahead) that cannot
flip the arrival order; the sign is set by the residual. A secondary top axis
expresses the offset as an equivalent shared-DM error via
d(offset)/dDM = -9.4078 ms per pc cm^-3 (K_DM=4148.808, f_ref=400, f_DSA=1405,
f_CHIME=600.39 MHz).

Reads pipeline/crossmatching/toa_crossmatch_results.json; deterministic; no
external data. Run:  conda run -n flits python scripts/plot_toa_offset_decomposition.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TOA_RESULTS = ROOT / "pipeline" / "crossmatching" / "toa_crossmatch_results.json"
OUT = ROOT / "figures" / "toa_offset_decomposition.pdf"

# d(offset)/dDM for a shared DM referred to 400 MHz (ms per pc cm^-3). K_DM in
# MHz^2 pc^-1 cm^3 s gives seconds, so scale to ms; offset = CHIME - DSA and
# referring the lower CHIME band to 400 MHz costs less than the DSA band, so the
# derivative is negative (d[CHIME]/dDM=+14.421, d[DSA]/dDM=+23.828 ms/pc cm^-3).
K_DM, F_REF, F_CHIME, F_DSA = 4148.808, 400.0, 600.39, 1405.0
DODDM = -K_DM * (1.0 / F_CHIME**2 - 1.0 / F_DSA**2) * 1.0e3  # = -9.4078 ms per pc cm^-3


def load_rows() -> list[dict]:
    # The figure shows the adopted model-t0 offset (scattering tail deconvolved),
    # which the crossmatch exposes as ``model_corrected_offset_ms``. Note the
    # canonical ``measured_offset_ms`` is the *peak* offset (robust, always
    # available); the model offset is the validation-gated field and is what this
    # decomposition is about, so read it explicitly rather than measured_offset_ms.
    d = json.loads(TOA_RESULTS.read_text())
    rows = []
    for name, r in d.items():
        off = r.get("model_corrected_offset_ms")
        geo = r.get("geometric_delay_ms")
        if off is None or geo is None:
            continue
        rows.append({"burst": name, "offset": float(off), "geo": float(geo)})
    rows.sort(key=lambda x: x["offset"])
    return rows


def make_figure(rows: list[dict]):
    names = [r["burst"] for r in rows]
    off = np.array([r["offset"] for r in rows])
    geo = np.array([r["geo"] for r in rows])
    y = np.arange(len(rows))[::-1]
    gmin, gmax = geo.min(), geo.max()
    c_off, c_geo = "#1f77b4", "#a98261"

    fig, ax = plt.subplots(figsize=(7.4, 5.4))
    ax.axvspan(gmin, gmax, color=c_geo, alpha=0.18, zorder=0, lw=0)
    ax.axvline(0, color="0.35", lw=1.0, zorder=1)
    for yi, g, o in zip(y, geo, off):
        ax.plot([g, o], [yi, yi], color="0.6", lw=1.4, zorder=2, solid_capstyle="round")
    ax.scatter(geo, y, marker="|", s=140, color=c_geo, zorder=3, lw=2.0)
    ax.scatter(off, y, s=46, color=c_off, zorder=4, edgecolor="white", lw=0.6)
    ax.set_yticks(y)
    ax.set_yticklabels(names)
    ax.set_xlabel("CHIME $-$ DSA arrival offset at 400 MHz (ms)")
    ax.set_xlim(-6.6, 5.2)
    ax.margins(y=0.03)
    ax.text(0.015, 0.965, "$\\leftarrow$ CHIME first", transform=ax.transAxes,
            ha="left", va="top", color="0.30", fontsize=7, style="italic")
    ax.text(0.985, 0.965, "DSA first $\\rightarrow$", transform=ax.transAxes,
            ha="right", va="top", color="0.30", fontsize=7, style="italic")

    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    leg = [
        Line2D([0], [0], marker="|", color=c_geo, lw=0, markersize=10,
               markeredgewidth=2, label="geometric delay (baseline)"),
        Line2D([0], [0], marker="o", color=c_off, lw=0, markersize=6,
               markeredgecolor="white", label="measured model offset"),
        Patch(facecolor=c_geo, alpha=0.18, label="geometric range, all 12"),
    ]
    ax.legend(handles=leg, loc="upper right", bbox_to_anchor=(0.995, 0.90),
              frameon=False, fontsize=6.5)
    secax = ax.secondary_xaxis("top", functions=(lambda x: x / DODDM, lambda d: d * DODDM))
    secax.set_xlabel(r"equivalent shared-DM offset (pc cm$^{-3}$)")
    fig.tight_layout()
    return fig


def main() -> None:
    try:
        plt.style.use(["science", "notebook"])
    except Exception:
        pass
    rows = load_rows()
    if len(rows) < 2:
        raise SystemExit(f"need >=2 rows with offset+geometry, got {len(rows)} from {TOA_RESULTS}")
    fig = make_figure(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT)
    print(f"wrote {OUT}  ({len(rows)} bursts; d(offset)/dDM={DODDM:.4f} ms/pc/cm3)")


if __name__ == "__main__":
    main()
