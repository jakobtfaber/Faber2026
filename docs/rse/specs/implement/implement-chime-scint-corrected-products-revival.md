# Implementation Summary: CHIME scint revival — Phases 1–2 (C1 through go/no-go)

---
**Date:** 2026-07-14
**Author:** AI Assistant (Claude Fable 5, session 39bdc6b7)
**Status:** Phases 1–2 complete; Phases 3–5 conditional path now active
**Plan Reference:** [plan-chime-scint-corrected-products-revival.md](../plan/plan-chime-scint-corrected-products-revival.md) (v1.1)

---

## Overview

Executed plan Phases 1 (eligibility caveat hygiene) and 2 (complete the
owner-decided C1 `c1-allpairs-crossgp` experiment through go/no-go). Phase 2
reached its predeclared **FAIL branch**: the blinded 24-cell × 128-trial
calibration matrix returned **NO-GO** (0/8 gated cells pass; null campaign
fails; all m=1.00 sanity cells pass), so no on-pulse fit was ever unblinded
and the DOCUMENTED-FAIL bundle was written. Per the decision doc's stop rule,
Phase 3 (`p1-window-upchan`, product regeneration) is now the active successor.

**Final Status:** ⚠️ Partially Complete by design — Phases 1–2 done and
verified; Phases 3–5 were always conditional on the Phase 2 verdict and remain
open (Phase 3 triggered).

## Plan Adherence

**Deviations:**
- **Calibration driver flags** — plan showed `run_c1_calibration.py --m ... --width-channels ... --outdir ...`; the implemented driver hardcodes the frozen grid (blinding: the grid is part of `frozen_config.json`, not a CLI knob) and exposes only `--workers/--trials`. Impact: none scientifically; grid identical.
- **Nulls composition** — decision doc's time/pol-scramble and coarse-channel phase-shift controls were folded into the two implemented null families (12 held-out off-pulse LOO windows + 12 seeded pairing-scrambles, 960 comparisons). The family-wise gate still fails even on this narrower set, so the verdict is conservative — adding controls could only add failures.
- **Undersized-cell rejection** added to `aggregate` beyond plan text (caught a stale 2-trial smoke checkpoint that a relative-path `rm` had silently left behind).

## Phases Completed

### Phase 1: Eligibility caveat hygiene — ✅ 2026-07-14
Registry `provenance_caveat: single_block` for hamilton (stays `candidate`) +
johndoeII; `finalize_measurement_status` passthrough (incl. inconclusive
fail-closed branch); campaign-runner registry injection;
`plan-chime-scint-gamma-campaign.md` goal paragraph corrected. Branch
`scint/eligibility-caveats` (worktree `flits-caveat-hygiene`), commits
`4414a53` + ledger `004f705`, **PR jakobtfaber/dsa110-FLITS#177**.

### Phase 2: C1 through go/no-go — ✅ 2026-07-14 (verdict: NO-GO)
Characterization pin (fixture `all_pairs_reference_20260717.npz`, rtol 1e-10)
→ exact closed-form vectorization of `all_pairs_cross_acf` (~1164×: 0.026 s vs
~30 s at freya scale) → `validate_freya_c1.py` (freeze/calibrate/nulls/
aggregate/unblind; unblind structurally refuses without hash-bound GO) → full
blinded matrix → DOCUMENTED-FAIL bundle (RESULT.md, verdict JSON, figures +
manifest + review, INVENTORY.yaml entry, inventory README). Branch
`scint/c1-allpairs-crossgp`, commits `d8d053a`, `694d3f6`, `8f0553f`, ledger
`9c42724`, **PR jakobtfaber/dsa110-FLITS#176**. Full cell × gate matrix:
[experiment-chime-scint-c1-calibration.md](../experiment/experiment-chime-scint-c1-calibration.md).

## Files Modified

