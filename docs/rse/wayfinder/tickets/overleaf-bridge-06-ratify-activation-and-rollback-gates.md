# Ratify the first activation and rollback gates

- Type: `wayfinder:grilling` (HITL)
- Status: open
- Assignee: —
- Blocked by: [Choose the manuscript projection contract](overleaf-bridge-03-choose-projection-contract.md), [Choose the two-way reconciliation state machine](overleaf-bridge-04-choose-reconciliation-state-machine.md), [Choose the execution and credential boundary](overleaf-bridge-05-choose-execution-and-credential-boundary.md)
- Map: [Manuscript-only Overleaf bridge](../map-overleaf-manuscript-bridge.md)
- Triage: `ready-for-human`

## Question

What evidence and owner gates must pass before the first bridge write, and what
exact rollback remains available after it? Decide snapshot preservation,
Overleaf-only path disposition, dry-run review, projected size checks,
unexpected-delete rejection, manuscript compile and PDF comparison, GitHub
pull-request receipt, Overleaf commit receipt, concurrent-edit invalidation,
and the stop conditions that leave the existing project unchanged.
