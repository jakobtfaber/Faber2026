#!/usr/bin/env python3
"""Gate 0: Route-B ceiling detectability for the freya CHIME Dnu_d measurement.

Predeclaration and pinned inputs: docs/rse/specs/experiment/experiment-chime-scint-gate0-detectability.md.
Fisher/optimal-quadratic-estimator bound with the instrumental common mode
assumed PERFECTLY removed (the Route-B best case). All inputs are published
summary statistics of the retained product; no burst data is read.
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# Pinned inputs (see the experiment record's provenance table).
N_CH = 23064            # high-band fine channels
DCH_KHZ = 6.1036        # fine channel width
N_EFF = N_CH / 2        # x2 oversampling correlates adjacent channels
N_ON, N_OFF = 100, 337  # on-pulse / usable off-pulse samples
N_POL = 2
F_B = 0.05              # burst flux fraction of on-pulse total intensity
M_RANGE = (0.15, 0.17)  # burst modulation prior
DNU_KHZ = np.linspace(6.0, 400.0, 400)  # Dnu_d sweep

# Per-channel noise-to-signal on the background-subtracted burst spectrum.
eps2 = (1.0 / (N_ON * N_POL) + 1.0 / (N_OFF * N_POL)) / F_B**2

out = {"eps2_per_channel": eps2, "curves": {}}
fig, ax = plt.subplots(figsize=(7.0, 4.5), dpi=200)
for m in M_RANGE:
    w = DNU_KHZ / DCH_KHZ
    snr = (m**2 / eps2) * np.sqrt(N_EFF * w / 2.0)
    out["curves"][f"m={m}"] = {
        "snr_at_35kHz": float(np.interp(35.0, DNU_KHZ, snr)),
        "snr_max_over_sweep": float(snr.max()),
        "dnu_khz_at_max": float(DNU_KHZ[snr.argmax()]),
    }
    ax.plot(DNU_KHZ, snr, label=f"m = {m}  (m² = {m**2:.4f})")

ax.axhline(5, color="green", ls="--", lw=1, label="GO floor (5)")
ax.axhline(3, color="red", ls="--", lw=1, label="NO-GO floor (3)")
ax.axvline(35.4, color="gray", ls=":", lw=1,
           label="instrumental width 35.4 kHz (every route's fitted scale)")
ax.set_xlabel(r"assumed $\Delta\nu_d$ (kHz)")
ax.set_ylabel("SNR ceiling (perfect common-mode removal)")
ax.set_title("Gate 0: Route-B detectability ceiling, freya high band")
ax.legend(fontsize=8)
ax.set_xlim(DNU_KHZ[0], DNU_KHZ[-1])
ax.set_ylim(0, None)
fig.tight_layout()
figpath = Path(__file__).resolve().parent.parent / "docs/rse/decks/scintillation/gate0-detectability/gate0-detectability-curve.png"
fig.savefig(figpath)

best_m = max(M_RANGE)
best = out["curves"][f"m={best_m}"]["snr_max_over_sweep"]
out["verdict"] = "GO" if best >= 5 else ("MARGINAL" if best >= 3 else "NO-GO")
out["verdict_basis"] = f"max SNR over sweep at m={best_m}: {best:.2f}"
print(json.dumps(out, indent=2))
