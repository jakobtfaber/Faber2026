# Implementation Plan: Fail-closed ToA convention

---
**Date:** 2026-07-17
**Author:** AI Assistant
**Status:** Complete
**Related Documents:**
- [Research: ToA convention and model-correction gate](research-toa-convention-gate-2026-07-17.md)
---

## Overview

Align the manuscript-facing ToA definition with the gate already enforced by
the pinned pipeline: `measured_offset_ms` remains the observed-peak offset
unless a fit is `PASS` and its diagnostic figure has been reviewed. Candidate
model-$t_0$ corrections remain available and described, but are not presented
as adopted measurements while all twelve rows are diagnostic-only.

**Goal:** Every compiled ToA claim and reproducibility record uses the citable
peak convention, and an automated audit prevents accidental promotion of
unvalidated model offsets.

## Current State Analysis

- `pipeline/crossmatching/toa_crossmatch.py:317-332` implements the fail-closed
  gate correctly.
- `sections/toa.tex:51-124` promotes model ToAs despite that gate.
- `scripts/plot_toa_offset_decomposition.py:43-53` reads the diagnostic model
  field for an embedded figure.
- `repro_manifest.csv:39` describes a superseded field switch.
- `scripts/consistency_audit.py:1-394` has no ToA-field/gate check.

## Desired End State

- The compiled manuscript identifies the tabulated residual and embedded
  decomposition as observed-peak quantities.
- Candidate model corrections are explicitly diagnostic and retain their
  numerical method description without being promoted.
- The embedded ToA-decomposition producer consumes `measured_offset_ms` and
  fails if an unvalidated row does not preserve the peak value.
- The reproducibility manifest describes the current pin and field semantics.
- The consistency audit detects both field-contract violations and known
  unconditional model-promotion wording.

## What We're NOT Doing

- [ ] Regenerating or editing Figure 1 (`codetection_data_grid`).
- [ ] Changing scattering-fit results or validation verdicts.
- [ ] Bumping the `pipeline/` gitlink; the scintillation reconciliation lane
      owns the next pin.
- [ ] Changing association thresholds, $P_{\rm cc}$, DM conventions, or the
      delay equations.

## Implementation Approach

Use the existing pipeline gate as the authority. Preserve candidate model
fields as diagnostics, switch only manuscript-facing timing consumers to the
canonical field, and add focused invariants rather than duplicating numerical
logic.

## Implementation Phases

### Phase 1: Add a failing convention audit

**Objective:** Encode the fail-closed contract before changing prose.

**Tasks:**

- [x] Add `check_toa_correction_gate()` to
  `scripts/consistency_audit.py:1-394`. It must load the pinned crossmatch rows,
  require unvalidated rows to satisfy
  `measured_offset_ms == peak_measured_offset_ms`, and flag the exact known
  unconditional model-promotion phrases in `sections/toa.tex` and
  `repro_manifest.csv`.
- [x] Add focused cases to `tests/test_consistency_audit.py:1-110` for the
  committed state and injected gate/prose regressions.
- [x] Run `uv run --project pipeline --frozen pytest -q
  tests/test_consistency_audit.py`; expect the committed-state test to fail
  before the prose/manifest repair.

### Phase 2: Repair manuscript and producers

**Objective:** Make every manuscript-facing timing output use the current
citable convention.

**Tasks:**

- [x] Update `sections/toa.tex:37-152` to describe model-$t_0$ as a candidate
  diagnostic gated on `PASS` plus figure review, and to identify the observed
  peak as the current primary association quantity.
- [x] Update `sections/toa.tex:309-356` and
  `scripts/plot_toa_offset_decomposition.py:1-117` so the embedded
  decomposition uses `measured_offset_ms`, labels it as observed peak, and
  reports peak-derived extrema/order statistics.
- [x] Clarify the observed-peak convention in
  `scripts/plot_association_summary.py:1-122` without changing its values.
  The sample-table producer and generated table are unchanged: their
  class-aware regeneration path is the repository's existing documented
  xfail and is outside this convention-only lane.
- [x] Replace the stale `repro_manifest.csv:39` pin-switch narrative with the
  current fail-closed contract.
- [x] Regenerate only `figures/toa_offset_decomposition.pdf` with
  `uv run --project pipeline --frozen python
  scripts/plot_toa_offset_decomposition.py`; do not run Figure 1 producers.

### Phase 3: Correct dependency documentation separately

**Objective:** Bring the FLITS docstring into parity without changing this
branch's gitlink.

**Tasks:**

- [x] In an isolated dsa110-FLITS worktree from current fork `main`, change only
  the `reproduce_model_result` docstring to state that model adoption is gated
  and that the candidate always remains in `model_corrected_offset_ms`.
- [x] Run the focused FLITS notebook-reproduction tests, commit, push, and open
  a ready-for-review FLITS PR.

## Success Criteria

### Automated Verification

- [x] `uv run --project pipeline --frozen pytest -q
      tests/test_consistency_audit.py tests/test_association_diagnostics.py`
- [x] `uv run --project pipeline --frozen python scripts/consistency_audit.py`
- [x] `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex`
- [x] `git diff --submodule=log --check`
- [x] The `pipeline` gitlink remains `5fb387e` on this branch.
- [x] `agent-closeout-check` passes with the task-scoped packet.

### Manual Verification

- [x] Review the compiled ToA page to confirm that symbols, caption, and figure
      labels consistently say observed peak while the model diagnostic remains
      clearly gated.

## Testing Strategy

The focused audit tests cover the gate invariant, producer field selection,
and prose-promotion regression. The existing association diagnostics confirm
that the numerical timing residuals remain unchanged. The full LaTeX build
checks cross-references and layout.

## Risk Assessment

- **Risk:** A future validated campaign legitimately promotes model offsets but
  the audit still forbids the prose. **Mitigation:** the phrase check is active
  only while at least one committed row is unvalidated.
- **Risk:** Figure 1 concurrently changes. **Mitigation:** do not touch or
  regenerate its producer or assets in this branch.
- **Risk:** A submodule bump enters the commit accidentally. **Mitigation:**
  assert the gitlink SHA before staging and use pathspec-only commits.

## Documentation Updates

- [x] Research, implementation, and validation artifacts under
      `docs/rse/specs/`.
- [x] Faber2026 manuscript methods/caption and `repro_manifest.csv`.
- [x] dsa110-FLITS producer docstring in a separate PR.

## References

- [Research: ToA convention and model-correction gate](research-toa-convention-gate-2026-07-17.md)
- `docs/superpowers/plans/2026-07-07-two-telescope-model-toas.md`
- `pipeline/crossmatching/toa_crossmatch.py`
- `pipeline/crossmatching/toa_crossmatch_results.json`
- `pipeline/crossmatching/association.py`
