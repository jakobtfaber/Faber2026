# Plan: injection-calibrated profile-component count

**Status:** implementation-ready; scientific operating gate pending  
**Scope:** Wayfinder ticket 20; non-blocking for the current submission  
**Code authority:** `dsa110-FLITS`, not this analysis repository

## Correction to prior planning

`plan-a1-trigger-calibration.md` calibrates the number of scattering scales in
a frequency autocorrelation function. It is reusable as campaign precedent,
but cannot set the number of temporal burst-profile components. Ticket 20 must
operate on the time-frequency profile likelihood in
`scattering/scat_analysis/burstfit_joint.py`.

## Frozen implementation seam

Use `fit_joint_scattering` and its existing multi-component layout:

- compare a ladder of `(components_C, components_D)` values;
- keep the likelihood, time-frequency crop, masks, scattering model, priors,
  sampler settings, and input bytes fixed across a ladder;
- use ordered arrival-time priors and the existing minimum-separation rule;
- run fixed gain-prior variance arms `1`, `10`, and `100`;
- require mode-matched runs and reject prior rails, out-of-window components,
  unresolved component pairs, or failed reproduction receipts;
- inject truth-known temporal components through the complete production
  channelization, dispersion, scattering, noise, masking, and crop path.

The calibration grid must span both instruments, true counts represented in
the sample, signal-to-noise ratio, component width, separation in native time
bins, relative fluence, scattering time, and masked-channel fraction.
Real off-pulse backgrounds are preferred; synthetic-noise-only cells are
controls, not the sole calibration.

## Statistic and output

For each injection, compute the full evidence ladder and apply one frozen
selection rule to choose a count pair. Do not reuse the temporary
`Δln Z > 5` neighbor rule as the calibrated threshold. Record the complete
confusion matrix and overcount, undercount, and exact-recovery rates per grid
cell, with binomial confidence bounds.

The campaign writes
`faber2026-profile-component-calibration/v1`, validated by
`scripts/profile_component_calibration.py`. The validator rejects:

- frequency-autocorrelation screen-count results;
- mixed likelihoods, crops, or gain-prior arms;
- mode-mismatched or incomplete cells;
- premature manuscript count-setting authority; and
- scientific thresholds inserted before owner ratification.

## Required implementation slices in `dsa110-FLITS`

1. Add a deterministic time-frequency injection generator around the current
   joint model and preprocessing path.
2. Add a same-support evidence-ladder runner with explicit seeds and receipts.
3. Add unit tests for truth construction, ordering, separation, and identical
   comparison support.
4. Add a small synthetic campaign proving schema-valid output.
5. Run the full grid on the high-performance computing cluster.
6. Independently replay a stratified subset and inspect confusion panels.

No real burst count changes, manuscript edits, or result promotion occur in
these slices.

## Scientific gate

After the full campaign, the manuscript owner must ratify:

1. the maximum acceptable overcount rate;
2. the maximum acceptable undercount rate;
3. the supported signal-to-noise, separation, width, and masking domain; and
4. behavior outside that domain: retain visual/heuristic counts or withhold a
   count, never extrapolate silently.

Until then, the statistic remains calibration-only and ticket 20 remains
non-blocking.
