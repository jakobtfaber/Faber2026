# Results library (pointer)

Campaign fit/analysis products are inventoried **outside** this git tree:

```text
~/Data/Faber2026/results-library/INDEX.md
~/Data/Faber2026/results-library/_inventory/inventory.yaml
```

Override root with `FABER2026_RESULTS_LIBRARY`. Catalog (edit to add campaigns):

```text
scripts/results_library_catalog.yaml
```

Refresh from the Faber2026 checkout:

```bash
python3 scripts/build_results_library_inventory.py --dry-run
python3 scripts/build_results_library_inventory.py --link --force
```

Path helper: `scripts/results_library.py` (`results_slot(...)`).  
Plan: [`docs/rse/specs/plan-results-library-2026-07-15.md`](../../docs/rse/specs/plan-results-library-2026-07-15.md)
