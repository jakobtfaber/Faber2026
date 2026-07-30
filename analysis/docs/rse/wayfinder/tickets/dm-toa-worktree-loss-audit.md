# Close the dm-toa worktree loss audit

- Type: `wayfinder:task` (HITL)
- Status: open
- Assignee: manuscript owner
- Blocked by: none
- Map: [ApJ submission](../map-apj-submission.md)
- GitHub: [Faber2026-analysis #167](https://github.com/jakobtfaber/Faber2026-analysis/pull/167)

## Current finding

The generated products were preserved before retirement, and the phase-B
configuration files landed under a new path. The only unresolved item is the
reported 1,918 uncommitted inserted lines across nine tracked files. No snapshot
of those exact bytes has been found.

## Owner decision card

```json
{
  "id": "dm-toa-worktree-loss",
  "kind": "scientific",
  "title": "Close dm-toa worktree loss audit",
  "decision": "Accept the nine unrecovered tracked-file modifications as superseded, or keep recovery open?",
  "recommended": {
    "choice": "require-accounting",
    "reason": "Generated products and phase-B configurations are accounted for, but the exact bytes of 1918 reported uncommitted insertions remain unavailable."
  },
  "choices": [
    {
      "id": "require-accounting",
      "label": "Keep recovery open until the nine tracked-file modifications are accounted for."
    },
    {
      "id": "accept-superseded",
      "label": "Accept the remaining uncertainty and close the audit."
    }
  ],
  "context": [
    "The generated dm-toa-geometry products were preserved with checksums before retirement.",
    "The 13 phase-b configuration filenames are tracked in origin/main at analysis-configs/absolute-dm/phase-b/.",
    "A targeted search found no snapshot of 1918 reported uncommitted insertions across nine tracked one-event workflow files."
  ],
  "evidence": [
    {
      "label": "Scope and worktree audit receipt",
      "path": "docs/rse/specs/receipt-branch-scope-and-worktree-audit-2026-07-29.md",
      "sha256": "eaa6371fd4f87d6e74b19bdcae5f8b06a77f7744fbc44209f98789f27425abea"
    },
    {
      "label": "Pull request 167, which landed the phase-b controls",
      "path": "https://github.com/jakobtfaber/Faber2026-analysis/pull/167"
    }
  ],
  "effect": "Settles only the remaining uncertainty around nine unrecovered tracked-file modifications.",
  "recorder": {
    "path": "docs/rse/wayfinder/tickets/dm-toa-worktree-loss-audit.md",
    "action": "Record the owner choice here, with the accounting or the explicit acceptance that closes it."
  },
  "priority": 15
}
```

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
