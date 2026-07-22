# Implementation Summary: Faber2026 analysis repository split

---
**Date:** 2026-07-22
**Author:** AI Assistant
**Status:** Automated validation complete; manual Overleaf gate pending
**Plan Reference:** [plan-faber2026-analysis-split.md](plan-faber2026-analysis-split.md)

---

## Overview

Split research, control, diagnostics, and tests into the public
`Faber2026-analysis` repository and mount it beside `pipeline/` in the compact
manuscript repository. Scientific values and the 37-page TeX closure remain
unchanged.

**Final Status:** Ready for parent merge. Automated and remote checks pass;
live Overleaf verification remains.

## Plan Adherence

Phases 1--3 followed the plan. Phase 4 found one incomplete path migration:
the knowledge base still resolved the analysis repository as the manuscript
root. The fix now resolves separate analysis, manuscript, and pipeline roots
and tests their combined source inventory.

## Phases Completed

- Phase 1: boundary recorded and fail-closed test added.
- Phase 2: filtered history published as `Faber2026-analysis` `main` at
  `520f4c4`.
- Phase 3: parent reduced to its allowlist; mounted analysis integration and
  two-gitlink interface implemented.
- Phase 4: local, fresh-clone, and pull-request checks pass; manual Overleaf
  checks remain.

## Key Changes

- Parent keeps TeX, generated tables, final figure assets, and exact analysis
  and pipeline pins.
- Analysis owns research documents, scripts, tests, diagnostics, and review
  state.
- Mounted tools distinguish analysis, manuscript, and pipeline roots.
- Knowledge-base adapters index all three roots and keep the database under
  the analysis repository.

## Verification Results

- `tests/test_manuscript_boundary.py`: 3 passed.
- Mounted scientific suite: 223 passed, 1 expected failure.
- Figure approval and state-drift gates: passed.
- Clean `latexmk` build: 37 pages; no recorder inputs under either submodule.
- Fresh local PDF SHA-256:
  `a6d0fef64861b3f94071f66da31643ab4e483a6f760839d26c481ea79da26c3a`.
- Knowledge-base regression tests: 9 passed.
- Knowledge-base source inventory: 359 documents, 697 code files, 90 pipeline
  configuration files, 63 bibliography entries, and 2,321 git records.
- Final knowledge base: all 14,581 chunks embedded; vector retrieval passed.
- Fresh recursive clone: both public pins resolved; boundary and integrity
  checks passed.
- Parent pull request #179: mergeable; all four checks passed.

## Issues Encountered

- The moved knowledge base silently omitted manuscript bibliography and
  pipeline configuration because its root remained analysis-local. Fixed with
  an explicit three-root configuration and regression coverage.
- Embedding progress was hidden by buffered output. Indexing is now run with
  observable source counts and database progress checks during closeout.

## Remaining Work

- [x] Finish the local embedding pass and verify hybrid retrieval.
- [x] Run both repository integrity and closeout checks.
- [x] Publish and merge the analysis integration pull request.
- [x] Pin merged analysis `main`; validate and publish the parent pull request.
- [x] Run independent plan validation before parent merge.
- [ ] Pull through Overleaf GitHub Sync and confirm the 37-page compile.

## References

- [Research: Faber2026 analysis repository split](research-faber2026-analysis-split.md)
- [Handoff](handoff-2026-07-21-21-49-faber2026-analysis-split.md)

---

**Implementation resumed by AI Assistant on 2026-07-22.**
