"""Generate compact display assets for the interactive window/RFI tool, ONE burst per process.

For the burst named in $ONE_BURST, write to $ASSET_DIR:
  <name>_disp.png   : de-scalloped dynamic spectrum, magma, origin-lower, display-downsampled
  <name>_disp.json  : {name, ntime, nchan, fmin, fmax, ntime_disp, nchan_disp,
                       profile (len ntime_disp), burst_lims, off_lims, descallop_method,
                       vmin, vmax}
Coordinates: PNG spans the FULL data range (col 0 -> t=0, last col -> t=ntime; row 0 -> fmin).
The browser maps a fractional x in [0,1] to bin = round(frac*ntime), fractional y to
freq = fmin + frac*(fmax-fmin). Windows are stored in FULL time bins.
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

CFG_DIR = R + "/scintillation/configs/bursts"
ASSET_DIR = os.environ.get("ASSET_DIR", "/Users/jakobfaber/Developer/scratch/window_tool_assets")
os.makedirs(ASSET_DIR, exist_ok=True)
name = os.environ["ONE_BURST"]

NDISP_T = 900      # display columns (time)
NDISP_F = 500      # display rows (freq)


def force_pc(cfg):
    c = copy.deepcopy(cfg); an = c.setdefault("analysis", {})
    an.setdefault("acf", {})["num_subbands"] = 4; an["acf"]["use_snr_subbanding"] = True
    an.setdefault("grid_regularization", {})["enable"] = True
    an.setdefault("bandpass_normalization", {})["enable"] = True
    return c


cfg_raw = config_module.load_config(f"{CFG_DIR}/{name}_chime.yaml")
cfg = force_pc(cfg_raw)
descallop_method = "off-pulse mean (pipeline bandpass_normalization)"
try:
    spec, burst_lims, off_lims = fs.prepare_spectrum_from_config(cfg)
except ValueError as e:
    cfg2 = force_pc(cfg_raw); cfg2["analysis"]["bandpass_normalization"]["enable"] = False
    spec, burst_lims, off_lims = fs.prepare_spectrum_from_config(cfg2)
    colmask = np.ones(spec.power.shape[1], bool); colmask[burst_lims[0]:burst_lims[1]] = False
    gain = np.ma.filled(np.ma.median(spec.power[:, colmask], axis=1), np.nan)
    med = np.nanmedian(gain[np.isfinite(gain) & (gain > 0)])
    bad = ~(np.isfinite(gain) & (gain > 1e-3 * med)); g = np.where(bad, 1.0, gain)
    m0 = spec.power.mask if spec.power.mask is not np.ma.nomask else np.zeros(spec.power.shape, bool)
    spec.power = np.ma.MaskedArray(spec.power.data / g[:, None], mask=m0 | bad[:, None])
    descallop_method = "time-median flat-field (off-pulse < 50 bins)"

P = spec.power
freqs = np.asarray(spec.frequencies, float)
nchan, ntime = P.shape
fmin, fmax = float(freqs.min()), float(freqs.max())

# band-averaged profile at full time resolution, then downsample for display
prof_full = np.ma.mean(P, axis=0).filled(np.nan)

# display downsample (block-mean); keep masked cells for set_bad rendering
tds = max(1, ntime // NDISP_T); fds = max(1, nchan // NDISP_F)
disp = P[: (nchan // fds) * fds, : (ntime // tds) * tds]
disp = disp.reshape(disp.shape[0] // fds, fds, disp.shape[1] // tds, tds).mean(axis=(1, 3))
ntime_disp = disp.shape[1]; nchan_disp = disp.shape[0]

# profile at display resolution
pf = prof_full[: (ntime // tds) * tds].reshape(-1, tds)
prof_disp = np.nanmean(pf, axis=1)

vmin, vmax = np.nanpercentile(disp.filled(np.nan), [5, 97.5])
cmap = plt.get_cmap("magma").copy(); cmap.set_bad("#1a1a1a")
plt.imsave(f"{ASSET_DIR}/{name}_disp.png", disp.filled(np.nan),
           cmap=cmap, vmin=vmin, vmax=vmax, origin="lower")

meta = dict(name=name, ntime=int(ntime), nchan=int(nchan), fmin=fmin, fmax=fmax,
            ntime_disp=int(ntime_disp), nchan_disp=int(nchan_disp),
            profile=[None if not np.isfinite(x) else round(float(x), 6) for x in prof_disp],
            burst_lims=[int(burst_lims[0]), int(burst_lims[1])],
            off_lims=[int(off_lims[0]), int(off_lims[1])],
            descallop_method=descallop_method,
            vmin=float(vmin), vmax=float(vmax))
with open(f"{ASSET_DIR}/{name}_disp.json", "w") as fh:
    json.dump(meta, fh)
print(f"OK {name}  ntime={ntime} nchan={nchan} disp=({nchan_disp}x{ntime_disp}) "
      f"burst={burst_lims} off={off_lims}")
