# Establish the native Overleaf Git contract

- Type: `wayfinder:research` (AFK)
- Status: resolved
- Assignee: —
- Blocked by: —
- Map: [Manuscript-only Overleaf bridge](../map-overleaf-manuscript-bridge.md)
- Triage: `ready-for-agent`
- Research branch: `research/overleaf-native-git-contract`
- Context: [Native Overleaf Git contract](../../research/research-overleaf-native-git-contract-2026-07-21.md)

## Question

What current, first-party Overleaf contracts govern a native Git bridge into
an existing project: authentication and token handling, remote and branch
semantics, editable-file and project limits, concurrent web-editor behavior,
history behavior, push rejection and conflict cases, and supported recovery?
Distinguish documented guarantees from observations or assumptions. Determine
which facts constrain a safe two-way bridge without testing a write against the
live project.

## Answer

Resolved 2026-07-21 from first-party Overleaf documentation; see the linked
research report for citations and guarantee-versus-inference boundaries.

The existing project is addressable through a token-authenticated native Git
remote with one hard-coded remote branch, `master`. Fetch or pull materializes
the current Overleaf state as translated Git history. The bridge may rely on
documented file limits and Overleaf History recovery, but not on ordinary
multi-branch Git semantics, one-commit-per-editor-change history, atomic
concurrent pushes, or preservation of comments and tracked changes across Git
writes.

Later decisions must therefore require expected-tip checks, a coordinated
write window, stable paths, hard size and unsupported-object preflight,
post-push tree verification, and an Overleaf History label plus downloaded
source snapshot before the first write. Those safeguards are conservative
bridge rules; Overleaf does not document them as a transaction guarantee.
