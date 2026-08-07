# Obtain the authoritative host-redshift ledger

- Type: `wayfinder:task` (HITL)
- Status: resolved
- Assignee: Codex
- Blocked by: none
- Map: [Expanded foreground catalog repair](../map-expanded-foreground-catalog-repair.md)
- Delegation: not covered by the standing delegation; created after `main` commit `33e9e1ce3570`
- Triage: `resolved`

## Question

Can the manuscript owner or Verdi source owner identify the authoritative draft
or released table and provide one row per Faber2026 sightline with the host
identifier, FRB identifier, redshift, row-level uncertainty, measurement kind,
bibliographic source, stable upstream row identifier, and release or retrieval
date?

The response must explicitly adjudicate:

- the current-versus-older draft differences for Wilhelm and Hamilton;
- the current `0.5535` value versus the blank local value for JohndoeII;
- the absent Zach and Whitney rows; and
- the suffix mappings for Freya, Hamilton, Mahi, and Chromatica.

Do not update the census from an email or prose answer alone. Freeze the
authoritative table or a source-owner-approved minimal extract and hash it.

## Resolution

Resolved 2026-07-22 by the manuscript owner's live approval: the burst-redshift
table entries in the supplied current named draft, `verdi2025.tex`, are the
authoritative Verdi redshift source. The previously frozen archive and minimal
extract preserve the approved bytes under
[`verdi-host-redshifts-2026-07-22/`](../../specs/evidence/verdi-host-redshifts-2026-07-22/);
the archive SHA-256 is
`c1e14983531711aa47f214f0c010cdba550f4bf26b1ac132da96280d748a7346`
and the approved current member SHA-256 is
`ea094a20d5cac53d79fde24e696c5c4aca967d82067e3dc7f23c8a6cdb640e90`.

Authority applies to the entries actually present in `verdi2025.tex`. The older
`test.tex` remains a superseded comparison artifact and is not authoritative.
A blank table cell remains no authoritative redshift; approval does not restore
Wilhelm's older `0.5100` value or invent values for absent rows. The paper-wide
`<0.4%` statement remains a bound, not a row-level uncertainty. No host-galaxy
identifier is inferred from the FRB identifier.

This decision does not change the census. Zach and Whitney remain absent from
the approved Verdi table and require
[Source authoritative host redshifts for Zach and Whitney](expanded-foreground-catalog-repair-18-source-zach-whitney-host-redshifts.md).
After the independent replay, any local-versus-Verdi numerical or identifier
difference routes to
[Adjudicate census host redshifts against the approved Verdi table](expanded-foreground-catalog-repair-19-adjudicate-host-redshift-differences.md).
