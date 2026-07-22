# Freeze the anonymous nine-sightline expanded-survey query corpus

- Type: `wayfinder:task` (AFK)
- Status: open — corrected corpus awaits independent review
- Assignee: —
- Blocked by: none
- Map: [Expanded foreground catalog repair](../map-expanded-foreground-catalog-repair.md)
- Delegation: not covered by the standing delegation; created after `main` commit `33e9e1ce3570`
- Triage: `review-required`

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

## Corrected corpus awaiting review

The previous closure used a sightline outside the authoritative Verdi and
protected roster naming JohndoeII. That mixed-roster closure is withdrawn. The same
producer now freezes 135 public-product/sightline cells for Zach, Whitney,
Oran, Isha, JohndoeII, Phineas, Hamilton, Chromatica, and Casey in
[`corpus-manifest.json`](../../specs/evidence/nine-sightline-anonymous-catalog-corpus-2026-07-22/corpus-manifest.json),
including separate eRASS1 main and primary-cluster products. The manifest binds
115,713 admitted records and 1,516 separate guard-only records, exact queries, releases, UTC retrieval times,
coverage decisions, native response bytes or canonical PS1 subsets, stable
identifiers, unrounded separations, native flags and uncertainties, complete
count/pagination evidence, and SHA-256 hashes. Its SHA-256 is
`14321fb328e372b8df0537d9a445dec2ab1376c4b258dabaf92116152eb023a5`.
The manifest binds a deterministic 618-member evidence bundle with SHA-256
`fed672e29c1d84ffd09f93de2487a1337fb722c02bd5dc718f7f97c1e593d32d`.

The terminal states are 37 `matched`, 31 `unmatched`, and 67
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
proof, 29 FITS files and hashes, and native-WCS positive-pixel replay. Whitney
and Casey are inside Swift coverage; JohndoeII and the other six are outside. Full
evidence and primary-source links are in
[`research-nine-sightline-anonymous-catalog-corpus-2026-07-22.md`](../../specs/research-nine-sightline-anonymous-catalog-corpus-2026-07-22.md).
No scientific or manuscript authority changed. The producer validator reports
zero errors, but ticket 14 remains open until independent review accepts the
corrected roster and evidence. Ticket 16 remains blocked until then.
