# Proposed design locks — Referee D2–D5 (scattering / scintillation / energetics)

**Status:** **ACCEPTED** — owner sign-off 2026-07-10 (all five questions: D2–D5 + D1 separate)  
**Date:** 2026-07-10  
**Scope:** presentation contracts the per-sightline attribution ledger inherits  
**Not in scope:** quoting any current fit numbers (trust-reset wave 1: scattering, sub-band EMG, scint ACF, energies remain **REVOKED** until V ladders clear). Accepting these locks does **not** make any fit citable.

**Authoritative asks:** historical referee D2–D5 (root report deleted 2026-07-19; see `docs/rse/ops/review-status.md`)  
**Tracking:** `docs/rse/ops/review-status.md` + wayfinder / BOARD  
**In-force drafts:** `CONTEXT.md` (geometry-adjudicated β, Wilhelm/EMG guardrail, A1 scint→scattering); verification-protocol + wayfinder (circulation megaplan frozen)  
**Methods drafts already on tree (referee impl):** `sections/budget.tex` §β-scattering / sub-band / gain-marg; `sections/methods.tex` §energies — this memo locks vocabulary and Results rules so those drafts can be kept, tightened, or revised on sign-off

---

## How to use this memo

**Owner accepted all five questions 2026-07-10.** Locks below are in force as
presentation contracts. They remain revisable if the owner re-opens them.
Accepting does **not** make any fit citable.

**Where each lock lives**

| Item | `tab:beta` / results tables | Methods (once) | Deferred until campaign C / V |
|------|----------------------------|----------------|-------------------------------|
| D2 | closure-regime column | β=4 / inner-scale degeneracy paragraph | geometry label from A2/A3; citable β only post-V+geometry |
| D3 | no turbulence column from sub-band slopes | EMG-bias / diagnostic argument | restore sub-band figure only post-V |
| D4 | n/a (Methods + Results-scint cross-ref) | gain-marg first introduction | gain-prior-width stability check on final V1 fits |
| D5 | `tab:burst-energies` caption + rest-frame interval note | non-comparability + eq:eiso intervals | optional fixed rest-frame variant only if owner elects under V3 |

---

## D2 — β=4 / inner-scale degeneracy → closure-regime column

### Referee ask
Do not report β=4 as a turbulence-spectrum measurement; bake a closure-regime column into the results table (Cordes et al. 2016; Cordes 2025).

### Options considered

1. **Prose-only caveat** — mention degeneracy in Methods; no table column.  
   *Tradeoff:* fails the referee’s explicit “bake into the table” ask; easy to miss in the ledger.

2. **Two-value column: `inertial` vs `endpoint-degenerate`** (proposed).  
   *Tradeoff:* minimum table contract; does not encode thin vs extended geometry (that is A3’s job). Avoids retired rail-class words.

3. **Three-value column merging geometry** (`inertial` / `endpoint-degenerate` / `extended`).  
   *Tradeoff:* conflates closure physics with geometry selection; blocks table fill until A2/A3 finish; over-builds relative to the referee ask.

### Proposed lock

**Table (`tab:beta`) — required column `closure_regime`:**

| Value | Meaning | What may be quoted (only after V + geometry adjudication) |
|-------|---------|-----------------------------------------------------------|
| `inertial` | Thin-screen inertial-range closure applies; diffractive scale treated as inside the inertial range; β resolved away from the β→4 endpoint | β (and derived α=2β/(β−2)) under the named geometry |
| `endpoint-degenerate` | Posterior concentrates at the square-law / inner-scale endpoint; α→4 regardless of underlying β | **No** β or α as a turbulence-spectrum measurement. Descriptive only: PBF consistent with the exponential limit (both bands), with geometry named or marked undecided |

**Forbidden:** quoting “β=4”, “square-law spectrum”, or “α=4 limit” as a turbulence index for any `endpoint-degenerate` row (aligns with geometry-adjudicated β: railing at β=4 is evidence against thin-screen closure completeness, not a square-law detection).

**Separate from this column:** geometry family (`thin` / `extended` / `undecided`) comes from A2/A3 and may be its own column or caption field — **not** folded into `closure_regime`.

