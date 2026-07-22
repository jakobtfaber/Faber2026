# Plan: Faber2026 results library

**Status:** Phase A landed (inventory + symlinks + path helpers)  
**Library:** `~/Data/Faber2026/results-library/`

## Done (Phase A — non-destructive)

- [x] Taxonomy under `~/Data/Faber2026/results-library/`
- [x] `INDEX.md` + `_inventory/inventory.yaml` covering parent + pipeline campaigns
- [x] Symlinks into existing result trees (code checkouts unchanged)
- [x] `scripts/build_results_library_inventory.py --link`
- [x] `scripts/results_library.py` + `pipeline/galaxies/foreground/results_library.py`
- [x] `RESULTS_LIBRARY.md` pointers in major `analysis/` / `results/` dirs
- [x] `DATA_LOCATIONS.md` section

## Next (Phase B — physical separation, needs PRs)

- [ ] Move **gitignored** bulk under `pipeline/results/dm_*` into library; leave README stubs in git
- [ ] Split mixed `analysis/<campaign>/` dirs: keep `.py` in FLITS; relocate tracked `results/`, `fit_summaries/`, `ppc/`, `_a1_fits/` into library with git history migration or content-addressed copy + path updates
- [ ] Point `tau_consistency`, `repro_manifest` producers at `results_slot(...)` 
- [ ] Optional: mirror library inventory slice to Drive `scattering_results/` for authority backup
- [ ] Do **not** move Overleaf-bound `figures/` out of Faber2026 git (link-only)

## Trust

Inventory tags follow trust-reset + provisional gates. Revoked campaigns stay under `archive/` or tagged `revoked-2026-07-06`.
