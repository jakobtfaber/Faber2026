"""Render Figure 1: a 12-panel grid of the joint CHIME/DSA observations.

Every panel is drawn from the archival `_cntr_bpc.npy` products at near-native
display resolution (1024 channels per band; DSA-110 native 32.768 us time
sampling, CHIME/FRB block-averaged to ~33.3 us to match), NOT from the coarse
fit-delivery grids stored in the jointmodel NPZs — those are for the model
audit (triptychs), where data and model must share one grid. Both archival
products span the full ~82 ms burst-centered window, so the shared
CHIME-width display crop never runs off the end of either band.

Each cell carries the band-summed profile strip on top and the time-integrated
on-pulse spectrum marginal on the right; RFI-excised (zapped/flat) channels are
NaN-masked and render in a uniform gray in every panel. No model or residual
values are drawn. Before display averaging, both native-resolution products
are re-dedispersed from their filename-stem DMs to the adopted CHIME
phase-coherence DM in ``analysis/dm-joint-phase-v2/manuscript_dm_catalog.csv``.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

from plot_codetection_gallery import _apply_style, onpulse_span
from plot_codetection_triptych import (
    DATA_ROOT_DEFAULT,
    MANIFEST_DEFAULT,
    ROOT,
    bands_archival,
    load_manifest,
)

OUT_DEFAULT = ROOT / "figures" / "codetection_data_grid"
DM_CATALOG_DEFAULT = ROOT / "analysis" / "dm-joint-phase-v2" / "manuscript_dm_catalog.csv"

# Block-averaging factors of the native archival grids (f_factor, t_factor):
# DSA 6144ch/32.768us -> 512ch at native time (1024ch buries the faintest DSA
# detections below per-pixel noise); CHIME 1024ch/2.56us -> native channels at
# ~33.3us, matching the DSA time resolution across the gap.
DISPLAY_FACTORS = {"dsa": (12, 1), "chime": (1, 13)}

# Display padding around the on-pulse union, as a fraction of the CHIME
# on-pulse width per side (1.5 ms floor). Half a CHIME width keeps the burst
# filling the panel instead of sitting in off-pulse noise; the absolute cap
# stops heavily scattered bursts (CHIME width tens of ms) from inflating the
# off-pulse margins.
DISPLAY_PAD_SCALE = 0.5
DISPLAY_PAD_CAP_MS = 3.0

MASKED_GRAY = "0.85"
# CHIME marginal color: magma(0.55), matching the waterfall colormap family.
CHIME_COLOR = "#b73779"
DSA_COLOR = "black"
CLIP_LO, CLIP_HI = 1.0, 99.5


def _finite_percentile(values: np.ndarray, percentile: float, default: float) -> float:
    finite = np.asarray(values, float)
    finite = finite[np.isfinite(finite)]
    return default if finite.size == 0 else float(np.percentile(finite, percentile))


def load_adopted_dms(path: Path) -> dict[str, float]:
    """Read and strictly validate the 12-burst manuscript DM catalog."""
    with path.open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    if len(rows) != 12:
        raise ValueError(f"DM catalog must contain 12 rows, got {len(rows)}")
    out: dict[str, float] = {}
    for row in rows:
        nick = row["nick"].lower()
        if nick in out:
            raise ValueError(f"duplicate DM catalog nick: {nick}")
        if row.get("adoption") != "chime_primary":
            raise ValueError(f"{nick}: Figure 1 requires chime_primary adoption")
        adopted = float(row["adopted_dm"])
        chime = float(row["chime_dm"])
        if not np.isclose(adopted, chime, rtol=0.0, atol=5e-7):
            raise ValueError(f"{nick}: adopted DM does not equal CHIME DM")
        out[nick] = adopted
    return out


def _block_mean_1d(x: np.ndarray, r: int) -> np.ndarray:
    n = (x.size // r) * r
    return np.nanmean(x[:n].reshape(-1, r), axis=1)


def _standardize(x: np.ndarray) -> np.ndarray:
    x = np.nan_to_num(np.asarray(x, float))
    x = x - x.mean()
    s = x.std()
    return x / s if s > 0 else x


def _register_fit_grid_ms(
    fit_t: np.ndarray, fit_prof: np.ndarray, native_prof: np.ndarray, dt_native_ms: float
) -> float:
    """Native-frame time (ms) of the fit grid's first sample.

    The fit-delivery grid is a crop+downsample of the same archival stream, so
    cross-correlating its band profile against the native archival profile
    (downsampled to the fit dt) registers the two frames exactly, using the
    whole profile rather than a single noisy peak sample.
    """
    dt_fit = float(np.median(np.diff(fit_t)))
    r = int(round(dt_fit / dt_native_ms))
    if r < 1 or abs(dt_fit - r * dt_native_ms) > 0.02 * dt_fit:
        raise ValueError(f"fit dt {dt_fit} is not a multiple of native dt {dt_native_ms}")
    arch = _standardize(_block_mean_1d(native_prof, r))
    fit = _standardize(fit_prof)
    if fit.size > arch.size:
        raise ValueError("fit grid longer than archival window")
    lag = int(np.argmax(np.correlate(arch, fit, mode="valid")))
    return lag * r * dt_native_ms


def fit_toa_shift_ms(
    row: dict, *, root: Path, data_root: Path, target_dm: float
) -> dict[str, float]:
    """Per-band shift (band label -> ms) moving the display anchor from the
    data profile peak to the fitted arrival time from the accepted joint fit:
    the t0 (referenced to the top of each band) of the model component nearest
    the model profile peak, i.e. the dominant component.

    Empty for rows without an accepted joint fit (peak anchor kept).
    """
    npz_rel = row.get("npz")
    if not npz_rel:
        return {}
    npz_path = root / npz_rel
    fit_json = Path(str(npz_path).replace("_jointmodel_", "_joint_fit_")).with_suffix(".json")
    percentiles = json.loads(fit_json.read_text())["percentiles"]
    z = np.load(npz_path, allow_pickle=True)

    from plot_codetection_gallery import BANDS, FILE_NICK, discover_products, load_band

    file_nick = FILE_NICK.get(row["nick"], row["nick"])
    products = discover_products(data_root, file_nick)

    shifts: dict[str, float] = {}
    for band_key, tel, label in (("C", "chime", "CHIME/FRB"), ("D", "dsa", "DSA-110")):
        t0s = [
            float(v["median"])
            for k, v in percentiles.items()
            if re.fullmatch(rf"t0_{band_key}\d*", k)
        ]
        if not t0s:
            raise ValueError(f"{row['nick']}: no t0_{band_key}* in {fit_json.name}")
        fit_t = np.asarray(z[f"time{band_key}"], float)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            fit_prof = np.nansum(np.asarray(z[f"data{band_key}"], float), axis=0)
            model_prof = np.nansum(np.asarray(z[f"model{band_key}"], float), axis=0)
        # Dominant component: t0 nearest the noiseless model profile peak.
        model_peak = float(fit_t[int(np.nanargmax(model_prof))])
        t0 = min(t0s, key=lambda v: abs(v - model_peak))

        # Register against the original archival stream because the fit NPZ
        # was made at the product's filename-stem DM. Compute the display
        # anchor separately after applying the same adopted-DM correction as
        # bands_archival; re-dedispersion changes the band-summed peak.
        f_factor, t_factor_disp = DISPLAY_FACTORS[tel]
        dt_native = BANDS[tel]["dt_ms"]
        band_native = dict(BANDS[tel], f_factor=f_factor, t_factor=1)
        _, native_prof = load_band(products[tel].path, band_native)
        band_disp = dict(BANDS[tel], f_factor=f_factor, t_factor=t_factor_disp)
        residual_dm = float(target_dm - products[tel].dm)
        _, disp_prof = load_band(
            products[tel].path,
            band_disp,
            telescope=tel,
            residual_dm=residual_dm,
        )
        pk_native_ms = int(np.nanargmax(disp_prof)) * t_factor_disp * dt_native

        start_native_ms = _register_fit_grid_ms(fit_t, fit_prof, native_prof, dt_native)
        toa_display_ms = start_native_ms + (t0 - float(fit_t[0])) - pk_native_ms
        shifts[label] = -toa_display_ms
    return shifts


def load_row_bands(row: dict, *, root: Path, data_root: Path, target_dm: float):
    """Near-native archival display bands for every burst (fit or no fit)."""
    return bands_archival(
        data_root,
        row["nick"],
        factors=DISPLAY_FACTORS,
        pad_scale=DISPLAY_PAD_SCALE,
        pad_cap_ms=DISPLAY_PAD_CAP_MS,
        target_dm=target_dm,
        extra_shift_ms=fit_toa_shift_ms(
            row, root=root, data_root=data_root, target_dm=target_dm
        ),
    )


def _band_dt_ms(band) -> float:
    t = np.asarray(band.time_ms, float)
    return float(np.median(np.diff(t))) if t.size > 1 else 0.033


def _is_chime(band) -> bool:
    return "CHIME" in band.label


def draw_joint_waterfall(ax, bands, *, title: str) -> None:
    """Both bands on one to-scale frequency axis; masked channels gray."""
    bands = sorted(bands, key=lambda band: band.frange[0])
    cmap = matplotlib.colormaps["magma"].copy()
    cmap.set_bad(MASKED_GRAY)
    for band in bands:
        data = np.asarray(band.data, float)
        lo = _finite_percentile(data, CLIP_LO, -1.0)
        hi = _finite_percentile(data, CLIP_HI, 1.0)
        if hi <= lo:
            hi = lo + 1.0
        ax.imshow(
            np.ma.masked_invalid(data),
            origin="lower",
            aspect="auto",
            interpolation="nearest",
            cmap=cmap,
            vmin=lo,
            vmax=hi,
            extent=(band.time_ms[0], band.time_ms[-1], *band.frange),
            rasterized=True,
        )
    x0 = min(b.time_ms[0] for b in bands)
    x1 = max(b.time_ms[-1] for b in bands)
    for lower, upper in zip(bands[:-1], bands[1:], strict=False):
        if upper.frange[0] > lower.frange[1]:
            ax.add_patch(
                Rectangle(
                    (x0, lower.frange[1]),
                    x1 - x0,
                    upper.frange[0] - lower.frange[1],
                    facecolor="white",
                    edgecolor="0.55",
                    hatch="///",
                    linewidth=0,
                    zorder=0.5,
                )
            )
    ax.set_xlim(x0, x1)
    ax.set_ylim(min(b.frange[0] for b in bands), max(b.frange[1] for b in bands))
    ax.set_title(title, fontsize=7, pad=2)


def draw_profile_strip(ax, bands, xlim) -> None:
    """Unit-peak band-summed profiles (DSA black, CHIME blue)."""
    for band in bands:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            prof = np.nansum(np.asarray(band.data, float), axis=0)
        pmax = np.nanmax(prof)
        ax.plot(
            band.time_ms,
            prof / (pmax if pmax > 0 else 1.0),
            lw=0.7,
            color=CHIME_COLOR if _is_chime(band) else DSA_COLOR,
            label=band.label,
        )
    ax.set_xlim(*xlim)
    ax.set_ylim(-0.15, 1.1)
    ax.set_xticks([])
    ax.set_yticks([])


def draw_spectrum_marginal(ax, bands, gap) -> None:
    """Unit-peak time-integrated on-pulse spectrum per band, freq vertical."""
    for band in bands:
        data = np.asarray(band.data, float)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            prof = np.nansum(data, axis=0)
            lo, hi, _ = onpulse_span(np.nan_to_num(prof), _band_dt_ms(band))
            spec = np.nanmean(data[:, lo : hi + 1], axis=1)
        smax = np.nanmax(spec)
        if np.isfinite(smax) and smax > 0:
            spec = spec / smax
        ax.plot(
            spec,
            band.freq_mhz,
            lw=0.5,
            color=CHIME_COLOR if _is_chime(band) else DSA_COLOR,
        )
    if gap is not None:
        ax.axhspan(
            gap[0], gap[1], facecolor="white", edgecolor="0.55", hatch="///",
            lw=0, zorder=0.5,
        )
    ax.set_xlim(-0.08, 1.15)
    ax.set_xticks([])
    ax.tick_params(labelleft=False)


def _band_gap_mhz(bands) -> tuple[float, float] | None:
    ordered = sorted(bands, key=lambda band: band.frange[0])
    for lower, upper in zip(ordered[:-1], ordered[1:], strict=False):
        if upper.frange[0] > lower.frange[1]:
            return lower.frange[1], upper.frange[0]
    return None


def render_grid(
    rows: list[dict],
    *,
    root: Path,
    data_root: Path,
    out: Path,
    dpi: int,
    dm_catalog: Path = DM_CATALOG_DEFAULT,
) -> None:
    adopted_dms = load_adopted_dms(dm_catalog)
    roster = {row["nick"].lower() for row in rows}
    if roster != set(adopted_dms):
        raise ValueError("manifest and adopted-DM catalog rosters differ")
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
    # At \textwidth the typeset height plus the combined adopted-DM/fitted-TOA
    # caption must fit on one AASTeX float page.
    fig = plt.figure(figsize=(7.3, 7.45))
    outer = fig.add_gridspec(
        3, 4, hspace=0.18, wspace=0.16, left=0.065, right=0.995, top=0.97, bottom=0.045
    )
    for index, row in enumerate(rows):
        bands = load_row_bands(
            row,
            root=root,
            data_root=data_root,
            target_dm=adopted_dms[row["nick"].lower()],
        )
        cell = outer[index // 4, index % 4].subgridspec(
            2, 2, width_ratios=[3.4, 1.0], height_ratios=[1.0, 3.6],
            wspace=0.07, hspace=0.09,
        )
        ax_prof = fig.add_subplot(cell[0, 0])
        ax_wf = fig.add_subplot(cell[1, 0])
        ax_sp = fig.add_subplot(cell[1, 1], sharey=ax_wf)

        draw_joint_waterfall(ax_wf, bands, title="")
        ax_prof.set_title(row["tns"], fontsize=7, pad=2)
        draw_profile_strip(ax_prof, bands, ax_wf.get_xlim())
        draw_spectrum_marginal(ax_sp, bands, _band_gap_mhz(bands))

        ax_wf.set_yticks([600, 1000, 1400])
        if index % 4 == 0:
            ax_wf.set_ylabel("Frequency (MHz)", fontsize=7)
        else:
            ax_wf.tick_params(labelleft=False)
        if index // 4 == 2:
            ax_wf.set_xlabel("Time (ms)", fontsize=7)
        if index == 0:
            ax_prof.legend(
                fontsize=5, frameon=False, loc="upper right", handlelength=1.0,
                borderaxespad=0.1, labelspacing=0.2,
            )
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out.with_suffix(".png"), dpi=dpi)
    fig.savefig(out.with_suffix(".pdf"), dpi=dpi)
    fig.savefig(out.with_suffix(".svg"), dpi=dpi)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_DEFAULT)
    parser.add_argument("--data-root", type=Path, default=DATA_ROOT_DEFAULT)
    parser.add_argument("--out", type=Path, default=OUT_DEFAULT)
    parser.add_argument("--dm-catalog", type=Path, default=DM_CATALOG_DEFAULT)
    parser.add_argument("--dpi", type=int, default=600)
    args = parser.parse_args()
    rows = load_manifest(args.manifest)
    render_grid(
        rows,
        root=ROOT,
        data_root=args.data_root,
        out=args.out,
        dpi=args.dpi,
        dm_catalog=args.dm_catalog,
    )
    print(f"wrote {args.out.with_suffix('.pdf')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
