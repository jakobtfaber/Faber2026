# Validation: F3 manuscript consistency audit

> Validated the F3 subsection of `plan-circulation-readiness.md`, the PR #64
> implementation, and the owner-approved endpoint wording resolution on
> 2026-07-15. This is a scoped F3 verdict, not a validation of the full
> circulation-readiness plan.

## Overall status: complete

The mechanical F3 implementation and all seven PR review threads are validated.
The owner resolved the remaining scientific wording decision on 2026-07-15:
the Methods text retains the square-law endpoint's theoretical
`tau proportional to nu^-4` identity without presenting `alpha=4` as a
quotable observational limit.

## Implementation status

### F3: mechanical consistency audit

**Status:** complete

- Per-section sample counts: implemented against the canonical twelve-row
  `sample_table.tex` roster, with roster parity checks for the DM and budget
  tables and explicit full-sample assertions for every current complete-sample
  claim in the abstract, observations,
  results, TOA, and conclusions sections.
- Retired-language sweep: implemented and clean. The two `sections/budget.tex`
  passages now distinguish the theoretical square-law endpoint from a
  per-sightline turbulence-index measurement.
- Table and figure provenance: implemented for generated `\input{}` targets
  and every reachable `\includegraphics{}` target. Generated tables require
  embedded manifest rows; wildcard figure families require all twelve roster
  assets; pipeline-produced outputs require the pinned `pipeline/` gitlink.
- Cross-references: implemented for duplicate labels and undefined references.
- Portable control state: the machine-local worktree path was removed.
- Static owner board: regenerated after the owner-view change.
- Renderer parity: the DM table producer now emits the same provenance banner
  as the committed generated table.

## Automated verification results

All scoped automated checks passed:

- `python3 -m pytest -q tests/test_consistency_audit.py tests/test_sync_state.py`
  — 22 passed.
- `make test-science` — 76 passed, 1 documented xfail; state drift gate,
  figure approval gate, and journal append test passed.
- `python3 scripts/sync_state.py --check --offline` — 3/3 views match;
  lane and ledger rules pass.
- `python3 scripts/sync_state.py --check` — live state has no stored/live
  contradictions.
- `python3 -m py_compile scripts/consistency_audit.py scripts/render_dm_measurements_table.py`
  — passed.
- `make` — clean 31-page PDF build; extracted rendered text contains the
  intended `tau proportional to nu^-4` and `square-law/exponential endpoint`
  wording.
- `git diff --check` — passed before commit.
- `agent-closeout-check` — passed with all five implementation paths classified
  as task-scoped and no runtime restart required.

The audit command now exits 0 with no findings.

## Code review findings

### What matches the plan

The implementation now covers every mechanical check named by F3: sample
counts, retired language, table/figure provenance against the pinned pipeline,
and cross-references. Regression tests exercise both the passing repository
state and failures for changed full-sample counts, an incomplete wildcard
figure family, an unmanifested figure, and an unmanifested generated table.

### Deviations

- The validation is intentionally limited to F3. Other unchecked phases in the
  circulation-readiness plan were not assessed.
- The owner-approved wording preserves the theoretical `tau proportional to
  nu^-4` square-law endpoint while removing result-like `alpha=4` shorthand.
  This resolves a narrow F1 sub-item; it does not mark the broader F1 rewrite
  complete.

### Potential issues

No additional implementation defects were identified. All seven PR #64 review
threads were resolved before merge.

## Manual testing required

No additional manual software test is required.

## Recommendations

### Critical

None.

### Important

None for the review-fix implementation.

### Follow-up

None for F3. The broader scattering re-fit, geometry adjudication, and F1
manuscript restructuring remain governed by the circulation-readiness plan.

## References

- Plan: [plan-circulation-readiness.md](../plan/plan-circulation-readiness.md), F3.
- Findings: [audit-f3-findings.md](../audit/audit-f3-findings.md).
- Pull request: <https://github.com/jakobtfaber/Faber2026/pull/64>.
