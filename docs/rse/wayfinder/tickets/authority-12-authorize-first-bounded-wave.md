# Authorize the first bounded preservation and consolidation wave

- Type: `wayfinder:grilling` (HITL)
- Status: resolved
- Assignee: —
- Blocked by: [Ratify preservation gates and the consolidation sequence](authority-11-ratify-preservation-and-consolidation-gates.md), [Choose the results-library and CHIME-path repair batch](authority-13-choose-link-and-chime-path-repair.md)
- Map: [Project authority and custody](../map-project-authority-and-custody.md)
- Delegation: [Standing delegated decision authority](../standing-delegation-2026-07-20.md)
- Triage: `ready-for-human`

## Question

Which exact, smallest class is approved for the first execution wave, with
source paths, destinations, receipts, rollback, and explicit exclusions? Test
the reported empty `faber_build` directories as candidates, but authorize no
removal unless fresh emptiness, process, reference, and ownership checks all
pass. Keep every unlisted path out of scope.

## Answer

The first bounded wave is exactly the already completed, owner-approved,
non-recursive removal of:

`/Users/jakobfaber/Developer/scratch/faber_build`

- **Class:** verified-empty, rebuildable output directory.
- **Destination:** none. No content existed to preserve or move.
- **Preflight:** at `2026-07-21T04:15:50Z`, the exact path was an ordinary
  directory, not a symbolic link; it contained zero children and zero KiB;
  owner was `jakobfaber`, mode was `0755`; no open file, live consumer, or
  symbolic-link reference was found.
- **Action:** owner explicitly approved that one exact directory; execution
  used `rmdir`, so a non-empty target would have failed closed.
- **Postflight:** at `2026-07-21T04:15:51Z`, the target was absent and its
  parent `/Users/jakobfaber/Developer/scratch` remained intact. A fresh check
  on 2026-07-20 America/Los_Angeles confirms the same state.
- **Recovery:** recreate only the empty directory with
  `mkdir -m 0755 /Users/jakobfaber/Developer/scratch/faber_build`.
- **Receipts:** [research](../../specs/research-first-bounded-consolidation-wave.md),
  [plan](../../specs/plan-first-bounded-consolidation-wave.md),
  [implementation](../../specs/implement-first-bounded-consolidation-wave.md),
  and [validation](../../specs/validation-first-bounded-consolidation-wave.md).
  Validation passed all three phases and all six checks; no manual gate remains.

No other path, worktree, preservation packet, data or results store, service,
branch, remote, fitting output, raw CHIME HDF5 file, or scientific trust state
is included. [Choose the results-library and CHIME-path repair batch](authority-13-choose-link-and-chime-path-repair.md)
defines a separate pending implementation batch; this ticket neither executes
nor broadens it. No further removal is authorized here.
