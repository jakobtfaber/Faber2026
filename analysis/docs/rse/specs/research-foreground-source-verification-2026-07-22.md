# Independent source verification of the foreground registry

Date: 2026-07-22

Disposition: **source identity pass; Figure 3 remains blocked**

Pinned analysis commit: `fe73689cad723db5d68427c61e301157a39cc101`

Pinned pipeline commit: `6057501da2db1eba09d002dd7846ffca7ded250c`

## Result

The offline independent replay checked every production row against frozen
source payloads, the owner-approved current Verdi table, and Law et al. (2024).
It imported no producing or adjudication code.

Every input is read with `git show <commit>:<path>`, not from the working tree.
The verifier records each Git blob identifier and SHA-256 in `replay.json` and
fails if the corresponding tracked working-tree file differs. Measurement kind
is derived from the frozen native fields: Legacy Survey and PS1-STRM are
photometric, quality-admitted DESI is spectroscopic, the NED `PUN` flag is
photometric, and WHL12 is a catalog-cluster value. The ledger's kind is checked
against that derivation. Adopted and source-reported uncertainty values and
explicit unavailable-uncertainty metadata are checked separately. Native
uncertainties must round exactly to the precision declared by the registry;
they do not use the looser redshift-value tolerance. In the pinned schema,
Legacy Survey, DESI, PS1-STRM, and WHL native uncertainties are bound through
the selected source row and `adopted_z_err`, so their separate
`source_reported_z_err` field must stay blank. NED must keep that field blank
and explicitly report that no uncertainty was supplied.

- 52/52 rows replayed; 46 are fully source-verified under the current identity
  and value contract.
- 52/52 stored verdicts and 52/52 budget flags reproduce.
- Substituting available authoritative host values changes 0 verdicts.
- 7/7 duplicate separations, redshifts, verdicts, and source-ledger identities
  reproduce.
- 46/46 adopted candidate redshifts match frozen source identities, positions,
  values, uncertainties where reported, measurement kinds, and payload hashes.
- 6 rows remain fail-closed for at least one source discrepancy.

The complete row-level result and input hashes are frozen in
[`replay.json`](evidence/foreground-source-verification-2026-07-22/replay.json).

## Discrepancies

### Host sources

- Whitney's seven rows retain registry host redshift `0.479`, matching the
  spectroscopic value in Connor et al. (2025)'s author-released sample table.
  Law et al. (2024)'s `0.477958` remains preserved but is not adopted.
- The seven Freya, Hamilton, and Chromatica rows now use the owner-approved
  Verdi source-event identifiers `20230325C`, `20230913G`, and `20240203D`.
- Zach's registry `0.043` is a valid three-decimal rounding of Law's
  `0.043040`; this is not a numerical discrepancy.
- Current production correctly leaves Wilhelm's host redshift blank, matching
  the approved current Verdi row. The older `0.5100` draft value is not used.

### Candidate sources

- Four redshiftless PS1-STRM rows independently match their frozen catalog
  identifiers and positions, and the source rows correctly report `UNSURE` and
  no redshift. The 52-row candidate provenance ledger nevertheless replaces
  those identities with `not_applicable`: Oran `195393180643665627`, Wilhelm
  `194453151328186646`, Hamilton `192943050854547067`, and Chromatica
  `196673126794497004`.
- The Isha `WISEA J044538.83+701843.3` and Oran
  `WISEA J211150.32+724807.8` extensions still have only manual prose
  provenance. No frozen authoritative source row establishes their identities
  and no-redshift dispositions.

### Identity repair (2026-07-23)

Pipeline commit `c913175e567db70980e5f2745dcdf8f7f3ad9fb4` repairs all six
candidate identity chains:

- The four redshiftless PS1-STRM rows now bind their exact frozen catalog rows,
  stable object identifiers, and no-redshift semantics.
- The two manual extensions now bind their exact AllWISE designations and
  frozen CDS VizieR `II/328/allwise` query rows. A separate live VizieR query
  returned both exact designations within the three-arcsecond search radius.
- No candidate redshift was adopted. Stored verdicts and budget flags are
  byte-for-byte unchanged.

The independent standard-library replay now verifies 52/52 rows with no source
discrepancies, verdict changes, or budget changes.

## Decision

The source replay validates 52/52. A separate adversarial review directly
checked all six pinned identities, coordinate separations, blank-redshift
semantics, provenance hashes, and unchanged Figure 3 inputs and passed on
2026-07-23. Its
[receipt](evidence/foreground-source-verification-2026-07-22/adversarial-review.json)
closes only the identity ticket. The source repair does not promote registry
authority, change verdicts or budgets, or promote Figure 3.

## Reproduction

```bash
python3 scripts/verify_foreground_registry_sources.py \
  --pipeline-dir /path/to/pipeline-at-c913175 \
  --output docs/rse/specs/evidence/foreground-source-verification-2026-07-22/replay.json
pytest -q tests/test_verify_foreground_registry_sources.py
```

The verifier exits nonzero while any row remains source-incomplete.
