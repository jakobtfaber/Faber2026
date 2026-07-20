# Assessment: CHIME scintillation successor routes after the P1 refutation

---
**Date:** 2026-07-15
**Author:** Claude (Fable 5), under the owner's 2026-07-15 amendment to the
scope-fork record: CHIME scintillation measurement remains an active goal of
this paper.
**Status:** SANCTIONED by owner 2026-07-15 (in-session): Gate 0 approved;
Route B (voltage-domain) approved to proceed immediately, conditional on
Gate 0; Route A's external calibrator-data request to the CHIME collaboration
is DECLINED — the owner keeps this in-house ("we'll keep hacking away at this
ourselves"), so Route A is viable only if suitable calibrator baseband already
exists on infrastructure we control
**Related documents:**
- [Decision: P1 scope fork §Owner amendment](../decision/decision-2026-07-15-p1-scope-fork.md) — governs this assessment
- [Research: the common-mode instrumental response](../research/research-chime-scint-instrumental-common-mode.md) — the measured confounder (untracked lane at time of writing; numbers restated here so this record is self-contained)
- [P1 result](../plan/plan-chime-scint-corrected-products-revival.md) — Phase 3 `DOCUMENTED-FAIL`
---

## What P1 established (and refuted)

P1 regenerated the freya product from coherently dedispersed baseband with
five predeclared window/oversampling variants. None moved the common-mode
statistic: off-pulse lag-1 polarization cross-correlation stayed at 0.59–0.62
against a baseline of 0.587, and the fitted Lorentzian amplitude stayed at
0.62–0.68 against a baseline of 0.586. Windowing the second-stage FFT does
essentially nothing, which **refutes the spectral-leakage origin hypothesis**:
the ~35 kHz common-mode frequency structure is not created by the
fine-channelization; it is already present in the baseband within each
390.625 kHz coarse channel (first-stage PFB response, analog bandpass
structure, and their appearance in detected intensity).

Fixed constraints any successor must respect (measured on the retained freya
product; see the common-mode research record):

- Instrumental common-mode Lorentzian: amplitude `A = 0.586`, width
  `w ≈ 35.4 kHz` — the same scale as the target Δν_d.
- Target scintillation at the real burst's modulation: `m² ≈ 0.023–0.029` —
  the confounder is 20–26× stronger.
- Removal requirement: ≥ 99 % suppression still leaves a residual comparable
  to the signal; **≥ 99.9 % is required** for a clean measurement.
- S/N ceiling: the burst is ~5 % above background in the retained product, so
  scintillation modulates *total* intensity by only ~0.75 % against the 59 %
  common-mode term. This bound is product-level, not estimator-level.

## Gate 0 (mandatory, before any route runs): detectability on paper

A deterministic calculation, no burst data touched: given each route's
*best-case* suppression ceiling and the measured S/N, compute the expected
significance of a Δν_d recovery on a single freya realization. If a route
cannot clear a predeclared significance floor even at its ceiling, it is not
sanctioned — the campaign answer becomes "no route exists on current data,"
which is itself the publishable outcome the owner amendment anticipates.
Gate 0 is cheap (algebra + the existing simulation engine), fully
predeclarable, and protects against a third mechanism-level fail.

## Route A — external instrumental characterization (steady calibrator)

**Mechanism.** Run a bright steady source (Cas A, Tau A, 3C-class) through the
*identical* baseband → coherent-dedispersion(bypass) → upchannelization path,
measure the common-mode response on a source with no scintillation at the
35 kHz scale, and divide it out of the burst product before the ACF.

**Why it could work.** It is the only route that measures the confounder
independently of the burst. If the common mode is a stable filter shape
(PFB × analog chain), division can in principle reach deep suppression.

**Why it could fail — the stationarity crux.** Division only reaches 99.9 %
if the response is stable between calibrator epoch and burst epoch to that
same level, through different beamforming phases, pointings, and gain states.
The off-pulse template subtraction already failed precisely because
realizations of this structure differ; a calibrator observation is another
realization. A predeclared stationarity gate (two calibrator epochs, measure
the residual after cross-division) answers this before any burst data enters.

**Requirements & unknowns.** CHIME baseband of a suitable calibrator processed
through `baseband-analysis` on h17. Whether archived calibrator baseband
exists and is obtainable is an external dependency (CHIME/FRB collaboration
ask) — the single biggest schedule risk. Cost if data exists: days, mostly
pipeline reuse.

## Route B — voltage-domain cross-statistics

**Mechanism.** The instrumental response is *linear on voltages* and
*multiplicative on detected intensity*. Working on the complex fine-channel
voltages (which P1's regeneration path already produces on h17 for freya),
second-order cross-statistics between polarizations can separate a common
multiplicative bandpass from source-flux modulation — scintillation modulates
the source flux only, the bandpass multiplies both polarizations identically.

**Why it could work.** No external data needed — the coherently dedispersed
freya baseband already sits on h17, and the P1 machinery reads it. The
separation is structural (phase/amplitude algebra on voltages), not a
template subtraction, so its ceiling is not bounded by realization-to-
realization stationarity.

**Why it could fail.** Method development is real work: the estimator must be
built, its null behavior calibrated on injections, and the polarized-flux
coupling handled (freya's pol0/pol1 carry different source contributions).
The 0.75 % effective signal fraction still applies — Gate 0 decides whether
even a perfect bandpass separation leaves a detectable signature.

## Recommendation

1. **Run Gate 0 now** for both routes (it is one predeclared calculation with
   two suppression-ceiling inputs). No owner input needed to run it; its
   verdict comes back to the owner with this assessment.
2. **If both survive Gate 0:** sanction **Route B first**. It has no external
   data dependency, reuses the P1 h17 assets, and its failure mode is
   informative (a calibrated null on the voltage statistic strengthens the
   information-limited conclusion). Route A stays queued behind the CHIME
   collaboration data ask, which can be initiated in parallel at zero
   analysis cost.
3. **Either route runs as a new predeclared experiment record** (P2-class ID,
   frozen gates before burst data inspection, blinded where applicable),
   per the stop-rule discipline that C1 and P1 followed.

## Owner ask — ANSWERED 2026-07-15 (in-session)

- Sanction Gate 0 → **YES.**
- Route order → **Route B starts immediately** (conditional on Gate 0);
  Route A demoted to in-house-data-only.
- CHIME collaboration ask for calibrator baseband → **DECLINED.** No external
  data request; self-reliant routes only.

Gate 0 execution record:
[experiment-chime-scint-gate0-detectability.md](../experiment/experiment-chime-scint-gate0-detectability.md).
