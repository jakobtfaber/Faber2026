# Implementation Plan: Outdated science-result quarantine

---
**Date:** 2026-07-17
**Author:** Codex
**Status:** Approved
**Related Documents:**
- [Research: outdated science-result quarantine](research-outdated-science-quarantine-2026-07-17.md)
---

## Overview

Move obsolete science-result bytes into dated, path-preserving quarantine trees
in Faber2026 and pipeline. Remove their compiled/current reachability, redirect
their historical generators to quarantine, and retain the current fail-closed
two-screen readiness product.

**Goal:** No obsolete numerical product remains compiled or presented as a
current source, while every moved byte remains tracked and reproducible for
later review.

**Motivation:** Several revoked or pre-production results survived either in the
compiled manuscript or at paths described as canonical.

## Current State Analysis

- `sections/results.tex:177-245,333-344` compiles two obsolete tables and points
  at the old joint-fit catalog.
- `sections/discussion.tex:82-115` interprets the obsolete foreground/scattering
  alignment table.
- `scripts/build_provisional_propagation_tables.py:260-284` regenerates all three
  tables at manuscript-root paths.
- `pipeline/analysis/beta_campaign/two_screen.py:180-221`,
  `pipeline/results/joint_fit_summary.md`,
  `pipeline/galaxies/foreground/data/sightline_attribution_matrix.csv`, and
  `pipeline/analysis/chime-scintillation/INVENTORY.yaml` remain current-looking.

## Desired End State

- Exact obsolete bytes live under
  `quarantine/2026-07-17-outdated-science/` in their owning repository.
- Each quarantine tree contains an index mapping original paths to reasons and
  review prerequisites.
- The manuscript compiles without the three obsolete tables and without the
  foreground/scattering causal readings.
- Historical producers write only to quarantine; active paths cannot silently
  reappear on regeneration.
- `twoscreen_provisional_table.tex` remains active and fail-closed.
- Pipeline lands separately; the parent gitlink is then advanced deliberately.

## What We're NOT Doing

- [ ] Delete any result bytes.
- [ ] Move legacy-energy products or already suppressed figure families.
- [ ] Refit scattering, remeasure scintillation, or create replacement science.
- [ ] Promote quarantined numbers back into the manuscript.
- [ ] Alter the mixed-dirty primary checkout.

**Rationale:** This change is reversible provenance hygiene, not a new science
campaign or a deletion decision.

## Implementation Approach

Use a dated quarantine in each Git repository and preserve the original relative
path beneath that date where practical. Add regression tests before moving files.
Leave historical computations executable, but redirect their outputs and label
their modules/reports as quarantined. Replace active prose with the current
fail-closed boundary rather than new numerical claims.

## Implementation Phases

### Phase 1: Pipeline quarantine

**Objective:** Remove four misleading pipeline result families from active paths.

**Tasks:**

- [x] Add `tests/test_outdated_science_quarantine.py` asserting that quarantined
  copies exist, old numerical paths are absent or tombstoned, and producers
  target the dated quarantine.
- [x] Run `uv run --frozen pytest -q tests/test_outdated_science_quarantine.py`
  and require the new assertions to fail before implementation.
- [x] Move the beta two-screen JSON/Markdown, joint-fit summary, attribution
  matrix, and legacy CHIME inventory/README with `apply_patch` move operations.
- [x] Redirect `two_screen.py`, `gen_joint_summary.py`, and
  `attribution_matrix.py`; update their tests and navigation documentation.
- [x] Replace attribution-matrix byte parity with snapshot-preservation and
  schema checks because a fresh historical build no longer matches the frozen
  CSV after registry/input drift.
- [x] Run `uv run --frozen pytest -q tests/test_outdated_science_quarantine.py tests/test_joint_summary_reproducible.py galaxies/foreground/test_attribution_matrix.py`.
- [x] Commit only the pipeline quarantine paths and push the feature branch.

**Dependencies:** Pipeline branch `agent/quarantine-outdated-science-20260717`
based on `origin/main` `8f5f06a`.

**Verification:** Old result paths contain no obsolete numerical claims; all
three historical producers write beneath the quarantine root; focused tests pass.

### Phase 2: Parent manuscript quarantine

**Objective:** Remove obsolete tables and interpretations from the manuscript.

**Tasks:**

- [x] Add `tests/test_outdated_science_quarantine.py` asserting the three root
  tables and full provisional-propagation ledger are quarantined, their labels
  and inputs are absent from active TeX, and the fail-closed table remains.
