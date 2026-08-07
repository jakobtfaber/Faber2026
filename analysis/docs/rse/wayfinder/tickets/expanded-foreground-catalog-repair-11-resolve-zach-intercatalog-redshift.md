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
`z_phot0 = 0.012668989` and the optical-only PS1--STRM value
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

### Source-row follow-up

Updated 2026-07-21 after the owner supplied the authenticated MAST CasJobs
export, frozen at
[`zach_foreground_jfaber.csv`](../../specs/research/evidence/zach-intercatalog-redshift-2026-07-21/zach_foreground_jfaber.csv)
(SHA-256
`d2fcc7fb2db3f1a627b1716ec7cf70d87456eacc57d1ef27d22c7f9bee6105f1`).

The export contains two PS1 sources separated by `0.9962 arcsec` sharing the
same WISE source `cntr=3113172601241027886`. The target PS1 object
`195373100910393540` is the more distant WISE association (`0.85675 arcsec`;
Bayes factor `1.9304e10`) and is extrapolated for both classification and
photometric redshift. Its official Monte Carlo value is
`z_phot=0.0122979190 +/- 0.0653016341`; the spreadsheet value `0.012668989` is
`z_phot0`, the base estimate. The second PS1 source is only `0.18604 arcsec`
from the same WISE position, has a `33.25` times larger Bayes factor, and is
classified QSO; no galaxy photometric redshift is provided for it.

This resolves the attribution and exposes a shared-WISE-source ambiguity, but
does not independently choose between the combined-catalog and optical-only
redshift estimates. Preserve the scientific status and require a separate
redshift/verdict adjudication before any change.
