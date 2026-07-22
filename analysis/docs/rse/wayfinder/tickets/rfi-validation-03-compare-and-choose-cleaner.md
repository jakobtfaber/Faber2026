# Compare and choose the CHIME RFI cleaner

- Type: `wayfinder:prototype` (HITL)
- Status: open
- Assignee: —
- Blocked by: [Build the frozen CHIME RFI-validation benchmark](rfi-validation-02-build-frozen-benchmark.md)
- Map: [ApJ submission](../map-apj-submission.md)
- Authorization: owner request, 2026-07-21

## Question

Which RFI method, thresholds, and ordering relative to bandpass correction
should advance to blind validation?

Compare a small, justified candidate set on tuning and validation data only.
The comparison must expose separate RFI-removal and bandpass effects, report
every acceptance-contract measure, and show concise review panels containing
the dynamic spectrum, collapsed spectrum, mask, and retained-data fraction.
The untouched test data must remain sealed.

Resolve with the owner's visual and numerical choice of one method, one
operation order, and one frozen configuration tied to a code revision. A
failure to find a qualifying candidate is a valid no-go resolution and must
not be converted into relaxed thresholds after results are seen.
