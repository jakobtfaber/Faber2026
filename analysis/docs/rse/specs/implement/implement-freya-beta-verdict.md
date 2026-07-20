# Implementation Summary: freya β verdict artifact + provisional-citable row candidate (dsa110-FLITS #106)

---
**Date:** 2026-07-03
**Author:** AI Assistant
**Status:** Complete (merged 2026-07-03, squash `3d31db7e`, owner-authorized; pin bumped in `0346068`)
**Plan Reference:** dsa110-FLITS issue #106 Agent Brief (posted 2026-07-03) + PRD ([prd-freya-beta-comodel-real-data-fit.md](../prd/prd-freya-beta-comodel-real-data-fit.md), story 13, deep module 3); blockers #100/#104/#105 all merged

---

## Overview

The DAG's closing node (8/8): a deterministic builder over the committed DAG
artifacts producing `freya_beta_verdict.json` + `freya_beta_verdict.md` — the
one provenance-bearing source that Step 4 and the eventual β-table row cite.

**Verdict: grade PASS, provisional-citable TRUE.**

- β = 3.6837 +0.0128/−0.0136 — un-railed **50σ / 25σ** from the [3, 4) edges;
  derived α = 4.3757 +0.0193/−0.0179; τ₁GHz = 0.11439 ms; lnZ = −24144.12 ± 0.55.
- Gates: PPC χ²/dof 1.18 / 1.03 (Level-2 PASS), Route A #111 validation PASS,
  x_ζ–β posterior correlation r = +0.011 (recomputed from the npz;
  Codex-recomputed +0.01085).
- A-vs-B (#105): **agree** on all four physics params.
- Exp-era comparison via the #100 comparator (B's derived-α triplet vs the
  deprecated free-α+exp-PBF artifact): overall **agree**, |Δα| = 0.020 ≤ 0.1 —
  **the manuscript's wording-only claim band holds on its validator burst.**
  Exp-era value framed throughout as the deprecated fit's *suggestion under
  test*, never citable truth.
- **Binding caveat carried verbatim in both artifacts**: tail-coverage
  preflight recomputed at the fitted medians — 2.07 e-folds / 87.4%, FAIL vs
  the 3.0 threshold; widening cannot rescue (81.9 ms raw captures); A-vs-B
  agreement cannot detect window-induced bias (same window both routes).
- Provisional-citable bar (CONTEXT.md): un-railed ✓, C1D1 confirmed ✓, grade
  PASS → β row candidate emitted with full provenance pointers.

## What changed (PR #116, branch `feat/106-freya-beta-verdict`)

- **`analysis/beta_poc/build_verdict.py`** (new): pure function over the
  committed artifacts (only the preflight touches data — one CHIME band prep);
  no RNG. Grading delegates to `_chi2_flag()`, an exact mirror of the kernel's
  `classify_fit_quality` χ² gate (PASS [0.3, 1.5]; MARGINAL (1.5, 10] and
  finite < 0.3; FAIL > 10 and non-finite, fail-closed on None/NaN/inf) — per
  Codex round-1 P1, which caught my invented thresholds (hard-fail at 3.0) and
  a NaN→MARGINAL→citable fall-through. Any A-vs-B verdict other than `agree`
  FAILs (consistent with #105's widened-is-a-breach semantics); railed β FAILs.
- **`analysis/beta_poc/test_build_verdict.py`** (new): un-railed arithmetic,
  railed edge case, kernel-contract grade matrix (4.6 → MARGINAL, 10.0 edge,
  NaN/inf/None → FAIL, widened → FAIL), **kernel parity test** importing the
  real `classify_fit_quality` and asserting `_chi2_flag` agreement over a
  12-point boundary grid, slow real-artifact roundtrip. Suite collection 522.
- **Committed artifacts**: `freya_beta_verdict.{json,md}` — byte-stable across
  rebuilds (sha `c2aa58f7…` pre/post the grading fix; 1.18/1.03 are PASS under
  both contracts).
- One pyproject `testpaths` entry.
- **Physics kernel untouched** (Codex-verified).

## Verification Results

- ✅ Tests 8/8 incl. kernel parity; ruff clean; collection 522; artifact JSON
  valid and byte-stable.
- ✅ Codex round-1 recomputation: all headline values match from the input
  artifacts (β/α/τ triplets, rail distances 50.35/24.76, |Δα| = 0.0197, corr
  +0.01085, 2.07 e-folds); markdown matches JSON rounding.
- ✅ Preflight provenance note (Codex): fitted-t0 convention gives 2.0735
  e-folds vs 2.0552 under the raw-init convention — both FAIL the 3.0
  threshold; no verdict sensitivity. (The MLE-refined t0 would give 0.64 —
  exactly why `tail_coverage.py` warns against it.)
- ✅ **Adversarial review** (Codex, gpt-5.5 high, read-only): round 1
  REQUEST_CHANGES — two P1s, one root cause (χ² grading diverged from the
  kernel contract; non-finite fall-through), fixed in `5d129ed8` with the
  parity test. Round 2 **APPROVE, zero findings** — verified the exact
  boundary edges against the kernel source, re-ran the parity grid via direct
  source import (4.6 → MARGINAL, non-finite → FAIL), confirmed commit scope
  and artifact byte-identity.

## Known Caveats

- The verdict's truncation caveat is the load-bearing epistemic statement: the
  β measurement is conditional on the truncated CHIME window. It rides with
  every downstream citation of the row candidate.
- Adjudication, pin bump, and manuscript prose/table edits are Step 6 / owner
  scope — deliberately out of this PR.

## Next Steps

1. ~~Merge PR #116~~ — **merged** 2026-07-03 (squash `3d31db7e`, owner-authorized); worktree/branch cleaned up, canonical clone synced.
2. ~~Pin bump~~ — done: `build:` commit `0346068` moves `pipeline/` from
   `6ce3e58` to `3d31db7e`; every DAG number in the manuscript is now
   reproducible from the pin.
3. Manuscript motion (β-table row, prose) — owner/Step 6, citing
   `freya_beta_verdict.json` as the provenance source.

## References

**Issue/PR:** https://github.com/jakobtfaber/dsa110-FLITS/issues/106 · https://github.com/jakobtfaber/dsa110-FLITS/pull/116
**Sibling docs:** [implement-route-a-crosscheck.md](../implement/implement-route-a-crosscheck.md) (#105) · [implement-freya-production-joint-fit.md](../implement/implement-freya-production-joint-fit.md) (#104) · [implement-posterior-comparator.md](../implement/implement-posterior-comparator.md) (#100)

---

**Implementation completed by AI Assistant on 2026-07-03**
