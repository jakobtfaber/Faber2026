# Fail-close the invalid expanded-catalog validation

- Type: `wayfinder:task` (AFK)
- Status: open
- Assignee: Codex
- Blocked by: none
- Map: [Expanded foreground catalog repair](../map-expanded-foreground-catalog-repair.md)
- Delegation: [Standing delegated decision authority](../standing-delegation-2026-07-20.md)
- Triage: `ready-for-agent`

## Question

What exact status and machine-readable gate prevent the current validation from
being cited as accepted while preserving its findings as superseded evidence?

## Acceptance decision

Replace `Ready / Verified` with `FAILED — superseded; do not use`. Record the
wrong Moster input units, incorrect Cluver equation label and missing rest-frame
condition, incomplete and non-deterministic matches, invalid Stern interpretation,
wrong morphology summary, absent pinned CSV, and unversioned Figure 3 input.
Any validator must exit nonzero until the rebuilt catalog and independent report
both pass.
