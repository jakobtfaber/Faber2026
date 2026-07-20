# Implementation Plan: Faber2026 remote repository cleanup

---
**Date:** 2026-07-17
**Author:** Codex
**Status:** Complete
**Related Documents:**
- [Repository cleanup research](research-repository-cleanup-2026-07-17.md)
---

## Overview

Apply the owner-approved first cleanup batch to the live Faber2026 and FLITS
fork GitHub repositories. The batch closes status-drifted PRs/issues, updates
the two active issues, enables merged-branch auto-deletion, and deletes only the
exact proven Faber2026 branch set. All local dirty work and all FLITS branch,
pin, upstream-PR, and root-layout decisions remain untouched.

**Goal:** Reduce Faber2026 from 45 to 5 live branches and make future merged PR
branches self-cleaning without losing active or unclassified work.

**Motivation:** Both personal repositories have `delete_branch_on_merge=false`,
and tracker state has drifted from the canonical lane state in
[`docs/rse/program-state.toml:22-111`](../program-state.toml).

## Current State Analysis

- [`docs/rse/program-state.toml:22-75`](../program-state.toml) marks issues #54,
  #68, and #75 done/terminal and the #55 Route B chain terminal.
- [`docs/rse/program-state.toml:78-111`](../program-state.toml) keeps #56 and #58
  proposed.
- [Repository cleanup research](research-repository-cleanup-2026-07-17.md)
  records 45 Faber branches, the exact 36 merged-PR branch set, three additional
  stale branches, and superseded PR #102's head branch.
- [`PIPELINE.md:3-14`](../../../PIPELINE.md) keeps the fork as the manuscript
  authority; no submodule remote or pin change belongs in this batch.

## Desired End State

- Faber2026 PR #102 and FLITS-fork PR #190 are closed as superseded.
- Faber2026 issues #54, #55, #68, and #75 are closed with evidence comments.
- Issues #56 and #58 remain open with current-status comments.
- Both personal repositories report `delete_branch_on_merge=true`.
- Faber2026 has exactly `main`, `gh-pages`, `entire/checkpoints/v1`,
  `infra/owner-board`, and `overleaf-2026-07-11-2125` as live branches.
- The dirty local parent and submodule paths are byte-unchanged except for this
  research/plan documentation.

## What We're NOT Doing

- [ ] Delete any FLITS branch.
- [ ] Merge or close upstream FLITS PR #49.
- [ ] Merge active fork PRs #192 or #193.
- [ ] Change the Faber2026 submodule pin or `.gitmodules`.
- [ ] Delete, move, regenerate, stage, or commit existing dirty local files.
- [ ] Move root manuscript tables or archive `language_audit.md`.

**Rationale:** These actions require separate scientific, provenance, or
repository-layout review and were excluded from the owner's approval.

## Implementation Approach

Use authenticated `gh` API/CLI operations with fail-closed preconditions. Query
each target immediately before mutation; abort if a target has changed state,
head, ownership, or branch disposition. Apply status changes before branch
deletions, then verify the complete remote state from fresh API queries.

## Implementation Phases

### Phase 1: Revalidate approved targets

**Objective:** Prove that the audited state still holds.

**Tasks:**

- [x] Run `gh pr view 102 --repo jakobtfaber/Faber2026 --json state,headRefName,comments`
  and require `OPEN`, the audited head, and the superseded comment.
- [x] Run `gh pr view 190 --repo jakobtfaber/dsa110-FLITS --json state,headRefName,mergeStateStatus`
  and require `OPEN`, the audited head, and no newer replacement work.
- [x] Query issues #54, #55, #56, #58, #68, and #75 and require they remain open.
- [x] Query the 45 Faber branch refs and require every deletion target to exist;
  require no target to back a new open PR.

**Verification:** No mutation occurs unless all predicates pass.

### Phase 2: Correct PR and issue state

**Objective:** Make GitHub status match the audited canonical state.

**Tasks:**

