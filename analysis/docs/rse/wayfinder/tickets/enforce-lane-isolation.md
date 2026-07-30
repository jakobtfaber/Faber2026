# Enforce lane isolation and identity

- Type: `wayfinder:task` (HITL)
- Status: open
- Assignee: manuscript owner
- Blocked by: none
- Map: [ApJ submission](../map-apj-submission.md)

## Owner decision card

```json
{
  "id": "enforce-lane-isolation",
  "kind": "scientific",
  "title": "Enforce lane isolation and identity",
  "decision": "Adopt an enforcing mechanism for concurrent lanes, or keep the advisory conventions and accept recurrence?",
  "recommended": {
    "choice": "isolate-and-identify",
    "reason": "One shared checkout with one shared git identity caused every incident this session and left three of them unattributable."
  },
  "choices": [
    {
      "id": "isolate-and-identify",
      "label": "One checkout per lane plus a per-lane committer identity, both enforced by hooks."
    },
    {
      "id": "identify-only",
      "label": "Keep the shared checkout; add per-lane committer identity so incidents stay attributable."
    },
    {
      "id": "accept",
      "label": "Keep advisory conventions and accept that these incidents recur and stay unattributable."
    }
  ],
  "context": [
    "Locks are advisory only: an integration lock was declared and then a 484-file commit, two pull-request merges, and two ticket deletions happened during it, because nothing in git, the hooks, or repowire can refuse a write on lock grounds.",
    "Every commit across every lane and both repositories is authored and committed as the same shared identity, so the 484-file sweep, both ticket deletions, and the unratified sampling decision could not be attributed from git at all.",
    "Four lanes shared one working tree and switched its branch under each other seven times in three hours, which is the direct cause of the scope drift, the vanished tickets, and two handoffs reporting stale test counts."
  ],
  "evidence": [
    {
      "label": "Scope and worktree audit receipt",
      "path": "docs/rse/specs/receipt-branch-scope-and-worktree-audit-2026-07-29.md",
      "sha256": "eaa6371fd4f87d6e74b19bdcae5f8b06a77f7744fbc44209f98789f27425abea"
    },
    {
      "label": "Unratified decision recorded during the same window",
      "path": "https://github.com/jakobtfaber/Faber2026-analysis/pull/201"
    }
  ],
  "effect": "Settles whether concurrent lanes get an enforced boundary or continue on conventions that demonstrably do not bind.",
  "recorder": {
    "path": "docs/rse/wayfinder/tickets/enforce-lane-isolation.md",
    "action": "Record the owner choice here, then implement only the selected option."
  },
  "priority": 10
}
```

## Proposed design, not implemented

Three layers, cheapest first. Each stands alone; the owner may take one, two, or
all three.

**1. Per-lane committer identity.** Every commit today reads
`Jakob Faber <jfaber@caltech.edu>`, so git attribution is worthless during an
incident. Give each lane a distinct committer whose author remains the owner, so
authorship for the record is unchanged while `%cn` identifies the writer:

```
git -c user.name="lane/<name>" -c user.email="lane+<name>@localhost" commit …
```

Enforce with a `pre-commit` hook that refuses a commit when the committer name
does not carry a `lane/` prefix. This is the smallest change with the largest
forensic return, and it would have named the author of all three unattributed
events. It does not prevent anything; it only makes events attributable.

**2. One checkout per lane.** The root cause is four lanes sharing one working
tree and one `HEAD`. Separate clones remove branch-switching races entirely.
The owner has previously preferred avoiding worktrees, so dedicated clones under
a lane directory are the better fit. Cost is disk; benefit is that a lane
physically cannot commit another lane's uncommitted work, which is what produced
the 491-file pull request.

**3. An enforcing lock.** For anything that must remain shared, an advisory
convention is insufficient. A lock is only real if a hook refuses the write:
a `pre-commit` and `pre-push` hook that reads a lock file recording holder,
scope, and expiry, and exits non-zero for any writer that is not the holder.
Expiry matters — an unbounded lock left by a crashed lane blocks everyone, which
is why the current convention gets ignored rather than obeyed.

**What none of this fixes.** Untracked work in a shared checkout is unprotected
by construction. Git tracks committed objects; a file that was never added has
no object, no reflog entry, and nothing for `fsck` to recover. Both destroyed
tickets were untracked, so no hook, lock, or identity check would have saved
either one, and it would be wrong to present this design as closing that gap.

The fix for that gap is the worktree pool, not a hook: if each lane holds its
own checkout, no other lane can reach its untracked files at all. Layer 1 makes
incidents attributable and layer 3 makes shared writes refusable, but only
physical separation protects work that has not been committed yet.
