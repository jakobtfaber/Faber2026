# Set the catalog crossmatch and quality contract

- Type: `wayfinder:task` (AFK)
- Status: resolved
- Assignee: —
- Blocked by: none
- Map: [Expanded foreground catalog repair](../map-expanded-foreground-catalog-repair.md)
- Delegation: [Standing delegated decision authority](../standing-delegation-2026-07-20.md)
- Triage: `resolved`

## Question

Which match rule, ambiguity rule, evidence snapshot, and catalog-native fields
are sufficient to make every GSC 2.4.2, ALLWISE, CatWISE2020, and unWISE row
auditable without a live network query?

## Acceptance decision

Sort by exact angular separation; never select response row zero implicitly.
Record search radius, selected separation, candidate count, second-nearest
separation, retrieval time, catalog identifier, release, query status, and a
snapshot hash. Mark a row ambiguous when the match is not unique under a tested
policy; never convert a query exception to `unmatched`. Preserve photometric
errors and native quality, contamination, artifact, and extension flags. Tests
run against committed normalized fixtures; refresh is an explicit network step.

## Resolution

Resolved 2026-07-22 under the
[standing delegated decision authority](../standing-delegation-2026-07-20.md),
after the blocking fail-close ticket was resolved. This resolution accepts the
contract already implemented by
[dsa110-FLITS PR #213](https://github.com/jakobtfaber/dsa110-FLITS/pull/213).
It does not change any catalog value, census verdict, budget flag, redshift, or
scientific trust state.

Acceptance evidence:

- This away-from-keyboard ticket was open at the delegation scope anchor,
  parent commit `33e9e1ce357073c78f6a4aaf7138b3e03e9c87da`; the 2026-07-22
  amendment permits resolution after ticket-scoped evidence and checks pass.
- PR #213 merged as `3e466c1a180fb169ad09845312348cf539b82632` on
  2026-07-21. Its Python 3.12, review, and security checks passed.
- Current pipeline `origin/main` is
  `f3c8d22a9088914e0179cfecf1ee4086777dc927` and contains that merge. The
  matching implementation and focused tests are unchanged since the merge.
- `select_match` sorts by exact angular separation and stable identifier,
  records the nearest and second-nearest separations and candidate count, marks
  tested near-ties ambiguous, and keeps `query_error` distinct from
  `unmatched`. The offline builder records radius, release, retrieval time,
  source identifier, response hash, photometric errors, and native quality,
  contamination, artifact, and extension fields from committed snapshots.
- In a clean isolated checkout at current pipeline `origin/main`,
  `conda run -n flits python -m pytest
  galaxies/foreground/test_expanded_catalog.py -q` passed: 13 tests.
- The offline rebuild reproduced tracked bytes with no diff. SHA-256:
  `482be53e3152030280949221d283f130e5545411f3ca8bb85fb6c9999e429ff5`
  for the expanded catalog and
  `6d7881c243613149b436de53e69b02d575041b84918f801a9c03a6d927329aef`
  for its build manifest.
