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
import json
import re
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
CHIME_FULL_ROOT_DEFAULT = Path.home() / "Data/Faber2026/chimefrb/CHIME_bursts"
DSA_FULL_ROOT_DEFAULT = Path.home() / "Data/Faber2026/dsa110/DSA_bursts"
PAD_FLOOR_MS = 1.5
TOA_RESULTS = ROOT / "pipeline" / "crossmatching" / "toa_crossmatch_results.json"
TOA_FIXTURE = ROOT / "pipeline" / "crossmatching" / "notebook_reproduction_fixture.json"
K_DM_S_MHZ2 = 4.148808e3


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


def toa_offset_at_dm_ms(
    nick: str,
    target_dm: float,
    *,
    toa_results: Path = TOA_RESULTS,
    toa_fixture: Path = TOA_FIXTURE,
) -> float | None:
    """Re-reference the legacy CHIME-minus-DSA 400-MHz offset to ``target_dm``.

    The tracked CHIME TOA is already expressed at 400 MHz. The DSA TOA was
    propagated from the fixture's native frequency to 400 MHz using the
    legacy row DM, so changing that DM by ``delta_dm`` changes the DSA TOA by
    ``K_DM * delta_dm * (400^-2 - nu_DSA^-2)``. Because the stored offset is
    CHIME minus DSA, that correction is subtracted from the legacy offset.
    """
    file_nick = FILE_NICK.get(nick, nick)
    rows = json.loads(toa_results.read_text())
    row = rows.get(file_nick) or rows.get(file_nick.lower())
    if row is None:
        return None
    fixture = json.loads(toa_fixture.read_text())
    f_ref = float(fixture["reference_frequency_mhz"])
    f_dsa = float(fixture["dsa_native_frequency_mhz"])
    delta_dm = float(target_dm) - float(row["dm"])
    dsa_delta_ms = (
        1e3 * K_DM_S_MHZ2 * delta_dm * (f_ref**-2 - f_dsa**-2)
    )
    return float(row["measured_offset_ms"]) - dsa_delta_ms


def _toa_offset(nick: str, *, target_dm: float | None = None) -> float | None:
    """Measured CHIME-minus-DSA offset in the requested DM convention.

    Crossmatch rows use file nicknames (for example ``johndoeII``), so map
    manuscript nicknames through ``FILE_NICK`` before either lookup.
    """
    file_nick = FILE_NICK.get(nick, nick)
    if target_dm is None:
        return toa_offset_ms(file_nick)
    return toa_offset_at_dm_ms(file_nick, target_dm)


def _align_toa(
    bands: list[BandSpectrum], nick: str, *, target_dm: float | None = None
) -> list[BandSpectrum]:
    chime = next(b for b in bands if "CHIME" in b.label)
    dsa = next(b for b in bands if "DSA" in b.label)
    offset = _toa_offset(nick, target_dm=target_dm)
    if offset is None:
        return [chime, dsa]
    return [_shift_time(chime, chime_toa_shift_ms(dsa, chime, offset)), dsa]


def fit_json_path(npz_path: Path) -> Path:
    """joint_fit JSON tracked beside a jointmodel NPZ (same run suffix)."""
    return Path(str(npz_path).replace("_jointmodel_", "_joint_fit_")).with_suffix(".json")


