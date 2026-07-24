# Regenerate Zach C2D4

- Type: `wayfinder:task` (AFK)
- Status: resolved (2026-07-23) — reproducibility passed; science and visual review pending
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

- [x] The run uses the owner-confirmed C2D4 morphology and the frozen controlled-run contract.
- [x] The fit and independent regeneration agree exactly on scientific content and panel bytes.
- [x] Every deprecated-Zach arrival, width, fluence, support, mode, and residual guard is evaluated and recorded.
- [x] No job-180 artifact can satisfy the new receipt.
- [x] The bundle is ready for ticket 6, with fitted values and count evidence still trust-pending.

## Blocked by

- [Build the seeded reproducible joint-fit runner](joint-scattering-controlled-rerun-02-build-seeded-runner.md)

## Resolution — 2026-07-23

The v4 Zach run completed twice on h17 from clean detached pipeline revision
`fba755ad7edbd69dece059c8c5f0868da41e3f2b`, with C2D4, seed `20220207`,
and the frozen controls. Independent verification recomputed every contract
input and output hash. JSON and SVG outputs agree byte-for-byte; weighted
samples and model-grid scientific arrays agree canonically. Both receipts pass
preflight, post-preparation reverification, and complete-output gates.

The verification receipt is
[`joint-scattering-controlled-rerun-05-zach-c2d4-20260723`](../../verify/joint-scattering-controlled-rerun-05-zach-c2d4-20260723/README.md).
It verifies that every required deprecated-Zach guard is recorded, but does
not interpret its fit-derived values or component-count evidence. Job 180
hashes are explicitly superseded. The panel remains unapproved and ineligible
for review until ticket 6 admits the controlled bundle to independent
scientific and visual review.
