# Build the verified Zach CHIME preprocessing baseline

- Type: `wayfinder:task` (AFK)
- Status: resolved (2026-07-22)
- Assignee: —
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

Owner review is complete. The no-go/current-next-method decision is accepted,
with the owner's 2026-07-22 clarification that the reviewed diagnostic is
**pre-bad-channel mask** and therefore does not approve the final science mask.
The resulting validation route is:

1. [Review the preservation limits on a controlled dynamic spectrum](rfi-validation-01a-review-preservation-dynamic-spectrum.md);
2. [Define the CHIME RFI-cleaning acceptance contract](rfi-validation-01-define-acceptance-contract.md).

Steps 3–7 of the original route (bandpass stabilization, frozen benchmark,
cleaner comparison, blind validation, cleaning-boundary ratification) were
the automated-cleaner campaign. The owner's 2026-07-26 disposition in
[rfi-validation-01](rfi-validation-01-define-acceptance-contract.md) made the
manual owner-reviewed bad-channel map route the authority and did not pursue
that campaign; those five tickets were removed 2026-07-26 (recoverable from
Git history).

Ticket 02 remains blocked by the complete input-remediation and campaign-rerun
ticket, not only by radio-frequency-interference validation.

## Resolution — 2026-07-22

The owner accepted the fail-closed baseline by directing this follow-on route.
The explicit-mask grid and migration preflight changes pass. Bandpass
correction is required but not yet stable. The current package RFI cleaner is
rejected, and no science fit or claim is admitted.