**Methods (once):** keep the Cordes degeneracy paragraph in `sections/budget.tex` (~L166–178). **Amend vocabulary** on sign-off: replace draft labels “interior” / “square-law/inner-scale limited” with `inertial` / `endpoint-degenerate` so “interior” does not collide with retired rail-class QA language.

**Results:** every `tab:beta` row carries `closure_regime`; figure captions that show β posteriors at the endpoint use the same words.

### Dependencies
Geometry-adjudicated β (CONTEXT); A2/A3; V1 fit re-validation; F2 `tab:beta` rework; ADR-0006/0007. Campaign rail tallies stay out of the manuscript.

### Owner accept/reject question
**D2:** Accept `closure_regime ∈ {inertial, endpoint-degenerate}` as a required `tab:beta` column, with no β/α turbulence quote on `endpoint-degenerate` rows, and Methods vocabulary amended away from “interior”?

---

## D3 — Sub-band EMG validation is diagnostic, not turbulence constraint

### Referee ask
Make explicit that sub-band EMG τ slopes are a validation diagnostic (shape-mismatch bias need not cancel in a frequency-independent way); do not treat them as a turbulence constraint.

### Options considered

1. **Drop sub-band slopes from the paper** — avoid the EMG tension entirely.  
   *Tradeoff:* loses a useful consistency check the Methods already motivate.

2. **Label as diagnostic; never quote as β/α** (proposed).  
   *Tradeoff:* minimum that satisfies the referee; keeps the cross-check.

3. **Promote to co-equal constraint when bias-cancellation tests pass.**  
   *Tradeoff:* speculative; needs a frequency-dependent bias study not in scope; conflicts with “minimum contract.”

### Proposed lock

**Methods (once):** keep `sections/budget.tex` §Sub-band (~L180–208): EMG kernel stated; bias-cancellation caveat stated; slopes labeled validation diagnostic only.

**Results / figures:**
- Captions and prose: “sub-band slope diagnostic” / “consistency check on joint-fit frequency scaling.”
- **Never** enter sub-band-derived α or β into `tab:beta`, the turbulence discussion as a measurement, or the screen-attribution ledger as a spectral-index constraint.
- Joint-fit (geometry-adjudicated) β remains the only turbulence-index path.

**Deferred (campaign / V):** restore the sub-band validation figure only after fit re-validation; figure must state burst list, exclusions, EMG family, and “diagnostic only” (see TODO at `budget.tex` ~L210–213).

### Dependencies
V1; results-turbulence TODO (`results.tex` ~L181–195). Independent of A1 geometry odds.

### Owner accept/reject question
**D3:** Accept that sub-band EMG slopes appear only as a labeled validation diagnostic (Methods argument as drafted), never as a `tab:beta` / turbulence-constraint input?

---

## D4 — Scintillation double-use (gain marginalization vs observable)

### Referee ask
At first introduction of gain marginalization, state that scintillation products come from a separate analysis path; address whether gain prior width interacts with the τ posterior at low S/N.

### Options considered

1. **Silent double-use** — gain absorbs scint; Results later quote Δν_d with no cross-link.  
   *Tradeoff:* fails the referee ask; looks like circular inference.

2. **Methods contract + low-S/N prior-width guard** (proposed; largely already drafted).  
   *Tradeoff:* minimum; defers quantitative prior-width sweeps to V1 verification.

3. **Joint burst-shape+ACF likelihood now.**  
   *Tradeoff:* contradicts A1 (joint likelihood deferred unless modular products conflict on a high-S/N sightline); out of scope for this lock.

### Proposed lock

**Methods (once, at first gain-marg mention):** keep `sections/budget.tex` §Gain-marginalized likelihood (~L215–245):
1. Marginalization absorbs scintillation into per-channel gain → scattering fit does **not** measure scintillation.
2. Decorrelation-bandwidth / scint products come from a **separate ACF analysis path** on the same dynamic spectra (`sec:results-scintillation`).
3. Low-S/N guard: informative (finite-width) gain prior, not flat; before quoting any low-τ result, verify τ_{1 GHz} posterior stability against gain-prior width.

