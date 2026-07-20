# Implementation Summary: Latest analysis artifacts

---
**Date:** 2026-07-20
**Author:** AI Assistant
**Status:** Implemented; manual organization review pending
**Plan Reference:** [plan-latest-analysis-artifacts.md](plan-latest-analysis-artifacts.md)
---

## Overview

Created a general archive-on-replacement promoter and published the twelve-burst
JointModel roster at
`~/Data/Faber2026/results-library/scattering/jointmodel/latest`.

Three independently revalidated v2 candidates carry artifacts. The remaining
nine have explicit not-yet-promoted records. No fit was upgraded to PASS.

## Plan Adherence

The plan was followed. One extension was added: catalog external paths support
an environment-derived suffix, so alternate `FABER2026_RESULTS_LIBRARY` roots
work correctly.

## Phases Completed

- Specification and lifecycle tests: complete.
- Promoter, clean-library reproduction, canonical publication, inventory: complete.
- Documentation and automated validation: complete; owner usability review pending.

## Files Modified

Created:
- `analysis/jointmodel-latest.yaml` — twelve-burst specification.
- `scripts/promote_analysis_latest.py` — preflight, hashing, staging,
  idempotence, archive-on-change.
- `tests/test_promote_analysis_latest.py` — five lifecycle/portability tests.
- Research, plan, implementation, and validation records under `docs/rse/specs/`.

Modified:
- `scripts/results_library_catalog.yaml` — JointModel current slot.
- `scripts/build_results_library_inventory.py` — environment-root suffix support.

External data created:
- `~/Data/Faber2026/results-library/scattering/jointmodel/latest/`.
- Updated results-library `INDEX.md` and `_inventory/inventory.yaml`.

No tracked scientific fit source was deleted or rewritten.

## Key Changes

1. Full source validation occurs before library mutation
   (`scripts/promote_analysis_latest.py:57-141`).
2. Changed slots archive before atomic replacement; unchanged slots are no-ops
   (`scripts/promote_analysis_latest.py:184-263`).
3. Recency, fit quality, figure review, adoption remain separate
   (`analysis/jointmodel-latest.yaml:11-112`).

## Verification Results

- `pytest`: 5 passed.
- Fresh library: 12 rows, 3 pairs, 6/6 hashes; second run unchanged 12/12.
- Fresh Python 3.13.9 virtual environment with PyYAML 6.0.3: reproduced.
- Canonical library: 12 unique rows, 3 pairs, 12 status records; idempotent.
- Inventory: 19 entries; JointModel resolves through the configured root.

## Scientific Boundary

Oran C1D1, JohnDoeII C1D2, and Zach C2D3 remain candidate-v2-owner-pending.
Their structural component-count figures were reviewed, but the complete
authoritative fit-quality classifier and four-diagnostic figure gate were not
run here. Their fit-quality status remains
`not-classified-under-authoritative-contract`.

## Remaining Work

- Owner confirms the organization is intuitive.
- Separate science work promotes current fits for the other nine bursts.
- Separate owner decision adopts, rejects, or defers the candidate counts.

## Reproducibility

```bash
python3 scripts/promote_analysis_latest.py \
  --spec analysis/jointmodel-latest.yaml \
  --library "$FABER2026_RESULTS_LIBRARY" \
  --as-of 2026-07-20T14:05:18Z
```

The manifest records source commit, paths, byte counts, and SHA-256 hashes. The
promotion reproduced cleanly. Original fit generation remains non-exactly
rerunnable because the v2 jobs recorded no sampler seeds and used
modified/untracked executed code.

## References

- [Plan](plan-latest-analysis-artifacts.md)
- [Research](research-latest-analysis-artifacts.md)
- [JointTF v2 validation](validation/validation-jointtf-v2-rerun-harvest-2026-07-19.md)
