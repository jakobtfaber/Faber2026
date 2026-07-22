# Ratify CHIME RFI cleaning and its science-use boundary

- Type: `wayfinder:grilling` (HITL)
- Status: open
- Resolution gate: pass-only
- Gate outcome: pending
- Assignee: —
- Blocked by: [Blind-validate the selected CHIME RFI cleaner](rfi-validation-04-blind-validate-cleaner.md)
- Map: [ApJ submission](../map-apj-submission.md)
- Authorization: owner request, 2026-07-21

## Question

Does the blind evidence justify accepting the selected cleaner, and exactly
which downstream measurements may consume its products?

The owner reviews the predeclared measures and compact diagnostic panels. A
pass must name the frozen code/configuration, accepted data scope, known
limitations, required provenance fields, and whether the result is sufficient
to start the complete scintillation-input remediation ticket. A no-go must keep
this ticket open with `Gate outcome: no-go`, keep all science products
fail-closed, and identify the smallest next method question; it must not
silently weaken the acceptance contract. Only a pass may resolve this ticket
and clear the remediation blocker.

The Zach preprocessing-baseline ticket is already resolved as a fail-closed
no-go. This ticket cannot revise that record, admit a cleaner by itself, or
authorize a burst, scattering, or scintillation claim.
