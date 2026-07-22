# Stabilize and qualify the CHIME bandpass model

- Type: `wayfinder:task` (AFK)
- Status: open
- Resolution gate: pass-only
- Gate outcome: pending
- Assignee: —
- Blocked by: [Define the CHIME RFI-cleaning acceptance contract](rfi-validation-01-define-acceptance-contract.md)
- Map: [ApJ submission](../map-apj-submission.md)
- Authorization: owner request, 2026-07-21

## Question

Which frozen bandpass model is stable enough to serve as the non-RFI
preprocessing baseline for cleaner comparison?

Establish the model and its operation order without opening any sealed test
output. Use only designated training and validation off-pulse data. Bind source
hashes, masks, channel maps, code, container, parameters, and exact rerun
commands. Predeclare stability limits across time halves and protected broad
frequency slices, and show the residual response without hiding missing data.

Resolution requires the frozen model to pass the accepted stability limits on
training and validation inputs. A no-go records `Gate outcome: no-go` but keeps
this ticket open, so the benchmark remains blocked. Bandpass qualification
neither validates RFI removal nor authorizes a science fit.
