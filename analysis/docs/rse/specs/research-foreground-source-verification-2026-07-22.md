# Independent source verification of the foreground registry

Date: 2026-07-22

Disposition: **fail closed**

Pinned analysis commit: `14ed87998646d80f48c8dc0713302383e4d332e8`

Pinned pipeline commit: `f3c8d22a9088914e0179cfecf1ee4086777dc927`

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

- 52/52 rows replayed; 34 are fully source-verified under the current identity
  and value contract.
- 52/52 stored verdicts and 52/52 budget flags reproduce.
- Substituting available authoritative host values changes 0 verdicts.
- 7/7 duplicate separations, redshifts, verdicts, and source-ledger identities
  reproduce.
- 46/46 adopted candidate redshifts match frozen source identities, positions,
  values, uncertainties where reported, measurement kinds, and payload hashes.
- 18 rows remain fail-closed for at least one source discrepancy.

The complete row-level result and input hashes are frozen in
[`replay.json`](evidence/foreground-source-verification-2026-07-22/replay.json).

## Discrepancies

### Host sources

- Seven Whitney rows use registry host redshift `0.479`. Law et al. (2024)
  reports `0.477958`, which rounds to `0.478`, not `0.479`. No stored verdict or
  budget flag changes, but adoption requires owner adjudication.
- Seven rows use local FRB identifiers not yet adjudicated against the
  owner-approved Verdi identifiers: two Freya rows (`20230325A` versus
  `20230325C`), two Hamilton rows (`20230913A` versus `20230913G`), and three
  Chromatica rows (`20240203A` versus `20240203D`). Their coordinates and
  redshifts agree; identity authority does not.
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

## Decision

Ticket 09's answer is **no**. Arithmetic is internally consistent, but all 52
rows do not pass source-level verification. Do not change registry authority,
verdicts, budgets, trust state, or Figure 3 here.

Route the Whitney value and Verdi identifier differences to ticket 19. Repair
the six candidate identity chains in a separate evidence-freeze change, then
repeat this verifier. Figure 3 remains blocked.

## Reproduction

```bash
python3 scripts/verify_foreground_registry_sources.py \
  --pipeline-dir /path/to/pipeline-at-f3c8d22 \
  --output docs/rse/specs/evidence/foreground-source-verification-2026-07-22/replay.json
pytest -q tests/test_verify_foreground_registry_sources.py  # 14 tests
```

The verifier exits nonzero while any row remains source-incomplete.
