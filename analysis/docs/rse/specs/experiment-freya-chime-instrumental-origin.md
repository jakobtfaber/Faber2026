# Experiment: instrumental origin of the freya CHIME ~35 kHz decorrelation scale

---
**Date:** 2026-07-05
**Author:** AI Assistant (Claude, Faber2026 session)
**Status:** Complete
**Related Documents:**
- [Handoff: E3 ν^4.4 reversal closeout](handoff-2026-07-05-14-34-freya-chime-e3-reversal.md) (item 1)
- [Experiment: freya CHIME Δν_d science-readiness](experiment-freya-chime-dnu-science-readiness.md) (the evidence chain this extends)

---

## Experiment Goal

**Primary Question:** Is the achromatic ~35 kHz decorrelation scale measured on
the freya CHIME gen-3 product (canonical pass-5: Δν_d = 35.19 ± 4.42 ± 17.0 kHz,
m_acf = 0.304) instrumental (upchannelization/product chain) or astrophysical
(diffractive scintillation)?

**Context:** The gen-3 E3 rerun reversed the ν^4.4 verdict (half-band ratio
0.85 ± 0.18, window-stable, vs prediction 1.88), re-elevating an instrumental
hypothesis for the very scale the manuscript would quote. The handoff named
three tests with crisp falsifiable predictions: an off-pulse ACF null,
lag-domain masking at coarse-block harmonics, and the same measurement on the
DSA-side product where the CHIME chain is absent.

## Hypothesis

**Expected outcomes per hypothesis (stated before running):**

- *Instrumental, noise-coupled:* off-pulse (pure noise) spectra show the same
  ~5–6-fine-channel correlation; the on-pulse fit has no Lorentzian wing; no
  time-persistent spectral pattern at the implied m_acf amplitude.
- *Astrophysical:* off-pulse ACF white; on-pulse Lorentzian survives low-lag
  excision; the burst carries a frozen (time-persistent) spectral pattern with
  burst-referenced cross-correlation ~ m_burst² ≈ 0.092; DSA-side width scales
  ~ν^4.4 into consistency.

**Success criteria:** each arm produces a measured discriminator with its
prediction table; the canonical Δν_d is either cleared for scintillation
interpretation or retracted with a named mechanism.

## Test Arms (all built and run; no arm estimated)

### Arm A: off-pulse ACF null (+ A2 mechanism variants)

**Description:** run the exact pipeline call (`prepare_spectrum_from_config` →
`measure_scintillation_bandwidth`, v3 windows, flat-field + grid
regularization ON) on 12 non-overlapping burst-width noise slices inside
[10, 200]; slice-averaged ACF at lags 1–12 ch; variants: flat-field OFF,
split-band, slice-width scaling. **Complexity:** Low.

### Arm B: on-pulse decomposition (B1 fit surgery, B2/B3 persistence CCF, B4 spectro-temporal profile)

**Description:** (B1) refit the on-pulse ACF with coarse-block-harmonic masks
(±0.05/±0.08 MHz at k·0.390625) and with low-lag excision (|lag| > N ch);
(B2/B3) cross-correlate disjoint time-splits of the burst (halves; even/odd
bins) — scintillation is frozen across the burst, radiometer noise and
per-realization artifacts are not; (B4) measure the artifact's temporal
correlation ρ_t(Δt) off-pulse and the on-pulse pair-CCF vs Δt. **Complexity:**
Medium.

### Arm C: DSA-side comparison

**Description:** identical battery on the DSA-110 product (`freya.npz`,
committed `freya_dsa.yaml`, windows [1249, 1319]/[0, 1166]): burst
measurement with fit-window scan, low-lag excision, off-pulse null,
split-band ratio, ν^4.4 cross-telescope scaling. **Complexity:** Low.

## Experiment Setup

