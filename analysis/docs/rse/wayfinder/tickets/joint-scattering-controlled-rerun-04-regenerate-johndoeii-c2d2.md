# Regenerate JohnDoeII C2D2

- Type: `wayfinder:task` (AFK)
- Status: resolved (2026-07-23) — reproducibility passed; science and visual review pending
- Assignee: —
- Blocked by: [Build the seeded reproducible joint-fit runner](joint-scattering-controlled-rerun-02-build-seeded-runner.md)
- Map: [ApJ submission](../map-apj-submission.md)
- Plan: [Controlled joint-scattering reruns](../../specs/plan-controlled-joint-scattering-reruns-2026-07-22.md)
- Authorization: manuscript-owner request, 2026-07-22

## What to build

Run a new clean, seeded JohnDoeII C2D2 joint fit matching the owner morphology
assignment and independently regenerate its diagnostic panel. The prior C1D2
artifact cannot be reused. Deliver the complete fit, residual, component,
provenance, and reproduction bundle needed for visual review without approving
fit values.

## Acceptance criteria

- [x] The run uses the owner-confirmed C2D2 morphology and the frozen controlled-run contract.
- [x] The fit and independent regeneration agree exactly on scientific content and panel bytes.
- [x] Prior-edge, posterior-predictive residual, component, window, and crop diagnostics are recorded.
- [x] The old C1D2 candidate cannot satisfy the new receipt.
- [x] The bundle is ready for ticket 6, with fitted values still trust-pending.

## Blocked by

- [Build the seeded reproducible joint-fit runner](joint-scattering-controlled-rerun-02-build-seeded-runner.md)

## Resolution — 2026-07-23

The v4 JohnDoeII run completed twice on h17 from clean detached pipeline
revision `fba755ad7edbd69dece059c8c5f0868da41e3f2b`, with C2D2, seed
`20230814`, and the frozen controls. Independent verification recomputed every
contract input hash and output hash. JSON and SVG outputs agree byte-for-byte;
weighted samples and model-grid scientific arrays agree canonically. Both
receipts pass preflight, post-preparation reverification, and complete-output
gates.

The verification receipt is
[`joint-scattering-controlled-rerun-04-johndoeii-c2d2-20260723`](../../verify/joint-scattering-controlled-rerun-04-johndoeii-c2d2-20260723/README.md).
It records only morphology and provenance. It does not approve or interpret
fit-derived values. The old C1D2 candidate and superseded triptych hashes
cannot satisfy this C2D2 receipt. The panel remains unapproved and ineligible
for review until ticket 6 admits the controlled bundle to independent
scientific and visual review.
