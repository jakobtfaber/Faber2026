# Pre-ratification RFI visual packet (2026-07-26)

Owner-requested decision support for ratifying the CHIME RFI acceptance
contract (`../owner-decision-packet-rfi-acceptance-contract-2026-07-23.md`,
ticket `rfi-validation-01`): raw dynamic spectra of all twelve bursts,
CHIME and DSA side by side, **no RFI cleaning applied** — the contract is
ex ante, so no data processed under it exists yet.

## Method (reproducible)

- Inputs: the 12+12 `*_cntr_bpc.npy` Stokes-I cubes at
  `~/Data/Faber2026/chimefrb/CHIME_bursts/` and
  `~/Data/Faber2026/dsa110/DSA_bursts/` (per-instrument dedispersed; the
  applied DM is the filename stem, per the recorded convention).
- Instrument parameters from dsa110-FLITS
  `scattering/configs/telescopes.yaml`: CHIME 400.19–800.19 MHz,
  2.56 µs, 1024 ch; DSA 1311.25–1498.75 MHz, 32.768 µs, 6144 ch; both
  stored frequency-descending (flipped to ascending for display); both
  windows span 81.9 ms centered on the burst.
- Rendering: block-mean binning (CHIME 2×16 freq×time, DSA 8×2),
  per-channel robust z-score (median/MAD), color scale −2 to
  max(99.5th percentile, 3). Fully-masked channels appear as flat bands.
- Script: session scratchpad `render_rfi_packet.py`; rerun is
  deterministic from the inputs above (matplotlib Agg, conda `py312`).

```python
# reproduce
conda run -n py312 python render_rfi_packet.py   # emits <burst>_rfi_packet.png x12
```

Delivered to the owner in-session 2026-07-26 (twelve PNGs). Visual vet
performed on zach and chromatica before delivery: burst at t=0, masked
bands and narrowband RFI lines legible, DM annotations correct
(chromatica CHIME 272.638 vs DSA 272.368 demonstrates the
per-instrument-DM convention).

## Status

Decision support only. No science product, no cleaning, no trust change.
The ratification decision (accept / amend / reject the five fail-closed
rules) remains open at ticket `rfi-validation-01`.
