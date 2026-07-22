# Research: CHIME/FRB RFI acceptance contract

**Date:** 2026-07-22
**Scope:** internal codebase and preserved project evidence
**Codebase state:** Faber2026 `e1c46097`; pipeline `5a49278`
**Related Documents:**
[acceptance ticket](../wayfinder/tickets/rfi-validation-01-define-acceptance-contract.md),
[owner-review ticket](../wayfinder/tickets/rfi-validation-01a-review-preservation-dynamic-spectrum.md),
[Zach preprocessing validation](validation-zach-chime-preprocessing-baseline.md)

## Question / Scope

Define the fail-closed evidence and numerical limits required before any
additional automated CHIME/FRB radio-frequency-interference (RFI) mask may feed
burst, scattering, or scintillation measurements. Reconcile that contract with
the later owner decision that manual channel maps, not automated row promotion,
are the current channel-row authority.

## Codebase Findings

The project vocabulary already separates padded, bandpass-corrected,
RFI-masked, RFI-validated, and science-admissible states. A mask is not validated
merely because it was applied (`CONTEXT.md:79-98`).

The Zach baseline establishes the nominal 65,536-row grid, with 55,744 measured
rows and 9,792 explicit missing rows. Missing data remain `NaN`; padding does not
create measurements (`docs/rse/specs/validation-zach-chime-preprocessing-baseline.md:121-125`).
The same audit rejects the package RFI routine: training-half mask overlap was
only 0.649, while bandpass gains varied by roughly 29% between halves
(`docs/rse/specs/validation-zach-chime-preprocessing-baseline.md:214-234`).
Bandpass stability and RFI removal must therefore remain separate gates.

The first real Zach candidate removed 9.86% of measured rows but left strong
residual RFI near 738 MHz; real data alone could not determine whether removed
support was interference or signal
(`docs/rse/wayfinder/tickets/rfi-validation-01a-review-preservation-dynamic-spectrum.md:62-79`).
The pixel-threshold replacement recovered 98.69% of synthetic contamination but
failed protected morphology, residual, and spectral-modulation measurements
(`docs/rse/wayfinder/tickets/rfi-validation-01a-review-preservation-dynamic-spectrum.md:83-98`).
Removal recall alone is therefore insufficient.

Later automated row candidates either missed owner-visible residuals or removed
broad frequency blocks and were rejected
(`docs/rse/wayfinder/tickets/rfi-validation-01a-review-preservation-dynamic-spectrum.md:113-195`).
The accepted policy instead makes hash-bound, owner-approved manual maps the
sole channel-row authority; retained values remain exact and selected rows
become explicit missing data
(`docs/rse/wayfinder/tickets/rfi-validation-01a-review-preservation-dynamic-spectrum.md:198-212`).
Zach's approved effective mask contains 9,792 source-unavailable rows plus 490
manual rows, with zero overlap
(`docs/rse/wayfinder/tickets/rfi-validation-01a-review-preservation-dynamic-spectrum.md:230-250`).

A one-dimensional channel map cannot address diagonal or time-local
interference without erasing the full swept band
(`docs/rse/wayfinder/tickets/rfi-validation-01a-review-preservation-dynamic-spectrum.md:226-228`).
That residual class must be tested through measurement stability before an
additional automated cleaner becomes necessary.

## Synthesis

Manual maps are the current science authority for stationary channel rows.
Automated cleaner development is conditional, not a prerequisite for later ACF
work. ACF preprocessing is not the immediate gate. The Zach analysis must first
identify and verify both instruments' original products and time axes, fit and
adopt the dual-band dispersion measures, then build standardized dynamic
spectra, complete the applicable manual masks, and validate the two-dimensional
burst fits. Only then may the approved effective mask feed an
autocorrelation-function (ACF) check for residual time-local bias.

Any later automated time-frequency mask must pass all predeclared limits:

- learn from no protected burst sample and alter no retained value;
- on interference-free injections, produce median measurement shifts no larger
  than 0.25 measurement uncertainty, 95% no larger than 0.5, and none larger
  than 1;
- on contaminated injections, keep at least 95% of measurements within one
  uncertainty of truth and median systematic offset no larger than 0.25;
- preserve detection status and component count away from predeclared decision
  boundaries;
- remove at least 99% of each contaminant class and leave at most 1% of its
  injected contaminated intensity;
- remove at most 0.2% of injected burst support, 0.1% of clean-control samples,
  and zero complete clean channel rows;
- achieve at least 0.90 training-half Jaccard overlap for stationary-row masks;
- keep protected measurements from each half within 0.5 uncertainty of truth
  and of the other half;
- pass separately for narrow-band, broadband, impulsive, and drifting
  contamination on a sealed Zach interval plus one interference-heavy and one
  relatively quiet untouched CHIME H5 file.

One binding failure is a no-go. Visual review may veto a numerical pass but may
not override a numerical failure. Test data are consumed once opened; retuning
requires new untouched data. The compact owner surface for each case contains
before/after dynamic spectra, the explicit mask, time-integrated spectrum, time
profile, retained fraction, and a concise pass/fail table.

## References / Sources

- [`CONTEXT.md:79`](../../../CONTEXT.md)
- [`validation-zach-chime-preprocessing-baseline.md:121`](validation-zach-chime-preprocessing-baseline.md)
- [`rfi-validation-01a-review-preservation-dynamic-spectrum.md:62`](../wayfinder/tickets/rfi-validation-01a-review-preservation-dynamic-spectrum.md)
