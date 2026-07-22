# Adjudicate census host redshifts against the approved Verdi table

- Type: `wayfinder:grilling` (HITL)
- Status: resolved
- Assignee: Codex
- Blocked by: none
- Map: [Expanded foreground catalog repair](../map-expanded-foreground-catalog-repair.md)
- Delegation: not covered by the standing delegation; created after `main` commit `33e9e1ce3570`
- Triage: `ready-for-human`

## Question

After independent replay, which local host-redshift values and FRB identifiers
should change to match the owner-approved `verdi2025.tex` table?

At minimum, adjudicate Wilhelm's local `0.51` versus the approved blank cell,
JohndoeII's local blank versus the approved `0.5535`, and the Freya, Hamilton,
Mahi, and Chromatica suffix differences. Record every adopted change at its
source; do not alter candidate verdicts, budget flags, or Figure 3 in this
decision ticket.

Ticket 09's independent replay is complete and fail-closed. The current
decision packet is narrower than the original minimum list: production already
leaves Wilhelm blank and contains no JohndoeII registry candidate. Adjudicate
Whitney `0.479` versus Law et al. (2024) `0.477958`, plus the Freya, Hamilton,
and Chromatica identifier aliases. See
[`research-foreground-source-verification-2026-07-22.md`](../../specs/research-foreground-source-verification-2026-07-22.md).

## Resolution

Retain Whitney's production host redshift `0.479`. Connor et al. (2025)'s
author-released baryon-census table independently lists Whitney / FRB 20220310F
at spectroscopic redshift `0.479`; the frozen row and source-table hash are in
[`connor2025-whitney-host-redshift-2026-07-22`](../../specs/evidence/connor2025-whitney-host-redshift-2026-07-22/).
Law et al. (2024)'s higher-precision `0.477958` remains source evidence but is
not adopted by the census.

Adopt the owner-approved Verdi source-event identifiers:

- Freya: `FRB 20230325C`
- Hamilton: `FRB 20230913G`
- Chromatica: `FRB 20240203D`

The identifier correction is implemented at the pipeline's canonical name
resolver and production census registry in dsa110-FLITS PR #225. Frozen
discovery inputs retain their historical local `A` suffixes. No candidate
verdict, budget flag, or Figure 3 artifact changed.
