# Validate the approved Zach manual map in ACF preprocessing

- Type: `wayfinder:task` (AFK)
- Status: open
- Assignee: —
- Blocked by: [Build Zach's standardized dynamic spectra and validate the burst models](zach-analysis-03-build-dynamic-spectra-fit-burst.md)
- Map: [ApJ submission](../map-apj-submission.md)
- Authorization: owner decision, 2026-07-22

## Question

Does the standardized Zach CHIME/FRB autocorrelation-function (ACF) input remain
measurement-stable after applying the approved effective bad-channel mask?

Use only the standardized post-dispersion-measure, post-burst-model Zach product.
Verify its adopted dispersion measure, time axis, time/frequency resolution,
bandpass state, source-valid mask, manual-map identity, and hashes. Apply the
approved effective mask without changing retained values. Do not reconstruct
these upstream decisions inside the ACF ticket.

Produce one compact owner-review artifact containing before/after dynamic
spectra, explicit mask, time-integrated spectrum, time profile, retained
fraction, and measurement-stability results. Test the frequency ACF, modulation
strength, and decorrelation-bandwidth estimate across predeclared window and
time-split perturbations. Explicitly assess whether residual diagonal or
time-local interference biases those measurements.

Resolution is one of:

- **pass:** manual-map preprocessing is admissible for the named Zach ACF input
  and unblocks the science-use-boundary ticket; or
- **no-go:** identify the failed protected measurement. Only a failure
  attributable to residual time-local RFI activates the deferred automated-
  cleaner benchmark.

No scattering, scintillation, or manuscript result may be promoted here.
