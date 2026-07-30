# Close the dm-toa worktree loss audit

- Type: `wayfinder:task` (AFK)
- Status: open
- Assignee: orchestrator
- Blocked by: none
- Map: [ApJ submission](../map-apj-submission.md)
- GitHub: [Faber2026-analysis #167](https://github.com/jakobtfaber/Faber2026-analysis/pull/167)

## Current finding

The generated products were preserved before retirement, and the phase-B
configuration files landed under a new path. The only unresolved item is the
reported 1,918 uncommitted inserted lines across nine tracked files. No snapshot
of those exact bytes has been found.

## Orchestrator disposition

This is a technical preservation audit, not a scientific or visual decision.
Recovery remains open until the nine tracked-file modifications are accounted
for or independently proven unrecoverable. No manuscript-owner action is
required, and the uncertainty does not authorize deletion or scientific use.

## Corrections recorded

The claim that the `phase-b` files existed in no commit, stash, or remote was
repeated twice and was already false when last repeated. The check tested the
old path, `dm-toa-geometry-20260728/phase-b`, instead of searching for the
content, which had moved to `analysis-configs/absolute-dm/phase-b`. The
practical consequence is that the preservation warning was overstated for those
13 files. Only the tracked-file accounting remains open.

The generated-product directory was also not lost. A preservation bundle with
checksums and a receipt exists under `~/Data/Faber2026/preservation/`. The
remaining uncertainty is limited to the nine tracked-file modifications.
