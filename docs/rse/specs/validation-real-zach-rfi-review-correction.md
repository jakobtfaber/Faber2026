# Validation Complete

> Validated against `plan-real-zach-rfi-review-correction.md` and
> `implement-real-zach-rfi-review-correction.md` at commit `f7b4cd4` on
> 2026-07-21.

## Overall Status: Awaiting owner figure review

- Phases: 2 of 2 implemented
- Automated checks: 5 passing, 0 failing
- Manual checks: 2 require owner judgment
- Critical issues: 0
- Important issues: 0

## Implementation Status

### Phase 1: Time and window invariants

**Status:** Fully implemented

- Analytic cold-plasma alignment test: complete
- Non-wrapping missing-edge test: complete
- Full-envelope and padding test: complete
- Fixed-window spectrum test: complete

### Phase 2: Rebuilt diagnostic

**Status:** Fully implemented

- Corrected H5-derived product and hashes: complete
- Aligned three-panel dynamic-spectrum comparison: complete
- Time profile, one-dimensional spectrum, and row decisions: complete
- Two byte-identical clean-container runs: complete
- Repository artifact and ticket replacement: complete

## Automated Verification Results

All automated checks passed:

- `python -m pytest tests/test_review_real_zach_rfi_cleaner.py tests/test_prototype_rfi_preservation_review.py -q` — 13 passed
- `python -m py_compile scripts/review_real_zach_rfi_cleaner.py tests/test_review_real_zach_rfi_cleaner.py` — passed
- `sha256sum -c SHA256SUMS` — SVG and JSON passed
- `python -m json.tool real_zach_rfi_method_comparison.json` — passed
- Remote `diff -u review-1/SHA256SUMS review-2/SHA256SUMS` — no differences

## Code Review Findings

### What Matches the Plan

- Coherent DM is `262.4359033801 pc cm^-3`, sourced from the H5 detected-power
  metadata.
- Per-row alignment uses `fpga_count`, the cold-plasma law, integer output-bin
  shifts, and no wraparound.
- The selected 14.42-ms on-pulse interval has 10.49 ms padding on each side.
- The 1D spectrum integrates only the fixed on-pulse interval.
- The record separates coherent DM, time0 schedule DM, and uncertified absolute
  arrival time.
- The status remains diagnostic-only.

### Deviations from the Plan

None.

### Potential Issues

No implementation issue found. Scientific interpretation remains intentionally
open because the observed event has no known RFI truth.

## Manual Testing Required

1. Confirm the complete burst and sufficient off-pulse context are visible.
2. Judge whether the 1D spectrum exposes the narrow-band contamination needed
   for the preservation-limit decision.

## Recommendations

### Critical

None.

### Important

None.

### Follow-Up

- Record the owner's decision on the RFI ticket.
- Do not use this diagnostic as cleaner validation or manuscript evidence.

## References

- [Plan](plan-real-zach-rfi-review-correction.md)
- [Implementation](implement-real-zach-rfi-review-correction.md)
