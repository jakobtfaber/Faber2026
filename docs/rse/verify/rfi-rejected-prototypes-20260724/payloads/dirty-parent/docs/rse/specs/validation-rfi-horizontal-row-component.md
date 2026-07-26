# Validation report

> Validated against `plan-rfi-horizontal-row-component.md` and
> `implementation-rfi-horizontal-row-component.md` in the Phase 7 worktree on
> 2026-07-22.

## Overall Status: Incomplete — infrastructure ready, owner maps pending

## Summary

- Phases: five rejected experiment phases preserved; manual-map infrastructure
  implemented; event review incomplete.
- Automated checks: passing.
- Manual testing: Zach row selection and approval required; 23 other
  event/instrument maps remain pending.
- Critical code issues: none for the draft infrastructure.
- Science use: blocked; no map is owner-approved and the diagonal/time-local
  RFI class is unresolved.

## Implementation Status

### Phases 1–5: Automated row candidates

**Status:** Complete as rejected experiments.

- Robust rows, Pixel 6, four-row seed promotion, isolated seeds, and raw-voltage
  parent mapping are reproducible.
- Owner rejected the final composite because it erased broad frequency blocks.
- Checked-in automated defaults are not bad-channel authority.

### Phase 6: Owner-reviewed manual bad-channel maps

**Status:** Partially implemented.

- Exact map validator and `NaN` application: complete.
- Twelve-event by two-instrument fail-closed index: complete.
- Zach CHIME/FRB draft bound to source and frequency hashes: complete.
- Zach bandpass-only 400–800 MHz atlas in eight 50-MHz segments: complete.
- Owner row selection, before/after review, and approval: pending.
- Remaining CHIME/FRB and DSA-110 atlases/maps: pending.
- Downstream pipeline integration: intentionally pending until an approved map
  exists.

## Automated Verification Results

### Passing checks

- `pytest` focused RFI/map/notebook/GUI suite — 53 passed.
- Python compilation for map loader, atlas generator, Zach review, and both
  diagnostic candidate modules — passed.
- Real Zach notebook execution with the dedicated `Faber2026 (Python 3)`
  kernel — passed without saving or selecting rows.
- Real Zach standalone GUI construction — passed without saving or selecting
  rows; all three drag panels retain the active frequency limits.
- Eight atlas JSON records — parse and cover contiguous intervals from 400 to
  800 MHz.
- `sha256sum -c` for all eight SVGs and eight JSON records — passed.
- Draft map with `--allow-draft` against live h17 products — validates and
  produces zero bad rows.
- The same draft without `--allow-draft` — fails with
  `bad-channel map is not owner-approved`, as required.
- Source-product SHA-256, frequency-axis SHA-256, full 65,536-row axis, and
  55,744 measured-position count match live h17 evidence.

### Failing checks

None in the implemented draft infrastructure.

## Code Review Findings

### What matches the plan

- Map use is fail-closed on approval, source hash, frequency hash, row count,
  range ordering, overlap, bounds, and recorded frequency limits.
- Selected rows alone become `NaN`; the input and retained rows remain exact.
- The manual atlas starts from bandpass-only measured support and applies no
  package RFI mask or proposed manual zap.
- Every atlas records exact input, review-script, atlas-script, and container
  hashes.

### Deviations from the earlier plan

- Automatic RFI row promotion was abandoned after direct owner rejection.
- Manual maps replace automatic row candidates as science authority.
- The first atlas version started after package row masking; it was invalidated
  and preserved separately before the bandpass-only rerun.

### Potential issues

- A one-dimensional map cannot remove diagonal or time-local interference
  without erasing the full swept frequency range.
- Atlas dynamic spectra are coarsened by eight fine rows for display. Final map
  ranges remain exact full-resolution row indices and require a before/after
  review.
- The map consumer is not yet wired into downstream measurements because no
  approved map exists. Science runs must remain blocked until that integration
  is tested with the first approved map.

## Manual Testing Required

1. Review Zach’s eight CHIME/FRB atlas segments and select exact stationary bad
   channel rows.
2. Render and inspect Zach before/after dynamic spectrum, off-pulse measures,
   on-pulse spectrum, time profile, and retained support.
3. Approve or revise the Zach map. Only then change status to
   `owner_approved` and add reviewer/time.
4. Repeat for the remaining eleven CHIME/FRB events, then twelve DSA-110 events.

## Recommendations

### Critical

- Do not use any manual map for science until owner approval and downstream
  integration validation.

### Important

- Keep diagonal/time-local RFI as a separate open method ticket; do not encode
  it as broad channel zaps by default.
- Add source-valid-mask hash verification to the downstream integration where
  the map is applied.

### Follow-up

- Generate the remaining event atlases from their standardized bandpass-only
  products.
- After the first approved map, add an end-to-end test proving every relevant
  measurement reads the same map and preserves retained values.

## References

- [Plan](plan-rfi-horizontal-row-component.md)
- [Implementation](implementation-rfi-horizontal-row-component.md)
- [Manual-map policy](../../../analysis/rfi/manual-bad-channels/README.md)
