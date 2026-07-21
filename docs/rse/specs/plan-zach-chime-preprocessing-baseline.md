# Implementation Plan: Zach CHIME preprocessing baseline

---
**Date:** 2026-07-21
**Author:** Codex
**Status:** Implemented; manual method decision pending
**Related Documents:**
- [Research](research-zach-chime-preprocessing-baseline.md)
- [Wayfinder task](../wayfinder/tickets/16-build-verified-zach-chime-preprocessing-baseline.md)
---

## Overview

Make future h17 source migrations fail closed before mutation, then produce one
hash-pinned Zach CHIME/FRB baseband preprocessing baseline on the nominal frequency
grid. Diagnose RFI and bandpass behavior using disjoint off-pulse data.

**Goal:** A reproducible evidence packet proving grid and mask semantics and
quantifying preprocessing weaknesses without making a science claim.

## Current State Analysis

- `scripts/h17_source_data_layout.py:320-375` starts renames before hashes are durable.
- `pipeline/analysis/scattering-refit-2026-06/baseband_recovery/upchannelize_chime.py:240-423`
  emits only retained fine channels.
- `pipeline/scintillation/configs/bursts/zach_chime.yaml:1-41` does not enable
  channel-by-channel bandpass normalization.

## Desired End State

- Every future migration attempt has byte-identical local and remote preflight
  packets before the first rename.
- Zach has 65,536 factor-64 positions, 55,744 measured positions, 9,792 missing
  positions, and an explicit validity mask.
- A held-out off-pulse report compares raw, grid-only, RFI-only, bandpass-only,
  and combined preprocessing.
- All inputs, code, container, commands, outputs, and failures have hashes.

## What We're NOT Doing

- Dispersion, scattering, scintillation, or morphology fitting.
- Adopting a manuscript value or promoting an existing CHIME scintillation result.
- Re-running or rewriting the already-completed 2026-07-21 source migration.
- Overwriting any prior baseband product.

## Implementation Approach

1. Canonically serialize a complete attempt-specific preflight packet, atomically
   persist it locally and remotely, verify matching SHA-256 hashes, then allow the
   existing rename transaction.
2. Preserve package-produced fine identifiers, scatter measured rows into the
   nominal grid, fill missing rows with `NaN`, and save a Boolean validity mask.
3. Stage the exact worker in a new h17 evidence directory. Run with read-only
   source data and the immutable container digest. Use disjoint off-pulse training
   and validation windows for diagnostics.

## Implementation Phases

### Phase 1: Durable migration preflight

**Objective:** No rename is reachable until complete local and remote preflight
artifacts exist and their SHA-256 hashes match.

**Tasks:**

- [x] Add failing tests in `tests/test_h17_source_data_layout.py` for canonical
  complete payloads, local-before-remote-before-migrate ordering, abort on either
  write failure or digest mismatch, and final receipt linkage.
- [x] Run `pytest -q tests/test_h17_source_data_layout.py`; expect new failures.
- [x] Add atomic local writing and remote write-and-verify support to
  `scripts/h17_source_data_layout.py`; use a unique attempt identifier and never
  overwrite existing evidence.
- [x] Run `pytest -q tests/test_h17_source_data_layout.py`; 12 passed.

**Verification:** No mocked `REMOTE_MIGRATE` call occurs after any persistence
failure or mismatch.

### Phase 2: Nominal-grid worker

**Objective:** Preserve measured values and make missing channels explicit.

**Tasks:**

- [x] Add failing unit tests beside the baseband recovery tests for a sparse
  synthetic channel map, exact measured-value preservation, nominal shape,
  monotonic frequencies, and missing=`NaN` plus mask=false.
- [x] Run the focused pipeline tests; three expected failures observed.
- [x] Update `upchannelize_chime.py` to retain fine identifiers, restore the
  nominal grid, save the mask, and always write provenance metadata.
- [x] Run the focused pipeline tests; 15 combined focused tests passed.

**Verification:** Synthetic factor-64 output has 65,536 rows and no missing row
contains a finite value.

