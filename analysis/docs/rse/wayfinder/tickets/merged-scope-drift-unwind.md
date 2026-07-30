# Unwind the merged scope drift

- Type: `wayfinder:task` (HITL)
- Status: resolved
- Assignee: Orchestrator
- Blocked by: none
- Map: [ApJ submission](../map-apj-submission.md)
- GitHub: [Faber2026-analysis #194](https://github.com/jakobtfaber/Faber2026-analysis/pull/194)

## Owner decision card

Resolved technically on 2026-07-30: keep the published history, audit the
landed content in place, and repair defects through focused pull requests.
Independent standards, specification, and science-evidence reviews found
blocking defects in the later Zach records; this ticket does not treat a green
suite as scientific acceptance.

```json
{
  "id": "merged-scope-drift-unwind",
  "kind": "scientific",
  "title": "Unwind merged scope drift",
  "decision": "Now that three lanes landed together in one merge, unwind any of it, or accept the combined history and move on?",
  "recommended": {
    "choice": "accept",
    "reason": "Every lane's content is on main and the suite is green, so unwinding would cost more than it recovers."
  },
  "choices": [
    {
      "id": "accept",
      "label": "Accept the combined history; require per-lane review only for future merges."
    },
    {
      "id": "review-in-place",
      "label": "Keep the history but have each lane owner review their own landed content now."
    },
    {
      "id": "unwind",
      "label": "Revert the combined merge and re-land each lane separately."
    }
  ],
  "context": [
    "Pull request 194 merged as b454154b: 491 files, +18847/-1365, combining the subject-directory migration (369 renames), the foreground census validation, and the Zach count-readiness work under a title naming only one of them.",
    "It also landed files that had been placed off-limits (OWNER_QUEUE.md, scripts/owner_queue.py, tests/test_owner_queue.py, the owner-queue ritual), and no lane owner reviewed their own content before it merged.",
    "The full suite is green at current main, and the cause was identified as one authorized reorganize-and-commit request executed inside a checkout three other lanes shared, not a defect in the landed content."
  ],
  "evidence": [
    {
      "label": "Pull request 194",
      "path": "https://github.com/jakobtfaber/Faber2026-analysis/pull/194"
    },
    {
      "label": "Scope and worktree audit receipt",
      "path": "docs/rse/specs/receipt-branch-scope-and-worktree-audit-2026-07-29.md",
      "sha256": "eaa6371fd4f87d6e74b19bdcae5f8b06a77f7744fbc44209f98789f27425abea"
    },
    {
      "label": "Subject-directory migration spec, the largest lane in the merge",
      "path": "docs/rse/specs/subject-directory-migration-2026-07-28.md",
      "sha256": "97be7463ce44892cb5f5c302033c0daf3d0e3d0067d896ec6b52575c19472f6f"
    }
  ],
  "effect": "Settles whether the combined merge stands as landed or is reverted and re-landed per lane.",
  "recorder": {
    "path": "docs/rse/wayfinder/tickets/merged-scope-drift-unwind.md",
    "action": "Record the owner choice here; if unwind is chosen, open the revert against the exact merge commit b454154b."
  },
  "priority": 25
}
```

## Provenance of this ticket

This card replaces `branch-194-scope-disposition.md`, which asked whether to
merge pull request 194. That question was overtaken: the pull request merged
while the objection was being written, so the remaining decision is whether to
unwind rather than whether to land.

The original ticket file was deleted from disk on 2026-07-29 without ever being
committed to any branch, so it exists in no commit, stash, or remote. Its
content was reconstructed from the authoring session transcript and rewritten
here for the post-merge question. The deletion remains unattributed: both
concurrent lanes disclaim it and neither transcript records a removal.

## What is not in dispute

The landed content itself is not alleged to be wrong. The suite passes at
current main, and the combined merge was traced to a single authorized request
to audit and reorganize `analysis/`, finishing with a commit, which was executed
as one commit inside a checkout that three other lanes shared. The decision here
is about review discipline and history, not about correctness of the code.