def dominant_t0_ms(
    percentiles: dict, band_key: str, fit_t: np.ndarray, model_prof: np.ndarray
) -> float:
    """Fitted arrival (t0 median, ms) of the dominant model component.

    Dominant = the component whose t0 is nearest the noiseless model-profile
    peak; anchoring on the earliest component instead lets weak leading
    components displace the anchor by many ms.
    """
    t0s = [
        float(v["median"])
        for k, v in percentiles.items()
        if re.fullmatch(rf"t0_{band_key}\d*", k)
    ]
    if not t0s:
        raise ValueError(f"no t0_{band_key}* in joint fit percentiles")
    peak = float(np.asarray(fit_t, float)[int(np.nanargmax(model_prof))])
    return min(t0s, key=lambda v: abs(v - peak))


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
    """Data + model on the identical fit-delivery grid from the NPZ.

    Time axes are anchored on the fitted arrival times: the DSA-110 dominant
    component's t0 defines t=0 and the CHIME/FRB band is placed with its
    fitted arrival at the measured inter-instrument offset. Falls back to the
    profile-peak alignment when the joint_fit JSON or measured offset is
    missing.
    """
    z = np.load(npz_path, allow_pickle=True)
    chime, dsa = _band_from_npz(z, "C"), _band_from_npz(z, "D")
    fj = fit_json_path(npz_path)
    offset = _toa_offset(nick)
    if fj.exists() and offset is not None:
        percentiles = json.loads(fj.read_text())["percentiles"]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            t0_c = dominant_t0_ms(
                percentiles, "C", z["timeC"], np.nansum(np.asarray(z["modelC"], float), axis=0)
            )
            t0_d = dominant_t0_ms(
                percentiles, "D", z["timeD"], np.nansum(np.asarray(z["modelD"], float), axis=0)
            )
        bands = [_shift_time(chime, offset - t0_c), _shift_time(dsa, -t0_d)]
    else:
        bands = _align_toa([chime, dsa], nick)
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
    chime_full_root: Path,
    dsa_full_root: Path,
    nick: str,
    factors: dict[str, tuple[int, int]] | None = None,
    pad_scale: float = 1.0,
    pad_cap_ms: float | None = None,
    target_dm: float | None = None,
    extra_shift_ms: dict[str, float] | None = None,
    extra_dedisp_pc: dict[str, float] | None = None,
) -> list[BandSpectrum]:
    """Archival `_cntr_bpc.npy` products as BandSpectrum pairs (no model).

    `factors` overrides the gallery display resolution per telescope as
    (f_factor, t_factor) block-averaging factors of the native grid.
    `pad_scale` scales and `pad_cap_ms` bounds the CHIME-width display
    padding around the on-pulse union.
    When ``target_dm`` is supplied, each native waterfall is shifted from its
    filename-stem DM to that common value before any display averaging.
    `extra_shift_ms` (band label -> ms) is applied after the TOA alignment
    and before windowing, e.g. to move the per-band anchor from the data
    profile peak to a fitted arrival time.
    `extra_dedisp_pc` (telescope key -> pc cm^-3) adds a per-product residual
    dedispersion on top of the stem-to-target shift -- the audit-derived
    correction for products whose filename stem misstates the actually-applied
    DM (scripts/audit_fig1_axes.py; the chromatica precedent).
    """
    file_nick = FILE_NICK.get(nick, nick)
    products = discover_products(chime_full_root, dsa_full_root, file_nick)
    out: list[BandSpectrum] = []
    for tel in ("chime", "dsa"):
        band = dict(BANDS[tel])
        if factors and tel in factors:
            band["f_factor"], band["t_factor"] = factors[tel]
        residual_dm = 0.0 if target_dm is None else float(target_dm - products[tel].dm)
        if extra_dedisp_pc:
            residual_dm += float(extra_dedisp_pc.get(tel, 0.0))
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
    fine = _align_toa(out, nick, target_dm=target_dm)
    if _toa_offset(nick, target_dm=target_dm) is None:
        chime, dsa = fine
        fine = [_shift_time(chime, _peak_time(dsa) - _peak_time(chime)), dsa]
    if extra_shift_ms:
        fine = [_shift_time(b, extra_shift_ms.get(b.label, 0.0)) for b in fine]
    return crop_bands(
        fine,
        chime_width_display_window(fine, pad_scale=pad_scale, pad_cap_ms=pad_cap_ms),
    )


def bands_data_only(
    chime_full_root: Path,
    dsa_full_root: Path,
    nick: str,
) -> list[BandSpectrum]:
    """Chromatica: archival products at gallery display resolution (no model)."""
    return bands_archival(chime_full_root, dsa_full_root, nick)


def panel_title(tns: str, flag: str | None) -> str:
    if flag and flag != "no accepted joint fit":
        return rf"{tns}$^\dagger$"
    return tns


def render_row(
    row: dict,
    *,
    root: Path,
    chime_full_root: Path,
    dsa_full_root: Path,
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
        bands = bands_data_only(chime_full_root, dsa_full_root, nick)
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
    path_arg = lambda value: Path(value).expanduser()  # noqa: E731
    ap.add_argument(
        "--chime-full-root", type=path_arg, default=CHIME_FULL_ROOT_DEFAULT
    )
    ap.add_argument("--dsa-full-root", type=path_arg, default=DSA_FULL_ROOT_DEFAULT)
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--burst", action="append", help="optional nick filter")
    args = ap.parse_args()

    rows = load_manifest(args.manifest)
    if args.burst:
        want = set(args.burst)
        rows = [r for r in rows if r["nick"] in want]
    written = [
        render_row(
            r,
            root=ROOT,
            chime_full_root=args.chime_full_root,
            dsa_full_root=args.dsa_full_root,
            out_dir=args.out_dir,
            dpi=args.dpi,
        )
        for r in rows
    ]
    print(f"rendered {len(written)} triptych(s) → {args.out_dir}")
    for p in written:
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
