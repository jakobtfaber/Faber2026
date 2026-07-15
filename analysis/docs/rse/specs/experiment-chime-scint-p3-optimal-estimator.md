# Experiment P3: delay-domain optimal quadratic Δν_d estimator — freya, CHIME band

---
**Date:** 2026-07-15
**Author:** Claude (Fable 5), under the owner's 2026-07-15 in-session sanction
("build P3") following the P2 `DOCUMENTED-FAIL`
**Status:** PREDECLARED — thresholds frozen below; Gate 0b runs first and can
terminate the experiment before any implementation; no on-pulse statistic may
be computed before gates G1″ and G2″ pass; any gate failure is a terminal
`DOCUMENTED-FAIL` with no unblinding
**Related documents:**
- [P3 implementation plan (handoff)](handoff-2026-07-15-04-00-p3-optimal-estimator-dev.md)
- [P2 predeclaration](experiment-chime-scint-routeb-voltage.md) — the ratio construction and discipline P3 inherits
- P2 result: pinned pipeline `analysis/chime-scintillation/experiments/p2-routeb-voltage/RESULT.md` (FLITS #180)
- [Gate 0 detectability](experiment-chime-scint-gate0-detectability.md) — the idealized ceiling and admissibility window
---

## Why P3 (and only what P3 changes)

P2 proved the on/off ratio cancels the ~35 kHz instrumental common mode
algebraically on real data (G2: 0/24 nulls, amplitude 0.586 → ≲ 0.006) and
that its **lag-space cross-ACF + Lorentzian curve-fit** cannot recover any
injected width at the real effective modulation `f_b·m ≈ 0.0075–0.0085`
(G1: 0/6 detectable cells; fits pin at 20–45 kHz on noise). Gate 0's GO was
priced for the *optimal quadratic* (Fisher) estimator, ~10× above the
lag-space fit's demonstrated sensitivity. P3 keeps P2's ratio-spectrum
construction **unchanged** and replaces only the statistic downstream of the
ratio spectra with the matched estimator Gate 0 priced. It is the last
in-house move: the outcomes are a broad-scintle detection or a clean
radiometer-limited exclusion for the manuscript.

## Estimator (frozen)

Delay-domain matched quadratic estimator on the S2-style split ratio spectra
(mathematically equivalent to the direct quadratic estimator for stationary
noise; O(N log N)):

1. **Inputs:** two split ratio spectra `r₁(ν), r₂(ν)` built exactly as P2's S2
   (disjoint interleaved on/off time halves ⇒ independent noise between
   splits; per-split pol mean `(R_p0 + R_p1)/2`), high band (627–800 MHz,
   23 064 fine channels @ 6.1036 kHz), RFI/LTE mask as P2's frozen config,
   block-demeaned within 64-channel coarse blocks.
2. **Transform:** FFT each split over frequency → `R₁(τ), R₂(τ)` (per coarse
   block or tapered full band — decided by test T5 on synthetic data and
   frozen by addendum **before** G1″ runs).
3. **Cross power:** `P̂(τ) = Re[R₁(τ) R₂*(τ)]` — noise-bias-free at every
   delay because the splits carry independent noise (P2's S2 trick, moved to
   the delay domain).
4. **Signal template:** for a unit-variance Lorentzian-ACF gain field with
   HWHM `Δν_d`, the delay-domain power is the FFT of
   `C(d) = 1/(1 + (d/w_ch)²)` — a one-sided exponential
   `T(τ; Δν_d) ∝ exp(−2π Δν_d τ)` — multiplied by the **block-demeaning
   transfer function** computed explicitly (test T4). Amplitude parameter
   `a = (f_b·m)²`.
5. **Noise weighting:** `Var[P̂(τ)]` measured empirically from ≥ 100 off-pulse
   split-pair null realizations (P2's G2 permutation construction, seeds
   `900000 + i`). No whiteness assumption — oversampling correlates adjacent
   channels and the empirical variance absorbs it.
6. **Matched amplitude:**
   `â(Δν_d) = Σ_τ w(τ) P̂(τ) T(τ) / Σ_τ w(τ) T(τ)²`, `w(τ) = 1/Var[P̂(τ)]`,
   `σ_â = (Σ_τ w T²)^{−1/2}`, scanned on a 25-point log grid
   `Δν_d ∈ [20, 400] kHz`. Detection statistic: `max_Δν â/σ_â`,
   trials-corrected against the **empirical** null distribution of the same
   max (from the ≥ 100 null realizations), never a Gaussian assumption.
7. **Optional refinement (only if the T-tests demand):** per-block direct
   `C_n^{-1}`-weighted quadratic estimator (64×64 covariances); the
   delay-domain version stays the reference implementation.

## Gate 0b — measured-noise forecast (frozen; runs FIRST, before any implementation)

**Question.** Gate 0 used idealized radiometer algebra. Recompute the ceiling
with the **measured** null variance `Var[P̂(τ)]` from real off-pulse data. If
the measured noise already sinks the window, stop before building (protects
against a fourth build-then-fail).

**Procedure (frozen).** Build ≥ 100 null split-pair realizations from real
off-pulse frames (100-sample pseudo-on ⟂ disjoint reference, S2 construction,
seeds `900000 + i`); measure `Var[P̂(τ)]`; compute
`SNR_forecast(Δν_d, m) = (f_b·m)² · sqrt(Σ_τ T²(τ)/Var[P̂(τ)])` with the
T4-corrected template, `f_b = 0.05`, on the Gate-0 grid
`Δν_d ∈ {35, 77, 127, 213, 352} kHz × m ∈ {0.15, 0.17}`.

**Frozen floor:** at `m = 0.17`, `Δν_d = 213 kHz`:

- `SNR_forecast ≥ 3` → **proceed to implementation** (G1″/G2″).
- `SNR_forecast < 3` → **DOCUMENTED-FAIL-BY-FORECAST** — terminal; nothing is
  built; the manuscript takes P2's censored exclusion with the measured-noise
  curve as the quantitative closure.

The full forecast curve is reported either way and appended to this record
as §Gate 0b result.

## Frozen gates (after Gate 0b passes)

**G1″ — injection recovery (burst-blind).** Identical grid and seeds to P2:
`m ∈ {0.15, 0.17} × Δν_d ∈ {35 (must-fail control), 77, 127, 213, 352} kHz ×
50 realizations`, seed `= 1000·cell + realization`, injected multiplicatively
into real off-pulse frames relabeled pseudo-on at `f_b = 0.05` through the
full estimator. A cell **certifies** when median recovered `Δν_d` is within
±30 % of injected, |median amplitude pull| ≤ 2, and ≥ 90 % of realizations
converge. **PASS requires:** every `Δν_d ≥ 213 kHz` cell certifies (the
Gate-0 ≥5σ window, both m values); the 35 kHz control must NOT certify. The
77/127 kHz cells are reported but not required (they sit between the 3σ and
5σ ceilings).

**G2″ — null campaign (burst-blind).** ≥ 100 off-pulse split-pair null
realizations (seeds `900000 + i`) through the full estimator including the
`Δν_d` scan; the trials-corrected max-significance distribution defines the
detection threshold; PASS requires the family-wise false-alarm rate at that
threshold ≤ 5 % (empirical, Šidák-consistent) and no null exceeding it.

**G3 — admissibility (after unblinding; unchanged from P2).** A detection
claim requires fitted `Δν_d` inside the Gate-0 ≥3σ window (≥ 77 kHz at
m = 0.17, ≥ 127 kHz at m = 0.15) AND trials-corrected significance ≥ 5.
Anything else is the censored exclusion: "no CHIME-band scintillation with
Δν_d above the window at m ≥ 0.15; smaller Δν_d unconstrained
(radiometer-limited)."

**Unblinding rule.** The on-pulse statistic is computed exactly once, after
G1″ and G2″ both pass, by the orchestrator (never the implementing agent),
with the frozen configuration. The structural guard
(`ON_PULSE_GUARD = (250, 350)`, `BlindingError`, `allow_unblind`) stays; the
implementing agent never passes `allow_unblind=True`. No threshold, window,
or estimator change after first sight of on-pulse data; a post-hoc change
creates a new experiment requiring fresh owner sanction.

## Test battery (all must pass before G1″ runs; frozen)

- **T1 bandpass invariance:** multiply synthetic frames by arbitrary `g(ν)`
  (including the measured 35 kHz-shaped realization); `â` invariant to
  machine precision (P2 achieved ~6e-19 on the ratio construction).
- **T2 unbiasedness:** pure synthetic (Gaussian scintle field + radiometer
  noise at the real `ε² ≈ 2.6`): `⟨â⟩ = a_inj` within errors across the grid.
- **T3 error calibration:** empirical scatter of `â` over realizations vs
  predicted `σ_â` ∈ [0.8, 1.2].
- **T4 block-demeaning transfer:** compute the suppression of `T(τ)` at small
  `τ` from 64-channel block-demeaning (analytically or numerically); verify
  the recovered amplitude corrects for it.
- **T5 block vs full-band:** compare per-coarse-block vs tapered-full-band
  SNR on synthetic; freeze the winner by addendum to this record before G1″.
- **T6 blinding guard:** unit test that on-pulse access raises without
  `allow_unblind`.

## Data and provenance (all in-house; no external requests)

- Input: pinned local npy set
  `~/Data/Faber2026/dsa110/upchan_codetections/crossacf-2026-07-14/`
  (pol0/pol1/intensity, 57 024 × 437; SHA-256 verified against the pipeline
  `DATA_MANIFEST.yaml` before any run). High band 627–800 MHz. On-pulse
  samples 250–350 (BLINDED), off-pulse 0–200 + post-350 remainder. h17 not
  needed.
- Code lands in FLITS: `scintillation/scint_analysis/optimal_dnu.py` + tests,
  branch `scint/p3-optimal-estimator` off main `1085de0`; experiment record
  `analysis/chime-scintillation/experiments/p3-optimal-estimator/` (RESULT.md,
  frozen config hash, gate JSONs, figures for visual vetting); then a
  Faber2026 pin bump — the C1/P1/P2 landing pattern.
- Seeds: G1″ `1000·cell + realization`; nulls/Gate 0b `900000 + i`.
  Environment: conda `py312`; package versions recorded in RESULT.

## Deliverables

1. §Gate 0b result appended to this record (either verdict).
2. If built: FLITS PR with estimator + T1–T6 + G1″/G2″ harness + frozen
   config + diagnostic figures; RESULT.md with one of the three terminal
   verdicts: `qualified measurement` (G3 detection), `censored exclusion`
   (G3 non-detection), or `DOCUMENTED-FAIL` (gate failure, no unblinding).

## Gate 0b result (2026-07-15, same day): DOCUMENTED-FAIL-BY-FORECAST under the frozen spec

Executed as predeclared (`gate0b_forecast.py` in the FLITS experiment dir,
branch `scint/p3-optimal-estimator`): 100 null split-pair realizations from
real off-pulse data (seeds 900000+i), Monte-Carlo templates carrying the T4
demeaning transfer (seeds 700000+…), 50 end-to-end multiplicative injections
at the floor cell (G1 cell-8 seeds). Input SHA-256s match the pipeline
`DATA_MANIFEST.yaml`.

**Frozen floor (m = 0.17, Δν_d = 213 kHz): FAILED.** Forecast SNR 1.24
(full-band transform) and 0.61 (per-block), against the frozen floor of 3.
End-to-end injection check: 1.6σ — the formula holds. σ̂ calibration
(empirical/analytic) 1.03–1.29. Under the frozen spec the experiment is
terminal: **nothing is built.**

**Root cause — the 64-channel block demeaning, not the radiometer noise.**
The forecast *decreases* with Δν_d (352 kHz: 0.73σ full-band), the opposite
of Gate 0's idealized √w growth: a scintle wider than the 390.6 kHz coarse
block is nearly constant within each block, so per-block demeaning removes
most of its variance. The demeaning was inherited from the pre-ratio routes,
where it protected against the instrumental common mode — protection the
ratio statistic has made redundant (P2 G2: cancellation to ≲ 0.006).

**Diagnostic (explicitly outside the frozen spec; off-pulse data only).**
Removing block demeaning (global mean removal only, full-band FFT, same
measured-noise weighting) restores the window at m = 0.17: 3.2σ at 127 kHz,
4.1σ at 213 kHz, 5.2σ at 352 kHz — tracking Gate 0's idealized curve within
~25 %. Excluding delay bins k < 11 (spectral structure smoother than
~13 MHz, where an intrinsic burst envelope would contaminate) costs only
~7 %: 3.0σ / 3.8σ / 4.5σ. End-to-end injections at the floor cell
(null-mean-subtracted, k ≥ 11): **3.2σ**. The null distribution carries a
~1σ positive mean offset, removable by null calibration.
Artifacts: `gate0b_forecast.{py,json,png}`,
`diagnostic_nodemean{,_hardening}.py`, `gate0b_nodemean_diagnostic{,2}.json`,
`gate0b_owner_decision.png` (FLITS experiment dir).

**Consequence and owner decision (per the unblinding rule, a spec change is a
new experiment requiring fresh owner sanction):**

- **Option A — stop (the predeclared fail branch).** The paper takes P2's
  censored exclusion; the measured-noise curves close the campaign
  quantitatively.
- **Option B — sanction P3′ (amended spec):** identical discipline, three
  amendments — no block demeaning (global mean only), delay-bin exclusion
  k ≥ 11 frozen as the envelope control, null-mean-subtracted matched
  estimator. Re-checked floor passes (3.8σ formula / 3.2σ injections at
  213 kHz). **Honest ceiling:** 3–4.5σ across the admissible window, below
  the inherited G3 detection bar of 5σ — so the realistic product is a
  calibrated 3–4σ-sensitive upper limit on Δν_d ∈ [127, 352] kHz (a
  quantified closure P2 could not deliver), with a qualified detection
  possible only if the true signal sits at the favorable edge and fluctuates
  upward. The G3 bar itself is NOT amended.

**Status: awaiting owner choice between A and B. No further computation on
burst data until then.**

## P3′ amendment (2026-07-15, same day — owner-sanctioned Option B in-session)

The owner sanctions the amended experiment. Three spec changes relative to the
frozen estimator above; everything else (G1″/G2″ grids, seeds, G3, the
unblinding rule, the test battery) is unchanged:

1. **No block demeaning.** Global mean removal only, full-band FFT over the
   23 064 fine channels. Safe now because the ratio statistic already cancels
   the common mode algebraically (P2 G2); the demeaning it replaced was
   protection the ratio has made redundant. This resolves T5 by amendment
   (full-band is frozen; the per-block variant is retired).
2. **Delay-bin exclusion `k < 11` (frozen).** Spectral structure smoother than
   ~12.8 MHz is excised from the matched sum — the envelope control replacing
   demeaning: an intrinsic burst spectral envelope (common to pols and time
   halves, invisible to the null campaign) lives at these lowest delay bins.
   Cost measured at ~7 % of SNR.
3. **Null-mean-subtracted z-scores with a calibration/evaluation null split.**
   Per-Δν_d detection score `z = (â − ⟨â⟩_null)/σ_null`; nulls seeds
   `900000 + i` with `i = 0–99` the calibration half (mean, σ per grid point)
   and `i = 100–199` the evaluation half (trials-corrected max-z
   distribution). Scan-template Monte-Carlo seeds `750000 + 1000·grid_index +
   j` (disjoint from all prior seed spaces). G2″ PASS interpretation, frozen
   before any burst data: the two independent null halves must give a
   consistent trials-corrected 95th-percentile max-z (within 15 %), and the
   T3 σ-calibration must hold on the evaluation half.

Scan-estimator semantics for G1″ certification (frozen): recovered `Δν_d` =
argmax of `z` over the 25-point log grid; amplitude pull evaluated at the grid
point nearest the injected width; "converged" = finite `â` and `σ_â`.

**Re-checked Gate 0b floor under this amendment: PASSES** — 3.8σ (formula) /
3.2σ (end-to-end injections) at m = 0.17, Δν_d = 213 kHz, k ≥ 11
(§Gate 0b result diagnostics). The G3 bar stays at 5σ; the owner sanctions
the build understanding the realistic product is a calibrated upper limit on
`Δν_d ∈ [127, 352] kHz`.
