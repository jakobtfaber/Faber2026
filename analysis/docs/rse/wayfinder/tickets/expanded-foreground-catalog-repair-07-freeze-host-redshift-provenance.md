# Freeze authoritative host-redshift evidence

- Type: `wayfinder:task` (HITL)
- Status: resolved
- Assignee: Codex
- Blocked by: [Independently verify foreground redshifts and verdicts](expanded-foreground-catalog-repair-06-verify-redshift-verdicts.md)
- Map: [Expanded foreground catalog repair](../map-expanded-foreground-catalog-repair.md)
- Delegation: [Standing delegated decision authority](../standing-delegation-2026-07-20.md)
- Triage: `resolved`

## Question

Can the authoritative Verdi host-redshift table, or a minimal source-bearing
extract, be frozen with FRB and host identifiers, redshift and uncertainty,
measurement kind, bibliographic source, upstream row identifier, release or
retrieval date, and content hash for every census sightline?

## Resolution

Resolved 2026-07-22 from the owner-supplied Verdi draft archive. The answer is
**no for authoritative, row-complete provenance**. A minimal comparison and
source manifest are frozen under
[`verdi-host-redshifts-2026-07-22/`](../../specs/evidence/verdi-host-redshifts-2026-07-22/).
The unpublished 20 MB archive is not copied into the repository; its SHA-256 is
`c1e14983531711aa47f214f0c010cdba550f4bf26b1ac132da96280d748a7346`.

The deterministic extract covers all 12 census sightlines. Six local values
match the current named draft. Zach and Whitney are absent. Wilhelm's local
`0.51` appears in the older `test.tex`, while the current named draft records
no redshift. The current draft supplies `0.5535` for JohndoeII while the local
census has no host redshift. Hamilton and Wilhelm differ between the two draft
files. Four local/source FRB suffixes differ, though their localization
coordinates match. No row has a host-galaxy identifier or row-level redshift
uncertainty; only Hamilton and Chromatica have explicit row-level spectroscopy
descriptions in the draft.

No adopted redshift, verdict, budget flag, or Figure 3 artifact changed.
Authority remains closed pending
[Obtain the authoritative host-redshift ledger](expanded-foreground-catalog-repair-17-obtain-authoritative-host-redshift-ledger.md).

Rebuild and fail-closed check:

```bash
python3 scripts/freeze_verdi_host_redshifts.py \
  --archive "$VERDI_ZIP" \
  --bursts "$FABER2026_ROOT/pipeline/galaxies/foreground/data/frozen_census/bursts.csv" \
  --output-dir docs/rse/specs/evidence/verdi-host-redshifts-2026-07-22 \
  --source-received-date 2026-07-22 \
  --expect-archive-sha256 c1e14983531711aa47f214f0c010cdba550f4bf26b1ac132da96280d748a7346
python3 scripts/freeze_verdi_host_redshifts.py \
  --archive "$VERDI_ZIP" \
  --bursts "$FABER2026_ROOT/pipeline/galaxies/foreground/data/frozen_census/bursts.csv" \
  --output-dir /tmp/verdi-host-redshift-check \
  --source-received-date 2026-07-22 \
  --expect-archive-sha256 c1e14983531711aa47f214f0c010cdba550f4bf26b1ac132da96280d748a7346 \
  --require-authoritative  # expected exit 2
```
