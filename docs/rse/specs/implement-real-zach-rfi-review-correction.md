# Implementation Summary: Correct the real Zach RFI review

**Date:** 2026-07-21
**Author:** Codex
**Status:** Implementation complete; owner review pending
**Plan:** [plan-real-zach-rfi-review-correction.md](plan-real-zach-rfi-review-correction.md)

## Overview

Replaced the invalid Zach diagnostic with a real-event product whose frequency
rows share an H5-derived time coordinate. The figure now shows the complete
burst with off-pulse padding and a one-dimensional time-integrated spectrum.

## Plan Adherence

The implementation follows the plan. No scientific acceptance claim was added:
the figure remains diagnostic-only because this observed event has no known RFI
truth.

## Phases Completed

- Phase 1: tests lock the dispersion-measure source, non-wrapping alignment,
  display width, padding, and integration window.
- Phase 2: rebuilt twice in the pinned network-disabled container; manifests are
  byte-identical; replaced the repository SVG, JSON, and checksums.

## Files

Created:

- `docs/rse/specs/research-real-zach-rfi-review-correction.md`
- `docs/rse/specs/plan-real-zach-rfi-review-correction.md`

Modified:

- `scripts/review_real_zach_rfi_cleaner.py`
- `tests/test_review_real_zach_rfi_cleaner.py`
- `docs/rse/verify/rfi-real-event-review-20260721/`
- `docs/rse/wayfinder/tickets/rfi-validation-01a-review-preservation-dynamic-spectrum.md`

No files were deleted. Git history retains the superseded artifact.

## Key Changes

1. Uses the source H5 coherent-dedispersion value
   `262.4359033801 pc cm^-3`.
2. Aligns each frequency row from its `fpga_count` without wraparound.
3. Shows `[197,305)` with on-pulse `[229,273)`: 14.42 ms on-pulse and
   10.49 ms padding on each side.
4. Adds the fixed-window time-integrated spectrum and frequency-row decisions.
5. Records the H5, worker, audit, container, input, script, array, and output
   hashes.

## Verification

- `13 passed` across the real-event and synthetic review tests.
- Python compilation passed.
- Repository artifact checksums and JSON parsing passed.
- Remote `review-1` and `review-2` manifests are byte-identical.
- Visual inspection confirms the full burst and new spectrum render.

## Remaining Work

- Owner judges the burst/window presentation and visible narrow-band
  contamination.
- The RFI cleaner remains unvalidated until a known-truth test supports it.
- Absolute arrival time remains uncertified.

## References

- [Research](research-real-zach-rfi-review-correction.md)
- [Plan](plan-real-zach-rfi-review-correction.md)
- [RFI ticket](../wayfinder/tickets/rfi-validation-01a-review-preservation-dynamic-spectrum.md)