**Environment:** conda `flits`; fresh FLITS worktree
`~/Developer/scratch/worktrees/flits-rerun` @ `a0a9c83e` (recreated at the
path the archived gen-3 scripts hardcode); module identity printed per run.
`scintillation/data/` in the worktree is a per-file symlink dir (no shared
state mutated).
**Test Data:** `freya_chime_hi.npz` gen-3 (md5 `1f644b07…`, matches handoff);
`freya.npz` DSA side (md5 `80f764d731d9affd309030d78ea54a58`, recorded here —
no prior canonical md5).
**Archived artifacts:** scripts + captured outputs at
`~/Data/Faber2026/dsa110/scintillation-data/exp-instrumental-origin-2026-07-05/`
(`a_offpulse_null.py`, `a2_offpulse_variants.py`, `b_onpulse_decomposition.py`,
`b3_interleaved_ccf.py`, `b4_artifact_time_profile.py`, `c_dsa_side.py`,
`out_{a,a2,b,b3,b4,c}.txt`; arm D: `d_subband_400_800.py`,
`d2_subband_flatfield.py`, `out_d{,2}.txt`; visual inspection:
`e_acf_figures.py`, `e2_acf_lowlag_zoom.py`, `e3_subband_zoom.py` →
`fig_acf_overview.png`, `fig_acf_lowlag_zoom.png`,
`fig_subband_offpulse{,_zoom}.png`). B4's pair subsampling is seeded
(20260705); other arms are deterministic. Visual inspection (2026-07-05,
owner-prompted) confirms the numeric picture: the off-pulse mean ACF is a
shape-matched ~×2.3-scaled copy of the on-pulse low-lag core (same
~30–100 kHz decay; on-pulse additionally rides a ~0.0045 broadband pedestal
the fit absorbs as baseline, and shows visible coarse-harmonic bumps at
0.39/0.78 MHz); the DSA ACF shows a morphologically distinct resolved wing
over ~2 MHz; the B4 ridge visibly marches ~2 ch per time bin; the sub-band
off-pulse ACFs are structured and hi-band-broader in 600–800 and dead flat
at 400–600.
**Constraints:** freya redshift still the z = 1.0000 placeholder (unused
here); CHIME on-pulse window is only 11 bins, so persistence tests at large
Δt have few pairs (quantified below).

## Experiments Run

### Arm A: off-pulse null — FAILS in the instrumental direction

**Execution:** `conda run -n flits python a_offpulse_null.py` (out_a.txt).

**Results:**
- ✅ Protocol control: on-pulse reproduces the canonical 35.19 ± 4.42 kHz.
- ❌ **All 12 pure-noise slices "successfully" fit Δν_d = 25.5–52.4 kHz**
  (median 37.7), bracketing the canonical value, m ≈ 0.22.
- ❌ Slice-averaged ACF positive at every lag 1–12 ch (per-lag z up to +11.4);
  **aggregate z(1–6 ch) = +24.1**. Off-pulse correlated amplitude at 1–6 ch =
  0.0033 vs on-pulse 0.0092 in identical (mean²) units — the noise floor
  carries ~36% of the on-pulse low-lag structure. (Aggregate-z values here
  and below sum per-lag z/√n assuming independent lags; adjacent ACF lags
  share slices, so aggregates are somewhat inflated — the per-lag z carries
  the verdict.)

**A2 mechanism variants** (out_a2.txt):
- Flat-field OFF: same scale (median 35.2 kHz) at 26× amplitude — the *static
  bandpass gain* also has ~35 kHz structure (removed by flat-fielding; the
  surviving artifact is a separate, noise-coupled layer).
- Split-band off-pulse: median 26.6 kHz (600–700) vs 53.9 kHz (700–800),
  ratio ≈ 2.0 — the noise artifact is **chromatic**, hi-band broader as the
  B4 alignment mechanism requires (∝ν³ predicts 1.54; measured medians run
  ~30% higher, no uncertainties on the medians — direction matches, tightness
  not established).
- Slice width 11→22→44 bins: amp × width ≈ const within ~7%
  (0.0033/0.0034/0.0031 rescaled; only 3 slices at width 44) — the
  correlated amplitude tracks radiometer variance: **the correlation lives
  in the noise itself**, not in an additive fixed pattern.

### Arm B: on-pulse decomposition

**Execution:** `b_onpulse_decomposition.py`, `b3_interleaved_ccf.py`,
`b4_artifact_time_profile.py` (out_b, out_b3, out_b4).

**B1 fit surgery** (unmasked replica first reproduces 35.19 ± 4.42 exactly):
- Coarse-harmonic masks: 42.2 ± 2.8 / 45.0 ± 2.5 kHz (±0.05/±0.08 MHz) —
  a mild (up to ~28%) shift; the harmonics are not the driver.
- ❌ **Low-lag excision collapses the fit**: 31.2 (N=2), 23.4 (N=3),
  17.2 (N=4) kHz, degenerate by N=6 (amp 2.3 at γ 1.5 kHz) and pinned at the
  bound by N=8. A true Lorentzian of HWHM ≈ 5.8 ch keeps its wing; the
  on-pulse ACF has **no wing** — the "35 kHz Lorentzian" is carried entirely
  by lags ≲ 6 channels.

