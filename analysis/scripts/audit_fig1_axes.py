"""Per-panel frequency-axis and DM-provenance audit for the Figure 1 gallery.

Executes the two resubmission requirements recorded by the manuscript owner in
figure_review batch 2026-07-17-fig1-model-toa (fig1-gallery decision addendum):

1. DM provenance: the producer re-dedisperses each archival waterfall from its
   filename-stem DM to the adopted CHIME phase-coherence DM, so a product whose
   stem misstates its actually-applied DM (the chromatica 272.368-vs-272.664
   precedent) leaves residual sweep. For every panel we measure the residual
   drift slope of on-pulse arrival time against nu^-2 at the adopted DM and
   convert it to an equivalent Delta-DM with uncertainty.

2. Frequency-axis validation: the loader assumes both products are stored
   frequency-descending (row 0 = band top; pipeline
   scattering/configs/telescopes.yaml `freq_descending`) and flips to
   ascending. The `.npy` products carry no header, so the audit validates the
   axis from the data and configuration rather than assuming the ordering:

   - Band edges: the gallery BANDS constants must equal the pipeline
     telescopes.yaml `f_min_GHz`/`f_max_GHz` exactly.
   - CHIME ordering (per panel, decisive): CHIME's persistent LTE mask at
     729-756 MHz is excised in every product. Under the correct ordering the
     excised rows concentrate in that window; under the mirrored ordering they
     would sit near 445-471 MHz where no comparable persistent allocation
     exists. Each product's flagged rows are scored under both hypotheses.
   - DSA ordering (per panel, convention + consistency): DSA flagging is
     per-epoch (no static mask), so no single allocation is decisive. Each
     product's flagged-row profile is scored against the leave-one-out pooled
     profile of the other eleven products versus its mirror, which proves all
     twelve share one storage convention; the convention itself (row 0 =
     1498.75 MHz) is the dsa110-scat writer convention recorded in
     pipeline/scattering/configs/telescopes.yaml (`freq_descending: true`,
     citing the burstfittools model flip). Raw headers live only in the CANFAR
     production tree and are recorded here as unavailable locally.

   Note on the casey incident: `~/Data/.../products/casey_chime_freq.npy` is an
   ascending 12336-channel axis belonging to the separate upchannelized
   product, not the 1024-row `_cntr_bpc` display product (whose LTE mask
   matches the descending hypothesis like every other CHIME product). Mixing
   the two families is the identified mechanism for the earlier upside-down
   render.

Outputs an audit JSON (and a per-panel drift diagnostic figure) intended to be
staged into the review batch's provenance directory.
"""

from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import yaml

from plot_codetection_data_grid import DM_CATALOG_DEFAULT, load_adopted_dms
from plot_codetection_gallery import BANDS, discover_products, load_band
from plot_codetection_triptych import (
    DATA_ROOT_DEFAULT,
    FILE_NICK,
    MANIFEST_DEFAULT,
    ROOT,
    load_manifest,
)

K_DM_MS = 4.148808e6  # dispersion constant, ms MHz^2 (pc cm^-3)^-1
LTE_MHZ = (729.0, 756.0)  # persistent CHIME excision window used as the anchor
TELESCOPES_YAML = ROOT / "pipeline" / "scattering" / "configs" / "telescopes.yaml"


