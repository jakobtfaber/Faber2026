# Define the CHIME RFI-cleaning acceptance contract

- Type: `wayfinder:grilling` (HITL)
- Status: closed — accepted 2026-07-22
- Assignee: Codex
- Blocked by: [Review the RFI preservation limits on a controlled dynamic spectrum](rfi-validation-01a-review-preservation-dynamic-spectrum.md)
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
- **Signal-preservation limits tentatively accepted 2026-07-21:** on
  interference-free injections, median cleaner-induced shift no greater than
  0.25 measurement uncertainty, 95% no greater than 0.5, and none greater than
  1; on contaminated injections, at least 95% within 1 uncertainty of truth
  and median systematic offset no greater than 0.25. Detection status and
  component count must remain unchanged away from predeclared decision
  boundaries. Final acceptance is blocked on the controlled dynamic-spectrum
  review.

## Resolution — accepted 2026-07-22

The owner accepted the following fail-closed contract after reviewing Zach's
approved manual-map artifact. Supporting synthesis:
[research-chime-rfi-acceptance-contract.md](../../specs/research-chime-rfi-acceptance-contract.md).

### Authority and invariants

- Owner-approved manual maps are the sole channel-row authority.
- Automated diagnostics cannot promote channel rows into science masks.
- Every rejected sample remains explicit missing data; retained values remain
  byte-exact. Interpolation and zero-filling are forbidden.
- No cleaner may learn from a protected burst window.
- Bandpass validation is a separate prerequisite; RFI validation cannot certify
  an unstable bandpass model.

### Binding limits

- Clean injections: median measurement shift no greater than 0.25 measurement
  uncertainty; 95% no greater than 0.5; none greater than 1.
- Contaminated injections: at least 95% of measurements within one uncertainty
  of truth; median systematic offset no greater than 0.25.
- Detection status and component count remain unchanged away from predeclared
  decision boundaries.
- Each narrow-band, broadband, impulsive, and drifting contaminant class: at
  least 99% recovered and at most 1% of injected contaminated intensity left.
- False removal: at most 0.2% of injected burst support, at most 0.1% of
  clean-control samples, and zero complete clean channel rows.
- Stationary-row masks: training-half Jaccard overlap at least 0.90.
- Protected measurements from each half remain within 0.5 uncertainty of truth
  and of the other half.

The protected set remains: total fluence; broad-sub-band fluence; time of
arrival; burst width; component count and separation; dispersion measure;
two-dimensional morphology; scattering-tail timescale; frequency ACF;
modulation strength; and decorrelation bandwidth.

### Blind scope and verdict rule

Blind evidence must include a sealed Zach interval plus one interference-heavy
and one relatively quiet untouched CHIME H5 file. Limits apply per contaminant
class and per file, not only in aggregate. One binding failure is a no-go.
Visual review may veto a numerical pass but cannot override a numerical fail.
Opening test data consumes them; retuning requires new untouched data.

Each owner-review surface contains before/after dynamic spectra, explicit mask,
time-integrated spectrum, time profile, retained fraction, and a concise
pass/fail table.

### Revised critical path

Automated-cleaner development is conditional. ACF work follows the foundational
Zach sequence: verify original DSA-110 and CHIME/FRB products and time axes; fit
and adopt the dual-band dispersion measures; build standardized dynamic spectra;
complete the applicable manual masks; and validate the two-dimensional burst
fits. Only then may the approved manual map feed an ACF stability check. A
demonstrated residual time-local RFI bias activates the deferred automated-
cleaner benchmark and blind-validation chain.

This closes the contract and unblocks
[Establish Zach's original products, metadata, and time axes](zach-analysis-01-establish-raw-products-time-axes.md).
