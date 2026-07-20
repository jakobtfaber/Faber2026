# Implementation Plan: V4 census-gap extension

---
**Date:** 2026-07-15
**Author:** Codex
**Status:** Implemented; manual verification pending
**Related Documents:**
- [Research: V4 census-gap extension](../research/research-v4-census-gap-extension.md)
---

## Overview

Add an append-only, provenance-bearing V4 extension to the frozen foreground
census, regenerate the foreground table, and revise the manuscript so the
discovery-to-validation gap is explicit. The existing budget gate remains the
only authority for Table 4.

**Goal:** represent all three omitted discovery systems without assigning an
unsupported DM column.

**Motivation:** the current registry and table incorrectly imply that the
discovery stage found no surviving candidate on one sightline and omit a
second galaxy candidate plus a second cluster-scale crossing.

## Current State Analysis

- `pipeline/galaxies/foreground/census_registry.py:85-163` builds only the
  frozen 49-row registry.
- `pipeline/galaxies/foreground/census_registry.py:76-82` already has the
  correct budget gate for these verdicts.
- `pipeline/galaxies/foreground/foreground_table_data.json` is the table SSOT.
- `sections/observations.tex:298-335` states the pre-extension counts.
- `sections/appendix.tex:33-68` documents the adopted cluster model.

## Desired End State

- The committed registry contains 52 rows: 30 confirmed, 15 inconclusive,
  7 refuted.
- The three extension rows are uniquely keyed and all are budget-ineligible.
- `foreground_table.tex` contains the three systems and only two explicit
  no-candidate sightlines.
- The manuscript distinguishes discovery completeness from budget
  eligibility and documents the unmodeled WHL12 cluster.
- `budget_table_data.json` and the generated budget table do not change.

## What We're NOT Doing

- [ ] Derive `M500` from WHL12 richness.
- [ ] Treat the WHL12 BCG as an isolated galaxy halo.
- [ ] Promote either weak galaxy photo-z to a confirmed foreground redshift.
- [ ] Change any Table 4 intervening-DM value.
- [ ] Regenerate the sightline-halo figure in this change.

**Rationale:** each excluded item requires a separate modeling or figure
provenance decision.

## Implementation Approach

Use a committed `v4_extension.csv` with the exact registry schema. A helper
loads and validates it, derives boolean gates from verdict/type/geometry, and
appends it only when rebuilding from the frozen source triplet. The checked-in
registry remains the fallback artifact. Tests fix the extension keys, counts,
and zero budget effect before implementation.

## Implementation Phases

### Phase 1: Registry extension

**Objective:** make the three adjudicated rows part of every rebuilt registry.

**Tasks:**
- [x] Add failing assertions in
  `pipeline/galaxies/foreground/test_census_registry.py:14-35` for 52 rows,
  verdict counts, the three keys, and zero eligible extension rows.
- [x] Run
  `uv run pytest galaxies/foreground/test_census_registry.py -q`; expect the
  new assertions to fail against the 49-row registry.
- [x] Add `pipeline/galaxies/foreground/data/census_extensions/v4_extension.csv`
  with the three adjudicated rows.
- [x] Add `load_census_extensions()` and append/validation logic in
  `pipeline/galaxies/foreground/census_registry.py:85-163`; reject duplicate
  keys and derive `registry_tier`/`budget_eligible` rather than trusting CSV
  booleans.
- [x] Regenerate `data/intervening_census_registry.csv` from the checked-in
  frozen inputs and rerun the focused test; expect pass.
- [x] Commit the focused FLITS change.

**Verification:**
- [x] `uv run pytest galaxies/foreground/test_census_registry.py -q`
- [x] `uv run pytest galaxies/foreground/test_sightline_budget.py -q`

### Phase 2: Generated foreground table

**Objective:** expose the extension while keeping the emitter tied to registry
verdicts.

**Tasks:**
- [x] Update failing row/count/empty-sightline assertions in
  `pipeline/galaxies/foreground/test_foreground_table_emitter.py:40-90`.
- [x] Run the focused test; expect failure.
- [x] Add the three table rows to `foreground_table_data.json`, replace the
  FRB 20221113A no-candidate row, and revise emitter caption/comments.
- [x] Run `uv run python -m galaxies.foreground.foreground_table_emitter`.
- [x] Rerun the focused emitter tests; expect pass.
- [x] Commit the table change.

**Verification:**
- [x] `uv run pytest galaxies/foreground/test_foreground_table_emitter.py -q`
- [x] `uv run python -m galaxies.foreground.foreground_table_emitter --check`

### Phase 3: Manuscript synchronization

**Objective:** update prose, Appendix B, generated table, and submodule pin.

**Tasks:**
- [x] Copy the generated FLITS export to `foreground_table.tex`.
- [x] Update `sections/observations.tex:298-335` with 38 total catalog rows,
  31 physical systems, 11 confirmed, 15 inconclusive, 5 refuted, and the
  discovery-handoff limitation.
- [x] Update `sections/appendix.tex:33-68` to disclose the WHL12 cluster and
  explain why no column is assigned.
- [x] Update the `pipeline` gitlink to the reviewed FLITS commit.
- [x] Compile with `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex`.
- [x] Commit the focused manuscript change.

**Verification:**
- [x] `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex`
- [x] `rg -n "WHL J115048|WISEA J044538|WISEA J211150" foreground_table.tex sections`

## Success Criteria

### Automated Verification

- [x] All focused census and emitter tests pass.
- [x] Registry has 52 unique keys and no extension row is budget-eligible.
- [x] Budget table input and export are unchanged.
- [x] Manuscript compiles without a LaTeX error.

### Manual Verification

- [ ] Owner confirms the table wording does not imply that the two weak
  photo-z values are validated redshifts.
- [ ] Owner confirms the WHL12 system should remain disclosed but unmodeled.

### Reproducibility & Correctness

- [x] Extension coordinates, discovery geometry, verdict reason, and provenance
  tag are committed in the CSV.
- [x] Exact regeneration/test commands are recorded in the implementation log.

## Testing Strategy

Focused tests cover row counts, stable keys, verdicts, budget gates, generated
table parity, and table-to-registry parity. The existing sightline-budget tests
serve as the integration check that no candidate leaks into Table 4. The final
PDF compile checks manuscript integration.

## Migration Strategy

Append the extension after the frozen registry and retain the frozen files
unchanged. Rollback is a normal revert of the extension commit and manuscript
pin commit.

## Risk Assessment

1. **Weak discovery redshift is mistaken for validation.** Mitigation: blank
   adopted `best_z` for the two inconclusive galaxies and keep the discovery
   value only in the reason/provenance text.
2. **Cluster leaks into the budget.** Mitigation: require finite `b/R500` for a
   confirmed cluster and assert all extension rows are ineligible.
3. **Counts drift between code and prose.** Mitigation: hard assertions plus
   generated table parity and a compiled manuscript check.

## References

- [Research: V4 census-gap extension](../research/research-v4-census-gap-extension.md)
- `pipeline/galaxies/foreground/census_registry.py`
- `pipeline/galaxies/foreground/foreground_table_emitter.py`
- `sections/observations.tex`
- `sections/appendix.tex`
