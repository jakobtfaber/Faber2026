# Implementation Plan: A-priori cluster-crossing probability for the codetected sample (Kulkarni S2)

---
**Date:** 2026-07-17
**Author:** AI Assistant
**Status:** Draft — predeclared method record, awaiting owner sanction (CONTEXT.md §V gate)
**Related Documents:**
- [Triage: Kulkarni-persona feedback (2026-07-17)](triage-kulkarni-feedback-2026-07-17.md) — S2 = referee §6 ("expected crossings ~0.1"); *needs a predeclared method before the number is quotable*
- [Plan: S1 mass bound](plan-cluster-xray-sz-mass-bound-2026-07-17.md) — predeclared-record precedent; S1's registry-vs-prose lesson applies here too
- [Plan: Thread 1 RM re-partition](plan-rm-cluster-bfield-repartition-2026-07-17.md) — sibling lane chartered the same day; S2's output sharpens the same a-posteriori framing
- [Handoff 2026-07-17 12:58](handoff-2026-07-17-12-58-s1-landed-owner-decisions-closed.md) — action item 5
- Project memory `verdi-draft-is-redshift-standard` — the z-set authority S2 must respect

---

## Overview

`sections/results.tex` (`sec:dominant-systems`) now states that the FRB
20230307A cluster crossing is "a single a-posteriori-identified alignment in a
depth-varying census, not an FRB-sightline population property." The Kulkarni
referee (§6) suggests quantifying that framing: given the twelve sightlines'
path lengths, what is the **a-priori expected number of crossings** within
$R_{500}$ of a cluster at least as massive as the one observed? The referee's
rough estimate is ~0.1; a defensible in-house number (with its sensitivity
spread) turns the qualitative "a-posteriori" sentence into a quantitative one.

The calculation is small and fully self-contained: a halo mass function
$n(>M,z)$ integrated against the proper cross-section $\pi R_{500}^2$ along
each sightline's comoving path,
$$N_{\rm exp} = \sum_i \int_0^{z_i} n_{\rm com}(>M,z)\,\pi R_{500}^2(M,z)\,
(1+z)^2\,\frac{c\,dz}{H(z)},$$
(the $(1+z)^2$ converts the proper cross-section to comoving to match the
comoving number density). It consumes no burst data, no fit product, and no
revoked-lane quantity — only the sample's host redshifts and published
cosmology/mass-function ingredients. The governance risk is the usual one: a
new quantitative manuscript input, so the method (mass thresholds, z-set,
mass-function choice, $R_{500}$ convention, quotability rule) is frozen here
before the integral is evaluated.

**Rough prior expectation (stated for calibration, not a result):**
$n(>1.5\times10^{14}) \sim$ few$\times10^{-6}$ Mpc$^{-3}$, $\sigma\sim2$–3
comoving Mpc$^2$, summed paths $\sim10^4$ Mpc → $N_{\rm exp}\sim0.1$, i.e. the
referee's order of magnitude. If the computed value lands far outside
[0.01, 1], that triggers the sanity-audit branch below, not a quiet quote.

**Goal:** A predeclared, owner-sanctionable $N_{\rm exp}$ (with sensitivity
spread) and a frozen rule for the single sentence it may add to
`sec:dominant-systems`.

## Current State Analysis

- `sections/results.tex:116-129` (origin/main `56cf4c4e`) — the a-posteriori
  framing sentence S2 would quantify; no crossing-probability number exists
  anywhere in the manuscript.
- `sections/appendix.tex:206-214` (origin/main) — the nine z-constrained
  sightlines currently in the books: 20220207C 0.043; 20220310F 0.479;
  20220506D 0.300; 20221113A 0.251; 20221203A 0.510 (note-r provisional);
  20230307A 0.271; 20230913A 0.302; 20240203A 0.074; 20240229A 0.287.
- **Verdi z-standard (project memory + journal 12:38):** the owner adopted the
  Verdi et al. DSA full-sample table as the sole z authority — 20230814B
  (johndoeII) $z=0.5535$ enters, 20221203A (wilhelm) drops. Net: still nine
  z-constrained sightlines, but the highest-z path moves 0.510 → 0.5535. The
  TARGETS/appendix propagation lane is **not yet chartered**; S2 must not block
  on it and must not contradict it.
- `pipeline/galaxies/foreground/data/intervening_census_registry.csv:23` — the
  observed system's pinned parameters: $M_{500}=1.48\times10^{14}\,M_\odot$,
  $R_{500}=0.729$ Mpc, $z_{\rm cl}=0.200$. The primary mass threshold and the
  $R_{500}$-convention anchor both come from this row (never from the prose
  "$\log M = 14.1$" — the S1 lesson).
