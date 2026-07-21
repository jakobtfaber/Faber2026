# Set the catalog crossmatch and quality contract

- Type: `wayfinder:task` (AFK)
- Status: resolved
- Assignee: Codex
- Blocked by: [Fail-close the invalid validation](expanded-foreground-catalog-repair-01-fail-close-validation.md)
- Map: [Expanded foreground catalog repair](../map-expanded-foreground-catalog-repair.md)
- Delegation: [Standing delegated decision authority](../standing-delegation-2026-07-20.md)
- Triage: `ready-for-agent`

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

Implemented in dsa110-FLITS PR #213, merge
`3e466c1a180fb169ad09845312348cf539b82632`. Independent replay reproduced all
208 selections, identifiers, ambiguity states, candidate counts, and second
separations with zero differences.
