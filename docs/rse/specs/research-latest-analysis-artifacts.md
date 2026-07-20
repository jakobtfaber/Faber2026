# Research: Latest analysis artifacts

**Date:** 2026-07-20
**Scope:** internal codebase
**Codebase state:** `c3e9870b` on 2026-07-20
**Related Documents:** [JointTF v2 validation](validation/validation-jointtf-v2-rerun-harvest-2026-07-19.md)

## Question / Scope

Determine where a maintained "latest" JointModel roster belongs, how superseded
artifacts should be retained, and how to avoid conflating recency with scientific
acceptance. External prior art is out of scope; this is a repository and local
results-library organization decision.

## Codebase Findings

- The catalog declares `~/Data/Faber2026/results-library` as the data inventory
  and distinguishes real materialized bytes from repository links
  (`scripts/results_library_catalog.yaml:1-20`).
- Existing scattering campaigns already occupy dated, trust-labelled library
  slots, but none is an explicit current per-burst roster
  (`scripts/results_library_catalog.yaml:23-55`).
- The materializer deliberately moves result bytes out of git while leaving code
  and navigation in the checkout (`scripts/materialize_results_library.py:1-14`).
- The Figure 1 manifest already identifies all twelve bursts and routes the three
  newest window-clamped candidates to Oran C1D1, JohnDoeII C1D2, and Zach C2D3
  (`scripts/jointmodel_triptych_manifest.yaml:1-67`).
- Those three artifacts are hash-bound deterministic reconstructions, but remain
  candidate fit-audit products rather than adopted production models
  (`figures/jointmodel_pair/fit_artifacts/candidate-jointtf-v2/README.md:1-31`).
- The independent validation supports their candidate component counts while
  keeping owner adoption and exact fit-generation reproducibility open
  (`docs/rse/specs/validation/validation-jointtf-v2-rerun-harvest-2026-07-19.md:1-29`).

## Synthesis

Use a real external results-library slot, `scattering/jointmodel/latest`, as the
current navigational surface. Keep a tracked promotion specification and tool in
git. Normalize artifact names inside per-burst directories, preserve source paths
and SHA-256 hashes in a generated manifest, and write explicit placeholder rows
when no current artifact has been promoted. On replacement, move the displaced
per-burst directory to a dated `historical` snapshot before publishing the new
slot. This is manageable because only promoted summaries/model dumps enter the
surface; raw samples and experiment ladders remain in compute storage.

"Latest" must describe recency only. Scientific fit quality, figure-review state,
and owner adoption remain separate fail-closed fields. The initial roster should
therefore promote only the three independently validated v2 candidates and mark
the other nine as not yet promoted rather than revive older pre-PL-PBF artifacts.

## References / Sources

- Code: `scripts/results_library_catalog.yaml:1-55`
- Code: `scripts/materialize_results_library.py:1-14`
- Code: `scripts/jointmodel_triptych_manifest.yaml:1-67`
- Evidence: `figures/jointmodel_pair/fit_artifacts/candidate-jointtf-v2/README.md:1-31`
- Validation: `docs/rse/specs/validation/validation-jointtf-v2-rerun-harvest-2026-07-19.md:1-29`
