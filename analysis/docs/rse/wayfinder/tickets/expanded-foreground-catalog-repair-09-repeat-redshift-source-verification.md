# Repeat source-level redshift verification

- Type: `wayfinder:research` (AFK)
- Status: resolved
- Assignee: Codex (independent source-verification agent)
- Blocked by: [Source authoritative host redshifts for Zach and Whitney](expanded-foreground-catalog-repair-18-source-zach-whitney-host-redshifts.md), [Independently replay the completed nine-sightline query corpus](expanded-foreground-catalog-repair-16-independently-replay-nine-sightline-query-corpus.md)
- Map: [Expanded foreground catalog repair](../map-expanded-foreground-catalog-repair.md)
- Delegation: [Standing delegated decision authority](../standing-delegation-2026-07-20.md)
- Triage: `resolved`

## Question

After source-bearing host and candidate evidence is frozen, do all 52 redshifts,
uncertainties, verdicts, duplicate dispositions, and budget flags pass an
independent replay, and which differences require owner-approved adjudication?

## Resolution

Resolved 2026-07-22 with a **fail-closed** answer. The independent offline
verifier replayed all 52 production rows at pipeline commit `f3c8d22` without
importing producer or adjudication code. All 52 verdicts, all 52 budget flags,
and all seven duplicate mappings reproduce. Only 34 rows have complete current
host-plus-candidate source verification; 18 rows retain at least one source
discrepancy.

The discrepancies are: seven Whitney rows use host redshift `0.479` instead of
Law et al. (2024) `0.477958`; seven Freya, Hamilton, and Chromatica rows use
local-versus-Verdi FRB identifier aliases not yet adjudicated; four
redshiftless PS1-STRM rows omit their real source identities from the candidate
provenance ledger; and two manual extension rows lack authoritative frozen
source rows. Some categories overlap. Using the available authoritative host
values changes no current verdict or budget flag.

The report, row-level dispositions, hashes, verifier, and tests are in
[`research-foreground-source-verification-2026-07-22.md`](../../specs/research-foreground-source-verification-2026-07-22.md).
No scientific authority changed. Route host value and identifier differences
to ticket 19; repair the six candidate identity chains separately. Figure 3
remains blocked.
