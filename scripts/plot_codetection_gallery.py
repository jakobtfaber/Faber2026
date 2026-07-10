"""Unified 12-burst co-detection dynamic-spectra gallery (fig:codetection-gallery).

Renders figures/codetection_gallery.{pdf,png,svg}: one cell per co-detected
burst (4 cols x 3 rows, MJD-ascending). Each cell mirrors the joint-fit
co-detection figures (pipeline/flits/batch/codetection_plots.py): both bands on
ONE frequency axis drawn to scale (CHIME/FRB 0.40-0.80, DSA-110 1.31-1.50 GHz)
with the unobserved 0.80-1.31 GHz gap hatched, a band-summed profile strip on
top, and a time-integrated on-pulse spectrum marginal on the right. The time
window is adaptive per burst (padded union of the two bands' on-pulse spans),
so the burst fills the panel instead of sitting in ~50 ms of off-pulse noise.

Data contract (docs/rse/specs/research-unified-12burst-figure.md):
  ~/Data/Faber2026/dsa110/DSA_bursts/{nick}_{tel}_I_{DMstem}_{N}b_cntr_bpc.npy
  DSA (6144, 2500) @ 32.768 us; CHIME (1024, 32000) @ 2.56 us; both are
  ~81.9 ms burst-centered windows, stored frequency-DESCENDING
  (pipeline/scattering/configs/telescopes.yaml) and flipped to ascending here.

DM convention: each panel is displayed at the instrument-optimized DM baked
into the product (encoded in the filename stem); no re-dedispersion is applied.
The caption states this. Times are relative to each band's profile peak (the
products carry no shared absolute time zero).

No fit/model products are read or drawn (CONTEXT.md trust reset: raw
observational inputs only).

Run: conda run -n flits python scripts/plot_codetection_gallery.py
"""

from __future__ import annotations

import argparse
import re
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT / "pipeline"))

DATA_ROOT = Path.home() / "Data/Faber2026/dsa110/DSA_bursts"
OUT_DIR = ROOT / "figures"

# Parity-tested against pipeline/scattering/scat_analysis/burst_metadata.py
# (_FALLBACK_TNS, which carries the verified mahi 20240119A -> 20240122A
# correction) by tests/test_codetection_gallery.py.
NICK_TNS = {
    "zach": "FRB 20220207C",
    "whitney": "FRB 20220310F",
    "oran": "FRB 20220506D",
    "isha": "FRB 20221113A",
    "wilhelm": "FRB 20221203A",
    "phineas": "FRB 20230307A",
    "freya": "FRB 20230325A",
    "johndoeii": "FRB 20230814B",
    "hamilton": "FRB 20230913A",
    "mahi": "FRB 20240122A",
    "chromatica": "FRB 20240203A",
    "casey": "FRB 20240229A",
}

# bursts.yaml keys are lowercase; data filenames use this casing.
FILE_NICK = {"johndoeii": "johndoeII"}

# Band geometry: pipeline/scattering/configs/telescopes.yaml (GHz, ms).
# Both products are stored frequency-descending; flipped to ascending on load.
BANDS = {
    "dsa": dict(f_lo=1.31125, f_hi=1.49875, dt_ms=32.768e-3, f_factor=12, t_factor=1),
    "chime": dict(f_lo=0.40019, f_hi=0.80019, dt_ms=2.56e-3, f_factor=2, t_factor=13),
}
# Display resolution after block averaging: ~33 us and 512 channels per band
# (DSA native time; CHIME averaged to match), sized for the adaptive tight
# windows -- the previous 163.84 us / 256-channel grid left only ~30 columns
# across a narrow burst.

WINDOW_MS_DEFAULT = 25.0  # hard clamp on the adaptive half-window
# Per-burst symmetric half-window overrides (ms): escape hatch when the
# adaptive on-pulse window mis-sizes a burst (visual QA).
WINDOW_MS_OVERRIDES: dict[str, float] = {}

# Unobserved band between the CHIME top and DSA bottom edges, hatched like the
# joint-fit figures (flits/batch/codetection_plots._hatch_rect).
BAND_GAP_GHZ = (BANDS["chime"]["f_hi"], BANDS["dsa"]["f_lo"])

