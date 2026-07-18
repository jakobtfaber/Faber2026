"""Independent per-subband Lorentzian ACF fits for ONE CHIME burst.

Fixes the joint-2D failure mode: fit each equal-S/N subband's ACF SEPARATELY with a
Lorentzian (excluding the lag-0 self-noise spike), report gamma_d (HWHM decorr bandwidth),
modulation index m, and a resolved/unresolved quality flag per subband. Derive alpha AFTERWARD
from only the subbands that show a genuinely resolved decay.

Lorentzian ACF model (off lag 0):  ACF(l) = A / (1 + (l/gamma)^2) + c
  gamma = HWHM decorrelation bandwidth (MHz);  m = sqrt(A) modulation index;  c = baseline.
"""
from __future__ import annotations
import os, sys, json, copy
import numpy as np
from scipy.optimize import curve_fit
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

R = os.environ["FLITS_ROOT"]; sys.path.insert(0, R + "/scintillation"); sys.path.insert(0, R)
sys.path.insert(0, "/Users/jakobfaber/Developer/scratch")
from scint_analysis import freya_scintillation as fs
from scint_analysis import config as config_module
from scint_analysis import analysis as ana
import auto_rfi_flag as arf

name = os.environ["ONE_BURST"]
CH = json.load(open(os.environ["CHOICES"]))[name]
OUT = os.environ.get("OUT", "/Users/jakobfaber/Developer/scratch/persubband_fits")
os.makedirs(OUT, exist_ok=True)
burst = tuple(int(x) for x in CH["burst_lims"]); off = tuple(int(x) for x in CH["off_lims"])
windows_are_default = bool(CH.get("_default_windows", False))
_MIN_OFF = 50; SIGMA_RFI = 5.0
LAG_MAX = 5.0          # MHz, max lag included in fit
N_SKIP = 1            # skip the lag-0 self-noise spike (fit from |lag|>0)
COMB_SPACING_MHZ = 0.390625   # CHIME coarse-channel spacing (harmonic-mask target)
COMB_HALFWIDTH_MHZ = 0.05     # pipeline default halfwidth

cfg = config_module.load_config(f"{R}/scintillation/configs/bursts/{name}_chime.yaml")
c = copy.deepcopy(cfg); an = c.setdefault("analysis", {})
an.setdefault("acf", {})["num_subbands"] = 4; an["acf"]["use_snr_subbanding"] = True
an.setdefault("grid_regularization", {})["enable"] = True
an.setdefault("bandpass_normalization", {})["enable"] = True
an.setdefault("rfi_masking", {})["manual_burst_window"] = list(burst)
an["rfi_masking"]["manual_noise_window"] = list(off)

use_median = (off[1] - off[0]) < _MIN_OFF
if use_median:
    c["analysis"]["bandpass_normalization"]["enable"] = False
spec, bl, ol = fs.prepare_spectrum_from_config(c)
if use_median:
    colmask = np.ones(spec.power.shape[1], bool); colmask[burst[0]:burst[1]] = False
    gain = np.ma.filled(np.ma.median(spec.power[:, colmask], axis=1), np.nan)
    med = np.nanmedian(gain[np.isfinite(gain) & (gain > 0)])
    bad = ~(np.isfinite(gain) & (gain > 1e-3 * med)); g = np.where(bad, 1.0, gain)
    m0 = spec.power.mask if spec.power.mask is not np.ma.nomask else np.zeros(spec.power.shape, bool)
    spec.power = np.ma.MaskedArray(spec.power.data / g[:, None], mask=m0 | bad[:, None])
descallop = "time-median flat-field" if use_median else "off-pulse mean (bandpass_normalization)"

flag, flag_info = arf.auto_flag(spec.power, off, sigma=SIGMA_RFI, iters=6)
m1 = spec.power.mask if spec.power.mask is not np.ma.nomask else np.zeros(spec.power.shape, bool)
spec.power = np.ma.MaskedArray(spec.power.data, mask=m1 | flag[:, None])

res = ana.calculate_acfs_for_subbands(spec, c, burst_lims=burst, noise_desc=None)
cf = np.asarray(res["subband_center_freqs_mhz"], float)


def lorentz(l, A, gamma, c0):
    return A / (1.0 + (l / gamma) ** 2) + c0


