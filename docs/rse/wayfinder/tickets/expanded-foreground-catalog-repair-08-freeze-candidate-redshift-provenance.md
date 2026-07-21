# Freeze candidate-redshift source evidence

- Type: `wayfinder:task` (AFK)
- Status: resolved
- Assignee: —
- Blocked by: [Independently verify foreground redshifts and verdicts](expanded-foreground-catalog-repair-06-verify-redshift-verdicts.md)
- Map: [Expanded foreground catalog repair](../map-expanded-foreground-catalog-repair.md)
- Delegation: [Standing delegated decision authority](../standing-delegation-2026-07-20.md)
- Triage: `resolved`

## Question

Can every adopted Legacy Survey, DESI, STRM, NED, WHL12, and extension redshift
be tied to a stable source identifier and a frozen, hashed source row or query
response with release, retrieval date, value, uncertainty, and measurement kind?

## Resolution

Resolved 2026-07-21 by
[PR #168](https://github.com/jakobtfaber/Faber2026/pull/168), which pins
pipeline commit `7d26b1f7d3747afebb0ed7064d3058d25fb33396`.

The answer is **yes for every adopted candidate redshift currently in the
registry**. The freeze ledger is
`pipeline/galaxies/foreground/data/candidate_redshift_provenance.csv`.
It covers all 52 registry rows and preserves every stored verdict and
budget-eligibility flag. Forty-six rows have adopted candidate redshifts with
stable source identifiers, source releases, retrieval timestamps, source-row
hashes, query-response hashes where applicable, adopted values, uncertainties
when present, and measurement kinds.

Source-family coverage for adopted candidate redshifts:

- Legacy Survey / Zhou et al. photometric redshifts: 17 rows.
- DESI spectra: 22 rows.
- PS1-STRM photometric redshifts: 5 rows.
- NED redshift: 1 row.
- WHL12 cluster catalog redshift: 1 row.

Six registry rows have no adopted candidate redshift and are recorded as
`no adopted redshift`; they remain inconclusive. This ticket does not
re-adjudicate any redshift, foreground verdict, duplicate relationship, or
budget flag.

Validation:

- `uv run python -m galaxies.foreground.freeze_candidate_redshift_provenance`
- `uv run rtk pytest galaxies/foreground/test_candidate_redshift_provenance.py -q`
- `uv run rtk pytest galaxies/foreground/test_census_registry.py galaxies/foreground/test_foreground_table_emitter.py galaxies/foreground/test_candidate_redshift_provenance.py -q -k 'not scratch_codetection_exists'`
- `uv run rtk ruff check galaxies/foreground/freeze_candidate_redshift_provenance.py galaxies/foreground/test_candidate_redshift_provenance.py`
