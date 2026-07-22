# Freeze protected WISE--PS1--STRM and UNIONS/CFIS evidence

- Type: `wayfinder:task` (HITL)
- Status: open
- Assignee: unassigned
- Blocked by: [Set the nine-sightline search-region and candidate-selection contract](expanded-foreground-catalog-repair-13-set-nine-sightline-search-contract.md)
- Map: [Expanded foreground catalog repair](../map-expanded-foreground-catalog-repair.md)
- Delegation: not covered by the standing delegation; created after `main` commit `33e9e1ce3570`
- Triage: `ready-for-human`

## Question

Can the manuscript owner run the authenticated MAST CasJobs and CADC queries
needed for WISE--PS1--STRM and UNIONS/CFIS, then export source-level responses
for the approved nine-sightline search regions?

Record the authenticated service identity without exposing credentials, job or
query identifier, release and table, exact query, retrieval time, coverage,
native rows and quality fields, canonical response bytes, and SHA-256. Shared
WISE identifiers across multiple optical objects remain `ambiguous`. If the
CADC identity still lacks `CFIS-read`, freeze a current `access_denied` receipt
rather than treating it as `unmatched`.

The exports are evidence only. They do not authorize a redshift, verdict,
duplicate, budget, trust, or Figure 3 change.
