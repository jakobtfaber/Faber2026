# Validation Complete

> Validated against `docs/rse/specs/plan-fig1-observed-peak-audit.md` /
> `docs/rse/specs/implement-fig1-observed-peak-audit.md` at commit `773a79a2`
> on 2026-07-17.

## Overall Status: Candidate ready; manuscript promotion blocked

## Summary

- Phases: 4 of 4 implemented for the candidate/provenance PR.
- Automated checks: 6 passing, 0 failing.
- Manual testing: exact-byte manuscript-owner review remains required.
- Critical issues for candidate PR: 0.
- Critical issues for manuscript promotion: 1 science gate plus owner approval.

## Implementation Status

### Phase 1: correct and test the producer

Status: fully implemented. The model-ToA helpers and dependency were removed;
both fitted and data-only rows pass `extra_shift_ms=None`; unit tests and
reproducibility documentation describe observed-profile timing.

### Phase 2: preserve audit evidence

Status: fully implemented. The focused batch records all 24 byte-pinned inputs,
12 DSA and 12 CHIME header/order summaries, both drift estimators, the explicit
gate failure, and only the task-scoped previous Figure 1 decision.

### Phase 3: generate a candidate, not a promotion

Status: fully implemented. Candidate SHA-256
`979e616b2d82c395080fa32c5f5554b64568849683c0129eb4b01f55eb63915a`
is staged with a preview and pending decision. The protected target, receipt,
and caption are unchanged.

### Phase 4: validate and publish the review branch

Status: validation complete; push and PR are the remaining publication actions.

## Automated Verification Results

All automated verification checks passed:

- `make test-science` — 132 passed, 1 expected failure; offline state check,
  figure approval gate, and journal append test passed.
- `python scripts/consistency_audit.py` in clean `flits` Conda — clean.
- `make` / `latexmk` — manuscript compiled successfully after rebasing onto
  `origin/main` at `26e37e4e` with pipeline pin `17d9d266`.
- `scripts/audit_fig1_frequency_axes.py` — regenerated exact committed SHA-256
  `bd5158a6620a3df82a3448174c0bd925907a2a8bcbecd6ad2e87a16ee2d83a37`.
- `scripts/audit_fig1_residual_drift.py` — regenerated exact committed SHA-256
  `ccb36c7f727015f441eb5e25d27d25ff4ab02022215320a199a148a2575d3581`.
- `scripts/figure_review.py render/verify` — focused packet validates and the
  existing protected-target gate remains green.

## Code Review Findings

### What matches the plan

- Figure 1 consumes only archival waterfalls plus the adopted-DM catalog.
- Frequency order is explicitly checked rather than inferred from a fixed axis.
- Missing drift fits are fail-closed as `unconstrained`, not counted as zero.
- Review staging is focused and does not import unrelated rejected candidates.

### Deviations from the plan

- The plan anticipated a possible caption update only after promotion. Because
  the science gate failed and exact bytes are unapproved, leaving the caption and
  target unchanged is the required fail-closed outcome.

### Potential issues

- The final `_cntr_bpc.npy` builder remains unverified/lost. The audit establishes
  raw-header order, current product bytes, and display-loader behavior, but does
  not claim a fresh end-to-end rebuild from raw data.
- The EMG gate result is 8 consistent with zero, 7 nonzero, and 9 unconstrained;
  it cannot support an all-panel zero-drift statement.

## Manual Testing Required

1. The manuscript owner must inspect `fig1-gallery` in batch
   `2026-07-17-fig1-observed-peak-audit` and resolve whether the residual-drift
   gate itself is scientifically appropriate.
2. If the gate is resolved favorably, the owner must explicitly approve the
   exact candidate hash before a separate promotion PR changes the target,
   receipt, or caption.

## Recommendations

### Critical before manuscript promotion

- Resolve the failed residual-drift gate and obtain exact-byte owner approval.

### Important

- Preserve the builder-lineage limitation in any data-release claim.

### Nice to have

- Add a direct raw-to-archival reconstruction check if the historical builder
  can be recovered.

### Follow-up work

- After approval, promote through `scripts/figure_review.py`, update the Figure 1
  caption to state the observed-profile convention, rebuild, and rerun closeout.

## References

- Plan: `docs/rse/specs/plan-fig1-observed-peak-audit.md`
- Implementation: `docs/rse/specs/implement-fig1-observed-peak-audit.md`
