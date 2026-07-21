# Choose the execution and credential boundary

- Type: `wayfinder:grilling` (HITL)
- Status: open
- Assignee: —
- Blocked by: [Establish the native Overleaf Git contract](overleaf-bridge-01-research-native-git-contract.md), [Choose the manuscript projection contract](overleaf-bridge-03-choose-projection-contract.md), [Choose the two-way reconciliation state machine](overleaf-bridge-04-choose-reconciliation-state-machine.md)
- Map: [Manuscript-only Overleaf bridge](../map-overleaf-manuscript-bridge.md)
- Triage: `ready-for-human`

## Question

Where should bridge runs execute, where should ephemeral Git state live, and
where should the Overleaf Git credential be held? Decide the boundary between
repo-local declarative tooling, a Mac-local authenticated runner, and any later
continuous-integration automation; the allowed trigger model; log redaction;
single-writer locking; and whether automation is admissible before a manual
pilot has produced complete receipts.
