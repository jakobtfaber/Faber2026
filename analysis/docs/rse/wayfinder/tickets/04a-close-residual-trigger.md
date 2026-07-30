# Close the scattering escalation trigger

- Type: `wayfinder:grilling` (HITL)
- Status: resolved — owner selected validation before use, 2026-07-29
- Assignee: manuscript owner
- Blocked by: [CHIME-band method](02-ratify-chime-scintillation-method.md)
- Map: [ApJ submission](../map-apj-submission.md)

## Owner decision card

```json
{
  "id": "scattering-residual-trigger",
  "kind": "scientific",
  "title": "Second-screen fitting rule",
  "decision": "If the observed burst profile has a mismatch at the delay expected for a second screen, and one-screen simulations do not reproduce it, may that result alone justify fitting a second scattering screen?",
  "recommended": {
    "choice": "calibrate",
    "reason": "First test the rule on known one-screen and two-screen examples, so we know how often it requests a second screen incorrectly and how often it detects one when present."
  },
  "choices": [
    {
      "id": "accept",
      "label": "Allow this predicted-delay mismatch test alone to start a second-screen fit."
    },
    {
      "id": "calibrate",
      "label": "Validate the predicted-delay mismatch rule on known one-screen and two-screen examples before use."
    }
  ],
  "context": [
    "The autocorrelation-based rule was retired: its conservative threshold rejected all eight simulated two-screen cases.",
    "The remaining proposal compares the observed burst profile with profiles simulated from the fitted one-screen model, specifically at the delay predicted for a second screen.",
    "No measured error rate currently shows how often that predicted-delay test invents or misses a second screen."
  ],
  "evidence": [
    {
      "label": "Trigger calibration",
      "path": "docs/rse/specs/plan-a1-trigger-calibration.md",
      "sha256": "974ec606a5466468b437f8c1f96e13a81529351660b747117529c383187b6346"
    },
    {
      "label": "Current circulation design",
      "path": "docs/rse/specs/plan-circulation-readiness.md",
      "sha256": "d2ae8ecc6eb7a3741ae7c208a0ec5e135d1f0ee68879b5c020a289840c787237"
    }
  ],
  "effect": "The choice determines whether and when the analysis may fit a second scattering screen.",
  "recorder": {
    "path": "docs/rse/wayfinder/tickets/04a-close-residual-trigger.md",
    "action": "Record the trigger decision and resolve this ticket."
  },
  "priority": 40
}
```

## Resolution

Owner decision, 2026-07-29: **validate before use**.

The predicted-delay mismatch rule may not by itself justify fitting a second
scattering screen until it has been tested on known one-screen and two-screen
examples. The validation must report both:

- how often one-screen cases incorrectly request a second screen; and
- how often true two-screen cases are detected.

Until those rates are measured and accepted, the rule remains unavailable for
scientific model selection.
