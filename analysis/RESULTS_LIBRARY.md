# Results library pointers (parent analysis/)

| Path | Library slot | Mode |
|------|--------------|------|
| `dm-joint-phase-v2/results` | `dispersion/dm-joint-phase-v2` | materialized |
| `provisional_propagation` | `foreground/provisional-propagation` | materialized |
| `v3_energetics` | `foreground/v3-energetics` | link_only (code stays here) |

```bash
python3 scripts/materialize_results_library.py
```

Catalog: `scripts/results_library_catalog.yaml`.
