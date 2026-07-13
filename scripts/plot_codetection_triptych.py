"""Opening Fig. 1 sequence producer: per-burst data | model | residual triptychs.

Renders figures/codetection_triptych/{nick}_triptych.{pdf,png,svg} from the
jointmodel NPZ roster in scripts/jointmodel_triptych_manifest.yaml.

Resolution contract: DATA and MODEL share the fit-delivery grid stored in the
jointmodel NPZ (the same f_factor/t_factor used when the burst was handed to the
fitter). Do not upsample archival products beside an interpolated model.
`show_model_on_data=False` — no overlays on the data waterfall.

Chromatica (npz: null) is data-only from archival `_cntr_bpc.npy` products.

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

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
sys.path.insert(0, str(ROOT / "scripts"))

from flits.batch.codetection_data import (  # noqa: E402
    chime_toa_shift_ms,
    toa_offset_ms,
)
from flits.batch.codetection_plots import BandSpectrum, plot_codetection  # noqa: E402

from plot_codetection_gallery import (  # noqa: E402
    BANDS,
    FILE_NICK,
    discover_products,
    load_band,
    onpulse_span,
)

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
    return [_shift_time(chime, chime_toa_shift_ms(dsa, chime, offset)), dsa]


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


def chime_width_display_window(
    bands: list[BandSpectrum],
    pad_scale: float = 1.0,
    pad_cap_ms: float | None = None,
) -> tuple[float, float]:
    """On-pulse union of both bands, padded by pad_scale x the CHIME width.

    `pad_cap_ms` bounds the padding in absolute ms so heavily scattered
    bursts (whose CHIME on-pulse width is itself tens of ms) do not inflate
    the off-pulse margins; the on-pulse union itself is never cropped.
    """
    by = {("CHIME" if "CHIME" in b.label else "DSA"): b for b in bands}
    if "CHIME" not in by or "DSA" not in by:
        raise ValueError("need CHIME and DSA bands for windowing")
    c_lo, c_hi = band_onpulse_ms(by["CHIME"])
    d_lo, d_hi = band_onpulse_ms(by["DSA"])
    p = max(pad_scale * (c_hi - c_lo), PAD_FLOOR_MS)
    if pad_cap_ms is not None:
        p = min(p, pad_cap_ms)
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


def bands_from_npz(npz_path: Path, nick: str) -> list[BandSpectrum]:
    """Data + model on the identical fit-delivery grid from the NPZ."""
    z = np.load(npz_path, allow_pickle=True)
    bands = _align_toa([_band_from_npz(z, "C"), _band_from_npz(z, "D")], nick)
    for b in bands:
        if b.data.shape != b.model.shape:
            raise RuntimeError(f"{nick} {b.label}: data/model shape mismatch {b.data.shape} vs {b.model.shape}")
    return crop_bands(bands, chime_width_display_window(bands))


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


def bands_archival(
    data_root: Path,
    nick: str,
    factors: dict[str, tuple[int, int]] | None = None,
    pad_scale: float = 1.0,
    pad_cap_ms: float | None = None,
    target_dm: float | None = None,
) -> list[BandSpectrum]:
    """Archival `_cntr_bpc.npy` products as BandSpectrum pairs (no model).

    `factors` overrides the gallery display resolution per telescope as
    (f_factor, t_factor) block-averaging factors of the native grid.
    `pad_scale` scales and `pad_cap_ms` bounds the CHIME-width display
    padding around the on-pulse union.
    When ``target_dm`` is supplied, each native waterfall is shifted from its
    filename-stem DM to that common value before any display averaging.
    """
    file_nick = FILE_NICK.get(nick, nick)
    products = discover_products(data_root, file_nick)
    out: list[BandSpectrum] = []
    for tel in ("chime", "dsa"):
        band = dict(BANDS[tel])
        if factors and tel in factors:
            band["f_factor"], band["t_factor"] = factors[tel]
        residual_dm = 0.0 if target_dm is None else float(target_dm - products[tel].dm)
        ds, profile = load_band(
            products[tel].path,
            band,
            telescope=tel,
            residual_dm=residual_dm,
        )
        n_f, n_t = ds.shape
        dt = band["dt_ms"] * band["t_factor"]
        pk = int(np.nanargmax(profile))
        t = (np.arange(n_t) - pk) * dt
        f_mhz = np.linspace(band["f_lo"], band["f_hi"], n_f) * 1e3
        label = "CHIME/FRB" if tel == "chime" else "DSA-110"
        out.append(
            BandSpectrum(
                freq_mhz=f_mhz,
                time_ms=t,
                data=ds,
                model=np.zeros_like(ds),
                sigma=_sigma_from_offpulse(ds),
                label=label,
                channel_valid=_channel_valid(ds),
            )
        )
    fine = _align_toa(out, nick)
    if toa_offset_ms(nick) is None:
        chime, dsa = fine
        fine = [_shift_time(chime, _peak_time(dsa) - _peak_time(chime)), dsa]
    return crop_bands(
        fine,
        chime_width_display_window(fine, pad_scale=pad_scale, pad_cap_ms=pad_cap_ms),
    )


def bands_data_only(data_root: Path, nick: str) -> list[BandSpectrum]:
    """Chromatica: archival products at gallery display resolution (no model)."""
    return bands_archival(data_root, nick)


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
        bands = bands_from_npz(root / npz, nick)
        columns = ("data", "model", "resid")
        title = panel_title(tns, flag)
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
    # Keep the burst name clear of the per-column titles in this manuscript layout.
    fig.suptitle(title, fontsize=10, y=1.02)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = out_dir / f"{nick}_triptych"
    fig.savefig(stem.with_suffix(".png"), dpi=dpi, bbox_inches="tight")
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(stem.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)
    return stem.with_suffix(".pdf")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path, default=MANIFEST_DEFAULT)
    ap.add_argument("--out-dir", type=Path, default=OUT_DEFAULT)
    ap.add_argument("--data-root", type=Path, default=DATA_ROOT_DEFAULT)
    ap.add_argument("--dpi", type=int, default=300)
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