def fit_subband(lags, acf):
    """Fit Lorentzian to |lag|>0 side. Returns dict with gamma, m, quality metrics."""
    lags = np.asarray(lags, float); acf = np.asarray(acf, float)
    i0 = int(np.argmin(np.abs(lags)))
    norm = acf[i0] if acf[i0] != 0 else np.nanmax(acf)
    a = acf / norm
    pos = lags > 0
    lp = lags[pos]; ap = a[pos]
    o = np.argsort(lp); lp = lp[o]; ap = ap[o]
    sel = lp <= LAG_MAX
    lp = lp[sel][N_SKIP - 1:]; ap = ap[sel][N_SKIP - 1:]
    # exclude the CHIME coarse-channel comb (residual channelizer correlation at
    # k*0.390625 MHz) using the pipeline's own harmonic_lag_mask, so the comb
    # spikes don't pull the Lorentzian fit.
    keep = ana.harmonic_lag_mask(lp, COMB_SPACING_MHZ, COMB_HALFWIDTH_MHZ)
    lp = lp[keep]; ap = ap[keep]
    if lp.size < 8:
        return dict(ok=False, reason="too few lags")
    # noise floor from the outer half of the lag window
    outer = lp > 0.5 * lp.max()
    noise = float(np.std(ap[outer])) if outer.sum() > 3 else float(np.std(ap))
    A0 = max(ap[0] - np.median(ap[outer]), 1e-3)
    g0 = 0.5
    try:
        p, cov = curve_fit(lorentz, lp, ap, p0=[A0, g0, 0.0],
                           bounds=([0, 0.01, -1], [10, 20, 1]), maxfev=20000)
        perr = np.sqrt(np.diag(cov))
    except Exception as e:
        return dict(ok=False, reason=str(e), noise=noise)
    A, gamma, c0 = p; Aerr, gerr, _ = perr
    resid = ap - lorentz(lp, *p)
    rms = float(np.sqrt(np.mean(resid ** 2)))
    m = float(np.sqrt(max(A, 0)))
    # resolved if: amplitude clears the noise floor, gamma is not railed at either bound,
    # gamma is larger than the lag resolution and smaller than the fit window
    dlag = float(np.median(np.diff(lp)))
    amp_snr = A / noise if noise > 0 else np.inf
    railed = (gamma < 0.02) or (gamma > 0.9 * 20) or (gamma > 0.9 * LAG_MAX)
    resolved = bool((amp_snr > 3) and (not railed) and (gamma > 2 * dlag) and (gerr < gamma))
    return dict(ok=True, A=float(A), A_err=float(Aerr), gamma=float(gamma), gamma_err=float(gerr),
                c0=float(c0), m=m, noise=noise, amp_snr=float(amp_snr), res_rms=rms,
                dlag=dlag, resolved=resolved,
                lp=lp.tolist(), ap=ap.tolist(), model=lorentz(lp, *p).tolist())


order = np.argsort(cf)[::-1]
fits = {}
for i in order:
    fits[i] = fit_subband(res["subband_lags_mhz"][i], res["subband_acfs"][i])

# figure
n = len(order)
fig, axes = plt.subplots(1, n, figsize=(3.4 * n, 3.4), sharex=True)
if n == 1: axes = [axes]
for ax, i in zip(axes, order):
    f = fits[i]
    if f["ok"]:
        ax.plot(f["lp"], f["ap"], color="#c0392b", lw=1.0, label="data")
        col = "#1e8449" if f["resolved"] else "#7f8c8d"
        ax.plot(f["lp"], f["model"], color=col, lw=1.8, ls="--",
                label=f"γ={f['gamma']:.3f}±{f['gamma_err']:.3f}\nm={f['m']:.2f} {'RESOLVED' if f['resolved'] else 'unres.'}")
    ax.axhline(0, color="k", lw=0.4, alpha=0.4)
    ax.set_xlim(0, LAG_MAX); ax.set_title(f"{cf[i]:.0f} MHz", fontsize=9)
    ax.set_xlabel("lag (MHz)"); ax.legend(fontsize=6.5, loc="upper right")
axes[0].set_ylabel("ACF (norm to lag 0)")
wtag = "DEFAULT windows" if windows_are_default else "edited windows"
fig.suptitle(f"{name}: independent per-subband Lorentzian fits  [{wtag}; RFI +{flag_info['n_flagged']} ch]", fontsize=10)
fig.tight_layout()
fig.savefig(f"{OUT}/{name}_persubband_fit.png", dpi=125, bbox_inches="tight")
plt.close(fig)

# derive alpha from resolved subbands only (log-log gamma vs nu)
resolved = [(cf[i], fits[i]["gamma"], fits[i]["gamma_err"]) for i in order
            if fits[i]["ok"] and fits[i]["resolved"]]
alpha_fit = None
if len(resolved) >= 2:
    fr = np.array([r[0] for r in resolved]); gm = np.array([r[1] for r in resolved])
    ge = np.array([r[2] for r in resolved])
    lw = 1.0 / (ge / gm) ** 2
    A = np.vstack([np.log(fr / np.mean(fr)), np.ones_like(fr)]).T
    W = np.diag(lw)
    cov = np.linalg.inv(A.T @ W @ A)
    beta = cov @ (A.T @ W @ np.log(gm))
    alpha_fit = dict(alpha=float(beta[0]), alpha_err=float(np.sqrt(cov[0, 0])),
                     n_resolved=len(resolved))

result = dict(name=name, descallop=descallop, windows_are_default=windows_are_default,
              burst_lims=list(burst), off_lims=list(off),
              rfi_new_flagged=int(flag_info["n_flagged"]),
              subbands=[dict(center_mhz=round(float(cf[i]), 1),
                             **{k: v for k, v in fits[i].items() if k not in ("lp", "ap", "model")})
                        for i in order],
              alpha_from_resolved=alpha_fit)
with open(f"{OUT}/persubband_fit_results.jsonl", "a") as fh:
    fh.write(json.dumps(result) + "\n")

nres = sum(1 for i in order if fits[i]["ok"] and fits[i]["resolved"])
gs = " ".join(f"{cf[i]:.0f}:{fits[i]['gamma']:.3f}{'*' if fits[i]['resolved'] else ''}"
              for i in order if fits[i]["ok"])
astr = f"alpha={alpha_fit['alpha']:.2f}+-{alpha_fit['alpha_err']:.2f}(n={alpha_fit['n_resolved']})" if alpha_fit else "alpha=n/a"
print(f"{name}: {nres} resolved | gamma[MHz] {gs} | {astr}")
