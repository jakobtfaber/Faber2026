"""Re-run per-burst ACF+window figures using MANUAL windows / RFI bands from window_choices.json.

Usage:
  FLITS_ROOT=... CHOICES=window_choices.json [ONLY_BURSTS=freya,oran] python3 perburst_acf_manual.py

For each burst in the choices file we:
  - build the de-scalloped spectrum exactly as the auto driver does, BUT force the on/off windows
    from the user's choices (bandpass_normalization uses the user's off-pulse window; falls back to
    the off-burst time-median flat-field when the chosen off window is < 50 bins);
  - mask every fine channel whose center frequency lies in a user-painted RFI band;
  - recompute the 4 equal-S/N sub-band ACFs and re-render the same 3-panel figure.
Outputs <name>_acf_windows_manual.png + perburst_meta_manual.json in $OUT.
"""
from __future__ import annotations
import os, sys, json, copy
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = os.environ["FLITS_ROOT"]
sys.path.insert(0, R + "/scintillation"); sys.path.insert(0, R)
from scint_analysis import freya_scintillation as fs
from scint_analysis import config as config_module
from scint_analysis import analysis as ana

CFG_DIR = R + "/scintillation/configs/bursts"
OUT = os.environ.get("OUT", "/Users/jakobfaber/Developer/scratch/perburst_figs_manual")
os.makedirs(OUT, exist_ok=True)
CHOICES = json.load(open(os.environ["CHOICES"]))
OFF_GREY = "#95a5a6"; ON_BLUE = "#2c74b3"
N_SUB = 4
_MIN_OFF = 50
_only = os.environ.get("ONLY_BURSTS")
BURSTS = _only.split(",") if _only else list(CHOICES.keys())


def force_pc(cfg):
    c = copy.deepcopy(cfg); an = c.setdefault("analysis", {})
    an.setdefault("acf", {})["num_subbands"] = N_SUB; an["acf"]["use_snr_subbanding"] = True
    an.setdefault("grid_regularization", {})["enable"] = True
    an.setdefault("bandpass_normalization", {})["enable"] = True
    return c


def build_manual(name, ch):
    burst_lims = tuple(int(x) for x in ch["burst_lims"])
    off_lims = tuple(int(x) for x in ch["off_lims"])
    rfi_bands = ch.get("rfi_bands_mhz", [])
    cfg_raw = config_module.load_config(f"{CFG_DIR}/{name}_chime.yaml")
    cfg = force_pc(cfg_raw)
    # inject the user's windows so the pipeline's bandpass_normalization / windowing use them
    for blk in ("rfi_masking",):
        cfg["analysis"].setdefault(blk, {})
    cfg["analysis"]["rfi_masking"]["manual_burst_window"] = list(burst_lims)
    cfg["analysis"]["rfi_masking"]["manual_noise_window"] = list(off_lims)

    descallop_method = "off-pulse mean (pipeline bandpass_normalization)"
    off_len = off_lims[1] - off_lims[0]
    use_median = off_len < _MIN_OFF
    if use_median:
        cfg["analysis"]["bandpass_normalization"]["enable"] = False
    spec, bl, ol = fs.prepare_spectrum_from_config(cfg)
    # honor the user's windows regardless of what determine_windows returned
    burst_lims = (int(burst_lims[0]), int(burst_lims[1]))
    off_lims = (int(off_lims[0]), int(off_lims[1]))
    if use_median:
        colmask = np.ones(spec.power.shape[1], bool); colmask[burst_lims[0]:burst_lims[1]] = False
        gain = np.ma.filled(np.ma.median(spec.power[:, colmask], axis=1), np.nan)
        med = np.nanmedian(gain[np.isfinite(gain) & (gain > 0)])
        bad = ~(np.isfinite(gain) & (gain > 1e-3 * med)); g = np.where(bad, 1.0, gain)
        m0 = spec.power.mask if spec.power.mask is not np.ma.nomask else np.zeros(spec.power.shape, bool)
        spec.power = np.ma.MaskedArray(spec.power.data / g[:, None], mask=m0 | bad[:, None])
        descallop_method = "time-median flat-field (off-pulse < 50 bins)"

    # apply user RFI bands: mask channels whose center freq falls in any painted band
    freqs = np.asarray(spec.frequencies, float)
    if rfi_bands:
        chan_bad = np.zeros(freqs.size, bool)
        for f0, f1 in rfi_bands:
            lo, hi = min(f0, f1), max(f0, f1)
            chan_bad |= (freqs >= lo) & (freqs <= hi)
        m = spec.power.mask if spec.power.mask is not np.ma.nomask else np.zeros(spec.power.shape, bool)
        spec.power = np.ma.MaskedArray(spec.power.data, mask=m | chan_bad[:, None])
    return spec, burst_lims, off_lims, descallop_method, rfi_bands