# Robust display clip percentiles (waterfalls).
CLIP_LO, CLIP_HI = 1.0, 99.5


@dataclass
class Product:
    path: Path
    dm: float


def block_mean(arr: np.ndarray, f_factor: int, t_factor: int) -> np.ndarray:
    """Block-average by integer factors, trimming any ragged edge.

    NaN-aware: a block keeps the mean of its finite samples, so a fully-dead
    (NaN-filled) channel block stays NaN and renders as masked.
    """
    nf = (arr.shape[0] // f_factor) * f_factor
    nt = (arr.shape[1] // t_factor) * t_factor
    a = arr[:nf, :nt].reshape(nf // f_factor, f_factor, nt // t_factor, t_factor)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        return np.nanmean(a, axis=(1, 3))


def dead_channel_mask(arr: np.ndarray) -> np.ndarray:
    """Channels with zero or non-finite variance (zapped/flat) -> True."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        std = np.nanstd(arr, axis=1)
    return (std == 0.0) | ~np.isfinite(std)


def peak_window(profile: np.ndarray, dt_ms: float, window_ms: float) -> tuple[int, int]:
    """[i0, i1) slice of +-window_ms around the profile peak, edge-clipped."""
    peak = int(np.nanargmax(profile))
    half = int(round(window_ms / dt_ms))
    return max(0, peak - half), min(profile.size, peak + half + 1)


def onpulse_span(
    profile: np.ndarray,
    dt_ms: float,
    thr_frac: float = 0.08,
    smooth_ms: float = 1.0,
    gap_ms: float = 2.0,
) -> tuple[int, int, int]:
    """(i_lo, i_hi, i_peak) above-threshold on-pulse span around the peak.

    The threshold is the larger of thr_frac x peak and off-pulse median + 4
    sigma (outer-quartile samples), evaluated on a boxcar-smoothed profile, so
    low-S/N noise never inflates the span. Above-threshold runs separated by
    less than gap_ms are merged, keeping multi-component bursts in one span.
    """
    k = max(1, int(round(smooth_ms / dt_ms)))
    sm = np.convolve(np.nan_to_num(profile, nan=0.0), np.ones(k) / k, mode="same")
    n = sm.size
    off = np.concatenate([sm[: n // 4], sm[-n // 4 :]])
    thr = max(thr_frac * float(sm.max()), float(np.median(off) + 4.0 * np.std(off)))
    pk = int(np.argmax(sm))
    on = np.flatnonzero(sm > thr)
    g = max(1, int(round(gap_ms / dt_ms)))
    lo = hi = pk
    for i in on[on < pk][::-1]:
        if lo - i <= g:
            lo = int(i)
        else:
            break
    for i in on[on > pk]:
        if i - hi <= g:
            hi = int(i)
        else:
            break
    return lo, hi, pk


def discover_products(data_root: Path, nick: str) -> dict[str, Product]:
    """Locate the per-telescope _cntr_bpc products and parse their DM stems."""
    out = {}
    for tel in ("dsa", "chime"):
        hits = sorted(Path(data_root).glob(f"{nick}_{tel}_I_*_cntr_bpc.npy"))
        if len(hits) != 1:
            raise FileNotFoundError(
                f"{nick}/{tel}: expected exactly 1 product, found {len(hits)} "
                f"in {data_root}"
            )
        m = re.match(rf"{re.escape(nick)}_{tel}_I_(\d+)_(\d+)_\d+b", hits[0].name)
        if m is None:
            raise ValueError(f"unparseable DM stem: {hits[0].name}")
        out[tel] = Product(hits[0], float(f"{m.group(1)}.{m.group(2)}"))
    return out


def _apply_style() -> None:
    """flits.plotting.use_flits_style() (the repo standard), with a fallback
    that replicates its rcParams (pipeline/flits/plotting.py:50-55) if the
    flits import chain (scattering.burstfit) is unavailable."""
    import matplotlib.pyplot as plt

    try:
        from flits.plotting import use_flits_style  # applies on import too

        use_flits_style()
        return
    except Exception:
        pass
    try:
        import scienceplots  # noqa: F401

        plt.style.use(["science", "notebook"])
    except Exception:
        import matplotlib

        rc = ROOT / "pipeline" / "matplotlibrc"
        if rc.exists():
            matplotlib.rc_file(str(rc))
    plt.rcParams["text.usetex"] = False
    plt.rcParams["font.family"] = "serif"
    plt.rcParams["font.serif"] = ["cmr10"]
    plt.rcParams["mathtext.fontset"] = "cm"
    plt.rcParams["axes.formatter.use_mathtext"] = True
    plt.rcParams["axes.unicode_minus"] = False


def load_band(path: Path, band: dict) -> tuple[np.ndarray, np.ndarray]:
    """Load one product -> (windowless waterfall [ascending freq, display res],
    band profile). Baseline: per-channel median over the outer quartiles."""
    raw = np.load(path, mmap_mode="r")
    arr = np.flipud(np.array(raw, dtype=np.float32, copy=True))  # ascending freq
    dead = dead_channel_mask(arr)
    arr[dead] = np.nan
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
    from matplotlib import colormaps

    import yaml

    _apply_style()
    plt.rcParams.update(
        {
            "font.size": 7,
            "axes.labelsize": 7,
            "xtick.labelsize": 6,
            "ytick.labelsize": 6,
            "axes.linewidth": 0.6,
            "xtick.direction": "in",
            "ytick.direction": "in",
        }
    )

    with open(ROOT / "pipeline" / "configs" / "bursts.yaml") as fh:
        catalog = yaml.safe_load(fh)["bursts"]
    order = sorted(catalog, key=lambda k: catalog[k]["mjd"])
    if set(order) != set(NICK_TNS):
        raise RuntimeError("bursts.yaml sample does not match NICK_TNS roster")

    cmap = colormaps["magma"].copy()
    cmap.set_bad("0.88")
    chime_color = "#4477aa"

    from matplotlib.patches import Rectangle

    def hatch_gap(ax, x0, x1):
        ax.add_patch(
            Rectangle(
                (x0, BAND_GAP_GHZ[0]), x1 - x0, BAND_GAP_GHZ[1] - BAND_GAP_GHZ[0],
                facecolor="white", edgecolor="0.55", hatch="///", lw=0.0, zorder=0.5,
            )
        )

    fig = plt.figure(figsize=(7.3, 9.2))
    outer = fig.add_gridspec(
        3, 4, hspace=0.30, wspace=0.30, left=0.07, right=0.99, top=0.97, bottom=0.045
    )

    rendered = []
    for idx, nick in enumerate(order):
        fnick = FILE_NICK.get(nick, nick)
        prods = discover_products(data_root, fnick)
        cell = outer[idx // 4, idx % 4].subgridspec(
            2, 2, width_ratios=[3.4, 1.0], height_ratios=[1.0, 3.6],
            wspace=0.07, hspace=0.09,
        )
        ax_prof = fig.add_subplot(cell[0, 0])
        ax_wf = fig.add_subplot(cell[1, 0])
        ax_sp = fig.add_subplot(cell[1, 1], sharey=ax_wf)

        loaded = {}
        for tel in ("dsa", "chime"):
            band = BANDS[tel]
            ds, profile = load_band(prods[tel].path, band)
            dt_disp = band["dt_ms"] * band["t_factor"]
            lo, hi, pk = onpulse_span(profile, dt_disp)
            loaded[tel] = dict(ds=ds, profile=profile, dt=dt_disp, lo=lo, hi=hi, pk=pk)

        # Padded union of the two bands' on-pulse spans, each relative to its
        # own profile peak (the products carry no shared absolute time zero).
        t_lo = min((d["lo"] - d["pk"]) * d["dt"] for d in loaded.values())
        t_hi = max((d["hi"] - d["pk"]) * d["dt"] for d in loaded.values())
        pad = min(max(1.5, 0.35 * (t_hi - t_lo)), 8.0)
        w_lo = max(t_lo - pad, -window_ms)
        w_hi = min(t_hi + pad, window_ms)
        if nick in WINDOW_MS_OVERRIDES:
            w_lo, w_hi = -WINDOW_MS_OVERRIDES[nick], WINDOW_MS_OVERRIDES[nick]

        for tel in ("dsa", "chime"):
            band, d = BANDS[tel], loaded[tel]
            ds, profile, dt_disp, pk = d["ds"], d["profile"], d["dt"], d["pk"]
            i0 = max(0, pk + int(np.floor(w_lo / dt_disp)))
            i1 = min(profile.size, pk + int(np.ceil(w_hi / dt_disp)) + 1)
            win = ds[:, i0:i1]
            t0, t1 = (i0 - pk) * dt_disp, (i1 - pk) * dt_disp
            finite = win[np.isfinite(win)]
            vmin, vmax = np.percentile(finite, [CLIP_LO, CLIP_HI])
            ax_wf.imshow(
                np.ma.masked_invalid(win),
                origin="lower",
                aspect="auto",
                cmap=cmap,
                vmin=vmin,
                vmax=vmax,
                extent=[t0, t1, band["f_lo"], band["f_hi"]],
                rasterized=True,
                interpolation="nearest",
            )
            color = "black" if tel == "dsa" else chime_color
            pw = profile[i0:i1]
            tw = (np.arange(i0, i1) - pk) * dt_disp
            pmax = np.nanmax(pw)
            ax_prof.plot(
                tw, pw / (pmax if pmax > 0 else 1.0), lw=0.7, color=color,
                label="DSA-110" if tel == "dsa" else "CHIME/FRB",
            )
            # Time-integrated spectrum over the on-pulse span, unit-peak per
            # band (bands are separately bandpass-corrected; absolute levels
            # are not comparable across the gap).
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                spec = np.nanmean(ds[:, d["lo"] : d["hi"] + 1], axis=1)
            smax = np.nanmax(spec)
            if smax > 0:
                spec = spec / smax
            f_centers = band["f_lo"] + (np.arange(ds.shape[0]) + 0.5) * (
                band["f_hi"] - band["f_lo"]
            ) / ds.shape[0]
            ax_sp.plot(spec, f_centers, lw=0.5, color=color)

        hatch_gap(ax_wf, w_lo, w_hi)
        ax_sp.axhspan(
            *BAND_GAP_GHZ, facecolor="white", edgecolor="0.55", hatch="///",
            lw=0, zorder=0.5,
        )
        if idx == 0:
            ax_wf.text(
                0.5 * (w_lo + w_hi), 0.5 * sum(BAND_GAP_GHZ), "no coverage",
                ha="center", va="center", fontsize=5.5, style="italic",
                color="0.4", zorder=1,
            )

        ax_wf.set_xlim(w_lo, w_hi)
        ax_wf.set_ylim(BANDS["chime"]["f_lo"], BANDS["dsa"]["f_hi"])
        ax_wf.set_yticks([0.6, 1.0, 1.4])
        ax_sp.set_xlim(-0.08, 1.15)
        ax_sp.set_xticks([])
        ax_sp.tick_params(labelleft=False)
        ax_prof.set_xlim(w_lo, w_hi)
        ax_prof.set_ylim(-0.15, 1.1)
        ax_prof.set_xticks([])
        ax_prof.set_yticks([])
        ax_prof.set_title(NICK_TNS[nick], fontsize=7, pad=2)
        if idx % 4 == 0:
            ax_wf.set_ylabel("Frequency (GHz)", fontsize=7)
        else:
            ax_wf.tick_params(labelleft=False)
        if idx // 4 == 2:
            ax_wf.set_xlabel("Time (ms)", fontsize=7)
        if idx == 0:
            ax_prof.legend(
                fontsize=5, frameon=False, loc="upper right", handlelength=1.0,
                borderaxespad=0.1, labelspacing=0.2,
            )
        rendered.append(nick)

    out_dir.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "svg", "png"):
        fig.savefig(out_dir / f"codetection_gallery.{ext}", dpi=300)
    plt.close(fig)
    return rendered


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-root", type=Path, default=DATA_ROOT)
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    ap.add_argument("--window-ms", type=float, default=WINDOW_MS_DEFAULT)
    args = ap.parse_args()
    rendered = render(args.data_root, args.out_dir, args.window_ms)
    print(f"rendered {len(rendered)} bursts (MJD order): {' '.join(rendered)}")
    if len(rendered) != 12:
        sys.exit("expected 12 bursts")


if __name__ == "__main__":
    main()
