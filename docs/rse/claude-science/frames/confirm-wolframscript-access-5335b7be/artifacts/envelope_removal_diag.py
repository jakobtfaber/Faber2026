"""Envelope-removal scintillation diagnostic, ONE burst per process.

For $ONE_BURST (windows/RFI bands from $CHOICES), build the de-scalloped spectrum with the manual
windows, mask user RFI bands on top of the pipeline mask, then per equal-S/N subband compare:
  - raw on-pulse frequency ACF
  - envelope-removed on-pulse ACF (divide spectrum by a running-median envelope over HP_WIN channels)
  - off-pulse noise ACF (median over non-overlapping burst-width chunks of the off window)
Writes <name>_env_diag.png + appends a row to $OUT/env_diag_results.jsonl:
  {name, subbands:[{center_mhz, cw_khz, nchan, raw_lag15, hp_lag15, off_lag15, on_off_ratio,
                    hp_dnu_1e_mhz, plateau_flag}]}
plateau_flag = raw ACF stays > 0.5*raw[lag1] out to the max lag (never rolls over) -> envelope-dominated.
"""
from __future__ import annotations
import os, sys, json, copy
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.ndimage import median_filter

R = os.environ["FLITS_ROOT"]; sys.path.insert(0, R + "/scintillation"); sys.path.insert(0, R)
from scint_analysis import freya_scintillation as fs
from scint_analysis import config as config_module
from scint_analysis import analysis as ana

name = os.environ["ONE_BURST"]
CH = json.load(open(os.environ["CHOICES"]))[name]
OUT = os.environ.get("OUT", "/Users/jakobfaber/Developer/scratch/env_diag")
os.makedirs(OUT, exist_ok=True)
burst = tuple(int(x) for x in CH["burst_lims"]); off = tuple(int(x) for x in CH["off_lims"])
bands = CH.get("rfi_bands_mhz", [])
HP_MHZ = 5.0            # envelope smoothing scale: reveals scintles NARROWER than this
_MIN_OFF = 50


def force_pc(cfg):
    c = copy.deepcopy(cfg); an = c.setdefault("analysis", {})
    an.setdefault("acf", {})["num_subbands"] = 4; an["acf"]["use_snr_subbanding"] = True
    an.setdefault("grid_regularization", {})["enable"] = True
    an.setdefault("bandpass_normalization", {})["enable"] = True
    an.setdefault("rfi_masking", {})["manual_burst_window"] = list(burst)
    an["rfi_masking"]["manual_noise_window"] = list(off)
    return c


cfg = force_pc(config_module.load_config(f"{R}/scintillation/configs/bursts/{name}_chime.yaml"))
use_median = (off[1] - off[0]) < _MIN_OFF
if use_median:
    cfg["analysis"]["bandpass_normalization"]["enable"] = False
spec, bl, ol = fs.prepare_spectrum_from_config(cfg)
if use_median:
    colmask = np.ones(spec.power.shape[1], bool); colmask[burst[0]:burst[1]] = False
    gain = np.ma.filled(np.ma.median(spec.power[:, colmask], axis=1), np.nan)
    med = np.nanmedian(gain[np.isfinite(gain) & (gain > 0)])
    bad = ~(np.isfinite(gain) & (gain > 1e-3 * med)); g = np.where(bad, 1.0, gain)
    m0 = spec.power.mask if spec.power.mask is not np.ma.nomask else np.zeros(spec.power.shape, bool)
    spec.power = np.ma.MaskedArray(spec.power.data / g[:, None], mask=m0 | bad[:, None])
freqs = np.asarray(spec.frequencies, float)
if bands:
    bad = np.zeros(freqs.size, bool)
    for f0, f1 in bands:
        bad |= (freqs >= min(f0, f1)) & (freqs <= max(f0, f1))
    m = spec.power.mask if spec.power.mask is not np.ma.nomask else np.zeros(spec.power.shape, bool)
    spec.power = np.ma.MaskedArray(spec.power.data, mask=m | bad[:, None])

res = ana.calculate_acfs_for_subbands(spec, cfg, burst_lims=burst, noise_desc=None)
cf = res["subband_center_freqs_mhz"]; sl = res["subband_channel_slices"]
cw = float(res["subband_channel_widths_mhz"][0])   # MHz/channel
P = spec.power
HP_WIN = max(11, int(round(HP_MHZ / cw)) | 1)       # odd window in channels