def render(name, ch):
    spec, burst_lims, off_lims, descallop_method, rfi_bands = build_manual(name, ch)
    cw = float(spec.channel_width_mhz)
    P = spec.power; freqs = np.asarray(spec.frequencies, float)
    nchan, ntime = P.shape
    prof = np.ma.mean(P, axis=0).filled(np.nan)

    cfg = force_pc(config_module.load_config(f"{CFG_DIR}/{name}_chime.yaml"))
    try:
        acf_res = ana.calculate_acfs_for_subbands(spec, cfg, burst_lims=burst_lims, noise_desc=None)
    except Exception as e:
        acf_res = {"error": f"{type(e).__name__}: {e}"}

    # RFI diagnostic
    _on = np.ma.filled(spec.get_spectrum(tuple(burst_lims)), np.nan)
    _med = np.nanmedian(_on); _mad = np.nanmedian(np.abs(_on - _med)) * 1.4826
    _z = np.abs((_on - _med) / _mad) if _mad > 0 else np.zeros_like(_on)
    _bright = np.isfinite(_z) & (_z > 8); _tot = np.nansum(np.abs(_on - _med))
    rfi_share = float(np.nansum(np.abs(_on[_bright] - _med)) / _tot) if _tot > 0 else 0.0

    fig = plt.figure(figsize=(12, 7.5))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.25, 1.0], height_ratios=[1, 4], hspace=0.05, wspace=0.22)
    ax_prof = fig.add_subplot(gs[0, 0]); ax_dyn = fig.add_subplot(gs[1, 0], sharex=ax_prof)
    ax_acf = fig.add_subplot(gs[:, 1])
    t = np.arange(ntime)
    ax_prof.plot(t, prof, color="black", lw=0.7)
    ax_prof.axvspan(off_lims[0], off_lims[1], color=OFF_GREY, alpha=0.35, label="off-pulse")
    ax_prof.axvspan(burst_lims[0], burst_lims[1], color=ON_BLUE, alpha=0.35, label="on-pulse")
    ax_prof.set_ylabel("band-avg\npower"); ax_prof.legend(fontsize=7, loc="upper right", ncol=2)
    ax_prof.tick_params(labelbottom=False)
    ax_prof.set_title(f"{name}: MANUAL windows  [de-scalloped: {descallop_method}]", fontsize=9)

    tds = max(1, ntime // 800); fds = max(1, nchan // 400)
    disp = P[: (nchan // fds) * fds, : (ntime // tds) * tds]
    disp = disp.reshape(disp.shape[0] // fds, fds, disp.shape[1] // tds, tds).mean(axis=(1, 3))
    vmin, vmax = np.nanpercentile(disp.filled(np.nan), [5, 97.5])
    cmap = plt.get_cmap("magma").copy(); cmap.set_bad("#1a1a1a")
    ax_dyn.imshow(disp, aspect="auto", origin="lower", extent=[0, ntime, freqs[0], freqs[-1]],
                  vmin=vmin, vmax=vmax, cmap=cmap)
    for xw, col in ((off_lims, OFF_GREY), (burst_lims, ON_BLUE)):
        ax_dyn.axvspan(xw[0], xw[1], color=col, alpha=0.18)
        for x in xw:
            ax_dyn.axvline(x, color=col, lw=1.0, ls="--")
    for f0, f1 in rfi_bands:
        ax_dyn.axhspan(min(f0, f1), max(f0, f1), color="#d62728", alpha=0.18)
    ax_dyn.set_xlabel("time (bins)"); ax_dyn.set_ylabel("frequency (MHz)")
    ax_dyn.yaxis.set_major_locator(plt.MaxNLocator(8))
    _c = "#d62728" if rfi_share > 0.10 else "#2ca02c"
    ax_dyn.text(0.015, 0.985, f"bright-channel share of ACF power: {rfi_share*100:.1f}%",
                transform=ax_dyn.transAxes, va="top", ha="left", fontsize=7.5, color="white",
                bbox=dict(boxstyle="round", fc=_c, ec="none", alpha=0.75))

    cfreqs = acf_res.get("subband_center_freqs_mhz")
    if "error" in acf_res or not acf_res.get("subband_acfs"):
        ax_acf.text(0.5, 0.5, f"ACF unavailable\n{acf_res.get('error','no subbands')}",
                    ha="center", va="center", transform=ax_acf.transAxes)
        cfreqs = []
    else:
        COMB = 0.390625; LAG_MAX = 0.5
        idx_order = list(np.argsort(cfreqs)[::-1])  # high freq at top
        offset = 0.0; step = 1.25; yticks = []; ylabels = []
        for h in range(1, int(LAG_MAX / COMB) + 1):
            ax_acf.axvline(h * COMB, color="0.75", ls=":", lw=0.8, zorder=0)
        for i in idx_order:
            lags = np.asarray(acf_res["subband_lags_mhz"][i], float)
            acf = np.asarray(acf_res["subband_acfs"][i], float)
            i0 = int(np.argmin(np.abs(lags))); a0 = acf[i0]
            if not np.isfinite(a0) or abs(a0) < 1e-30:
                continue
            a = acf / a0; keep = (lags >= 0) & (lags <= LAG_MAX)
            if keep.sum() < 3:
                continue
            base = offset
            ax_acf.plot(lags[keep], a[keep] + base, color="#c0392b", lw=1.1, zorder=3)
            ax_acf.axhline(base, color="0.85", lw=0.5, zorder=1)
            yticks.append(base + 0.5)
            bw = acf_res["subband_num_channels"][i] * acf_res["subband_channel_widths_mhz"][i]
            ylabels.append(f"{cfreqs[i]:.0f} MHz\n({bw:.0f} MHz)")
            offset += step
        ax_acf.set_yticks(yticks); ax_acf.set_yticklabels(ylabels, fontsize=8)
        ax_acf.set_xlim(0, LAG_MAX); ax_acf.set_xlabel("frequency lag (MHz)")
        ax_acf.set_title("equal-S/N sub-band ACFs (lag-0 = 1)\nhigh freq at top; dotted = 0.39 MHz comb",
                         fontsize=10)
    fig.savefig(f"{OUT}/{name}_acf_windows_manual.png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    return dict(name=name, burst_lims=list(burst_lims), off_lims=list(off_lims),
                cw_khz=round(cw * 1e3, 3), nchan=int(nchan), ntime=int(ntime),
                descallop_method=descallop_method, rfi_bands_mhz=rfi_bands,
                rfi_acf_power_share=round(rfi_share, 4),
                subband_center_freqs_mhz=[round(float(x), 1) for x in (cfreqs or [])])


meta = []
for name in BURSTS:
    if name not in CHOICES:
        print(f"  {name} not in choices, skip"); continue
    try:
        meta.append(render(name, CHOICES[name])); print(f"OK {name}")
    except Exception as e:
        print(f"ERR {name}: {type(e).__name__}: {e}")
with open(f"{OUT}/perburst_meta_manual.json", "w") as fh:
    json.dump(meta, fh, indent=1)
print(f"WROTE {OUT}/perburst_meta_manual.json")
