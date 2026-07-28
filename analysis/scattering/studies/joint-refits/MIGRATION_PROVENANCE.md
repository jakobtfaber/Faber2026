# Migration provenance — scattering/studies/joint-refits campaign diagnostics

**Date:** 2026-07-27
**Status:** diagnostic / provenance-preserved. Nothing in this directory is a
paper-ready scientific result; it is the campaign-specific diagnostic and
workflow record relocated out of the FLITS pipeline repository.

## What this directory is

The complete `analysis/scattering/studies/joint-refits/` tree from the
`dsa110-FLITS` repository, containing the Zach fine-structure diagnostics
(`zach_*.py`, `run_joint_fit_zachfine.py`), the two-screen fitter and its
validation suite (`twoscreen*.py`, `validate_twoscreen.py`,
`TWOSCREEN_FITTER_PROVENANCE.md`), the PL-PBF fitter suite (`plpbf*.py`,
`PLPBF_FITTER_PROVENANCE.md`), and the surrounding drivers, helpers,
audit documents, and run records of the 2026-06/07 scattering-refit
campaign.

Boundary rule applied (owner, 2026-07-27): the FLITS repository retains
only general reusable two-dimensional time–frequency fitting
infrastructure; manuscript-specific analysis choices and campaign
workflow live here in Faber2026-analysis.

## Exact source snapshot

- Source repository: `jakobtfaber/dsa110-FLITS`
- Tree extracted at commit `d171a595722565377bbbca66bd3623855697be65`
  (`git archive d171a59 analysis/scattering/studies/joint-refits`), the tip of
  the local integration branch `integrate/h17-snapshots-20260727`
  (checked out in the worktree `/private/tmp/flits-integrate`; that
  commit only removes an editor backup file from the stacked snapshots
  and is not itself pushed).
- The integration branch stacks three frozen snapshots of dirty h17
  worktrees, each preserved on a remote branch:

  | Snapshot commit | Remote branch (origin) | h17 dirty-worktree base |
  |---|---|---|
  | `643ecb0bb2a00a4afaf79ee26cea715988dec9aa` | `archive/h17-joint-tf-fits-snapshot-20260727` | `d292f4b91ef0` |
  | `923b1eae6b3d5869bd56ffe13af66a16682f68ae` | `archive/h17-model-grid-diagnostic-snapshot-20260727` | `31f7744758cc` |
  | `e7a274774026f67cf957cbbbbc1a97504568f56b` | `archive/h17-resolution-diagnostic-snapshot-20260727` | `08649392d9c9` |

- Because the snapshots stack, `joint_tf_prep.py` in this tree carries
  the resolution-diagnostic version (`e7a2747`). The joint-tf-fits
  version it superseded is preserved verbatim at
  `variants/joint_tf_prep.py.snapshot-joint-tf-fits-643ecb0`.

## FLITS engine diffs carried as unapplied patches

The joint-tf-fits and model-grid snapshots also modified generic engine
files under `scattering/scat_analysis/` in FLITS. Per the boundary rule
those files are not migrated as code here; the exact diffs are preserved
unapplied in `flits-library-diffs/`:

- `643ecb0-joint-tf-fits-scat_analysis.patch` — `burstfit.py`,
  `burstfit_joint.py` (the snapshot's 1621-line editor backup file
  `burstfit.py.bak-fftfix-20260717-163931` is excluded; it was dropped
  from the integration branch in `d171a59` and remains recoverable from
  `origin/archive/h17-joint-tf-fits-snapshot-20260727`).
- `923b1ea-model-grid-joint_model_grid.patch` — `joint_model_grid.py`.

Their disposition (adopt into the analysis-owned engine during
decoupling, or land in FLITS) is an open item of the decoupling plan.

## Scientific standing

Diagnostic evidence only. Known campaign-level caveats recorded
elsewhere still apply (e.g. the PL-PBF single-screen model was rejected
2026-07-18; the ±20 ms t0-prior bug invalidates certain fine fits).
Nothing here supersedes the production limits or the two-screen
two-band decomposition record in `CONTEXT.md`.

## What was NOT changed

- The FLITS source repository, its branches, worktrees, and the
  `pipeline/` submodule pin in Faber2026 are untouched.
- No scientific result is promoted by this migration.

## Cutover / retirement gate

FLITS-side retirement of the source material is separately gated; see
`docs/rse/specs/plan-flits-decoupling-2026-07-27.md`. Do not delete the
FLITS copies or the archive branches until that plan's acceptance
verification passes and the owner approves the retirement step.
