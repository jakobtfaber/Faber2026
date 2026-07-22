# Audit the deprecated Zach C2D4 failure

- Type: `wayfinder:task` (AFK)
- Status: resolved (2026-07-22)
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

- [x] Original fit, samples, model grid, logs, configuration, and input hashes are identified; missing provenance is explicit.
- [x] Component arrivals, widths, fluence fractions, fitted support, residuals, and comparison validity are recomputed from producing artifacts.
- [x] The rerun guard contract is machine-readable and covered by tests.
- [x] An independent check agrees with the audit's quantitative findings.
- [x] Deprecated artifacts remain diagnostic-only and hidden from review.

## Blocked by

None — can start immediately.

## Resolution — 2026-07-22

The [artifact audit](../../../../figure_review/audits/2026-07-22-deprecated-zach-c2d4/audit.json)
and [scientific interpretation](../../specs/research-deprecated-zach-c2d4-failure-2026-07-22.md)
resolve the ticket. Job 180's fourth DSA-110 component is 59.38 fitted-window
widths wide and carries 3.0818% of modeled band fluence. It is a pedestal, not
the owner-identified fourth pulse. The same-arm comparison favors C2D3 by
10.102 log-evidence units, but does not adjudicate the owner C2D4 morphology.
Job 180 remains hidden and cannot seed the replacement run.
