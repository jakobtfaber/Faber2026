# Validation: F3 manuscript consistency audit

> Validated the F3 subsection of `plan-circulation-readiness.md` and the PR #64
> review-fix implementation through commit `fa225ca` on 2026-07-15. This is a scoped
> F3 verdict, not a validation of the full circulation-readiness plan.

## Overall status: decision pending

The mechanical F3 implementation and all four PR review fixes are validated.
F3 is not complete because the audit still reports the two deliberately
owner-gated `alpha=4` passages in `sections/budget.tex`.

## Implementation status

### F3: mechanical consistency audit

**Status:** validated; owner decision remains

- Per-section sample counts: implemented against the canonical twelve-row
  `sample_table.tex` roster, with roster parity checks for the DM and budget
  tables and explicit full-sample assertions for every current complete-sample
  claim in the abstract, observations,
  results, TOA, and conclusions sections.
- Retired-language sweep: implemented; the two known `sections/budget.tex`
  findings remain visible rather than being suppressed.
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

- `python3 -m pytest -q tests/test_consistency_audit.py` — 8 passed.
- `make test-science` — 76 passed, 1 documented xfail; state drift gate,
  figure approval gate, and journal append test passed.
- `python3 scripts/sync_state.py --check --offline` — 3/3 views match;
  lane and ledger rules pass.
- `python3 -m py_compile scripts/consistency_audit.py scripts/render_dm_measurements_table.py`
  — passed.
- `latexmk -pdf -g -interaction=nonstopmode -halt-on-error main.tex` — clean
  31-page PDF build.
- `git diff --check` — passed before commit.
- `agent-closeout-check` — passed with all five implementation paths classified
  as task-scoped and no runtime restart required.

The audit command itself exits 1 by design and reports exactly two findings:
`sections/budget.tex:138` and `sections/budget.tex:162`, both retired
`alpha=4`-limit language awaiting the owner/scattering-gate decision.

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
- The two `alpha=4` passages were not rewritten because that is an explicit
  scientific wording decision, not a mechanical audit repair.

### Potential issues

No additional implementation defects were identified. GitHub review threads
have not been replied to or resolved; those outward writes require explicit
user authorization under the review-feedback workflow.

## Manual testing required

No additional manual software test is required. The remaining action is an
owner decision: retain/reframe the two scattering-methodology passages now, or
defer their rewrite to the scattering gate.

## Recommendations

### Critical

None.

### Important

None for the review-fix implementation.

### Follow-up

- Obtain the owner decision on the two `sections/budget.tex` findings.
- After that decision, rerun the audit and update the F3 lane status.
- Request a fresh PR review; reply to or resolve the four original threads only
  when explicitly authorized.

## References

- Plan: [plan-circulation-readiness.md](plan-circulation-readiness.md), F3.
- Findings: [audit-f3-findings.md](audit-f3-findings.md).
- Pull request: <https://github.com/jakobtfaber/Faber2026/pull/64>.
