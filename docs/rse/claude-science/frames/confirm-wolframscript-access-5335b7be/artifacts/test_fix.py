import sys, numpy as np
sys.path.insert(0,"scint_analysis")
import window_refit as wr, window_optimize as wo

def prof_of(name):
    bl,ol=wr.default_windows(name); spec,_,_=wr._build_spec(name,bl,ol)
    p=np.ma.filled(np.ma.mean(spec.power,axis=0),np.nan); return np.nan_to_num(p,nan=np.nanmedian(p))

def run(name, use_core=False):
    p=prof_of(name); sel=wo.select_windows(p)
    burst = sel["burst_core"] if use_core else sel["burst_lims"]
    wts=None
    if not use_core and sel["weights"] is not None:
        wts=sel["weights"]  # weights already span full time-length? check
    r=wr.refit(name, burst, sel["off_lims"], time_weights=wts)
    a=r["alpha"]; cf=r["center_freqs"]
    gl="/".join(f"{r['fits'][int(i)]['gamma']:.3f}{'*' if r['fits'][int(i)]['resolved'] else ''}" for i in r["order"] if r["fits"][int(i)]["ok"])
    astr=f"{a['alpha']:+.2f}+-{a['alpha_err']:.2f} n={a['n']}" if a else "n/a"
    print(f"  {name:11} off={str(sel['off_lims']):12} off_snr={sel['off_snr']:4.1f} burst={burst} : a={astr} [{gl}]")

print("=== OFF-FIX, primary path (tail-expanded burst_lims + matched weights) ===")
for nm in ["chromatica","zach","whitney"]: run(nm, use_core=False)
print("=== OFF-FIX + burst_core (narrow ACF window) ===")
for nm in ["chromatica","zach","whitney"]: run(nm, use_core=True)
