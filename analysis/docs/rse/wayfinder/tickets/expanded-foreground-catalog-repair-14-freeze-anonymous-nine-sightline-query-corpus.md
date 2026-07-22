# Freeze the anonymous nine-sightline expanded-survey query corpus

- Type: `wayfinder:task` (AFK)
- Status: resolved
- Assignee: —
- Blocked by: none
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

The producer froze 135 public-product/sightline cells in
[`corpus-manifest.json`](../../specs/evidence/nine-sightline-anonymous-catalog-corpus-2026-07-22/corpus-manifest.json),
including separate eRASS1 main and primary-cluster products. The manifest binds
109,117 admitted records and 1,474 separate guard-only records, exact queries, releases, UTC retrieval times,
coverage decisions, native response bytes or canonical PS1 subsets, stable
identifiers, unrounded separations, native flags and uncertainties, complete
count/pagination evidence, and SHA-256 hashes. Its SHA-256 is
`6ce903044e91f5eb0a1dd4660d85b202aeb8d74b2a7a4af97a247a72596b62c8`.
The manifest binds a deterministic 626-member evidence bundle with SHA-256
`1b53ea98abd5d232a793ed9b7bde8a876ea4fa44153ceba31608a014ecd09026`.

The terminal states are 37 `matched`, 32 `unmatched`, and 66
`outside_footprint`. Legacy Survey Data Release 9 northern g/r/z NEXP bytes,
XMM-Newton XSA polygons, Chandra CSC polygons, and Swift UKSSDC LSXPS native
exposure-map FITS files supply exact official coverage evidence.
The exact eROSITA-DE public boundary puts all nine positions outside both
public eRASS1 products. The cluster route fixes the complete official bulk
catalogue and inclusive 5-proper-Mpc Planck18 calculation with no angular
fallback.

Independent review reopened this ticket. Exact 15-arcminute admission and all
coverage repairs now pass. Swift evidence freezes raw API requests and
responses, the API endpoint and version, a conservative candidate-envelope
proof, 29 FITS files and hashes, and native-WCS positive-pixel replay. Whitney,
Wilhelm, and Casey are inside Swift coverage; the other six are outside. Full
evidence and primary-source links are in
[`research-nine-sightline-anonymous-catalog-corpus-2026-07-22.md`](../../specs/research-nine-sightline-anonymous-catalog-corpus-2026-07-22.md).
No scientific or manuscript authority changed. Ticket 16 can now perform the
separate independent replay.
