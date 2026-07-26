"""Twelve-burst pre-ratification RFI visual packet.

Renders raw (un-cleaned) _cntr_bpc dynamic spectra, CHIME + DSA side by
side per burst, with per-channel robust normalization so narrowband RFI
is visible. Applied DM comes from the filename stem (these products are
per-instrument dedispersed; see CHIME-products-carry-CHIME-optimized-DMs).
"""
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HOME = Path.home()
CH_DIR = HOME / "Data/Faber2026/chimefrb/CHIME_bursts"
DS_DIR = HOME / "Data/Faber2026/dsa110/DSA_bursts"
OUT = Path(__file__).parent / "rfi_packet"
OUT.mkdir(exist_ok=True)

# telescopes.yaml (dsa110-FLITS scattering/configs): raw params
BAND = {
    "chime": dict(fmin=400.19, fmax=800.19, dt_ms=2.56e-3, tbin=16, fbin=2),
    "dsa": dict(fmin=1311.25, fmax=1498.75, dt_ms=32.768e-3, tbin=2, fbin=8),
}


def parse_dm(path):
    # e.g. zach_chime_I_262_3621_32000b -> 262.3621 ; zach_dsa_I_262_368_2500b -> 262.368
    m = re.match(r"(\w+?)_(chime|dsa)_I_(\d+)_(\d+)_", path.name)
    return m.group(1), m.group(2), float(f"{m.group(3)}.{m.group(4)}")


def prep(path, inst):
    p = BAND[inst]
    a = np.load(path, mmap_mode="r").astype(np.float32)
    nf, nt = a.shape
    a = a[: nf - nf % p["fbin"], : nt - nt % p["tbin"]]
    a = a.reshape(nf // p["fbin"], p["fbin"], -1, p["tbin"]).mean(axis=(1, 3))
    med = np.nanmedian(a, axis=1, keepdims=True)
    mad = np.nanmedian(np.abs(a - med), axis=1, keepdims=True)
    mad[mad == 0] = np.nan
    z = (a - med) / (1.4826 * mad)
    z = np.nan_to_num(z, nan=0.0)
    z = z[::-1]  # row 0 = f_max on disk -> flip to ascending
    span_ms = a.shape[1] * p["tbin"] * p["dt_ms"]
    return z, span_ms


def panel(ax, z, span, inst, dm):
    p = BAND[inst]
    vmax = np.percentile(z, 99.5)
    ax.imshow(
        z, aspect="auto", origin="lower", cmap="magma",
        vmin=-2, vmax=max(vmax, 3),
        extent=[-span / 2, span / 2, p["fmin"], p["fmax"]],
        interpolation="nearest",
    )
    ax.set_title(f"{inst.upper()}  (applied DM {dm:g} pc cm$^{{-3}}$)", fontsize=10)
    ax.set_xlabel("time [ms]")
    ax.set_ylabel("frequency [MHz]")


bursts = sorted(parse_dm(f)[0] for f in CH_DIR.glob("*_cntr_bpc.npy"))
print("bursts:", bursts)
for name in bursts:
    ch = next(CH_DIR.glob(f"{name}_chime_I_*_cntr_bpc.npy"))
    ds = next(DS_DIR.glob(f"{name}_dsa_I_*_cntr_bpc.npy"))
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    for ax, path, inst in ((axes[0], ch, "chime"), (axes[1], ds, "dsa")):
        _, _, dm = parse_dm(path)
        z, span = prep(path, inst)
        panel(ax, z, span, inst, dm)
    fig.suptitle(
        f"{name} — raw _cntr_bpc dynamic spectra (no RFI cleaning applied); "
        "per-channel robust z-score", fontsize=12,
    )
    fig.tight_layout()
    fig.savefig(OUT / f"{name}_rfi_packet.png", dpi=140)
    plt.close(fig)
    print("rendered", name)
print("done ->", OUT)
