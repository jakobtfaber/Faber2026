# Foreground analysis

Canonical package for foreground galaxies, galaxy clusters, sightline geometry,
halo models, and their dispersion-measure and scattering contributions.

- `census/`: survey coverage, catalog queries, cross-matching, adjudication,
  frozen source data, and the unified foreground registry.
- `propagation/`: modified-NFW halo columns, scattering, sightline budgets,
  uncertainty propagation, and host-DM inference.
- `visualization/`: figure producers and shared plotting code.
- `results/`: generated manuscript tables and provisional interpretation products.
- `tests/`: package-level scientific and repeatability checks.

Run modules from the analysis repository:

```bash
uv run --group test --frozen python -m pytest foregrounds/tests
uv run --frozen python -m foregrounds.visualization.sightline_halo_grid \
  --halo-csv foregrounds/census/data/sightline_halo_grid.csv \
  --out-dir figure_review/artifacts/staging/fig3_halo_grid/figures
```

No code or data in this package depends on the retired `pipeline/` tree or FLITS.
