"""Co-detection gallery variant: each burst re-dedispersed to ONE joint
arrival-regression DM across BOTH bands (diagnostic; the manuscript
fig:codetection-gallery stays raw-data-only per the trust reset).

Same layout/data contract as plot_codetection_gallery.py. The stored products
are per-instrument dedispersed (file-stem DM; CHIME and DSA stems differ for
the same burst), so a per-band residual shift leaves the two bands at
DIFFERENT absolute DMs -- the v1 of this figure did exactly that. Here each
band's absolute arrival DM is stem + battery residual (the residual is defined
on the stored waterfall, so this is convention-free even though the battery's
dm_ref bookkeeping differs for CHIME rows); the per-burst joint DM is the
inverse-variance weighted mean over the constrained bands, and each band is
shifted by (DM_joint - its own stem). Cross-band consistency where both bands
constrain: chromatica 272.656 vs 272.662, whitney 462.193 vs 462.190. Bursts
with no constrained band (mahi) are shown as stored and flagged.

Run: conda run -n flits python scripts/plot_codetection_gallery_arrivaldm.py
"""

from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path

import numpy as np

from plot_codetection_gallery import (
    BANDS,
    CLIP_HI,
    CLIP_LO,
    DATA_ROOT,
    FILE_NICK,
    NICK_TNS,
    ROOT,
    WINDOW_MS_DEFAULT,
    _apply_style,
    block_mean,
    dead_channel_mask,
    discover_products,
    peak_window,
)

BATTERY_JSON = ROOT / "pipeline/results/dm_campaign/battery/battery_results.json"
OUT_DIR = ROOT / "figures/prototypes/codetection"


def load_residuals(path: Path) -> dict[tuple[str, str], dict]:
    recs = json.loads(path.read_text())
    return {(r["burst"], r["telescope"]): r for r in recs
            if r["adapter"] == "arrival_regression"}


def joint_dm(residuals, fnick, prods):
    """One DM per burst: inverse-variance weighted mean of the constrained
    bands' absolute arrival DMs (stem + residual). Returns
    (dm, sigma, bands_used) or (None, None, []) when neither band constrains."""
    vals = []
    for tel in ("chime", "dsa"):
        r = residuals[(fnick, tel)]
        if r["residual"] is not None:
            vals.append((prods[tel].dm + r["residual"], r["sigma"], tel))
    if not vals:
        return None, None, []
    w = np.array([1.0 / s**2 for _, s, _ in vals])
    dm = float(np.sum(w * [v for v, _, _ in vals]) / w.sum())
    return dm, float(w.sum() ** -0.5), [t for _, _, t in vals]


