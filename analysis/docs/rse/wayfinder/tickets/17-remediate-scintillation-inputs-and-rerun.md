# Remediate the scintillation inputs and rerun the campaign

- Type: `wayfinder:task` (AFK)
- Status: resolved — superseded 2026-07-26 by
  [scint-redo-01](scint-redo-01-interactive-recampaign-from-raw-data.md):
  the owner chartered a full interactive re-do from raw data, so this
  ticket's remediate-and-rerun path for the old campaign is moot. Its seven
  requirements carry forward as checklist inputs to the re-do. Its RFI
  blocker also resolved differently: the owner-reviewed manual bad-channel
  route is the bad-channel authority (see
  [rfi-validation-01](rfi-validation-01-define-acceptance-contract.md)), and
  no automated-cleaner ratification is planned, so the recorded owner review
  of the route stands in for the `pass` this ticket originally required.
- Assignee: —
- Blocked by: — (originally the automated-cleaner ratification ticket,
  removed 2026-07-26 after the manual-route disposition in
  [rfi-validation-01](rfi-validation-01-define-acceptance-contract.md))
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
