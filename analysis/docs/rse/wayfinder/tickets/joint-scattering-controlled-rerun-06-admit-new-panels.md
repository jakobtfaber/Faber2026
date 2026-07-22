# Admit only newly reproduced joint-scattering panels

- Type: `wayfinder:task` (AFK)
- Status: open
- Assignee: —
- Blocked by: [Regenerate Oran C1D1](joint-scattering-controlled-rerun-03-regenerate-oran-c1d1.md), [Regenerate JohnDoeII C2D2](joint-scattering-controlled-rerun-04-regenerate-johndoeii-c2d2.md), [Regenerate Zach C2D4](joint-scattering-controlled-rerun-05-regenerate-zach-c2d4.md)
- Map: [ApJ submission](../map-apj-submission.md)
- Plan: [Controlled joint-scattering reruns](../../specs/plan-controlled-joint-scattering-reruns-2026-07-22.md)
- Authorization: manuscript-owner request, 2026-07-22

## What to build

Create a new immutable visual-review batch from the three controlled-rerun
bundles. Admit only panels whose new fit and rendering reproduction receipts
pass. Preserve completed older batches, return at most one eligible figure at a
time, leave owner decisions unset, and prohibit fitted-value approval or
manuscript promotion.

## Acceptance criteria

- [ ] Every admitted panel is bound to a new fit, sample, model-grid, diagnostic, and panel hash.
- [ ] Every old joint-scattering artifact hash is explicitly rejected.
- [ ] Failed or incomplete reruns remain hidden and cannot receive an owner decision.
- [ ] The review status and next-item commands expose only eligible new panels, one at a time.
- [ ] Registry trust remains pending and manuscript promotion remains disabled.

## Blocked by

- [Regenerate Oran C1D1](joint-scattering-controlled-rerun-03-regenerate-oran-c1d1.md)
- [Regenerate JohnDoeII C2D2](joint-scattering-controlled-rerun-04-regenerate-johndoeii-c2d2.md)
- [Regenerate Zach C2D4](joint-scattering-controlled-rerun-05-regenerate-zach-c2d4.md)
