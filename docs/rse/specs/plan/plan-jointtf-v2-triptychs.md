# Implementation Plan: JointTF v2 triptychs

---
**Date:** 2026-07-20  
**Author:** AI Assistant  
**Status:** Complete  
**Related Documents:**
- [Research](../research/research-jointtf-v2-triptychs.md)
- [Prior validation](../validation/validation-jointtf-v2-rerun-harvest-2026-07-19.md)
---

## Overview

Generate full candidate triptychs for oran C1D1, johndoeII C1D2, and zach C2D3
from the `s2=100` v2 results. Archive the superseded triptychs under explicit
count labels and preserve the owner-ratification gate.

## Current State Analysis

- `scripts/jointmodel_triptych_manifest.yaml:1-67` selected three stale model dumps.
- `scripts/plot_codetection_triptych.py:236-265` already enforced aligned data/model grids.
- `scripts/plot_codetection_triptych.py:366-407` already produced the required triptych formats.

## Desired End State

- Active triptychs use jobs 171, 175, and 178.
- Historical outputs are count-labeled and separated.
- Every model and figure is hashed; repeated rendering is byte-stable.
- Candidate status remains machine-readable and manuscript compilation remains blocked.

## What We're NOT Doing

- [x] No sampler rerun.
- [x] No component-count adoption or production-table rewrite.
- [x] No manuscript promotion or rung-2 launch.

## Implementation Approach

Use the existing median-model reconstruction on h17. Use the exact zach fine
window hook for job 178. Copy paired NPZ/JSON artifacts, update only the three
roster rows, archive old figure bytes, and make vector metadata deterministic.

## Implementation Phases

### Phase 1: Reconstruct candidate model grids

- [x] Run `dump_jointmodel.py oran _C1D1_s2-100` and
  `dump_jointmodel.py johndoeII _C1D2_s2-100` in h17 `flits-a1-312`.
- [x] Import `run_joint_fit_zachfine.py`, force `common_window=False`, and run
  `dump_jointmodel.py zach _C2D3_s2-100_fine`.
- [x] Assert expected counts, finite model arrays, and identical data/model shapes.

### Phase 2: Replace and archive figure products

- [x] Add a failing roster/archive test in `tests/test_codetection_triptych.py`.
- [x] Update `scripts/jointmodel_triptych_manifest.yaml:1-51` with candidate status,
  counts, `s2`, job IDs, and new paths.
- [x] Move nine older outputs into `figures/codetection_triptych/historical-pre-v2/`.
- [x] Render three replacements with `scripts/plot_codetection_triptych.py:366-407`.

### Phase 3: Reproducibility and verification

- [x] Add a failing timestamp reproducibility test, then implement
  `SOURCE_DATE_EPOCH` metadata and a stable SVG hash salt in
  `scripts/plot_codetection_triptych.py`.
- [x] Render twice and require byte-identical hashes for all nine outputs.
- [x] Run targeted figure, manuscript-suppression, and layout tests.

## Success Criteria

### Automated Verification

- [x] Three model NPZ files match expected counts and contain finite aligned arrays.
- [x] Nine active and nine historical figure files exist.
- [x] Two consecutive renders produce identical SHA-256 hashes for all active files.
- [x] `pytest` target reports 26 passing tests.
- [x] Full root test run reaches only the two known, unrelated pipeline campaign
  failures: pinned revision mismatch and missing 24-record campaign set.

### Manual Verification

- [ ] Owner reviews all three triptychs at full size.
- [ ] Owner ratifies, rejects, or defers each candidate count separately.

## Testing Strategy

Unit tests enforce candidate metadata, historical paths, deterministic metadata,
and the sampled-DM candidate boundary. Integration tests exercise the real NPZ
files through the production renderer. Visual scientific acceptance remains manual.

## References

- [Research](../research/research-jointtf-v2-triptychs.md)
- [Validation](../validation/validation-jointtf-v2-rerun-harvest-2026-07-19.md)
- `scripts/plot_codetection_triptych.py`
- `tests/test_codetection_triptych.py`
