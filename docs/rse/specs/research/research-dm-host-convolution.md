# Research: Deterministic host-DM convolution

**Date:** 2026-07-15
**Scope:** internal codebase
**Related Documents:**
- [Research: DM IGM PDF / Connor 2024](../research/research-dm-igm-pdf-connor2024.md)
- [Research: V4 census-gap extension](../research/research-v4-census-gap-extension.md)

## Question / Scope

Replace the Monte-Carlo construction of the nine host-DM distributions with
the standard deterministic convolution of the additive foreground probability
densities, and regenerate the table and figure from the current V4 census.
The audit covers the source of each component, numerical correctness, generated
artifact parity, and downstream manuscript language.

Codebase state researched: Faber2026 `e90d4aa2` with FLITS `a70b9c54817a94d2739eaa95860333e6e3f03c0a` on 2026-07-15.

## Codebase Findings

### Current host calculation is Monte-Carlo evaluation of a convolution

- `scripts/dm_budget_uncertainty.py:64-65` fixes a NumPy seed and draws
  200,000 samples.
- `scripts/dm_budget_uncertainty.py:215-227` independently samples the MW disk,
  MW halo, TNG-calibrated IGM, and a single sightline-sum intervening prior,
  then subtracts their draw-wise sum from the fixed observed DM.
- `scripts/dm_budget_uncertainty.py:418-435` turns the samples into plotted
  curves with a Gaussian KDE, downsampling to 12,000 samples and imposing a
  minimum 2 pc cm^-3 bandwidth. The KDE adds sampling texture and smoothing
  bias that are not part of the physical model.

For independent additive variables this sampling procedure converges to the
same foreground-sum PDF as repeated convolution, but only at Monte-Carlo
rate. The problem is one-dimensional and every active foreground component
already has an evaluable marginal PDF, so deterministic convolution is the
natural numerical reference.

### Current inputs duplicate authoritative products

- `scripts/dm_budget_uncertainty.py:70-101` hard-codes nine sightlines,
  including exact observed DMs and rounded foreground columns.
- `analysis/dm-joint-phase-v2/manuscript_dm_catalog.csv:1-13` is the
  authoritative exact adopted-DM catalog.
- `pipeline/galaxies/foreground/budget_table_data.json` is the pinned budget
  SSOT for redshift, MW, cosmic comparator, and total intervening columns.
- `scripts/dm_budget_intervening_systems.csv` is the versioned per-system
  decomposition used by the figure. Its grouped point columns reproduce the
  rounded budget totals, including four modeled systems toward FRB 20230307A
  and two toward FRB 20240229A.
- `scripts/render_budget_table.py:27-64` already merges the adopted-DM catalog,
  the pipeline budget SSOT, and the generated host CSV. The posterior producer
  should use the same sources rather than maintain a second roster.

FLITS `origin/main` is exactly the pinned V4 commit; there is no newer remote
census commit. The relevant update is the already-merged three-row V4 extension.
One downstream artifact is stale: the committed attribution matrix reports 16
confirmed phineas registry rows while `build_attribution_matrix()` recomputes
17 after the V4 cluster extension.

### Deterministic construction

Each positive component can be evaluated on a common uniform DM grid. The MW
disk, MW halo, and intervening systems are lognormal. The IGM marginal is a
mixture of lognormals over the asymmetric-normal `f_IGM` prior; deterministic
Gauss-Legendre quadrature over each smooth side of the standard-normal
parameterization, with the clipped endpoint masses included analytically,
preserves the prior without random draws or slow convergence across clip kinks. Repeated
`scipy.signal.fftconvolve(..., mode="full") * dx`, with zero padding supplied by
the full convolution and explicit renormalization, yields the foreground-sum
PDF. Reflecting and shifting that PDF about the exact adopted DM yields the
host distribution.

The grid must be derived rather than tuned to the result. A fixed
`dx = 0.1 pc cm^-3` bounds quantile discretization at approximately 0.05
pc cm^-3, well below integer manuscript rounding. Each lognormal support can
end at its `1 - 1e-10` quantile; the omitted mass is then bounded before
renormalization. A `dx = 0.05` rerun provides a convergence reference.

### Intervening-system correction

The current host calculation applies one lognormal to the already-summed
`DM_int`, while the figure separately displays the individual system priors
(`scripts/dm_budget_uncertainty.py:43-46,240-263`). Under the stated
independence assumption the standard construction is to convolve the
per-system PDFs. This is especially material for phineas: the fractional width
of a sum of independent systems is narrower than assigning the cluster-family
width to the entire 243 pc cm^-3 total. The regenerated posterior is therefore
expected to change for multi-system sightlines even if the census point total
is unchanged.

## Synthesis

The replacement should be deterministic for the host-DM distributions while
retaining a seeded Monte-Carlo calculation only as an independent validation
oracle. The nonlinear beta-model cluster-profile sensitivity is a separate
calculation and can remain seeded Monte Carlo; it is not an additive host-PDF
convolution.

The implementation should load the current budget and adopted-DM products,
validate per-system census totals against the budget, convolve each modeled
intervening system, emit direct normalized PDFs without KDE, and regenerate the
host CSV, budget table, Appendix C table/prose, and PDF/PNG figure together.
The FLITS attribution-matrix artifact should be regenerated with a parity test
in a separate submodule commit, then pinned by the manuscript PR.

## References / Sources

- `scripts/dm_budget_uncertainty.py:43-46,64-65,70-101,215-227,240-263,418-435`
- `analysis/dm-joint-phase-v2/manuscript_dm_catalog.csv`
- `pipeline/galaxies/foreground/budget_table_data.json`
- `scripts/dm_budget_intervening_systems.csv`
- `scripts/render_budget_table.py:27-64`
- `pipeline/galaxies/foreground/attribution_matrix.py:167-205`
- `pipeline/galaxies/foreground/data/sightline_attribution_matrix.csv`
- [Research: DM IGM PDF / Connor 2024](../research/research-dm-igm-pdf-connor2024.md)
