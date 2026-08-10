# Receipt: deleted dispersion-measure worktree accounting

- Date: 2026-07-29
- Updated: 2026-07-29 after recovery search
- Scope: unresolved content accounting only
- Status: **partially resolved**

## Proven preserved

The removed worktree was
`~/Developer/scratch/worktrees/Faber2026-analysis-dm-toa-geometry-20260728`.
Its generated `dm-toa-geometry-20260728/` products were preserved before
retirement at:

`~/Data/Faber2026/preservation/Faber2026-analysis-dm-toa-geometry-20260728-untracked-20260729/`

The preservation receipt records 19 files, 313 MB, checksums, branch tip
`2354e48`, merged commit `be627c5`, and exact branch-tree equivalence after
pull request 167.

The 13 phase-B configuration filenames previously reported missing are tracked
under `analysis-configs/absolute-dm/phase-b/`. That earlier loss claim was
false; it searched only the retired path.

## Still unresolved

A pre-removal status report attributed 1,918 uncommitted inserted lines to nine
tracked paths:

- `dm-toa-geometry-20260728/README.md`
- `dm-toa-geometry-20260728/casey-hybrid/workflow-config.json`
- `dm-toa-geometry-20260728/one-event-workflow.schema.json`
- `scripts/audit_one_event_dsa_state_h17.py`
- `scripts/build_one_event_dsa_hybrid_h17.py`
- `scripts/one_event_workflow.py`
- `scripts/render_one_event_hybrid_packet.py`
- `scripts/run_one_event_absolute_dm_workflow.py`
- `tests/test_one_event_workflow.py`

The preservation bundle contains generated products and logs, not a snapshot of
these tracked-file modifications. The surviving `codex/dm-minimal` worktree
contains later committed revisions, not proof of the removed uncommitted bytes.
No byte-for-byte comparison is currently possible.

## Recovery checks performed

- Located and read the preservation receipt and checksum inventory.
- Confirmed the old worktree is absent.
- Located the surviving `codex/dm-minimal` worktree.
- Compared its six overlapping script/test files with pull request 167; they
  differ because that branch contains later refactoring.
- Searched the former worktree parent, preservation store, trash, and available
  editor-history locations for a tracked-file snapshot; none found.

## Disposition

Generated products and phase-B configurations: **preserved or integrated**.

Nine reported tracked-file modifications: **unverified possible loss**. Keep
`docs/rse/wayfinder/tickets/dm-toa-worktree-loss-audit.md` open until recovered
bytes permit comparison or the owner explicitly accepts the uncertainty.