**Results-scintillation:** open by pointing back to that Methods sentence (products are modular ACF outputs with quality flags — A1), not by re-deriving scint from the gain vector.

**A1 consistency:** separate-path ACF products are exactly the “frozen posterior/limit products with quality flags” that later set **prior odds** on PBF family. Double-use is resolved by path separation + deferred coupling, not by claiming independence of science stories.

**Deferred:** quantitative gain-prior-width stability checks on final V1 fits (Methods already promises the check; do not invent numbers now).

### Dependencies
A1 (working draft); B-campaign scint products under V1; Results-scintillation section fill.

### Owner accept/reject question
**D4:** Accept the existing Methods three-part contract (separate ACF path; finite gain prior; τ stability vs prior width before low-τ quotes), with Results-scintillation required to cite it — and treat this as consistent with A1 modular prior-odds coupling?

---

## D5 — Energetics comparability

### Referee ask
Band-restricted two-band E_iso is not comparable to literature fixed rest-frame-band energies — either provide a fixed rest-frame-band variant **or** state prominently they cannot go on standard luminosity functions; write out per-band rest-frame intervals sampled by `eq:eiso`.

### Options considered

1. **Disclaimer + rest-frame intervals only** (proposed minimum).  
   *Tradeoff:* fully satisfies “either/or”; no extra energy product to re-validate.

2. **Always publish a fixed rest-frame-band companion table.**  
   *Tradeoff:* requires spectral extrapolation the Methods deliberately avoid; new V3 product and selection rules.

3. **Disclaimer now + promise a variant “where comparison is needed”** (current Methods draft wording).  
   *Tradeoff:* satisfies the referee but commits the paper to a product that may never ship; risk of a dangling promise.

### Proposed lock

**Methods (once):** keep the prominent non-comparability statement and the explicit per-burst rest-frame intervals in `sections/methods.tex` (~L41–55):

- CHIME 0.400–0.800 GHz → rest-frame \([0.400(1+z),\,0.800(1+z)]\) GHz  
- DSA 1.311–1.499 GHz → rest-frame \([1.311(1+z),\,1.499(1+z)]\) GHz  
- Single (1+z) in `eq:eiso` = bandwidth/time-dilation k-correction only; per-band γ enter only the in-band integrals.

**Amend on sign-off:** soften or remove “provide a fixed rest-frame-band variant alongside” unless the owner **elects** Option 2. Default lock = Option 1 (disclaimer is sufficient).

**Results / `tab:burst-energies`:**
- Caption states: band-restricted observed-frame energies; **not** for standard luminosity functions without extrapolation.
- Optional column or note: rest-frame interval per band per burst (or pointer to Methods formula).
- No energy row until V3 + redshift/amplitude/calibration/inclusion rules clear (trust reset).

**Deferred:** fixed rest-frame-band variant only if owner explicitly elects it under V3 (then add Methods sentence + table column).

### Dependencies
V3 energy re-validation; `results.tex` TODO ~L211–222; energies trust boundary in CONTEXT.md.

### Owner accept/reject question
**D5:** Accept disclaimer + written rest-frame intervals as the submission contract (Option 1), and drop the Methods promise of a fixed-band variant unless you elect to build one under V3?

---

## Consistency check (A1 · geometry-adjudicated β · Wilhelm)

| Contract | D2 | D3 | D4 | D5 |
|----------|----|----|----|-----|
| **A1** modular scint layer, prior odds, no hard geometry cut, joint likelihood deferred | OK — closure column ≠ geometry cut | OK — diagnostic only | **OK / required** — separate ACF path is the modular product source | n/a |
| **Geometry-adjudicated β** — no α for ex-railed; no rail-class prose; β=4 rail ≠ square-law detection | **Tension resolved by proposed vocab** — draft Methods “interior / square-law/inner-scale limited” collides with retired “interior” rail language and can be read as a square-law measurement; proposed `inertial` / `endpoint-degenerate` + separate geometry field fixes this | OK | OK | n/a |
| **Wilhelm / EMG guardrail** — residual morphology ≠ evidence against EMG family | OK | **OK** — D3 criticizes using EMG slopes as turbulence constraints, not the exponential family itself; Wilhelm remains “high-S/N residual within preferred exponential-tail model” | OK | n/a |
| **Trust reset** — no citable fits yet | All locks are presentation contracts only; no numbers claimed | same | same | same |

