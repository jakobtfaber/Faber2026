# Implementation: post-PL-PBF joint-fit figure reconciliation

**Date:** 2026-07-17
**Status:** implemented; replacement campaign remains blocked

- `sections/observations.tex` no longer inputs the historical Whitney triptych.
- `sections/results.tex` removes the stale figure reference and records the
  full-roster production-refit, dump, and review blocker.
- `sections/appendix.tex` no longer inputs `jointmodel_pairs.tex`; it records
  that the six grids contain eleven actual retained panels because Chromatica
  had no retained joint fit.
- Historical TeX producers and figure bytes remain untouched.
- The two `repro_manifest.csv` families are now `embedded_in_manuscript=no`
  with `superseded_pre_pl_pbf` status and the reviewed pin in their notes.
- The owner checklist records suppression separately from future replacement.

No candidate packet was staged because no complete replacement artifact set
passed the provenance gate.
