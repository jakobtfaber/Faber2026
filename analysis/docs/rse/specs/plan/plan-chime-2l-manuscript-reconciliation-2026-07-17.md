# Implementation Plan: CHIME 2L manuscript reconciliation

---
**Date:** 2026-07-17
**Author:** Codex
**Status:** Approved
**Related Documents:**
- [Research: CHIME 2L manuscript reconciliation](../research/research-chime-2l-manuscript-reconciliation-2026-07-17.md)
---

## Overview

Advance the Faber2026 FLITS pin to the merged, gate-closed PR #192 campaign;
replace stale all-diagnostic CHIME prose and its hand-written table with
fail-closed, generated statements; and remove the owner-rejected DSA-only
summary from the compiled manuscript. Prepare, but do not promote, an exact-byte
joint DSA+CHIME candidate under the repository's two-PR figure policy.

**Goal:** The manuscript and evidence ledger agree with the pinned campaign:
one qualified CHIME measurement (`chromatica_hi`), 23 diagnostic-only records,
and no unapproved scintillation-summary figure in the compiled PDF.

## Current State Analysis

- `pipeline` pins `5fb387e`, immediately before PR #192.
- `sections/results.tex:285-334` reports the superseded zero-measurement result.
- `sections/results.tex:243-252` compiles the rejected DSA-only summary.
- `docs/rse/control/evidence-ledger.toml` marks most CHIME products unavailable.

## Desired End State

- `pipeline` pins remote-main merge commit `17d9d266...`.
- A deterministic builder verifies upstream statuses and writes the twelve-row
  campaign table; it exits nonzero if the campaign is not closed or more/less
  than the expected single measurement is present.
- Results prose reports the qualified high-resolution FRB 20240203A subbands
  and explicitly withholds cross-telescope scaling/screen inference.
- The rejected DSA-only figure is absent from compiled TeX and replaced by a
  named owner-review placeholder.
- A separate candidate-only branch carries a reproducible joint-summary
  generator and immutable review packet; no figure is promoted in this plan.

## What We're NOT Doing

- Changing `sections/toa.tex` or Figure 1 assets.
- Re-running upstream fits or changing scientific thresholds.
- Promoting a joint figure without exact-byte manuscript-owner approval.
- Treating diagnostic-only records as measurements or drawing a scaling law
  between different bursts.

## Implementation Approach

The parent change consumes only committed JSON at the pinned FLITS revision.
The table builder requires `validation.status == "closed"`, injection pass,
exactly 24 records, and exactly one record with all three statuses set to pass.
The figure candidate uses the same fail-closed loader plus the already-qualified
DSA validation record. Each CHIME error bar combines fit, window, and
finite-scintle terms in quadrature; the DSA interval remains asymmetric.

## Implementation Phases

### Phase 1: Pin and status contract

**Objective:** Make stale campaign claims fail a focused test before editing.

**Tasks:**
- [x] Add `tests/test_scintillation_campaign_manuscript.py` asserting the
  submodule gitlink is `17d9d266...`, the text names the single CHIME
  measurement, and the old zero-measurement sentences are absent.
- [x] Run `pytest -q tests/test_scintillation_campaign_manuscript.py` and
  observe failure on the old pin/prose.
- [x] Check out `17d9d266...` in `pipeline` and stage only the gitlink.
- [x] Re-run the focused test after Phase 2 and observe pass.

### Phase 2: Generated table and manuscript reconciliation

**Objective:** Derive every campaign outcome from pinned JSON.

**Tasks:**
- [x] Add `scripts/build_scintillation_campaign_summary.py` with explicit
  closed/injection/count/single-measurement assertions and deterministic burst
  ordering.
- [x] Generate `chime_scintillation_campaign_table.tex` using
  `/opt/anaconda3/bin/conda run -n py312 python scripts/build_scintillation_campaign_summary.py`.
- [x] Update `sections/results.tex`, the figure wishlist, the evidence ledger,
  and reproducibility manifest to consume the generated record and preserve
  diagnostic-versus-measurement distinctions.
- [x] Replace the rejected summary inclusion with the repository's standard
  owner-review placeholder.
- [x] Verify with `python scripts/consistency_audit.py`, focused tests, and
  `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex`.

### Phase 3: Candidate-only joint summary

**Objective:** Produce reviewable bytes without manuscript promotion.

**Tasks:**
- [x] Add a loader/plot path to the builder that requires the DSA qualification
  gates and the CHIME measurement/artifact/figure statuses to pass.
- [x] Render only qualified measurements to a temporary candidate root under
  the protected `fig6-scint-summary` target; include no cross-burst scaling
  curve.
- [x] Stage an immutable batch with SHA-256, input paths, pipeline revision,
  status fields, and preview. Keep this phase in a stacked candidate-only PR.
- [x] Add all 24 hash-matched PR #192 CHIME ACF renders as separately labeled
  diagnostic candidates; do not present them as the unavailable joint DSA+CHIME
  appendix replacements.
- [x] Run the focused loader tests and visually inspect the summary, selected
  ACF panels, and full contact sheet.

## Success Criteria

### Automated Verification

- [x] `pytest -q tests/test_scintillation_campaign_manuscript.py` passes.
- [x] `python scripts/consistency_audit.py` passes.
- [x] `python scripts/figure_review.py verify` passes with no unapproved
  protected inclusion.
- [x] `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex` passes.
- [x] `agent-closeout-check` passes; the clean committed worktree and exact
  staged gitlink required no dirty-state packet or runtime restart inventory.

### Manual Verification

- [ ] Manuscript owner reviews the new joint-summary candidate and records an
  exact-byte decision before a later promotion PR.

### Reproducibility & Correctness

- [x] The generator records parent/pipeline revisions, source paths and hashes,
  runtime versions, exact command, and output hashes.
- [x] A fresh clean-Conda invocation reproduces byte-identical JSON/table data;
  PDF metadata differences, if any, are recorded separately from plotted data.

## Testing Strategy

Unit tests exercise fail-closed status parsing and manuscript parity against the
real pinned records. Integration checks rebuild the table, compile the paper,
run the scientific consistency audit, and verify that no protected candidate
was promoted without approval.

## Risk Assessment

1. **Risk:** A later FLITS `main` commit lands while this branch is open.
   **Mitigation:** pin the reviewed science merge `17d9d266...`; only advance
   again if a later commit is explicitly required and revalidated.
2. **Risk:** A joint plot implies a cross-burst frequency law.
   **Mitigation:** separate panels, explicit burst/telescope labels, no
   connecting curve, and a caption that forbids screen inference.

## References

- [Research record](../research/research-chime-2l-manuscript-reconciliation-2026-07-17.md)
- `figure_review/README.md`
- `sections/results.tex`
- dsa110-FLITS merge `17d9d26675702e9f8917da655621bef3231f0ddb`