### Phase 3: Live Zach run and preprocessing audit

**Objective:** Execute the pinned baseband chain once and measure RFI/bandpass
behavior without fitting science parameters.

**Tasks:**

- [x] Create a collision-free evidence directory under
  `/data/Faber2026/evidence/zach-chime-preprocessing-20260721/`; record pre-run
  process, disk, input, worker, and container hashes.
- [x] Stage the exact worker and run Zach with source mounted read-only, network
  disabled, and output limited to the evidence directory.
- [x] Verify 1,024 coarse / 65,536 fine positions, 153 / 9,792 missing positions,
  monotonic spacing, unchanged measured rows, and deterministic metadata.
- [x] Run the off-pulse audit using training bins 55:137 and validation bins
  138:220. Record mask fraction/stability, per-channel mean and standard-deviation
  dispersion, lag-one correlation, low-lag frequency autocorrelation, coarse-grid
  comb power, and bandpass-gain stability for all five variants.
- [x] Write hashes and exact commands to a repo-local validation document. Do not
  label any scintillation result validated.

**Verification:** Evidence JSON passes its invariant checker; source hash remains
unchanged; no existing output path changes.

## Success Criteria

### Automated Verification

- [x] `pytest -q tests/test_h17_source_data_layout.py`
- [x] Focused pipeline baseband-recovery tests pass.
- [x] Local and remote preflight bytes have identical SHA-256 hashes in mocks.
- [x] Live output reports `65536`, `55744`, `9792` for total, measured, missing.
- [x] Missing positions are non-finite and excluded by the validity mask.
- [x] Input SHA-256 remains
  `215079a689c18b50a4b2cd8003529e34d531a326be677a86187be02e47d0f1a9`.

### Manual Verification

- [ ] Owner reviews the concise RFI/bandpass diagnostic figures before any method
  is adopted.
- [ ] Owner decides whether the combined preprocessing is acceptable for a later
  Zach science run.

### Reproducibility & Correctness

- [x] Record source hash, worker hash, git commit, container repository digest,
  image identifier, package commit, exact command, channel map, windows, and output hashes.
- [x] Synthetic restoration preserves every retained value exactly.
- [x] RFI masks and bandpass gains use no on-pulse or held-out validation sample.

## Testing Strategy

Unit tests mock SSH and use small synthetic matrices. Live integration uses the
real Zach H5 read-only and writes only to a new evidence directory. The source is
hashed before and after. Figures are diagnostic-only and must show training and
validation separately.

## Migration Strategy

The new preflight format applies only to future migration attempts. Existing
receipts remain unchanged. Mid-transaction mixed layouts stop for manual recovery;
the tool does not auto-resume.

## Risk Assessment

- **Zero interpreted as missing:** prevented by `NaN` plus explicit mask invariants.
- **Remote code drift:** prevented by staging and recording the exact worker hash.
- **Burst leakage into cleaning:** prevented by disjoint off-pulse training and
  validation windows.
- **False scientific promotion:** prevented by ticket scope and explicit no-fit boundary.

## Edge Cases and Error Handling

- Existing preflight artifact: fail; never overwrite.
- Remote digest mismatch: abort before rename.
- Duplicate or out-of-range channel identifier: fail before output.
- Finite value at mask=false: fail output validation.
- Insufficient off-pulse samples or nonpositive gain: mask and report; never divide.

## Documentation Updates

- Update the migration implementation/validation documents without rewriting
  historical evidence.
- Add a Zach preprocessing validation report and resolve the Wayfinder task only
  after the evidence packet exists.

## References

- [Research](research-zach-chime-preprocessing-baseline.md)
- `scripts/h17_source_data_layout.py`
- `pipeline/analysis/scattering-refit-2026-06/baseband_recovery/upchannelize_chime.py`
- `pipeline/analysis/scattering-refit-2026-06/baseband_recovery/windowed_upchan.py`
- `docs/rse/specs/notes/owner-data-review-findings-2026-07-18.md`
