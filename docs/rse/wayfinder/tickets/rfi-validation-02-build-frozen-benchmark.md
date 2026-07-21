# Build the frozen CHIME RFI-validation benchmark

- Type: `wayfinder:task` (AFK)
- Status: open
- Assignee: —
- Blocked by: [Define the CHIME RFI-cleaning acceptance contract](rfi-validation-01-define-acceptance-contract.md)
- Map: [ApJ submission](../map-apj-submission.md)
- Authorization: owner request, 2026-07-21

## Question

Build the reproducible benchmark required to compare RFI cleaners under the
accepted contract, without fitting any burst science.

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
