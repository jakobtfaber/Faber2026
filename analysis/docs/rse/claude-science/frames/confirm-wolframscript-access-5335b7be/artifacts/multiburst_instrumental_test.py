"""Multi-burst instrumental-origin test: run freya's decisive discriminators on ALL bursts.

Question: does the CHIME ~kHz decorrelation scale fail the same way for every burst
(instrumental everywhere), or does freya fail uniquely (freya quenched, others carry real
scintillation)?

Two discriminators, reusing the exact freya_scintillation machinery:
  Arm A  off-pulse ACF null: measure "dnu" in burst-free noise slices with the identical fit.
         - instrumental: off-pulse reproduces the on-pulse scale; aggregate z(1-6 ch) >> 0.
         - astrophysical: off-pulse ACF white; z ~ 0; on-pulse ACF >> off-pulse ACF at low lags.
  Arm B2 split-time persistence CCF: cross-correlate the two on-pulse halves.
         Scintillation is a multiplicative spectral pattern frozen over the burst, so it
         survives in CCF(half1,half2); radiometer/noise-borne correlation does not.
         - real scintillation: burst-referenced CCF(1-6 ch) ~ m^2 > 0, z >> 0.
         - noise-borne artifact: CCF ~ 0.
The clean verdict is the RATIO on-pulse/off-pulse ACF (arm A) and the persistence CCF (B2):
both separate a real frozen spectral pattern from a per-realization noise-borne correlation.
"""
from __future__ import annotations
import os, sys, json
import numpy as np

R = os.environ["FLITS_ROOT"]
sys.path.insert(0, R + "/scintillation")
sys.path.insert(0, R)
from scint_analysis import freya_scintillation as fs
from scint_analysis import config as config_module

BURSTS = ["casey", "whitney", "phineas", "mahi", "freya", "zach",
          "chromatica", "wilhelm", "oran", "hamilton", "johndoeII", "isha"]
CFG_DIR = R + "/scintillation/configs/bursts"


