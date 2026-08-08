# Implementation Summary: Fail-closed ToA convention

---
**Date:** 2026-07-17
**Plan:** [plan-toa-convention-gate-2026-07-17.md](../plan/plan-toa-convention-gate-2026-07-17.md)
**Status:** Complete
---

## Outcome

The manuscript-facing timing convention now matches the pinned pipeline's
fail-closed contract. All twelve committed crossmatch rows remain
`diagnostic_only:MARGINAL` and unreviewed, so the citable residual is the
observed-peak value in `measured_offset_ms`; candidate model-$t_0$ values remain
available only in `model_corrected_offset_ms`.

## Work completed

- Reframed the model-$t_0$ method in `sections/toa.tex` as a candidate
  diagnostic requiring both `PASS` fit quality and figure review before
  adoption.
- Recomputed the manuscript-facing spread, extrema, and named largest offset
  from the canonical observed-peak values.
- Changed the embedded ToA-decomposition producer to consume
  `measured_offset_ms`, fail if an unvalidated row has diverged from
  `peak_measured_offset_ms`, reject mixed conventions, and use data-derived
  limits that keep every marker inside the frame.
- Regenerated only `figures/toa_offset_decomposition.pdf`; Figure 1 and its
  producer were not touched.
- Updated `repro_manifest.csv` and the association-summary producer's labels
  to state the current observed-peak convention.
- Added a consistency-audit gate plus regression tests for field promotion,
  prose promotion, producer selection, convention mixing, and marker bounds.
- Corrected the corresponding FLITS producer docstring in separate merged PR
  [dsa110-FLITS #198](https://github.com/jakobtfaber/dsa110-FLITS/pull/198)
  (squash `3b40a96d`) without changing the Faber2026 `pipeline/` gitlink.

## Verification performed

- Focused Faber2026 audit/plot tests: 17 passed.
- Full Faber2026 science suite: 132 passed, 1 known xfail.
- Broader ToA/association/Figure-1 regression selection: 33 passed, 1 known
  xfail for the pre-existing class-aware sample-table pin mismatch.
- Pinned FLITS association and notebook reproduction tests: 22 passed.
- FLITS PR tests: 6 passed; Ruff passed.
- `scripts/consistency_audit.py`: clean.
- Forced `latexmk` build: success, 54 pages; existing warnings only.
- Standalone and compiled-page visual review: passed. The post-review
  data-derived x-limit includes the +6.2 ms marker fully inside the frame.
- `git diff --check`: passed; the `pipeline/` gitlink remains `5fb387e`.

## Deviations and adjacent findings

The plan initially named `scripts/make_sample_table.py` and `sample_table.tex`
for a comment-only clarification. They remain unchanged because regenerating
that table currently hits the repository's existing, explicitly xfailed
class-aware-provenance mismatch. Expanding this convention audit into that
separate pin/producer reconciliation would have mixed scopes and changed no
ToA values.

Figure 1's model-anchor producer and `REPRODUCE.md` wording also remain outside
this branch, as required by the parallel Figure-1 lane.

## Scientific stopping point

No model-$t_0$ offset is promoted. A future campaign may change the canonical
field only after each adopted row has `model_fit_quality == "PASS"` and its
diagnostic figure has been reviewed. The current rows satisfy neither gate.
