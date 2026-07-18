import sys, numpy as np
sys.path.insert(0,"scint_analysis")
import window_refit as wr
# chromatica MANUAL windows (user-supplied, validated): burst [184,198] off [20,175]
MANUAL = dict(chromatica=([184,198],[20,175]))
for nm,(bl,ol) in MANUAL.items():
    print(f"=== {nm} MANUAL window {bl}/{ol} with PR-192 fitter (no time_weights) ===")
    r = wr.refit(nm, bl, ol)
    cf=r["center_freqs"]
    for i in r["order"]:
        f=r["fits"][int(i)]
        if not f["ok"]: print(f"  {cf[i]:6.0f} no fit"); continue
        gb=f"  gb={f['gamma_b']:.2f}" if f.get('gamma_b') else ""
        print(f"  {cf[i]:6.0f} MHz g={f['gamma']:.4f} m={f['m']:.2f} {f['model_sel']} "
              f"dBIC2={f.get('dbic_2comp') or 0:.1f} {'RES' if f['resolved'] else 'unr'}{gb}")
    a=r["alpha"]; print(f"  alpha={a['alpha']:+.2f}+-{a['alpha_err']:.2f} n={a['n']}" if a else "  alpha=n/a")
    # also with matched weights on manual window
    prof=np.ma.mean(wr._build_spec(nm,bl,ol)[0].power,axis=0)
    prof=np.ma.filled(prof,np.nanmedian(prof)); w=np.clip(prof-np.median(prof),0,None)
    w[:bl[0]]=0; w[bl[1]:]=0
    print(f"  -- same window + matched weights --")
    r2=wr.refit(nm,bl,ol,time_weights=w); cf=r2["center_freqs"]
    for i in r2["order"]:
        f=r2["fits"][int(i)]
        if f["ok"]: print(f"  {cf[i]:6.0f} MHz g={f['gamma']:.4f} m={f['m']:.2f} {f['model_sel']} {'RES' if f['resolved'] else 'unr'}")
    a=r2["alpha"]; print(f"  alpha={a['alpha']:+.2f}+-{a['alpha_err']:.2f} n={a['n']}" if a else "  alpha=n/a")
