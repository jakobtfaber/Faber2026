# Define the CHIME RFI-cleaning acceptance contract

- Type: `wayfinder:grilling` (HITL)
- Status: open
- Assignee: —
- Blocked by: [Build the verified Zach CHIME preprocessing baseline](16-build-verified-zach-chime-preprocessing-baseline.md)
- Map: [ApJ submission](../map-apj-submission.md)
- Authorization: owner request, 2026-07-21

## Question

What evidence and numerical limits must a CHIME radio-frequency-interference
(RFI) cleaner satisfy before its products may feed burst, scattering, or
scintillation measurements?

Set the fail-closed contract before testing replacements. At minimum, decide:

1. which contamination-removal, false-removal, retained-data, and
   time-split-stability measures are binding;
2. which injected signals and protected burst features must survive, and how
   closely their fluence, width, spectrum, and time-frequency structure must
   be preserved;
3. which evidence must come from data withheld from all tuning;
4. whether acceptance is Zach-only or also requires untouched raw CHIME files
   with different interference conditions; and
5. which compact figures the owner must inspect before ratification.

The contract must distinguish bandpass flattening from RFI removal, require
explicit masks for missing or rejected samples, and forbid calling a product
"clean" merely because its collapsed spectrum is smoother.
