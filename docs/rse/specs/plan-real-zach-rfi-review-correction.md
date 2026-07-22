# Implementation Plan: Correct the real Zach RFI review

---
**Date:** 2026-07-21
**Author:** Codex
**Status:** Implemented; owner rejected cleaner for residual RFI
**Related Documents:**
- [Research](research-real-zach-rfi-review-correction.md)
---

## Overview

Replace the invalid Zach review with a time-aligned product at the H5 coherent
dispersion measure, a padded full-burst display, and an explicit
time-integrated spectrum.

**Goal:** A reproducible diagnostic in which every frequency row shares the
same defined time coordinate and the entire 14.21-ms burst is visible.

## Current State Analysis

- `scripts/review_real_zach_rfi_cleaner.py:22-25` hard-codes the clipped
  `[232,248)` interval and no H5 time alignment.
- `scripts/review_real_zach_rfi_cleaner.py:214-306` plots three dynamic spectra
  but no one-dimensional time-integrated spectrum.
- `tests/test_review_real_zach_rfi_cleaner.py:31-53` locks in the wrong slice.

## Desired End State

- Coherent product DM: `262.4359033801 pc cm^-3`.
- Non-wrapping `fpga_count` alignment with an analytic delay-law test.
- Display `[197,305)`; on-pulse integration `[229,273)`.
- Three aligned dynamic spectra, one time profile, one time-integrated spectrum,
  and one retained/rejected-channel panel.
- Superseded artifact explicitly invalidated in the ticket and machine record.

## What We're NOT Doing

- [ ] Adopting a new manuscript DM.
- [ ] Validating the RFI classifier without known truth.
- [ ] Fitting scattering, scintillation, or burst components.

## Implementation Approach

Use the existing pinned worker and audit code. Add a pure alignment helper that
derives nominal fine-channel identifiers, maps each row to its H5 coarse-channel
`fpga_count`, and applies integer non-wrapping shifts. The time-integrated
spectrum is the sum of standardized intensity over the independently fixed
on-pulse envelope.

## Implementation Phases

### Phase 1: Lock the time and window invariants

**Objective:** Make the previous failure deterministic.

**Tasks:**
- [x] Add tests in `tests/test_review_real_zach_rfi_cleaner.py` asserting the
  analytic two-channel delay alignment, a display wider than the 14.21-ms
  envelope with padding, and distinct display/on-pulse intervals.
- [x] Run
  `/Users/jakobfaber/.conda/envs/py312/bin/python -m pytest tests/test_review_real_zach_rfi_cleaner.py -q`
  and observe failure before implementation.
- [x] Implement `alignment_shifts()` and `align_nonwrapping()` in
  `scripts/review_real_zach_rfi_cleaner.py`.
- [x] Re-run the same command and require all tests to pass.

### Phase 2: Rebuild and reproduce the diagnostic

**Objective:** Generate the corrected real-event artifact.

**Tasks:**
- [x] Update input hashes to the `262.4359033801` product and load only training
  `[55,137)` plus source columns needed for aligned display `[197,305)`.
- [x] Replace the old plot with aligned dynamic spectra, a time profile, a
  time-integrated spectrum over `[229,273)`, and a channel-support panel.
- [x] Run the exact script twice in the pinned network-disabled container under
  `/data/Faber2026/evidence/zach-chime-rfi-review-correction-20260721/`.
- [x] Require byte-identical manifests and visually inspect the SVG.
- [x] Replace the local SVG/JSON/checksums and update the RFI ticket.

## Success Criteria

### Automated Verification

- [x] Current crop test fails before the fix and passes afterward.
- [x] Two-channel analytic alignment test passes exactly to one output bin.
- [x] All Zach review and synthetic-prototype tests pass.
- [x] Corrected container runs have byte-identical manifests.
- [x] JSON records DM, time0-derived schedule DM, shifts, windows, hashes, and
  exact commands.

### Manual Verification

- [ ] Owner confirms the complete burst and off-pulse padding are visible.
- [x] Owner can judge narrow-band contamination from the one-dimensional
  spectrum. Outcome: current candidate rejected for residual RFI at
  700–750 MHz.

### Reproducibility & Correctness

- [x] The cold-plasma delay law is the independent alignment criterion.
- [x] Original H5, worker, audit, container, corrected product, script, and
  output hashes are recorded.
- [x] Clean-container reproduction matches byte-for-byte.

## Testing Strategy

Unit tests cover slice access, analytic shifts, non-wrapping missing values,
window width, coarsening, and status language. The integration run uses the
real H5-derived product but makes no cleaner-correctness claim.

## Risk Assessment

- Incorrect sign in the alignment shift: caught by the analytic arrival-time
  invariant and cross-band peak-spread report.
- Burst window selected from the same cleaner output: avoided by fixing it from
  the bandpass-only aligned profile and documenting it separately.
- Superseded figure consumed accidentally: prevented by replacing the review
  path and recording the invalidation in the ticket/JSON.

## References

- [Research](research-real-zach-rfi-review-correction.md)
- `scripts/review_real_zach_rfi_cleaner.py`
- `tests/test_review_real_zach_rfi_cleaner.py`
- `pipeline/analysis/scattering-refit-2026-06/baseband_recovery/upchannelize_chime.py`
