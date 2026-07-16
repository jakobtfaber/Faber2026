# Results library index (pointer)

The navigable results inventory lives **outside** the fitting repos:

```text
~/Data/Faber2026/results-library/INDEX.md
~/Data/Faber2026/results-library/_inventory/inventory.yaml
```

Catalog (git, edit to add campaigns):

```text
scripts/results_library_catalog.yaml
```

Refresh (always from this checkout):

```bash
python3 scripts/build_results_library_inventory.py --dry-run
python3 scripts/build_results_library_inventory.py --link --force
```

Plan: [`plan-results-library-2026-07-15.md`](plan-results-library-2026-07-15.md)
