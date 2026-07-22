# Results live in the results library

Fit / analysis **outputs** for campaigns under `analysis/` are inventoried at:

```text
~/Data/Faber2026/results-library/
```

- Human index: `INDEX.md`
- Machine catalog: `_inventory/inventory.yaml`
- Env: `FABER2026_RESULTS_LIBRARY`

Refresh:

```bash
python3 scripts/build_results_library_inventory.py --link --force
```

Driver scripts in this tree remain **code**. Register new result dumps in the inventory builder.
