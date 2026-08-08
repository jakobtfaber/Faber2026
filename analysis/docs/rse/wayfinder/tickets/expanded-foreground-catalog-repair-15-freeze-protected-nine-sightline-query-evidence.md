# Freeze protected WISE--PS1--STRM and UNIONS/CFIS evidence

- Type: `wayfinder:task` (HITL)
- Status: resolved
- Assignee: —
- Blocked by: none
- Map: [Expanded foreground catalog repair](../map-expanded-foreground-catalog-repair.md)
- Delegation: not covered by the standing delegation; created after `main` commit `33e9e1ce3570`
- Triage: `resolved`

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

## Resolution

Resolved 2026-07-22 after the owner supplied the MAST CasJobs credential
through macOS Keychain. The password was never printed, logged, committed, or
placed in an environment variable. A live authentication handshake succeeded
for account `jfaber` before acquisition.

The protected MAST corpus is frozen at
[`protected-nine-sightline-2026-07-22`](../../specs/evidence/protected-nine-sightline-2026-07-22/manifest.json):

- context `HLSP_WISE_PS1_STRM`, table `catalogRecordRowStore`, release
  WISE--PS1--STRM v1, DOI `10.17909/wf64-kq10`;
- nine separate uncapped CasJobs batch materializations and CSV extraction
  jobs, with exact SQL, job identifiers, server times, response bytes, and
  SHA-256 hashes;
- 26,540 native response rows with all 210 catalog columns; a documented
  one-arcsecond guard rectangle proves containment of every inclusive
  15-arcminute cone;
- 20,788 rows inside the exact spherical cones and 5,752 guard-only rows,
  recorded without discarding the raw response;
- 242 WISE identifiers shared by multiple optical objects inside the exact
  cones, all explicitly retained as `ambiguous` rather than merged.

The authenticated CADC result is frozen at
[`cadc-cfis-access-2026-07-22`](../../specs/evidence/cadc-cfis-access-2026-07-22/manifest.json).
The certificate identity completed a live read-only VOSpace listing, but the
same identity could not see `cfht.cfiscat`. The exact ADQL request and response
are hash-bound as `access_denied`, consistent with the official CFIS access
documentation. This is not `unmatched` and does not require fabricating empty
source rows.

Ten focused producer and evidence tests pass. The later replay ticket must
independently recompute exact-cone membership and ambiguity from the frozen raw
bytes; it must not import these producer functions. No redshift, verdict,
duplicate disposition, budget flag, trust state, or Figure 3 artifact changed.
