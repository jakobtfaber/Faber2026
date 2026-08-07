# Adopt count-audit remediation as standing method

- Type: `wayfinder:grilling` (HITL)
- Status: resolved (2026-07-22)
- Assignee: Codex controller
- Blocked by: —
- Map: [ApJ submission](../map-apj-submission.md)
- Delegation: [Standing delegated decision authority](../standing-delegation-2026-07-20.md)

## Question

The mass-refit campaign exposed a count-ladder gap: D4 was never launched
campaign-wide and several component counts were hand-assigned. The proposed
remedy is the fixed-s2 neighbor protocol (s2=100, ΔlnZ>5) — but s2=100 can
mode-trap low-count fits (zach fits a wrong steep corner), conflating count
with solution mode. Owner decisions: (a) adopt the neighbor protocol as the
standing count-justification method (with what mode-trap guard)? (b) adopt
the pending neighbor-test count changes (phineas C4 +75, johndoeII C3 +47
with τ-sanity flag, whitney D2/C2 — which moves β off the floor and may
dissolve the whitney "rail")? (c) how does this interact with the
profile-component-count statistic charter (ticket 05) — is the neighbor
protocol the realization of that statistic or a stopgap? Owner morphology
knowledge remains a legitimate ground-truth input (zach D4 precedent).

## Decision — 2026-07-22 (manuscript-owner checkpoint receipt)

Owner accepted the recommendation in
`docs/rse/specs/research-count-audit-remediation-2026-07-20.md`.

- The fixed-gain-variance neighboring-count comparison is adopted as a temporary
  validation step, with the guards listed in the packet.
- It is not a count setter by itself.
- None of the proposed count changes (phineas C4, johndoeII C3, whitney C2/D2,
  zach D4/D5) are adopted.
- Affected counts remain pending until clean, mode-matched, two-gain-prior-arm
  comparisons plus owner morphology review agree.
- The profile-component-count statistic charter is now a distinct successor
  ticket:
  [Develop an injection-calibrated profile-component-count statistic](20-develop-injection-calibrated-profile-component-count-statistic.md).
  The neighbor protocol is a stopgap aid for that statistic, not its completed
  realization.

Owner receipt: [Manuscript-owner governance receipt — 2026-07-22](https://github.com/jakobtfaber/Faber2026-analysis/pull/46#issuecomment-5050854194).
