# Review the RFI preservation limits on a controlled dynamic spectrum

- Type: `wayfinder:prototype` (HITL)
- Status: open
- Assignee: Codex
- Blocked by: [Build the verified Zach CHIME preprocessing baseline](16-build-verified-zach-chime-preprocessing-baseline.md)
- Map: [ApJ submission](../map-apj-submission.md)
- Authorization: owner request, 2026-07-21

## Question

Do the proposed signal-preservation limits look scientifically appropriate
when applied to a controlled Zach dynamic-spectrum example?

Build a development-only review artifact without opening any sealed test data.
Use a burst-like injection with known truth and synthetic interference, then
show:

1. the injected truth dynamic spectrum;
2. the same injection with synthetic interference;
3. the output of the current rejected cleaner, used only as an illustrative
   candidate;
4. the output-minus-truth residual and explicit mask; and
5. concise pass/fail annotations for every proposed preservation limit.

Include the time profile and fluence by broad frequency slice beside the
dynamic spectra where needed to make hidden redistribution visible. Bind the
source, injection, random seed, code, environment, and output hashes. The
artifact is diagnostic only: it cannot validate the cleaner or admit science.

Resolution requires owner review of the figure and either acceptance or
revision of the proposed preservation limits.

## Observed-event supplement — 2026-07-21

Owner requested the candidate cleaner applied to a real sample event. The
supplement uses Zach's observed CHIME/FRB Stokes-I product. The first version at
commit `bd149c00` is invalid: it used the 5.24-ms scintillation sub-window
`[232,248)` and treated array column number as a common time coordinate.

The replacement is coherently dedispersed at the source H5
`tiedbeam_power.DM_coherent` value, `262.4359033801 pc cm^-3`, then aligned
without wraparound from each coarse channel's `fpga_count`. The independent fit
of the H5 cutout-start schedule corresponds to `263.247551 pc cm^-3`; that is a
time-coordinate property, not the coherent filter or a manuscript dispersion
measure. The aligned review shows the 14.42-ms on-pulse interval `[229,273)`
inside the 35.39-ms display `[197,305)`, with 10.49 ms of off-pulse padding on
each side. It adds a time-integrated on-pulse spectrum for visual RFI review.

Only off-pulse training columns `[55,137)` and source-context columns
`[149,305)` are loaded as numerical samples. The public validation interval and
sealed test interval remain unopened.

- Figure: [real Zach method comparison](../../verify/rfi-real-event-review-20260721/real_zach_rfi_method_comparison.svg)
- Machine record: [JSON](../../verify/rfi-real-event-review-20260721/real_zach_rfi_method_comparison.json)
- Exact script: [`review_real_zach_rfi_cleaner.py`](../../../../scripts/review_real_zach_rfi_cleaner.py)
- Remote evidence:
  `/data/Faber2026/evidence/zach-chime-rfi-review-correction-20260721/`
- Reproduction: pinned, network-disabled `baseband-analysis` container runs
  `review-1` and `review-2` have byte-identical output manifests.

Result: the cleaner retains 50,250 of 55,744 measured frequency rows and drops
5,494 rows (9.86%). On retained rows, its values equal the bandpass-only result
exactly; the maximum absolute difference is `0.0`. The visible effect is thus
support removal. Because the observed event has no known truth, this supplement
does not establish whether the removed rows are interference or signal and does
not validate the cleaner. Absolute arrival time remains uncertified.

### Owner review outcome — 2026-07-21

Rejected for revision. The owner identified obvious residual RFI between
700–750 MHz. The strongest retained on-pulse spectral row is 738.876 MHz with a
time-integrated value of 206.22, 18.39 times the retained-band median-based
spread above its median. Twenty retained rows exceed 100 and lie between
737.405–739.200 MHz.

The current candidate is therefore insufficient. Do not tune a frequency cut or
threshold on Zach: the next method must be specified independently and tested
against known truth before returning to this observed-event review.

This ticket remains open for a revised candidate and repeat owner review.

## Pixel-6 replacement attempt — 2026-07-21

The independently specified replacement retained the package row masks and
added a fixed two-dimensional mask after normalization: every finite,
row-valid pixel with absolute standardized intensity at least `6.0` became
explicit missing data. Threshold and code were frozen before Zach application.

Known-truth recovery improved to 98.69% overall, 99.66% for the broadband
impulse, and 100% for the drifting line. The candidate nevertheless failed
three protected measurements: morphology by 17.70 measurement uncertainties,
normalized residual by 14.47, and spectral modulation by 1.33. It is rejected.

On Zach, the same frozen code lowered the 700–750 MHz outlier score from 18.39
to 6.36 and removed all integrated rows above 100. The review panel also shows
that it clips the burst: the rejected-pixel mask follows the burst and the time
profile peak falls materially. This is not acceptable RFI cleaning.

- [Synthetic known-truth review](../../verify/rfi-time-frequency-candidate-20260721/synthetic/rfi_preservation_review.svg)
- [Synthetic machine record](../../verify/rfi-time-frequency-candidate-20260721/synthetic/rfi_preservation_review.json)
- [Zach rejected-candidate review](../../verify/rfi-time-frequency-candidate-20260721/zach/real_zach_rfi_method_comparison.svg)
- [Zach machine record](../../verify/rfi-time-frequency-candidate-20260721/zach/real_zach_rfi_method_comparison.json)
- Remote evidence:
  `/data/Faber2026/evidence/rfi-time-frequency-candidate-20260721/`
- Exact final reruns: `synthetic-{1,2}` and `zach-{5,6}` have byte-identical
  manifests within each pair.

The ticket remains open. Owner review may confirm the rejection visually, but
cannot promote Pixel 6. A future candidate must be specified from known truth,
not tuned on Zach.
