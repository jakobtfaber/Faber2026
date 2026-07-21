# Ratify CHIME RFI cleaning and its science-use boundary

- Type: `wayfinder:grilling` (HITL)
- Status: open
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
to resume the CHIME-band scintillation-method decision. A no-go must keep all
science products fail-closed and identify the smallest next method question;
it must not silently weaken the acceptance contract.

On acceptance, close the Zach preprocessing-baseline task and unblock
[Ratify the CHIME-band scintillation method and unblock the full-sample campaign](02-ratify-chime-scintillation-method.md).
