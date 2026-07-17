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

# Display height of the unobserved 0.8-1.31 GHz gap as a fraction of its true
# bandwidth. At true scale the gap eats ~46% of the frequency axis; compressing
# it (hatching still marks it, caption states not-to-scale) returns that space
# to the observed bands.
GAP_COMPRESS = 0.25

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


def _published_scatter_corr(nick: str) -> tuple[float, float] | None:
    """Adopted per-band scattering correction (Delta_scat, ms) for a burst.

    Reads the published values ``scatter_corr_chime_ms`` / ``scatter_corr_dsa_ms``
    from the crossmatch results tracked in the pipeline submodule. These are the
    band-averaged, flux-weighted peak shifts of the fitted scattering kernel
    (intrinsic model arrival = observed profile peak - Delta_scat), computed in
    the ToA analysis; using them here keeps the figure identical to that analysis
    rather than re-deriving from the figure's display NPZs (a different, DM-locked
    fit family whose Delta_scat diverges from the published free-DM values).

    Returns ``None`` when no correction is tracked (e.g. chromatica, no accepted
    joint fit): the burst then keeps the observed-peak anchor.
    """
    from plot_codetection_triptych import FILE_NICK, TOA_RESULTS

    file_nick = FILE_NICK.get(nick, nick)
    rows = json.loads(Path(TOA_RESULTS).read_text())
    row = rows.get(file_nick) or rows.get(file_nick.lower())
    if row is None:
        row = next((v for k, v in rows.items() if k.lower() == file_nick.lower()), None)
    if row is None or "scatter_corr_chime_ms" not in row:
        return None
    return float(row["scatter_corr_chime_ms"]), float(row["scatter_corr_dsa_ms"])


def fit_toa_shift_ms(
    row: dict, *, root: Path, data_root: Path, target_dm: float
) -> dict[str, float]:
    """Per-band shift (band label -> ms) anchoring each band on its adopted
    intrinsic model arrival rather than on the observed (scattered) profile peak.

    The ToA analysis defines the arrival time as the joint-fit model t0 with the
    scattering tail deconvolved out: intrinsic arrival = observed peak minus the
    band-averaged scattering peak shift Delta_scat (see ``_published_scatter_corr``).
    The scattered peak lags the arrival, and by more at CHIME (0.6 GHz) than at
    DSA (1.4 GHz) because tau ~ nu^-alpha; the earlier convention (dominant-component
    t0 referenced to the top of each band) carried a dispersion mismatch and did not
    cancel this differential, so the displayed CHIME-DSA separation disagreed with the
    ToA analysis (most severely for oran: 3.4 ms off, sign flipped).

    ``bands_archival`` first calls ``_align_toa`` with the measured CHIME-minus-DSA
    *peak* offset, which places the two observed peaks at that separation. Adding the
    same DSA scattering correction to both bands is a pure translation that moves the
    DSA intrinsic arrival to t=0; the CHIME intrinsic arrival then lands at
    peak_offset - (Delta_scat_C - Delta_scat_D) = the model-corrected offset. The
    observed peaks stay separated by the measured peak offset (the scattering tail
    remains visible); the intrinsic arrivals are separated by the model offset,
    matching the ToA analysis. Everything is expressed at the adopted display DM,
    consistent with the re-dedispersion applied to the waterfalls.

    Empty for rows without a tracked scattering correction (observed-peak anchor kept).
    """
    corr = _published_scatter_corr(row["nick"])
    if corr is None:
        return {}
    _scatter_corr_chime_ms, scatter_corr_dsa_ms = corr
    return {"CHIME/FRB": scatter_corr_dsa_ms, "DSA-110": scatter_corr_dsa_ms}


def load_row_bands(
    row: dict,
    *,
    root: Path,
    data_root: Path,
    target_dm: float,
    anchor: str = "observed-peak",
    dm_corrections: dict[str, dict[str, float]] | None = None,
):
    """Near-native archival display bands for every burst (fit or no fit).

    ``anchor`` selects the per-band time anchor. The default ``observed-peak``
    keeps the data-only convention (2026-07-14 lock; owner decision recorded in
    figure_review batch 2026-07-17-fig1-model-toa): bands are aligned on the
    measured peak offset with no model-derived translation. ``model-toa``
    additionally applies the published scattering correction from the joint-fit
    kernels via ``fit_toa_shift_ms`` -- gated: those kernels are wave-1
    V1-revoked (RFI-contaminated downsample), so this mode may only feed a
    review batch after V1 clearance, RFI-fixed refits, and an explicit lock
    amendment.
    """
    if anchor not in ("observed-peak", "model-toa"):
        raise ValueError(f"unknown anchor {anchor!r}")
    extra = (
        fit_toa_shift_ms(row, root=root, data_root=data_root, target_dm=target_dm)
        if anchor == "model-toa"
        else {}
    )
    return bands_archival(
        data_root,
        row["nick"],
        factors=DISPLAY_FACTORS,
        pad_scale=DISPLAY_PAD_SCALE,
        pad_cap_ms=DISPLAY_PAD_CAP_MS,
        target_dm=target_dm,
        extra_shift_ms=extra,
        extra_dedisp_pc=(dm_corrections or {}).get(row["nick"].lower()),
    )


def _band_dt_ms(band) -> float:
    t = np.asarray(band.time_ms, float)
    return float(np.median(np.diff(t))) if t.size > 1 else 0.033


def _is_chime(band) -> bool:
    return "CHIME" in band.label


