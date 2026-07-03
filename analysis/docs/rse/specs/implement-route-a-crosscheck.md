# Implementation Summary: Route A cross-check + A-vs-B verdict (dsa110-FLITS #105)

---
**Date:** 2026-07-03
**Author:** AI Assistant
**Status:** Complete pending merge (PR #115 open, Codex round-2 APPROVE; merge owner-gated)
**Plan Reference:** dsa110-FLITS issue #105 Agent Brief (posted 2026-07-03) + PRD ([prd-freya-beta-comodel-real-data-fit.md](prd-freya-beta-comodel-real-data-fit.md)); blockers #100/#102/#104 all merged

---

## Overview

The independence check on the #104 measurement: the completed Route A POC
harness (`run_beta_poc.py --real`, `BetaCoupledLogL`) fit on the identical real
freya prepared inputs, adjudicated against Route B's posterior samples with the
#100 comparator. #103 proved the wirings agree at fixed θ; #105 shows two
independent sampler paths over independent implementations land on the same
posterior.

**Result: overall verdict `agree` on all four shared physics parameters.**

| param | Route A | Route B | shift | width ratio | overlap |
|---|---|---|---|---|---|
| β | 3.68338 | 3.68373 | 0.02σ | 0.99 | 0.98 |
| τ₁GHz [ms] | 0.114423 | 0.114389 | 0.02σ | 0.99 | 0.99 |
| ζ₁GHz | 0.0854958 | 0.0855491 | 0.07σ | 1.00 | 0.97 |
| x_ζ | −0.749998 | −0.751613 | 0.06σ | 1.03 | 1.00 |

Route A fit: β=3.683 → derived α=4.376, lnZ=−24127.2, dlogz-converged at
0.003 (ncall 189,608 < the 400k cap — a genuine convergence, not a cap stop),
seed-pinned, ~6 min single-process. #111 three-level validation PASS, no
marginals. Stop condition NOT triggered; #106 unblocked.

## What changed (PR #115, branch `feat/105-route-a-crosscheck`)

- **`analysis/beta_poc/compare_routes.py`** (new): thin deterministic driver
  over the #100 pure function. Physics params only
  (`beta, tau_1ghz, zeta_1ghz, x_zeta`) per the comparator's cross-fit
  guidance; nonzero exit on any overall verdict other than `agree` — per Codex
  round-1 P1, `widened` counts as a tolerance breach (`STOP_VERDICTS =
  (widened, shifted, incompatible)`, fixed in `8979fa70`).
- **`analysis/beta_poc/test_compare_routes.py`** (new): fixtures matching both
  real producer layouts; pins physics-param selection (nuisance t0 shift in B
  cannot move the verdict), incompatible-shift stop (7.07σ arithmetic
  Codex-verified), widened stop, bookkeeping, and a slow real-artifact
  roundtrip. Suite collection 520.
- **Committed artifacts** (`analysis/beta_poc/freya/`):
  `freya_beta_poc_fit_real.json`, `freya_route_a_vs_b.json` (comparator verdict
  with provenance/thresholds), `_real` diagnostic figures (force-added) +
  manifest/review updates — CHIME red_χ²=1.18 and DSA 1.03 on-panel, matching
  Route B's PPC values from an independent code path; honest notes on the
  ~−3σ CHIME peak-residual excursion and Q-Q tail scatter.
- One pyproject `testpaths` entry (per-file precedent).
- **Physics kernel untouched** (`burstfit.py`, `burstfit_joint.py` — Codex
  `git diff --quiet` verified).

## Verification Results

- ✅ Route A fit converged (not capped); validation PASS.
- ✅ Comparator: all `agree`; committed verdict JSON recomputes exactly from
  the artifacts (Codex: `stored_matches_computed=True`; byte-identical SHA
  across the round-1 fix commit).
- ✅ Tests 5/5 (+ slow roundtrip); ruff clean; CI green.
- ✅ **Adversarial review** (Codex, gpt-5.5 high, read-only): round 1
  REQUEST_CHANGES — one P1 (`widened` passed the stop gate); fixed in-lane
  with a pinning test. Round 2 **APPROVE, zero findings** — probe-confirmed
  the widened test exercises `widened` (shift 0, ratio 1/3), re-ran the suite
  independently.

## Known Caveats

- Expected asymmetries absorbed by the tolerance: A nlive 150 vs B 600; A
  seed-pinned, B not; prior t0 centers differ (raw-init vs driver init) —
  posteriors nonetheless agree to ≤0.07σ.
- The A-vs-B agreement cannot detect window-induced bias (both routes see the
  same truncated window); the #101 truncation caveat (2.07 e-folds / 87.4% at
  the fitted candidate) still binds on #106.

## Next Steps

1. **Merge PR #115** — owner-gated, not yet authorized.
2. **#106** verdict artifact — comparator A-vs-B `agree` + Route B vs the
   exp-era α=4.355 suggestion, carrying the truncation caveat verbatim.
3. **Pin bump** in Faber2026 (deliberate `build:` commit, target ≥ #115's
   squash SHA) once the DAG's code has merged; manuscript β numbers move only
   after #106.

## References

**Issue/PR:** https://github.com/jakobtfaber/dsa110-FLITS/issues/105 · https://github.com/jakobtfaber/dsa110-FLITS/pull/115
**Sibling docs:** [implement-freya-production-joint-fit.md](implement-freya-production-joint-fit.md) (#104) · [implement-likelihood-equivalence.md](implement-likelihood-equivalence.md) (#103) · [implement-posterior-comparator.md](implement-posterior-comparator.md) (#100)

---

**Implementation completed by AI Assistant on 2026-07-03**