**B2/B3 persistence CCF:**
- Half-vs-half CCF positive (lag-0 z +5.5; mean 0.058 burst-referenced at
  1–6 ch; disjoint off×off control null at −1.6σ).
- Interleaved even/odd CCF much stronger (z(1–6) = +33) — **but its off-pulse
  control is NOT null (z = +18)**: the artifact is correlated across adjacent
  time bins, so small-Δt CCFs do not isolate persistence.

**B4 spectro-temporal profile (the decisive read):**
- Off-pulse pair CCF vs Δt: the correlation is a **drifting ridge** — peak at
  ~1 ch (Δt=1), ~2–3 ch (Δt=2), ~4–6 ch (Δt=3); at Δt=4 the 4–6 ch and
  8–12 ch columns are comparable (+0.0031/+0.0026), and the 0–6 ch columns
  are gone by Δt ≈ 5–7 (an unquantified +0.002–0.003 residual persists at
  8–12 ch, no sems printed). Fitted drift of the peak assignments
  ≈ 2 ch/bin.
- **Mechanism (hypothesis with quantitative support):** the gen-3 builder
  aligns channels with per-channel integer-bin dispersion shifts
  (∂t/∂ν → 0.41 bins per fine channel at 700 MHz). Any common-mode temporal
  power fluctuation (RFI, gain/Tsys wander) becomes a slanted streak in the
  aligned frame with exactly this drift: predicted 2.43 ch/bin at 700 MHz
  (1.95 @650, 2.99 @750 — chromatic ∝ν³, same direction as A2's split-band
  ratio; these predictions are derived here, not part of the captured
  outputs). The instantaneous channel-correlation scale ≈ drift ×
  (common-mode coherence ~1–2 bins) ≈ 2–5 ch ≈ 15–30 kHz — the observed
  scale.
- ❌ **No frozen-pattern plateau on-pulse:** the on-pulse pair CCF decays with
  Δt like the off-pulse artifact (dead by Δt ≈ 4–5) instead of holding at
  m_p². At Δt = 4–5 (den-weighted, 1–3 ch) values span −0.034…+0.023, i.e.
  **any time-persistent spectral modulation has burst-referenced amplitude
  ≲ 0.03–0.05 (m_p ≲ 0.2)**, well below the m_acf = 0.30 the ACF fit
  implies. Caveat: only 6–7 pairs at these separations (11-bin window; the
  Δt ≥ 6 rows are too few-pair to use); treated as a bounded limit, not a
  precision measurement.

### Arm C: DSA side — behaves like real scintillation

**Execution:** `c_dsa_side.py` (out_c.txt). 6144 channels, cw = 30.5 kHz,
1311–1498 MHz.

**Results:**
- ✅ Burst: **Δν_d = 448 ± 135 kHz @ 1405 MHz** (fit_lag 10 MHz); 470 ± 146 at
  5 MHz (stable); ⚠️ 15.6 MHz at fit_lag 25 — a wide second component grabs
  the fit there (window systematic persists on the DSA side; the stored
  legacy config fits show the same two-component structure).
- ✅ **Excision-robust:** γ = 713/710/629/615/554 kHz at N = 2/3/4/6/8 ch —
  the Lorentzian wing survives (collapse only at N=12 ≈ 366 kHz ≈ γ, as a
  real feature must). Contrast CHIME B1.
