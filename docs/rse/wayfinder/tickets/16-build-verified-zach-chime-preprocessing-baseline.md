# Build the verified Zach CHIME preprocessing baseline

- Type: `wayfinder:task` (AFK)
- Status: open
- Assignee: Codex
- Blocked by: —
- Map: [ApJ submission](../map-apj-submission.md)
- Authorization: owner request, 2026-07-21

## Question

Produce the evidence-bearing Zach preprocessing baseline required before the
CHIME-band scintillation method can be ratified. The task must:

1. Make the h17 source-migration tool persist its complete preflight path,
   metadata, and SHA-256 payload locally and remotely before the first rename,
   with fail-closed tests and no second data move.
2. Pin and verify the live h17 `chimefrb/baseband-analysis` container, inspect
   the Zach singlebeam HDF5 structure, and execute the smallest metadata-safe
   processing run needed to establish how the 871 retained frequency channels
   are restored to the nominal 1,024-channel CHIME grid. Record whether padding
   is supplied by the package or must be an explicit, mask-carrying project
   step; never represent padded channels as measured zero-valued data.
3. Trace the current radio-frequency-interference excision and bandpass
   correction ordering and implementation, then quantify their behavior on
   Zach with burst-blind/off-pulse controls. Preserve the prior finding that
   mask-unaware zero-filled rebinning is scientifically inadmissible unless
   new evidence overturns it.
4. Store exact commands, container identity, source hashes, masks, channel maps,
   diagnostic products, failures, and a go/no-go verdict. Do not run a
   scattering/scintillation fit or promote a scientific claim in this ticket.

Resolution requires a reproducible evidence packet and a precise next method
decision for the already-assigned CHIME-band ratification ticket.

## Progress — 2026-07-21

Implementation and live h17 execution are complete. See
[validation-zach-chime-preprocessing-baseline](../../specs/validation-zach-chime-preprocessing-baseline.md).

- Nominal 1,024-channel grid plus explicit mask: pass.
- Preflight persistence before future migrations: pass.
- Bandpass correction: required, but half-window stability remains poor.
- Current package RFI excision: rejected; pre-bandpass use worsens held-out
  response and produces an unstable, excessive mask.
- Science fit/claim: not run.

Status remains open pending owner review of the diagnostic figure and acceptance
of the no-go/current-next-method decision. The resulting validation route is:

1. [Define the CHIME RFI-cleaning acceptance contract](rfi-validation-01-define-acceptance-contract.md);
2. [Build the frozen CHIME RFI-validation benchmark](rfi-validation-02-build-frozen-benchmark.md);
3. [Compare and choose the CHIME RFI cleaner](rfi-validation-03-compare-and-choose-cleaner.md);
4. [Blind-validate the selected CHIME RFI cleaner](rfi-validation-04-blind-validate-cleaner.md); and
5. [Ratify CHIME RFI cleaning and its science-use boundary](rfi-validation-05-ratify-cleaning-boundary.md).

Ticket 02 remains blocked.
