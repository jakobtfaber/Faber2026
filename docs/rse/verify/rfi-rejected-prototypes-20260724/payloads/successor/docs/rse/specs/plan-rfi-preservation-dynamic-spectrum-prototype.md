# Implementation Plan: RFI preservation dynamic-spectrum prototype

---
**Date:** 2026-07-21
**Author:** Codex
**Status:** In Progress — automated work complete; owner visual review pending
**Related Documents:**
- [Research](research-rfi-preservation-dynamic-spectrum-prototype.md)
- [Owner review ticket](../wayfinder/tickets/rfi-validation-01a-review-preservation-dynamic-spectrum.md)
---

## Overview

Build one deterministic, development-only figure showing known burst truth,
known synthetic radio-frequency interference (RFI), the exact rejected cleaner,
and cleaner-induced signal damage. Run on h17 in the pinned baseband-analysis
container. Keep sealed data unopened.

**Goal:** Give the owner enough visual and numerical evidence to accept or
revise the tentative signal-preservation limits.

**Motivation:** The existing audit collapses time and cannot show whether a
cleaner removes or distorts a burst.

## Current State Analysis

- `pipeline/analysis/scattering-refit-2026-06/baseband_recovery/audit_chime_preprocessing.py:55-107`
  wraps the package cleaner and learns a per-channel mean and scale.
- `pipeline/analysis/scattering-refit-2026-06/baseband_recovery/audit_chime_preprocessing.py:249-280`
  defines the rejected RFI then bandpass then RFI order.
- `pipeline/dispersion/dm_campaign/injection.py:61-125` provides the existing
  dispersed, scattered, multi-component injection model.
- `docs/rse/verify/zach-chime-preprocessing-20260721/zach_chime_preprocessing_metadata.json:1`
  records the 1,024-channel nominal grid and 871 measured coarse channels.

The present figure shows held-out frequency summaries only. It cannot reveal
time-local interference, surviving interference, or burst-shape damage.

## Desired End State

One SVG shows fixed-scale panels for known truth, contaminated input, rejected
cleaner output, residual, categorical masks, time profiles, and fluence in eight
fixed broad frequency slices. A JSON record binds every input hash, parameter,
metric, command, code revision, container digest, and output hash.

Success means the figure is reproducible, readable, and explicitly marked
`development_only_not_cleaner_validation`.

## What We're NOT Doing

- Opening Zach's real burst interval or any sealed test data.
- Selecting or validating a replacement cleaner.
- Running dispersion, scattering, or scintillation science fits.
- Treating one synthetic example as a median or 95th-percentile benchmark.
- Adding the prototype figure to the manuscript.

These belong to later frozen-benchmark and blind-test tickets.

## Implementation Approach

Create a self-contained prototype script in the parent repository. It will load
only the five hash-whitelisted development inputs, generate synthetic truth with
a fixed seed, apply known RFI, call the package cleaner at mean=5 and standard
deviation=3, and reproduce the rejected two-pass order. Missing grid positions
remain `NaN` and render gray.

Key decisions:

1. **Known synthetic truth.** Observed Zach intensity is not truth.
2. **Full fine grid.** Cleaner behavior is tested on 65,536 nominal positions;
   plotting alone averages to coarse channels.
3. **Bandpass shape does not define source support.** Cleaner-induced `NaN`
   rows in the development bandpass arrays are linearly interpolated only to
   shape synthetic raw data; the independent source-valid mask remains exact.
4. **Separate support loss from value distortion.** No masked pixel becomes
   zero during measurement.
5. **One-example annotations are illustrative.** Distribution limits remain
   tentative until the frozen benchmark.

## Implementation Phases

### Phase 1: Deterministic truth and contamination

**Objective:** Establish testable numerical invariants before plotting.

**Automated status:** Complete.

- Add `tests/test_prototype_rfi_preservation_review.py:1` with assertions that
  fixed-seed generation is byte-identical, source-missing pixels are `NaN`, the
  burst has two components, and every contamination class sets its truth mask.
- Run `python3 -m pytest -q tests/test_prototype_rfi_preservation_review.py` and
  observe import/test failure before implementation.
- Add `scripts/prototype_rfi_preservation_review.py:1` with explicit
  `SeedSequence` children, dispersed Gaussian components with exponential
  tails, and persistent-line, broadband-impulse, drifting-line, and comb RFI.
- Rerun the same test; require all assertions to pass.

**Dependencies:** NumPy and SciPy already present in the pinned container.

### Phase 2: Exact rejected cleaning and measurements

