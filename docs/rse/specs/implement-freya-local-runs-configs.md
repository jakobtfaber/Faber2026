# Implementation Summary: freya local-runs configs + band-prep smoke test (dsa110-FLITS #99)

---
**Date:** 2026-07-02
**Author:** AI Assistant
**Status:** Complete
**Plan Reference:** dsa110-FLITS issue #99 + its Agent Brief comment (the tracker issues are the plan — see `prd-freya-beta-comodel-real-data-fit.md` status line); supplemented by the PRD's Implementation/Testing Decisions.

---

## Overview

First slice (1/8) of the freya β co-model real-data fit DAG: freya (FRB 20230325A)
CHIME+DSA run-configs authored in the established local-runs pattern, plus a
slow-marked smoke test proving real-data band preparation end-to-end through the
local joint-fit driver's own `prepare()` step, with no driver changes.

**Implementation Duration:** 2026-07-02, single session.

**Final Status:** ✅ Complete — merged to upstream main as `00a66262` (squash of PR #107, 2026-07-03), #99 auto-closed.

## Plan Adherence

**Plan Followed:** issue #99 agent brief (jakobtfaber/dsa110-FLITS), all four acceptance criteria met.

**Deviations from Plan:**

- **Deviation 1:** `alpha_fixed: 4.0` omitted from the freya configs despite literal
  field-mirroring of the whitney_fine precedent.
  - **Reason:** The joint driver never reads it in this prep path; production freya
    configs don't carry it; and mirroring it as an inert field is not harmless — a
    future single-band reuse of these YAMLs would read it as a fixed-α constraint.
    freya's α/β must remain unconstrained because measuring whether the deprecated
    exp-era fit's steep-α suggestion (free-α + fixed-exponential-PBF, α ≈ 4.36 —
    invalid as ground truth per CONTEXT.md) survives under the β co-model is the
    hypothesis this whole DAG tests. Epistemic status: "α > 4 for freya" is a
    deprecated-fit suggestion and the target of validation, not a current-model
    result.
  - **Impact:** None on the joint path; single-band re-use samples β instead of
    fixing it. Documented in the PR body.

No other deviations.

## Phases Completed

### Phase 1 (only phase): configs + smoke test
- ✅ **Status:** Complete (2026-07-02)
- **Summary:** Worktree `~/Developer/scratch/worktrees/flits-issue99-freya`, branch
  `feat/99-freya-local-runs-configs` off upstream main `43f4c824` (worktree-per-agent
  + protected-branch rules observed). Two config YAMLs + one test file; no source changes.

## Files Modified

**Created (dsa110-FLITS, branch `feat/99-freya-local-runs-configs`):**
- `analysis/scattering-refit-2026-06/local_runs/configs/freya_chime_run.yaml` — CHIME band config; `dm_init: 0.0` (coherently dedispersed), f16/t24, `outer_trim: 0.15`.
- `analysis/scattering-refit-2026-06/local_runs/configs/freya_dsa_run.yaml` — DSA band config; `dm_init: 912.4` (catalog DM, `configs/bursts.yaml` — incoherently dedispersed, smearing at dedispersion DM), f384/t2.
- `tests/test_freya_local_runs_smoke.py` — slow-marked band-prep smoke test.

**Modified:** `docs/entire-tracing-checkpoints.md` (post-commit hook ledger, tail-committed per repo closeout convention). No source files modified. No files deleted.

## Key Changes Summary

1. **Provenance-correct data paths.** All `path`/`telcfg_path`/`sampcfg_path` entries
   resolve through the pinned manuscript checkout
   (`/Users/jakobfaber/Developer/overleaf/Faber2026/pipeline/...`), whose
   `data/{chime,dsa}/*.npy` are symlinks into `~/Data/Faber2026/`. This corrects the
   whitney precedent's canonical-clone paths (the provenance trap flagged in the
   handoff) and honors the PRD's execution locus: fits run from the pin.
2. **Smoke test exercises the driver itself.** The test importlib-loads
   `local_runs/run_joint_fit.py` (with `FLITS_REPO` pointed at the repo under test)
   and calls its `prepare()` — so "consumable by the driver without driver changes"
   is asserted literally, covering config load → telescope block → `.npy` load →
   bandpass/trim/downsample/on-pulse crop → `FRBModel` → data-driven init.
   Asserts shapes (64 CHIME / 16 DSA channels), ascending frequency, band endpoints,
   finite S/N-unit data, per-channel noise vector, positive-τ init — no fitted values.
   Skips when the external data symlinks are unstaged (`test_flux_cal.py` convention).

