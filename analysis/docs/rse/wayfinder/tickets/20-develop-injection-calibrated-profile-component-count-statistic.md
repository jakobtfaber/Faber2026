# Develop an injection-calibrated profile-component-count statistic

- Type: `wayfinder:task` (AFK)
- Status: scientific gate pending — implementation contract ready (2026-07-23)
- Assignee: Codex
- Blocked by: —
- Map: [ApJ submission](../map-apj-submission.md)
- Delegation: [Standing delegated decision authority](../standing-delegation-2026-07-20.md)

## Charter

This is the non-blocking successor to the resolved blocker/defer decision in
[ticket 05](05-profile-component-statistic-blocker-decision.md) and the
temporary validation-guard decision in
[ticket 15](15-count-audit-remediation-standing-method.md).

Scope: a sample-wide, known-truth-injection-calibrated component-count-setting
procedure. The procedure must be calibrated against known-truth synthetic
injections before its component-count output may be used to set manuscript
component counts in a future campaign.

This ticket is non-blocking for the current submission. The current submission
continues to use visual/heuristic component vetting with the temporary
neighbor-count protocol from ticket 15 as a guard.

## Predecessors

- [Decide whether the profile-component-count statistic blocks submission](05-profile-component-statistic-blocker-decision.md) — resolved (2026-07-22)
- [Adopt count-audit remediation as standing method](15-count-audit-remediation-standing-method.md) — resolved (2026-07-22)

## Agent-delegable work completed

The [implementation contract](../../specs/plan-profile-component-count-calibration.md)
identifies the production profile-likelihood seam, required injection grid,
comparison invariants, output schema, test slices, and fail-closed behavior.
`scripts/profile_component_calibration.py` validates evidence packets and
prevents calibration output from setting manuscript counts before ratification.

The older autocorrelation-function trigger plan is explicitly not accepted as
this statistic: it counts scattering scales, not temporal profile components.

## Scientific gate

After the full `dsa110-FLITS` injection campaign, the manuscript owner must
ratify acceptable overcount and undercount rates, the supported injection
domain, and out-of-domain behavior. This remains non-blocking for the current
submission; current visual/heuristic counts and ticket 15 guards are unchanged.
