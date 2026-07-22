# Freeze the anonymous nine-sightline expanded-survey query corpus

- Type: `wayfinder:task` (AFK)
- Status: open
- Assignee: Codex (anonymous-corpus agent)
- Blocked by: [Set the nine-sightline search-region and candidate-selection contract](expanded-foreground-catalog-repair-13-set-nine-sightline-search-contract.md)
- Map: [Expanded foreground catalog repair](../map-expanded-foreground-catalog-repair.md)
- Delegation: not covered by the standing delegation; created after `main` commit `33e9e1ce3570`
- Triage: `ready-for-agent`

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

## Work log

- 2026-07-22: Added a fail-closed 126-cell manifest validator, live anonymous
  service preflight, regression tests, and the public PS1--STRM bulk extraction
  route. See
  [the execution checkpoint](../../specs/research-nine-sightline-anonymous-catalog-corpus-2026-07-22.md).
- Keep this ticket open. Service reachability is proven, but a preflight is not
  the required fully paginated nine-sightline corpus. Closure still requires
  all service/sightline query cells and exposure-first X-ray evidence.
- No owner credential or decision is required. The official PS1--STRM shard is
  anonymously downloadable; authenticated MAST CasJobs is optional only.
