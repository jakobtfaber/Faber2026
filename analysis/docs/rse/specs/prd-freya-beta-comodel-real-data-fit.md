# PRD — First real-data β co-model joint fit: freya (FRB 20230325A)

**Date:** 2026-07-02
**Status:** broken into issues 2026-07-02 — dsa110-FLITS #99–#106 (`needs-triage`), dependency order 99 → 101/102 → 103 → 104 → 105 → 106 (100 = comparator, unblocked)
**Scope:** Phase 1 / Step 3 of the manuscript 2D-modeling validation — one burst, single-component (C1D1)
**Codebase state:** Faber2026 `40e78c0`; `pipeline/` pinned at `6ce3e58`; upstream dsa110-FLITS main at `43f4c824` (#97 ADR-0006 addendum, #98 fixed-α/EMG fixes). **#98 does touch this task's Route B prep path:** it rewrote the MLE init refinement, which on the pinned checkout silently no-ops (its pre-co-model `FRBParams(alpha=…)` construction TypeErrors and is swallowed by a broad except). Nested-sampling posteriors are init-independent by design (absolute prior bounds), so the measurement is unaffected — but init quality/prints differ, and this is a concrete reason the eventual pin bump targets ≥ `43f4c824`.
**Related:** `docs/rse/specs/research-pipeline-2d-fit-scattering-index.md` (the scout this PRD stands on); pipeline ADRs 0004–0006; `CONTEXT.md`

## Problem Statement

The manuscript's scattering narrative now rests on the β co-model (ADR-0006): the
turbulence index β is the single sampled parameter, driving both the PBF shape and
the frequency scaling α = 2β/(β−2). But every real-data number the manuscript
carries for its designated clean single-component validator — freya's
α = 4.35 ± 0.04, τ₁GHz = 0.119 ms — comes from the deprecated free-α +
fixed-exponential-PBF fit, which CONTEXT.md declares physically inconsistent and
invalid as input for β conversion. The β co-model has only ever been exercised on
freya via a synthetic injection (the POC), because the real `.npy` data was absent
from that worktree. The data is now locally present. Until a real-data β fit
exists, `tab:beta` stays empty, the "clean validator" claim in the budget section
is unbacked, and Phase 1 ("is our 2D burst modeling correct?") cannot close.

## Solution

Run the first real-data β co-model joint CHIME+DSA fit for freya from the pinned
pipeline checkout, via a hybrid of the two scouted routes: the production
joint-fit driver as the primary instrument (Route B — evidence, posterior samples,
gate/PPC-compatible outputs, proven local-run precedent), and the completed POC
harness as an independent-likelihood cross-check (Route A — its real-data branch
is a deliberate stub whose own docstring prescribes reusing the driver's
band-preparation step). Agreement between two independently implemented
likelihoods on the same data, plus the existing validation gates, constitutes the
correctness evidence. Output: freya's provisional-citable β row candidate and a
validated comparison against the deprecated exp-era posterior.

## User Stories

1. As the manuscript author, I want freya's β measured from real data under the β co-model, so that the empty β table gains its first provisional-citable row.
2. As the manuscript author, I want the derived α from the β posterior compared against the exp-era α = 4.355, so that the manuscript's "well-constrained sightlines shift ≤ 0.1" claim is tested on its own validator burst.
3. As the manuscript author, I want the fit run from the pinned submodule, so that every number remains reproducible from the pin per the repo's non-negotiables.
4. As a pipeline maintainer, I want the POC harness's real-data stub completed, so that the β co-model's reference implementation is exercisable end-to-end without synthetic fallback.
5. As a pipeline maintainer, I want freya run-configs authored in the established local-runs pattern, so that any burst can follow the same local real-data path later.
6. As a skeptical referee, I want two independent likelihood implementations evaluated on identical inputs to agree, so that the measurement doesn't depend on one code path's private assumptions.
7. As a skeptical referee, I want the fit to pass the three-level validation contract (hard gates, χ²red/whiteness quality, physics plausibility), so that PASS means something beyond convergence.
8. As a skeptical referee, I want confirmation that β is un-railed against its prior bounds, so that the provisional-citable bar (un-railed, component count confirmed, PASS/MARGINAL) is demonstrably met.
9. As a pipeline maintainer, I want a tail-coverage preflight confirming the CHIME on-pulse window captures enough e-folds of the heavy power-law tail at freya's τ scale, so that a truncated tail cannot silently bias β (the POC's own comments flag this exact risk at τ ≈ 0.12 ms).
10. As an agent validator, I want the fit outputs in the format the existing gate/PPC tooling consumes, so that adversarial verification runs without adapter work.
11. As the manuscript author, I want the x_ζ–β posterior covariance inspected, so that the documented shared-ζ(ν) degeneracy caveat is checked rather than assumed benign.
12. As a pipeline maintainer, I want any code completing the stub to land upstream via PR before a pin bump, so that the pinned-submodule discipline holds.
13. As the manuscript author, I want a written verdict artifact (JSON + short markdown) capturing recovery, gates, and the exp-era comparison, so that Step 4 and the eventual β-table row cite one provenance-bearing source.

## Implementation Decisions

