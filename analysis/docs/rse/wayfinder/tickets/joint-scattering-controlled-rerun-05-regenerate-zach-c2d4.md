# Regenerate Zach C2D4

- Type: `wayfinder:task` (AFK)
- Status: open
- Assignee: —
- Blocked by: [Build the seeded reproducible joint-fit runner](joint-scattering-controlled-rerun-02-build-seeded-runner.md)
- Map: [ApJ submission](../map-apj-submission.md)
- Plan: [Controlled joint-scattering reruns](../../specs/plan-controlled-joint-scattering-reruns-2026-07-22.md)
- Authorization: manuscript-owner request, 2026-07-22

## What to build

Run a new clean, seeded Zach C2D4 joint fit under the deprecated-failure guards
and independently regenerate its diagnostic panel. Job 180 and all of its
derived artifacts are audit evidence only and cannot be reused. Deliver the
complete fit, residual, component, provenance, and reproduction bundle needed
for visual review without approving fit values or component-count evidence.

## Acceptance criteria

- [ ] The run uses the owner-confirmed C2D4 morphology and the frozen controlled-run contract.
- [ ] The fit and independent regeneration agree exactly on scientific content and panel bytes.
- [ ] Every deprecated-Zach arrival, width, fluence, support, mode, and residual guard is evaluated and recorded.
- [ ] No job-180 artifact can satisfy the new receipt.
- [ ] The bundle is ready for ticket 6, with fitted values and count evidence still trust-pending.

## Blocked by

- [Build the seeded reproducible joint-fit runner](joint-scattering-controlled-rerun-02-build-seeded-runner.md)
