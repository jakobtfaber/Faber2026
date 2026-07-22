# Independently replay the completed nine-sightline query corpus

- Type: `wayfinder:research` (AFK)
- Status: resolved
- Assignee: unassigned
- Blocked by: none
- Map: [Expanded foreground catalog repair](../map-expanded-foreground-catalog-repair.md)
- Delegation: not covered by the standing delegation; created after `main` commit `33e9e1ce3570`
- Triage: `resolved`

## Question

Does a separate implementation reproduce the completed corpus's coverage,
deterministic candidate selection, angular separations, identity and duplicate
handling, redshift comparisons, stored verdict inputs, and budget flags?

The replay must not import the producing selection or verdict functions.
Spectroscopic redshifts outrank photometric estimates; extrapolated or
materially disagreeing photometric estimates remain inconclusive. Every
identity, coverage, classification, redshift, or duplicate conflict must be
named and routed to a separate owner-approved adjudication; no stored or
manuscript-facing authority changes in this ticket.

## Independent replay result

The 2026-07-22 clean-room replay reproduced all frozen bytes, exact-cone row
counts, coordinate-derived separations, coverage states, protected SQL bounds,
and shared-WISE ambiguity. Both corrected corpora contain the same nine
authoritative sightlines. The anonymous lowercase `johndoeii` label is a case
alias of the protected/Verdi `johndoeII`, not a different identity.

Evidence and commands are frozen in
[`research-nine-sightline-independent-corpus-replay-2026-07-22.md`](../../specs/research-nine-sightline-independent-corpus-replay-2026-07-22.md).
The corpus layers pass. At pipeline commit `f3c8d22`, all 52 candidate
provenance identities match the 52 registry objects; all 49 rows with finite
host redshift independently reproduce their stored verdict and budget flag;
all seven duplicate separations reproduce. Wilhelm remains a real foreground
object but is excluded from finite-host arithmetic because its host redshift is
blank. JohndoeII correctly has no selected foreground candidate. The full
replay exits zero. No redshift, identity,
duplicate disposition, verdict, budget flag, trust state, or Figure 3 artifact
changed.
