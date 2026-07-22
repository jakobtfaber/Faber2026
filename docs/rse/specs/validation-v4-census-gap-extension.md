# Validation: V4 census-gap extension

Validated against [the plan](plan-v4-census-gap-extension.md) and
[implementation log](implement-v4-census-gap-extension.md) at Faber2026
`f76b85f` with FLITS `a70b9c5` on 2026-07-15.

## Implementation Status

- Phase 1, registry extension: implemented and freshly verified.
- Phase 2, generated foreground table: implemented and freshly verified.
- Phase 3, manuscript synchronization: implemented and freshly compiled.
- Publication: FLITS merged; Faber2026 is ready for PR but awaits the two manual
  owner checks below.

## Automated Verification Results

- PASS — census tests: 10 passed.
- PASS — foreground table emitter tests: 4 passed.
- PASS — sightline-budget integration subset: 19 passed, 1 skipped; the one
  excluded pre-existing test requires an unavailable fit artifact.
- PASS — full FLITS GitHub test workflow on Python 3.12.
- PASS — registry invariants: 52 unique rows; verdicts 30/15/7; three extension
  rows; zero extension budget eligibility.
- PASS — budget table SSOT/export unchanged from FLITS `origin/main` at branch
  creation.
- PASS — FLITS export and manuscript `foreground_table.tex` are byte-identical.
- PASS — focused Ruff checks.
- PASS — final `latexmk` compile; 36 pages.
- PASS — `agent-closeout-check` for the FLITS worktree before publication.

## Code Review Findings

The implementation matches the plan's append-only design. The extension CSV
uses the registry schema, stable keys are enforced, and `registry_tier` plus
`budget_eligible` are recomputed from authoritative fields rather than trusted
from hand-entered booleans. Named table rows are now covered by registry parity.
No extension system can reach Table 4 under the current gate.

The only intentional numerical deviation is the WHL12 impact parameter:
repository coordinates/cosmology reproduce 614.33 kpc, consistent with the
captured 613.99-kpc discovery output; the 608-kpc continuation value is retained
only as a documented provenance difference.

## Manual Testing Required

Please confirm both statements:

1. The table/prose make it clear that the displayed 0.084 WISExSCOS value and
   the GLADE+ distance value are discovery context, not validated redshifts.
2. WHL J115048.0+714428 should remain a confirmed, budget-ineligible cluster
   systematic until a separate WHL12 richness/mass and identity adjudication.

## Recommendations

### Critical

None.

### Important

- Do not merge the Faber2026 PR until the two manual checks above are accepted.

### Follow-up

- If the cluster should enter the budget, open a separate modeling lane for
  WHL12 richness-to-`M500`, centroid/identity adjudication, and double-counting
  control against J115120.4+714435.
- Regenerate the sightline-halo figure separately if the extension markers are
  meant to become part of the final visual artifact.

## References

- [Plan](plan-v4-census-gap-extension.md)
- [Implementation log](implement-v4-census-gap-extension.md)
- [Research](research-v4-census-gap-extension.md)
