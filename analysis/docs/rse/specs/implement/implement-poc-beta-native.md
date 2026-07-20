# Implementation Summary: β-native POC harness + real-data branch (dsa110-FLITS #102)

---
**Date:** 2026-07-03
**Author:** AI Assistant
**Status:** Complete (merged 2026-07-03, squash `37d76a49`)
**Plan Reference:** dsa110-FLITS issue #102 + its Agent Brief (the tracker issues are the plan); PRD "Route A completion" in [prd-freya-beta-comodel-real-data-fit.md](../prd/prd-freya-beta-comodel-real-data-fit.md).

---

## Overview

Slice 8/8 of the freya β co-model DAG's ready pair: `analysis/beta_poc/run_beta_poc.py` migrated to the β-native `FRBParams` API, its dead per-model PBF attribute writes deleted, and its real-data stub completed via the joint driver's own `prepare()` + the #99 freya run-configs. Route A now exists as the independent-likelihood cross-check instrument for #103/#105.

**Final Status:** ✅ Complete — PR https://github.com/jakobtfaber/dsa110-FLITS/pull/110 (`Closes #102`), branch `feat/102-poc-beta-native` off `424d724c`, **merged** 2026-07-03 (squash `37d76a49`, owner-authorized).

## Plan Adherence

One design deviation, surfaced in the PR body: the real-data path is explicit opt-in (`--real`, output to `freya_beta_poc_fit_real.json`) instead of the old auto-detect. Reason: the #99 configs resolve to staged data on this machine, so auto-detect would silently start a real fit on any default invocation and clobber the synthetic artifact. Impact: cheap default preserved; the real Route A fit stays a deliberate act (its runtime budget belongs to #104/#105).

A second in-scope adaptation: real-path t0 prior *centers* come from the raw `data_driven_initial_guess`, not `prepare()`'s MLE-refined init — #101 observed the post-#98 refine dragging CHIME t0 17.6 → 31.4 ms while railing β. Not chasing the refine itself (per the brief); just not inheriting it into a prior center.

## Files Modified

**Modified (dsa110-FLITS):**
- `analysis/beta_poc/run_beta_poc.py` — three `FRBParams(alpha=…)` sites → `beta=` (`_inject`, `_band_ll`, `_goodness`); dead `pbf`/`pbf_beta` writes deleted from `_build_band`/`_inject`/`BetaCoupledLogL`/`_goodness` (the forward model dispatches the PBF on the sampled `p.beta` alone); `BetaCoupledLogL` drops its redundant closure round-trip; `_prepare_real_bands()` + `--real` flag implement the stub; recovery/truth bookkeeping now synthetic-only; vestigial `blocker` field removed.
- `analysis/beta_poc/freya/freya_beta_poc_fit.json` — refreshed under the β-native API (was API-stale pre-co-model provenance).
- Entire-tracing ledger (hook).

**Physics kernel untouched** (`burstfit.py` not in the diff — hard constraint).

## Verification Results

All in the `flits` conda env on jakob-mbp (env-scoped):

- ✅ Synthetic path re-runs without TypeError and **reproduces the pre-migration surface**: β = 3.714 (old artifact 3.712; truth 3.70, rel_err 0.37%), lnZ = −18255.3 (old −18254.6), ncall 181,743 (old 177,627), verdict MARGINAL both. Same seed, same deterministic injection — strong evidence the deleted writes were dead and the migration is behavior-preserving.
- ✅ Real branch wired end-to-end via a deliberately truncated run (`--real --nlive 40 --maxcall 1500 --dlogz 10`): prepared shapes CHIME 64×585 / DSA 16×472 (match the #99 smoke expectations), raw-init t0 17.56/7.97 ms (match #101's probe), real likelihood evaluations ran, `_real.json` written. Junk output deleted, not committed.
- ✅ `ruff check` + `ruff format --check` clean; full collection 487 tests, no import errors.
- ⚠️ **Adversarial review** (Codex, gpt-5.5 high, read-only): REQUEST_CHANGES on two MAJOR findings, **both pre-existing from PR #96 and untouched by this diff** — (1) the POC's private `_validate()` lets R² flip the verdict to MARGINAL, contradicting the kernel's `classify_fit_quality` (R² deliberately informational-only there; both old and refreshed artifacts share the behavior, and chi2_red ≈ 0.99/1.00 is PASS-range); (2) the runner emits no diagnostic figures. Assessed out-of-scope for the migration (changing validation semantics would muddy the behavior-preservation evidence) and filed as **dsa110-FLITS #111**; every in-scope migration check passed. PR comment records the assessment; owner can request the #111 fix inside PR #110 if preferred.

## Known Caveats

- `--real` defaults (`nlive=150`, `maxcall=400k`) are smoke-scale; the production Route A fit for #105 needs a deliberate budget (the exp-era exemplar burned ~10⁶ calls).
- #101's preflight found the prepared CHIME window truncates the heavy tail at the exp-era-suggested scale (2.08 e-folds at τ=0.119/β=3.7) — any real Route A fit inherits that window question; resolve at #104 (`FLITS_ONPULSE_PAD`).
- The dual module identity (`scat_analysis` via the driver's sys.path insert vs `scattering.scat_analysis` in the POC) is carried by duck typing, as in the #99 smoke test — fine at this pin, worth remembering if `isinstance` checks ever appear.

## Next Steps

1. ~~Owner review/merge of PRs #109 and #110.~~ Both merged 2026-07-03 (`d8348f68`, `37d76a49`).
2. ~~Re-triage **#103** (likelihood equivalence) → `ready-for-agent` with a brief once both merge.~~ Done 2026-07-03.
3. #104 (production joint fit) — gated on #101 PASS at its adopted candidates + #103 PASS; must decide the CHIME window question first.
4. ~~**#111** (POC `_validate()` vs `classify_fit_quality`; diagnostic figures).~~ Fixed via PR #112, merged (`d0d3592a`) — see [implement-poc-validate-diagnostics.md](../implement/implement-poc-validate-diagnostics.md).

## References

**Issue/PR:** https://github.com/jakobtfaber/dsa110-FLITS/issues/102 · https://github.com/jakobtfaber/dsa110-FLITS/pull/110
**Branch commits:** `e397b636` (migration + artifact), `c1a2e996` (ledger).
**Sibling docs:** [implement-freya-tail-coverage-preflight.md](../implement/implement-freya-tail-coverage-preflight.md) (#101) · [implement-posterior-comparator.md](../implement/implement-posterior-comparator.md) (#100)

---

**Implementation completed by AI Assistant on 2026-07-03**
