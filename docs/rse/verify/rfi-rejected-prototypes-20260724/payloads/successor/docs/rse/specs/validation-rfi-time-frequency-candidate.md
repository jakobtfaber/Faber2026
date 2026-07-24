# Validation Complete

> Validated against `plan-rfi-time-frequency-candidate.md` and
> `implement-rfi-time-frequency-candidate.md` in the task-scoped working tree
> based on commit `4980c36d` on 2026-07-21.

## Overall Status: Issues found

- Phases: 3 of 3 implemented.
- Automated checks: 8 passing, 0 failing.
- Manual checks: 1 owner visual review remains.
- Critical implementation issues: 0.
- Important scientific issues: 1; candidate clips burst signal and is rejected.

## Implementation Status

### Phase 1: Lock mask semantics

**Status:** Fully implemented.

- Exact threshold boundary, missing-data behavior, value preservation, input
  immutability, and invalid input are tested.
- Rejected pixels become `NaN`; retained values are unchanged.

### Phase 2: Rebuild synthetic known-truth review

**Status:** Fully implemented.

- The shared two-dimensional mask is applied after the package row masks.
- Measurements use common finite-pixel support.
- Synthetic runs `synthetic-1` and `synthetic-2` have identical manifests.

### Phase 3: Apply frozen candidate to Zach

**Status:** Fully implemented.

- Threshold `6.0` was unchanged.
- Coherent dispersion measure, time alignment, windows, and training slice were
  unchanged.
- Final runs `zach-5` and `zach-6` have identical manifests.
- The review includes three dynamic spectra, the burst profile, on-pulse
  spectrum, explicit pixel mask, and rejected-candidate warning.

## Automated Verification Results

All automated implementation checks passed:

- `pytest` on the three focused files: 22 passed.
- `py_compile` on changed scripts and tests: passed.
- Local four-file evidence checksum verification: passed.
- Both JSON records parse: passed.
- `git diff --check`: passed.
- Remote synthetic manifest comparison: identical.
- Remote final Zach manifest comparison: identical.
- Numerical plan assertions: passed, including 98.69% overall RFI recovery,
  99.66% broadband-impulse recovery, 100% drifting-line recovery, at most 0.2%
  added clean-pixel rejection, fixed threshold `6.0`, and Zach outlier score
  below 10.

## Code Review Findings

### What matches the plan

- One shared development-only module supplies the threshold and mask semantics.
- Both integrations copy and hash the exact shared module.
- No interpolation or zero replacement is introduced.
- Observed public-validation and sealed-test intervals remain unopened.
- Figures and records state that this is not cleaner validation.

### Deviations from the plan

- Final Zach repeat directories are `zach-5` and `zach-6`, not `zach-1` and
  `zach-2`. Earlier pairs were retained while the rejection warning layout was
  corrected. Impact: none; the final pair is exact and reproducible.

### Important scientific finding

The method is invalid as a cleaner. Its threshold was justified using a
pre-normalization injected amplitude but applied to post-normalization values.
Normalized burst pixels exceed six and are removed. Synthetic morphology,
normalized residual, and spectral modulation fail by 17.70, 14.47, and 1.33
measurement uncertainties. The Zach profile and mask show the same failure.

## Manual Testing Required

1. Owner views the Zach panel and confirms that the mask follows burst signal
   and the profile peak falls. Expected outcome: confirm rejection only. This
   review cannot promote Pixel 6.

## Recommendations

### Critical

- None for preserving this diagnostic implementation and failure record.

### Important

- Do not merge or invoke Pixel 6 as a science cleaner.
- Define the next candidate's protection logic on its actual operating scale,
  then test on known truth before any Zach application.

### Follow-up

- Keep the Wayfinder preservation-review ticket open.
- Continue later benchmark, comparison, and blind-validation tickets only after
  a candidate passes every protected measurement.

## References

- [Plan](plan-rfi-time-frequency-candidate.md)
- [Implementation](implement-rfi-time-frequency-candidate.md)
- [Experiment](experiment-rfi-time-frequency-candidate.md)
- [Wayfinder ticket](../wayfinder/tickets/rfi-validation-01a-review-preservation-dynamic-spectrum.md)
