# Regenerate Oran C1D1

- Type: `wayfinder:task` (AFK)
- Status: open
- Assignee: —
- Blocked by: [Build the seeded reproducible joint-fit runner](joint-scattering-controlled-rerun-02-build-seeded-runner.md)
- Map: [ApJ submission](../map-apj-submission.md)
- Plan: [Controlled joint-scattering reruns](../../specs/plan-controlled-joint-scattering-reruns-2026-07-22.md)
- Authorization: manuscript-owner request, 2026-07-22

## What to build

Run a new clean, seeded Oran C1D1 joint fit and independently regenerate its
diagnostic panel. Deliver the complete fit, residual, component, provenance,
and reproduction bundle needed for visual review. Do not approve fitted values
or promote the panel to the manuscript.

## Acceptance criteria

- [ ] The run uses the owner-confirmed C1D1 morphology and the frozen controlled-run contract.
- [ ] The fit and independent regeneration agree exactly on scientific content and panel bytes.
- [ ] Prior-edge, posterior-predictive residual, component, window, and crop diagnostics are recorded.
- [ ] The old diagnostic candidate cannot satisfy the new receipt.
- [ ] The bundle is ready for ticket 6, with fitted values still trust-pending.

## Blocked by

- [Build the seeded reproducible joint-fit runner](joint-scattering-controlled-rerun-02-build-seeded-runner.md)
