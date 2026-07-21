# Choose the manuscript projection contract

- Type: `wayfinder:grilling` (HITL)
- Status: open
- Assignee: —
- Blocked by: [Inventory the live manuscript projection](overleaf-bridge-02-inventory-live-projection.md)
- Map: [Manuscript-only Overleaf bridge](../map-overleaf-manuscript-bridge.md)
- Triage: `ready-for-human`

## Question

Given the live inventory, what declarative contract determines the exact files
that may cross the bridge? Decide how the `main.tex` dependency closure is
computed, which explicit inclusions and exclusions are permitted, how generated
tables and approved figure outputs retain provenance, how missing and orphaned
dependencies fail, and what size margin below Overleaf's limits is required.
The contract must be reviewable without running a sync and must not admit whole
research directories by convenience.
