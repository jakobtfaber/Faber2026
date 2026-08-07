"""Raw-layer axis / dispersion-measure convention helpers (wayfinder ticket 17).

Pure functions used by certificates and automated tests. No dependency on
local data paths except where callers pass explicit Paths.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np

# Handoff 2026-07-19-14-56: corrected 400-MHz-anchored DM binshift.
K_DM = 1.0 / 2.41e-4  # matches builder / remediation recipe
F_REF_MHZ = 400.0


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            block = f.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def md5_prefix(path: Path, n: int = 8) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        while True:
            block = f.read(1 << 20)
            if not block:
                break
            h.update(block)
    return h.hexdigest()[:n]


def freq_order_from_axis(freq_mhz: np.ndarray) -> str:
    """Return ascending / descending / mixed from a frequency axis array."""
    d = np.diff(np.asarray(freq_mhz, dtype=float))
    if d.size == 0:
        return "mixed"
    if np.all(d > 0):
        return "ascending"
    if np.all(d < 0):
        return "descending"
    return "mixed"


def dm_binshift_samples(
    freq_mhz: np.ndarray,
    delta_dm: float,
    dt_s: float,
    f_ref_mhz: float = F_REF_MHZ,
) -> np.ndarray:
    """Corrected-sign residual-DM bin shifts (positive ⇒ later in time).

    ``binshift(f) = -K_DM · ΔDM · (1/f² - 1/f_ref²) / DT``
    with ``f`` in MHz. For ``ΔDM > 0`` and ``f > f_ref``, shift is positive
    (high frequencies move later) — the single-channel sign convention.
    """
    f = np.asarray(freq_mhz, dtype=float)
    return -K_DM * delta_dm * (1.0 / f**2 - 1.0 / f_ref_mhz**2) / dt_s


def apply_binshifts(data: np.ndarray, shifts: np.ndarray) -> np.ndarray:
    """Apply per-channel integer rolls (positive shift ⇒ later)."""
    out = np.empty_like(data)
    for i, sh in enumerate(np.asarray(shifts)):
        out[i] = np.roll(data[i], int(round(float(sh))))
    return out
