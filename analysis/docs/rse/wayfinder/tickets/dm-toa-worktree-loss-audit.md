# Close the dm-toa worktree loss audit

- Type: `wayfinder:task` (AFK)
- Status: resolved
- Assignee: manuscript owner
- Blocked by: none
- Map: [ApJ submission](../map-apj-submission.md)
- GitHub: [Faber2026-analysis #167](https://github.com/jakobtfaber/Faber2026-analysis/pull/167)

## Current finding

The generated products were preserved before retirement, and the phase-B
configuration files landed under a new path. The only unresolved item is the
reported 1,918 uncommitted inserted lines across nine tracked files. No snapshot
of those exact bytes has been found.

## Owner disposition, 2026-07-30: closed as unverifiable

The manuscript owner closed this audit. The content landed via pull request
167, byte equivalence of the nine tracked-file modifications is unrecoverable,
and reconstructing it is not worth the effort. Recovery is not to be pursued
further.

What is settled: the generated products were preserved with checksums before
retirement, and the 13 phase-B configuration files are tracked on `main` under
`analysis-configs/absolute-dm/phase-b/`, having landed via pull request 167
under a path different from the one first searched.

What stays on the record as unresolved rather than resolved: the 1,918
uncommitted inserted lines across nine tracked paths were never snapshotted, so
no byte-for-byte comparison was ever possible and none will now be attempted.
This ticket closes with that uncertainty stated, not discharged. The
uncertainty still does not authorize deletion or scientific use of anything
derived from those bytes.

The structural cause is carried forward by `enforce-lane-isolation`: untracked
work in a shared checkout is unprotected by construction, and the remedy is a
per-lane checkout rather than any hook.

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
