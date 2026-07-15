# Experiment P4: exploratory intrinsic-envelope modeling + residual scintillation search — freya, CHIME band

---
**Date:** 2026-07-15
**Author:** Claude (Fable 5), under the owner's 2026-07-15 in-session sanction
of the exploratory follow-up to P3′
**Status:** PREDECLARED (exploratory class) — the single blind on-pulse
computation was spent in P3′ (owner-authorized), so **no P4 result carries
blind-analysis evidential weight and every P4 statement is labeled
exploratory/post-hoc**. Predeclaration still binds: every threshold, grid,
selection rule, and verdict criterion below is frozen BEFORE any residual,
sub-band, or component statistic is computed. A post-hoc change to any of
them is reported as a further degradation of evidential class, not silently
absorbed.
**Related documents:**
- [P4 implementation plan (handoff)](handoff-2026-07-15-06-50-p4-envelope-model-dev.md)
- [P3 record incl. §P3′ amendment and §Outcome](experiment-chime-scint-p3-optimal-estimator.md)
- P3′ results: pinned pipeline `analysis/chime-scintillation/experiments/p3-optimal-estimator/` (`RESULT.md`, `unblind_onpulse.json`)
---

## Question

Freya's CHIME-band on-pulse ratio spectrum is dominated by broad intrinsic
spectral structure (â ≈ 0.8–1.2×10⁻³ across the P3′ scan; implied
modulation ~0.6). Can that envelope be modeled and divided out well enough
that the residual regains sensitivity to a scintle at the calibrated ceiling
(`a = (f_b·m)² ≈ 5–7×10⁻⁵`), and does any surviving residual structure pass
the physical discriminants that separate propagation from emission?

## Data and access rules

- Same pinned inputs as P2/P3′ (`~/Data/Faber2026/dsa110/upchan_codetections/
  crossacf-2026-07-14/`; SHA-256s must match the pipeline
  `DATA_MANIFEST.yaml` and P3′ `frozen_config.json.inputs_sha256`).
- High band 627–800 MHz; P2 frozen mask (19 465 good channels); on-pulse
  samples 250–350; off-pulse pool 10–200 ∪ 360–437.
- On-pulse reads are permitted (P3′ unblinding spent, owner-sanctioned);
  every `allow_unblind=True` call site in P4 code carries the comment
  `# P4 exploratory: post-unblinding, owner-sanctioned 2026-07-15`.
- **Look accounting:** the real on-pulse residual z-scan is computed exactly
  once per model family at its E2-frozen operating point (three looks
  total), and the trials correction in §E3 accounts for taking their
  maximum. No other real-residual statistic may be inspected before the E2
  freeze.

## E0 — envelope characterization (descriptive; no thresholds consumed)

On-pulse ratio spectrum `R(ν)` via the P3′ S2 construction (both split
halves and their mean): delay power spectrum (full k, no cut),
autocorrelation scale(s), amplitude distribution, half-to-half correlation
coefficient (time stability). Profile inspection of samples 250–350.

**Frozen component rule (for E3b availability):** sub-components are local
maxima of the Gaussian-smoothed (σ = 2 samples) on-pulse profile with peak
S/N ≥ 5 against the off-pulse noise and separation ≥ 3 samples. If ≥ 2
components qualify, E3b runs; otherwise it is recorded as unavailable.

## E1 — envelope model families (frozen grids)

Residual is multiplicative: `r(ν) = R(ν)/E(ν) − 1`, `E(ν)` clipped below at
the 5th percentile of its positive values to avoid division blowups
(clipped channels → NaN, treated as masked).

- **M1 spline:** cubic smoothing spline in ν, knot spacing
  `Λ ∈ {0.5, 1, 2, 5, 10} MHz`.
- **M2 Gaussian process:** squared-exponential kernel, length scale
  `ℓ ∈ {0.5, 1, 2, 5, 10} MHz`, noise level fixed from the off-pulse
  per-channel variance; fit on a 4× decimated grid and interpolated.
- **M3 delay high-pass:** zero delay bins `k < k_env`,
  `k_env ∈ {25, 50, 100, 200}` (removes structure smoother than ≈ 5.6, 2.8,
  1.4, 0.7 MHz), inverse-transform; residual formed multiplicatively from
  the retained smooth part.

Downstream statistic: the P3′ `MatchedScan` (25-point grid 20–400 kHz,
k ≥ 11 exclusion retained) with **templates and null calibration rebuilt
through the identical model+subtract chain per (family, scale) operating
point** — the P3/Gate-0b lesson: every filter's transfer lives inside the
Monte-Carlo templates. Template seeds `760000 + 1000·grid_index + j`
(disjoint from all prior spaces).

