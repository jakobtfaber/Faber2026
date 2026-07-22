# Expand and independently replay catalog coverage for nine host-redshift sightlines

- Type: `wayfinder:research` (AFK)
- Status: open
- Assignee: unassigned
- Blocked by: none
- Map: [Expanded foreground catalog repair](../map-expanded-foreground-catalog-repair.md)
- Delegation: not covered by the standing delegation; created after `main` commit `33e9e1ce3570`
- Triage: `ready-for-agent`

## Question

Can the nine sightlines with authoritative host redshifts be searched and
cross-matched uniformly across the expanded survey set, with frozen
source-level evidence and a genuinely independent replay, and which resulting
identity, coverage, classification, or redshift conflicts require a separate
owner-approved adjudication?

The pass covers all 50 current registry rows on those nine sightlines. Search
catalogs inspect the full recorded sightline region; classification catalogs
cross-match the resulting candidate list.

Required search and redshift sources are DESI DR1, Sloan Digital Sky Survey
Data Release 19, LAMOST Data Release 11, Legacy Survey photometric-redshift
products, PS1--STRM, WISE--PS1--STRM, and coverage-aware J-PLUS, J-PAS, and
UNIONS/CFIS queries. NED and SIMBAD are provenance-discovery services, not
independent redshift authorities.

Required classification enrichments are Gaia Data Release 3, LoTSS Data
Release 3, VLASS, and eROSITA eRASS1. XMM-Newton, Chandra, and Swift are queried
only where an exposure covers the candidate. NVSS, WENSS, TGSS, GALEX, and
2MASS are fallback evidence, not mandatory duplicate queries where a deeper
catalog already resolves the question. The BASS bulk classifier is excluded
unless a source-level service becomes available.

Every query must freeze its release, query or cone definition, retrieval time,
source identifier, coordinates, match separation, native quality and
uncertainty fields, coverage result, response bytes or normalized snapshot,
and SHA-256 hash. Normalized states must distinguish `matched`, `unmatched`,
`outside_footprint`, `ambiguous`, `access_denied`, and `query_error`. Shared
WISE identifiers across multiple optical sources are explicitly ambiguous.

The independent replay must use a separate calculation path to reproduce
coverage, deterministic candidate selection, separations, duplicate handling,
redshift comparisons, stored verdict inputs, and budget flags. Spectroscopic
redshifts outrank photometric estimates; extrapolated or materially disagreeing
photometric estimates remain inconclusive. Results may flag conflicts but may
not silently change an adopted redshift, candidate verdict, duplicate
disposition, budget eligibility, scientific-trust state, or Figure 3 status.
