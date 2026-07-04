# Experiment: freya CHIME Δν_d science-readiness — resolving the four pass-2 blockers

---
**Date:** 2026-07-03
**Author:** AI Assistant (Claude, Faber2026 session)
**Status:** Complete
**Related Documents:**
- [Handoff: freya scint lane closeout](handoff-2026-07-03-18-22-freya-scint-lane-closeout.md)
- [Implement: freya scint fit quality (#118 → PR #119)](implement-freya-scint-fit-quality.md)

---

## Experiment Goal

**Primary Question:** Is the freya CHIME-side scintillation measurement
(pass-2 first look: Δν_d = 49.6 ± 9.0 kHz, m = 0.187) science-ready, and if
not, what concretely blocks it?

**Context:** The pass-2 flat-fielding run left four blockers: (E1) the hi-res
npz sits on a gapped frequency grid and `calculate_acf` labels index lags with
the *mean* channel spacing, stretching the lag axis; (E2) a residual ~0.497 MHz
ACF periodicity of unknown origin; (E3) a single-estimator result with no
internal consistency check; (E4) a reported modulation index m ≈ 0.19 that is
far below the m ≈ 1 expectation for point-source diffractive scintillation.

## Hypothesis

**Expected Outcome:**
- E1: the 1.234× mean-vs-native spacing ratio is a pure axis mislabeling;
  regridding to the native uniform grid rescales Δν_d by ~1/1.234 (~40 kHz).
- E2: the 0.497 MHz ripple is the 0.390625 MHz coarse-channel scallop
  stretched by the E1 mislabeling (0.390625 × 1.234 = 0.482); fixing the grid
  relocates it to ≈ 0.390625 MHz.
- E3: if the signal is Milky-Way diffractive scintillation, half-band widths
  scale ~ν^4.4 (predicted hi/lo ratio 1.88); if instrumental (PFB leakage,
  fixed in channel units), the ratio is 1.00.
- E4: m = 0.187 under-reports the physical modulation because the estimator
  divides by the mean *without* off-level subtraction; the ACF zero-lag
  amplitude gives the physical m, and the two-screen coherence constraint (as
  encoded in `scint_analysis/analysis.py:1111`) shows whether MW + host scales
  are mutually observable.

**Success Criteria:**
- Each blocker either resolved with a measured number or converted into a
  named, bounded caveat.
- A single defensible Δν_d statement with statistical *and* systematic error.

## Approaches to Test (data path, measured head-to-head)

### Approach A: keep the gapped npz as-is (pass-2 baseline)

**Description:** 26,528-channel npz with 61 gap junctions; `calculate_acf`
correlates by index lag and labels lags with mean(diff) = 7.532 kHz.

**Pros:** zero code/data change; what pass-2 already measured.
**Cons:** lag axis stretched 1.2340×; gap-straddling index lags mix
non-adjacent frequencies into low-lag bins; ripple lands at a non-physical
frequency, defeating instrumental-artifact identification.
**Complexity:** Low

### Approach B: gapless NaN-filled regrid at the native fine spacing

**Description:** re-embed all 26,528 channels into the full uniform grid
(32,736 channels at 0.390625/64 = 6.1035 kHz), NaN-filling the ~6,208 missing
channels; masked-array ACF then has index lag ≡ physical lag.

**Pros:** axis physically correct; ripple relocates to its true frequency;
no interpolation of data values (only placement, snap ≤ 0.5 channel).
**Cons:** 49% of channels snap by >0.25 fine channel (inter-block registration
drift up to 3.05 kHz — real property of the upchannelized product); ~19% NaN
rows reduce lag-bin counts.
**Complexity:** Medium

Both approaches were fully built and run through the same worktree code path
(`prepare_spectrum_from_config` → `measure_scintillation_bandwidth`, pass-2
flat-fielding ON, commit `41816c7d` of `feat/freya-chime-scint-config`).

## Experiment Setup

**Environment:** conda env `flits`; module under test shadowed to the worktree
`~/Developer/scratch/worktrees/flits-chime-scint/` (verified via
`module.__file__`).
**Test Data:** `scintillation/data/freya_chime_hi.npz`
(from `~/Data/Faber2026/dsa110/upchan_codetections/freya_chime_upchan.npy`,
U=64, provenance in that directory's `PROVENANCE.md`); gapless variant
`freya_chime_hi_gapless.npz` built by `e2_regrid.py`.
**Preserved artifacts:** all experiment scripts, the gapless npz, the variant
config, and output JSON are archived at
`~/Data/Faber2026/dsa110/scintillation-data/exp-dnu-2026-07-03/`.
**Constraints:** freya redshift is a PLACEHOLDER z = 1.0000
(`galaxies/foreground/config.py:46`) — every distance-dependent number below
is parametric, not citable.

## Experiments Run

### E1: gapped-grid diagnosis (`e1_grid_diag.py`)

**Observations:**
- 26,528 channels; channel-spacing histogram (Hz: count):
  {6104: 26466, 396735: 41, 787366: 11, 1177996: 4, 1568627: 3, 1959258: 2} —
  61 gap junctions, ≈ 6,208 missing fine channels (~97 coarse channels).
- mean(diff) = 7.532 kHz vs native 6.1035 kHz → **axis stretch 1.2340×**.

**Results:**
- ✅ CONFIRMED: `calculate_acf` (`scint_analysis/analysis.py:259+`) computes
  index-lag ACF and labels `positive_lags_mhz = lags * channel_width_mhz`
  with channel_width = mean(diff); on a gapped grid every reported lag (and
  therefore Δν_d) is stretched by 1.2340.
- ⚠️ Gap-straddling index pairs additionally mix physically distant channels
  into low-lag bins (not just a relabeling), so a post-hoc ÷1.234 of the
  pass-2 number is *not* equivalent to the regrid (40.2 kHz naive vs
  44.7 kHz measured below).

### E2: gapless regrid + ripple relocation (`e2_regrid.py`, `e2_ripple_locate.py`)

**Observations (regrid):** 32,736-channel uniform grid; snap error max
3.05 kHz (= 0.4996 fine channel), median 1.5 kHz, 49% of channels >0.25
channel — upchan blocks are internally uniform but inter-block offsets drift
by up to half a fine step; burst recovered at time bin 257 (z = 8.58).

**Results (gapless full-band rerun, same CLI path):**
- ✅ **Δν_d = 44.73 ± 7.93 kHz** (fit success, structure width = 1 channel,
  channel width 6.1035 kHz) — vs pass-2 gapped 49.6 ± 9.0 kHz.
- ✅ Ripple relocation: parabolic-refined ripple peak moved
  **0.4960 MHz (gapped) → 0.4024 MHz (gapless)**, ratio 1.233 — exactly the
  E1 stretch factor. The ripple is **grid-locked instrumental structure**,
  not a physical spectral feature.
- ⚠️ Residual 3% offset: 0.4024 MHz vs the coarse-channel spacing
  0.390625 MHz is unexplained; amplitude unchanged by flat-fielding, so it is
  not a static bandpass ripple — working hypothesis is burst-locked PFB
  leakage. Origin still open.
- ⚠️ **Fit-window systematic:** the ripple sits inside the default 1.0 MHz
  fit window and biases the Lorentzian fit. Refit vs `fit_lag_mhz`:
  44.72 ± 7.93 (1.0 MHz) / 57.21 ± 2.75 (0.3) / 67.72 ± 3.81 (0.2, ripple
  excluded). Fit-window systematic ~±20 kHz dominates the statistical error.

### E3: split-band and split-time consistency (`e3_splits.py`)

**Results (gapless grid, same masking/flat-fielding):**
- band 600–700: Δν_d = 40.46 ± 8.69 kHz @ 650.0 MHz, m = 0.191
- band 700–800: Δν_d = 78.93 ± 9.86 kHz @ 749.9 MHz, m = 0.181
- **band ratio hi/lo = 1.95 ± 0.48 vs ν^4.4 prediction 1.88; achromatic
  (instrumental) prediction 1.00** → rejects the achromatic hypothesis at
  ~2σ; consistent with MW diffractive scintillation scaling.
- time halves (bins 244–256 / 256–268): 39.42 ± 12.02 / 34.87 ± 10.43 kHz,
  m = 0.280 / 0.272 — mutually consistent, no time evolution artifact.

### E4: modulation-index dilution + two-screen coherence (`e4_quenching.py`)

**Results:**
- ACF model(0) = 0.348, large-lag baseline = 0.081 → zero-lag amplitude
  0.266 → **physical m_burst = √0.266 ≈ 0.52**. The reported
  modulation_index = 0.187 is std/mean *without* off-level subtraction
  (noise floor in the denominator) — a diluted diagnostic, not the physical
  modulation. E4 blocker is a **reporting bug**, not a physics tension.
- Host-screen bandwidth from the β co-model τ (#104 medians,
  τ_1GHz = 0.11439 ms, α = 4.3757): τ(700 MHz) = 0.545 ms →
  Δν_host = 0.339 kHz → **132× scale separation** from the MW Δν_d.
- Two-screen coherence constraint (`analysis.py:1111`), d_L(z=1 PLACEHOLDER)
  = 6791.3 Mpc: d_⊕,MW × d_hostscr,src ≤ **1426.8 kpc²** — satisfied by
  orders of magnitude for any plausible geometry (MW screen 0.3/1/3 kpc →
  host-screen limit 4756/1427/476 kpc). Even a 10× smaller d_L stays
  permissive. Both scales are mutually observable; m_burst ≈ 0.5 is
  consistent with moderate quenching. A *quantitative* m prediction requires
  the real redshift.

## Comparison Matrix

| Criterion | A: gapped as-is | B: gapless regrid |
|-----------|-----------------|-------------------|
| Lag-axis correctness | ❌ 1.2340× stretch + lag mixing | ✅ index lag ≡ physical lag |
| Δν_d (full band) | 49.6 ± 9.0 kHz (biased axis) | 44.7 ± 7.9 kHz (stat) ± ~20 kHz (fit window) |
| Ripple diagnosis | 0.4960 MHz, unidentifiable | 0.4024 MHz ≈ coarse spacing → instrumental |
| Physics consistency test | not possible | ν^4.4 ratio 1.95 ± 0.48 vs 1.88 ✅ |
| Data integrity | native | placement snap ≤ 0.5 fine channel (bounded) |
| Complexity | none | one regrid step, ~40 lines |

## Key Insights

1. All four blockers traced to two root causes: a **data-grid convention**
   (E1, E2 — gapped npz vs index-lag ACF) and an **estimator definition**
   (E4 — no off-subtraction in modulation_index). E3 was the physics check
   and it passed.
2. The naive ÷1.234 correction is wrong (40.2 vs 44.7 kHz): gap-straddling
   lag mixing distorts the ACF shape, not just its axis. The regrid is the
   only correct fix.
3. The dominant remaining uncertainty is the **fit-window systematic**
   (45–68 kHz) driven by the unmodeled 0.40 MHz instrumental ripple inside
   the fit range — not the statistical error.

**Surprising Findings:**
- Inter-block registration drift (up to half a fine channel) in the
  upchannelized product — blocks are internally uniform but not co-registered
  on one global grid.
- The ripple survives per-channel flat-fielding, ruling out a static bandpass
  origin (burst-locked PFB leakage suspected).

**Failed Assumptions:**
- "Ripple relocates to exactly 0.390625 MHz" — it landed 3% high (0.4024).
- "Regrid ≡ rescale by 1/1.234" — see insight 2.

## Recommendation

**Recommended Approach:** B — gapless regrid as the production data path,
plus the modulation-index reporting fix.

**Reasoning:** B is measured, bounded (snap ≤ 0.5 channel), and is the only
path on which the instrumental ripple is identifiable and the ν^4.4 physics
check can pass. Every science number should be quoted from the gapless grid.

**Current best statement (NOT yet citable):**
Δν_d(freya, CHIME 600–800 MHz) ≈ 45–68 kHz at 700 MHz
(44.7 ± 7.9 kHz statistical at the default 1.0 MHz fit window; fit-window
systematic to 67.7 ± 3.8 kHz when the 0.40 MHz instrumental ripple is
excluded), half-band values 40.5 ± 8.7 kHz @ 650 / 78.9 ± 9.9 kHz @ 750,
consistent with ν^4.4 MW scintillation; physical m_burst ≈ 0.52.

**Why Not A:** physically wrong lag axis; conclusions built on it are
irreproducible against the native grid.

**Implementation Considerations (durable-fix lane, owner-gated):**
1. Move the regrid into pipeline code — either the npz build convention or
   loader-level gap handling in `DynamicSpectrum`/`calculate_acf` — with
   tests; the scratch npz is not a production artifact.
2. Fix or annotate `modulation_index` (off-subtracted numerator/denominator,
   or report both diluted and ACF-derived m).
3. Handle the grid-locked ripple in the fit (mask lag windows near multiples
   of the coarse period, or report the fit-window sensitivity as a systematic).

## Conditions for Alternative Approaches

**If** the upstream npz build is regenerated with all coarse channels present
(no gaps), **then** approach A's code path is correct as-is and only the
modulation-index fix remains.

## Next Steps

1. Owner decision: open the durable-fix lane (issue + PR on dsa110-FLITS)
   implementing the three items above.
2. Obtain the real freya redshift (placeholder z = 1.0000) before any
   coherence/quenching number is quoted.
3. Identify the 0.4024-vs-0.390625 MHz 3% ripple offset (burst-locked PFB
   leakage hypothesis).
4. Merge `feat/freya-chime-scint-config` and bump the Faber2026 pipeline pin
   before the manuscript cites any scintillation number.

## References

**Code Files Tested:**
- `scintillation/scint_analysis/analysis.py:234-320` (calculate_acf), `:1111`
  (two_screen_coherence_constraint)
- `scintillation/scint_analysis/freya_scintillation.py:370` (normalize_bandpass),
  `:442-455` (wiring)
- worktree `feat/freya-chime-scint-config` @ `41816c7d`

**Archived experiment code + data:**
`~/Data/Faber2026/dsa110/scintillation-data/exp-dnu-2026-07-03/`
(e1_grid_diag.py, e2_regrid.py, e2_ripple_locate.py, e3_splits.py,
e4_quenching.py, freya_chime_hi_gapless.npz, configs, out/freya_scintillation.json)

---

## ADDENDUM 2026-07-04: dedispersion defect found — headline number DEPRECATED pending product regeneration

Owner figure inspection of the full-band view flagged the burst as too wide
(~8 ms) with no inter-channel drift. Investigation confirmed **the upchan
product was never coherently dedispersed**: the h17 script called
`coherent_dedisp(data, dm, time_shift=True)` but the function operates on a
COPY and returns the de-chirped array (write-back only with `write=True`) —
the return value was discarded and the RAW `tiedbeam_baseband` was
upchannelized. Evidence: (1) coarse-block-folded burst image shows a
full-magnitude intra-channel sawtooth (arrival drift ≈ 10.7 ms @650 /
7.0 ms @750 across each 64-fine-channel block, wrap at block edges), sign =
natural dispersion (lower fine frequency later); (2) magnitudes match
8.3 µs · DM · 0.390625 / ν³ exactly; (3) singlebeam metadata:
`tiedbeam_baseband` has no `DM_coherent` attr (raw), while `tiedbeam_power`
records `DM_coherent = 912.4699`.

**This resolves E2's residual**: the 0.4024 MHz grid-locked, burst-locked,
flat-field-surviving ripple is the on-pulse window (244–268) clipping the
per-block sawtooth — captured burst energy modulated with one-coarse-block
periodicity. Not PFB leakage.

**Status downgrades:** Δν_d = 44.7 ± 7.9 kHz (and the fit-window scan, the
half-band ratio, m_burst) were measured on the defective product — treat all
as *deprecated-fit suggestions* until the product is regenerated with the
de-chirp actually applied (`dedisp = coherent_dedisp(...)` →
`_upchannel(dedisp, ...)`, or `write=True`). E1's grid conclusions and the
#120/#121 code fixes are unaffected (the gapped-grid mislabeling is real and
independent). Prediction for the causal test: on the fixed product the burst
collapses to ~1–2 ms, the sawtooth vanishes, the 0.40 MHz ripple disappears,
and spectral S/N rises substantially.

### Outcome (2026-07-04): product regenerated — all four causal predictions confirmed

The h17 script was fixed (`dedisp = coherent_dedisp(data, dm, time_shift=True)`
→ `_upchannel(dedisp, ...)`; snapshot
`upchannelize_chime_h17_snapshot_20260704_dedispfix.py`, md5
`58c3f5b76a6b9cf9d12894e07db46e3d`), the product regenerated in the same docker
image, and the npz pair rebuilt with the byte-validated builder. Defective
originals quarantined in `DEFECTIVE_nodedisp_20260703/` (h17 + local, npy +
npz). New `freya_chime_upchan.npy` md5 `39c329ce0866c0229f931acab6592e03`.

1. **Burst collapse ✓** — ~8 ms → 0.66 ms FWHM-ish; peak z = 63 (600–800 MHz
   flat-fielded profile). `time_shift=True` aligns to 400 MHz, moving the
   burst to bin 386 (t = 126.5 ms); record-edge wrap artifacts at bins
   ~421–436 (excluded from windows).
   *Low-band circular wrap (owner-spotted in the full-band figure, verified):*
   the FFT phase-ramp shift is circular within each channel's valid buffer L,
   which shrinks toward 400 MHz (~348 bins at 412 MHz); wherever L < 387 the
   aligned burst index 386 wraps to bin (386 mod L) — predicted 38/24/13/4 vs
   observed 40/33/18/8 at 412/437/462/487 MHz, streak widths 5.9/5.2/2.6 ms
   matching the scattering law (5.6/3.5/2.7 ms) rather than the 25–42 ms
   un-de-chirped smear. So below ~505 MHz the burst is correctly de-chirped
   and aligned but circularly displaced into bins 2–40 (inside the [0, 180]
   noise window!) — full-band analyses must mask < ~505 MHz or unwrap; the
   600–800 MHz measurement band is unaffected (L ≥ 413 there).
2. **Sawtooth gone ✓** — folded (k,t) image: vertical stripe both subbands;
   centroid drift +0.41/+0.23 ms vs |7.0|/|10.7| ms predictions, R² ≈ 0.1
   (noise around zero).
3. **Ripple suppressed ✓** — sinusoid amplitude 0.085 → 0.0155 (5.5×
   absolute; ~14× relative to scintillation ACF amplitude); residual sits at
   the native 0.390625 MHz coarse-block period, consistent with the periodic
   RFI-mask/gap geometry, not the sawtooth.
4. **Spectral contrast up ✓** — m 0.187 → 0.319 (m_acf 0.301); relative
   statistical error 18% → 14%.

**Pass-4 measurement** (windows updated to [385, 393] burst / [0, 180] noise;
merged #120/#121 pipeline, grid regularization + flat-field on):

- Δν_d(700 MHz) = **35.4 ± 5.1 (stat) ± 13.9 (fit-window) kHz**
- fit-window scan: 35.4 / 45.6 / 49.3 kHz at 1.0 / 0.3 / 0.2 MHz — the window
  systematic still dominates and stays with the measurement.
- NE2025 MW-floor expectation at 700 MHz ≈ 76.6 kHz (1.6421 MHz @ 1.405 GHz
  scaled ν^4.4): the measurement sits ~2× below it, a *current-model result*
  to be interpreted in the two-screen framing (E4), not yet a claim.
- Run artifacts: `flits-rerun scintillation/plots/freya_chime_pass4_dedispfix/`
  (JSON + dynamic spectrum + ACF + structure-function figures).

**Band-extension check (2026-07-04, owner-prompted):** the 600–800 MHz
measurement band was chosen for floor resolvability (NE2025 floor ∝ ν^4.4
drops to 1–3 fine channels below ~500 MHz) and scattering S/N — not because
of the low-band wrap, which only affects < ~505 MHz. Verified empirically: a
505–800 MHz run (identical config; 40,173 channels, zero wrapped) gives
Δν_d = 35.85 ± 4.76 kHz vs 35.43 ± 5.06 for 600–800 — identical central
value, 6% statistical gain, but the dominant fit-window systematic inflates
13.9 → 16.5 kHz (scan 35.8/49.5/52.3 vs 35.4/45.6/49.3), so total error
worsens 14.8 → 17.2 kHz. The 505–600 MHz scintles (3–6 channels wide,
marginally resolved) add window sensitivity, not information. 600–800 MHz
stands. Unwrapped full-band display confirms the burst is continuous
400–800 MHz with the scattering tail following τ ∝ ν⁻⁴·⁴ (display script
`fullband_unwrap.py`, canvas identity: burst at absolute bin 386 regardless
of per-channel capture offset).

**Generation 3 (2026-07-04, owner-requested "low band usable"):** the
`time_shift=True` circular wrap made the low band unusable in the files, so
the product was regenerated a third time with a new `--no-time-shift` script
flag (pure per-channel de-chirp, no roll) and inter-channel alignment moved
into the npz builder (`build_npz_aligned_20260704.py`): integer-bin placement
onto a padded 446-bin canvas using the same delay formula and per-channel
`fpga_count` capture times pulled from the singlebeam h5 (K_DM verified
identical to baseband_analysis's constant). No circular wraps anywhere.
Verification: sawtooth null (−0.71/−0.20 ms vs |7.0|/|10.7| predictions);
burst peak flat at bin 254–255 across 600–800 MHz; low-band peaks lag by the
expected ~0.3–0.4 τ(ν) scattering peak-shift + 0.07 pc/cm³ DM offset (912.4
used vs CHIME structure DM 912.4699); **low band now z = 10.6–13.0 per
25-MHz slice** (was 3–4 with the wrap polluting the flat-field off-window).
Known narrowband RFI at 482–487 MHz near bin 391. **Pass-5 regression:
Δν_d = 35.19 ± 4.42 (stat) ± 17.0 (fit-window) kHz, m_acf = 0.304 —
consistent with pass-4 at 0.05σ; this is now the canonical measurement**
(windows [253, 264]/[10, 200]). Generation 2 quarantined in
`SUPERSEDED_timeshift_20260704/`. Full provenance:
`upchan_codetections/PROVENANCE.md` (generation history section).

E3-style split-band/split-time consistency and the E4 quenching update have
not yet been rerun on the fixed product; the E3/E4 numbers in this doc remain
defective-product values.

## Appendix: Raw Experiment Data

```
E1: n_chan 26528; diff histogram (Hz: count) {6104: 26466, 396735: 41,
    787366: 11, 1177996: 4, 1568627: 3, 1959258: 2}; missing-channel
    equivalent 6208.1; mean diff 7.5322e-3 MHz -> ratio vs native 1.2340445

E2 regrid: n_full 32736; snap error MHz: max 3.05e-3, median 1.5e-3,
    frac>0.25ch 0.49; fill fraction 0.8104; burst peak bin 257, z 8.58
E2 gapless JSON: dnu_mhz 0.04472631967443332 +/- 0.007928177501085373;
    modulation_index 0.18699; channel_width_mhz 0.006103515625
E2 ripple: pass2_gapped peak 0.4960 MHz (amp 0.118); gapless peak 0.4024 MHz
    (amp 0.134); coarse spacing 0.390625; mislabel prediction 0.4821
E2 fit-window scan (gapless): fit_lag 1.0 -> 44.72 +/- 7.93 kHz;
    0.3 -> 57.21 +/- 2.75; 0.2 -> 67.72 +/- 3.81

E3: band 600-700 -> 40.46 +/- 8.69 kHz @ 650.0, m 0.191;
    band 700-800 -> 78.93 +/- 9.86 kHz @ 749.9, m 0.181;
    band ratio hi/lo = 1.95 +/- 0.48 | nu^4.4 prediction 1.88 |
    achromatic prediction 1.00
    time (244,256) -> 39.42 +/- 12.02, m 0.280;
    time (256,268) -> 34.87 +/- 10.43, m 0.272

E4: ACF model(0) 0.348, baseline 0.081 -> amplitude 0.266 -> m_burst 0.52
    tau_host(700 MHz) 0.545 ms -> Dnu_host 0.3389 kHz; separation 132x
    d_L(z=1 PLACEHOLDER) 6791.3 Mpc ->
    d_earth,MW x d_hostscr,src <= 1426.8 kpc^2
    examples: MW screen 0.3 kpc -> host limit 4756 kpc; 1.0 -> 1427; 3.0 -> 476
```
