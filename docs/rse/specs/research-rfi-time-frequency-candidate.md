# Research: Time-frequency RFI candidate

**Date:** 2026-07-21
**Scope:** Internal codebase and pinned h17 container
**Codebase state:** Faber2026 `4980c36d`; pipeline `ab6af1f7`
**Related Documents:**
[controlled prototype](research-rfi-preservation-dynamic-spectrum-prototype.md),
[real-event diagnosis](research-real-zach-rfi-review-correction.md),
[owner review ticket](../wayfinder/tickets/rfi-validation-01a-review-preservation-dynamic-spectrum.md)

## Question / Scope

What independently specified replacement can detect the time-local RFI that
survived the package's whole-frequency-row mask, while preserving an explicit
missing-data mask and avoiding tuning on Zach's observed burst?

This pass covers the current synthetic known-truth prototype, the corrected
real-event review seam, and primitives available in the pinned container. It
does not open public validation or sealed test intervals, select a production
cleaner, or promote any result to science use.

## Codebase Findings

### The package detector can reject only complete frequency rows

The exact package path calculates a mean and standard deviation for every
frequency row over the caller's training interval, then returns one Boolean per
row. The prototype broadcasts that decision across every time sample
(`scripts/prototype_rfi_preservation_review.py:311-360`). The real-event path
also learns both row masks only from the off-pulse training interval
(`scripts/review_real_zach_rfi_cleaner.py:171-224`). It has no representation
for an intermittent bad pixel.

### The existing synthetic truth exercises the missing behavior

The controlled generator includes persistent lines, a 64-fine-channel comb, a
three-bin broadband impulse, and a drifting line with exact truth masks
(`scripts/prototype_rfi_preservation_review.py:134-199`). The row-only baseline
recovered 73.99% of injected RFI pixels, but only 20.93% of rejected pixels were
true RFI; the broadband impulse survived. This is sufficient for a development
comparison without touching observed intensity or sealed benchmark data.

### The integration seam already preserves values and missing-data semantics

Bandpass normalization produces standardized samples after off-pulse training
(`scripts/prototype_rfi_preservation_review.py:311-345`). Coarsening averages
only finite values and never fills a rejected value with zero
(`scripts/prototype_rfi_preservation_review.py:364-388`). A pixel detector can
therefore operate after normalization and add a two-dimensional Boolean mask;
its only data mutation is setting explicitly rejected pixels to `NaN`.

The corrected Zach review separately aligns channel time coordinates before
forming its display and one-dimensional spectrum
(`scripts/review_real_zach_rfi_cleaner.py:516-532`). The same frozen pixel-mask
function can be applied after that alignment without changing the coherent
dispersion measure, time coordinate, or review window.

### Required primitive is present in both environments

Local SciPy 1.17.1 and pinned-container SciPy 1.16.0 both provide
`scipy.ndimage.binary_propagation`. This permits connected growth from strong
outlier seeds through adjacent weaker outliers without adding a dependency.

## Synthesis

Compare three candidates on synthetic known truth only:

1. the current training-derived whole-row mask;
2. that row mask plus independent pixels with absolute standardized intensity
   at least 6;
3. that row mask plus connected growth from pixels at least 6 through
   eight-connected pixels at least 4.

The thresholds are fixed before any Zach application. Six is a high seed level
relative to the synthetic burst's maximum signal amplitude of 2.8; four is only
eligible when connected to a six-level seed. The comparison must report RFI
pixel recall and precision, false rejection of interference-free truth, and all
protected measurement shifts already used by the controlled prototype.

If a candidate qualifies on synthetic truth, freeze its thresholds and code
hash before applying it to the already authorized Zach training/context slices.
The Zach result remains diagnostic-only because burst-coincident narrow
structure has no known truth. A successful visual review resolves only the
preservation-limit prototype ticket; cleaner selection and blind validation
remain later tickets.

## Post-application correction

The amplitude argument above was wrong. The injected maximum of 2.8 is on the
pre-normalization scale, while Pixel 6 acts on values divided by an off-pulse
frequency-row scale. The normalized burst contains values above six. The full
known-truth panel and Zach mask therefore show the candidate clipping bright
burst pixels. This scale mismatch explains the failed morphology and residual
checks and rejects the method. A replacement must define its signal-protection
logic on the actual operating scale.

## References / Sources

- `scripts/prototype_rfi_preservation_review.py:134-199,311-388`
- `scripts/review_real_zach_rfi_cleaner.py:171-224,516-532`
- `docs/rse/specs/experiment-rfi-preservation-dynamic-spectrum-prototype.md`
- Pinned container:
  `chimefrb/baseband-analysis@sha256:f510909d892d0d5224c982c590cbe80967a49a59b79c396ab72bb710105c4c41`
