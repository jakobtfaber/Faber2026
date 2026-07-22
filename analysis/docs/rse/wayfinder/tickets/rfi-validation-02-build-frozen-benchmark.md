# Build the frozen CHIME RFI-validation benchmark

- Type: `wayfinder:task` (AFK)
- Status: open
- Assignee: —
- Blocked by: [Stabilize and qualify the CHIME bandpass model](rfi-validation-01b-stabilize-bandpass-model.md)
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

Padded channels remain missing data, never zero-valued measurements. Generate
reproducible baseline results and panels only for tuning and validation inputs.
For Zach's sealed test interval and both untouched raw CHIME test files, record
only hashes and manifests until blind validation.

Resolution requires a checksummed evidence packet and a command that
reproduces every tuning and validation input and expected baseline result while
leaving all test outputs sealed.
