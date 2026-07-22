# Implementation Summary: tail-coverage preflight (dsa110-FLITS #101)

---
**Date:** 2026-07-03
**Author:** AI Assistant
**Status:** Complete (merged 2026-07-03, squash `d8348f68`)
**Plan Reference:** dsa110-FLITS issue #101 + its Agent Brief (the tracker issues are the plan); PRD "deep module 1" in [prd-freya-beta-comodel-real-data-fit.md](../notes/prd-freya-beta-comodel-real-data-fit.md).

---

## Overview

Slice 7/8 of the freya β co-model DAG: `analysis/scattering-refit-2026-06/tail_coverage.py` — a pure, deterministic function `(band geometry, τ₁GHz, β, prepared window[, t0]) → captured e-folds of the power-law PBF tail + hard-threshold PASS/FAIL`, plus the recorded preflight artifact on freya's real prepared CHIME+DSA windows. #104 gates on this check before any sampling.

**Final Status:** ✅ Complete — PR https://github.com/jakobtfaber/dsa110-FLITS/pull/109 (`Closes #101`), branch `feat/101-tail-coverage-preflight` off `424d724c`, **merged** 2026-07-03 (squash `d8348f68`, owner-authorized).

## What the math is

Closed-form integrals of the `gaussian_powerlaw_convolution` piecewise PBF (exp head ≤ s_c, `(s/s_c)^(-β/2)` tail beyond, s_c = 2 ln(2/(4−β))), normalized by the total area; "captured e-folds" is the equivalent exponential depth E = −ln(1−F), which reduces *exactly* to window-span-in-τ-units on the model's pure-exponential branch (β within `BETA_EXP_EPS` of 4). Verdict evaluated at the band's lowest frequency (largest τ(ν), worst tail). β clipping and exp-branch dispatch mirror `FRBModel.__call__` exactly. Threshold default 3.0 e-folds (≈95% area) — caller-tunable engineering default; adjudication out of scope per the brief.

## Files Modified

**Created (dsa110-FLITS):**
- `analysis/scattering-refit-2026-06/tail_coverage.py` — module + CLI (`run_preflight` over a (τ, β) candidate grid via the joint driver's own `prepare()` + the #99 freya run-configs).
- `analysis/scattering-refit-2026-06/test_tail_coverage.py` — 22 analytic unit tests + 1 slow-marked real-window test (skips where the pinned-checkout data symlinks are absent).
- `analysis/scattering-refit-2026-06/local_runs/freya_tail_coverage.json` — the recorded verdict artifact (24 grid points × 2 bands' metadata).

**Modified:** `pyproject.toml` (one `testpaths` entry, per the #100 precedent); entire-tracing ledger (hook).

## Findings (these gate #104)

1. **CHIME FAILs the preflight at the exp-era-suggested scale**: at (τ=0.119 ms, β=3.7) only **2.08 e-folds / 87.5%** of the PBF area fits in the prepared on-pulse-cropped window (raw-init t0 = 17.6 ms, window end 35.9 ms, τ(0.4 GHz) ≈ 6.4 ms). CHIME fails **all** β ≤ 3.7 grid points and passes only near the exponential limit (β=3.95 at τ ≤ 0.119). **DSA passes everywhere** (≥ 3.95 e-folds). If freya's τ/β are near the deprecated exp-era suggestion, the current CHIME window truncates the tail — the silent-β-bias risk the POC sidestepped synthetically (its τ=0.05 ms + early t0 bought ~10 e-folds). Practical lever for #104: the driver's `FLITS_ONPULSE_CROP` / `FLITS_ONPULSE_PAD` env knobs widen the window with zero code change; that decision belongs to #104.
2. **The post-#98 MLE init refine drags t0, not just β**: on freya CHIME it moved t0 from 17.56 ms (raw data-driven guess) to 31.35 ms (near the window end) while railing β → 2.065. The preflight therefore evaluates at the **raw** data-driven t0 and records both (`t0_raw_init_ms`, `t0_mle_init_ms`). Still init-only for the nested-sampling measurement, but anything consuming init.t0 as a location (prior centers, window checks) must not inherit it. Extends the #99 observation; flagged again for #104.

## Verification Results

All in the `flits` conda env on jakob-mbp (env-scoped, per the #99/#100 convention):

- ✅ 23/23 tests (4.1 s): closed form vs independent trapezoid integration of the piecewise PBF (β ∈ {3, 11/3, 3.7} × S ∈ {0.5, 2, 5, 20}, rel 1e-3); exp-limit E=S equality; threshold boundary (≥ at, < below); monotonicity + slow heavy-tail saturation (β=3.7 needs s≈2·10⁴ for <0.1% outstanding); worst-channel = f_min; τ(ν) scaling + t0 handling; burst-past-window-end → 0 captured, FAIL; β-edge clipping mirrors kernel; JSON-serializability at extreme s; crossover known values; slow real-window run end-to-end.
- ✅ `ruff check` + `ruff format` clean; full collection 510 tests, no import errors.
- ✅ Physics kernel, crop/window logic, sampler: untouched (hard constraints honored).
- ✅ **Adversarial review** (Codex, gpt-5.5 high, read-only): **APPROVE, zero findings** — reviewer re-derived the closed-form integrals independently, confirmed the `FRBModel.__call__` dispatch mirror, and spot-recomputed artifact grid points without importing the module (CHIME (0.119, 3.7) → E = 2.0754; DSA → E = 6.7133; both match the JSON).

## Epistemic status

The τ grid **spans the deprecated exp-era fit's suggestion** (τ₁GHz ≈ 0.119 ms, α ≈ 4.36 → β ≈ 3.70) as a stress-test scale — class (2) claims per the guardrail (deprecated-fit suggestions), not ground truth; the artifact's `epistemic_note` says so. The CHIME FAIL is a *conditional* statement: **if** τ/β land near that suggestion, the window truncates the tail.

## Next Steps

1. ~~#102 (Route A completion) — parallel slice, separate lane (PR in flight this session).~~ Merged (PR #110, `37d76a49`).
2. ~~#103 (likelihood equivalence) → re-triage `ready-for-agent` once #101/#102 merge.~~ Re-triaged 2026-07-03 with an Agent Brief.
3. #104 must run this preflight at its adopted candidates and decide the CHIME window question (`FLITS_ONPULSE_PAD` widening vs accepting the near-exponential-only regime) **before** the hours-long dynesty run.

## References

**Issue/PR:** https://github.com/jakobtfaber/dsa110-FLITS/issues/101 · https://github.com/jakobtfaber/dsa110-FLITS/pull/109
**Branch commits:** `97476391` (module + tests + artifact), `7a9377dd` (ledger).
**Sibling docs:** [implement-posterior-comparator.md](../implement/implement-posterior-comparator.md) (#100) · [implement-freya-local-runs-configs.md](../implement/implement-freya-local-runs-configs.md) (#99)

---

**Implementation completed by AI Assistant on 2026-07-03**
