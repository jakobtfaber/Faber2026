"""Unified 12-burst co-detection dynamic-spectra gallery (fig:codetection-gallery).

Renders figures/codetection_gallery.{pdf,png,svg}: one cell per co-detected
burst (4 cols x 3 rows, MJD-ascending), each cell stacking the band-summed
profiles (top strip), the DSA-110 waterfall (1.31-1.50 GHz), and the CHIME/FRB
waterfall (0.40-0.80 GHz) on a common relative-time axis.

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
    "dsa": dict(f_lo=1.31125, f_hi=1.49875, dt_ms=32.768e-3, f_factor=24, t_factor=5),
    "chime": dict(f_lo=0.40019, f_hi=0.80019, dt_ms=2.56e-3, f_factor=4, t_factor=64),
}
# Display resolution after block averaging: 163.84 us, 256 channels per band.

WINDOW_MS_DEFAULT = 25.0
# Per-burst display half-windows (ms), widened where scattering tails or
# component spans need it (visual QA, plan Phase 3).
WINDOW_MS_OVERRIDES: dict[str, float] = {}

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

    fig = plt.figure(figsize=(7.3, 8.0))
    outer = fig.add_gridspec(
        3, 4, hspace=0.34, wspace=0.22, left=0.065, right=0.985, top=0.965, bottom=0.055
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

        half_ms = WINDOW_MS_OVERRIDES.get(nick, window_ms)
        for tel, ax in (("dsa", ax_dsa), ("chime", ax_chime)):
            band = BANDS[tel]
            ds, profile = load_band(prods[tel].path, band)
            dt_disp = band["dt_ms"] * band["t_factor"]
            i0, i1 = peak_window(profile, dt_disp, half_ms)
            peak = int(np.nanargmax(profile))
            win = ds[:, i0:i1]
            t0, t1 = (i0 - peak) * dt_disp, (i1 - peak) * dt_disp
            finite = win[np.isfinite(win)]
            vmin, vmax = np.percentile(finite, [CLIP_LO, CLIP_HI])
            ax.imshow(
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
            pw = profile[i0:i1]
            tw = (np.arange(i0, i1) - peak) * dt_disp
            pmax = np.nanmax(pw)
            ax_prof.plot(
                tw,
                pw / (pmax if pmax > 0 else 1.0),
                lw=0.7,
                color="black" if tel == "dsa" else chime_color,
                label="DSA-110" if tel == "dsa" else "CHIME/FRB",
            )
            ax.set_xlim(-half_ms, half_ms)

        ax_prof.set_xlim(-half_ms, half_ms)
        ax_prof.set_ylim(-0.15, 1.1)
        ax_prof.set_xticks([])
        ax_prof.set_yticks([])
        ax_prof.set_title(NICK_TNS[nick], fontsize=7, pad=2)
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
