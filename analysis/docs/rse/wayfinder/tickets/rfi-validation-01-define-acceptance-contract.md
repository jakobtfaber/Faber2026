# Define the CHIME RFI-cleaning acceptance contract

- Type: `wayfinder:grilling` (HITL)
- Status: resolved — owner disposition 2026-07-26: manual route sufficient;
  automated-cleaner campaign not pursued
- Assignee: Codex
- Blocked by: —
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

## Resolution — 2026-07-26

The owner reviewed the twelve-burst pre-ratification visual packet
(`docs/rse/specs/notes/rfi-preratification-visual-packet-2026-07-26.md`;
raw `_cntr_bpc` dynamic spectra, CHIME and DSA side by side, no
contract-governed cleaning) and ruled that **additional RFI cleaning is not
necessary** for the sample, with one exception in the Zach CHIME data. The
exception was dispositioned through the existing owner-reviewed manual
bad-channel route, not an automated cleaner:

- unmasked sliver 727.54–729.49 MHz between upstream-masked blocks, and
- the 707.50–710.79 MHz burst-window crossing of a 0.165 MHz/ms swept
  narrowband tone (owner chose the crossing-only mask; the full-sweep
  option was declined),

both landed as an amendment to the owner-approved
`rfi/manual-bad-channels/chime-frb/zach.json` (pull request #116, merged
2026-07-26; before/after evidence under
`docs/rse/verify/manual-bad-channel-review-20260726/zach-chime/`).

Consequently the five-rule acceptance contract below is **not ratified and
not rejected on its merits**: it remains the recorded standard should an
automated-cleaner campaign ever be chartered, but no such campaign is
planned. The manual owner-reviewed map route (this ticket's `index.json`
policy) is the bad-channel authority for science processing. The accepted
2026-07-21/23 vocabulary, sealing, and preservation-limit decisions remain
in force as recorded.

## Decisions — in progress

- **Vocabulary accepted 2026-07-21:** `padded`, `bandpass-corrected`,
  `RFI-masked`, `RFI-validated`, and `science-admissible preprocessing` are
  distinct states. Unqualified `clean` is forbidden. Definitions are recorded
  in [`CONTEXT.md`](../../../../CONTEXT.md).
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
- **Signal-preservation limits accepted 2026-07-23:** on
  interference-free injections, median cleaner-induced shift no greater than
  0.25 measurement uncertainty, 95% no greater than 0.5, and none greater than
  1; on contaminated injections, at least 95% within 1 uncertainty of truth
  and median systematic offset no greater than 0.25. Detection status and
  component count must remain unchanged away from predeclared decision
  boundaries. Raw-unit thresholds are illustrative only. The accepted
  controlled review closes the preservation-limit dependency but does not
  validate a cleaner or admit science.

## Proposed remaining contract — owner decision pending

The following limits are proposed before any replacement is compared. They
apply separately to every required file and broad frequency slice; aggregate
success cannot hide a failed case.

### Frozen benchmark definitions

Before any candidate output is viewed, the benchmark must hash and freeze:

- the contaminated-sample truth labels, injected-excess-power reference,
  truth-clean and source-valid labels, source-invalid exclusions, approved
  manual channel map, otherwise-usable denominator, and every mask;
- broad-frequency-slice and contiguous-time-block edges, contaminant classes,
  protected-signal parameter strata, required measurements, applicability
  rules, and minimum sample and injection counts for every reported cell;
- injections of known-truth contaminants and protected bursts into each of
  the three held-out raw backgrounds. Unlabelled native raw samples cannot
  establish contamination-identification or false-removal truth; and
- the uncertainty reference used to normalize every protected-measurement
  shift. It must come from the injected-truth or frozen reference pipeline, or
  from another predeclared combination rule; candidate-inflated uncertainty
  cannot make a shift pass.

No candidate-dependent relabelling, denominator change, exclusion, mask
change, uncertainty choice, or merging of sparse cells is permitted.

