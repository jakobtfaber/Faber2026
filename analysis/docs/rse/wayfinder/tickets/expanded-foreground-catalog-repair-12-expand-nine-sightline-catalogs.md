# Expand and independently replay catalog coverage for nine host-redshift sightlines

- Type: `wayfinder:research` (AFK)
- Status: resolved
- Assignee: Codex
- Blocked by: none
- Map: [Expanded foreground catalog repair](../map-expanded-foreground-catalog-repair.md)
- Delegation: not covered by the standing delegation; created after `main` commit `33e9e1ce3570`
- Triage: `resolved`

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

## Resolution

Resolved 2026-07-21 by
[Nine-sightline catalog coverage replay](../../specs/research-nine-sightline-catalog-coverage-replay-2026-07-21.md).

The answer is **no at the full ticket scope**. The current 50 finite-host rows
can be replayed internally, but the required uniform expanded-survey search and
independent selection replay cannot yet be executed.

What reproduced:

- 50/50 stored verdicts: 30 confirmed, 13 inconclusive, 7 refuted.
- 50/50 budget flags; 15 row-level flags are true.
- All seven duplicate-pair separations, stored redshifts, and verdicts.
- All 50 rows in the existing GSC 2.4.2, ALLWISE, CatWISE2020, and unWISE
  snapshots.
- A diagnostic, non-independent live adapter run reproduced all 44 adopted
  stable source identifiers and selected-row hashes. Seven cluster-cone
  response hashes drifted while the selected sources remained unchanged.

What blocks the full answer:

- The frozen census never recorded its original discovery cone or aperture, so
  “full recorded sightline region” is not an executable uniform query contract.
- No frozen nine-sightline response corpus exists for the required DESI,
  Sloan Digital Sky Survey, LAMOST, Legacy, STRM, J-PLUS, J-PAS, CFIS, Gaia,
  radio, or X-ray survey matrix.
- The current duplicate table is owner-adjudicated and lacks the source-row
  evidence needed for independent duplicate discovery.
- Authoritative host-redshift source rows remain a separate open gate.

No adopted redshift, verdict, duplicate mapping, budget flag, trust state, or
Figure 3 artifact changed. Scientific trust and Figure 3 promotion remain
closed.

The route continues through
[Set the nine-sightline search-region and candidate-selection contract](expanded-foreground-catalog-repair-13-set-nine-sightline-search-contract.md),
[Freeze the anonymous nine-sightline expanded-survey query corpus](expanded-foreground-catalog-repair-14-freeze-anonymous-nine-sightline-query-corpus.md),
[Freeze protected WISE--PS1--STRM and UNIONS/CFIS evidence](expanded-foreground-catalog-repair-15-freeze-protected-nine-sightline-query-evidence.md),
and
[Independently replay the completed nine-sightline query corpus](expanded-foreground-catalog-repair-16-independently-replay-nine-sightline-query-corpus.md).
