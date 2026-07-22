# Adjudicate census host redshifts against the approved Verdi table

- Type: `wayfinder:grilling` (HITL)
- Status: open
- Assignee: unassigned
- Blocked by: [Repeat source-level redshift verification](expanded-foreground-catalog-repair-09-repeat-redshift-source-verification.md)
- Map: [Expanded foreground catalog repair](../map-expanded-foreground-catalog-repair.md)
- Delegation: not covered by the standing delegation; created after `main` commit `33e9e1ce3570`
- Triage: `blocked`

## Question

After independent replay, which local host-redshift values and FRB identifiers
should change to match the owner-approved `verdi2025.tex` table?

At minimum, adjudicate Wilhelm's local `0.51` versus the approved blank cell,
JohndoeII's local blank versus the approved `0.5535`, and the Freya, Hamilton,
Mahi, and Chromatica suffix differences. Record every adopted change at its
source; do not alter candidate verdicts, budget flags, or Figure 3 in this
decision ticket.
