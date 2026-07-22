# Build the frozen CHIME RFI-validation benchmark

- Type: `wayfinder:task` (AFK)
- Status: deferred — conditional, not on the current critical path
- Assignee: —
- Triggered by: a no-go from [Validate the approved Zach manual map in ACF preprocessing](rfi-validation-02a-validate-zach-manual-map-acf.md) attributable to residual time-local RFI
- Map: [ApJ submission](../map-apj-submission.md)
- Authorization: owner request, 2026-07-21

## Question

Build the reproducible benchmark required to compare RFI cleaners under the
accepted contract, without fitting any burst science.

This ticket does not govern stationary channel rows; owner-approved manual maps
remain their sole authority. Activate this benchmark only if the manual-map ACF
check demonstrates measurement bias from residual diagonal or time-local RFI.

The benchmark must bind source hashes, container and code identities, channel
maps, masks, time/frequency resolutions, and bandpass inputs. It must separate
tuning, validation, and untouched test data before method comparison. Include:

- real off-pulse intervals with distinct interference conditions;
- synthetic narrow-band, broad-band, impulsive, and drifting contaminants with
  known truth;
- protected burst-like injections spanning relevant widths and spectra;
- no-cleaning, bandpass-only, and current-package baselines; and
- deterministic metrics and compact before/after dynamic-spectrum panels.

Padded channels remain missing data, never zero-valued measurements. Resolution
requires a checksummed evidence packet and a command that reproduces every
benchmark input and expected baseline result.