- [x] Run `pytest -q tests/test_outdated_science_quarantine.py` and require the
  new assertions to fail before implementation.
- [x] Move the three obsolete tables and old full results ledger with
  `apply_patch`; add the quarantine index.
- [x] Replace stale Results/Discussion text with the no-attribution boundary.
- [x] Redirect the provisional-table generator and remove stale foreground
  rows from the active results ledger; update `repro_manifest.csv` and the
  results-library catalog.
- [x] Run `pytest -q tests/test_outdated_science_quarantine.py tests/test_provisional_propagation.py tests/test_consistency_audit.py`.
- [x] Run `latexmk -pdf -g -interaction=nonstopmode -halt-on-error main.tex` and
  verify `main.fls` does not contain the quarantined table names.

**Dependencies:** Parent branch `ms/quarantine-outdated-science-20260717` based
on Faber2026 `origin/main` `33ecbb66`.

**Verification:** Manuscript builds; stale labels/inputs are unreachable; current
fail-closed table remains compiled.

### Phase 3: Integrate the pipeline pin and validate

**Objective:** Point the parent at the merged pipeline quarantine without hiding
the intervening pin delta.

**Tasks:**

- [ ] Merge the focused pipeline PR after its checks pass.
- [ ] Update the parent submodule gitlink to the merged pipeline commit.
- [ ] Inspect `git diff --name-status 17d9d266..NEW_PIN` and record all imported
  files in the implementation report.
- [ ] Re-run the parent focused tests, consistency audit, and LaTeX build against
  the new pin.
- [ ] Run `agent-closeout-check` for both repositories with touched-path and
  dirty-state packets.
- [ ] Commit the parent quarantine/pin change and publish through a focused PR.

**Dependencies:** Phases 1 and 2.

**Verification:** The parent points at the merged pipeline quarantine; both
repositories are clean on their feature branches; no primary-checkout dirt moved.

## Success Criteria

### Automated Verification

- [ ] Focused parent and pipeline quarantine tests pass.
- [ ] Existing provisional-propagation, attribution-matrix, joint-summary, and
  consistency-audit tests pass after their path/policy updates.
- [ ] `latexmk` succeeds.
- [ ] `main.fls` contains `twoscreen_provisional_table.tex` but none of the three
  quarantined table inputs.
- [ ] `git status --short` is clean after task-scoped commits in both worktrees.
- [ ] `agent-closeout-check` passes for both repositories.

### Manual Verification

- [ ] Later owner review decides whether each quarantined family is deleted,
  rehabilitated with new science, or retained indefinitely. This decision is
  intentionally outside the migration.

## Testing Strategy

Regression tests enforce file placement, producer destinations, manuscript
reachability, tombstone wording, and the preserved matrix schema. Existing
numerical-unit tests may continue to exercise historical algorithms, but no test
asserts that drifted current inputs reproduce the frozen attribution snapshot.
The LaTeX build is the integration test for manuscript reachability.

## Migration Strategy

The path map in each quarantine README is the rollback record. Restoring a file
requires moving it back, restoring its producer destination, and separately
re-establishing scientific trust; moving bytes alone never restores citable
status.

## Risk Assessment

1. **Broken generator/test paths** — medium likelihood, medium impact. Mitigated
   by redirecting producers and running their focused drift tests.
2. **Accidental submodule side effects** — medium likelihood, high impact.
   Mitigated by a separate pipeline commit/PR and explicit full-range pin audit.
3. **Historical documents gain broken links** — medium likelihood, low impact.
   Mitigated by tombstones for high-traffic summary paths and quarantine indexes.

## Edge Cases and Error Handling

- A producer invoked with an explicit temporary output path may still write
  there for testing; only default committed destinations are forced into
  quarantine.
- Missing external result-library inputs do not block static placement tests.
- The active two-screen readiness table must fail closed if fixed-index refits
  remain unavailable.

## Documentation Updates

- [ ] Add quarantine indexes in both repositories.
- [ ] Add implementation and validation reports under `docs/rse/specs/`.
- [ ] Update current navigation surfaces; leave dated historical specs intact.

## References

- [Research document](research-outdated-science-quarantine-2026-07-17.md)
- `repro_manifest.csv`
- `scripts/results_library_catalog.yaml`
- `pipeline/analysis/RESULTS_LIBRARY.md`

## Review History

### Version 1.0 — 2026-07-17

- Direct-mode plan implementing the owner's reversible-quarantine request.
