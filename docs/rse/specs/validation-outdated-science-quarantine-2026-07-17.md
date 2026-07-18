# Validation Complete

> Validated against `docs/rse/specs/plan-outdated-science-quarantine-2026-07-17.md` / `docs/rse/specs/implement-outdated-science-quarantine-2026-07-17.md`
> at commit `d09aceb7` on `2026-07-17`.

## Overall Status: ✅ Ready

## Summary

- Phases: 3 of 3 fully implemented; parent PR #131 is published.
- Automated Checks: 10 passing, 0 implementation failures.
- Manual Testing: 1 later owner-review item, intentionally outside this migration.
- Critical Issues: 0.
- Important Issues: 0.

## Implementation Status

### Phase 1: Pipeline quarantine

**Status:** ✅ Fully implemented

- Exact-byte artifacts preserved beneath the dated quarantine root.
- Current-looking paths are absent, tombstoned, or redirected.
- Historical producer defaults write only under quarantine.
- Focused and dependency-complete tests pass.
- Pipeline PR #202 merged at `23fbd295`.

### Phase 2: Parent manuscript quarantine

**Status:** ✅ Fully implemented

- Three obsolete tables and the full old ledger are preserved under quarantine.
- Active TeX no longer inputs or interprets them.
- The fail-closed two-screen product remains active.
- Manifest, catalog, generator, prose, and tests agree on the new boundary.

### Phase 3: Pipeline integration

**Status:** ✅ Fully implemented

- Parent gitlink advances from `17d9d266` to `23fbd295` by ancestry.
- The full imported range was reviewed and documented.
- Parent tests, audit, and PDF build passed against the new pin.
- Closeout checks pass in clean isolated worktrees.

## Automated Verification Results

### Passing Checks

- ✅ Pipeline focused suite — 15 passed.
- ✅ Pipeline frozen-uv suite — 788 passed, 8 skipped, 1 xfailed; the nine
  dynesty-dependent collection failures were environment-only.
- ✅ Pipeline clean Conda `flits` rerun of those nine tests — 9 passed.
- ✅ Parent `PYTHONPATH=. python3 -m pytest -q tests` — 151 passed, 1 xfailed.
- ✅ Parent focused quarantine/propagation/consistency suite — 23 passed.
- ✅ `python3 scripts/consistency_audit.py` — clean.
- ✅ `latexmk -pdf -g -interaction=nonstopmode -halt-on-error main.tex` —
  succeeded, 37 pages.
- ✅ `main.fls` reachability audit — fail-closed two-screen table present; all
  three quarantined tables absent.
- ✅ `git diff --check` — clean in both repositories.
- ✅ `agent-closeout-check` — passed for both clean isolated worktrees; no
  restart inventory or dirty-state packet required.

All automated implementation checks passed. The dsa110-FLITS merge-commit
GitHub workflow was still running when this report was written and is treated as
a publication check, not a substitute for the completed local validation.

## Code Review Findings

### What Matches Plan

- Quarantine is dated, indexed, path-preserving, and reversible.
- No quarantined bytes were deleted or silently regenerated at active paths.
- Active manuscript claims now match the fail-closed readiness state.
- The parent and nested repository were committed and reviewed independently.
- The primary mixed-dirty checkout was not modified.

### Deviations from Plan

- **Foreground-attribution parity changed to snapshot preservation.**
  - **Reason:** Current inputs no longer recreate the old frozen CSV; Wilhelm
    coherence and DM-budget cells drift.
  - **Impact:** Tests verify exact snapshot retention and schema, while the
    generator writes only to quarantine.
  - **Assessment:** Acceptable and scientifically safer than asserting false
    reproducibility.
- **Pipeline merge preceded completion of a non-required merge-commit workflow.**
  - **Reason:** Focused tests, the near-full suite, clean-environment dependency
    reruns, diff checks, and closeout had already passed.
  - **Impact:** The workflow remains a publication check and must be observed
    before final parent delivery.
  - **Assessment:** Acceptable, provided the final workflow succeeds.

### Potential Issues

No implementation issue was identified. Restoration from quarantine must not be
treated as restoration of scientific trust; the documented review prerequisites
still apply.

## Manual Testing Required

1. **Later scientific disposition review**
   - Review each indexed family with its stated prerequisites.
   - Decide whether to delete, rehabilitate, or retain it indefinitely.
   - Expected outcome: no product returns to an active path solely because its
     bytes were restored.

This is intentionally deferred by the owner's request to re-examine the results
before removal.

## Recommendations

### Critical (Must Fix Before Merge)

None.

### Important (Should Fix)

None.

### Nice to Have

- Add a future disposition date or owner column to each quarantine index when
  the scientific review is scheduled.

### Follow-Up Work

- Complete the manual disposition review before deleting or promoting anything.

## References

- Plan: `docs/rse/specs/plan-outdated-science-quarantine-2026-07-17.md`
- Implementation: `docs/rse/specs/implement-outdated-science-quarantine-2026-07-17.md`
- Pipeline PR: https://github.com/jakobtfaber/dsa110-FLITS/pull/202
- Parent PR: https://github.com/jakobtfaber/Faber2026/pull/131
