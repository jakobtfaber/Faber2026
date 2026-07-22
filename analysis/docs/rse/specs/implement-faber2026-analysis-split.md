# Implementation Summary: Faber2026 analysis repository split

---
**Date:** 2026-07-22
**Author:** AI Assistant
**Status:** In Progress
**Plan Reference:** [plan-faber2026-analysis-split.md](plan-faber2026-analysis-split.md)

---

## Overview

Split research, control, diagnostics, and tests into the public
`Faber2026-analysis` repository and mount it beside `pipeline/` in the compact
manuscript repository. Scientific values and the 37-page TeX closure remain
unchanged.

**Final Status:** Partially complete. Local implementation passes; publication,
independent validation, and live Overleaf verification remain.

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
- Phase 4: local manuscript and scientific checks pass; publication and manual
  Overleaf checks remain.

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
- Mounted scientific suite: 222 passed, 1 expected failure.
- Figure approval and state-drift gates: passed.
- Clean `latexmk` build: 37 pages; no recorder inputs under either submodule.
- PDF SHA-256: `806fc47ac58810b8ca3fc5ff1a29434d67efe306da3e0222079b495f164f79d9`.
- Knowledge-base regression tests: 9 passed.
- Knowledge-base source inventory: 354 documents, 696 code files, 90 pipeline
  configuration files, 63 bibliography entries, and 2,294 git records.

## Issues Encountered

- The moved knowledge base silently omitted manuscript bibliography and
  pipeline configuration because its root remained analysis-local. Fixed with
  an explicit three-root configuration and regression coverage.
- Embedding progress was hidden by buffered output. Indexing is now run with
  observable source counts and database progress checks during closeout.

## Remaining Work

- [ ] Finish the local embedding pass and verify hybrid retrieval.
- [ ] Run both repository integrity and closeout checks.
- [ ] Publish and merge the analysis integration pull request.
- [ ] Pin merged analysis `main`; validate and publish the parent pull request.
- [ ] Run independent plan validation before parent merge.
- [ ] Pull through Overleaf GitHub Sync and confirm the 37-page compile.

## References

- [Research: Faber2026 analysis repository split](research-faber2026-analysis-split.md)
- [Handoff](handoff-2026-07-21-21-49-faber2026-analysis-split.md)

---

**Implementation resumed by AI Assistant on 2026-07-22.**
