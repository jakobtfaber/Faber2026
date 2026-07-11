"""Fig. 1 producer: per-burst data | model | residual triptychs.

Renders figures/codetection_triptych/{nick}_triptych.{pdf,png,svg} from the
jointmodel NPZ roster in scripts/jointmodel_triptych_manifest.yaml.

Resolution contract: DATA come from the archival `_cntr_bpc.npy` products at
the gallery display grid (DSA native 32.768 µs / CHIME ×13 ≈ 33 µs; 512
channels per band). The jointmodel NPZ supplies the 2-D model on the coarse
fit grid; that model is interpolated onto the archival display grid before
plotting. Residuals are (data − model) / σ on the same fine grid.
`show_model_on_data=False` — no overlays on the data waterfall.

Time window: observed on-pulse union of both bands, padded on each side by
P = max(W_CHIME, 1.5 ms).

Run: conda run -n flits python scripts/plot_codetection_triptych.py
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import yaml
from scipy.interpolate import RegularGridInterpolator

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
sys.path.insert(0, str(ROOT / "scripts"))

from flits.batch.codetection_data import (  # noqa: E402
    chime_toa_shift_ms,
    toa_offset_ms,
)
from flits.batch.codetection_plots import BandSpectrum, plot_codetection  # noqa: E402

from plot_codetection_gallery import (  # noqa: E402
    BANDS as _GALLERY_BANDS,
    FILE_NICK,
    discover_products,
    load_band,
    onpulse_span,
)

# Full structural display grid: DSA native time; CHIME native time (not ×13);
# 512 frequency channels per band. Stricter than the compact gallery grid.
BANDS = {
    "dsa": {**_GALLERY_BANDS["dsa"], "f_factor": 12, "t_factor": 1},
    "chime": {**_GALLERY_BANDS["chime"], "f_factor": 2, "t_factor": 1},
}

MANIFEST_DEFAULT = ROOT / "scripts" / "jointmodel_triptych_manifest.yaml"
OUT_DEFAULT = ROOT / "figures" / "codetection_triptych"
DATA_ROOT_DEFAULT = Path.home() / "Data/Faber2026/dsa110/DSA_bursts"
PAD_FLOOR_MS = 1.5


def load_manifest(path: Path) -> list[dict]:
    raw = yaml.safe_load(path.read_text())
    rows = list(raw["bursts"])
    if len(rows) != 12:
        raise ValueError(f"manifest must list 12 bursts, got {len(rows)}")
    return rows


def _band_from_npz(z, band: str) -> BandSpectrum:
    label = "CHIME/FRB" if band == "C" else "DSA-110"
    return BandSpectrum(
        freq_mhz=np.asarray(z[f"freq{band}"], float) * 1e3,
        time_ms=np.asarray(z[f"time{band}"], float),
        data=np.asarray(z[f"data{band}"], float),
        model=np.asarray(z[f"model{band}"], float),
        sigma=np.asarray(z[f"noise{band}"], float),
        label=label,
        channel_valid=np.asarray(z[f"valid{band}"], bool),
    )


def _shift_time(b: BandSpectrum, shift_ms: float) -> BandSpectrum:
    return BandSpectrum(
        freq_mhz=b.freq_mhz,
        time_ms=np.asarray(b.time_ms, float) + shift_ms,
        data=b.data,
        model=b.model,
        sigma=b.sigma,
        label=b.label,
        channel_valid=b.channel_valid,
    )


def _align_toa(bands: list[BandSpectrum], nick: str) -> list[BandSpectrum]:
    chime = next(b for b in bands if "CHIME" in b.label)
    dsa = next(b for b in bands if "DSA" in b.label)
    offset = toa_offset_ms(nick)
    if offset is None:
        return [chime, dsa]
    shift_c = chime_toa_shift_ms(dsa, chime, offset)
    return [_shift_time(chime, shift_c), dsa]


def _dt_ms(b: BandSpectrum) -> float:
    t = np.asarray(b.time_ms, float)
    if t.size < 2:
        return 0.033
    return float(np.median(np.diff(t)))


def _peak_time(b: BandSpectrum) -> float:
    t = np.asarray(b.time_ms, float)
    prof = np.nansum(np.asarray(b.data, float), axis=0)
    return float(t[int(np.nanargmax(prof))])


def band_onpulse_ms(b: BandSpectrum) -> tuple[float, float]:
    t = np.asarray(b.time_ms, float)
    prof = np.nansum(np.asarray(b.data, float), axis=0)
    lo, hi, _ = onpulse_span(prof, _dt_ms(b))
    return float(t[lo]), float(t[hi])


def chime_width_display_window(bands: list[BandSpectrum]) -> tuple[float, float]:
    by = {("CHIME" if "CHIME" in b.label else "DSA"): b for b in bands}
    if "CHIME" not in by or "DSA" not in by:
        raise ValueError("need CHIME and DSA bands for windowing")
    c_lo, c_hi = band_onpulse_ms(by["CHIME"])
    d_lo, d_hi = band_onpulse_ms(by["DSA"])
    w_c = max(c_hi - c_lo, 0.0)
    p = max(w_c, PAD_FLOOR_MS)
    return min(c_lo, d_lo) - p, max(c_hi, d_hi) + p


def crop_spectrum(b: BandSpectrum, t0: float, t1: float) -> BandSpectrum:
    t = np.asarray(b.time_ms, float)
    i0 = int(np.searchsorted(t, t0, side="left"))
    i1 = int(np.searchsorted(t, t1, side="right"))
    i0 = max(0, i0)
    i1 = min(t.size, max(i0 + 1, i1))
    return BandSpectrum(
        freq_mhz=b.freq_mhz,
        time_ms=t[i0:i1],
        data=np.asarray(b.data, float)[:, i0:i1],
        model=np.asarray(b.model, float)[:, i0:i1],
        sigma=b.sigma,
        label=b.label,
        channel_valid=b.channel_valid,
    )


def crop_bands(bands: list[BandSpectrum], xlim: tuple[float, float]) -> list[BandSpectrum]:
    return [crop_spectrum(b, *xlim) for b in bands]


def _channel_valid(ds: np.ndarray) -> np.ndarray:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        row = np.nanmean(ds, axis=1)
    return np.isfinite(row)


def _sigma_from_offpulse(ds: np.ndarray) -> np.ndarray:
    n_t = ds.shape[1]
    off = np.concatenate([ds[:, : n_t // 4], ds[:, -n_t // 4 :]], axis=1)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        sig = np.nanstd(off, axis=1)
    return np.where(np.isfinite(sig) & (sig > 0), sig, 1.0)


def load_archival_band(data_root: Path, nick: str, tel: str) -> BandSpectrum:
    """Archival product at gallery display resolution (full structural grid)."""
    file_nick = FILE_NICK.get(nick, nick)
    products = discover_products(data_root, file_nick)
    band = BANDS[tel]
    ds, profile = load_band(products[tel].path, band)
    n_f, n_t = ds.shape
    dt = band["dt_ms"] * band["t_factor"]
    pk = int(np.nanargmax(profile))
    t = (np.arange(n_t) - pk) * dt
    f_mhz = np.linspace(band["f_lo"], band["f_hi"], n_f) * 1e3
    label = "CHIME/FRB" if tel == "chime" else "DSA-110"
    return BandSpectrum(
        freq_mhz=f_mhz,
        time_ms=t,
        data=ds,
        model=np.zeros_like(ds),
        sigma=_sigma_from_offpulse(ds),
        label=label,
        channel_valid=_channel_valid(ds),
    )


def interpolate_field(src: BandSpectrum, field: str, dest_f: np.ndarray, dest_t: np.ndarray) -> np.ndarray:
    """Bilinear regrid of src.{field} onto dest frequency (MHz) × time (ms)."""
    f = np.asarray(src.freq_mhz, float)
    t = np.asarray(src.time_ms, float)
    vals = np.asarray(getattr(src, field), float)
    if f[0] > f[-1]:
        f = f[::-1]
        vals = vals[::-1]
    # RegularGridInterpolator needs strictly increasing axes
    if not (np.all(np.diff(f) > 0) and np.all(np.diff(t) > 0)):
        raise ValueError(f"non-monotonic axes for {src.label} {field}")
    interp = RegularGridInterpolator(
        (f, t),
        np.nan_to_num(vals, nan=0.0),
        bounds_error=False,
        fill_value=0.0,
    )
    ff, tt = np.meshgrid(dest_f, dest_t, indexing="ij")
    return interp((ff, tt))


def fuse_archival_with_model(
    coarse: BandSpectrum,
    fine: BandSpectrum,
) -> BandSpectrum:
    """Archival data on the fine grid; coarse NPZ model interpolated onto it.

    Time-align by matching band-summed data-profile peaks (archival ↔ NPZ data).
    """
    fine_aligned = _shift_time(fine, _peak_time(coarse) - _peak_time(fine))
    model = interpolate_field(coarse, "model", fine_aligned.freq_mhz, fine_aligned.time_ms)
    return BandSpectrum(
        freq_mhz=fine_aligned.freq_mhz,
        time_ms=fine_aligned.time_ms,
        data=np.asarray(fine_aligned.data, float),
        model=model,
        sigma=fine_aligned.sigma,
        label=fine_aligned.label,
        channel_valid=fine_aligned.channel_valid,
    )


def bands_fullres(npz_path: Path, nick: str, data_root: Path) -> list[BandSpectrum]:
    z = np.load(npz_path, allow_pickle=True)
    coarse = _align_toa([_band_from_npz(z, "C"), _band_from_npz(z, "D")], nick)
    fine_chime = load_archival_band(data_root, nick, "chime")
    fine_dsa = load_archival_band(data_root, nick, "dsa")
    fine = _align_toa([fine_chime, fine_dsa], nick)
    by_c = {("CHIME" if "CHIME" in b.label else "DSA"): b for b in coarse}
    by_f = {("CHIME" if "CHIME" in b.label else "DSA"): b for b in fine}
    fused = [
        fuse_archival_with_model(by_c["CHIME"], by_f["CHIME"]),
        fuse_archival_with_model(by_c["DSA"], by_f["DSA"]),
    ]
    return crop_bands(fused, chime_width_display_window(fused))


def bands_data_only(data_root: Path, nick: str) -> list[BandSpectrum]:
    fine = _align_toa(
        [load_archival_band(data_root, nick, "chime"), load_archival_band(data_root, nick, "dsa")],
        nick,
    )
    # peak-align CHIME to DSA when no TOA table entry
    if toa_offset_ms(nick) is None:
        chime, dsa = fine
        fine = [_shift_time(chime, _peak_time(dsa) - _peak_time(chime)), dsa]
    return crop_bands(fine, chime_width_display_window(fine))


def panel_title(tns: str, flag: str | None) -> str:
    if flag and flag != "no accepted joint fit":
        return rf"{tns}$^\dagger$"
    return tns


def render_row(
    row: dict,
    *,
    root: Path,
    data_root: Path,
    out_dir: Path,
    dpi: int,
) -> Path:
    nick = row["nick"]
    tns = row["tns"]
    flag = row.get("flag")
    npz = row.get("npz")
    if npz:
        bands = bands_fullres(root / npz, nick, data_root)
        columns = ("data", "model", "resid")
        title = panel_title(tns, flag)
        # Sanity: refuse to ship coarse-only panels
        for b in bands:
            dt = _dt_ms(b)
            if b.data.shape[0] < 256:
                raise RuntimeError(
                    f"{nick} {b.label}: too few channels {b.data.shape}; "
                    "expected archival display-res (≥256)"
                )
            # CHIME must be near-native time; DSA native 32.768 µs.
            if "CHIME" in b.label and dt > 0.005:
                raise RuntimeError(
                    f"{nick} {b.label}: dt={dt*1e3:.2f} µs too coarse; expected ~2.56 µs"
                )
            if "DSA" in b.label and dt > 0.04:
                raise RuntimeError(
                    f"{nick} {b.label}: dt={dt*1e3:.2f} µs too coarse; expected ~32.8 µs"
                )
    else:
        bands = bands_data_only(data_root, nick)
        columns = ("data",)
        title = f"{tns} (no accepted joint fit)"

    fig = plot_codetection(
        bands,
        columns=columns,
        show_model_on_data=False,
        per_band_scale=True,
        gap_label=False,
        band_labels=False,
        show_column_titles=True,
        per_band_marginals=True,
        figsize=(12.4, 4.9),
        title=title,
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = out_dir / f"{nick}_triptych"
    fig.savefig(stem.with_suffix(".png"), dpi=dpi)
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(stem.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)
    return stem.with_suffix(".pdf")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path, default=MANIFEST_DEFAULT)
    ap.add_argument("--out-dir", type=Path, default=OUT_DEFAULT)
    ap.add_argument("--data-root", type=Path, default=DATA_ROOT_DEFAULT)
    ap.add_argument("--dpi", type=int, default=600)
    ap.add_argument("--burst", action="append", help="optional nick filter")
    args = ap.parse_args()

    rows = load_manifest(args.manifest)
    if args.burst:
        want = set(args.burst)
        rows = [r for r in rows if r["nick"] in want]
    written = [
        render_row(r, root=ROOT, data_root=args.data_root, out_dir=args.out_dir, dpi=args.dpi)
        for r in rows
    ]
    print(f"rendered {len(written)} triptych(s) → {args.out_dir}")
    for p in written:
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
