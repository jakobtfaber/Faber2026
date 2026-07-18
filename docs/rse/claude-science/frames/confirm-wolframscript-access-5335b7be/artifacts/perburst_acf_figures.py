"""Per-burst CHIME diagnostic figures:
  (left)  dynamic spectrum with the on-pulse and off-pulse time windows marked, + time profile;
  (right) the 4 equal-S/N sub-band ACFs stacked vertically in frequency (400-800 MHz).

Sub-bands use the pipeline's OWN equal-S/N partition (analysis.calculate_acfs_for_subbands with
num_subbands=4, use_snr_subbanding=True): channels are split so each sub-band holds an equal share
of the burst-integrated signal -> equivalent S/N per sub-band, not equal bandwidth.
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

BURSTS = ["casey", "whitney", "phineas", "mahi", "freya", "zach",
          "chromatica", "wilhelm", "oran", "hamilton", "johndoeII", "isha"]
_only = os.environ.get("ONLY_BURSTS")
if _only:
    BURSTS = _only.split(",")
CFG_DIR = R + "/scintillation/configs/bursts"
OUT = "/Users/jakobfaber/Developer/scratch/perburst_figs"
os.makedirs(OUT, exist_ok=True)
CH_RED = "#c0392b"; OFF_GREY = "#95a5a6"; ON_BLUE = "#2c74b3"

N_SUB = 4


def force_provenance_complete(cfg):
    """Config copy with the de-scalloping ENABLED and 4 equal-S/N sub-bands.

    The 0.39 MHz coarse-channel scallop is a MULTIPLICATIVE PFB bandpass ripple; it is removed by
    bandpass_normalization (divide each fine channel by its off-pulse mean). The stock _chime.yaml
    configs are diagnostic_only (bandpass_normalization OFF) — that is why the comb survives. Turn
    it on, plus grid_regularization (uniform lag axis; casey ships with it off).
    """
    c = copy.deepcopy(cfg)
    an = c.setdefault("analysis", {})
    an.setdefault("acf", {})
    an["acf"]["num_subbands"] = N_SUB
    an["acf"]["use_snr_subbanding"] = True
    an.setdefault("grid_regularization", {})["enable"] = True
    an.setdefault("bandpass_normalization", {})["enable"] = True
    return c


def make_figure(name):
    cfg_raw = config_module.load_config(f"{CFG_DIR}/{name}_chime.yaml")
    cfg = force_provenance_complete(cfg_raw)
    descalloped = True
    descallop_method = "off-pulse mean (pipeline bandpass_normalization)"
    try:
        spec, burst_lims, off_lims = fs.prepare_spectrum_from_config(cfg)
    except ValueError as e:
        # off-pulse window too short for the pipeline's off-pulse-mean flat-field (wide bursts).
        # The PFB scallop is a STATIC (time-independent), MULTIPLICATIVE per-channel gain, so a
        # robust per-channel TIME-MEDIAN over the whole record divides it out just as well — the
        # burst occupies few time bins, so the median tracks the off-burst bandpass. Apply that
        # manually so these bursts are de-scalloped too (documented, distinct from the pipeline path).
        cfg2 = force_provenance_complete(cfg_raw)
        cfg2["analysis"]["bandpass_normalization"]["enable"] = False
        spec, burst_lims, off_lims = fs.prepare_spectrum_from_config(cfg2)
        # per-channel time-median EXCLUDING the on-pulse columns, so a wide burst (e.g. oran,
        # 74 ms, fills ~half the record) does not bias the gain estimate and leave residual comb.
        colmask = np.ones(spec.power.shape[1], bool)
        colmask[burst_lims[0]:burst_lims[1]] = False
        offcols = spec.power[:, colmask]
        gain = np.ma.median(offcols, axis=1)                          # per-channel, off-burst time-median
        gain = np.ma.filled(gain, np.nan)
        med = np.nanmedian(gain[np.isfinite(gain) & (gain > 0)])
        bad = ~(np.isfinite(gain) & (gain > 1e-3 * med))
        g = np.where(bad, 1.0, gain)
        newp = spec.power.data / g[:, None]
        newmask = (spec.power.mask if spec.power.mask is not np.ma.nomask else np.zeros(spec.power.shape, bool)) | bad[:, None]
        spec.power = np.ma.MaskedArray(newp, mask=newmask)
        descallop_method = "time-median flat-field (off-pulse < 50 bins)"
        print(f"  [{name}] fell back to time-median flat-field: {e}")
    cw = float(spec.channel_width_mhz)
    P = spec.power                                   # (nchan, ntime) masked
    freqs = np.asarray(spec.frequencies, float)      # ascending MHz
    nchan, ntime = P.shape

    # time profile (band-averaged) to show where the burst sits
    prof = np.ma.mean(P, axis=0).filled(np.nan)

    # equal-S/N sub-band ACFs via the pipeline's own routine (cfg already provenance-complete)
    try:
        acf_res = ana.calculate_acfs_for_subbands(spec, cfg, burst_lims=burst_lims, noise_desc=None)
    except Exception as e:
        acf_res = {"error": f"{type(e).__name__}: {e}"}

    # ---- RFI diagnostic: what fraction of the on-pulse ACF power comes from bright (|z|>8) channels ----
    # (persistent narrowband RFI normalizes to ~1 under the flat-field, so this is what the ACF actually sees)
    _on = np.ma.filled(spec.get_spectrum(tuple(burst_lims)), np.nan)
    _med = np.nanmedian(_on); _mad = np.nanmedian(np.abs(_on - _med)) * 1.4826
    _z = np.abs((_on - _med) / _mad) if _mad > 0 else np.zeros_like(_on)
    _bright = np.isfinite(_z) & (_z > 8)
    _tot = np.nansum(np.abs(_on - _med))
    rfi_share = float(np.nansum(np.abs(_on[_bright] - _med)) / _tot) if _tot > 0 else 0.0

    # ---- figure ----
    fig = plt.figure(figsize=(12, 7.5))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.25, 1.0], height_ratios=[1, 4],
                          hspace=0.05, wspace=0.22)
    ax_prof = fig.add_subplot(gs[0, 0])
    ax_dyn = fig.add_subplot(gs[1, 0], sharex=ax_prof)
    ax_acf = fig.add_subplot(gs[:, 1])

    # ---- time profile ----
    t = np.arange(ntime)
    ax_prof.plot(t, prof, color="black", lw=0.7)
    ax_prof.axvspan(off_lims[0], off_lims[1], color=OFF_GREY, alpha=0.35, label="off-pulse")
    ax_prof.axvspan(burst_lims[0], burst_lims[1], color=ON_BLUE, alpha=0.35, label="on-pulse")
    ax_prof.set_ylabel("band-avg\npower"); ax_prof.legend(fontsize=7, loc="upper right", ncol=2)
    ax_prof.tick_params(labelbottom=False)
    ax_prof.set_title(f"{name}: dynamic spectrum + windows  [de-scalloped: {descallop_method}]", fontsize=9)

    # ---- dynamic spectrum (downsample time for display) ----
    tds = max(1, ntime // 800); fds = max(1, nchan // 400)
    disp = P[: (nchan // fds) * fds, : (ntime // tds) * tds]
    disp = disp.reshape(disp.shape[0] // fds, fds, disp.shape[1] // tds, tds).mean(axis=(1, 3))
    vmin, vmax = np.nanpercentile(disp.filled(np.nan), [5, 97.5])
    cmap = plt.get_cmap("magma").copy(); cmap.set_bad("#1a1a1a")   # masked -> dark, not white
    ax_dyn.imshow(disp, aspect="auto", origin="lower",
                  extent=[0, ntime, freqs[0], freqs[-1]], vmin=vmin, vmax=vmax, cmap=cmap)
    for xw, col in ((off_lims, OFF_GREY), (burst_lims, ON_BLUE)):
        ax_dyn.axvspan(xw[0], xw[1], color=col, alpha=0.18)
        for x in xw:
            ax_dyn.axvline(x, color=col, lw=1.0, ls="--")
    ax_dyn.set_xlabel("time (bins)"); ax_dyn.set_ylabel("frequency (MHz)")
    ax_dyn.yaxis.set_major_locator(plt.MaxNLocator(8))   # avoid MAXTICKS blow-up on huge freq extents
    _rfi_col = "#d62728" if rfi_share > 0.10 else "#2ca02c"
    ax_dyn.text(0.015, 0.985, f"bright-channel (|z|>8) share of ACF power: {rfi_share*100:.1f}%",
                transform=ax_dyn.transAxes, va="top", ha="left", fontsize=7.5, color="white",
                bbox=dict(boxstyle="round", fc=_rfi_col, ec="none", alpha=0.75))

    # ---- 4 equal-S/N sub-band ACFs stacked vertically in frequency ----
    if "error" in acf_res or not acf_res.get("subband_acfs"):
        ax_acf.text(0.5, 0.5, f"ACF unavailable\n{acf_res.get('error','no subbands')}",
                    ha="center", va="center", transform=ax_acf.transAxes)
    else:
        cfreqs = acf_res["subband_center_freqs_mhz"]
        COMB = 0.390625                        # upchannelization coarse-channel comb period (MHz)
        LAG_MAX = 0.5                          # zoom: show scintillation decay + first comb peak
        # stack high-freq at TOP: sort descending by center freq
        idx = list(np.argsort(cfreqs)[::-1])
        offset = 0.0; step = 1.25; yticks = []; ylabels = []
        panel_meta = []
        # comb harmonics as faint vertical guides
        for h in range(1, int(LAG_MAX / COMB) + 1):
            ax_acf.axvline(h * COMB, color="0.75", ls=":", lw=0.8, zorder=0)
        for rank, i in enumerate(idx):
            lags = np.asarray(acf_res["subband_lags_mhz"][i], float)
            acf = np.asarray(acf_res["subband_acfs"][i], float)
            # normalize each panel to lag-0 = 1 (scintillation = initial decay from 1)
            i0 = int(np.argmin(np.abs(lags)))
            a0 = acf[i0]
            if not np.isfinite(a0) or abs(a0) < 1e-30:
                continue
            a = acf / a0
            keep = (lags >= 0) & (lags <= LAG_MAX)
            if keep.sum() < 3:
                continue
            base = offset
            ax_acf.plot(lags[keep], a[keep] + base, color=CH_RED, lw=1.1, zorder=3)
            ax_acf.axhline(base, color="0.85", lw=0.5, zorder=1)
            yticks.append(base + 0.5)
            nchan_i = acf_res["subband_num_channels"][i]
            cwid = acf_res["subband_channel_widths_mhz"][i] * 1e3
            bw = nchan_i * acf_res["subband_channel_widths_mhz"][i]
            ylabels.append(f"{cfreqs[i]:.0f} MHz\n({bw:.0f} MHz)")
            panel_meta.append(dict(center_mhz=round(float(cfreqs[i]),1), n_chan=int(nchan_i),
                                   chan_width_khz=round(float(cwid),2), bw_mhz=round(float(bw),2),
                                   slice=acf_res["subband_channel_slices"][i]))
            offset += step
        ax_acf.set_yticks(yticks); ax_acf.set_yticklabels(ylabels, fontsize=8)
        ax_acf.set_xlabel("frequency lag (MHz)")
        ax_acf.set_xlim(0, LAG_MAX)
        ax_acf.set_title("equal-S/N sub-band ACFs (lag-0 = 1)\nhigh freq at top; dotted = 0.39 MHz comb", fontsize=10)
        acf_res["_panel_meta"] = panel_meta

    fig.savefig(f"{OUT}/{name}_acf_windows.png", dpi=140, bbox_inches="tight")
    plt.close(fig)
    # save a compact per-burst metadata record
    meta = dict(name=name, burst_lims=list(burst_lims), off_lims=list(off_lims),
                cw_khz=round(cw * 1e3, 3), nchan=int(nchan), ntime=int(ntime),
                descalloped=True, descallop_method=descallop_method,
                rfi_acf_power_share=round(rfi_share, 4),
                subband_meta=acf_res.get("_panel_meta", acf_res.get("error")))
    return meta


all_meta = {}
for b in BURSTS:
    try:
        all_meta[b] = make_figure(b)
        print(f"OK {b}")
    except Exception as e:
        import traceback
        all_meta[b] = {"error": f"{type(e).__name__}: {e}", "tb": traceback.format_exc()[-400:]}
        print(f"ERR {b}: {e}")

json.dump(all_meta, open(f"{OUT}/perburst_meta.json", "w"), indent=2)
print("WROTE", f"{OUT}/perburst_meta.json")
