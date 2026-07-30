"""Zach DSA-110 profile at native 32.768 us versus adjacent-pair 65.536 us.

One archival product, one frequency averaging, one window. The only thing that
differs between the two arms is the time factor. Writes a figure and a JSON
receipt so the numbers are checkable rather than asserted.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")

ANALYSIS = Path(sys.argv[1])
OUT = Path(sys.argv[2])
INPUT = Path(
    "~/Data/Faber2026/dsa110/DSA_bursts/zach_dsa_I_262_368_2500b_cntr_bpc.npy"
).expanduser()

# The producer is imported by bare name, so the analysis scripts directory must
# be on sys.path before the import; ruff's ordering rule cannot express that.
sys.path.insert(0, str(ANALYSIS / "scripts"))
from plot_codetection_gallery import BANDS, load_band  # noqa: E402

matplotlib.rcParams.update({"font.family": "DejaVu Sans", "mathtext.fontset": "dejavusans"})
import matplotlib.pyplot as plt  # noqa: E402

DT_NATIVE_MS = BANDS["dsa"]["dt_ms"]  # 32.768 us


def profile(t_factor: int) -> np.ndarray:
    """Band-summed time profile at the requested time factor, nothing else changed."""
    band = dict(BANDS["dsa"], f_factor=BANDS["dsa"]["f_factor"], t_factor=t_factor)
    _, prof = load_band(INPUT, band, telescope="dsa")
    return np.asarray(prof, float)


def peak_window(prof: np.ndarray, dt_ms: float, half_ms: float = 6.0):
    peak = int(np.nanargmax(prof))
    half = max(1, int(round(half_ms / dt_ms)))
    lo, hi = max(0, peak - half), min(prof.size, peak + half + 1)
    return lo, hi, peak


native = profile(1)
coarse = profile(2)

# The averaging identity: does the t_factor 2 array equal the adjacent-pair mean
# of the t_factor 1 array? This is arithmetic, not evidence about blending.
n = (native.size // 2) * 2
pairmean = native[:n].reshape(-1, 2).mean(axis=1)
m = min(pairmean.size, coarse.size)
identity_max_abs = float(np.nanmax(np.abs(pairmean[:m] - coarse[:m])))

# Normalise each arm by its own off-pulse statistics so the comparison is about
# structure, not scale.
lo_n, hi_n, pk_n = peak_window(native, DT_NATIVE_MS)
lo_c, hi_c, pk_c = peak_window(coarse, DT_NATIVE_MS * 2)


def offpulse_sigma(prof, lo, hi):
    mask = np.ones(prof.size, bool)
    mask[lo:hi] = False
    return float(np.nanstd(prof[mask])), float(np.nanmean(prof[mask]))


sig_n, mu_n = offpulse_sigma(native, lo_n, hi_n)
sig_c, mu_c = offpulse_sigma(coarse, lo_c, hi_c)
snr_native = (native - mu_n) / sig_n
snr_coarse = (coarse - mu_c) / sig_c


# Component structure: count local maxima above 5 sigma inside the on-pulse
# window, which is the property the owner decision actually turns on.
def peaks_above(snr, lo, hi, thresh=5.0):
    seg = snr[lo:hi]
    idx = [
        i
        for i in range(1, seg.size - 1)
        if seg[i] > thresh and seg[i] >= seg[i - 1] and seg[i] > seg[i + 1]
    ]
    return [(int(i + lo), float(seg[i])) for i in idx]


pk_native = peaks_above(snr_native, lo_n, hi_n)
pk_coarse = peaks_above(snr_coarse, lo_c, hi_c)

t_native = (np.arange(native.size) - pk_n) * DT_NATIVE_MS
t_coarse = (np.arange(coarse.size) - pk_c) * DT_NATIVE_MS * 2

receipt = {
    "input": str(INPUT),
    "input_sha256": hashlib.sha256(INPUT.read_bytes()).hexdigest(),
    "held_identical": {
        "f_factor": BANDS["dsa"]["f_factor"],
        "telescope": "dsa",
        "loader": "plot_codetection_gallery.load_band",
        "residual_dm": 0.0,
    },
    "arms": {
        "native": {
            "t_factor": 1,
            "dt_us": DT_NATIVE_MS * 1e3,
            "samples": int(native.size),
            "peak_snr": float(np.nanmax(snr_native)),
            "offpulse_sigma": sig_n,
            "components_above_5sigma": len(pk_native),
        },
        "adjacent_pair": {
            "t_factor": 2,
            "dt_us": DT_NATIVE_MS * 2e3,
            "samples": int(coarse.size),
            "peak_snr": float(np.nanmax(snr_coarse)),
            "offpulse_sigma": sig_c,
            "components_above_5sigma": len(pk_coarse),
        },
    },
    "components": {
        "native_ms_from_peak_and_snr": [
            [round(float((i - pk_n) * DT_NATIVE_MS), 3), round(v, 1)] for i, v in pk_native
        ],
        "adjacent_pair_ms_from_peak_and_snr": [
            [round(float((i - pk_c) * DT_NATIVE_MS * 2), 3), round(v, 1)] for i, v in pk_coarse
        ],
    },
    "raw_peak_amplitude": {
        "native": float(np.nanmax(native)),
        "adjacent_pair": float(np.nanmax(coarse)),
        "ratio_coarse_over_native": float(np.nanmax(coarse) / np.nanmax(native)),
    },
    "averaging_identity_max_abs_difference": identity_max_abs,
    "averaging_identity_note": (
        "NOT round-off. The coarse arm differs from a literal adjacent-pair mean "
        "of the native arm by a near-constant 0.0997, about 0.37 off-pulse sigma, "
        "so load_band's t_factor path is not a bare pairwise average. A previously "
        "claimed 2.22e-15 identity is not reproducible through this production "
        "loader; it presumably came from an independent averaging step rather than "
        "from the path the fits actually use."
    ),
    "component_structure_differs": len(pk_native) != len(pk_coarse),
    "peak_snr_ratio_coarse_over_native": float(np.nanmax(snr_coarse) / np.nanmax(snr_native)),
}

fig, axes = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
for ax, t, snr, lab, marks in (
    (axes[0], t_native, snr_native, "native, 32.768 us", pk_native),
    (axes[1], t_coarse, snr_coarse, "adjacent-pair, 65.536 us", pk_coarse),
):
    ax.step(t, snr, where="mid", lw=0.9)
    ax.axhline(5.0, ls="--", lw=0.7, color="0.5")
    for i, v in marks:
        ax.plot(t[i], v, "v", ms=6, color="crimson")
    ax.set_ylabel("signal to noise")
    ax.set_xlim(-6, 6)
    ax.text(0.02, 0.88, f"{lab}: {len(marks)} components above 5 sigma", transform=ax.transAxes)
axes[1].set_xlabel("time from peak (ms)")
fig.tight_layout()

OUT.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT / "zach_dsa_resolution_comparison.pdf")
fig.savefig(OUT / "zach_dsa_resolution_comparison.png", dpi=150)
(OUT / "zach_dsa_resolution_comparison.json").write_text(
    json.dumps(receipt, indent=2, sort_keys=True) + "\n"
)
print(json.dumps(receipt, indent=2, sort_keys=True))
