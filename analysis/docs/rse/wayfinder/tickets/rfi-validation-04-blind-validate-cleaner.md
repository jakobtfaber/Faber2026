# Blind-validate the selected CHIME RFI cleaner

- Type: `wayfinder:task` (AFK)
- Status: open
- Assignee: —
- Blocked by: [Compare and choose the CHIME RFI cleaner](rfi-validation-03-compare-and-choose-cleaner.md) (requires `pass`)
- Map: [ApJ submission](../map-apj-submission.md)
- Authorization: owner request, 2026-07-21

## Question

Run the frozen cleaner and configuration once on every untouched test input
and determine whether every predeclared acceptance limit passes.

Do not retune after opening the test results. Run on Zach's sealed test
interval and both preselected untouched raw CHIME files: one
interference-heavy and one relatively quiet. Record per-case and aggregate
contamination removal, false removal, retained-data fraction, mask stability,
and injected-signal recovery. Produce concise before/after dynamic spectra,
collapsed spectra, and mask panels for owner review.

Resolution requires a checksummed evidence packet, exact rerun command, source
and environment identities, and an unambiguous pass/no-go verdict. Failure on
any required file is a no-go. No burst, scattering, or scintillation result may
be promoted by this ticket.
