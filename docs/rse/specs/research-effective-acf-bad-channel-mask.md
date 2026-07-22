# Research: Effective ACF bad-channel mask

**Date:** 2026-07-22
**Scope:** internal codebase
**Code state:** parent `5f204398`; pipeline `ab6af1f`

## Question / Scope

How can every autocorrelation-function (ACF) calculation retain the channels
already unavailable before manual review while also applying only an
owner-approved manual map?

## Codebase Findings

- The manual validator currently returns only rows listed in
  `bad_row_ranges`; it validates approval and source/frequency file hashes but
  does not accept the source-valid array (`scripts/manual_bad_channels.py:34`).
- The review map already records the source-valid file SHA-256 under
  `frequency_axis.source_valid_sha256`, so the missing input can be bound
  without changing the map schema (`analysis/rfi/manual-bad-channels/chime-frb/zach.json:1`).
- The notebook-style ACF path loads a dynamic spectrum, regularizes and
  downsamples it, then performs automatic masking
  (`pipeline/scintillation/scint_analysis/freya_scintillation.py:660`). There is
  no external bad-channel authority at this boundary.
- The object-oriented ACF path has the same missing boundary before grid
  regularization (`pipeline/scintillation/scint_analysis/pipeline.py:124`).
- `DynamicSpectrum` preserves masked values during downsampling, so a verified
  full-resolution row mask must be applied before regularization and
  downsampling (`pipeline/scintillation/scint_analysis/core.py:134`).

## Synthesis

Materialize a hash-bound effective mask from the exact set union
`not source_valid OR manual_bad`. Verify that invariant before writing. At both
ACF loading boundaries, verify the mask file, provenance file, frequency-value
digest, event, instrument, and owner-approved status before applying it. A
configuration marked `required` must fail if either artifact is absent or
invalid. The current Zach draft cannot pass this gate.

## References / Sources

- `scripts/manual_bad_channels.py:34-142`
- `analysis/rfi/manual-bad-channels/README.md:1-28`
- `pipeline/scintillation/scint_analysis/freya_scintillation.py:660-698`
- `pipeline/scintillation/scint_analysis/pipeline.py:124-193`
- `pipeline/scintillation/scint_analysis/core.py:62-175`
