# Handoff: close the expanded foreground catalog repair map

Date: 2026-07-23

## Objective

Continue the expanded foreground catalog repair through source verification,
Figure 3 regeneration, independent validation, and owner visual approval.

## Starting state

- Host-redshift differences were resolved.
- Independent replay verified 46/52 rows.
- Exactly six source-identity chains remained:
  - Oran `195393180643665627`
  - Wilhelm `194453151328186646`
  - Hamilton `192943050854547067`
  - Chromatica `196673126794497004`
  - Isha `WISEA J044538.83+701843.3`
  - Oran `WISEA J211150.32+724807.8`
- The four PS1-STRM rows matched frozen catalog rows but their provenance-ledger
  identities were missing.
- The two WISEA extensions lacked frozen authoritative identity rows.

## Required order

1. Freeze all six source identities.
2. Rerun `scripts/verify_foreground_registry_sources.py`; require 52/52 and
   zero verdict or budget changes.
3. Regenerate Figure 3.
4. Independently validate the regenerated figure.
5. Stop for owner visual approval.
6. Promote only after approval.

## Guardrails

- `intervening_census_registry.csv` remains verdict and budget authority.
- Frozen discovery files retain historical identifiers.
- Do not change redshifts, verdicts, or budget flags in an identity repair.
- Do not bump manuscript submodule pointers as a side effect.
- Numerical validation does not equal scientific release approval.
- Record every substantive changed path with `verify-gate`.

## Current continuation

Ticket 20 validates the six identity repairs at pipeline commit
`c913175e567db70980e5f2745dcdf8f7f3ad9fb4`. The replay now passes
52/52 with zero verdict and budget changes. A separate adversarial review must
pass before resolving the ticket or starting Figure 3 regeneration. The owner
visual-approval gate remains mandatory.
