# Validation: Wayfinder blocker execution routes

> Phase 1 validated against
> `plan-wayfinder-blocker-execution-routes-2026-07-22.md` at working-tree base
> `eb550d9` on 2026-07-22. Later phases remain in progress.

## Overall Status: Phase 1 ready; campaign in progress

## Implementation Status

### Phase 1: Repair tracker route and close the Zach baseline

Fully implemented.

- Reconciled the board and regression test with the detailed route merged by
  pull request 6; did not restore the superseded deleted-ticket route.
- Resolved the Zach baseline after owner review.
- Recorded the owner's pre-bad-channel-mask clarification.
- Preserved the failed RFI/stationarity verdict and science no-go.
- Preserved CHIME-method ratification's dependency on complete input
  remediation and campaign rerun.
- Added a focused regression test for route existence, blocker targets, and
  fail-closed status.

### Phases 2–7

In progress. No completion claim is made here.

## Automated Verification Results

- PASS — `pytest -q tests/test_wayfinder_certified_data_route.py`:
  3 passed after reconciliation.
- PASS — `FABER2026_ROOT=... pytest -q
  tests/test_wayfinder_certified_data_route.py
  tests/test_h17_source_data_layout.py tests/test_kb.py`: 24 passed.
- PASS — relative-link audit over the map, all ticket files, the Zach
  validation, research, and plan: 61 files checked, zero missing targets.
- PASS — `git diff --check`.

The first combined test attempt lacked `FABER2026_ROOT` and failed during
knowledge-base test collection. The clean rerun set the required manuscript
root explicitly and passed; no test was skipped.

## Code Review Findings

### Matches the plan

- The detailed route is the already-merged pull request 6 route; this change
  only reconciles the board and records the owner's clarification.
- The Zach resolution grants only the nominal-grid/source-mask contract.
- The final bad-channel mask, bandpass, interference removal, dispersion
  measure, time axis, and science outputs remain open and explicitly gated.
- Original input data are untouched.

### Deviations

- The initial plan proposed restoring historical tickets 17–22. Concurrent
  pull request 6 merged a more precise route, so the implementation preserves
  that route and removes the duplicate restoration.

### Potential issues

- The route exposes substantial owner-gated work; closing the Zach baseline does
  not make the CHIME method or any result science-ready.
- The remaining phases must rebase after each concurrent ticket merge to avoid
  map conflicts.

## Manual Testing

- Completed: owner reviewed the Zach diagnostic on 2026-07-22 and accepted the
  grid/mask contract and no-go decision, clarifying that the figure is before
  the bad-channel mask.
- Still required later: review of final data cards, 36 waterfalls, fit
  diagnostics, both-band autocorrelation functions, and scientific trust
  promotion.

## Recommendations

### Critical

- Do not promote the current RFI/bandpass output or the previous scintillation
  campaign.

### Important

- Merge Phase 1 before resolving downstream CHIME tickets so every blocker
  points to an existing `origin/main` artifact.

### Follow-up

- Continue Phases 2–7 under the plan; replace this report only when the full
  campaign reaches a later validated boundary.

## References

- [Plan](plan-wayfinder-blocker-execution-routes-2026-07-22.md)
- [Research](research-wayfinder-blocker-execution-routes-2026-07-22.md)
- [Zach validation](validation-zach-chime-preprocessing-baseline.md)
