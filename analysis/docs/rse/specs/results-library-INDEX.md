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

Dry-run a named catalog entry before any write:

```bash
python3 scripts/build_results_library_inventory.py \
  --only dispersion.dm-joint-phase-v2-parent --dry-run
python3 scripts/materialize_results_library.py \
  --only dispersion.dm-joint-phase-v2-parent --dry-run
```

Apply only after the dry-run matches the frozen action packet. Keep a receipt:

```bash
python3 scripts/build_results_library_inventory.py \
  --only dispersion.dm-joint-phase-v2-parent \
  --link --receipt docs/rse/certificates/results-library-repair-2026-07-20/example-receipt.json
python3 scripts/materialize_results_library.py \
  --only dispersion.dm-joint-phase-v2-parent
```

Regenerate the complete 18-entry inventory without changing links:

```bash
python3 scripts/build_results_library_inventory.py
```

Plan: [`plan-results-library-2026-07-15.md`](plan-results-library-2026-07-15.md)