def _gap_display_map(bands, gap_scale: float = GAP_COMPRESS):
    """Real MHz -> display MHz, compressing the inter-band gap to gap_scale
    of its true bandwidth; each observed band keeps its true scale."""
    ordered = sorted(bands, key=lambda band: band.frange[0])
    gap_lo = ordered[0].frange[1]
    gap_hi = ordered[-1].frange[0]
    if gap_hi <= gap_lo:
        return lambda f: np.asarray(f, float)

    def fmap(f):
        f = np.asarray(f, float)
        inside = np.clip(f, gap_lo, gap_hi) - gap_lo
        return f - (1.0 - gap_scale) * inside

    return fmap


def draw_joint_waterfall(ax, bands, *, title: str, fmap=None) -> None:
    """Both bands on one frequency axis (gap compressed); masked channels gray."""
    bands = sorted(bands, key=lambda band: band.frange[0])
    if fmap is None:
        fmap = _gap_display_map(bands)
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
            extent=(
                band.time_ms[0],
                band.time_ms[-1],
                float(fmap(band.frange[0])),
                float(fmap(band.frange[1])),
            ),
            rasterized=True,
        )
    x0 = min(b.time_ms[0] for b in bands)
    x1 = max(b.time_ms[-1] for b in bands)
    for lower, upper in zip(bands[:-1], bands[1:], strict=False):
        if upper.frange[0] > lower.frange[1]:
            ax.add_patch(
                Rectangle(
                    (x0, float(fmap(lower.frange[1]))),
                    x1 - x0,
                    float(fmap(upper.frange[0])) - float(fmap(lower.frange[1])),
                    facecolor="white",
                    edgecolor="0.55",
                    hatch="///",
                    linewidth=0,
                    zorder=0.5,
                )
            )
    ax.set_xlim(x0, x1)
    ax.set_ylim(
        float(fmap(min(b.frange[0] for b in bands))),
        float(fmap(max(b.frange[1] for b in bands))),
    )
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


def draw_spectrum_marginal(ax, bands, gap, *, fmap=None) -> None:
    """Unit-peak time-integrated on-pulse spectrum per band, freq vertical."""
    if fmap is None:
        fmap = _gap_display_map(bands)
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
            fmap(band.freq_mhz),
            lw=0.5,
            color=CHIME_COLOR if _is_chime(band) else DSA_COLOR,
        )
    if gap is not None:
        ax.axhspan(
            float(fmap(gap[0])), float(fmap(gap[1])),
            facecolor="white", edgecolor="0.55", hatch="///",
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
    anchor: str = "observed-peak",
    dm_corrections: dict[str, dict[str, float]] | None = None,
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
    fig = plt.figure(figsize=(7.3, 7.62))
    outer = fig.add_gridspec(
        4, 3, hspace=0.2, wspace=0.14, left=0.065, right=0.995, top=0.978, bottom=0.042
    )
    for index, row in enumerate(rows):
        bands = load_row_bands(
            row,
            root=root,
            data_root=data_root,
            target_dm=adopted_dms[row["nick"].lower()],
            anchor=anchor,
            dm_corrections=dm_corrections,
        )
        fmap = _gap_display_map(bands)
        cell = outer[index // 3, index % 3].subgridspec(
            2, 2, width_ratios=[3.4, 1.0], height_ratios=[1.0, 4.1],
            wspace=0.07, hspace=0.09,
        )
        ax_prof = fig.add_subplot(cell[0, 0])
        ax_wf = fig.add_subplot(cell[1, 0])
        ax_sp = fig.add_subplot(cell[1, 1], sharey=ax_wf)

        draw_joint_waterfall(ax_wf, bands, title="", fmap=fmap)
        ax_prof.set_title(row["tns"], fontsize=7, pad=2)
        draw_profile_strip(ax_prof, bands, ax_wf.get_xlim())
        draw_spectrum_marginal(ax_sp, bands, _band_gap_mhz(bands), fmap=fmap)

        yticks = [500, 700, 1400]
        ax_wf.set_yticks([float(fmap(v)) for v in yticks])
        ax_wf.set_yticklabels([str(v) for v in yticks])
        if index % 3 == 0:
            ax_wf.set_ylabel("Frequency (MHz)", fontsize=7)
        else:
            ax_wf.tick_params(labelleft=False)
        if index // 3 == 3:
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
    parser.add_argument(
        "--anchor",
        choices=("observed-peak", "model-toa"),
        default="observed-peak",
        help=(
            "per-band time anchor; observed-peak is the data-only default "
            "(2026-07-14 lock), model-toa consumes V1-revoked joint-fit "
            "kernels and is gated on a lock amendment"
        ),
    )
    parser.add_argument(
        "--dm-correction-json",
        type=Path,
        default=None,
        help=(
            "JSON {nick: {telescope: delta_dm_pc_cm3}} of audit-derived "
            "applied-DM corrections (scripts/audit_fig1_axes.py) added to the "
            "stem-to-adopted residual dedispersion per product"
        ),
    )
    args = parser.parse_args()
    rows = load_manifest(args.manifest)
    corrections = None
    if args.dm_correction_json:
        corrections = {
            k.lower(): v for k, v in json.loads(args.dm_correction_json.read_text()).items()
        }
    render_grid(
        rows,
        root=ROOT,
        data_root=args.data_root,
        out=args.out,
        dpi=args.dpi,
        dm_catalog=args.dm_catalog,
        anchor=args.anchor,
        dm_corrections=corrections,
    )
    print(f"wrote {args.out.with_suffix('.pdf')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