**Conflicts found:** one soft conflict only — D2 Methods draft vocabulary vs geometry-adjudicated β / retired rail “interior.” No conflict with A1 or Wilhelm under the proposed locks.

---

## D1 note — bundle or separate?

**Keep D1 separate.**  
Minimum ask (acknowledge fixed Kolmogorov α=4.4 in Obs-MW vs fitted β) is already DONE (`observations.tex`). Full screen-attribution policy (fixed-α Galactic comparison vs β-posterior propagation) lives in `discussion.tex` screen-attribution TODO and needs the C-campaign ledger. Bundling it with D2–D5 would block sign-off on table/Methods contracts that do not depend on that choice. Revisit D1 when writing §Discussion screen attribution.

---

## Implementation checklist (later — do not execute in this lock pass)

When scattering / scintillation / energetics sections are written post-V/C:

### D2
- [ ] `tab:beta` schema: add `closure_regime` column (`inertial` \| `endpoint-degenerate`)
- [ ] Optional separate geometry field from A3 (`thin` \| `extended` \| `undecided`)
- [x] Amend `sections/budget.tex` vocabulary (drop “interior” / “square-law/inner-scale limited” labels) — done 2026-07-10 on sign-off
- [ ] `results.tex` `sec:results-alpha` TODO (~L181–195): fill only post-V+geometry; enforce no β/α quote on `endpoint-degenerate`
- [ ] F2 in plan-circulation-readiness: `tab:beta` rework

### D3
- [ ] Keep Methods argument (`budget.tex` ~L180–208)
- [ ] Restore sub-band figure only post-V; caption = diagnostic only (`budget.tex` TODO ~L210–213)
- [ ] Results prose: never promote sub-band slopes into turbulence constraints or `tab:beta`

### D4
- [ ] Keep Methods three-part contract (`budget.tex` ~L215–245)
- [ ] Results-scintillation first paragraph: cite separate ACF path + Methods gain-marg
- [ ] On final V1 fits: record τ stability vs gain-prior width before any low-τ quote
- [ ] Ensure A1 prior-odds language in Discussion does not re-claim scint from the gain vector

### D5
- [x] Keep / tighten `methods.tex` ~L41–55 (intervals + non-comparability); drop “variant alongside” — done 2026-07-10 on sign-off
- [ ] `results.tex` `sec:burst-energies` TODO (~L211–222) + `tab:burst-energies` caption: not for standard LFs
- [ ] **TODO(energies-fixed-band-variant)** — optional under V3: if LF comparison is needed, elect fixed rest-frame-band companion \(E_{\rm iso}\) (band + gap extrapolation + table column + Methods sentence). Tracked in `methods.tex` / `results.tex` TODOs and plan V3.

### Trust / quoting
- [ ] No fit-, scint-, or energy-derived number enters Results until its V ladder clears
- [ ] Per-section sample rule: every subset states its burst list and exclusions

---

## Compressed proposed locks (sign-off card)

| ID | Proposed lock (one line) |
|----|--------------------------|
| **D2** | Required `tab:beta` column `closure_regime ∈ {inertial, endpoint-degenerate}`; never quote β/α as turbulence on `endpoint-degenerate`; geometry is a separate A3 field; amend Methods off “interior.” |
| **D3** | Sub-band EMG slopes = validation diagnostic only; never a turbulence / `tab:beta` constraint. |
| **D4** | At gain-marg: scint products from separate ACF path; finite gain prior; τ–prior-width stability before low-τ quotes; consistent with A1 modular prior odds. |
| **D5** | Prominent non-comparability + write out per-band rest-frame intervals; no fixed-band variant unless owner elects under V3. |

---

## Owner questions (resolved 2026-07-10)

1. **D2** — Accepted.
2. **D3** — Accepted.
3. **D4** — Accepted.
4. **D5** — Accepted (disclaimer+intervals only).
5. **D1** — Confirmed separate.
