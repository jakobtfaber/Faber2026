"""Run de-scallop + automatic off-pulse RFI flag + equal-S/N subband ACFs + joint 2D Lorentzian
fit (gamma(nu) = gamma_0*(nu/nu_ref)^alpha) for ONE burst. Writes a per-burst JSON result and a
3-panel figure (dynamic spectrum w/ flag, subband ACFs w/ fit overlay, gamma(nu) scaling).
"""
from __future__ import annotations
import os, sys, json, copy
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

R = os.environ["FLITS_ROOT"]; sys.path.insert(0, R + "/scintillation"); sys.path.insert(0, R)
sys.path.insert(0, "/Users/jakobfaber/Developer/scratch")
from scint_analysis import freya_scintillation as fs
from scint_analysis import config as config_module
from scint_analysis import analysis as ana
from scint_analysis import fitting_2d as f2d
import auto_rfi_flag as arf

name = os.environ["ONE_BURST"]
CH = json.load(open(os.environ["CHOICES"]))[name]
OUT = os.environ.get("OUT", "/Users/jakobfaber/Developer/scratch/autorfi_fits")
os.makedirs(OUT, exist_ok=True)
burst = tuple(int(x) for x in CH["burst_lims"]); off = tuple(int(x) for x in CH["off_lims"])
windows_are_default = bool(CH.get("_default_windows", False))
_MIN_OFF = 50
SIGMA_RFI = 5.0

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
descallop_method = "time-median flat-field" if use_median else "off-pulse mean (pipeline bandpass_normalization)"

# automatic off-pulse RFI flag
flag, flag_info = arf.auto_flag(spec.power, off, sigma=SIGMA_RFI, iters=6)
m1 = spec.power.mask if spec.power.mask is not np.ma.nomask else np.zeros(spec.power.shape, bool)
already = m1[:, off[0]:off[1]].all(axis=1)
spec.power = np.ma.MaskedArray(spec.power.data, mask=m1 | flag[:, None])

# trust checks
acf_off_before = arf.offpulse_acf_lowlag(np.ma.MaskedArray(spec.power.data, mask=m1), off, burst)
acf_off_after = arf.offpulse_acf_lowlag(spec.power, off, burst)
bright = arf.burst_bright_channels(spec.power, burst, z_thresh=8.0)
burst_overlap = int((flag & bright).sum())

res = ana.calculate_acfs_for_subbands(spec, c, burst_lims=burst, noise_desc=None)
cf = np.asarray(res["subband_center_freqs_mhz"], float)

# joint 2D Lorentzian fit across sub-bands
fit_ok = True; fit_err = None
try:
    fitres = f2d.fit_2d_scintillation(res, model_type="lorentzian", fit_range_mhz=5.0,
                                       gamma_0_init=0.1, alpha_init=4.0, vary_alpha=True)
except Exception as e:
    fit_ok = False; fit_err = str(e); fitres = None

order = np.argsort(cf)[::-1]
n = len(order)
fig, axes = plt.subplots(1, n, figsize=(3.2 * n, 3.2), sharey=True)
if n == 1:
    axes = [axes]
for ax, i in zip(axes, order):
    lags = np.asarray(res["subband_lags_mhz"][i], float)
    acf = np.asarray(res["subband_acfs"][i], float)
    i0 = int(np.argmin(np.abs(lags))); a = acf / acf[i0]
    pos = lags > 0; lp = lags[pos]; ap = a[pos]
    o = np.argsort(lp); lp = lp[o]; ap = ap[o]
    ax.plot(lp, ap, color="#c0392b", lw=1.0, label="data")
    if fit_ok and fitres.success:
        g, gerr = fitres.gamma_at_freq(cf[i])
        m0 = fitres.m_0
        model = f2d.lorentzian_acf(lp, g, m0)
        ax.plot(lp, model, color="#2c74b3", lw=1.4, ls="--", label=f"fit γ={g:.3f}")
    ax.set_xlim(0, min(5.0, lp.max() if lp.size else 5.0))
    ax.set_title(f"{cf[i]:.0f} MHz", fontsize=9)
    ax.set_xlabel("lag (MHz)")
axes[0].set_ylabel("ACF (norm)"); axes[0].legend(fontsize=7)
ttl = f"{name}: joint 2D Lorentzian fit"
if fit_ok and fitres.success:
    ttl += f"  γ₀={fitres.gamma_0:.3f}±{fitres.gamma_0_err:.3f} α={fitres.alpha:.2f}±{fitres.alpha_err:.2f} χ²ν={fitres.redchi:.2f}"
else:
    ttl += "  FIT FAILED" if not fit_ok else "  fit did not converge"
fig.suptitle(ttl, fontsize=10)
fig.tight_layout()
fig.savefig(f"{OUT}/{name}_autorfi_fit.png", dpi=125, bbox_inches="tight")
plt.close(fig)

result = dict(
    name=name, descallop_method=descallop_method, windows_are_default=windows_are_default,
    burst_lims=list(burst), off_lims=list(off),
    rfi=dict(sigma=SIGMA_RFI, n_flagged_total=flag_info["n_flagged"], frac_total=flag_info["frac"],
              n_pipeline_masked=int(already.sum()), n_new_auto=int((flag & ~already).sum()),
              offpulse_acf_before=acf_off_before, offpulse_acf_after=acf_off_after,
              burst_overlap=burst_overlap),
    subband_center_freqs_mhz=[round(float(x), 1) for x in cf],
    fit=(dict(success=bool(fitres.success), gamma_0=fitres.gamma_0, gamma_0_err=fitres.gamma_0_err,
              alpha=fitres.alpha, alpha_err=fitres.alpha_err, m_0=fitres.m_0, m_0_err=fitres.m_0_err,
              nu_ref=fitres.nu_ref, redchi=fitres.redchi, nfree=fitres.nfree)
         if fit_ok else dict(success=False, error=fit_err)),
)
with open(f"{OUT}/autorfi_fit_results.jsonl", "a") as fh:
    fh.write(json.dumps(result) + "\n")

if fit_ok and fitres.success:
    print(f"OK {name}  gamma_0={fitres.gamma_0:.4f}+-{fitres.gamma_0_err:.4f} MHz  "
          f"alpha={fitres.alpha:.2f}+-{fitres.alpha_err:.2f}  redchi={fitres.redchi:.2f}  "
          f"rfi_new={result['rfi']['n_new_auto']} off_acf {acf_off_before:.4f}->{acf_off_after:.4f}")
else:
    print(f"FAIL {name}  {fit_err if not fit_ok else 'did not converge'}")