## E2 — injection calibration on the real envelope (frozen)

**Recovery arm.** Multiply the real on-pulse frames by synthetic scintle
gains `(1 + m·δ(ν))`: grid `m ∈ {0.15, 0.17} × Δν_d ∈ {77, 127, 213, 352}
kHz × 50 realizations`, seed `600000 + 1000·cell + realization`
(`cell = m_index·4 + dnu_index`). Chain: inject → model fit → subtract →
matched scan. A cell **certifies** when the median recovered width (argmax
z) is within ±30 % of injected, |median amplitude pull| ≤ 2 (σ from the
same-operating-point null set), and ≥ 90 % of realizations are finite.

**Noise/null arm.** 100 off-pulse permutation nulls (seeds `650000 + i`)
through each chain: per-operating-point null mean/σ (for the pulls and the
z calibration) and the radiometer+filter confusion component.

**Model-mismatch control (surrogate arm).** For each pair of distinct
families (A fits, B analyzes): surrogate spectra
`E_A(ν)·(1 + radiometer noise at the measured off-pulse level)` (50
realizations, seeds `680000 + …`) run through B's chain at each scale. The
resulting spurious max-z distribution bounds envelope-model-mismatch false
structure. A (family, scale) is **control-clean** if its surrogate p95
max-z ≤ the noise-arm p95 max-z × 1.5.

**Operating-point rule (frozen — uses injections and surrogates only,
never the real residual):** per family, the scale with the highest count of
certified cells; ties broken by (i) certification at 213 kHz, (ii) smaller
Λ/ℓ (or larger k_env) — less envelope leakage. A family with zero certified
cells at any `Δν_d ≥ 127 kHz`, or no control-clean scale, is dropped.

**Fail branch:** if all three families drop, P4 terminates as
`DOCUMENTED-FAIL (envelope not separable)` with the E2 tables as the
quantitative closure. The real residual is then never scanned.

## E3 — the three real-residual looks and the physical discriminants (frozen)

The real on-pulse residual is scanned once per surviving family at its
operating point. Detection statistic: max over the three looks of the
null-calibrated max-z; reference distribution: the same max-over-families
statistic on the 100 noise-arm nulls (empirical trials correction).

A **residual-structure candidate** requires trials-corrected significance
≥ 95th percentile of that null max distribution AND amplitude admissibility:
`â_res` at the argmax implies `m = √â_res / f_b ∈ [0.05, 0.30]` (physical
scintillation range around the 0.15–0.17 prior; anything larger is
envelope leakage by construction).

A candidate is promoted to **exploratory scintillation candidate** only if
it additionally passes:

- **E3a sub-band scaling** (run only if the candidate's full-band
  trials-corrected z ≥ 5 — below that the test is underpowered): four equal
  sub-bands of 627–800 MHz; per-sub-band recovered width; weighted fit of
  `Δν_d(ν) ∝ ν^α` must give `α ∈ [3, 5]`.
- **E3b component correlation** (only if E0 finds ≥ 2 components): Pearson
  correlation of per-component residual spectra > the 95th percentile of
  the off-pulse split-pair null correlation distribution.
- **E3c cross-band consistency:** candidate width consistent within a
  factor of 3 with the trusted DSA-band Δν_d measurement for freya
  extrapolated by `(ν_CHIME/ν_DSA)^4.4` (the DSA value is read from the
  manuscript's trusted ledger at evaluation time; it is a measured
  constant, not a tunable threshold).

## Verdict taxonomy (frozen; all manuscript statements labeled exploratory)

1. **Exploratory scintillation candidate** — candidate + E3a (if powered) +
   E3c pass (+ E3b if available). Reported with full post-hoc caveats;
   never a blind-equivalent claim.
2. **Exploratory upper limit** — no candidate above the trials-corrected
   threshold: the E2-calibrated post-subtraction sensitivity becomes the
   quantified limit, replacing P3′'s unquantified envelope censoring.
3. **DOCUMENTED-FAIL (envelope not separable)** — the E2 fail branch.

## Deliverables

FLITS branch `scint/p4-envelope-model` (off `563645c`):
`scintillation/scint_analysis/envelope_model.py` + unit tests; harness
`analysis/chime-scintillation/experiments/p4-envelope-model/p4_calibration.py`
(`freeze → e0 → e2 → e3 → verdict`); frozen config (hashed); E0/E2/E3 JSONs;
figures for visual vetting at every stage; RESULT.md; INVENTORY.yaml entry;
then Faber2026 pin bump. Journal every ≤ 10 min of active work.
