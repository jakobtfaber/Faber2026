# Choose the two-way reconciliation state machine

- Type: `wayfinder:grilling` (HITL)
- Status: open
- Assignee: —
- Blocked by: [Establish the native Overleaf Git contract](overleaf-bridge-01-research-native-git-contract.md), [Inventory the live manuscript projection](overleaf-bridge-02-inventory-live-projection.md)
- Map: [Manuscript-only Overleaf bridge](../map-overleaf-manuscript-bridge.md)
- Triage: `ready-for-human`

## Question

What exact states and transitions safely carry collaborator edits from
Overleaf into a reviewed GitHub branch and the merged manuscript projection
back to Overleaf? Decide snapshot identities, edit-freeze boundaries,
three-way comparison inputs, conflict and concurrent-edit behavior, deletion
semantics, stale-snapshot rejection, idempotence, and the receipts that prove
which bytes moved in each direction. GitHub `main` must remain authoritative;
automatic conflict resolution is not allowed.
