# Establish the native Overleaf Git contract

- Type: `wayfinder:research` (AFK)
- Status: open
- Assignee: —
- Blocked by: —
- Map: [Manuscript-only Overleaf bridge](../map-overleaf-manuscript-bridge.md)
- Triage: `ready-for-agent`
- Research branch: `research/overleaf-native-git-contract`
- Planned artifact:
  `docs/rse/research/research-overleaf-native-git-contract-2026-07-21.md`

## Question

What current, first-party Overleaf contracts govern a native Git bridge into
an existing project: authentication and token handling, remote and branch
semantics, editable-file and project limits, concurrent web-editor behavior,
history behavior, push rejection and conflict cases, and supported recovery?
Distinguish documented guarantees from observations or assumptions. Determine
which facts constrain a safe two-way bridge without testing a write against the
live project.
