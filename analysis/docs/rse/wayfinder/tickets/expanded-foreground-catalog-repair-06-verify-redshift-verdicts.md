# Independently verify foreground redshifts and verdicts

- Type: `wayfinder:research` (AFK)
- Status: resolved
- Assignee: unassigned
- Blocked by: none
- Map: [Expanded foreground catalog repair](../map-expanded-foreground-catalog-repair.md)
- Triage: `ready-for-agent`

## Question

Do the cited source data independently support every adopted host and candidate
redshift, uncertainty, foreground verdict, and budget-eligibility flag?

## Acceptance decision

Check all 52 registry rows against their cited spectra, photometric-redshift
products, catalog identifiers, and host redshifts. Recompute the verdict from the
documented uncertainty rule; verify duplicate handling and budget eligibility.
Record source, release, identifier, retrieval date, value, uncertainty, redshift
kind, recomputed verdict, stored verdict, and disposition per row. A match passes;
an unexplained difference blocks Figure 3. Changing a stored value or verdict
requires a separate evidence-backed adjudication record and owner approval.

## Resolution

Resolved 2026-07-20 from
[Independent foreground redshift and verdict audit](../../specs/research-expanded-foreground-redshift-verdict-audit.md)
(`research/foreground-redshift-verdicts`, commit `6e6a986b`).

The answer is **no**. Independent calculation reproduces all 52 verdicts, all
52 row-level budget flags, and all seven declared duplicate relationships, but
0/52 rows has a complete checked-in source chain for both host and candidate
redshift. The missing Verdi host table blocks every row; candidate-side gaps
include absent Legacy Survey and DESI identifiers/query metadata, incomplete
STRM retrieval provenance, missing NED uncertainty/reference metadata, and
incomplete extension source rows. Keep the stored values labeled
`legacy-adjudicated, provenance incomplete`; do not change them from this audit.
Figure 3 remains blocked.

The finding graduates three explicit follow-ups:

- [Freeze authoritative host-redshift evidence](expanded-foreground-catalog-repair-07-freeze-host-redshift-provenance.md)
- [Freeze candidate-redshift source evidence](expanded-foreground-catalog-repair-08-freeze-candidate-redshift-provenance.md)
- [Repeat source-level redshift verification](expanded-foreground-catalog-repair-09-repeat-redshift-source-verification.md)
