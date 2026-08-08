# Plan: FLITS decoupling — Faber2026-analysis becomes the sole submodule

**Date:** 2026-07-27 · **Status:** Stage 1 landing; Stages 2–5 planned
**Owner decision (relayed 2026-07-27):** after cutover, Faber2026 must not
depend on dsa110-FLITS at runtime, as a submodule, or as an external
package. Faber2026-analysis owns a complete, independently runnable
implementation and tests for every manuscript-required
fitting/scattering/scintillation workflow. FLITS keeps its own
historical/general copies and remains a standalone reusable project.
Faber2026 remains the manuscript repository synchronized with Overleaf,
with `analysis` as its only submodule.

## End-state acceptance test (fresh-clone)

From a fresh clone of `jakobtfaber/Faber2026`:

1. `git submodule status` lists exactly one submodule: `analysis`.
2. No `pipeline/` checkout; `.gitmodules` has no FLITS entry.
3. `git grep` across Faber2026 and Faber2026-analysis shows no FLITS
   import (`from flits`, `import flits`, `scat_analysis`,
   `scint_analysis`) that resolves outside the analysis-owned package,
   no `pipeline/` path reference, and no FLITS package requirement in
   any environment file used by manuscript builds.
4. Manuscript-required figure/table scripts and their tests run from the
   analysis repository alone.

Verification of each item must be independent (re-runnable commands
recorded alongside the receipt), not a completion claim.

## Dependency map (measured 2026-07-27 at origin/main `2e43ee7`)

`git grep -l -E 'flits|scat_analysis|scint_analysis|pipeline/'` over
Faber2026-analysis matches **356 files**. Categories:

- **Python imports of the FLITS engine** — e.g.
  `scripts/plot_codetection_triptych.py` (`flits.batch.codetection_data`,
  `codetection_plots`), `scripts/plot_codetection_gallery.py` /
  `scripts/dm_budget_uncertainty.py` (`flits.plotting.use_flits_style`),
  `figures/jointmodel_pair/fit_artifacts/run_whitney_*.py`
  (`scat_analysis.burstfit*`, `scat_analysis.pipeline.*`),
  `dm-joint-phase-v2/code/tests/test_dmphase_recovery.py`
  (`flits.common.constants`).
- **Path references into the `pipeline/` checkout** — e.g.
  `scripts/kb/config.py` (`MANUSCRIPT_ROOT / "pipeline" / "flits"`),
  `scripts/make_sample_table.py` (`PIPELINE_SOURCE /
  "scattering" / "scat_analysis" / "burst_metadata.py"`).
- **Runtime environment** — `conda run -n flits` invocations in script
  docstrings and Make targets.
- **Declarative metadata** — `figures/catalog.yaml` tool tags,
  `scripts/results_library_catalog.yaml`, absolute scratch-run paths in
  `figures/jointmodel_pair/fit_artifacts/*.yaml`.
- **Docs/receipts** — historical references; do not rewrite, they are
  records.

Parent repository (Faber2026): `.gitmodules` `pipeline` entry; knowledge
base indexes `pipeline/`. The `pipeline` submodule pin is currently
`99e60c3a4e88d43b4a80b8954ce4f06404e682ab`.

## Stages

**Stage 1 (this change).** Relocate the campaign-specific diagnostic
workflow `analysis/scattering-refit-2026-06/` (Zach fine-structure,
two-screen, PL-PBF suites) from FLITS into `scattering-refit-2026-06/`
here, provenance-preserved (`MIGRATION_PROVENANCE.md`). Additive only.

**Stage 2 — vendor the engine.** Copy the manuscript-required FLITS
engine (the `flits` package, `scattering/scat_analysis`, the
scintillation analysis package, required `configs/` and `tests/`) into
an analysis-owned internal package at the exact FLITS pin, with a
per-directory provenance table (source SHA per tree). Decide disposition
of the unapplied engine diffs in
`scattering-refit-2026-06/flits-library-diffs/`. The import/package
surface (final module names) is an explicit migration item — current
FLITS module names are not assumed final.

Open Stage-2 item (queued 2026-07-27, job work-5e4de3fc06cb): propagate
the DSA `.fil` time-axis warning (header `tstart` and T2 MJDs are
millisecond-wrong despite 11-digit rendering; microsecond truth lives in
`trigger_mjd_microsecond_recovery.json` beside the data) into every
migrated pipeline/analysis config and README that states or consumes a
burst start time.

**Stage 3 — rewrite the import surface.** Point the ~356 referencing
files at the analysis-owned package; replace `pipeline/` path lookups
and the `flits` conda env with analysis-owned equivalents; leave
historical docs/receipts untouched.

**Stage 4 — acceptance.** Run the fresh-clone acceptance test above;
record commands and outputs as a receipt.

**Stage 5 — cutover (owner-gated).** Remove the `pipeline` submodule
from Faber2026. This is a deliberate, separately scoped submodule
change: never a side effect, performed only after Stage 4 passes and
with explicit owner approval. FLITS sources, branches, and archive
snapshots are not deleted by any stage of this plan.

## Safe deletion / cutover gate

Before any FLITS-side retirement or submodule removal, all must hold:

1. Stage 4 acceptance receipt exists and its commands re-run clean.
2. The three h17 archive snapshot branches remain intact on
   `origin` (`archive/h17-*-snapshot-20260727`).
3. Independent content verification of every migrated tree against its
   source SHA (bit-exact diff against `git archive` of the source
   commit).
4. Explicit owner approval naming the exact refs/paths being retired.
