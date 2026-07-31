# Close the scintillation-to-scattering coupling design

- Type: `wayfinder:grilling` (HITL)
- Status: open
- Assignee: —
- Blocked by: [trigger](04a-close-residual-trigger.md)
- Map: [ApJ submission](../map-apj-submission.md)
- Delegation: [Standing delegated decision authority](../standing-delegation-2026-07-20.md)

## Question

The 2026-07-10 D4 design lock accepted frozen posterior/limit products with
quality flags and a prior-odds-only role for scintillation geometry. Those
elements remain in force. The only reopened element is the escalation trigger.

The nested-sampling autocorrelation comparison was retired for lack of a usable
operating point, leaving posterior-predictive profile residuals as the sole
trigger. Ticket 04a records whether that trigger is sufficient or requires its
own false-escalation calibration.

## Current state (2026-07-31)

Ticket 04a resolved 2026-07-29: validate before use. The validation campaign
has now run (plan `plan-predicted-delay-trigger-calibration.md`; 27 cells,
200 injections each, seed0 20260731, source revision `7a4b6a0`; results in
`simulation/experiments/predicted-delay-trigger/`). Measured:

- Conservative false-escalation envelopes on the windowed residual
  statistic: 4.70 / 4.65 / 3.94 at 0.5 / 1 / 5 per cent.
- Detection: second screens with `r = tau2/tau1 >= 1` are detectable
  (97.5-100 per cent at S/N 30; 65-99 per cent at S/N 15 for r = 3);
  `r <= 0.3` has **zero** detection power at every S/N and rate — the
  sub-tau1 regime a resolved scintillation bandwidth would actually imply.
- Nested-sampling anchor: 30 paired injections, mean |delta p| = 0.0003
  (max 0.005) — the maximum-likelihood surrogate is faithful.
- Calibration validity is restricted: single-component truth,
  CHIME-like geometry (2.56 microsecond sampling), exponential
  pulse-broadening family.

## Owner decision card

```json
{
  "id": "predicted-delay-trigger-operating-point",
  "kind": "scientific",
  "title": "Predicted-delay trigger operating point",
  "decision": "Accept the 1 per cent false-escalation envelope (windowed residual statistic threshold 4.65) as the second-screen escalation operating point, restricted to the regimes where the calibration shows power, or reject the trigger?",
  "recommended": {
    "choice": "accept-restricted",
    "reason": "At the 1 per cent envelope the rule reliably detects comparable-or-larger second screens while the false-escalation rate is measured, and the calibration proves the rule has no power for tau2 <= 0.3 tau1 — so acceptance must carry that restriction explicitly rather than implying general sensitivity; a resolved scintillation bandwidth implying a much smaller near-screen tau cannot be adjudicated by this trigger."
  },
  "choices": [
    {
      "id": "accept-restricted",
      "label": "Accept the 1 per cent envelope, valid only for r >= 1 second screens on matching CHIME-like geometry."
    },
    {
      "id": "reject",
      "label": "Reject the trigger; second-screen escalation remains unavailable."
    },
    {
      "id": "recalibrate",
      "label": "Request a modified campaign (different grids, geometry, or statistic) before deciding."
    }
  ],
  "context": [
    "False-escalation envelopes (max over 15 null cells, 200 injections each): statistic 4.70 / 4.65 / 3.94 at 0.5 / 1 / 5 per cent.",
    "Detection at the 1 per cent envelope: 97.5-100 per cent for r >= 1 at S/N 30, 65 per cent for r = 3 at S/N 15, and exactly zero for r <= 0.3 at every S/N.",
    "The 30-injection nested-sampling anchor shows the ML surrogate is faithful (mean |delta p| = 0.0003); validity is restricted to single-component morphology and CHIME-like geometry."
  ],
  "evidence": [
    {
      "label": "Calibration report",
      "path": "simulation/experiments/predicted-delay-trigger/calibration.md",
      "sha256": "a3fc6eb4da6d2dc1e5079d2696d0bd85d456bdaf574a53ac6910db8b083c3031"
    },
    {
      "label": "Machine-readable rate table",
      "path": "simulation/experiments/predicted-delay-trigger/calibration.json",
      "sha256": "440ffb1b15393abd4b16dc7d5a35d0c3c70204caed6f4d8ae7013e39e13a2a79"
    },
    {
      "label": "Nested-sampling anchor pairs",
      "path": "simulation/experiments/predicted-delay-trigger/anchor.json",
      "sha256": "f18438bcb76915d5c34dbfeff81a947d7ef4b808db1fe519db9416bd3613f33a"
    }
  ],
  "effect": "Sets whether and when a second scattering screen may be fitted, closing the reopened escalation-trigger element of the D4 coupling design.",
  "recorder": {
    "path": "docs/rse/wayfinder/tickets/04-close-scint-scattering-coupling-design.md",
    "action": "Record the operating-point decision in this ticket and resolve it."
  },
  "priority": 30
}
```
