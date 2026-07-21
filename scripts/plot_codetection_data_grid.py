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
The time axes retain the measured-profile convention supplied by
``bands_archival``: DSA-110's observed peak is at zero and CHIME/FRB is placed
with the recorded measured peak offset. No scattering-model correction or
joint-fit artifact participates in Figure 1.
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
    CHIME_FULL_ROOT_DEFAULT,
    DSA_FULL_ROOT_DEFAULT,
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


def load_row_bands(
    row: dict,
    *,
    root: Path,
    chime_full_root: Path,
    dsa_full_root: Path,
    target_dm: float,
    dm_corrections: dict[str, dict[str, float]] | None = None,
):
    """Near-native archival bands, retaining the measured-profile peak anchor.

    ``dm_corrections`` maps burst nick -> telescope -> extra dedispersion
    (pc cm^-3) applied on top of the stem-DM-to-adopted-DM shift. It exists to
    correct audit-established archival filename-stem DM misstatements (the
    stem disagrees with the DM actually applied to the stored product); it is
    not a model correction and does not touch the time-axis convention.
    """
    extra = (dm_corrections or {}).get(row["nick"].lower())
    return bands_archival(
        chime_full_root,
        dsa_full_root,
        row["nick"],
        factors=DISPLAY_FACTORS,
        pad_scale=DISPLAY_PAD_SCALE,
        pad_cap_ms=DISPLAY_PAD_CAP_MS,
        target_dm=target_dm,
        extra_shift_ms=None,
        extra_dedisp_pc=extra,
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
    chime_full_root: Path,
    dsa_full_root: Path,
    out: Path,
    dpi: int,
    dm_catalog: Path = DM_CATALOG_DEFAULT,
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
            chime_full_root=chime_full_root,
            dsa_full_root=dsa_full_root,
            target_dm=adopted_dms[row["nick"].lower()],
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
    path_arg = lambda value: Path(value).expanduser()  # noqa: E731
    parser.add_argument(
        "--chime-full-root", type=path_arg, default=CHIME_FULL_ROOT_DEFAULT
    )
    parser.add_argument("--dsa-full-root", type=path_arg, default=DSA_FULL_ROOT_DEFAULT)
    parser.add_argument("--out", type=Path, default=OUT_DEFAULT)
    parser.add_argument("--dm-catalog", type=Path, default=DM_CATALOG_DEFAULT)
    parser.add_argument("--dpi", type=int, default=600)
    parser.add_argument(
        "--dm-correction-json",
        type=Path,
        help="JSON {nick: {telescope: extra pc cm^-3}} of audit-established "
        "stem-DM misstatement corrections applied before display averaging",
    )
    args = parser.parse_args()
    rows = load_manifest(args.manifest)
    dm_corrections = None
    if args.dm_correction_json:
        raw = json.loads(args.dm_correction_json.read_text())
        dm_corrections = {
            nick.lower(): {tel.lower(): float(val) for tel, val in per.items()}
            for nick, per in raw.items()
        }
    render_grid(
        rows,
        root=ROOT,
        chime_full_root=args.chime_full_root,
        dsa_full_root=args.dsa_full_root,
        out=args.out,
        dpi=args.dpi,
        dm_catalog=args.dm_catalog,
        dm_corrections=dm_corrections,
    )
    print(f"wrote {args.out.with_suffix('.pdf')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
