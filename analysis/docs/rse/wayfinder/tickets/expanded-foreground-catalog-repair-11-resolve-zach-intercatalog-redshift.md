# Resolve Zach's inter-catalog redshift discrepancy

- Type: `wayfinder:research` (AFK)
- Status: resolved
- Assignee: unassigned
- Blocked by: none
- Map: [Expanded foreground catalog repair](../map-expanded-foreground-catalog-repair.md)
- Triage: `done`

## Question

Can official WISE--Pan-STARRS source-row evidence, public spectroscopy,
independent northern optical photometry, or classification catalogs distinguish
between the legacy WISE--Pan-STARRS--STRM photometric redshift
`z_phot = 0.012668989` and the optical-only PS1--STRM value
`z_phot = 0.4693608582 +/- 0.047097985` for the source at
RA `310.0912903 deg`, Dec `+72.81041703 deg`?

This investigation records evidence and access blockers only. It does not
change the adopted redshift, foreground verdict, or budget eligibility.

## Resolution

Resolved 2026-07-21 from
[Zach candidate: inter-catalog redshift investigation](../../specs/research-zach-intercatalog-redshift-discrepancy-2026-07-21.md)
(`research/zach-redshift-catalogs`).

The public evidence does **not** distinguish the two photometric redshifts.
Native 5-arcsec searches found no DESI DR1, Sloan Digital Sky Survey Data
Release 19, LAMOST Data Release 11, Gaia Data Release 3, or Legacy Surveys Data
Release 10 row that supplies an independent redshift or classification. The
decisive combined WISE--Pan-STARRS--STRM row requires an authenticated MAST
CasJobs export. UNIONS/CFIS photometry requires CADC access to `CFIS-read` and,
if obtained, would support a new validated fit rather than directly choose a
stored value. Retain the explicit inter-catalog disagreement; do not change the
redshift, verdict, or budget eligibility from this research.
