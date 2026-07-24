# Implementation Summary: Time-frequency RFI candidate

---
**Date:** 2026-07-21
**Author:** Codex
**Status:** Implementation complete; candidate rejected
**Plan Reference:** [plan](plan-rfi-time-frequency-candidate.md)
---

## Overview

Implemented the frozen Pixel-6 development candidate and applied it to the
synthetic known-truth case and corrected Zach CHIME/FRB product. The method adds
an explicit two-dimensional mask after the existing package row masks and
bandpass normalization. Rejected samples become `NaN`; retained values are not
changed.

The implementation is reproducible. The scientific candidate is not accepted:
it removes injected interference but also removes burst structure.

## Plan Adherence

All three implementation phases are complete. The threshold remained `6.0`
before and after Zach application. Public validation and sealed test intervals
were not opened. The corrected coherent dispersion measure, time alignment,
display interval, on-pulse interval, and training slice were unchanged.

One presentation-only correction followed the first exact Zach pair: the final
panel now labels the candidate as rejected in a layout-managed header. Final
runs `zach-5` and `zach-6` include that exact script and match byte-for-byte.

## Files

- `scripts/rfi_time_frequency_candidate.py` — frozen mask construction and
  explicit missing-data application.
- `scripts/prototype_rfi_preservation_review.py` — known-truth integration,
  common-pixel measurements, mask accounting, and panel.
- `scripts/review_real_zach_rfi_cleaner.py` — frozen Zach application,
  time-frequency mask panel, profile, spectrum, and 700–750 MHz diagnostic.
- `tests/test_rfi_time_frequency_candidate.py` — threshold, missing-data,
  immutability, and shape tests.
- `tests/test_prototype_rfi_preservation_review.py` — pixel-mask integration.
- `tests/test_review_real_zach_rfi_cleaner.py` — common support, outlier score,
  mask coarsening, and frozen-threshold tests.
- `docs/rse/verify/rfi-time-frequency-candidate-20260721/` — review packet.

## Results

Synthetic RFI-pixel recovery reached 98.69% overall, 99.66% for the broadband
impulse, and 100% for the drifting line. The candidate failed morphology,
normalized-residual, and spectral-modulation preservation by 17.70, 14.47, and
1.33 measurement uncertainties, respectively.

On Zach, the frozen candidate reduced the 700–750 MHz outlier score from 18.39
to 6.36 median-based spread units. The apparent improvement is not acceptable:
the mask follows the burst and lowers its profile peak. The panel says
explicitly that the candidate is rejected and not valid for science use.

## Reproducibility

- Container:
  `chimefrb/baseband-analysis@sha256:f510909d892d0d5224c982c590cbe80967a49a59b79c396ab72bb710105c4c41`
- Network disabled for all container runs.
- Remote evidence:
  `/data/Faber2026/evidence/rfi-time-frequency-candidate-20260721/`
- Synthetic runs `synthetic-1` and `synthetic-2`: byte-identical manifests.
- Final Zach runs `zach-5` and `zach-6`: byte-identical manifests.
- Candidate module SHA-256:
  `ca947385262e72e354c43681f6cf8bc3103ca152cbf2d6d800fbb54eb9873e73`.
- Final Zach script SHA-256:
  `76f573c29410b8057bd1079829071bb40f7fa11b8eeeb1575dd5f9c7e5f1f7b1`.

## Remaining Work

- Owner may confirm the rejection visually; this does not authorize promotion.
- Specify the next candidate from synthetic known truth or the later frozen
  benchmark. Do not tune it on Zach.
- The Wayfinder ticket remains open because no preservation-safe cleaner has
  been demonstrated.

## References

- [Research](research-rfi-time-frequency-candidate.md)
- [Experiment](experiment-rfi-time-frequency-candidate.md)
- [Plan](plan-rfi-time-frequency-candidate.md)
- [Owner review ticket](../wayfinder/tickets/rfi-validation-01a-review-preservation-dynamic-spectrum.md)
