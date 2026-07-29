# Close the scattering escalation trigger

- Type: `wayfinder:grilling` (HITL)
- Status: open
- Assignee: manuscript owner
- Blocked by: [CHIME-band method](02-ratify-chime-scintillation-method.md)
- Map: [ApJ submission](../map-apj-submission.md)

## Owner decision card

```json
{
  "id": "scattering-residual-trigger",
  "kind": "scientific",
  "title": "Scattering escalation trigger",
  "decision": "May posterior-predictive residuals alone trigger a second broadening component?",
  "recommended": {
    "choice": "calibrate",
    "reason": "Require a false-escalation calibration before residuals become the sole trigger."
  },
  "choices": [
    {
      "id": "accept",
      "label": "Accept posterior-predictive residuals as the sole trigger."
    },
    {
      "id": "calibrate",
      "label": "Require false-escalation calibration before accepting the trigger."
    }
  ],
  "context": [
    "The autocorrelation model-comparison trigger was retired because it had no usable operating point.",
    "Posterior-predictive residuals are the only remaining proposed escalation trigger."
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
  "effect": "The choice fixes the trigger used by later scattering model selection.",
  "recorder": {
    "path": "docs/rse/wayfinder/tickets/04a-close-residual-trigger.md",
    "action": "Record the trigger decision and resolve this ticket."
  },
  "priority": 40
}
```

## Resolution

Open. Silence leaves the trigger unaccepted.