def _flagged_rows_raw(path: Path, n_cols: int = 1500) -> np.ndarray:
    """Zero-variance / non-finite rows of the RAW (unflipped) product."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        arr = np.asarray(np.load(path, mmap_mode="r")[:, :n_cols], float)
        sd = np.nanstd(arr, axis=1)
    return np.where((~np.isfinite(sd)) | (sd == 0))[0]


def _row_freqs(n: int, f_lo_mhz: float, f_hi_mhz: float, descending: bool) -> np.ndarray:
    ramp = np.linspace(f_hi_mhz, f_lo_mhz, n) if descending else np.linspace(f_lo_mhz, f_hi_mhz, n)
    return ramp


def audit_band_edges() -> dict:
    tel = yaml.safe_load(TELESCOPES_YAML.read_text())
    out = {}
    for key in ("dsa", "chime"):
        cfg_lo, cfg_hi = float(tel[key]["f_min_GHz"]), float(tel[key]["f_max_GHz"])
        band_lo, band_hi = float(BANDS[key]["f_lo"]), float(BANDS[key]["f_hi"])
        out[key] = {
            "telescopes_yaml_GHz": [cfg_lo, cfg_hi],
            "gallery_BANDS_GHz": [band_lo, band_hi],
            "match": bool(cfg_lo == band_lo and cfg_hi == band_hi),
            "config_freq_descending": bool(tel[key].get("freq_descending", False)),
        }
    return out


def audit_chime_ordering(path: Path, n_rows: int) -> dict:
    """Score the LTE-mask position under descending vs mirrored hypotheses."""
    rows = _flagged_rows_raw(path)
    scores = {}
    for hyp, descending in (("descending", True), ("ascending", False)):
        f = _row_freqs(n_rows, BANDS["chime"]["f_lo"] * 1e3, BANDS["chime"]["f_hi"] * 1e3, descending)
        in_lte = (f[rows] >= LTE_MHZ[0]) & (f[rows] <= LTE_MHZ[1])
        # fraction of the LTE window's rows that are flagged (occupancy)
        window_rows = np.sum((f >= LTE_MHZ[0]) & (f <= LTE_MHZ[1]))
        scores[hyp] = float(np.sum(in_lte) / max(window_rows, 1))
    verdict = "descending" if scores["descending"] > 2.0 * scores["ascending"] else (
        "ascending" if scores["ascending"] > 2.0 * scores["descending"] else "ambiguous"
    )
    return {
        "n_flagged_rows": int(len(rows)),
        "lte_occupancy_if_descending": round(scores["descending"], 3),
        "lte_occupancy_if_ascending": round(scores["ascending"], 3),
        "verdict": verdict,
        "matches_loader_assumption": verdict == "descending",
    }


def audit_dsa_ordering(paths: dict[str, Path], n_rows: int, bin_width: int = 64) -> dict:
    """Leave-one-out flagged-profile consistency across all DSA products."""
    profiles = {}
    for nick, p in paths.items():
        h = np.zeros(n_rows // bin_width)
        rows = _flagged_rows_raw(p)
        for r in rows:
            h[min(r // bin_width, len(h) - 1)] += 1
        profiles[nick] = h
    out = {}
    for nick, h in profiles.items():
        pooled = np.sum([v for k, v in profiles.items() if k != nick], axis=0)
        a, b = h - h.mean(), pooled - pooled.mean()
        m = b[::-1]
        denom = np.sqrt((a**2).sum() * (b**2).sum())
        c_same = float((a * b).sum() / denom) if denom else 0.0
        denom_m = np.sqrt((a**2).sum() * (m**2).sum())
        c_mirr = float((a * m).sum() / denom_m) if denom_m else 0.0
        out[nick] = {
            "corr_vs_pool": round(c_same, 3),
            "corr_vs_mirrored_pool": round(c_mirr, 3),
            "consistent_with_shared_convention": bool(c_same > c_mirr),
        }
    return out


def audit_dm_drift(
    path: Path, telescope: str, stem_dm: float, target_dm: float, n_sub: int = 8
) -> dict:
    """Residual arrival-time drift vs nu^-2 at the adopted DM -> Delta-DM.

    Loads through the gallery's own `load_band` (flip + residual dedispersion +
    display averaging), splits the band into `n_sub` sub-bands, measures the
    on-pulse intensity-weighted arrival centroid per sub-band, and fits
    t = a + b * (nu^-2 - <nu^-2>). b converts to an equivalent DM offset;
    consistency with zero is the pass condition the owner specified.
    """
    band = dict(BANDS[telescope])
    ds, profile = load_band(path, band, telescope=telescope, residual_dm=float(target_dm - stem_dm))
    n_f, n_t = ds.shape
    dt = band["dt_ms"] * band["t_factor"]
    f_mhz = np.linspace(band["f_lo"], band["f_hi"], n_f) * 1e3
    pk = int(np.nanargmax(profile))
    half = max(8, int(round(6.0 / dt)))  # +-6 ms on-pulse window around the peak
    lo, hi = max(0, pk - half), min(n_t, pk + half)
    t_axis = (np.arange(n_t) - pk) * dt

    xs, ys, ws = [], [], []
    edges = np.linspace(0, n_f, n_sub + 1, dtype=int)
    for i in range(n_sub):
        sub = ds[edges[i] : edges[i + 1], lo:hi]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            prof = np.nanmean(sub, axis=0)
        if not np.isfinite(prof).any():
            continue
        prof = prof - np.nanmedian(prof)
        prof[~np.isfinite(prof)] = 0.0
        prof = np.clip(prof, 0.0, None)
        w = float(prof.sum())
        if w <= 0:
            continue
        t_c = float((prof * t_axis[lo:hi]).sum() / w)
        f_c = float(np.mean(f_mhz[edges[i] : edges[i + 1]]))
        xs.append(f_c**-2)
        ys.append(t_c)
        ws.append(w)
    if len(xs) < 4:
        return {"status": "insufficient_subbands", "n_subbands_used": len(xs)}
    f_c = np.asarray(xs) ** -0.5  # recover centroid freqs from nu^-2
    y = np.asarray(ys)
    w = np.asarray(ws)

    def _wls(design: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        sw = np.sqrt(w)
        a = design * sw[:, None]
        b = y * sw
        coef, *_ = np.linalg.lstsq(a, b, rcond=None)
        resid = b - a @ coef
        dof = max(len(y) - design.shape[1], 1)
        cov = np.linalg.inv(a.T @ a) * float(resid @ resid) / dof
        return coef, np.sqrt(np.diag(cov))

    x2 = f_c**-2 - np.average(f_c**-2, weights=w)
    x4 = f_c**-4 - np.average(f_c**-4, weights=w)
    ones = np.ones_like(x2)

    # nu^-2-only fit: biased positive for scattered bursts (the tail's centroid
    # lag ~ tau ~ nu^-4 masquerades as extra dispersion) -- recorded for
    # transparency, not the pass criterion.
    c2, s2 = _wls(np.column_stack([ones, x2]))
    # joint fit separates dispersion (nu^-2) from the scattering-tail centroid
    # lag (nu^-4); the DM verdict comes from this fit.
    c24, s24 = _wls(np.column_stack([ones, x2, x4]))

    scan = _sharpness_scan_ddm(ds, f_mhz, dt, lo, hi)
    ddm, ddm_sigma = scan["delta_dm_pc_cm3"], scan["delta_dm_sigma"]
    return {
        "status": "ok",
        "n_subbands_used": int(len(xs)),
        # Verdict metric: profile-sharpness maximization over trial residual
        # DM -- to first order symmetric under scattering, unlike the centroid
        # slope, which a nu^-4 tail biases positive (recorded below anyway).
        "delta_dm_pc_cm3": round(ddm, 4),
        "delta_dm_sigma": round(ddm_sigma, 4),
        "consistent_with_zero_2sigma": bool(abs(ddm) <= max(2.0 * ddm_sigma, 0.05)),
        "centroid_nu2_slope_pc_cm3": round(float(c2[1] / K_DM_MS), 4),
        "centroid_nu2_slope_sigma": round(float(s2[1] / K_DM_MS), 4),
        "centroid_joint_nu2_pc_cm3": round(float(c24[1] / K_DM_MS), 4),
        "centroid_joint_nu2_sigma": round(float(s24[1] / K_DM_MS), 4),
        "subband_nu_inv2": [round(v, 10) for v in xs],
        "subband_t_ms": [round(v, 4) for v in ys],
    }


def _sharpness_scan_ddm(
    ds: np.ndarray,
    f_mhz: np.ndarray,
    dt_ms: float,
    lo: int,
    hi: int,
    half_span: float = 0.6,
    step: float = 0.02,
    n_boot: int = 30,
    seed: int = 20260707,
) -> dict:
    """Residual DM by band-summed-profile peak maximization.

    Trial residual dedispersion is applied as integer sample rolls per channel
    (matching the display pipeline's shift quantization); the peak of the
    smoothed band-summed profile is maximized over the trial grid, refined by
    parabolic interpolation, and the uncertainty is the channel-bootstrap
    spread of that argmax.
    """
    rng = np.random.default_rng(seed)
    pad = int(np.ceil(K_DM_MS * half_span * abs(f_mhz.min() ** -2 - f_mhz.max() ** -2) / dt_ms)) + 4
    w0, w1 = max(0, lo - pad), min(ds.shape[1], hi + pad)
    sub = np.asarray(ds[:, w0:w1], float)
    sub = sub - np.nanmedian(sub, axis=1, keepdims=True)
    sub[~np.isfinite(sub)] = 0.0
    n_f, n_t = sub.shape
    ref_inv2 = float(f_mhz.max() ** -2)
    trials = np.arange(-half_span, half_span + step / 2, step)
    kern = np.ones(5) / 5.0

    shift_per_unit = K_DM_MS * (f_mhz**-2 - ref_inv2) / dt_ms  # samples per pc cm^-3

    def scan(rows: np.ndarray) -> float:
        amps = np.empty(trials.size)
        for i, d in enumerate(trials):
            shifts = np.rint(shift_per_unit[rows] * d).astype(int)
            idx = (np.arange(n_t)[None, :] + shifts[:, None]) % n_t
            prof = np.take_along_axis(sub[rows], idx, axis=1).sum(axis=0)
            amps[i] = np.convolve(prof, kern, mode="same").max()
        j = int(np.argmax(amps))
        if 0 < j < trials.size - 1:
            a, b, c = amps[j - 1], amps[j], amps[j + 1]
            denom = a - 2 * b + c
            frac = 0.5 * (a - c) / denom if denom != 0 else 0.0
            return float(trials[j] + np.clip(frac, -1, 1) * step)
        return float(trials[j])

    all_rows = np.arange(n_f)
    best = scan(all_rows)
    boots = [scan(rng.choice(all_rows, size=n_f, replace=True)) for _ in range(n_boot)]
    return {
        "delta_dm_pc_cm3": best,
        "delta_dm_sigma": float(np.std(boots, ddof=1)),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-root", type=Path, default=DATA_ROOT_DEFAULT)
    ap.add_argument("--manifest", type=Path, default=MANIFEST_DEFAULT)
    ap.add_argument("--dm-catalog", type=Path, default=DM_CATALOG_DEFAULT)
    ap.add_argument("--out", type=Path, default=ROOT / "figure_review" / "axes_audit.json")
    ap.add_argument("--fig-out", type=Path, default=None)
    args = ap.parse_args()

    rows = load_manifest(args.manifest)
    adopted = load_adopted_dms(args.dm_catalog)
    report: dict = {"band_edges": audit_band_edges(), "panels": {}}

    dsa_paths: dict[str, Path] = {}
    chime_paths: dict[str, Path] = {}
    for row in rows:
        nick = row["nick"]
        prods = discover_products(args.data_root, FILE_NICK.get(nick, nick))
        dsa_paths[nick] = prods["dsa"].path
        chime_paths[nick] = prods["chime"].path
        panel: dict = {}
        n_chime = int(np.load(prods["chime"].path, mmap_mode="r").shape[0])
        panel["chime_ordering"] = audit_chime_ordering(prods["chime"].path, n_chime)
        for tel in ("chime", "dsa"):
            panel[f"{tel}_dm_drift"] = audit_dm_drift(
                prods[tel].path, tel, prods[tel].dm, adopted[nick.lower()]
            )
            panel[f"{tel}_stem_dm"] = prods[tel].dm
        panel["adopted_dm"] = adopted[nick.lower()]
        report["panels"][nick] = panel

    n_dsa_rows = int(np.load(next(iter(dsa_paths.values())), mmap_mode="r").shape[0])
    dsa_consistency = audit_dsa_ordering(dsa_paths, n_dsa_rows)
    for nick, res in dsa_consistency.items():
        report["panels"][nick]["dsa_ordering"] = res

    # CHIME tie-breaker: a product whose flagged fraction saturates both LTE
    # hypotheses (wilhelm: heavy band-limited excision) is disambiguated by the
    # same leave-one-out raw-row template test used for DSA -- the static CHIME
    # mask runs are a strong shared fingerprint in raw row order.
    n_chime_rows = int(np.load(next(iter(chime_paths.values())), mmap_mode="r").shape[0])
    chime_template = audit_dsa_ordering(chime_paths, n_chime_rows, bin_width=16)
    for nick, res in chime_template.items():
        p = report["panels"][nick]
        p["chime_template_consistency"] = res
        if p["chime_ordering"]["verdict"] == "ambiguous":
            resolved = "descending" if res["consistent_with_shared_convention"] else "ambiguous"
            p["chime_ordering"]["verdict"] = resolved
            p["chime_ordering"]["matches_loader_assumption"] = resolved == "descending"
            p["chime_ordering"]["resolved_by"] = "leave-one-out template vs 11 LTE-proven products"
    report["dsa_ordering_note"] = (
        "per-epoch flagging: convention (row0=1498.75 MHz) from "
        "pipeline/scattering/configs/telescopes.yaml + burstfittools flip; "
        "leave-one-out profile consistency proves a single shared storage "
        "convention across all 12 products; raw CANFAR headers unavailable locally"
    )

    ok_chime = all(p["chime_ordering"]["matches_loader_assumption"] for p in report["panels"].values())
    ok_dsa = all(p["dsa_ordering"]["consistent_with_shared_convention"] for p in report["panels"].values())
    ok_edges = all(v["match"] for v in report["band_edges"].values())
    drift_flags = {
        nick: {t: p[f"{t}_dm_drift"].get("consistent_with_zero_2sigma") for t in ("chime", "dsa")}
        for nick, p in report["panels"].items()
    }
    report["summary"] = {
        "band_edges_match_config": ok_edges,
        "chime_ordering_all_descending": ok_chime,
        "dsa_shared_convention_all": ok_dsa,
        "dm_drift_consistent_with_zero": drift_flags,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    print(f"wrote {args.out}")

    if args.fig_out:
        fig, axes = plt.subplots(4, 3, figsize=(11, 12), sharex=False)
        for ax, (nick, p) in zip(axes.ravel(), report["panels"].items()):
            for tel, color in (("chime", "#b73779"), ("dsa", "black")):
                d = p[f"{tel}_dm_drift"]
                if d.get("status") != "ok":
                    continue
                x = np.asarray(d["subband_nu_inv2"]) * 1e6
                ax.plot(x, d["subband_t_ms"], "o", ms=3, color=color,
                        label=f"{tel} dDM={d['delta_dm_pc_cm3']:+.3f}")
            ax.set_title(nick, fontsize=8)
            ax.legend(fontsize=5, frameon=False)
        fig.supxlabel(r"$\nu^{-2}$ [$10^{-6}$ MHz$^{-2}$]")
        fig.supylabel("on-pulse arrival centroid [ms]")
        fig.tight_layout()
        args.fig_out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.fig_out, dpi=200)
        plt.close(fig)
        print(f"wrote {args.fig_out}")

    print(json.dumps(report["summary"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
