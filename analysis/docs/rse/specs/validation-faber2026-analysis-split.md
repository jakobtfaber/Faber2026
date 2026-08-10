# Validation Complete

> Validated against `plan-faber2026-analysis-split.md` /
> `implement-faber2026-analysis-split.md` at analysis commit `e02114c` and
> parent commit `98709f0` on 2026-07-22.

## Overall Status: Ready for merge

- Phases: 4 of 4 implemented.
- Automated checks: all passing.
- Manual testing: 2 Overleaf checks remain.
- Critical issues: 0.
- Important issues: 0 before merge; manual gate required immediately after.

## Implementation Status

### Phase 1: Record and test the boundary

**Status:** Fully implemented.

- Exact allowlist and two-gitlink checks exist.
- Editable and total-tree size limits pass.

### Phase 2: Extract and publish analysis history

**Status:** Fully implemented.

- Public analysis repository exists.
- Filtered history, sample history, and repository integrity pass.

### Phase 3: Replace parent paths with the analysis gitlink

**Status:** Fully implemented.

- Parent tree matches the allowlist.
- Analysis and pipeline are sibling mode-`160000` gitlinks.
- Automation, figure producers, and provenance paths use the mounted analysis
  repository.

### Phase 4: Validate and publish

**Status:** Automated work complete; manual Overleaf gate pending.

- Analysis pull requests #1 and #2 merged.
- Parent pull request #179 is mergeable with all checks passing.
- Superseded parent pull request #172 is closed; branch retained.

## Automated Verification Results

All automated checks passed.

- `python3 -m pytest tests/test_manuscript_boundary.py -q`: 3 passed.
- `make test-science`: 223 passed, 1 expected failure; state, figure approval,
  and journal checks passed.
- Clean `latexmk`: 37 pages, 8,848,845 bytes; no recorder inputs under
  `analysis/` or `pipeline/`.
- `make kb-index`: 14,581 of 14,581 chunks embedded; vector-only bibliography
  retrieval returned the expected dispersion-measure literature.
- `git fsck --full`: parent and analysis passed.
- Fresh `--recurse-submodules` clone: analysis `e02114c`, pipeline `ab6af1f`;
  boundary and integrity checks passed.
- GitHub pull request #179: root scientific tests, table parity, and two
  security checks passed.

## Code Review Findings

### What Matches the Plan

- Manuscript compile closure and scientific values remain in the parent.
- Research/control files and their history remain public in analysis.
- Parent boundary is fail-closed and below Overleaf limits.
- Pipeline pin did not change.

### Deviations from the Plan

- Knowledge-base root migration was incomplete in the first implementation.
  It now resolves analysis, manuscript, and pipeline separately, with regression
  coverage. Assessment: necessary and correct.
- Fifteen analysis-owned paths landed on parent `main` during migration. Their
  eleven commits were replayed into analysis; all 15 hashes matched before the
  parent merge kept them deleted. Assessment: preserves both concurrent work
  and the intended boundary.

### Potential Issues

- Overleaf acceptance of the second unexpanded gitlink is not proven until the
  live GitHub Sync pull. This is the planned manual gate, not an automated
  validation failure.

## Manual Testing Required

1. In the existing Overleaf project, pull the merged parent through GitHub Sync.
   Expected: sync completes without repository-size or submodule errors.
2. Recompile in Overleaf.
   Expected: successful 37-page manuscript.

## Recommendations

### Critical

None.

### Important

- Perform both Overleaf checks immediately after merge. Revert the parent merge
  if GitHub Sync rejects the second gitlink.

### Nice to Have

- None for this migration.

### Follow-Up

- Record the Overleaf outcome in the implementation summary after the live
  gate.

## References

- Plan: [plan-faber2026-analysis-split.md](plan-faber2026-analysis-split.md)
- Implementation: [implement-faber2026-analysis-split.md](implement-faber2026-analysis-split.md)
