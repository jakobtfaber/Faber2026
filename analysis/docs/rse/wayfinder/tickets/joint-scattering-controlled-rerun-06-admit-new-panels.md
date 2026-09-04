# Admit only newly reproduced joint-scattering panels

- Type: `wayfinder:task` (AFK)
- Status: resolved
- Assignee: Orchestrator
- Blocked by: [Regenerate Oran C1D1](joint-scattering-controlled-rerun-03-regenerate-oran-c1d1.md), [Regenerate JohnDoeII C2D2](joint-scattering-controlled-rerun-04-regenerate-johndoeii-c2d2.md), [Regenerate Zach C2D4](joint-scattering-controlled-rerun-05-regenerate-zach-c2d4.md)
- Map: [ApJ submission](../map-apj-submission.md)
- Plan: [Controlled joint-scattering reruns](../../specs/plan-controlled-joint-scattering-reruns-2026-07-22.md)
- Authorization: manuscript-owner request, 2026-07-22

## Owner decision — revise all panels (2026-09-04)

- Decision: return Oran C1D1, JohnDoeII C2D2 and Zach C2D4 for revision;
  admit none of the three controlled-rerun panels to independent review.
- Recorded: manuscript owner during the owner-queue walkthrough, 2026-09-04.
- Effect: all three exact panels remain review-ineligible; scientific trust,
  fitted values and manuscript promotion remain blocked.

## Owner decision card — resolved 2026-09-04

Retained for provenance. The owner selected `revise-all`; the decision and
its fail-closed effect are recorded above and in the machine-readable packet.

```json
{
  "id": "controlled-joint-panel-disposition",
  "kind": "scientific",
  "title": "Controlled joint-panel disposition",
  "decision": "Should the exact three-panel controlled-rerun packet be revised or admitted to independent review?",
  "recommended": {
    "choice": "revise-all",
    "reason": "Revise all three panels. Every model family fails its prior-edge diagnostic and retains additional crop, component-width, low-fluence or structured-residual defects. Exact reproduction proves identity, not scientific adequacy."
  },
  "choices": [
    {
      "id": "revise-all",
      "label": "Return all three panels for revision; admit none to independent review."
    },
    {
      "id": "admit-all",
      "label": "Admit all three exact panels and receipt-bound diagnostics to independent review only."
    }
  ],
  "context": [
    "Oran C1D1, JohnDoeII C2D2 and Zach C2D4 reproduce exactly against complete controlled-run receipts.",
    "All three panels fail scientific-readiness diagnostics; the packet recommends revise for each.",
    "Admission would not approve a manuscript figure, trust a fitted value or enable manuscript promotion."
  ],
  "evidence": [
    {
      "label": "Owner review with exact panels and diagnostic reasons",
      "path": "docs/rse/verify/joint-scattering-controlled-rerun-06-owner-review-20260723/README.md",
      "sha256": "7f930986efc84284c0299a8b75e77d0a0a3f29b378e207e38bfcbbf40c1331a2"
    },
    {
      "label": "Machine-readable panel identities, receipt hashes and recorded revise decisions",
      "path": "docs/rse/verify/joint-scattering-controlled-rerun-06-owner-review-20260723/decision-packet.json",
      "sha256": "91305964d71ea5a75e46a2a33b8b8d0b7f0720d9b169055fbaf8afe983cb7fba"
    }
  ],
  "effect": "Either keeps all three panels out of review pending revision or admits only their exact receipt-bound packets to a later independent review. Scientific trust and manuscript promotion remain blocked.",
  "recorder": {
    "path": "docs/rse/wayfinder/tickets/joint-scattering-controlled-rerun-06-admit-new-panels.md",
    "action": "Record the packet disposition here and update the machine-readable owner decisions before changing review eligibility."
  },
  "priority": 40
}
```

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

## Agent review — 2026-07-23

The owner scientific and visual decision was pending from 2026-07-23 until
the owner selected revision for all three panels on 2026-09-04.

All three v4 bundles pass exact reproduction and provenance checks. Full-size
inspection and the receipt-bound diagnostics do not support automatic
admission:

- Oran C1D1: **revise**
- JohnDoeII C2D2: **revise**
- Zach C2D4: **revise**

The smallest owner packet is
[`joint-scattering-controlled-rerun-06-owner-review-20260723`](../../verify/joint-scattering-controlled-rerun-06-owner-review-20260723/README.md).
It contains the exact reproduced SVGs, hashes, receipt bindings, readiness
flags, and recorded revise decisions.

No panel was promoted or added to the final-draft figure queue. Registry trust
and fitted values remain untrusted; manuscript promotion remains disabled.
The ticket stops at the owner's scientific and visual approve-for-review or
revise decisions.

## Resolution

Resolved 2026-09-04: revise all three panels. No panel was admitted to
independent review or promoted.
