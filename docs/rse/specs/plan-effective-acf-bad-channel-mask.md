# Implementation Plan: Effective ACF bad-channel mask

---
**Date:** 2026-07-22
**Author:** Codex
**Status:** Complete
**Related Documents:**
- [Research](research-effective-acf-bad-channel-mask.md)
---

## Overview

Materialize and consume one effective row mask containing all pre-existing
unavailable rows plus owner-approved manual rows. Bind it to exact inputs and
fail closed at both ACF data-loading paths.

**Goal:** No Zach CHIME/FRB ACF can run without a verified effective mask, and
the mask excludes exactly the union of its two authoritative components.

## Current State Analysis

- `scripts/manual_bad_channels.py:34-104` validates and applies only manual rows.
- `pipeline/scintillation/scint_analysis/freya_scintillation.py:660-669` reaches
  automatic masking without a manual authority.
- `pipeline/scintillation/scint_analysis/pipeline.py:124-170` has the same gap.

## Desired End State

- A deterministic `.npy` mask and JSON provenance record are produced only
  from an owner-approved map whose source-valid hash matches.
- The materializer proves `effective == (~source_valid | manual)` exactly.
- Both ACF loaders verify hashes, frequency values, event, instrument, and
  approval before broadcasting the row mask.
- An authoritative artifact bypasses legacy statistical channel-row promotion;
  source masks and later non-finite/bandpass-validity masks remain active.
- Zach CHIME/FRB requires the artifact and remains blocked while its map is a
  draft.

## What We're NOT Doing

- Approving or changing the current Zach draft.
- Promoting automated RFI candidates into science support.
- Computing or accepting a new ACF result.
- Interpolating, replacing, or altering retained values.

## Implementation Approach

Use a versioned JSON provenance record beside a standard Boolean `.npy` mask.
The whole-file SHA-256 values are configured at consumption. A canonical digest
of the frequency values protects row alignment across different container
paths. Exact Boolean set equality is the correctness criterion; no numerical
tolerance or regression baseline is involved.

## Implementation Phases

### Phase 1: Materialize the exact union

- [x] Add tests in `tests/test_manual_bad_channels.py` proving the analytic set
  union, no extra rows, source-valid hash rejection, and draft rejection.
- [x] Run
  `/Users/jakobfaber/.conda/envs/py312/bin/python -m pytest tests/test_manual_bad_channels.py -q`
  and observe failure on the absent materializer.
- [x] Add `effective_bad_row_mask()` and artifact/provenance writing to
  `scripts/manual_bad_channels.py`; add `--source-valid`, `--output-mask`, and
  `--output-provenance`.
- [x] Re-run the focused test and require pass.

### Phase 2: Enforce the artifact at ACF boundaries

- [x] Add `scintillation/scint_analysis/tests/test_bad_channel_mask.py` proving
  exact masking, retained-value preservation, and rejection of missing,
  altered, misaligned, wrong-event, or unapproved artifacts.
- [x] Run the focused pipeline test and observe import failure.
- [x] Add `scintillation/scint_analysis/bad_channel_mask.py`, call it before
  regularization/downsampling from `freya_scintillation.py` and `pipeline.py`,
  bypass automatic row promotion when authoritative, and set the Zach CHIME
  config to `required: true, authoritative: true`.
- [x] Re-run focused pipeline tests and require pass.

### Phase 3: Validate and reproduce

- [x] Demonstrate each new correctness test fails under a deliberate local
  mutation, then restore it.
- [x] Run both focused suites and the existing ACF/config suites.
- [x] Repeat the focused suites in a fresh temporary virtual environment using
  the repository dependency specification.
- [x] Write implementation and validation records with exact commands.

## Success Criteria

### Automated Verification

- [x] Parent focused tests pass.
- [x] Pipeline focused and affected ACF tests pass.
- [x] Zach CHIME preparation fails with a clear missing-artifact error while
  the map remains draft.
- [x] Deliberately removing one source-invalid row from the union makes the
  invariant test fail.

### Manual Verification

None for the mechanism. Owner approval of the five current Zach draft ranges is
a separate scientific gate and remains pending.

### Reproducibility & Correctness

- [x] Criterion: exact Boolean equality to the analytic union; no tolerance.
- [x] Inputs and outputs carry file hashes and a canonical frequency digest.
- [x] Minimal clean-environment reproduction passes.

## Testing Strategy

Small synthetic Boolean arrays provide a complete analytic reference. File
tampering and metadata mismatches exercise fail-closed behavior. Existing ACF
tests check integration regressions.

## Migration Strategy

Only Zach CHIME is activated now. After owner approval, materialize its
artifact and add the two expected hashes to its config. Other events opt in as
their maps are reviewed.

## Risk Assessment

- Mask applied after downsampling: high impact; prevented by applying at load.
- Wrong-event reuse: high impact; prevented by event/instrument checks.
- Draft science use: high impact; prevented at materialization and consumption.

## Edge Cases and Error Handling

Missing files, wrong dtype/shape, altered hashes, frequency reversal/drift,
wrong event/instrument, unapproved status, and empty manual selections all have
explicit behavior. An empty manual selection is valid only after owner approval;
source-unavailable rows still remain masked.

## Performance Considerations

One Boolean row mask is loaded once per preparation; cost is negligible beside
dynamic-spectrum loading.

## Documentation Updates

- [x] Update the manual-map README with materialization and ACF use.

## References

- [Research](research-effective-acf-bad-channel-mask.md)
- `scripts/manual_bad_channels.py`
- `pipeline/scintillation/scint_analysis/freya_scintillation.py`
- `pipeline/scintillation/scint_analysis/pipeline.py`

## Review History

### Version 1.0 — 2026-07-22

- Direct-mode plan accepted by the user’s instruction to plan and implement now.
