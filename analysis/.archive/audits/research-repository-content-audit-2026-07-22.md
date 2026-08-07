# Research: repository content audit

**Date:** 2026-07-22
**Scope:** Parent repository plus recorded `analysis` pin and checked-out `pipeline` commit.
**State:** parent `cca8f8e7`; analysis `11b716c`; pipeline `7d26b1f`.

## Question / Scope

Find redundant databases/files, superseded analysis code, and contradictory or
obsolete documentation. Preserve provenance; do not confuse repeated evidence
snapshots with accidental duplicates.

## Codebase Findings

- The knowledge-base authority is `analysis/.kb/kb.sqlite3`
  (`scripts/kb/config.py:15-16`). The parent `.kb/kb.sqlite3` is the populated
  pre-split database (2,721 documents; 13,426 chunks); the current analysis DB
  is empty. One populated DB should remain at the configured path.
- Both repositories deliberately retain obsolete science under
  `quarantine/2026-07-17-outdated-science`, while the results catalog already
  names its consumer slot `archive` (`scripts/results_library_catalog.yaml:167-176`).
  The path contradicts the requested dedicated `.archive/` convention.
- The Casey calibration deck contains three files whose names explicitly say
  `SUPERSEDED-signbug`; only `casey_dm_strip_CORRECTED.png` is truthful. The
  handoff confirms this (`docs/rse/specs/handoff/handoff-2026-07-19-14-56-scint-input-remediation-casey-dm-calibration.md:37-51`).
- `pipeline/configs/{sampler,telescopes}.yaml` are Git symlinks, not redundant
  copies (`pipeline/configs/README.md:43-62`). Keep them.
- `pipeline/scintillation/scint_analysis/reference_arc/` is regression and
  provenance evidence used by active tests and plans. Keep it.
- No tracked SQLite, DuckDB, or similar database exists in the three Git trees.
  `.grit/registry.db` is a separate tool registry, not a duplicate.
- Exact duplicate figures and result JSON under `analysis/figure_review/` are
  immutable review snapshots. Their placement and provenance differ; keep them.
- Two completed implementation records have no inbound references:
  `implement-toa-convention-gate-2026-07-17.md` and
  `implement-unified-12burst-figure.md`. Git history and current tests/code
  provide the live search surface; archive the records.

## Synthesis

Archive only high-confidence superseded material. Preserve scientific evidence
snapshots and compatibility symlinks. Move obsolete science bytes, explicit
sign-bug figures, and unreferenced completed workflow records. Consolidate the
knowledge database at the configured analysis path and refresh the index.

## References / Sources

- `scripts/kb/config.py:15-16`
- `scripts/results_library_catalog.yaml:167-176`
- `pipeline/configs/README.md:43-62`
- `docs/rse/specs/handoff/handoff-2026-07-19-14-56-scint-input-remediation-casey-dm-calibration.md:37-51`
