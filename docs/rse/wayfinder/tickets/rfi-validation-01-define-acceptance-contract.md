# Define the CHIME RFI-cleaning acceptance contract

- Type: `wayfinder:grilling` (HITL)
- Status: open
- Assignee: Codex
- Blocked by: [Build the verified Zach CHIME preprocessing baseline](16-build-verified-zach-chime-preprocessing-baseline.md)
- Map: [ApJ submission](../map-apj-submission.md)
- Authorization: owner request, 2026-07-21

## Question

What evidence and numerical limits must a CHIME radio-frequency-interference
(RFI) cleaner satisfy before its products may feed burst, scattering, or
scintillation measurements?

Set the fail-closed contract before testing replacements. At minimum, decide:

1. which contamination-removal, false-removal, retained-data, and
   time-split-stability measures are binding;
2. which injected signals and protected burst features must survive, and how
   closely their fluence, width, spectrum, and time-frequency structure must
   be preserved;
3. which evidence must come from data withheld from all tuning;
4. whether acceptance is Zach-only or also requires untouched raw CHIME files
   with different interference conditions; and
5. which compact figures the owner must inspect before ratification.

The contract must distinguish bandpass flattening from RFI removal, require
explicit masks for missing or rejected samples, and forbid calling a product
"clean" merely because its collapsed spectrum is smoother.

## Decisions — in progress

- **Vocabulary accepted 2026-07-21:** `padded`, `bandpass-corrected`,
  `RFI-masked`, `RFI-validated`, and `science-admissible preprocessing` are
  distinct states. Unqualified `clean` is forbidden. Definitions are recorded
  in [`CONTEXT.md`](../../../CONTEXT.md).
- **Validation scope accepted 2026-07-21:** tune only on Zach training and
  validation intervals; blind-test the frozen method on Zach's sealed test
  interval and two preselected untouched raw CHIME files representing
  interference-heavy and relatively quiet conditions. Science admissibility
  attaches only to the exact processing configuration and tested data scope.
  Full-sample execution remains a later campaign.
- **Data sealing accepted 2026-07-21:** use contiguous time blocks separated
  by a guard interval longer than the measured time correlation; hash and
  publish all splits before cleaner comparison. Freeze method, ordering, and
  thresholds before viewing test outputs. Only predeclared per-file estimates
  from designated off-pulse data are allowed. A failed blind test consumes the
  test data; another attempt requires new untouched test data.
- **Protected measurements accepted 2026-07-21:** injected-signal tests must
  preserve total fluence; fluence by broad frequency slice; time of arrival;
  burst width; component count and separation; dispersion measure;
  two-dimensional time-frequency morphology; scattering-tail timescale; and
  the frequency autocorrelation, modulation strength, and decorrelation
  bandwidth used for scintillation analysis.
