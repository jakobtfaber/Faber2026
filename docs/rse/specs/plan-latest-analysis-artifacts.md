# Implementation Plan: Latest analysis artifacts

---
**Date:** 2026-07-20
**Author:** AI Assistant
**Status:** Implemented; manual organization review pending
**Related Documents:**
- [Research: Latest analysis artifacts](research-latest-analysis-artifacts.md)
---

## Overview

Create a general, manifest-driven promotion tool and use it to seed the current
twelve-burst JointModel roster in the external results library. A per-burst
replacement archives the displaced slot before installing the new artifact.

**Goal:** One unambiguous `scattering/jointmodel/latest` entry point with all
twelve bursts represented and no implied scientific acceptance.

**Motivation:** Campaign-dated directories preserve provenance but make it easy
to open an obsolete fit. A curated latest surface removes that ambiguity.

## Current State Analysis

**Existing Implementation:**
- `scripts/results_library_catalog.yaml:23-55` — dated scattering campaigns.
- `scripts/materialize_results_library.py:60-115` — safe external-byte moves.
- `scripts/jointmodel_triptych_manifest.yaml:7-67` — twelve-burst routing.
- `figures/jointmodel_pair/fit_artifacts/candidate-jointtf-v2/README.md:7-31` — three hash-bound v2 candidates.

**Current Behavior:** No all-burst current slot exists; users must infer recency
across campaigns and branches.

**Current Limitations:**
- Recency, validation, and adoption are easy to conflate.
- Replacing one burst has no automatic archive step.

## Desired End State

`~/Data/Faber2026/results-library/scattering/jointmodel/latest` contains twelve
per-burst records, three current fit/model pairs, a manifest, and a policy README.
Future promotions automatically archive changed per-burst slots under
`historical/<timestamp>/`.

## What We're NOT Doing

- [ ] Adopting candidate counts into production or manuscript tables.
- [ ] Calling any fit PASS without the authoritative diagnostics and review gate.
- [ ] Copying posterior samples, fit ladders, or raw burst data.
- [ ] Reviving pre-PL-PBF artifacts as current entries.

**Rationale:** This change provides navigation and lifecycle management only.

## Implementation Approach

Add a tracked YAML promotion specification and a generic Python promoter. The
promoter validates every source before mutation, hashes copied artifacts,
installs through staging directories, and archives only when content changes.

Key decisions:
1. External library stores bytes; git stores the specification and tool.
2. `latest` means newest promoted, with independent status fields.
3. Missing bursts receive explicit records rather than stale fallback files.
4. Archive paths are immutable timestamped snapshots.

## Implementation Phases

### Phase 1: Specify and test promotion behavior

**Objective:** Define the twelve-burst roster and executable invariants.

**Tasks:**
- [x] Add `analysis/jointmodel-latest.yaml` with all twelve unique bursts and the
  three candidate-v2 source pairs.
- [x] Add `tests/test_promote_analysis_latest.py` asserting initial promotion,
  idempotence, preflight failure, and changed-content archival.
- [x] Run `python3 -m pytest tests/test_promote_analysis_latest.py -q`; expect
  failure before `scripts/promote_analysis_latest.py` exists.

**Dependencies:** Existing candidate JSON/NPZ files at commit `c3e9870b`.

**Verification:** Test collection succeeds and fails only for the missing tool.

### Phase 2: Implement and materialize

**Objective:** Publish the current JointModel roster safely.

**Tasks:**
- [x] Add `scripts/promote_analysis_latest.py` implementing complete preflight,
  SHA-256 records, staging installs, idempotence, and archive-on-change.
- [x] Run `python3 -m pytest tests/test_promote_analysis_latest.py -q`; expect PASS.
- [x] Run the promoter against a temporary clean library and compare all six
  copied artifact hashes with their sources.
- [x] Run the promoter against `~/Data/Faber2026/results-library`.
- [x] Add the new slot to `scripts/results_library_catalog.yaml` and regenerate
  the inventory without replacing real library content.

**Dependencies:** Phase 1.

**Verification:** Twelve records, three complete artifact pairs, nine explicit
not-yet-promoted records, zero source/hash mismatches.

### Phase 3: Document and validate

**Objective:** Record implementation and verification boundaries.

**Tasks:**
- [x] Write `docs/rse/specs/implement-latest-analysis-artifacts.md`.
- [x] Re-run all automated checks and write
  `docs/rse/specs/validation-latest-analysis-artifacts.md`.
- [x] Run `agent-closeout-check` with the exact touched paths and dirty-state packet.
- [x] Commit only task-scoped paths and follow the configured push policy.

**Dependencies:** Phase 2.

**Verification:** Clean task diff, passing checks, current library path readable.

## Success Criteria

### Automated Verification

- [x] `python3 -m pytest tests/test_promote_analysis_latest.py -q` passes.
- [x] `python3 scripts/promote_analysis_latest.py --spec analysis/jointmodel-latest.yaml --library <temp>` succeeds twice without creating history on the second run.
- [x] Generated manifest has twelve unique bursts, three `artifact-present` rows,
  and nine `not-yet-promoted` rows.
- [x] Every copied file SHA-256 matches its tracked source.
- [x] `python3 scripts/build_results_library_inventory.py --root "$(pwd)" --library ~/Data/Faber2026/results-library` succeeds without mutating unrelated slots.

### Manual Verification

- [ ] Owner confirms the directory semantics are intuitive.
- [ ] Owner separately ratifies or rejects the three candidate component counts;
  this is not an implementation-completion criterion.

### Reproducibility & Correctness

- [x] Promotion is reproduced against a fresh temporary library and an isolated
  Python 3.13.9 virtual environment with PyYAML 6.0.3.
- [x] Source commit, paths, hashes, exact command, and status boundaries appear
  in the generated manifest.
- [x] Fit-generation seed/provenance gaps remain explicit.

## Testing Strategy

Unit tests use temporary directories and dummy artifacts. Integration validation
uses the real tracked v2 sources and a fresh temporary library before touching
the canonical library. No fitting job or numerical inference is rerun.

## Migration Strategy

Initial publication creates the new slot without deleting dated campaigns.
Future changed promotions move only the displaced burst directory into history.
Rollback is restoration of the archived burst directory plus its manifest row.

## Risk Assessment

1. **Stale artifact labelled current** — medium impact; prevented by no fallback
   and explicit not-yet-promoted records.
2. **Partial promotion** — high impact; prevented by full preflight and staging.
3. **Status inflation** — high impact; prevented by separate fit, figure-review,
   and adoption fields.

## Edge Cases and Error Handling

- Missing source: abort before any library mutation.
- Duplicate burst: reject the specification.
- Same hashes: no-op; do not create history.
- Changed hashes: archive the complete prior burst slot before replacement.
- Missing current fit: install metadata only; never copy an older fallback.

## Performance Considerations

Only six small fit/model artifacts are copied initially. Hashing cost is negligible.

## Documentation Updates

- [x] Generated library README and manifest.
- [x] Catalog entry documenting trust and location.
- [x] Research, implementation, and validation records.

## References

- [Research: Latest analysis artifacts](research-latest-analysis-artifacts.md)
- `scripts/results_library_catalog.yaml`
- `scripts/materialize_results_library.py`
- `scripts/jointmodel_triptych_manifest.yaml`
- `figures/jointmodel_pair/fit_artifacts/candidate-jointtf-v2/README.md`

## Review History

### Version 1.0 — 2026-07-20
- Direct-mode plan derived from the owner's explicit request.