- [x] Close PRs #102 and #190 with explicit supersession comments; delete their
  head branches.
- [x] Comment on and close issues #54, #55, #68, and #75.
- [x] Comment on issues #56 and #58 with active/current status; leave them open.

**Verification:** `gh pr list --state open` excludes #102/#190; Faber open issue
numbers are exactly `56` and `58`.

### Phase 3: Prevent recurrence and prune Faber branches

**Objective:** Enable future automatic cleanup and remove only the approved set.

**Tasks:**

- [x] Patch both personal repositories with `delete_branch_on_merge=true`.
- [x] Delete the 36 merged-PR branches enumerated in the research document.
- [x] Delete literal branch `HEAD` and the two superseded closed-PR branches.

**Verification:** Faber branch names equal the five-name desired set; FLITS
still has all pre-existing branches except PR #190's approved head deletion.

### Phase 4: Final verification and durable record

**Objective:** Prove the remote cleanup and preserve exact outcomes.

**Tasks:**

- [x] Re-query repository settings, branch names, open PRs, and open issues.
- [x] Confirm active FLITS PRs #192/#193 and upstream PR #49 remain open.
- [x] Confirm local dirty paths were not cleaned, reset, staged, or committed.
- [x] Write `implement-repository-cleanup-2026-07-17.md` with before/after state.

**Verification:** All automated success criteria below pass.

## Success Criteria

### Automated Verification

- [x] Faber branch count is 5 and names match the desired set exactly.
- [x] Faber open PR count is 0.
- [x] FLITS-fork open PR numbers are exactly 192 and 193.
- [x] Faber open issue numbers are exactly 56 and 58.
- [x] Both personal repositories return `delete_branch_on_merge=true`.
- [x] Upstream FLITS PR #49 remains `OPEN`.
- [x] `git status --short` still shows the pre-existing dirty lanes plus the two
  cleanup documents; no unrelated path changes state.

### Manual Verification

- [ ] Owner accepts the live GitHub branch/issue/PR summaries after execution.

## Testing Strategy

There is no application code in this batch. Each mutation is surrounded by API
precondition and postcondition queries. The final integration check compares
the complete live branch-name set and issue/PR number sets, not cached local
remote-tracking refs.

## Migration Strategy

Branch deletion is the only hard-to-reverse operation. Merged and closed PR refs
retain commit provenance; the two superseded branches retain replacement PRs.
If a branch is later needed, recreate it from the recorded PR head SHA. Closed
PRs/issues can be reopened, and the auto-delete setting can be disabled through
the same repository API.

## Risk Assessment

1. **Concurrent branch update** — low likelihood, high impact. Re-query all refs
   and abort if any target changed or gained an open PR.
2. **Deleting a branch used by a local worktree** — low impact to local bytes,
   but tracking is lost. The only such audited branch is clean and remains as a
   local branch after remote deletion.
3. **Confusing fork and upstream PR numbers** — medium impact. Every command
   uses an explicit `--repo` target.

## Edge Cases and Error Handling

- A missing branch is treated as already cleaned only after confirming it is not
  an API pagination/error artifact.
- A changed head or new open PR aborts deletion for that branch while the rest
  of the independently validated set may proceed.
- Any API/authorization failure stops the phase; no force push or history rewrite
  is used.

## Documentation Updates

- [x] Complete this plan's execution checkboxes.
- [x] Add `implement-repository-cleanup-2026-07-17.md`.

## References

- [Repository cleanup research](research-repository-cleanup-2026-07-17.md)
- [Branch consolidation handoff](handoff-2026-07-14-branch-consolidation-and-next-actions.md)
- [GitHub Faber2026](https://github.com/jakobtfaber/Faber2026)
- [GitHub FLITS fork](https://github.com/jakobtfaber/dsa110-FLITS)
- [GitHub FLITS upstream](https://github.com/dsa110/dsa110-FLITS)

## Review History

### Version 1.0 — 2026-07-17

- Initial plan written from the live audit and approved outward-action batch.
