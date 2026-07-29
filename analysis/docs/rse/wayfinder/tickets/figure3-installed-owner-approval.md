# Approve the installed Figure 3

- Type: `wayfinder:task` (HITL)
- Status: open
- Assignee: manuscript owner
- Blocked by: none
- Map: [ApJ submission](../map-apj-submission.md)
- GitHub: [Issue #206](https://github.com/jakobtfaber/Faber2026/issues/206)

## Owner decision card

```json
{
  "id": "figure3-approval",
  "kind": "visual",
  "title": "Figure 3 approval",
  "decision": "Approve the exact installed Figure 3 bytes for the manuscript?",
  "recommended": {
    "choice": "approve",
    "reason": "The independent census validation passes and the staged bytes match the manuscript exactly."
  },
  "choices": [
    {
      "id": "approve",
      "label": "Approve the exact figure bytes."
    },
    {
      "id": "revise",
      "label": "Request a revision and state the required visual change."
    }
  ],
  "context": [
    "All six independent census, source, matching, coverage, radius, and figure-content checks pass.",
    "The staged review artifact and installed manuscript figure are byte-identical.",
    "This approval is visual; it does not replace the recorded scientific validation."
  ],
  "evidence": [
    {
      "label": "Exact Figure 3 PDF",
      "path": "figure_review/artifacts/staging/fig3_halo_grid/figures/sightline_halo_grid.pdf",
      "sha256": "281e4bf4c9d910c070cb822195a743920a7ecf14e249c924521e359a9d788a75"
    },
    {
      "label": "Independent validation",
      "path": "docs/rse/specs/evidence/foreground-census-analysis-only-2026-07-29/validation.json",
      "sha256": "577ccb27f97e6a85009df8b64ba90c9b49025ad3ccbc41fcac9eb2754e2cd36a"
    },
    {
      "label": "Reproduction receipt",
      "path": "docs/rse/specs/receipt-foreground-census-analysis-only-2026-07-29.md",
      "sha256": "c13404f855275f53240a5c6255d5964cb6b48d1b74696facddf3e1eb20840ae0"
    }
  ],
  "effect": "Approval closes the Figure 3 visual gate and permits issue #206 closeout.",
  "recorder": {
    "path": "docs/rse/wayfinder/tickets/figure3-installed-owner-approval.md",
    "action": "Record the owner choice and bind any approval receipt to the exact PDF hash."
  },
  "priority": 10
}
```

## Resolution

Open. Silence leaves the figure unapproved.
