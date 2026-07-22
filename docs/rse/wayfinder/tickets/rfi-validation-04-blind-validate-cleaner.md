# Blind-validate the selected CHIME RFI cleaner

- Type: `wayfinder:task` (AFK)
- Status: deferred — conditional
- Assignee: —
- Blocked by: [Compare and choose the CHIME RFI cleaner](rfi-validation-03-compare-and-choose-cleaner.md)
- Map: [ApJ submission](../map-apj-submission.md)
- Authorization: owner request, 2026-07-21

## Question

Run the frozen cleaner and configuration once on the untouched test data and
determine whether every predeclared acceptance limit passes.

This ticket runs only if the conditional automated time-frequency-cleaner lane
is activated. Manual channel maps remain a separate fixed input.

Do not retune after opening the test results. Record per-case and aggregate
contamination removal, false removal, retained-data fraction, mask stability,
and injected-signal recovery. Produce concise before/after dynamic spectra,
collapsed spectra, and mask panels for owner review. Include at least one raw
CHIME file not used during Zach development if required by the accepted
generalization contract.

Resolution requires a checksummed evidence packet, exact rerun command, source
and environment identities, and an unambiguous pass/no-go verdict. No burst,
scattering, or scintillation result may be promoted by this ticket.
