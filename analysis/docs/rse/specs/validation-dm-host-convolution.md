# Validation: deterministic host-DM convolution

**Date:** 2026-07-15  
**Plan:** [plan-dm-host-convolution.md](plan-dm-host-convolution.md)

## Result

Validated. The deterministic engine reproduces an independent 500,000-draw
Monte-Carlo oracle under identical median-centered priors for all nine
sightlines. The regenerated CSV, root budget table, appendix table, results
text, and figure agree. The full manuscript compiles and the rendered host table
and figure were inspected directly.

## Numerical evidence

- 25 focused parent tests passed under the clean `flits` environment; the full
  parent suite passed with 88 tests and one expected failure (`xfail`).
- 14 focused FLITS attribution/budget tests passed.
- All evaluated PDFs normalize to one and reject material negative density.
- Analytic Normal+Normal convolution recovers mean 7 and variance 13.
- The lognormal discretization recovers the analytic mean and places the quoted
  point at its median.
- IGM 32/64/128-node quadrature summaries agree within the predeclared bounds.
- Halving `dx` from 0.1 to 0.05 changes every p16/p50/p84 by less than
  0.25 pc cm^-3 and every negative probability by less than `2e-4`.
- Against the independent 500,000-draw median-centered oracle, the maximum
  absolute quantile difference is 0.313 pc cm^-3 and the maximum absolute
  negative-probability difference is 0.0008.
- Deliberately changing the analytic expected convolution variance from 13 to
  14 produced the intended failing test before restoration.

## Separating the two changes

The deterministic-vs-Monte-Carlo differences above are numerical noise at a
scale far below reported rounding. Separately, correcting the legacy
mean-preserving lognormal factor so that quoted disk, halo, and individual
system values are medians lowers the Monte-Carlo host medians by:

| Sightline | Median shift (pc cm^-3) |
|---|---:|
| FRB 20220207C | -5.67 |
| FRB 20220310F | -4.93 |
| FRB 20220506D | -6.15 |
| FRB 20221113A | -6.38 |
| FRB 20221203A | -6.10 |
| FRB 20230307A | -17.39 |
| FRB 20230913A | -5.79 |
| FRB 20240203A | -7.89 |
| FRB 20240229A | -13.81 |

The larger phineas and casey shifts are expected because their foreground sums
contain four and two independently skewed intervening priors, respectively.
These are scientific prior-definition changes, not evidence that convolution
is less accurate than Monte Carlo.

## Artifact and manuscript checks

- `scripts/dm_budget_uncertainty.py --check-inputs`: nine sightlines validated.
- Host CSV parity test: exact integer summaries and probabilities within the
  three-decimal serialization tolerance.
- `scripts/render_budget_table.py --check`: byte-exact pass.
- `latexmk -pdf -g -interaction=nonstopmode -halt-on-error main.tex`: pass,
  producing a 37-page PDF.
- Rendered page 30: updated nine-row host table is legible and numerically
  consistent with the CSV.
- Rendered page 31: all nine direct host/component PDFs are legible; the
  individual and convolved intervening curves appear only where expected.

Existing manuscript-wide float/box warnings remain outside this scoped change;
there is no new LaTeX error from the rebuilt host section.
