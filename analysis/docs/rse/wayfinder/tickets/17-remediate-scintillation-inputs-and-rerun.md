# Remediate the scintillation inputs and rerun the campaign

- Type: `wayfinder:task` (AFK)
- Status: open
- Assignee: —
- Blocked by: [Ratify CHIME RFI cleaning and its science-use boundary](rfi-validation-05-ratify-cleaning-boundary.md) (requires `pass`)
- Map: [ApJ submission](../map-apj-submission.md)
- Authorization: owner data-review findings, 2026-07-18

## Question

Rebuild and review every input required before the CHIME-band scintillation
method can return to ratification.

Execution must:

1. apply only the ratified CHIME RFI configuration and document each mask;
2. remove and document the DSA-110 central-channel contamination;
3. reconcile one authoritative dispersion measure per burst across the
   upchannelized targets, full-resolution products, and manuscript catalog;
4. regenerate aligned products, provenance, checksums, and registry inputs;
5. rerun the windowed-refit campaign under its unchanged predeclared gates;
6. rerun closure and finalization and regenerate validation products; and
7. obtain fresh owner review of all input dynamic spectra and frequency
   autocorrelation-function panels.

Resolution requires every item above. A radio-frequency-interference pass
alone cannot resolve this ticket, make a result science-ready, or authorize a
manuscript claim. Return to ticket 02 only after this full chain resolves.