## Verification Results

### Automated Verification

All automated results below are from the `flits` conda env on jakob-mbp — they are
environment-specific, not universal (independently reproduced by a Codex review,
2026-07-02, which re-ran the smoke test: 2 passed in 7.58s).

- ✅ `pytest tests/test_freya_local_runs_smoke.py` — 2 passed in 6.35s (real data, both bands; on-pulse crop engaged: DSA 875 → 472 samples)
- ✅ `ruff check` + `ruff format --check` — clean on the Python test file (the YAML configs are not a ruff surface)
- ✅ `pytest -m "not slow"` on the file — 2 deselected (marker honored; `--strict-markers` active)
- ✅ `pytest --collect-only -q` — 475 tests collected, no import errors, **in the `flits` env**. Caveat: a clean py312 runner fails collection on missing `ipywidgets` — on this branch *and* on upstream main alike (pre-existing environment gap, not a PR regression). Remote PR checks summarize as 4 passed.

### Manual Verification

- [x] PR https://github.com/jakobtfaber/dsa110-FLITS/pull/107 reviewed (owner delegated review to Codex: APPROVE, zero findings) and merged on owner instruction 2026-07-03 (`00a66262`).
- [ ] Optional spot-check: run the smoke test from the pinned checkout context once the pin advances past this merge.

## Issues Encountered

No blocking issues. One observation recorded for downstream (#104): the post-#98 MLE
init refinement drives β to the thin-screen floor on both freya bands (CHIME β → 2.065,
derived α ≈ 63; DSA β → 2.495, α ≈ 10). Init-only — nested sampling uses absolute
prior bounds and is init-independent by design — but worth eyes when the production
joint fit runs. Noted in the PR body.

## Testing Summary

**Tests Added:** `tests/test_freya_local_runs_smoke.py::test_freya_band_prep_smoke[{chime,dsa}]` — real-data band-preparation smoke via the driver's `prepare()`.

**All Tests Passing:** ✅ Yes (2/2 in the `flits` env; see the environment caveat under Verification Results).

## Performance Observations

Not a concern for this slice (smoke test runs in ~6 s with real data).

## Documentation Updated

No documentation updates required beyond config header comments (why-comments per repo style) and this summary.

## Remaining Work

The rest of the #99–#106 DAG (this slice unblocks #101, #102):

- [x] #100 posterior comparator — merged as `424d724c` (PR #108); see `implement-posterior-comparator.md`
- [x] Re-triage #101/#102 → `ready-for-agent` with agent briefs (done 2026-07-03, post-merge)
- [ ] #103–#106 per the DAG; pin bump only after upstream merges (target now ≥ `424d724c`)

## Next Steps

1. Human: review + merge PR #107 (`Closes #99` auto-closes the issue).
2. Re-triage #101/#102 with agent briefs (per `docs/agents/triage-labels.md`).
3. Implement #100 in a separate worktree.
4. Validate with `ai-research-workflows:validating-implementations` if desired before merge.

## Lessons Learned

**Technical Insights:**
- The local-runs driver reads configs from `$FLITS_RUNS/configs/`, so the test drives
  `prepare()` directly with explicit config paths — no env-dependent directory layout
  needed beyond `FLITS_REPO`.
- The repo's post-edit autoformatter and `--strict-markers` were non-issues here
  because imports shipped with consumers in the same edit and `slow` is registered.

## References

**Plan:** https://github.com/jakobtfaber/dsa110-FLITS/issues/99 (agent brief comment)
**PRD:** [prd-freya-beta-comodel-real-data-fit.md](prd-freya-beta-comodel-real-data-fit.md)
**Research:** [research-pipeline-2d-fit-scattering-index.md](research-pipeline-2d-fit-scattering-index.md)
**Handoff resumed:** [handoff-2026-07-02-20-06-freya-beta-fit-issues-triage.md](handoff-2026-07-02-20-06-freya-beta-fit-issues-triage.md)
**PR:** https://github.com/jakobtfaber/dsa110-FLITS/pull/107
**Commits:** `9328bf8` (configs + test), `579c108` (entire ledger tail-commit)

---

**Implementation completed by AI Assistant on 2026-07-02**
