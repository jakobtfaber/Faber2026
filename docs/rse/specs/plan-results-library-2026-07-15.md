# Plan: Faber2026 results library

**Status:** Phase A partial (catalog-YAML builder + local library tree)  
**Library:** `~/Data/Faber2026/results-library/`

## Done (Phase A — non-destructive)

- [x] Taxonomy under `~/Data/Faber2026/results-library/`
- [x] Catalog data in `scripts/results_library_catalog.yaml`
- [x] Builder `scripts/build_results_library_inventory.py` (load → validate → probe → optional link → emit)
- [x] Path helper `scripts/results_library.py` (`DEFAULT_LIBRARY`, `results_slot`, `require_results_library`)
- [x] Repo pointer `docs/rse/specs/results-library-INDEX.md`

## Not done yet (claimed earlier; still open)

- [ ] `pipeline/galaxies/foreground/results_library.py` — **do not add**; keep a single helper in parent `scripts/`
- [x] `RESULTS_LIBRARY.md` pointers in parent `analysis/` dirs (`dm-joint-phase-v2`, `provisional_propagation`, `v3_energetics`)
- [x] FLITS docs branch pushed: `cursor/results-library-data-locations-7b14` (`DATA_LOCATIONS.md` section + `analysis/`/`results/` `RESULTS_LIBRARY.md`); open PR via compare link (cloud token cannot create FLITS PRs); **no** Faber2026 pin bump
- [ ] Producers calling `results_slot(...)`

## Next (Phase B — physical separation, needs PRs)

- [ ] Move **gitignored** bulk under `pipeline/results/dm_*` into library; leave README stubs in git
- [ ] Split mixed `analysis/<campaign>/` dirs: keep `.py` in FLITS; relocate tracked `results/`, `fit_summaries/`, `ppc/`, `_a1_fits/` into library with git history migration or content-addressed copy + path updates
- [ ] Point `tau_consistency`, `repro_manifest` producers at `results_slot(...)`
- [ ] Optional: mirror library inventory slice to Drive `scattering_results/` for authority backup
- [ ] Do **not** move Overleaf-bound `figures/` out of Faber2026 git (link-only)

## Trust

Inventory tags are constrained by `trust_legend` in the catalog YAML. Unknown tags fail the build.

## Refresh

```bash
python3 scripts/build_results_library_inventory.py --dry-run
python3 scripts/build_results_library_inventory.py --link --force
```

Always run the script from the git checkout (no library-side copy of the builder).
