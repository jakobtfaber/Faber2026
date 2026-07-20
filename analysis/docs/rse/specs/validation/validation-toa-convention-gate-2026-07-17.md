# Validation: Fail-closed ToA convention

> Validated the implementation of
> [plan-toa-convention-gate-2026-07-17.md](../plan/plan-toa-convention-gate-2026-07-17.md)
> on branch `ms/toa-convention-audit-20260717`, based on Faber2026
> `e4b79f80` with pinned pipeline `5fb387e`.

## Overall status: ready

The implementation matches the plan and preserves the pipeline's fail-closed
science semantics. The manuscript, embedded decomposition, manifest, and
automated audit now agree that the current citable quantity is the observed
peak. Diagnostic model-$t_0$ values are retained but not adopted.

## Requirements traceability

| Requirement | Evidence | Verdict |
|---|---|---|
| Preserve candidate model results | `model_corrected_offset_ms` is still read only as a diagnostic comparator | Pass |
| Fail closed while validation is incomplete | Plot producer and consistency audit require unvalidated `measured_offset_ms == peak_measured_offset_ms` | Pass |
| Remove stale promotion claims | ToA prose and manifest describe the two-part adoption gate and current `MARGINAL`/unreviewed state | Pass |
| Keep Figure 1 and scintillation work isolated | No Figure-1, scintillation, or pipeline-gitlink path is modified | Pass |
| Preserve reproducibility | Producer, tests, manifest, research note, implementation summary, and this report are included | Pass |

## Automated verification

- `make test-science` — 132 passed, 1 known xfail; offline sync-state,
  figure-approval, and journal gates passed.
- `uv run --project pipeline --frozen pytest -q
  tests/test_consistency_audit.py tests/test_toa_offset_decomposition.py`
  — 17 passed.
- `uv run --project pipeline --frozen python -m pytest -q -ra
  --strict-config --strict-markers tests/test_consistency_audit.py
  tests/test_toa_offset_decomposition.py tests/test_association_diagnostics.py
  tests/test_codetection_data_grid.py` — 33 passed, 1 known xfail.
- `uv run --frozen python -m pytest -q -ra --strict-config --strict-markers
  tests/test_crossmatching_notebook_reproduction.py tests/test_association.py`
  from the pinned `pipeline/` environment — 22 passed.
- `uv run --project pipeline --frozen python scripts/consistency_audit.py`
  — clean.
- `latexmk -g -pdf -interaction=nonstopmode -halt-on-error main.tex`
  — success, 54 pages.
- `git diff --submodule=log --check` — passed; gitlink remains `5fb387e`.
- FLITS docstring PR #198 — merged at `3b40a96d` after 6 focused tests and
  Ruff passed; the parent pin deliberately remains `5fb387e`.

The single xfail is the repository's pre-existing class-aware sample-table
producer mismatch at the pinned FLITS revision. The ToA convention change does
not modify that producer or its generated table.

## Manual verification

The standalone decomposition and compiled manuscript pages were rendered and
reviewed. Plot labels and caption say observed peak; the diagnostic model is
clearly gated in the surrounding prose; every marker is inside the plot frame,
including the +6.2 ms point. Independent post-fix visual QA reached the same
result.

## Scope and remaining science decision

Validation does not certify the candidate model fits. Promotion remains a
science decision requiring `PASS` fit quality plus human review of the fit
diagnostics. Figure 1's separate model-anchor lane must reconcile its own
producer and `REPRODUCE.md` wording without being folded into this PR.

## Verdict

Ready for review. The implementation is internally consistent, tested,
visually checked, and leaves the pipeline gitlink unchanged.
