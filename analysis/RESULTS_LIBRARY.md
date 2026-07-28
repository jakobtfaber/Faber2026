# Results library pointers (parent analysis/)

| Path | Library slot | Mode |
|------|--------------|------|
| `dispersion/results/joint-phase/results` | `dispersion/dispersion/results/joint-phase` | materialized |
| `foregrounds/results/provisional-propagation` | `foreground/provisional-propagation` | materialized |
| `energetics/studies/legacy-v3` | `foreground/v3-energetics` | link_only (code stays here) |

```bash
python3 scripts/materialize_results_library.py
```

Catalog: `scripts/results_library_catalog.yaml`.
