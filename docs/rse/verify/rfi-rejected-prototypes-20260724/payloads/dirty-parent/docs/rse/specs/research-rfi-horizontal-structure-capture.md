# Research: Horizontal RFI structure capture

**Date:** 2026-07-21
**Scope:** Internal codebase and existing Zach evidence
**Codebase state:** Faber2026 `5f204398`; pipeline `ab6af1f7`
**Related Documents:**
[rejected Pixel-6 research](research-rfi-time-frequency-candidate.md),
[rejected Pixel-6 experiment](experiment-rfi-time-frequency-candidate.md),
[owner review ticket](../wayfinder/tickets/rfi-validation-01a-review-preservation-dynamic-spectrum.md)

## Question / Scope

How should the next development method identify the partially captured,
horizontally extended contaminated frequency-channel structures highlighted by
the owner, without again treating burst brightness as RFI evidence?

This pass examines current mask semantics, saved Zach diagnostics, synthetic
truth coverage, and existing repository primitives. It does not tune on Zach,
open validation or sealed intervals, or promote a cleaner.

## Codebase Findings

### The marked panel shows rejection, not surviving intensity

Pixel 6 rejects each finite, row-valid normalized pixel whose absolute value is
at least six (`scripts/rfi_time_frequency_candidate.py:17-44`). The real-event
panel reconstructs that added mask after non-wrapping alignment
(`scripts/review_real_zach_rfi_cleaner.py:597-605`). It then reports, for each
64-fine-row block and time bin, the fraction of still-valid fine rows rejected
(`scripts/review_real_zach_rfi_cleaner.py:327-342,490-508`).

Dark horizontal lines therefore mean sustained Pixel-6 rejection. A plotted
fraction near 0.07 represents only about three or four rejected fine rows in a
coarse block; it does not prove that the full contaminated structure was
captured. The aggregation also cannot show whether the same fine row persists
through time.

### Existing arrays confirm incomplete capture but not RFI identity

The checksummed Zach run saves the fine-pixel mask, row support, alignment, and
before/after on-pulse spectra (`scripts/review_real_zach_rfi_cleaner.py:515-537`).
Frequency-agnostic inspection of those arrays shows both partial masks and
surviving spectral peaks. At 738.876 MHz, Pixel 6 rejects 25% of on-pulse
samples yet leaves an integrated value of 67.97. Several 600–650 MHz peaks
survive with no Pixel-6 rejection. Zach has no known truth, so these values
motivate a failure class but cannot label every survivor as interference.

### Synthetic truth lacks the observed stationary-intermittent failure class

The generator includes persistent three-row lines, a persistent single-row
comb, a three-bin broadband impulse, and a drifting line
(`scripts/prototype_rfi_preservation_review.py:142-207`). It has no fixed
frequency channel that turns on and off, no near-threshold horizontal amplitude
evolution, and no segment-level truth measure.

Aggregate comb recovery is 98.29%, but current reporting can hide wholly missed
rows or fragmented recovery. The main path reports union-level pixel confusion
(`scripts/prototype_rfi_preservation_review.py:865-874,956-973`); the throwaway
experiment adds only per-class recall
(`.experiments/rfi-time-frequency/candidate_experiment.py:149-169`). Neither
reports per-contaminated-row completeness, longest missed run, or residual
contaminated intensity.

### Off-pulse robust row learning already exists

`pipeline/scintillation/scint_analysis/auto_rfi_flag.py` computes off-pulse
standard deviation and lag-one temporal correlation per fine-frequency row,
then iteratively flags across-row median-absolute-deviation outliers
(`auto_rfi_flag.py:37-83`). Its caller rejects overlapping off-pulse and burst
windows before learning (`pipeline/scintillation/scint_analysis/window_refit.py:331-359`).
This family targets variable or temporally correlated bad rows without using
on-pulse brightness.

The existing claim that off-pulse learning “cannot remove burst signal” is too
strong. It prevents the burst from causing the decision, but a whole-row veto
still removes real burst support at that frequency. The existing burst-bright
overlap diagnostic (`auto_rfi_flag.py:110-114`) and retained-support measures
must remain binding.

### Available structure primitives need no new dependency

The pinned container provides SciPy connected growth, component labeling, and
dilation. The rejected 6-to-4 global growth experiment demonstrates an allowed
support barrier but also shows that unconstrained growth adds false rejection
(`.experiments/rfi-time-frequency/candidate_experiment.py:24-40`). Existing
pure-NumPy helpers also compute contiguous runs and bounded growth. These are
appropriate only after off-pulse evidence classifies a channel or component;
on-pulse morphology alone cannot distinguish a burst from broadband RFI.

## Synthesis

The next development experiment should add a stationary, intermittent,
near-threshold horizontal contaminant to known truth and add three binding
structure measures:

1. recall for each contaminated fine row;
2. longest surviving contaminated run per row; and
3. residual contaminated intensity, not only mask recall.

Compare a small candidate set learned only from the frozen off-pulse window:

- the existing robust row learner using off-pulse variability and temporal
  correlation;
- an off-pulse exceedance-occupancy row learner; and
- their union, with any mask growth confined to independently classified rows.

Whole-row decisions may be applied to the display only after the configuration
is selected on synthetic truth. Pixel brightness inside the burst must never be
a seed. Every candidate must retain explicit missing-data support, preserve
unchanged values, pass every protected measurement, and bound additional clean
row loss. Zach frequency locations may be attached only after a frozen method
has selected rows without frequency-specific tuning.

The review figure must separate four quantities now conflated by the coarse
mask panel: surviving candidate intensity, exact fine-row occupancy, row-level
classification, and removed on-pulse spectrum.

## Post-research correction from Zach

The robust row learner passed the original near-threshold synthetic class but
failed the owner-marked Zach bands. Post-normalization row standard deviation
was effectively fixed at one, lag-one correlation selected only seven rows,
and the strongest residuals were unchanged. Training-tail thresholds either
missed those rows or rejected thousands of rows.

The marked panel supplied a different signal: repeated Pixel-6 seeds outside
the protected burst envelope. The follow-up experiment therefore tests
seed-to-row promotion with CHIME coarse-group recurrence and broadband-column
exclusion. See
[experiment-rfi-offpulse-seed-promotion.md](experiment-rfi-offpulse-seed-promotion.md).

### Second correction after owner review

The four-row coarse-group gate still left owner-visible horizontal saturation
in 700–750 MHz. Two independently observable misses explained it. Some fine
rows had one protected off-pulse event above six standard deviations but fewer
than four neighboring seed rows. The 720.703 MHz parent coarse channel had
raw-voltage amplitude kurtosis 4.77 median-based-spread units above the retained
population, just below the frozen cutoff of five.

The bounded revision accepts an isolated six-standard-deviation row seed only
after excluding simultaneous broadband columns, and lowers the independent
raw-voltage cutoff to 4.5. Neither change reads protected on-pulse samples or
uses the owner-marked frequency interval as configuration. Three-seed
known-truth experiments precede the repeated Zach application. The owner-marked
interval is used only for reporting and the dedicated review figure.

## References / Sources

- `scripts/rfi_time_frequency_candidate.py:17-44`
- `scripts/review_real_zach_rfi_cleaner.py:327-342,490-537,597-618`
- `scripts/prototype_rfi_preservation_review.py:142-207,865-973`
- `.experiments/rfi-time-frequency/candidate_experiment.py:24-40,149-169`
- `pipeline/scintillation/scint_analysis/auto_rfi_flag.py:37-83,110-114`
- `pipeline/scintillation/scint_analysis/window_refit.py:331-359`