- `scripts/dm_budget_uncertainty.py` cosmology block (origin/main) — the budget
  cosmology: FlatΛCDM $H_0=70$, $\Omega_m=0.3$. S2 reuses it unchanged.
- `pipeline/pyproject.toml` — **no halo-mass-function package** (astropy only;
  no colossus/hmf). The mass function must be implemented directly (scipy +
  numpy, already available root-side) — root-side script + tests, following the
  `scripts/dm_budget_uncertainty.py` + `tests/test_dm_budget_uncertainty.py`
  pattern; the FLITS submodule tree (live joint-tf lane) is not touched.

## Desired End State

- `scripts/cluster_crossing_probability.py` — self-contained, deterministic
  (quadrature, no MC), emitting `scripts/cluster_crossing_probability.csv`
  with per-sightline and total $N_{\rm exp}$ for every predeclared variant.
- `tests/test_cluster_crossing_probability.py` — anchors below all green.
- A record figure `docs/rse/specs/s2-figures/crossing_probability.pdf`
  ($N_{\rm exp}(>M)$ vs. $M$ with the two thresholds marked and per-sightline
  stacking) — ships with the PR per the visibility preference.
- A one-sentence gated prose candidate, entered only per the frozen quotability
  rule + owner sanction.

## What We're NOT Doing

- [ ] Not computing cluster *association* probabilities for specific observed
      systems (that is the census's $P_{\rm cc}$ machinery, V4-cleared,
      untouched).
- [ ] Not modeling survey selection or optical-catalog completeness — this is
      the a-priori geometric expectation, deliberately survey-independent; the
      prose sentence must say "expected number of chance crossings," not
      "detection rate."
- [ ] Not introducing a package dependency (colossus/hmf) into the pipeline —
      the Tinker et al. 2008 fit is ~40 lines of scipy against an
      Eisenstein–Hu transfer function, all root-side.
- [ ] Not waiting on (or preempting) the Verdi z-propagation lane — S2
      predeclares both z-vectors and quotes the Verdi-standard one; when the
      propagation lane lands TARGETS, the pin test flips to reading TARGETS
      (Phase 3 note).
- [ ] Not touching S3 (f_IGM decircularization) — explicitly deferred to the
      V5 follow-up per the triage doc.
- [ ] Not quoting any number in prose before owner sanction + the stability
      rule passing.

**Rationale:** S2's value is one honest sentence; anything larger re-derives
census machinery or crosses into survey-modeling scope the referee didn't ask
for.

## Implementation Approach

**Technical Strategy:** Deterministic quadrature over published fitting
functions; every convention pinned; sensitivity axes predeclared and reported
as a spread, not cherry-picked.

**Pinned inputs (frozen now):**

