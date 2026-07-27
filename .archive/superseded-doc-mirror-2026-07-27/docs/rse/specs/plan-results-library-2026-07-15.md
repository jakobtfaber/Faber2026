# Plan: Faber2026 results library

**Status:** Phase B local materialize done in worktree `Faber2026-results-library-b`  
**Library:** `~/Data/Faber2026/results-library/`

## Done (Phase A — non-destructive)

- [x] Taxonomy under `~/Data/Faber2026/results-library/`
- [x] Catalog data in `scripts/results_library_catalog.yaml`
- [x] Builder `scripts/build_results_library_inventory.py` (load → validate → probe → optional link → emit)
- [x] Path helper `scripts/results_library.py` (`DEFAULT_LIBRARY`, `results_slot`, `require_results_library`)
- [x] Repo pointer `docs/rse/specs/results-library-INDEX.md`

## Done (Phase B — this worktree)

- [x] Catalog `mode: materialize` vs `link_only`
- [x] `scripts/materialize_results_library.py` — invert Phase A links; move bytes into library
- [x] Materialized (10 ops): July DM-locked results, June `_a1_fits`/`joint_json`, beta fits+verdicts, DSA lorentzian results, `pipeline/results`, parent `dm-joint-phase-v2/results`, `provisional_propagation`
- [x] Left link_only: Overleaf `figures/`, `figure_review/`, `repro_manifest.csv`, `tau_consistency_catalog.csv`, TeX `exports/`, mixed CHIME trees, `v3_energetics` (code)
- [x] gitignore + `RESULTS_LIBRARY.md` stubs (parent + FLITS)
- [x] `tau_consistency.ALLEXP_FITS_DIR` resolves repo symlink else library slot
- [x] `DATA_LOCATIONS.md` results-library section
- [x] Inventory refresh (`--link --force`)

## Still open (commit / PRs)

- [ ] Parent PR: scripts + docs + gitignore + delete tracked `analysis/dm-joint…/results` + `provisional_propagation` from git index
- [ ] FLITS PR: gitignore + stubs + `tau_consistency` path resolve + delete tracked fit JSON from index (do **not** bump parent gitlink casually)
- [ ] Optional: Drive mirror of library inventory slice
- [ ] Do **not** move Overleaf-bound `figures/` out of Faber2026 git

## Trust

Inventory tags are constrained by `trust_legend` in the catalog YAML. Unknown tags fail the build.

## Refresh

```bash
python3 scripts/materialize_results_library.py --dry-run
python3 scripts/materialize_results_library.py
python3 scripts/build_results_library_inventory.py --link --force
```

Always run from the git checkout (no library-side copy of the builder).
