# Implementation Summary: Route A/B likelihood equivalence check (dsa110-FLITS #103)

---
**Date:** 2026-07-03
**Author:** AI Assistant
**Status:** Complete (merged 2026-07-03, squash `41bfe977`, owner-authorized)
**Plan Reference:** dsa110-FLITS issue #103 Agent Brief (posted 2026-07-03) + the PRD's Implementation/Testing Decisions ([prd-freya-beta-comodel-real-data-fit.md](../notes/prd-freya-beta-comodel-real-data-fit.md), deep module 2)

---

## Overview

The decisive, cheap, deterministic gate before the expensive #104 fit: Route A (`BetaCoupledLogL`, the POC harness) and Route B (`_JointLogLikelihoodGainSharedZeta`, the production shared-ζ(ν) driver path) evaluated at identical 8-vector θ on identical prepared band models, agreement asserted within rel ≤ 1e-12.

**Result: PASS on freya's real prepared CHIME+DSA models — max_rel_diff = 0.0, exact bitwise agreement across all 260 θ points.**

**Final Status:** ✅ Complete — PR https://github.com/jakobtfaber/dsa110-FLITS/pull/113 (`Closes #103`), branch `feat/103-likelihood-equivalence` off `d0d3592a`; Codex round-1 MAJOR fixed in-lane, round-2 **APPROVE, zero findings**; **merged** 2026-07-03 (squash `41bfe977`, owner-authorized). Worktree/branch cleaned up; upstream main now `41bfe977`.

## What changed

**`analysis/scattering-refit-2026-06/likelihood_equivalence.py`** (new, placement per the #100/#101 precedent):

- `evaluate(m_C, m_D, thetas)` — totals through each route's own `__call__` (the θ-unpacking IS the wiring under test) plus per-band values via each route's band function (`run_beta_poc._band_ll` / `_JointLogLikelihoodGainSharedZeta._band_ll`) as the diagnostic breakdown.
- `adjudicate(records, rtol)` — hard verdict; **recomputes every total and per-band diff from the stored `route_A`/`route_B` values** (records' `rel_diff` is informational-only); any NaN fails closed; failures carry the full per-band, per-θ breakdown.
- `rel_diff(a, b)` = |a−b| / max(|a|,|b|, 1) — symmetric, denominator floored at 1 so near-zero values compare absolutely.
- `theta_grid(t0_C, t0_D)` — (260, 8): all 2⁸ prior-box corners + center through the POC's own `_ptform_factory`, the exp-era-suggested point (τ=0.119 ms, β=3.70 — deprecated-fit *suggestion*, not truth), and β ∈ {3.99, 4.0} where both routes must dispatch the `BETA_EXP_EPS` exponential-PBF branch identically (ADR-0006; branch point 4.0 − 0.02).
- CLI: real freya bands via the POC's `_prepare_real_bands()` (the joint driver's own `prepare()`, #99 configs, raw data-driven t0 centers — never the post-#98 MLE refine); writes `local_runs/freya_likelihood_equivalence.json`; nonzero exit on disagreement.

**Honest scope (per the PRD, recorded in the module docstring and the artifact's `scope_note`):** both routes wrap the same `log_likelihood_gain_marginal` kernel, so the check verifies independent θ-packing / shared-β application / per-band wiring — not the kernel itself (Step 1 analytic audit + Step 2 injection-recovery own that).

**`test_likelihood_equivalence.py`** (new): fast deterministic synthetic bands (`_demo_shared_zeta` pattern); grid-contents pin; bitwise agreement on the full 260-θ grid (`max_rel_diff == 0.0` unit-asserted); exp-branch dispatch points 3.97 | 3.99, 4.0; fabricated disagreement mutates `route_B` while deliberately leaving stale `rel_diff = 0.0` (detection, not reaction); NaN fail-closed; real-window application slow-marked with the data-absent skip convention.

**Also in this lane (per the brief):** stale `alpha` θ-label fixed at `burstfit_joint.py:672` (code unpacks `beta` post-ADR-0006); one pyproject `testpaths` entry.

**Committed artifact:** `local_runs/freya_likelihood_equivalence.json` — verdict PASS, 260 θ, max_rel_diff 0.0, bands CHIME (64, 585) / DSA (16, 472), raw t0_C = 17.557 ms (consistent with #101's raw-init value).

**Physics kernel untouched** (`burstfit.py` not in the diff — Codex-verified).

## Verification Results

All in the `flits` conda env on jakob-mbp, from the `flits-103` worktree:

- ✅ `pytest analysis/scattering-refit-2026-06/test_likelihood_equivalence.py` — 6/6 incl. the slow real-window test; full-suite collection 516 (510 + 6 new), no import errors.
- ✅ Real freya CLI run: PASS, 260 θ, max_rel_diff = 0.0, ~10 s wall.
- ✅ `ruff check` + `ruff format --check` clean on the new files.
- ✅ **Adversarial review** (Codex, gpt-5.5 high, read-only): round 1 REQUEST_CHANGES — one MAJOR: `adjudicate()` trusted precomputed `rel_diff` fields and the disagreement test updated the diff by hand (proving reaction, not detection). Fixed in `b97c12e0` (recompute-from-route-values + stale-diff test). Round 2 **APPROVE, zero findings** — Codex independently executed the `rel_diff()`/`adjudicate()` bodies against the stale-diff case.

## Known Caveats

- Bitwise identity (max_rel_diff = 0.0) holds because both routes execute literally identical float ops in identical order on this machine/env; RTOL = 1e-12 is the documented contract if either route's internals ever diverge legitimately.
- The check is wiring-level by design; kernel correctness evidence lives in Step 1/Step 2 (PRD).
- Stale "alpha" θ labels persist out-of-lane at `burstfit_joint.py` ~634, ~708–709, ~757, and the ~175 comment block (noted in the PR body); pre-existing B905 at `burstfit_joint.py:252`.

## Next Steps

1. **#104** (production joint fit) — its #103 gate is green (merged); still needs the #101 preflight at adopted candidates and the CHIME window decision (`FLITS_ONPULSE_CROP`/`FLITS_ONPULSE_PAD`) first; hours-long dynesty run in background.
2. #105 (Route A cross-check fit; quality-bearing post-#111), #106 (verdict artifact) per the DAG.
3. Pin bump (deliberate `build:` commit in Faber2026) once the DAG's code has merged; target ≥ `41bfe977`.

## References

**Issue/PR:** https://github.com/jakobtfaber/dsa110-FLITS/issues/103 · https://github.com/jakobtfaber/dsa110-FLITS/pull/113
**Sibling docs:** [implement-poc-validate-diagnostics.md](../implement/implement-poc-validate-diagnostics.md) (#111) · [implement-poc-beta-native.md](../implement/implement-poc-beta-native.md) (#102) · [implement-freya-tail-coverage-preflight.md](../implement/implement-freya-tail-coverage-preflight.md) (#101)

---

**Implementation completed by AI Assistant on 2026-07-03**
