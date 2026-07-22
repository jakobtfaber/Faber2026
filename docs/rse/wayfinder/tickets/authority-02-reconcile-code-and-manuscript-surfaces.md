# Reconcile the code and manuscript truth surfaces

- Type: `wayfinder:research` (AFK)
- Status: resolved
- Assignee: —
- Blocked by: —
- Map: [Project authority and custody](../map-project-authority-and-custody.md)
- Triage: `ready-for-agent`

## Question

What is the current, evidence-backed relationship among GitHub's default
branch, the canonical Mac checkout, the `pipeline/` submodule and its upstream,
the independent Overleaf checkout, `.worktrees/review-prose-89`, and every
Faber2026 or FLITS checkout listed in the estate audit? For each surface record
repository identity, branch or detached commit, upstream divergence, dirt,
submodule pin, unique commits/files, and concurrent ownership. Research only;
do not merge, pull, push, reset, stage, or remove anything.

## Answer

Resolved by
[`Research: Code and manuscript authority surfaces`](../../specs/research/research-authority-code-manuscript-surfaces-2026-07-20.md).

At the observation time, live GitHub `main`, the canonical checkout commit, and
its local `origin/main` agreed at `179ed2bf`; the canonical working tree still
contained broad concurrent dirt. The manuscript pin and clean detached
submodule agreed at `c6111390`, while the live FLITS fork was one bounded
analysis-only commit ahead. The standalone FLITS clone was stale and dirty.

The independent Overleaf checkout is clean but history-orphaned: its commit is
absent from current GitHub, it has no merge base with canonical history, and a
tree comparison found 89 changed common paths plus 57 Overleaf-only paths. It
must be reconciled as a separate content source, never blindly merged or
treated as merely behind. Unique commits or dirt also remain in the JointTF,
quarantine, scintillation, archive-diagnostics, review-prose, science-gates,
and fitting lanes. The two contributor-rewrite repositories have different
commit identities but byte-identical main trees, confirming rewrite staging
rather than independent manuscript content.
