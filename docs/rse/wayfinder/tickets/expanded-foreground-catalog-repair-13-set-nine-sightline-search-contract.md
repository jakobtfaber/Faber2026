# Set the nine-sightline search-region and candidate-selection contract

- Type: `wayfinder:grilling` (HITL)
- Status: open
- Assignee: unassigned
- Blocked by: none
- Map: [Expanded foreground catalog repair](../map-expanded-foreground-catalog-repair.md)
- Delegation: not covered by the standing delegation; created after `main` commit `33e9e1ce3570`
- Triage: `ready-for-human`

## Question

What exact sky region and deterministic candidate-admission rule should govern
the expanded nine-sightline replay?

The frozen census records recovered candidates but not the original galaxy
discovery-cone aperture. Decide the center and angular or proper-radius rule for
each sightline; whether galaxy and cluster searches use different regions; the
catalog fields and quality cuts that create a candidate; and the identity,
ambiguity, and duplicate rules applied before classification enrichments.

This decision defines a new reproducible audit search. It does not retroactively
claim completeness for the frozen census or authorize changing any adopted
redshift, verdict, budget flag, trust state, or Figure 3 status.