### Binding measures

- **Contamination removal:** on known-truth synthetic contamination, remove at
  least 90 percent of injected excess power and identify at least 95 percent of
  contaminated samples. Report both numbers; a smooth collapsed spectrum is
  not evidence.
- **False removal:** on source-valid, truth-clean samples, falsely reject no
  more than 1 percent overall and no more than 2 percent in any predeclared
  broad frequency slice or contiguous time block.
- **Retained data:** after source-invalid samples and the approved manual
  channel map are excluded from the denominator, retain at least 95 percent
  for the relatively quiet test file and 80 percent for the
  interference-heavy test file. Report retained fractions by time block and
  frequency slice.
- **Time-split stability:** use one frozen configuration. Each contiguous half
  must independently pass every applicable removal, false-removal, retention,
  and signal-preservation limit. No average-over-halves rescue is allowed.
- **Class and signal-stratum stability:** every predeclared narrow-band,
  broad-band, impulsive, and drifting contaminant class and every protected
  burst-parameter stratum with the frozen minimum support must independently
  pass its applicable limits. Pooled success cannot rescue a failed class or
  signal stratum.
- **Signal preservation:** apply the already accepted
  uncertainty-normalized limits to every protected measurement listed above.
  A protected measurement is evaluated only where its known-truth injection
  and measurement uncertainty are valid; unavailable measurements are
  explicit missing results, not passes.

An exact-threshold equality passes. Any missing required measure, invalid
uncertainty estimate, undeclared mask change, or per-file/per-slice failure is
a no-go. Confidence intervals and sample counts accompany every rate; the
point estimate must pass and its 95-percent lower confidence bound must meet
the minimum for removal/retention, while its 95-percent upper confidence bound
must not exceed the maximum for false removal. The benchmark ticket must
freeze the interval calculation before candidate comparison. It must account
for time-frequency correlation using predeclared independent clusters or a
cluster bootstrap, report the effective independent sample count, and mark a
cell invalid when the frozen minimum support is not met. Treating correlated
pixels as independent Bernoulli trials is forbidden.

### Evidence and scope

- Tuning and method selection use only Zach training and validation intervals.
- Final evidence must come from Zach's sealed test interval and two
  preselected untouched raw CHIME files: one relatively quiet and one
  interference-heavy. All three are withheld from tuning.
- Synthetic contaminants span narrow-band, broad-band, impulsive, and drifting
  cases. Protected burst injections span the predeclared ranges of fluence,
  width, spectral occupancy, component count, scattering timescale, and
  scintillation bandwidth, including cases near but not on declared decision
  boundaries.
- Bandpass-only, no-RFI-removal, and current-package results are reported as
  baselines. Bandpass correction and RFI removal have separate masks,
  parameters, provenance, and measurements.
- Acceptance is not Zach-only: every required test file must pass. It attaches
  only to the exact code, configuration, operation order, source scope, and
  hashes tested. It does not authorize the full-sample campaign.

### Required owner review

The owner reviews one compact packet before this contract is ratified:

1. a table of every binding measure, threshold, point estimate, 95-percent
   confidence interval, raw sample count, effective independent sample count,
   and pass/no-go result by file, time half, broad frequency slice,
   contaminant class, and protected-signal stratum;
2. matched no-removal, bandpass-only, and candidate panels showing the dynamic
   spectrum, collapsed spectrum, explicit mask, and retained-data fraction;
3. known-truth overlays for contamination and false removal;
4. protected-measurement shift distributions in units of their measurement
   uncertainty, with failed or missing measures visible; and
5. a provenance page binding sources, split hashes, truth labels,
   denominators, slice/block edges, applicability and support rules,
   uncertainty reference, manual map, bandpass, cleaner code/configuration,
   environment, operation order, and rerun command.

Ratifying this contract will unblock bandpass qualification only. It will not
validate a cleaner, open sealed test outputs, or admit burst, scattering,
scintillation, or manuscript results.
