# Implementation Plan: Time-frequency RFI candidate

**Date:** 2026-07-21
**Author:** Codex
**Status:** Implemented; candidate rejected by preservation checks
**Related Documents:**
[research](research-rfi-time-frequency-candidate.md),
[experiment](experiment-rfi-time-frequency-candidate.md),
[owner review ticket](../wayfinder/tickets/rfi-validation-01a-review-preservation-dynamic-spectrum.md)

## Overview

Implement the frozen Pixel-6 development candidate, rebuild its synthetic
known-truth review, then apply the same code and threshold to the corrected Zach
product. The candidate retains the package's off-pulse row mask and adds an
explicit two-dimensional mask after bandpass normalization.

**Goal:** Produce reproducible synthetic and Zach review panels showing whether
fixed six-level pixel clipping removes the residual time-local contamination
without hidden value replacement.

## Current State Analysis

- The synthetic script broadcasts one row decision across all time samples
  (`scripts/prototype_rfi_preservation_review.py:311-360`).
- Synthetic truth already includes four contamination classes
  (`scripts/prototype_rfi_preservation_review.py:134-199`).
- The real-event script returns normalized context and a row-valid mask
  (`scripts/review_real_zach_rfi_cleaner.py:171-224`).
- The corrected real display and spectrum are formed only after non-wrapping
  time alignment (`scripts/review_real_zach_rfi_cleaner.py:516-532`).

## Desired End State

- One shared development function returns a Boolean pixel mask for finite,
  row-valid samples with `abs(value) >= 6.0`.
- Synthetic and Zach scripts use that exact function and record its source hash.
- All rejected samples are `NaN`; unmasked values are byte-unchanged.
- Synthetic review reports truth-mask recovery and protected measurements.
- Zach review shows bandpass-only, row-only, and Pixel-6 output; a dynamic mask;
  time profile; and one-dimensional on-pulse spectrum.
- Threshold and code are frozen before the first Zach run.

## What We're NOT Doing

- Opening public validation or sealed test intervals.
- Adjusting the threshold after viewing Zach.
- Selecting or validating a production cleaner.
- Replacing masked values by interpolation or zero.
- Promoting the candidate to manuscript or science use.

## Implementation Approach

Add `scripts/rfi_time_frequency_candidate.py` as a development-only shared
module. It contains only mask construction and mask application. Both review
scripts import it. Existing row-mask and bandpass code remains unchanged.

The candidate order is: off-pulse package row mask, off-pulse bandpass model,
normalization, second training-derived row mask, then fixed per-pixel clipping.
The Zach mask is calculated before time regridding and moved with its samples by
the existing non-wrapping alignment.

## Implementation Phases

### Phase 1: Lock mask semantics

**Status:** Complete.

1. Add failing tests to `tests/test_rfi_time_frequency_candidate.py` asserting:
   exact-threshold pixels are rejected; invalid rows and `NaN` pixels are not
   newly classified; unmasked values are unchanged; masked values become
   `NaN`; and input arrays are not mutated.
2. Run
   `/Users/jakobfaber/.conda/envs/py312/bin/python -m pytest tests/test_rfi_time_frequency_candidate.py -q`
   and require failure because the module does not exist.
3. Add `scripts/rfi_time_frequency_candidate.py` with constant
   `ABSOLUTE_PIXEL_THRESHOLD = 6.0`, `absolute_pixel_mask()`, and
   `apply_pixel_mask()`.
4. Re-run the same test and require all assertions to pass.

### Phase 2: Rebuild synthetic known-truth review

**Status:** Complete.

1. Add failing integration assertions to
   `tests/test_prototype_rfi_preservation_review.py` requiring a two-dimensional
   predicted mask and common-pixel-support measurements.
2. Update `scripts/prototype_rfi_preservation_review.py` to apply the shared
   candidate after the existing row mask, generalize confusion accounting to a
   pixel mask, and render the Pixel-6 output and mask.
3. Run both test files and require all tests to pass.
4. Run twice in the pinned network-disabled container under
   `/data/Faber2026/evidence/rfi-time-frequency-candidate-20260721/synthetic-{1,2}`;
   require byte-identical manifests.

### Phase 3: Apply frozen candidate to Zach

**Status:** Complete.

1. Add failing tests to `tests/test_review_real_zach_rfi_cleaner.py` requiring
   the shared threshold, explicit pixel mask, and common-pixel-support spectrum.
2. Update `scripts/review_real_zach_rfi_cleaner.py` without changing coherent
   dispersion measure, alignment, display, on-pulse interval, or training slice.
3. Run twice in the same pinned container under
   `/data/Faber2026/evidence/rfi-time-frequency-candidate-20260721/zach-{1,2}`;
   require byte-identical manifests.
4. Require the predeclared diagnostic failure signal in 700–750 MHz to improve
   from 18.39 to below 10 median-based spread units. Failure rejects the frozen
   candidate; it does not authorize threshold tuning.
5. Copy only the synthetic/Zach SVG, JSON, and checksums into
   `docs/rse/verify/rfi-time-frequency-candidate-20260721/`.

## Success Criteria

### Automated Verification

- All three focused test files pass.
- Synthetic Pixel-6 recovery matches the frozen experiment within `1e-12`:
  overall `0.98689303068266`, broadband impulse `0.9966393991580559`, and
  drifting line `1.0`.
- The added clean-pixel rejection fraction is at most `0.002` beyond row only.
- Unmasked values are byte-identical to normalized input.
- Two synthetic and two Zach manifests are pairwise byte-identical.
- Zach's 700–750 MHz retained-spectrum maximum is below 10 median-based spread
  units without changing threshold `6.0`.
- Local checksums, JSON parsing, Python compilation, and `git diff --check` pass.

### Manual Verification

- Owner judges whether residual RFI remains in the Zach dynamic spectrum and
  one-dimensional spectrum.
- Owner judges whether the pixel mask removes plausible burst structure.
- Figure wording remains development-only and does not imply validation.

### Reproducibility and Correctness

- Input, source, container, seed, threshold, command, and output hashes are
  recorded.
- An analytic unit test proves mask and value-preservation semantics.
- Clean-container reruns reproduce byte-for-byte.

## Testing Strategy

Unit tests cover threshold boundaries, missing-data semantics, immutability, and
common support. Full-grid synthetic integration checks known truth; the Zach run
is diagnostic-only and uses no truth claim.

## Risks

- Bright astrophysical fine pixels may exceed 6. The mask panel and known-truth
  preservation checks expose, but cannot fully resolve, that risk.
- Row-only false rejection remains dominant; Pixel 6 does not repair it.
- A successful Zach appearance does not replace the later frozen benchmark or
  blind test.

## Outcome

The implementation and repeated runs satisfy the mechanical plan. The candidate
does not satisfy the scientific preservation purpose. On synthetic known truth,
it exceeds the tentative single-case bounds for morphology, normalized
residual, and spectral modulation. On Zach it lowers the 700–750 MHz outlier
score from `18.39` to `6.36`, but the mask and time profile show that it also
clips the burst. The candidate is rejected and must not advance to validation
or science use.

## References

- [Research](research-rfi-time-frequency-candidate.md)
- [Experiment](experiment-rfi-time-frequency-candidate.md)
- [Original prototype plan](plan-rfi-preservation-dynamic-spectrum-prototype.md)
- `scripts/prototype_rfi_preservation_review.py`
- `scripts/review_real_zach_rfi_cleaner.py`