**Pipeline submodule, branch `scint/c1-allpairs-crossgp` (PR #176):**
- `scintillation/scint_analysis/cross_acf.py` — vectorized `all_pairs_cross_acf`; extracted `_demean_by_block`, `_lag_block_stats`
- `scintillation/scint_analysis/tests/test_cross_acf.py` + `tests/fixtures/all_pairs_reference_20260717.npz` (+ PROVENANCE.md) — pinned characterization test
- `analysis/chime-scintillation/experiments/c1-allpairs-crossgp/` — `validate_freya_c1.py`, `run_c1_calibration.py`, `plot_c1_calibration.py`, `frozen_config.json`, `RESULT.md`, `calibration_verdict.json`, `calibration/` (24 cells + nulls), `figures/` + manifest + review
- `analysis/chime-scintillation/INVENTORY.yaml`, `README.md` — C1 entry + current-answer update

**Pipeline submodule, branch `scint/eligibility-caveats` (PR #177):**
- `scintillation/configs/chime_products.yaml`, `scint_analysis/chime_artifact_guards.py`, `scint_analysis/pipeline.py`, tests × 2, `scripts/run_chime_scint_campaign.py`

**Faber2026 (this repo):**
- Plan v1.1 checkboxes (Phases 1–2), `experiment-chime-scint-c1-calibration.md` (new), `plan-chime-scint-gamma-campaign.md` (eligibility wording), `docs/rse/control/ACTIVE_LANES.md` C1 row

No files deleted.

## Verification Results

### Automated
- ✅ `pytest scintillation/scint_analysis/tests/test_cross_acf.py -q` — 9 passed (8 existing + pinned reference)
- ✅ `pytest tests/test_chime_product.py tests/test_chime_artifact_guards.py -q` (worktree) — 38 passed
- ✅ 24 calibration cells × 128 finite trials; aggregate recomputes from checkpoints and rejects undersized cells
- ✅ No unblinding artifact exists (aggregate `go: false`; `unblind` never invoked)
- ✅ Campaign runner compiles; registry caveat lookup returns exactly {hamilton, johndoeII}

### Manual
- ✅ Figure review (visual): all 3 calibration figures `match` their manifest expectations (`figures.review.json`)
- ⬜ Owner review of the NO-GO verdict and PRs #176/#177 (pending — human step)

## Issues Encountered

- **Stale smoke checkpoint**: a relative-path `rm` with `2>/dev/null` from the wrong cwd silently failed; the 2-trial `cell_m0.15_w6.json` was skipped as "already complete". Caught by the aggregate undersized-cell check; cell rerun with 128 trials (`--force`) and re-aggregated. Lesson: absolute paths for deletions; never suppress rm stderr.
- **`conda run` heredoc stdin silently no-ops** — generator scripts must be written to disk and run by path.

## Remaining Work

- [ ] Phase 3 (`p1-window-upchan`): windowed oversampled fine channelization — local synthetic tests, h17 regeneration of freya variants (hann×2/×4, `--save-polarizations`), paired products, fresh blinded campaign under a new frozen config (thresholds unchanged)
- [ ] Phase 4/5: conditional on Phase 3 PASS (sample-wide regeneration, campaign rerun, manuscript)
- [ ] Separate lane (decision pending): dirty regenerated B4 outputs in the main pipeline tree — commit with own figure review or revert
- [ ] Merge PRs #176 and #177 (owner/one-way door)

## Next Steps

1. Owner reviews PRs #176/#177 and the NO-GO record.
2. Open the Phase 3 lane (new worktree/branch, h17 access) per plan tasks at `plan-chime-scint-corrected-products-revival.md` Phase 3.
3. Route validation of this implementation via `ai-research-workflows:validating-implementations` if desired.

## References

- [Plan v1.1](../plan/plan-chime-scint-corrected-products-revival.md) · [Research doc](../research/research-chime-scint-measurement.md) · [Owner decision](../decision/decision-2026-07-14-figure1-and-chime-c1.md) · [Experiment record](../experiment/experiment-chime-scint-c1-calibration.md)
- Commits (pipeline): `d8d053a`, `694d3f6`, `8f0553f`, `9c42724` (C1); `4414a53`, `004f705` (caveats)
- PRs: jakobtfaber/dsa110-FLITS#176, #177
