"""Independent re-derivation of the native-versus-averaged component count.

Deliberately shares no code with compare_resolution.py: it reads the archival
array directly, does its own dead-channel handling and its own block averaging,
defines the off-pulse baseline once in native time so both arms subtract the
same thing, and detects components with scipy.signal.find_peaks rather than a
hand-rolled local-maximum loop. If "six at native, four after averaging" is an
artifact of the first implementation's choices, this should disagree.
"""

from pathlib import Path

import numpy as np
from scipy.signal import find_peaks

RAW = Path("~/Data/Faber2026/dsa110/DSA_bursts/zach_dsa_I_262_368_2500b_cntr_bpc.npy").expanduser()
DT_MS = 0.032768
F_FACTOR = 12


def band_profile(t_factor):
    """Frequency-summed profile at the requested time factor, own implementation."""
    arr = np.flipud(np.array(np.load(RAW, mmap_mode="r"), dtype=np.float64))
    # Dead channels: no variance at all. Simpler and stricter than the
    # production heuristic, on purpose.
    dead = ~np.isfinite(arr).any(axis=1) | (np.nanstd(arr, axis=1) == 0)
    arr[dead] = np.nan

    nf = (arr.shape[0] // F_FACTOR) * F_FACTOR
    nt = (arr.shape[1] // t_factor) * t_factor
    ds = np.nanmean(
        arr[:nf, :nt].reshape(nf // F_FACTOR, F_FACTOR, nt // t_factor, t_factor),
        axis=(1, 3),
    )
    return np.nansum(ds, axis=0)


def detect(prof, t_factor, sigma_thresh, min_prominence_sigma):
    """Peak times in ms from the maximum, with significance, via find_peaks."""
    dt = DT_MS * t_factor
    peak = int(np.nanargmax(prof))
    # One off-pulse definition in NATIVE time, so both arms subtract and scale
    # by the same physical region rather than by their own quartiles.
    half = int(round(6.0 / dt))
    mask = np.ones(prof.size, bool)
    mask[max(0, peak - half) : peak + half + 1] = False
    mu, sd = np.nanmean(prof[mask]), np.nanstd(prof[mask])
    snr = (prof - mu) / sd

    lo, hi = max(0, peak - half), min(prof.size, peak + half + 1)
    seg = np.nan_to_num(snr[lo:hi], nan=-1e9)
    idx, props = find_peaks(seg, height=sigma_thresh, prominence=min_prominence_sigma)
    return [(round(float((i + lo - peak) * dt), 3), round(float(seg[i]), 1)) for i in idx], snr


native = band_profile(1)
coarse = band_profile(2)

print(f"{'threshold':>9} {'prominence':>11} {'native':>7} {'coarse':>7}  verdict")
for thresh in (4.0, 5.0, 6.0):
    for prom in (0.0, 1.0, 2.0):
        n, _ = detect(native, 1, thresh, prom)
        c, _ = detect(coarse, 2, thresh, prom)
        verdict = (
            "native resolves more"
            if len(n) > len(c)
            else ("EQUAL" if len(n) == len(c) else "COARSE MORE (!)")
        )
        print(f"{thresh:>9} {prom:>11} {len(n):>7} {len(c):>7}  {verdict}")

print("\nAt the recorded criterion (5 sigma, no prominence requirement):")
n, _ = detect(native, 1, 5.0, 0.0)
c, _ = detect(coarse, 2, 5.0, 0.0)
print("  native:", n)
print("  coarse:", c)
for t, s in n:
    if not any(abs(t - y) < 0.07 for y, _ in c):
        near = min((y for y, _ in c), key=lambda y: abs(t - y))
        print(
            f"  LOST {t:+.3f} ms ({s} sigma) -> nearest surviving {near:+.3f}, "
            f"separation {abs(t - near):.3f} ms"
        )