def arm_a_offpulse_null(spectrum, burst_lims, off_lims, cw):
    """Off-pulse fitted-scale null (scale-invariant, the decisive discriminator).

    The fitted decorrelation scale is normalized internally by curve_fit, so it is robust to
    the missing bandpass normalization in these diagnostic_only configs. If off-pulse (noise-only)
    slices reproduce the on-pulse scale, the recovered scale is instrumental/noise-borne.
    """
    def measure(win):
        sub = spectrum.get_spectrum(win)
        return fs.measure_scintillation_bandwidth(sub, channel_width_mhz=cw,
                                                  max_lag_mhz=5.0, fit_lag_mhz=1.0)
    r_on = measure(tuple(burst_lims))
    w = burst_lims[1] - burst_lims[0]
    starts = list(range(off_lims[0] + 2, off_lims[1] - w, w + 4))
    off = [measure((s, s + w)) for s in starts]
    fitted = [r for r in off if r.success and r.delta_nu_mhz]
    off_dnu = [round(r.delta_nu_mhz * 1e3, 1) for r in fitted]

    # --- scale-separation z: is the on-pulse fitted scale distinguishable from the noise floor? ---
    on_dnu = None if r_on.delta_nu_mhz is None else r_on.delta_nu_mhz * 1e3
    on_err = None if r_on.delta_nu_err_mhz is None else r_on.delta_nu_err_mhz * 1e3
    sep_z = None; verdict = "no-fit"
    if on_dnu is not None and off_dnu:
        off_med = float(np.median(off_dnu))
        off_mad = float(np.median(np.abs(np.array(off_dnu) - off_med))) * 1.4826
        off_scatter = off_mad / np.sqrt(len(off_dnu)) if off_mad > 0 else (np.std(off_dnu)/np.sqrt(len(off_dnu)) or 1.0)
        comb = np.sqrt((on_err or 0.0) ** 2 + off_scatter ** 2)
        sep_z = round(float((on_dnu - off_med) / comb), 2) if comb > 0 else None
        # instrumental if the noise floor reproduces the on-pulse scale (on not > off at >3 sigma)
        verdict = "INSTRUMENTAL (off reproduces on)" if (sep_z is None or sep_z < 3) else "on-pulse excess"

    # slice-averaged off-pulse ACF on the shared channel-lag grid.
    # These configs are NOT bandpass-normalized (raw correlator units), so normalize each
    # slice's ACF to its own lag-0 value (scale-invariant) and take the MEDIAN across slices
    # to resist pathological slices (near-zero-variance -> blow-up on lag-0 division).
    def norm_acf(r):
        lg = np.asarray(r.lags_mhz, float); ac = np.asarray(r.acf, float)
        ch = np.round(lg / cw).astype(int)
        i0 = int(np.argmin(np.abs(ch)))                     # lag-0 index
        a0 = ac[i0]
        if not np.isfinite(a0) or abs(a0) < 1e-30:
            return None
        return ch, ac / a0
    off_norm = [x for x in (norm_acf(r) for r in off if r.acf and r.lags_mhz) if x is not None]
    if not off_norm:
        return dict(on_dnu_khz=(None if r_on.delta_nu_mhz is None else round(r_on.delta_nu_mhz*1e3,2)),
                    off_dnu_khz=off_dnu, off_dnu_median_khz=(round(float(np.median(off_dnu)),1) if off_dnu else None),
                    n_off=len(off), sep_z=sep_z, verdict=verdict,
                    agg_z_1_6=None, on_acf_1_6=None, off_acf_1_6=None, ratio_on_off=None)
    lag_ch = off_norm[0][0]
    A = np.vstack([a for _, a in off_norm])
    med_acf = np.nanmedian(A, axis=0)
    # robust spread across slices -> pseudo-SEM via MAD
    mad = np.nanmedian(np.abs(A - med_acf), axis=0) * 1.4826
    sem_acf = mad / np.sqrt(A.shape[0])
    on = norm_acf(r_on)
    if on is None:
        return dict(on_dnu_khz=(None if r_on.delta_nu_mhz is None else round(r_on.delta_nu_mhz*1e3,2)),
                    off_dnu_khz=off_dnu, n_off=len(off), off_dnu_median_khz=(round(float(np.median(off_dnu)),1) if off_dnu else None),
                    sep_z=sep_z, verdict=verdict,
                    agg_z_1_6=None, on_acf_1_6=None, off_acf_1_6=None, ratio_on_off=None)
    on_ch, on_acf = on
    sel = (lag_ch >= 1) & (lag_ch <= 6)
    on_sel = (on_ch >= 1) & (on_ch <= 6)
    with np.errstate(divide="ignore", invalid="ignore"):
        zz = med_acf[sel] / sem_acf[sel]
        agg_z = float(np.nansum(zz) / np.sqrt(int(sel.sum())))
    off_acf_16 = float(np.nanmedian(med_acf[sel]))
    on_acf_16 = float(np.nanmedian(on_acf[on_sel]))
    ratio = on_acf_16 / off_acf_16 if off_acf_16 and np.isfinite(off_acf_16) else None
    return dict(
        on_dnu_khz=(None if r_on.delta_nu_mhz is None else round(r_on.delta_nu_mhz * 1e3, 2)),
        on_dnu_err_khz=(None if r_on.delta_nu_err_mhz is None else round(r_on.delta_nu_err_mhz*1e3,2)),
        off_dnu_khz=off_dnu, n_off=len(off),
        off_dnu_median_khz=(round(float(np.median(off_dnu)), 1) if off_dnu else None),
        sep_z=sep_z, verdict=verdict,
        agg_z_1_6=round(agg_z, 2),
        # amplitude-based fields UNRELIABLE here (configs lack bandpass_normalization -> raw units)
        on_acf_1_6=round(on_acf_16, 6), off_acf_1_6=round(off_acf_16, 6),
        ratio_on_off=(round(ratio, 2) if ratio else None))


