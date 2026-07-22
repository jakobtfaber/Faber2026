# Implementation Summary: V4 census-gap extension

---
**Date:** 2026-07-15
**Author:** Codex
**Status:** Implemented; manual verification pending
**Plan Reference:** [plan-v4-census-gap-extension.md](../plan/plan-v4-census-gap-extension.md)
---

## Overview

The frozen 49-row foreground census now has an append-only, adjudicated
three-row extension. The two weak-redshift galaxy candidates remain
inconclusive, the WHL12 cluster is confirmed but lacks adopted cluster-model
inputs, and all three rows are budget-ineligible. The generated foreground
table and manuscript disclose them; Table 4 is unchanged.

**Final Status:** automated implementation and validation complete; two owner
wording/model-scope checks remain manual.

## Plan Adherence

The implementation followed
[plan-v4-census-gap-extension.md](../plan/plan-v4-census-gap-extension.md).

Deviations:

- The reproducible cluster geometry is 614.33 kpc (captured discovery output:
  613.99 kpc), not the continuation handoff's rounded 608 kpc. The manuscript
  records both rather than silently selecting one.
- The local sightline-budget integration run excludes the existing
  `test_budget_ingests_allexp_joint_marginal`, whose required fit artifact is
  absent in a clean checkout. GitHub's complete `uvx nox -s tests` job passed
  on PR #186.

## Phases Completed

### Phase 1: Registry extension

- Added `data/census_extensions/v4_extension.csv`.
- Added idempotent append/schema/key validation and derived budget flags.
- Regenerated the checked-in registry to 52 unique rows.

### Phase 2: Generated foreground table

- Added three named rows and removed the FRB 20221113A no-candidate row.
- Tightened table-to-registry parity to cover named extension IDs.
- Regenerated the FLITS export; budget inputs/exports stayed unchanged.

### Phase 3: Manuscript synchronization

- Synced the generated table, observations counts/completeness discussion, and
  Appendix B cluster caveat.
- Pinned FLITS merge `a70b9c54817a94d2739eaa95860333e6e3f03c0a`.
- Recompiled the 36-page manuscript successfully.

## Files Modified

Created in FLITS:

- `galaxies/foreground/data/census_extensions/v4_extension.csv`

Modified in FLITS:

- `.gitignore`
- `galaxies/foreground/census_registry.py`
- `galaxies/foreground/data/intervening_census_registry.csv`
- `galaxies/foreground/foreground_table_data.json`
- `galaxies/foreground/foreground_table_emitter.py`
- `galaxies/foreground/test_census_registry.py`
- `galaxies/foreground/test_foreground_table_emitter.py`
- `exports/foreground_table.tex`

Modified in Faber2026:

- `foreground_table.tex`
- `sections/observations.tex`
- `sections/appendix.tex`
- `pipeline` gitlink

No files were deleted.

## Verification Results

### Automated Verification

- `FLITS_FOREGROUND_SCRATCH=galaxies/foreground/data/frozen_census uv run rtk pytest galaxies/foreground/test_census_registry.py -q` — 10 passed.
- `uv run rtk pytest galaxies/foreground/test_foreground_table_emitter.py -q` — 4 passed.
- `uv run rtk pytest galaxies/foreground/test_sightline_budget.py -q -k 'not test_budget_ingests_allexp_joint_marginal'` — 19 passed, 1 skipped.
- `uv run python -m galaxies.foreground.foreground_table_emitter --check` — exact export parity.
- Focused `ruff check` — passed.
- Registry invariant — 52 rows; 30 confirmed, 15 inconclusive, 7 refuted; unique keys; 3 extension rows; 0 extension rows budget-eligible.
- `cmp -s foreground_table.tex pipeline/exports/foreground_table.tex` — passed.
- `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex` — passed; 36-page PDF.
- FLITS PR #186 GitHub `uvx nox -s tests` (Python 3.12) — passed.
- Codex and Claude automated PR reviews — no issues found.

### Manual Verification

Pending owner confirmation:

- The table wording does not imply that the two weak photo-z values are
  validated redshifts.
- WHL J115048.0+714428 should remain disclosed but unmodeled until a separate
  cluster-identification/mass decision is made.

## Reproducibility

Environment and code:

- Faber2026 base: `2f9ef717`; implementation through `f76b85f` before this log.
- FLITS: `a70b9c54817a94d2739eaa95860333e6e3f03c0a` (PR #186).
- Local clean worktree used a fresh uv environment, CPython 3.13.13 on macOS;
  CI independently passed with Python 3.12 and the committed `uv.lock`.
- No random sampling is used by this extension.

Input hashes:

- `v4_extension.csv`: `sha256:c3284c954040cfa0d9363944336118b30f33249ab30e81eeac010d7d7e3817ed`
- `intervening_census_registry.csv`: `sha256:8e1998fd41b42e982cb2cdf4967e69eb028df1037caa1cf061578bb6ec2cab97`
- `uv.lock`: `sha256:bd703e22973732448d6167307dd29547a2c7843c01316ec03b0a1d2688473e0f`

Minimal clean-worktree reproduction:

```bash
cd pipeline
FLITS_FOREGROUND_SCRATCH=galaxies/foreground/data/frozen_census \
  uv run pytest galaxies/foreground/test_census_registry.py -q
uv run pytest galaxies/foreground/test_foreground_table_emitter.py -q
uv run python -m galaxies.foreground.foreground_table_emitter --check
cd ..
cmp -s foreground_table.tex pipeline/exports/foreground_table.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

This reproduction was run successfully in the fresh parent worktree after the
merged submodule pin was installed.

## Issues Encountered

- The live NED `astroquery` handshake timed out after 60 seconds. No verdict
  was upgraded on that failed query.
- A concurrent repository process left `packed-refs.lock`; the rebase itself
  completed and no process owned the lock when checked. The lock was not
  deleted by this task.
- `origin/main` advanced during implementation; the manuscript branch was
  rebased onto `2f9ef717` before the submodule pin was added.

## Remaining Work

- Owner manual verification of the two wording/model-scope criteria above.
- Merge the Faber2026 PR after that confirmation.

## References

- [Plan](../plan/plan-v4-census-gap-extension.md)
- [Research](../research/research-v4-census-gap-extension.md)
- [FLITS PR #186](https://github.com/jakobtfaber/dsa110-FLITS/pull/186)