- ✅ **Off-pulse null passes:** 12 noise slices, aggregate z(1–6 ch) = +0.76
  (also validates that arm A's CHIME positive is not an artifact of the
  experiment's own slice/ACF machinery).
- ✅ Split-band ratio 2.37 ± 1.58 vs ν^4.4 prediction 1.34 (consistent;
  uninformative precision).
- Cross-telescope: ν^4.4-scaling 448 kHz @1405 → **20.9 ± 6.3 kHz @ 700 MHz**
  = 3.4 CHIME fine channels; width in DSA channels 14.7 (not few-channel).

### Arm D (owner-prompted follow-up, same day): 100-MHz sub-banded ACF fits, 400–800 MHz

**Question:** is scintillation being washed out by Δν_d's ν^4.4 evolution
across a wide fitting band — would 100-MHz sub-band ACFs (incl. the
never-analyzed 400–500 / 500–600) recover it?

**Execution:** `d_subband_400_800.py` (committed full-band `freya_chime.yaml`
as-is — turned out to trace the static-bandpass layer: that config has no
flat-fielding and poly-1 baseline ON, means near zero, m = −42 nonsense;
retained as out_d.txt for the record) and `d2_subband_flatfield.py`
(same npz, hi-protocol preprocessing: flat-field ON, baseline OFF, config
overridden in-memory). Full-band gen-3 npz (`freya_chime.npz`, 65,472 ch,
400–800 MHz), windows [253, 268]/[10, 200].

**Results (D2, flat-fielded):**

| subband | ON fit (1.0 MHz) | ON (0.3 MHz) | OFF median | OFF ACF(1–6 ch) z |
|---|---|---|---|---|
| 400–500 | 42.9 ± 12.9 kHz (7.0 ch) | 77.4 ± 21.3 | 5/10 fits, scattered | **−0.5 (null)** |
| 500–600 | 68.2 ± 35.2 (11.2 ch) | 140.0 ± 68.1 | 45.4 kHz (8/10) | +4.4 (weak) |
| 600–700 | 62.2 ± 4.0 (10.2 ch) | 97.4 ± 3.9 | 39.5 kHz (10/10) | +38.0 |
| 700–800 | 68.5 ± 6.9 (11.2 ch) | 69.5 ± 6.4 | 90.1 kHz (10/10) | +16.8 |

- ❌ **No washout rescue:** the on-pulse sub-band widths show no ν^4.4 family
  (observed ~1.5× spread 450→750 vs the predicted 9.5×), and every subband
  still "fits" at the tens-of-kHz artifact scale with strong fit-window
  sensitivity.
- **Resolution wall, not band-averaging:** DSA-anchored real scintillation is
  0.5 ch @450 and 1.2 ch @550 (NE2025-anchored: 1.8 / 4.3 ch) — unresolvable
  or marginal at the 6.1 kHz channelization, so sub-banding cannot recover a
  real signal below ~600 MHz regardless of the artifact.
- **Artifact chromaticity extends the mechanism evidence:** the off-pulse
  correlation is strong and hi-band-broader in 600–800 (medians 39.5 → 90.1
  kHz), weakens at 500–600, and *vanishes* at 400–500 (z = −0.5) — consistent
  with the alignment-shift mechanism, whose correlation length falls below
  one channel at low ν (shift gradient 1.55 bins/ch @450 vs 0.41 @700);
  medians carry no uncertainties, direction-level evidence only.
- ⚠️ Protocol sensitivity on display: this diagnostic config (RFI threshold
  5.0, window [253, 268], full-band npz) gives 62.2 ± 4.0 kHz at 600–700
  where the canonical hi-config (threshold 3.0, [253, 264], hi npz) gives
  36.94 ± 4.79 — the on-pulse "width" moves by ~70% under masking/window
  choices, further evidence it is not a stable astrophysical quantity.

### Arm G (owner-prompted): right window edge at the 1/e time

`g_1e_window.py` (out_g.txt). Band-mean 1/e crossing: bin 256.28 (0.75 ms
after peak 254) → window [253, 258), 5 bins = 1.64 ms (per-band edges:
[253, 258) at 600–700, [253, 257) at 700–800). Burst mean excess doubles
(0.343 → 0.666); noise variance ×2.20.

- Full band: **30.96 ± 4.75 kHz** (vs canonical 35.19 ± 4.42 — statistically
  identical; equals the E3 split-time first-half value exactly, same window).
  fit_lag 0.3 → 44.07 ± 3.08: the fit-window systematic persists.
- Half-band ratio: 1.16 ± 0.28 (common edge) / 1.06 ± 0.26 (per-band 1/e
  edges) — still ~2.6–3σ below the ν^4.4 prediction 1.88.
- Off-pulse null at matched 5-bin width still FAILS: 20/21 slices fit, median
  20.0 kHz, ACF(1–6 ch) +0.00567 (×1.72 the 11-bin amplitude, tracking the
  ×2.20 noise-variance scaling), z(1–6) = +32. Note the artifact's *fitted
  scale shrinks* with window length (20 kHz at 5 bins vs 37.7 at 11) —
  consistent with the drifting-ridge mechanism: longer averaging mixes
  drifted copies into a broader apparent channel scale.
- Net: tightening to the 1/e time raises burst contrast ×1.9 but the
  artifact-to-burst-squared contamination only improves ~×0.6, and every
  verdict (achromatic ratio, off-pulse failure, window systematic) is
  unchanged.

### Arm H (owner-prompted): cropping-width sweep — no width-stable feature at any crop

`h_width_sweep.py` (out_h.txt, `fig_width_sweep.png`). Left edge 253 fixed,
right edge 255–268 (widths 2–15 bins); per width: on-pulse fit + width-matched
off-pulse artifact level + burst-referenced on−off excess.

- **The fitted Δν_d is a monotonic function of window length for burst AND
  pure noise alike**: on-pulse 22.7 → 42.6 kHz as off-pulse slides 13.6 →
  46.7 kHz (w = 2 → 15), the two converging at the canonical width. No crop
  yields a window-independent width — the "measurement" inherits its scale
  from the crop length, as the drifting-ridge mechanism predicts
  (time-averaging mixes drifted correlation copies into a broader apparent
  channel scale).
- The burst-referenced on−off excess ACF(1–6 ch) plateaus at ~0.085–0.095
  for w ≥ 6 — numerically at m_acf² = 0.092 — but **rises steeply at w ≤ 4**
  (0.22 at w = 2), which a frozen pattern cannot do. That width-dependence is
  the burst SELF-NOISE signature (per-realization emission speckle, channel-
  correlated over a few fine channels by upchan leakage; its burst-referenced
  variance grows as the crop clips the burst). The Δt-resolved persistence
  test (B4), which self-noise cannot pass, already capped the truly frozen
  part at ≲ 0.03–0.05 — so the plateau decomposes as mostly self-noise (+
  artifact-scaling residual), locating where the apparent m_acf ≈ 0.30
  "modulation" actually lives.
- m_on falls 0.64 → 0.23 across the sweep (noise + self-noise dilution); no
  stable modulation index either.
- *Caveat (resolved by arm H2):* the on−off subtraction here assumes the
  noise artifact has the same fractional (mean²-normalized) amplitude on- and
  off-pulse. Arm H2 replaces that assumption with a composed prediction from
  the measured artifact kernel and confirms the excess curve to ≤ 1.5%.

### Arm H2 (owner-prompted): amplitude-accurate artifact subtraction — the residual excess is lag-flat, not a 35 kHz feature

`h2_amplitude_corrected.py` (out_h2.txt, `fig_width_sweep_corrected.png`).
Fixes the amplitude inaccuracy in arm H's excess estimator. Instead of
subtracting the width-matched off-pulse ACF (equal-fractional-amplitude
assumption), measure the single-bin off-pulse pair cross-covariance kernel
C1(Δc, Δt) (Δc = 0–12 ch, Δt = 0–8 bins, 120 random off-pulse pairs per Δt,
seed 20260705) and *compose* the artifact covariance of any window from it:
A(Δc; w) = Σ_{t,t'} w_t w_t' C1(Δc, |t−t'|) / (w²μ²), under two bracketing
scalings — multiplicative (artifact ∝ total power, w_t = 1 + b_t from the
band-mean burst profile) and additive (w_t = 1). Corrected excess =
[ACF_on − A] × μ²/(μ−1)² at lags 1–6.

- Kernel C1(1–6 ch mean) by Δt: 0.00731, 0.00697, 0.00578, 0.00386, 0.00191,
  0.00048, then ≈ −0.0006 at Δt = 6–8 — the same temporal-correlation profile
  B4 measured, recovered independently from raw pair covariances.
- **Validation passed** before any subtraction was trusted: composing over
  off-pulse windows (w_t = 1) reproduces the directly measured off-window
  ACF(1–6): w=5 composed +0.00585 vs direct +0.00567 (n=21); w=11 +0.00332
  vs +0.00330 (n=12).
- **The amplitude-scaling ambiguity is a ≤ 1.5% effect, not a loophole**:
  multiplicative vs additive corrected excess at the canonical w=11 is
  0.0881 ± 0.0005 vs 0.0893 ± 0.0004; the two curves are near-identical at
  every width (w=2: 0.2256 both; w=15: 0.0822/0.0833). Because the artifact's
  temporal correlation dies by Δt ≈ 5 and the window mean is burst-dominated,
  the on-pulse artifact level barely depends on how it couples to signal
  power. Arm H's excess curve is confirmed as-is: steep rise at w ≤ 4
  (self-noise), plateau ~0.082–0.10 at w ≥ 6.
- **New discriminating fact — the corrected excess is FLAT in channel lag.**
  At w=11 (multiplicative), dc = 1..8: +0.079, +0.092, +0.083, +0.097,
  +0.087, +0.090, +0.086, +0.083 — no decay out to ≥ 8 channels (≳ 50 kHz);
  w=5 is equally flat (~0.093–0.116). A real ~35 kHz Lorentzian at the
  matched amplitude 0.092 would fall to ~0.030 by dc = 8 (fig, red dotted).
  Contrast mean(dc 1–3) − mean(dc 6–8) = −0.002 vs +0.045 predicted for the
  Lorentzian: **any lag-decaying 20–50 kHz-scale component in the residual is
  consistent with zero, amplitude ≲ 0.015 → m ≲ 0.12** — tighter than, and
  independent of, B4's persistence cap (m_p ≲ 0.2). The 35-kHz-*shaped* part
  of the on-pulse ACF is therefore fully accounted for by the noise-artifact
  kernel; what remains is a broadband pedestal (burst self-noise / smooth
  spectral envelope, absorbed as "baseline" by the Lorentzian fit), not a
  decorrelation feature. *Scale caveat:* a pattern with HWHM ≳ 100 kHz would
  also look flat over dc 1–8 and is degenerate with the pedestal here — the
  m ≲ 0.12 bound is specific to the 20–50 kHz scale in question.

## Comparison Matrix

| Discriminator | Prediction: instrumental | Prediction: astrophysical | Measured (CHIME) | Measured (DSA) |
|---|---|---|---|---|
| Off-pulse ACF | same scale present | white | **25–52 kHz in all 12 slices, z=+24** | null (z=+0.8) |
| Amplitude scaling | ∝ noise variance | none off-pulse | **≈ ∝ 1/T (7% spread)** | — |
| Lorentzian wing (excision) | collapses | survives | **collapses by N=4–6** | survives to N=8 |
| Frozen pattern (CCF vs Δt) | decays like artifact ρ_t | Δt-independent ≈ m² | **decays; m_p ≲ 0.2** | — (not needed) |
| Coarse-harmonic masking | (either) minor | minor | +20–28% shift | — |
| Chromaticity of noise scale | ∝ν³ (alignment mechanism) | n/a | **ratio 2.0 vs 1.54 pred.; drift ~2 ch/bin ≈ 2.4 pred.** | — |
| Excess lag profile after kernel subtraction (H2) | flat (broadband pedestal) | Lorentzian decay at ~35 kHz | **flat to ≥8 ch; narrow component ≲0.015 (m ≲ 0.12)** | — |

## Key Insights

1. **The canonical CHIME Δν_d = 35.19 ± 4.42 ± 17.0 kHz is an instrumental
   artifact scale, not a scintillation measurement.** Every discriminator
   landed on the instrumental side: it is in the pure-noise floor at the same
   scale, it scales as radiometer variance, it has no Lorentzian wing, and
   the burst carries no time-persistent spectral pattern at the implied
   amplitude.
2. **Mechanism (hypothesis, quantitatively supported, not yet
   forward-modeled):** per-channel dispersion-alignment shifts (gen-3
   builder; any CHIME upchan product needs them) convert common-mode
   temporal noise into slanted spectro-temporal streaks — measured ridge
   drift ~2 ch/bin vs 2.43 predicted, chromatic in the predicted direction.
   Two additional instrumental layers identified: static bandpass fine
   structure at the same scale (removed by flat-field) and burst-locked
   self-noise (in the E3 mixture).
3. **E3's "achromatic ratio 0.85" is best read as a property of the
   artifact-dominated mixture**, not of the underlying signal — no mixture
   decomposition was computed (the artifact alone is chromatic ratio ~2.0,
   the on-pulse mixture measures 0.85; burst self-noise plausibly supplies
   the channel-locked pull, but that reconciliation is unverified). Either
   way the ratio cannot be quoted as a property of the sky.
4. **The recoverable freya scintillation measurement lives on the DSA side:**
   448 ± 135 kHz @ 1405 MHz, excision-robust, off-pulse-clean. Scaled to
   700 MHz it predicts ~21 ± 6 kHz (3.4 fine channels — resolved). Note a
   fully-developed diffractive pattern at that scale would have m ~ 1, which
   the B4 persistence bound (m_p ≲ 0.2) and the tighter H2 shape bound
   (m ≲ 0.12 at 20–50 kHz, from the lag-flat corrected excess) exclude:
   cross-telescope
   consistency therefore *requires* strong modulation suppression at 700 MHz
   (e.g. two-screen quenching, finite source size) — a constraint to carry
   into the E4 framework, not a settled consistency.

**Surprising findings:** the interleaved-CCF control failing (artifact
correlated across adjacent bins) — without B4's ρ_t profile the B3 result
would have been misread as a persistent pattern detection; the static
bandpass carrying the same ~35 kHz scale as the noise-coupled layer.

**Failed assumptions:** "off-pulse null clears the product for scintillation"
(it failed instead); "even/odd interleaving isolates persistence" (only
Δt-resolved CCFs do, given temporally-correlated artifacts).

## Recommendation

**Recommended interpretation:** retract the CHIME Δν_d as a scintillation
measurement; treat ~35 kHz as the product's noise-correlation scale.
The manuscript's scintillation budget should quote the **DSA-side**
Δν_d = 448 ± 135 kHz @ 1405 MHz (with its own fit-window systematic to be
characterized) and may cite the CHIME side only as consistent upper-limit
territory: any real 700-MHz pattern has m_p ≲ 0.2 at the ~20–35 kHz scale.

**Why not the alternatives:** the astrophysical reading requires the noise
floor of a burst-free window to scintillate (arm A), a Lorentzian with no
wing (B1), and a frozen pattern that is absent (B4) — all measured, not
argued.

**Caveats:** m_p limit rests on 5–7 pairs at Δt ≥ 4 (11-bin window);
the alignment-streak mechanism is quantitatively supported (drift rate,
chromaticity, variance scaling) but not yet forward-modeled end-to-end;
DSA fit_lag 25 MHz picks up a wide second component — the DSA number needs
its own window-systematic treatment before it is citable.

## Conditions for Alternative Approaches

**If** the other four CHIME targets (casey, isha, mahi, phineas), once
regenerated gen-3-style, show *no* off-pulse correlation at the ~few-channel
scale, **then** the mechanism attribution (product chain, not freya-specific
RFI environment) needs revisiting — though arm A/B verdicts for freya stand
regardless. **If** a forward model (synthetic common-mode noise through the
aligned builder) fails to reproduce the drift/scale, the alignment mechanism
specifically is wrong and the artifact needs a different chain-level origin.

## Next Steps

1. Off-pulse ACF null as a **standing pre-flight check** for every CHIME
   upchan scintillation product (cheap: arm-A script generalizes; candidate
   for a pipeline diagnostic in FLITS).
2. DSA-side window-systematic treatment (fit-window scan + two-component
   handling) to make 448 ± 135 kHz citable; then re-derive E4 two-screen
   numbers from the DSA scale (still gated on the real redshift).
3. Forward-model the alignment-streak mechanism (synthetic common-mode noise
   through `build_npz_aligned_20260704.py` arithmetic) to close the mechanism
   hypothesis.
4. Update the manuscript scattering/scintillation prose: nothing CHIME-side
   citable; the "consistent with ν^4.4 MW scintillation" clause stays dead,
   now for a measured instrumental reason.
5. Carry to the other 4 targets when regenerated (handoff item 3): predicted
   clincher is the same off-pulse scale appearing in each.

## References

**Code exercised:** worktree `flits-rerun` @ `a0a9c83e` —
`scintillation/scint_analysis/freya_scintillation.py`
(`prepare_spectrum_from_config`, `measure_scintillation_bandwidth`,
`_lorentzian_with_baseline`, `_normalise_spectrum`),
`scint_analysis/analysis.py:234` (`calculate_acf`); configs
`freya_chime_hi.yaml` (v3), `freya_dsa.yaml`.

**Archived experiment code + outputs:**
`~/Data/Faber2026/dsa110/scintillation-data/exp-instrumental-origin-2026-07-05/`

---

## Appendix: Raw Experiment Data

```
Arm A (off-pulse, flat-field ON, mean^2 units):
  on-pulse control: dnu 35.19 +/- 4.42 kHz, m 0.271
  12/12 noise slices fit: [52.4, 42.3, 38.0, 32.8, 38.2, 34.5, 37.5, 39.3,
                           28.9, 40.0, 25.5, 30.3] kHz, m 0.217-0.231
  slice-avg ACF: lag1 +0.00440+/-0.00039 (z 11.4) ... lag6 +0.00254 (z 7.0)
    ... lag12 +0.00109 (z 5.6); aggregate z(1-6) +24.1
  mean off ACF(1-6ch) 0.0033 vs on-pulse 0.0092

Arm A2:
  V1 flat-field OFF: amp(1-6ch) +0.0867 (26x), z +650, median dnu 35.2 kHz
  V2 split-band medians: 26.6 kHz (600-700) vs 53.9 kHz (700-800)
  V3 width 11/22/44 bins: amp 0.00330/0.00168/0.00078; amp*width/11
     0.00330/0.00336/0.00313 (const -> noise-variance scaling)

Arm B1 (fit_lag 1.0 MHz):
  unmasked 35.19+/-4.42 (protocol check = reference exactly)
  harmonics +/-0.05: 42.21+/-2.76 | +/-0.08: 45.02+/-2.46
  excise <=2ch: 31.23+/-6.16 | <=3: 23.38+/-7.48 | <=4: 17.24+/-12.80
  excise <=6: amp 2.31 at gamma 1.53 kHz (degenerate) | <=8: at upper bound

Arm B2 (burst-referenced): half-half CCF lag0 +0.175+/-0.032; mean(1-6)
  +0.058, z +6.2; off x off control z -1.6
Arm B3: interleaved CCF z(1-6) +33; per-band mean(1-6) 0.142 (lo) / 0.121 (hi)
  persistent-pattern Lorentzian (misread if taken alone): 38.8+/-7.2 kHz
  OFF-PULSE INTERLEAVED CONTROL NOT NULL: mean(1-6) +0.0044, z +18.1
Arm B4 off-pulse pair CCF (mean^2 units), ridge by Dt:
  Dt=0: ch1 0.0165 | Dt=1: ch1 0.0127 | Dt=2: ch2-3 0.0065 | Dt=3: ch4-6
  0.0055 | Dt=4: ch4-6 0.0031 / ch8-12 0.0026 (comparable) | Dt=5-7:
  ch0-6 ~0, ch8-12 residual +0.0029/+0.0023 (no sems; unquantified)
  => drift of peak assignments ~2 ch/bin (derived predictions, not captured
  output: 2.43 @700 MHz, 1.95 @650, 2.99 @750)
Arm B4 on-pulse pair CCF (burst-referenced, den-weighted), ch1/ch2/ch3:
  Dt=1: +0.217/+0.228/+0.194 | Dt=2: +0.112/+0.127/+0.124
  Dt=3: +0.046/+0.058/+0.050 | Dt=4: -0.005/+0.023/+0.000
  Dt=5: +0.005/-0.034/-0.029 (pairs: 10/9/8/7/6)

Arm C (DSA, 6144 ch, cw 30.5 kHz, 1311-1498 MHz):
  fit_lag 25/10/5 MHz: 15619+/-3045 (wide component) / 448.0+/-134.7 /
    470.2+/-145.9 kHz
  excision N=2/3/4/6/8/12: 713/710/629/615/554/43(degenerate) kHz
  off-pulse: aggregate z(1-6ch) +0.76
  split-band: lo 360.7+/-147.7 @1358 | hi 853.6+/-448.9 @1452;
    ratio 2.37+/-1.58 vs nu^4.4 1.34
  nu^4.4 scaling: 448+/-135 @1405 -> 20.9+/-6.3 kHz @700 (= 3.4 CHIME ch;
    14.7 DSA ch)

Arm D2 (flat-fielded sub-bands, full-band npz, windows [253,268]):
  400-500: ON 42.85+/-12.94 / 77.44+/-21.33 kHz; OFF 5/10 median 190.9,
    ACF(1-6) -0.00002, z -0.5
  500-600: ON 68.23+/-35.24 / 139.95+/-68.05; OFF 8/10 median 45.4,
    ACF(1-6) +0.00016, z +4.4
  600-700: ON 62.18+/-4.00 / 97.38+/-3.87; OFF 10/10 median 39.5,
    ACF(1-6) +0.00553, z +38.0
  700-800: ON 68.49+/-6.90 / 69.46+/-6.41; OFF 10/10 median 90.1,
    ACF(1-6) +0.00526, z +16.8
  (out_d.txt = committed-config run, static-bandpass layer, diagnostic only)

Arm H2 (kernel-composed subtraction, burst-referenced, lags 1-6):
  C1(1-6ch mean) by Dt=0..8: 0.00731 0.00697 0.00578 0.00386 0.00191
    0.00048 -0.00055 -0.00076 -0.00075
  validation (s_t=1): w=5 composed +0.00585 vs direct +0.00567 (n=21);
    w=11 +0.00332 vs +0.00330 (n=12)
  excess mult/add: w=2 0.2256/0.2256 | w=5 0.1047/0.1057 | w=11
    0.0881+/-0.0005 / 0.0893+/-0.0004 | w=15 0.0822/0.0833
  lag profile w=11 mult, dc 1..8: +0.079 +0.092 +0.083 +0.097 +0.087
    +0.090 +0.086 +0.083 (flat; 35 kHz Lorentzian at amp 0.092 predicts
    decay to ~0.030 by dc=8)

Checksums: freya_chime_hi.npz 1f644b07... (matches handoff);
  freya_chime.npz 0b3b423a... (matches); freya.npz (DSA)
  80f764d731d9affd309030d78ea54a58 (recorded this session)
```
