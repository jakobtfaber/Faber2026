# Audit the deprecated Zach C2D4 failure

- Type: `wayfinder:task` (AFK)
- Status: open
- Assignee: —
- Blocked by: —
- Map: [ApJ submission](../map-apj-submission.md)
- Plan: [Controlled joint-scattering reruns](../../specs/plan-controlled-joint-scattering-reruns-2026-07-22.md)
- Authorization: manuscript-owner request, 2026-07-22

## What to build

Produce a hash-bound failure audit of the deprecated Zach C2D4 fit before any
replacement fit starts. Reconstruct the fourth DSA-110 component from the
producing artifacts, quantify why it behaves as a broad low-fluence pedestal,
separate valid same-mode comparisons from invalid evidence comparisons, and
freeze executable guards for the controlled rerun. Never admit the deprecated
panel to visual review.

## Acceptance criteria

- [ ] Original fit, samples, model grid, logs, configuration, and input hashes are identified; missing provenance is explicit.
- [ ] Component arrivals, widths, fluence fractions, fitted support, residuals, and comparison validity are recomputed from producing artifacts.
- [ ] The rerun guard contract is machine-readable and covered by tests.
- [ ] An independent check agrees with the audit's quantitative findings.
- [ ] Deprecated artifacts remain diagnostic-only and hidden from review.

## Blocked by

None — can start immediately.
