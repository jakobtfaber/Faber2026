# Implementation record: deterministic host-DM convolution

**Date:** 2026-07-15  
**Parent baseline:** `e90d4aa27a83ce4adfaa61e162d52e0ab7e9b294`  
**FLITS implementation head:** `90d8f2dadb36c2cbcd6caf2cbe0919797a577ff0`  
**FLITS merged main:** `af78543d4747d339b9f13283b4b8528c91a71cb3` (PR #188)

## Model and numerical method

- Canonical grid: `dx = 0.1 pc cm^-3`.
- Component tail target: `1e-10`.
- Quoted MW-disk, MW-halo, and individual intervening-system point columns
  are lognormal medians.
- The IGM mixture uses 64-node Gauss--Legendre quadrature on each smooth side
  of the asymmetric standard-normal parameterization. Probability clipped to
  `f_IGM = 0.30` and `0.98` is included analytically as endpoint mass.
- Independent component densities are combined with full FFT convolution,
  including the factor of `dx` required for density units. The total foreground
  PDF is reflected about the exact adopted observed DM.
- The published summaries and figure use direct PDFs. Monte Carlo is retained
  only as an independent validation oracle; the cluster beta-model calculation
  remains the separately seeded Monte Carlo used before this change.
- Convolution is performed in observer-frame DM. The reported rest-frame
  p16/p50/p84 values are the exact monotone `(1+z)` rescaling of those
  observer-frame quantiles.
- Six modeled rows outside the deep-imaging footprints retain the manuscript's
  upper-limit designation because their intervening census is incomplete.

## Authoritative inputs

| Input | SHA-256 |
|---|---|
| `analysis/dm-joint-phase-v2/manuscript_dm_catalog.csv` | `86f631aaedefc6a37571360b718589e864d80c05c7864ac1e4c21661367a11c8` |
| `pipeline/galaxies/foreground/budget_table_data.json` | `d5dd5e2a2959be55773f69ef54be4eb494346c6868e316f91e02e7218b10a272` |
| `scripts/dm_budget_intervening_systems.csv` | `8a50fd78c48c61c0ba08ca348710100e7c1840893c68318b186de7e915ec4376` |

The loader requires exactly nine redshift-constrained sightlines, exact adopted
DM matches, no systems on a zero-`DM_int` row, and rounded equality between each
nonzero budget total and the sum of its current individual census columns.

## Canonical runtime and commands

The clean launcher resolved `/Users/jakobfaber/.conda/envs/flits/bin/python`:
Python 3.12.13, NumPy 2.4.6, SciPy 1.17.1, Matplotlib 3.10.8.

```sh
env -i HOME="/Users/jakobfaber" \
  PATH="/opt/anaconda3/bin:/opt/homebrew/bin:/usr/bin:/bin" \
  /opt/anaconda3/bin/conda run -n flits \
  python scripts/dm_budget_uncertainty.py

env -i HOME="/Users/jakobfaber" \
  PATH="/opt/anaconda3/bin:/opt/homebrew/bin:/usr/bin:/bin" \
  /opt/anaconda3/bin/conda run -n flits \
  python scripts/render_budget_table.py
```

The resulting summary CSV and budget table are byte-stable across the base
Python 3.13/SciPy 1.16 check and the canonical clean Conda run:

| Output | SHA-256 |
|---|---|
| `scripts/dm_budget_uncertainty.csv` | `5cee3a81ad94b02b5f22bd2e3ffaff277a403d798f7a50aaf983bee07b8e29ff` |
| `budget_table.tex` | `e4b3d43e6ec58666809903f6bbbef4b89e5f08c04e35386e1cdc8fccafdc2b86` |

The raster figure is environment-renderer dependent and is therefore validated
visually and through numerical PDF tests rather than promised byte-identical
across Matplotlib versions.
