"""Run the PR-192 estimator end-to-end on real bursts: objective window selection
(window_optimize) -> matched refit (window_refit) -> per-subband gamma + alpha."""
import sys, os, numpy as np
sys.path.insert(0,"scint_analysis")
import window_refit as wr, window_optimize as wo

def band_profile(name):
    """Band-averaged S/N time profile from the de-scalloped spectrum (default windows)."""
    bl, ol = wr.default_windows(name)
    spec, c, method = wr._build_spec(name, bl, ol)
    p = spec.power
    prof = np.ma.mean(p, axis=0)         # average over channels -> time profile
    return np.ma.filled(prof, np.nan), bl, ol

def run(name):
    prof, bl0, ol0 = band_profile(name)
    prof = np.nan_to_num(prof, nan=np.nanmedian(prof))
    sel = wo.select_windows(prof)
    if sel is None:
        print(f"{name}: window selection returned None (fallback to default {bl0},{ol0})")
        burst, off, wts = bl0, ol0, None
    else:
        burst = sel["burst_lims"]; off = sel["off_lims"]; wts = sel["weights"]
        print(f"{name}: auto burst={burst} off={off} off_snr={sel['off_snr']:.1f} "
              f"matched_snr={sel['matched']['snr']:.1f}")
    r = wr.refit(name, burst, off, time_weights=wts)
    cf = r["center_freqs"]
    for i in r["order"]:
        f = r["fits"][int(i)]
        if not f["ok"]:
            print(f"    {cf[i]:6.0f} MHz  no fit ({f.get('reason','')[:30]})"); continue
        tag = "RESOLVED" if f["resolved"] else "unres"
        gb = f"  gb={f['gamma_b']:.2f}" if f.get("gamma_b") else ""
        print(f"    {cf[i]:6.0f} MHz  g={f['gamma']:.4f} m={f['m']:.2f} "
              f"{f['model_sel']} dBIC2={f.get('dbic_2comp') or 0:.1f} {tag}{gb}")
    a = r["alpha"]
    if a: print(f"    alpha = {a['alpha']:+.2f} +- {a['alpha_err']:.2f} (n={a['n']}"
                f"{', PROVISIONAL' if a.get('provisional') else ''})")
    else: print("    alpha = n/a (<2 resolved with m<=1.2)")

for nm in ["chromatica","zach","whitney"]:
    print("="*60); run(nm)
