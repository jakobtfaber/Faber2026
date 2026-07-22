# Freeze the anonymous nine-sightline expanded-survey query corpus

- Type: `wayfinder:task` (AFK)
- Status: resolved
- Assignee: Codex (anonymous-corpus agent)
- Blocked by: [Set the nine-sightline search-region and candidate-selection contract](expanded-foreground-catalog-repair-13-set-nine-sightline-search-contract.md)
- Map: [Expanded foreground catalog repair](../map-expanded-foreground-catalog-repair.md)
- Delegation: not covered by the standing delegation; created after `main` commit `33e9e1ce3570`
- Triage: `resolved`

## Question

Can the owner-approved search contract be executed against every anonymously
available required service, with raw or canonical normalized responses frozen
for all nine sightlines and every resulting candidate?

Cover DESI Data Release 1, Sloan Digital Sky Survey Data Release 19, LAMOST
Data Release 11, Legacy Survey photometric-redshift products, PS1--STRM,
coverage-aware J-PLUS and J-PAS, Gaia Data Release 3, LoTSS Data Release 3,
VLASS, and eROSITA eRASS1. Query XMM-Newton, Chandra, and Swift only after an
exposure-coverage check. Use NED and SIMBAD only for provenance discovery.

Every record must retain release, exact query or cone, retrieval time, source
identifier, coordinates, separation, native quality and uncertainty fields,
coverage result, response bytes or canonical snapshot, SHA-256, and one of
`matched`, `unmatched`, `outside_footprint`, `ambiguous`, `access_denied`, or
`query_error`. Do not change scientific or manuscript authority fields.

## Resolution

Resolved 2026-07-22. The producer froze 135 public-product/sightline cells in
[`corpus-manifest.json`](../../specs/evidence/nine-sightline-anonymous-catalog-corpus-2026-07-22/corpus-manifest.json),
including separate eRASS1 main and primary-cluster products. The manifest binds
110,591 normalized records, exact queries, releases, UTC retrieval times,
coverage decisions, native response bytes or canonical PS1 subsets, stable
identifiers, unrounded separations, native flags and uncertainties, complete
count/pagination evidence, and SHA-256 hashes. Its SHA-256 is
`f4eb168580c92d858ba4bebf80146f4bd5ef67f924d9564f283027cb3e227839`.

The terminal states are 37 `matched`, 41 `unmatched`, and 57
`outside_footprint`; none is access-denied, query-error, truncated, or
overflowed. XMM-Newton, Chandra, and Swift source queries were coverage-gated.
The exact eROSITA-DE public boundary puts all nine positions outside both
public eRASS1 products. The cluster route fixes the complete official bulk
catalogue and inclusive 5-proper-Mpc Planck18 calculation with no angular
fallback.

Focused producer tests pass (`23 passed`), and the byte-level validator passes
all 135 cells. Full evidence and primary-source links are in
[`research-nine-sightline-anonymous-catalog-corpus-2026-07-22.md`](../../specs/research-nine-sightline-anonymous-catalog-corpus-2026-07-22.md).
No scientific or manuscript authority changed. Ticket 16 remains the separate
independent replay gate.