def load_band_at_dm(path: Path, band: dict, tel: str, residual_dm: float):
    """plot_codetection_gallery.load_band with an extra full-resolution
    residual-DM shift applied before display downsampling."""
    from dispersion.dm_power_analysis import (
        _freq_grid_mhz,
        shift_waterfall_residual_dm,
    )

    raw = np.load(path, mmap_mode="r")
    arr = np.flipud(np.array(raw, dtype=np.float32, copy=True))  # ascending freq
    dead = dead_channel_mask(arr)
    arr[dead] = np.nan
    if residual_dm:
        freq = _freq_grid_mhz(tel, arr.shape[0])
        arr = shift_waterfall_residual_dm(arr, freq, band["dt_ms"] * 1e-3,
                                          float(residual_dm))
    ds = block_mean(arr, band["f_factor"], band["t_factor"])
    nt = ds.shape[1]
    off = np.concatenate([ds[:, : nt // 4], ds[:, -nt // 4 :]], axis=1)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        baseline = np.nanmedian(off, axis=1, keepdims=True)
        ds = ds - baseline
        profile = np.nansum(ds, axis=0)
    return ds, profile


def render(data_root: Path, out_dir: Path, window_ms: float) -> list[str]:
    import matplotlib.pyplot as plt
    import yaml
    from matplotlib import colormaps

    _apply_style()
    plt.rcParams.update({
        "font.size": 7, "axes.labelsize": 7, "xtick.labelsize": 6,
        "ytick.labelsize": 6, "axes.linewidth": 0.6,
        "xtick.direction": "in", "ytick.direction": "in",
    })

    with open(ROOT / "pipeline" / "configs" / "bursts.yaml") as fh:
        catalog = yaml.safe_load(fh)["bursts"]
    order = sorted(catalog, key=lambda k: catalog[k]["mjd"])
    residuals = load_residuals(BATTERY_JSON)

    cmap = colormaps["magma"].copy()
    cmap.set_bad("0.88")
    chime_color = "#4477aa"

    fig = plt.figure(figsize=(7.3, 8.4))
    outer = fig.add_gridspec(
        3, 4, hspace=0.34, wspace=0.22, left=0.065, right=0.985, top=0.94, bottom=0.05
    )

    rendered = []
    for idx, nick in enumerate(order):
        fnick = FILE_NICK.get(nick, nick)
        prods = discover_products(data_root, fnick)
        cell = outer[idx // 4, idx % 4].subgridspec(
            3, 1, height_ratios=[1.0, 2.2, 2.2], hspace=0.10
        )
        ax_prof = fig.add_subplot(cell[0])
        ax_dsa = fig.add_subplot(cell[1])
        ax_chime = fig.add_subplot(cell[2])

        dm_j, dm_j_sig, bands_used = joint_dm(residuals, fnick, prods)
        for tel, ax in (("dsa", ax_dsa), ("chime", ax_chime)):
            band = BANDS[tel]
            ddm = None if dm_j is None else dm_j - prods[tel].dm
            ds, profile = load_band_at_dm(prods[tel].path, band, tel, ddm or 0.0)
            dt_disp = band["dt_ms"] * band["t_factor"]
            i0, i1 = peak_window(profile, dt_disp, window_ms)
            peak = int(np.nanargmax(profile))
            win = ds[:, i0:i1]
            t0, t1 = (i0 - peak) * dt_disp, (i1 - peak) * dt_disp
            finite = win[np.isfinite(win)]
            vmin, vmax = np.percentile(finite, [CLIP_LO, CLIP_HI])
            ax.imshow(
                np.ma.masked_invalid(win), origin="lower", aspect="auto",
                cmap=cmap, vmin=vmin, vmax=vmax,
                extent=[t0, t1, band["f_lo"], band["f_hi"]],
                rasterized=True, interpolation="nearest",
            )
            if ddm is None:
                note, color = "as stored (no arrival DM)", "#ffb3a7"
            else:
                note, color = f"shift {ddm:+.3f} from stem {prods[tel].dm:.3f}", "white"
            ax.text(0.03, 0.95, note, transform=ax.transAxes, fontsize=5,
                    va="top", color=color,
                    bbox=dict(facecolor="black", alpha=0.55, pad=1.2,
                              edgecolor="none"))
            pw = profile[i0:i1]
            tw = (np.arange(i0, i1) - peak) * dt_disp
            pmax = np.nanmax(pw)
            ax_prof.plot(
                tw, pw / (pmax if pmax > 0 else 1.0), lw=0.7,
                color="black" if tel == "dsa" else chime_color,
                label="DSA-110" if tel == "dsa" else "CHIME/FRB",
            )
            ax.set_xlim(-window_ms, window_ms)

        ax_prof.set_xlim(-window_ms, window_ms)
        ax_prof.set_ylim(-0.15, 1.1)
        ax_prof.set_xticks([])
        ax_prof.set_yticks([])
        ax_prof.set_title(NICK_TNS[nick], fontsize=7, pad=2)
        if dm_j is not None:
            src = "+".join(t.upper().replace("CHIME", "C").replace("DSA", "D")
                           for t in bands_used)
            ax_prof.text(0.02, 0.88, f"{dm_j:.3f}$\\pm${dm_j_sig:.3f} {src}",
                         transform=ax_prof.transAxes, fontsize=4.8, va="top",
                         color="0.35")
        ax_dsa.set_yticks([1.35, 1.45])
        ax_chime.set_yticks([0.5, 0.7])
        ax_dsa.set_xticklabels([])
        if idx % 4 == 0:
            ax_chime.set_ylabel("Frequency (GHz)", fontsize=7)
            ax_chime.yaxis.set_label_coords(-0.24, 1.05)
        if idx // 4 == 2:
            ax_chime.set_xlabel("Time (ms)", fontsize=7)
        if idx == 0:
            ax_prof.legend(
                fontsize=5, frameon=False, loc="upper right", handlelength=1.0,
                borderaxespad=0.1, labelspacing=0.2,
            )
        rendered.append(nick)

    fig.suptitle(
        "Co-detections at ONE joint arrival-regression DM per burst (both bands): "
        "DM = inverse-variance mean of constrained bands' (stem + $\\Delta$DM); "
        "each band shifted by DM $-$ its own stored stem DM; red = no arrival DM, as stored",
        fontsize=7.5,
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / "codetection_gallery_arrival_dm.png", dpi=300)
    plt.close(fig)
    return rendered


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-root", type=Path, default=DATA_ROOT)
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    ap.add_argument("--window-ms", type=float, default=WINDOW_MS_DEFAULT)
    args = ap.parse_args()
    rendered = render(args.data_root, args.out_dir, args.window_ms)
    print(f"rendered {len(rendered)} bursts: {' '.join(rendered)}")


if __name__ == "__main__":
    main()
