# Independently replay the completed nine-sightline query corpus

- Type: `wayfinder:research` (AFK)
- Status: open
- Assignee: unassigned
- Blocked by: [Freeze the anonymous nine-sightline expanded-survey query corpus](expanded-foreground-catalog-repair-14-freeze-anonymous-nine-sightline-query-corpus.md), [Freeze protected WISE--PS1--STRM and UNIONS/CFIS evidence](expanded-foreground-catalog-repair-15-freeze-protected-nine-sightline-query-evidence.md)
- Map: [Expanded foreground catalog repair](../map-expanded-foreground-catalog-repair.md)
- Delegation: not covered by the standing delegation; created after `main` commit `33e9e1ce3570`
- Triage: `blocked`

## Question

Does a separate implementation reproduce the completed corpus's coverage,
deterministic candidate selection, angular separations, identity and duplicate
handling, redshift comparisons, stored verdict inputs, and budget flags?

The replay must not import the producing selection or verdict functions.
Spectroscopic redshifts outrank photometric estimates; extrapolated or
materially disagreeing photometric estimates remain inconclusive. Every
identity, coverage, classification, redshift, or duplicate conflict must be
named and routed to a separate owner-approved adjudication; no stored or
manuscript-facing authority changes in this ticket.