def acf1d(x1d):
    x = x1d - np.ma.mean(x1d); x = np.ma.filled(x, 0.0); n = x.size
    ac = np.correlate(x, x, mode="full")[n - 1:]
    return ac / ac[0] if ac[0] != 0 else ac


def highpass(x1d):
    filled = np.ma.filled(x1d, np.ma.median(x1d))
    env = median_filter(filled, size=HP_WIN, mode="nearest")
    return np.ma.MaskedArray(filled / np.where(env == 0, 1, env), mask=np.ma.getmaskarray(x1d))


onw = burst[1] - burst[0]
offchunks = [(s, s + onw) for s in range(off[0], off[1] - onw, onw)] if (off[1] - off[0]) > onw else []
order = list(np.argsort(cf)[::-1])
NL = 60
fig, axes = plt.subplots(len(order), 1, figsize=(8, 2.4 * len(order)), sharex=True)
if len(order) == 1:
    axes = [axes]
rows = []
for ax, i in zip(axes, order):
    s = sl[i]; sub = P[s[0]:s[1], :] if isinstance(s, (list, tuple)) else P[s, :]
    on_spec = np.ma.mean(sub[:, burst[0]:burst[1]], axis=1)
    a_raw = acf1d(on_spec); a_hp = acf1d(highpass(on_spec))
    offr = None
    if offchunks:
        acc = [acf1d(np.ma.mean(sub[:, a:b], axis=1)) for a, b in offchunks]
        acc = [o[:NL] for o in acc if o.size >= NL]
        if acc:
            offr = np.median(np.array(acc), axis=0)
    lags = np.arange(a_raw.size) * cw
    L = slice(1, NL)
    ax.plot(lags[L], a_raw[L], color="#c0392b", lw=1.2, label="on-pulse (raw)")
    ax.plot(lags[L], a_hp[L], color="#2c74b3", lw=1.2, label="on-pulse (envelope removed)")
    if offr is not None:
        ax.plot(lags[1:NL], offr[1:NL], color="#888", lw=1.0, ls="--", label="off-pulse (noise)")
    ax.axhline(0, color="k", lw=0.4); ax.set_ylim(-0.05, max(0.5, float(np.nanmax(a_raw[L])) * 1.1))
    ax.set_ylabel(f"{cf[i]:.0f} MHz\nACF", fontsize=8)
    # metrics
    raw15 = float(a_raw[1:6].mean()); hp15 = float(a_hp[1:6].mean())
    off15 = float(offr[1:6].mean()) if offr is not None else float("nan")
    below = np.where(a_hp[1:NL] < a_hp[1] / np.e)[0]
    hp_dnu = float(below[0] * cw) if below.size else float("nan")
    # plateau: raw ACF never drops below half its lag-1 value within the window
    plateau = bool(np.all(a_raw[1:NL] > 0.5 * a_raw[1]))
    on_off = float(raw15 / off15) if (offr is not None and off15) else float("nan")
    rows.append(dict(center_mhz=round(float(cf[i]), 1), cw_khz=round(cw * 1e3, 2),
                     nchan=int(res["subband_num_channels"][i]),
                     raw_lag15=round(raw15, 4), hp_lag15=round(hp15, 4), off_lag15=round(off15, 4),
                     on_off_ratio=round(on_off, 1) if np.isfinite(on_off) else None,
                     hp_dnu_1e_mhz=round(hp_dnu, 4) if np.isfinite(hp_dnu) else None,
                     plateau_flag=plateau))
axes[0].legend(fontsize=7, loc="upper right")
axes[-1].set_xlabel("frequency lag (MHz)")
axes[0].set_title(f"{name}: subband ACFs — raw vs envelope-removed (HP {HP_MHZ:.0f} MHz) vs off-pulse noise",
                  fontsize=10)
fig.tight_layout()
fig.savefig(f"{OUT}/{name}_env_diag.png", dpi=125, bbox_inches="tight")
plt.close(fig)
with open(f"{OUT}/env_diag_results.jsonl", "a") as fh:
    fh.write(json.dumps(dict(name=name, descallop="median" if use_median else "pipe",
                             hp_win_ch=HP_WIN, subbands=rows)) + "\n")
print(f"OK {name}  " + " | ".join(
    f"{r['center_mhz']:.0f}MHz raw{r['raw_lag15']:.2f} hp{r['hp_lag15']:.2f} "
    f"off{r['off_lag15']:.3f} {'PLATEAU' if r['plateau_flag'] else 'decays'}" for r in rows))