**Objective:** Reproduce the rejected cleaner order without importing sealed
or observed intensity data.

**Automated status:** Complete.

- Extend the test with analytic mask-confusion counts, bandpass round-trip, and
  finite-common-support measurement assertions; run and observe failure.
- Implement the audit's package mask, bandpass model, normalization, final
  row mask, mask confusion, profiles, broad-slice fluence, arrival centroid,
  width, component separation, dispersion slope, morphology correlation,
  tail proxy, spectral modulation, and frequency-autocorrelation proxy.
- Run the unit test and require all assertions to pass.
- Run the script in the pinned container against read-only whitelisted inputs.

**Dependencies:** Phase 1 and the exact container digest.

### Phase 3: Review artifact and reproduction

**Objective:** Produce a deterministic owner-review packet.

**Automated status:** Complete. Manual owner review remains open.

- Add a failing integration assertion that output status, hashes, fixed seed,
  cleaner thresholds/order, metrics, and figure panels exist.
- Implement one deterministic SVG, JSON record, and `SHA256SUMS`; suppress SVG
  timestamps and set a fixed SVG hash salt.
- Run twice into separate empty directories with identical inputs and compare
  JSON semantic content plus SVG and parameter hashes.
- Copy only the SVG, JSON, checksums, run log, and exact script into
  `docs/rse/verify/rfi-preservation-prototype-20260721/`; verify checksums.

**Dependencies:** Phase 2.

## Success Criteria

### Automated Verification

- `python3 -m pytest -q tests/test_prototype_rfi_preservation_review.py` passes.
- All five h17 input hashes match the plan before execution.
- Container image ID is
  `sha256:8c903ec6a5a836e8a97fe3468fd3ee02177c220ead84e6d1d25e8f41b735db4b`.
- Two clean runs have matching deterministic artifact hashes.
- `sha256sum -c SHA256SUMS` passes remotely and locally.
- `git diff --check` passes.

### Manual Verification

- Owner can distinguish truth, contamination, cleaner output, and residual.
- Missing input, true RFI, rejected rows, false positives, and false negatives
  are distinguishable.
- Time-profile and broad-frequency-fluence changes are readable.
- Figure wording does not imply cleaner validation or science acceptance.

### Reproducibility & Correctness

- Seed, independent random streams, inputs, code, container, and command are in
  JSON.
- Bandpass application followed by oracle normalization reproduces the
  standardized synthetic float32 array within `5e-6` on valid finite support.
- Second clean run reproduces deterministic outputs.

## Testing Strategy

Unit tests cover fixed-seed generation, missing-data semantics, RFI truth masks,
bandpass inversion, confusion accounting, and finite-support metrics. The h17
integration test exercises the actual package cleaner. Manual review is limited
to figure legibility and interpretation.

## Migration Strategy

No migration. This is a throwaway prototype branch. The accepted decision, not
the prototype code, will be folded into the Wayfinder ticket. Deleting the
separate output root rolls back the remote run without touching baseline data.

## Risk Assessment

1. **Writable baseline evidence:** rehash every input immediately before use;
   mount the evidence root read-only.
2. **Cleaner implementation confusion:** call only
   `baseband_analysis.core.flagging.get_RFI_channels` in the pinned image.
3. **Single-example overclaim:** label every output development-only and retain
   the later distribution benchmark.
4. **Mask-as-zero bias:** use `NaN` and explicit support masks throughout.

## Edge Cases and Error Handling

- Hash mismatch: stop before generation.
- Existing output directory: stop rather than overwrite.
- Nonpositive bandpass scale or missing source row: mark invalid.
- Empty frequency slice or insufficient common support: return `null`, not zero.
- Package cleaner failure: preserve log and emit no review artifact.

## Performance Considerations

Use float32 for 65,536 by 512 dynamic spectra and boolean masks. Plot only
64-row coarse averages. Expected peak memory is below 2 GiB.

## Documentation Updates

- Store the prototype research, plan, figure, JSON, checksums, and experiment
  record on the throwaway branch.
- Record only the owner's accepted or revised limits in the Wayfinder ticket.

## References

- [Prototype research](research-rfi-preservation-dynamic-spectrum-prototype.md)
- [Baseline validation](validation-zach-chime-preprocessing-baseline.md)
- [Owner review ticket](../wayfinder/tickets/rfi-validation-01a-review-preservation-dynamic-spectrum.md)
- `pipeline/analysis/scattering-refit-2026-06/baseband_recovery/audit_chime_preprocessing.py`
- `pipeline/dispersion/dm_campaign/injection.py`
