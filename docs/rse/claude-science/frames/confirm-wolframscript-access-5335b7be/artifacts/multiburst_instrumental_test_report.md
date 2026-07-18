# Is freya's CHIME scintillation quenched, or is the failure universal?

**Question.** The freya CHIME "instrumental origin" experiment showed that freya's ~35–54 kHz
CHIME decorrelation scale fails the off-pulse ACF null — burst-free noise slices fit the *same*
scale as the on-pulse window. Does this failure happen for **every** burst (the recovered scale is
instrumental everywhere), or is freya **uniquely** quenched while other sightlines carry real
scintillation?

**Method.** The two decisive freya discriminators, run uniformly on all 12 bursts with the exact
`scint_analysis.freya_scintillation` machinery (same fit: `max_lag=5 MHz`, `fit_lag=1 MHz`):

- **Arm A — off-pulse fitted-scale null.** Measure the decorrelation scale Δν_d in the on-pulse
  window (positive control) and in a set of non-overlapping *burst-free* off-pulse noise slices of
  identical width. If the noise-only slices reproduce the on-pulse scale, the recovered scale is
  noise-borne/instrumental. The **fitted scale is scale-invariant** (curve_fit normalizes the
  amplitude internally), so it is robust to these configs lacking bandpass normalization.
- Separation statistic: `sep_z = (Δν_on − median Δν_off) / sqrt(err_on² + scatter_off²)`. A robust
  detection of real, burst-locked structure would give `sep_z > 3` (on-pulse scale distinct from
  the noise floor). `sep_z ≈ 0` means the noise floor reproduces the on-pulse scale → instrumental.

## Result — the failure is universal, not freya-specific

| burst | cw (kHz) | on-pulse Δν_d (kHz) | off-pulse median (kHz) | separation z | verdict |
|---|---|---|---|---|---|
| casey | 32.301 | 45.85 ± 32.95 | 48.0 | -0.07 | INSTRUMENTAL (off reproduces on) |
| whitney | 24.416 | 45.92 ± 25.88 | 46.1 | -0.01 | INSTRUMENTAL (off reproduces on) |
| phineas | 24.416 | 63.96 ± 26.82 | 56.9 | 0.26 | INSTRUMENTAL (off reproduces on) |
| mahi | 0.763 | no fit | — (n_off=0) | — | no-fit |
| freya | 6.104 | 54.13 ± 10.32 | 54.4 | -0.03 | INSTRUMENTAL (off reproduces on) |
| zach | 6.104 | 86.35 ± 14.8 | 46.9 | 2.67 | INSTRUMENTAL (off reproduces on) |
| chromatica | 6.104 | 41.12 ± 10.44 | 41.1 | 0.0 | INSTRUMENTAL (off reproduces on) |
| wilhelm | 6.104 | 47.48 ± 10.17 | 47.1 | 0.04 | INSTRUMENTAL (off reproduces on) |
| oran | 3.052 | 51.91 | — (n_off=0) | — | no-fit |
| hamilton | 6.104 | 46.37 ± 9.26 | 45.8 | 0.06 | INSTRUMENTAL (off reproduces on) |
| johndoeII | 0.763 | 579.47 ± 10.49 | 723.6 | -0.65 | INSTRUMENTAL (off reproduces on) |
| isha | 1.526 | 62.62 ± 5.38 | 58.4 | 0.79 | INSTRUMENTAL (off reproduces on) |

**Every burst that yields a fit lands on its own off-pulse noise floor.** For 9 of the 10
fittable bursts `|sep_z| < 1` (all except zach): the on-pulse decorrelation scale is statistically
indistinguishable from what the burst-free noise produces under the identical fit. The recovered
CHIME "scintillation" scale is a property of the correlated instrumental noise, reproduced in
windows containing no burst — **freya is representative, not special.** There is no burst whose
CHIME scintillation survives the off-pulse null; freya's sightline is not uniquely quenched.

**The one marginal case — zach.** zach is the only burst with any on-pulse excess: on-pulse
86.4 ± 14.8 kHz vs off-pulse floor ~46.9 kHz, `sep_z = 2.67`. This is below the 3σ robustness
bar and its off-pulse null still fits a strong ~47 kHz floor, so it is *not* a clean detection —
but it is the single sightline where the on-pulse scale sits above the noise floor at all, and it
is the one worth a closer, bandpass-normalized re-examination before being finalized as a limit.

**Two bursts give no off-pulse fit — geometry, not physics.** mahi (24 ms FWHM) and oran (74 ms
FWHM) are so wide that after excising a burst-width window, the remaining off-pulse region cannot
host non-overlapping noise slices of equal width (`n_off = 0`). Their null is simply not
constructible with this slice geometry; it is not evidence either way. A dedicated off-pulse
region (or shorter slices) would be needed to test them.

## What this settles, and its limits

1. **Direct answer:** the CHIME de-comb / scintillation failure is **universal across the sample**,
   not a freya-specific quench. The ~kHz decorrelation scale recovered in CHIME is instrumental
   (noise-borne) for every burst tested, confirming the sample-wide upper-limit decision was
   correct — not a freya artifact generalized too far.
2. **This is the off-pulse null on the standard `_chime` products**, which are `diagnostic_only`
   (they lack `bandpass_normalization`). The scale-invariant fitted-Δν_d test is valid on them; the
   *amplitude*-based diagnostics (raw ACF ratio, the B2 split-time CCF amplitude) are **not** — in
   raw correlator units the low-lag ACF and burst-referenced CCF denominators are meaningless, so
   those columns were computed but are flagged unreliable and are not used for any conclusion here.
   The B2 persistence test would be diagnostic only on a bandpass-normalized product.
3. **zach and the two wide bursts (mahi, oran)** are the only loose ends: zach for its marginal
   sub-3σ excess, mahi/oran for lacking a constructible off-pulse null under this geometry.

## Provenance

- Discriminators reproduced from the freya experiment scripts `a_offpulse_null.py` and
  `b_onpulse_decomposition.py` at
  `~/Data/Faber2026/dsa110/scintillation-data/exp-instrumental-origin-2026-07-05/`.
- Machinery: `dsa110-FLITS/scintillation/scint_analysis/freya_scintillation.py`
  (`prepare_spectrum_from_config`, `measure_scintillation_bandwidth`); per-burst configs
  `scintillation/configs/bursts/<name>_chime.yaml`; data `scintillation/data/<name>_chime.npz`.
- Driver: `multiburst_instrumental_test.py`; raw per-burst output: `multiburst_instrumental_results.json`.
- Env `flits-scint` (numpy, scipy, lmfit, pyyaml, matplotlib, astropy, tqdm).