def arm_b2_persistence(spectrum, burst_lims, off_lims, cw, max_lag_ch=170):
    """Split-time CCF of the two on-pulse halves (burst-referenced)."""
    t0, t1 = burst_lims
    mid = (t0 + t1) // 2
    if mid - t0 < 2 or t1 - mid < 2:
        return dict(ccf_1_6=None, z_1_6=None, note="burst too narrow to split")
    s1 = spectrum.get_spectrum((t0, mid)); s2 = spectrum.get_spectrum((mid, t1))
    off_level = float(np.ma.mean(spectrum.get_spectrum(off_lims)))
    mu1, mu2 = float(np.ma.mean(s1)), float(np.ma.mean(s2))
    denom = (mu1 - off_level) * (mu2 - off_level)
    xa = s1.filled(np.nan) - mu1; xb = s2.filled(np.nan) - mu2
    ks = np.arange(-max_lag_ch, max_lag_ch + 1)
    vals = np.full(ks.size, np.nan); sems = np.full(ks.size, np.nan)
    for i, k in enumerate(ks):
        p = (xa[:xa.size - k] * xb[k:]) if k >= 0 else (xa[-k:] * xb[:xb.size + k])
        p = p[np.isfinite(p)]
        if p.size > 20:
            vals[i] = np.mean(p); sems[i] = np.std(p, ddof=1) / np.sqrt(p.size)
    if denom == 0 or not np.isfinite(denom):
        return dict(ccf_1_6=None, z_1_6=None, note="denom zero")
    vals /= denom; sems /= denom
    sel = (np.abs(ks) >= 1) & (np.abs(ks) <= 6)
    v16 = float(np.nanmean(vals[sel]))
    z16 = v16 / (np.sqrt(np.nansum(sems[sel] ** 2)) / int(sel.sum()))
    return dict(ccf_1_6=round(v16, 5), z_1_6=round(float(z16), 2),
                denom=round(denom, 6), note="ok")


results = {}
for b in BURSTS:
    cfg_path = f"{CFG_DIR}/{b}_chime.yaml"
    if not os.path.exists(cfg_path):
        results[b] = {"error": "no config"}; continue
    try:
        cfg = config_module.load_config(cfg_path)
        spec, bl, ol = fs.prepare_spectrum_from_config(cfg)
        cw = float(spec.channel_width_mhz)
        a = arm_a_offpulse_null(spec, bl, ol, cw)
        b2 = arm_b2_persistence(spec, bl, ol, cw)
        results[b] = dict(cw_khz=round(cw * 1e3, 3), nchan=int(spec.power.shape[0]),
                          burst_lims=list(bl), off_lims=list(ol), arm_a=a, arm_b2=b2)
    except Exception as e:
        import traceback
        results[b] = {"error": f"{type(e).__name__}: {e}", "tb": traceback.format_exc()[-500:]}

out = "/Users/jakobfaber/Developer/scratch/multiburst_instrumental_results.json"
json.dump(results, open(out, "w"), indent=2)
print("WROTE", out)
# compact console summary — the SCALE-INVARIANT columns are the decisive ones:
#   on_dnu vs off_med (fitted scale) and sep_z (does on-pulse scale exceed the noise floor?).
# Amplitude columns (ACF ratio, B2 CCF amplitude) are unreliable: these diagnostic_only configs
# lack bandpass_normalization, so absolute power is in raw correlator units.
print(f"\n{'burst':11} {'cw_kHz':>7} {'on_dnu':>8} {'off_med':>8} {'sep_z':>7}  verdict")
for b in BURSTS:
    r = results.get(b, {})
    if "error" in r:
        print(f"{b:11} ERROR: {r['error'][:50]}"); continue
    a = r["arm_a"]
    print(f"{b:11} {r['cw_khz']:>7.2f} {str(a['on_dnu_khz']):>8} {str(a.get('off_dnu_median_khz')):>8} "
          f"{str(a.get('sep_z')):>7}  {a.get('verdict','')}")