- **Hybrid route, B-primary.** The production joint driver runs the measurement
  (shared-ζ(ν) gain-marginal variant, C1D1, the same 8-vector as the POC). The POC
  harness is completed per its own prescription — building band models via the
  driver's preparation step — and run as cross-check.
- **Route A completion is more than the one stub.** The pinned POC predates the
  co-model API: it constructs params via a deprecated `alpha=` keyword that now
  TypeErrors, so even its synthetic path cannot re-run as-is (its recorded
  artifacts predate the API change), and its per-model PBF attribute writes are
  dead code. Completion = real-data branch + migrating param construction to the
  β-native API + deleting the dead writes.
- **Physics verified equivalent pre-implementation:** the pinned forward model
  dispatches the PBF on the sampled β alone (exp form within 0.02 of β = 4,
  power-law below); the driver's per-band PBF attributes are dead code. No physics
  changes required or permitted in this task.
- **β bounds** enter through the driver's legacy α-vocabulary mapping (only α ≥ 4
  reachable — acceptable: freya is the only single-component (C1D1) sightline whose
  deprecated exp-era fit (free-α + fixed-exponential-PBF, roster α ≈ 4.36 — invalid
  as β-conversion input per CONTEXT.md) *suggested* α > 4; whether that suggestion
  survives under the β co-model is the hypothesis this fit tests, not established
  physics. whitney's exp-era α ≈ 5.1 is the multi-component multiplicity exemplar,
  out of scope here. The extended-medium branch stays an open `@decision`
  untouched).
- **New shallow artifact:** freya CHIME+DSA run-configs following the existing
  local-runs precedent, pointing at the pinned checkout's data symlinks (not the
  canonical clone — the whitney precedent's paths are a provenance trap to correct
  for this use).
- **New deep module 1 — tail-coverage preflight:** pure function from (band
  geometry, τ₁GHz, β, window) → captured e-folds of the PBF tail, with a hard
  threshold; run before sampling.
- **New deep module 2 — likelihood equivalence check:** evaluate Route A's and
  Route B's log-likelihoods at identical θ vectors on identical prepared models;
  assert agreement within floating-point tolerance. Honest scope: both routes
  wrap the **same** gain-marginal kernel, so this check verifies the independent
  θ-packing / shared-β application / per-band parameter wiring — not the kernel
  itself. Kernel correctness is owned by Step 1 (analytic kernel audit) and
  Step 2 (injection-recovery); the check remains exact, cheap, and deterministic
  where a posterior comparison is stochastic and expensive.
- **New deep module 3 — posterior comparator:** pure function over two posterior
  artifacts (A's medians vs B's samples, plus B vs exp-era) → overlap/shift
  metrics and a verdict JSON.
- **Execution locus:** fits run from the pinned submodule checkout; code
  completing the stub is developed on an upstream branch in the canonical clone,
  PR'd, and only then considered for a pin bump. Fit artifacts follow the
  established pattern of landing via upstream PR (as the POC artifacts did).
- **Sampler settings** inherit the canonical joint-fit defaults (nested sampling,
  established nlive/dlogz); no tuning beyond what the exp-era exemplar used, to
  keep the comparison clean.

## Testing Decisions

- Good tests assert **external behavior**: recovered posteriors, gate verdicts,
  likelihood values at fixed inputs — never sampler internals.
- **Test scope (user-confirmed 2026-07-02): all three deep modules.**
  - Likelihood equivalence check — the decisive one; exact, deterministic, fast.
    Prior art: the β co-model regression tests asserting derived-α and PBF/scaling
    coupling.
  - Tail-coverage preflight — unit-tested against analytic cases (known τ, β,
    window → known e-folds; threshold behavior at the boundary).
  - Posterior comparator — unit-tested with synthetic posterior files (agreeing,
    shifted, widened cases).
  - Run-config smoke — band preparation succeeds on the real freya files and
    yields expected shapes/orientation (slow-marked, per repo convention).
- End-to-end fit quality is **gated, not unit-tested**: the three-level
  validation contract, PPC, and the adversarial fit-verify workflow are the
  acceptance instruments, per the repo's "fit validation is mandatory" contract.

## Out of Scope

- The extended-medium (β > 4, α < 4) branch — open `@decision`, untouched.
- Any other burst; any multi-component (C>1) path; the mixed-model wiring gaps
  (upstream #98 territory, already fixed there).
- Pin bump and manuscript prose/table edits (`tab:beta` row, budget-section
  claim) — Step 6, gated on this PRD's outputs plus Steps 4–5.
- Physics-kernel changes of any kind; sub-band Δα investigation (Step 5).
- HPCC re-runs; everything here is local.

## Further Notes

- The POC's synthetic truth deliberately used τ = 0.05 ms because freya's real
  τ ≈ 0.119 ms under a heavy power-law tail needs a much longer window — the
  tail-coverage preflight exists precisely because the real fit walks into the
  regime the POC sidestepped.
- Runtime expectation: the exp-era exemplar burned ~10⁶ likelihood calls; plan
  for hours, run in background, monitor convergence.
- If the two routes disagree beyond tolerance, that disagreement *is* the Phase 1
  finding — stop and diagnose before any manuscript motion.
