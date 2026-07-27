# Implementation Summary: freya scintillation fit-quality semantics + baseline-guard parity (dsa110-FLITS #118)

---
**Date:** 2026-07-03
**Author:** AI Assistant
**Status:** Complete (merged 2026-07-03, squash `9ebe02cf`, owner-authorized; issue #118 auto-closed)
**Plan Reference:** dsa110-FLITS issue #118 (the issue body is the approved
brief, per the #103–#106 lane pattern); findings originate from PR #117
adversarial review round 1 (findings 3–5, unresolved at the #117
fast-forward merge `bffd875`)

---

## Overview

Closes the fit-quality gap left by the freya scintillation CLI lane (#117,
merged `bffd875` by the coordinating Codex session): an uninformative or
bound-railed Lorentzian ACF fit was indistinguishable from a good measurement
in the JSON, and the CLI's baseline-subtraction guard was far weaker than the
neighboring pipeline's.

## What changed (PR #119, branch `fix/118-freya-scint-fit-quality`)

- **`scintillation/scint_analysis/freya_scintillation.py`** (`751acb69`):
  - `measure_scintillation_bandwidth` fails closed — `success=False`,
    `delta_nu_mhz=None`, explicit message — when (a) `curve_fit`'s covariance
    is non-finite (uninformative minimum), or (b) the fitted γ is within 1%
    (`_GAMMA_BOUND_REL_TOL`) of either bound: `0.25*channel_width_mhz` (lower,
    "unresolved by channelization") or `fit_lag_mhz` (upper, "treat as a lower
    limit on Δν_d"). A railed width is a limit, not a measurement — freya's
    YAML has `fit_lagrange_mhz=25` while stored fits include a ~259 MHz wide
    component, so the upper-bound case is realistic.
  - `_failed_fit_result` gained an optional `acf_model` arg so the ACF figure
    still shows the attempted fit on these failure paths (bandwidth marker
    suppressed since `delta_nu_mhz is None`).
  - Baseline subtraction in `prepare_spectrum_from_config` now requires >50
    off-pulse bins — verbatim parity with `pipeline.py:178` — and logs the same
    skip-warning instead of silently proceeding at >2 bins.
  - CLI exit semantics unchanged by design: `main()` already keys the exit code
    off `result.acf.success`, so fail-closed fits now exit 1 (intended per the
    issue).
- **`scintillation/scint_analysis/tests/test_freya_scintillation.py`**
  (`751acb69` + `9f07662`): +6 tests — known-width Lorentzian recovery within
  2% (γ_true=0.4, crafted-ACF monkeypatch of `calculate_acf`; recovered
  0.401656), upper-bound rail (γ_true=5 vs 1 MHz fit range), deterministic
  lower-bound rail (monkeypatched `curve_fit` at γ=0.25×channel_width),
  non-finite covariance, and baseline-guard spy parametrized over
  {30, 50 → skip; 51, 90 → subtract} pinning the exact `pipeline.py` edge.
- **Physics kernel (`scattering/`) untouched**; diff scope is exactly the two
  files (Codex-verified).

## Verification Results

- ✅ Focused pytest: 14 passed; full scint suite: 107 passed (at `751acb69`;
  `9f07662` adds 3 parametrized cases); ruff clean on both files.
- ✅ **Adversarial review** (Codex gpt-5.5 high, read-only, worktree at
  `751acb69`): round 1 **APPROVE, zero P1/P2**. Two P3 test-coverage nits
  (lower-bound branch untested; 50/51 guard edge untested) addressed in
  `9f07662`. Reviewer independently verified via direct source import:
  fail-closed paths serialize `delta_nu_mhz` as `null` under strict
  `allow_nan=False` JSON; figure code plots the retained model curve and
  suppresses the bandwidth marker; guard parity against `pipeline.py:178`
  including the exactly-50/51 edge.
- Verify-gate records: `test` on the module, `test` + `cross-check` on the
  test file.

## Known Caveats

- The two r4 residuals from #117 remain open and out of scope here: no
  end-to-end run against real `scintillation/data/freya.npz` (data product not
  in the checkout), and the mixed `scint_analysis.*` vs
  `scintillation.scint_analysis.*` import pattern's Numba cache risk (needs an
  install-side check).
- The 1% boundary tolerance is a heuristic for TRF asymptotic convergence; a
  legitimate γ within 1% of `fit_lag_mhz` would be reported as a lower limit —
  the conservative direction for a citable bandwidth.

## Next Steps

1. ~~Merge PR #119~~ — **merged** 2026-07-03 (squash `9ebe02cf`, CI 4/4); worktree/branch cleaned up, canonical clone synced.
2. After merge: Faber2026 pin bump to the merged SHA (deliberate `build:`
   commit) if the manuscript is to cite scintillation numbers from this code.
3. Real-data freya run + figure inspection once `freya.npz` is staged
   (#117 handoff, suggested next steps 1–2).

## References

**Issue/PR:** https://github.com/jakobtfaber/dsa110-FLITS/issues/118 · https://github.com/jakobtfaber/dsa110-FLITS/pull/119
**Provenance:** PR #117 review round 1 (findings 3–5) · r4 re-review (coordinating session) · #117 merged ff `bffd875`
**Sibling docs:** [implement-freya-beta-verdict.md](../implement/implement-freya-beta-verdict.md) (#106) · [implement-route-a-crosscheck.md](../implement/implement-route-a-crosscheck.md) (#105)

---

**Implementation completed by AI Assistant on 2026-07-03**
