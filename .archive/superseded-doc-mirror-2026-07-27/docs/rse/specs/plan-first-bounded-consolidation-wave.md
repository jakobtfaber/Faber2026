# Implementation Plan: first bounded consolidation wave

---
**Date:** 2026-07-20 local / 2026-07-21 UTC
**Author:** Codex
**Status:** Approved
**Related Documents:**
- [Research: first bounded consolidation wave](research-first-bounded-consolidation-wave.md)
- [Ratified consolidation gates](../wayfinder/tickets/authority-11-ratify-preservation-and-consolidation-gates.md)

---

## Overview

Remove one verified-empty, rebuildable scratch build directory using
non-recursive `rmdir`. The owner explicitly approved this exact deletion list
after reviewing the live evidence. Every other path remains excluded.

**Goal:** Remove only
`/Users/jakobfaber/Developer/scratch/faber_build`, fail closed if its state
changes, and record post-removal proof.

**Motivation:** Exercise the ratified consolidation gates on the smallest,
lowest-risk candidate before any broader preservation or repair wave.

## Current State Analysis

The candidate is named by the first-wave ticket, which requires fresh
emptiness, process, reference, and ownership checks
([authority-12:12-16](../wayfinder/tickets/authority-12-authorize-first-bounded-wave.md#L12)).
The prior estate inventory classified it as an empty, ordinary, non-Git build
directory
([worktree classification:78-84](research/research-authority-worktree-classification-2026-07-20.md#L78)).
The live research packet confirms zero contents, zero KiB, no current consumer,
and mode `0755`
([research](research-first-bounded-consolidation-wave.md)).

## Desired End State

- The exact target path does not exist.
- No sibling or other project path changes.
- The action receipt records preflight and post-removal evidence.
- Rollback remains `mkdir -m 0755` on the exact path.

## What We're NOT Doing

- No recursive removal, wildcard, variable-expanded target, or second path.
- No worktree, data, results, log, preservation packet, or service change.
- No results-library or CHIME-path repair.
- No scientific adoption, branch merge, archive, retirement, or remote action.

## Implementation Approach

Use literal-path assertions immediately before a literal-path, non-recursive
`rmdir`. `rmdir` is the safety mechanism: it refuses to remove a non-empty
directory. Postflight proves the path is absent and its parent remains present.

## Implementation Phases

### Phase 1: Fail-closed preflight

- [x] Complete

**Objective:** Prove the approved target has not drifted.

Run:

```bash
test -d /Users/jakobfaber/Developer/scratch/faber_build
test ! -L /Users/jakobfaber/Developer/scratch/faber_build
test "$(find /Users/jakobfaber/Developer/scratch/faber_build -mindepth 1 -maxdepth 1 -print | wc -l | tr -d ' ')" = 0
test "$(stat -f '%Su' /Users/jakobfaber/Developer/scratch/faber_build)" = jakobfaber
test "$(stat -f '%Lp' /Users/jakobfaber/Developer/scratch/faber_build)" = 755
test -z "$(lsof +D /Users/jakobfaber/Developer/scratch/faber_build 2>/dev/null)"
```

Any failure stops the wave without mutation.

### Phase 2: Remove the exact empty directory

- [x] Complete

**Objective:** Remove only the approved target.

```bash
rmdir /Users/jakobfaber/Developer/scratch/faber_build
```

No `rm`, recursion, glob, environment variable, or command substitution is
permitted.

### Phase 3: Verify and receipt

- [x] Complete

**Objective:** Prove the exact outcome.

```bash
test ! -e /Users/jakobfaber/Developer/scratch/faber_build
test -d /Users/jakobfaber/Developer/scratch
```

Record executor, authorization, timestamps, literal command, preflight results,
postflight results, exclusions, and rollback in
`docs/rse/specs/implement-first-bounded-consolidation-wave.md`.

## Success Criteria

### Automated Verification

- All Phase-1 assertions pass immediately before removal.
- `rmdir` exits zero.
- Both Phase-3 assertions pass.
- Repository dirty paths are unchanged except for this task's documentation.

### Manual Verification

- Owner approval names the one exact deletion target.
- Receipt states that no other target was changed.

## Testing Strategy

The preflight assertions are the test-first guard. Non-empty, missing,
symbolic-link, wrong-owner, wrong-mode, or open-file states stop before the
implementation command. The postflight assertions test the outcome.

## Migration Strategy

No data migration occurs. If the empty path is later needed, restore it with:

```bash
mkdir -m 0755 /Users/jakobfaber/Developer/scratch/faber_build
test -d /Users/jakobfaber/Developer/scratch/faber_build
test "$(stat -f '%Lp' /Users/jakobfaber/Developer/scratch/faber_build)" = 755
```

## Risk Assessment

- **State drift:** low likelihood, low impact. Immediate assertions plus
  non-recursive `rmdir` stop on new contents.
- **Hidden consumer:** low likelihood, low impact. Live open-file/reference
  checks pass; historical callers already create the directory with `mkdir -p`.
- **Wrong target:** low likelihood, high impact. Literal path only; no variable,
  glob, recursion, or second target.

## Edge Cases and Error Handling

- Target missing before execution: stop and record no-op; do not recreate then
  remove it.
- Target gains content: `rmdir` fails; leave contents untouched and stop.
- Owner/mode/open-file check changes: stop and refresh the action packet.
- Postflight fails: do not touch siblings; inspect exact path and use rollback
  only if required.

## Performance Considerations

One empty-directory metadata operation; expected completion is immediate.

## Documentation Updates

- Create the implementation receipt named in Phase 3.
- Refresh the knowledge-base index after receipt creation.

## References

- [Research: first bounded consolidation wave](research-first-bounded-consolidation-wave.md)
- [Ratify preservation gates and the consolidation sequence](../wayfinder/tickets/authority-11-ratify-preservation-and-consolidation-gates.md)
- [Authorize the first bounded preservation and consolidation wave](../wayfinder/tickets/authority-12-authorize-first-bounded-wave.md)
- [Worktree classification](research/research-authority-worktree-classification-2026-07-20.md)

## Review History

### Version 1.0 — 2026-07-20

- Exact one-directory plan created after explicit owner approval.