1. **Mass thresholds:** primary $M_{500c} \ge 1.48\times10^{14}\,M_\odot$ (the
   registry mass of the observed system — "a cluster at least this massive");
   secondary $M_{500c} \ge 1.0\times10^{14}$ (the referee's round number).
   Both reported; the prose sentence uses the primary.
2. **Cross-section:** $b \le R_{500}(M,z)$, matching the budget's $b\le R_{500}$
   aperture (registry $b/R_{500}=0.83<1$). $R_{500}$ from
   $M_{500}=\tfrac{4}{3}\pi R_{500}^3\,500\rho_c(z)$.
3. **Cosmology:** FlatΛCDM $H_0=70$, $\Omega_m=0.3$ (budget values), plus the
   S2-new power-spectrum pins $\sigma_8=0.81$, $n_s=0.965$,
   $\Omega_b=0.048$ (Planck-2018-consistent, fixed here; Eisenstein & Hu 1998,
   ApJ 496, 605 — zero-baryon-wiggle transfer function).
4. **Mass function:** primary Tinker et al. 2008 (ApJ 688, 709) at
   $\Delta_m(z) = 500/\Omega_m(z)$ (their Δ-interpolation covers it);
   sensitivity alternative Despali et al. 2016 (MNRAS 456, 2486) (or, if its
   coefficients prove awkward at this Δ, Sheth–Tormen as the fallback
   alternative — whichever is used is recorded; the *pair* primary+one-
   alternative is the frozen requirement).
5. **z-vectors:**
   - *Primary (Verdi standard):* {0.043, 0.479, 0.300, 0.251, 0.271, 0.302,
     0.074, 0.287, 0.5535} — the appendix nine with 20221203A (0.510) removed
     and 20230814B (0.5535) added.
   - *Control (current manuscript):* {0.043, 0.479, 0.300, 0.251, 0.510,
     0.271, 0.302, 0.074, 0.287}.
   - The three no-z sightlines (20230325A, 20240122A, and whichever of the
     twelve lacks z under each variant) contribute zero path — stated in the
     sentence as "the nine redshift-constrained sightlines." A twelve-sightline
     variant with no-z bursts assigned the z-constrained median is computed as
     a tertiary sensitivity row only.

**Frozen quotability rule (fixed before evaluation):** the sentence enters
`sec:dominant-systems` (gated on owner sanction) **iff** the primary
configuration (Verdi z-set, Tinker08, thresholds as pinned) and every
sensitivity variant (control z-set; alternative mass function) agree on
$N_{\rm exp}$(primary threshold) within **30% relative**. Otherwise the spread
is reported in this record and the owner adjudicates whether/how to quote a
range. **Sanity-audit branch:** if any configuration yields
$N_{\rm exp} \notin [0.01, 1]$, halt and audit the integrand against the
Phase-1 anchors before any classification — do not quote.

**Proposed sentence shape (final wording at Phase 3):** "A-priori, the expected
number of chance crossings within $R_{500}$ of a $\ge1.5\times10^{14}\,M_\odot$
cluster across the nine redshift-constrained sightlines is
$N_{\rm exp}\approx X$ (Tinker et al. 2008 mass function; varying the mass
function and redshift bookkeeping shifts this by $\lesssim$30%), consistent
with the single observed alignment being a coverage-weighted accident."

## Implementation Phases

### Phase 0: Conventions + pins (pre-sanction; no evaluation)

**Objective:** Machine-verify the pinned inputs and the $R_{500}$ convention
against the registry before any integral runs.

**Tasks:**
- [ ] **Write the failing tests** in `tests/test_cluster_crossing_probability.py`:

  ```python
  import math
  from scripts.cluster_crossing_probability import (
      PINNED, r500_proper_mpc, Z_PRIMARY, Z_CONTROL,
  )

  def test_r500_convention_reproduces_registry():
      # registry row 23: M500=1.48e14, z=0.200 -> R500 = 0.729 Mpc.
      # This anchors the 500*rho_c(z) convention to the census's own books.
      r = r500_proper_mpc(m500_msun=1.48e14, z=0.200)
      assert abs(r - 0.729) / 0.729 < 0.03

  def test_z_vectors_pinned():
      assert len(Z_PRIMARY) == len(Z_CONTROL) == 9
      assert max(Z_PRIMARY) == 0.5535 and 0.510 not in Z_PRIMARY
      assert max(Z_CONTROL) == 0.510 and 0.5535 not in Z_CONTROL
      assert PINNED["m500_primary"] == 1.48e14
      assert PINNED["m500_secondary"] == 1.0e14

  def test_cosmology_matches_budget():
      assert PINNED["H0"] == 70.0 and PINNED["Om0"] == 0.3
  ```
- [ ] **Run, watch fail** (`uv run --project pipeline --frozen python -m pytest tests/test_cluster_crossing_probability.py -v`).
- [ ] **Implement** the `PINNED` dict (+ provenance comments), the z-vectors,
      and `r500_proper_mpc` (astropy `FlatLambdaCDM(70, 0.3).critical_density(z)`).
- [ ] **Run, watch pass. Commit:**
      `git commit -m "feat(s2): pinned conventions for cluster-crossing probability" -- scripts/cluster_crossing_probability.py tests/test_cluster_crossing_probability.py`

**Dependencies:** none.

**Verification:**
- [ ] The $R_{500}$ round-trip against the registry passes — the convention is
      anchored to the census, not to a textbook choice.

### Phase 1: Mass function + anchors (post-sanction)

**Objective:** A validated $n(>M,z)$.

**Tasks:**
- [ ] **Write the failing anchor tests:**

  ```python
  def test_sigma8_normalization_roundtrip():
      from scripts.cluster_crossing_probability import sigma_r
      assert abs(sigma_r(8.0 / 0.7, z=0.0) - 0.81) < 0.005  # sigma(8/h Mpc) = sigma8

  def test_hmf_order_of_magnitude_z02():
      from scripts.cluster_crossing_probability import n_gt_m
      n = n_gt_m(1.0e14, z=0.2)          # M500c, comoving Mpc^-3
      assert 1e-6 < n < 3e-5             # published-cluster-abundance band

  def test_hmf_monotonic_and_decreasing_with_z():
      from scripts.cluster_crossing_probability import n_gt_m
      assert n_gt_m(1.0e14, 0.2) > n_gt_m(2.0e14, 0.2)
      assert n_gt_m(1.48e14, 0.0) > n_gt_m(1.48e14, 0.55)
  ```
- [ ] **Run, watch fail. Implement:** the Eisenstein & Hu 1998 (ApJ 496, 605)
      zero-wiggle transfer function → $\sigma(R,z)$ (top-hat, scipy
      quadrature, growth factor by the standard integral) → the Tinker et al.
      2008 $f(\sigma)$ with the Δ-interpolated coefficients at
      $\Delta_m(z)=500/\Omega_m(z)$ → $n(>M,z)$ by integrating $dn/dM$; plus
      the alternative mass function behind the same interface
      (`n_gt_m(..., fit="tinker08"|"alt")`).
- [ ] **Run, watch pass. Commit.**

**Dependencies:** Phase 0; owner sanction (first evaluation of physics
ingredients).

**Verification:**
- [ ] All three anchors green; the band test documents the external comparison
      value and its source in a comment.

### Phase 2: The crossing integral (post-sanction)

**Objective:** $N_{\rm exp}$ per sightline and total, all variants.

**Tasks:**
- [ ] **Write the failing tests:**

  ```python
  def test_expected_crossings_scale_linearly_with_path():
      from scripts.cluster_crossing_probability import n_cross_sightline
      # doubling a small z approximately doubles the expectation
      lo = n_cross_sightline(0.05, m_thresh=1.48e14)
      hi = n_cross_sightline(0.10, m_thresh=1.48e14)
      assert 1.7 < hi / lo < 2.3

  def test_total_matches_sum_of_sightlines():
      from scripts.cluster_crossing_probability import n_cross_total, Z_PRIMARY
      total, per = n_cross_total(Z_PRIMARY, m_thresh=1.48e14)
      assert abs(total - sum(per)) < 1e-12
  ```
- [ ] **Run, watch fail. Implement** `n_cross_sightline` (quadrature of the
      Overview integral; both the fixed-threshold-mass cross-section variant
      and the mass-integrated $\int dM\,(dn/dM)\,\pi R_{500}^2(M)$ variant —
      the mass-integrated one is the reported primary, since "at least this
      massive" clusters have mass-dependent $R_{500}$; both emitted) and
      `n_cross_total`; emit the CSV (per-sightline × variant matrix) and the
      record figure.
- [ ] **Run, watch pass.**
- [ ] **Evaluate the frozen quotability rule** (30% agreement; sanity band);
      print the verdict in `main()` and write it into the CSV header comment.
- [ ] **Commit.**

**Dependencies:** Phase 1.

**Verification:**
- [ ] CSV + figure regenerate deterministically; rule verdict recorded.

### Phase 3: Gated prose (post-sanction, quotability rule passed)

**Objective:** The single sentence, or the recorded spread.

**Tasks:**
- [ ] **Quotable branch:** add the sentence (shape above, numbers from the CSV)
      to `sections/results.tex` (`sec:dominant-systems`, adjoining the
      a-posteriori sentence at :116-129); add the Tinker et al. 2008 (and
      alternative-fit) citations to `bib/refs.bib`; run
      `python3 scripts/consistency_audit.py` and `latexmk -pdf`; focused
      `ms/…` branch + PR per precedent, owner sanction recorded first.
- [ ] **Spread branch:** record the variant table in this plan's Review
      History + the triage doc S2 row; owner adjudicates.
- [ ] **TARGETS note:** when the Verdi z-propagation lane lands, flip
      `test_z_vectors_pinned` to read the z-vector from the pipeline TARGETS
      source of truth instead of the literal list (one-line change, called out
      here so the pin does not silently rot).

**Dependencies:** Phases 1–2; owner sanction.

**Verification:**
- [ ] Quotable branch: audit + latexmk clean; diff = one sentence + bib
      entries.
- [ ] Triage doc S2 row updated either way.

## Success Criteria

### Automated Verification
- [ ] `uv run --project pipeline --frozen python -m pytest tests/test_cluster_crossing_probability.py -v` all green.
- [ ] `python3 scripts/cluster_crossing_probability.py` regenerates the CSV
      byte-identically (deterministic quadrature).
- [ ] $R_{500}$ registry round-trip (<3%) and $\sigma_8$ round-trip (<0.005)
      pass.
- [ ] Quotable branch only: `python3 scripts/consistency_audit.py` clean;
      `latexmk -pdf` clean.

### Manual Verification
- [ ] The mass-function implementation spot-checked against a published
      abundance value (source cited in the band test).
- [ ] The quotability rule applied as written (diff plan vs. merged record).
- [ ] Owner sanction recorded before any prose lands.

### Reproducibility & Correctness
- [ ] All pins carry provenance comments; no prose-derived threshold.
- [ ] The sentence, if quoted, states the z-set ("nine redshift-constrained
      sightlines") and the mass-function dependence explicitly.

## Testing Strategy

**Unit:** convention round-trips, σ8 normalization, HMF band + monotonicity,
path-linearity, total=Σ. **Integration:** full script → CSV + figure.
**Manual:** published-abundance spot-check; sentence faithfulness.

## Risk Assessment

1. **Risk:** Hand-rolled mass-function error (the classic Δ-convention slip:
   $500c$ vs $500m$ vs $200m$).
   - **Likelihood:** Medium. **Impact:** High (wrong quoted number).
   - **Mitigation:** The $\Delta_m(z)=500/\Omega_m(z)$ mapping is explicit in
     code; the registry $R_{500}$ round-trip anchors the $500c$ convention; the
     abundance band test catches order-of-magnitude slips; the two-fit spread
     bounds fit-choice error.
2. **Risk:** The Verdi propagation lands mid-lane and changes the z-vector.
   - **Likelihood:** Medium. **Impact:** Low (both vectors predeclared; the
     highest-z swap moves the total by only the 0.510→0.5535 path difference).
   - **Mitigation:** Phase 3 TARGETS note; the control row quantifies the
     shift.
3. **Risk:** Scope creep toward survey-completeness modeling.
   - **Likelihood:** Low. **Impact:** Medium.
   - **Mitigation:** NOT-doing list; the sentence's "chance crossings" wording.

## Edge Cases and Error Handling

1. **Case:** the two mass-function fits disagree >30% → the frozen spread
   branch (owner adjudication), never a silent pick.
2. **Case:** $N_{\rm exp}$ outside [0.01, 1] in any variant → sanity-audit
   halt (predeclared above).
3. **Error:** growth-factor/quadrature non-convergence → the script raises;
   no partial CSV.

## Documentation Updates

- [ ] Triage doc S2 row on completion.
- [ ] This plan's Review History at each gate.

## Timeline Estimate

Phase 0 small; Phase 1 moderate (the mass function is the long pole); Phase 2
small; Phase 3 small, human-gated.

## Open Questions

*(None. The z-set question is resolved by predeclaring both vectors with the
Verdi one primary; the mass-function-choice question is resolved by the
primary+alternative spread rule.)*

---

## References

- [Triage: Kulkarni feedback](triage-kulkarni-feedback-2026-07-17.md) · [S1 plan](plan-cluster-xray-sz-mass-bound-2026-07-17.md) · [Thread 1 plan](plan-rm-cluster-bfield-repartition-2026-07-17.md) · [Handoff 12:58](handoff-2026-07-17-12-58-s1-landed-owner-decisions-closed.md)
- Files analyzed: `sections/results.tex:101-157`, `sections/appendix.tex:184-227` (both origin/main); `pipeline/galaxies/foreground/data/intervening_census_registry.csv:23`; `scripts/dm_budget_uncertainty.py` (cosmology block); `pipeline/pyproject.toml`
- External: Tinker et al. 2008 (ApJ 688, 709 — mass function + Δ interpolation); Despali et al. 2016 (MNRAS 456, 2486) / Sheth–Tormen (alternative fit); Eisenstein & Hu 1998 (ApJ 496, 605 — transfer function); the referee note's ~0.1 estimate (triage S2 row)

---

## Review History

### Version 1.0 — 2026-07-17
- Initial predeclared method record for Kulkarni S2.
- Pinned thresholds to the registry mass (1.48e14, never the prose-rounded
  14.1), the $R_{500}$ convention to a registry round-trip test, and both
  z-vectors (Verdi-primary per the owner's 2026-07-17 adoption; manuscript
  control) before any evaluation.
- Froze the 30%-stability quotability rule, the [0.01, 1] sanity band, and the
  sentence shape.
- **Status: awaiting owner sanction** for Phases 1–3 (Phase 0 is pin
  verification only).
