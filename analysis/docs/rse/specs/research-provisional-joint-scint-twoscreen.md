# Research: provisional joint-fit, scintillation, and two-screen products

**Date:** 2026-07-15
**Scope:** internal codebase

## Question / Scope

Identify the newest frozen joint 2D fits and DSA-110 Lorentzian fits that can be
shown as best-so-far manuscript products without representing them as fully
re-trust-certified measurements, and determine the strongest two-screen test
that can be made from those products.

## Codebase Findings

- The DM-locked campaign stores one retained fit for 11/12 bursts and a frozen
  residual adjudication for all 12
  (`pipeline/analysis/scattering-dm-locked-2026-07-14/results/fit_adjudication.csv`).
  Seven rows are `accepted_physical`, three are `morphology_only`, and two are
  rejected; Chromatica has no retained fit JSON.
- Marginal medians and 16th--84th percentile intervals for `tau_1ghz`, `alpha`,
  and `beta` are in the campaign `results/fit_summaries/` JSON files. The JSONs
  do not retain the full posterior samples, so covariance-aware propagation is
  not available.
- The DSA campaign stores all component-level widths, errors, modulation
  indices, sub-band frequencies, and quality flags in
  `pipeline/analysis/scintillation-dsa-lorentzian-2026-07-07/results/dsa_lorentzian_components.csv`.
  Forty-one components pass the internal fit-quality cuts. Only Oran's
  1328.24-MHz component has subsequently passed the frozen injection/null
  qualification battery.
- The existing manuscript figure files already match these frozen catalogs:
  `figures/codetection_triptych/`, `figures/jointmodel_pair/`,
  `figures/dsa_lorentzian_summary.pdf`, and `figures/dsa_scint_acf/`.
- The physically direct screen statistic is
  `P = tau(nu) [ms] * Delta-nu-d [MHz] * 1000`, equivalent to
  `tau[s] * Delta-nu-d[Hz]`. A common screen is expected in the conservative
  interval `0.1 <= P <= 2` (`pipeline/flits/batch/analysis_logic.py:29-31`).

## Synthesis

The manuscript can show all retained joint-fit panels and all DSA ACF panels as
provisional diagnostics, while restricting the two-screen calculation to the
seven residual-adjudicated joint fits and clean narrow (`component=1`) DSA
components. Each DSA component should be paired with `tau` evaluated at its
actual center frequency. This avoids fitting or assuming a DSA-only bandwidth
power law. A burst is provisionally two-screen-favored only when every paired
component remains above `P=2` at one propagated standard deviation; otherwise
it is indeterminate. Because the fit summaries lack joint samples, uncertainty
propagation must be labeled approximate and covariance-free.

## References / Sources

- `sections/results.tex`
- `sections/twoscreen_formalism.tex`
- `pipeline/analysis/scattering-dm-locked-2026-07-14/results/fit_adjudication.csv`
- `pipeline/analysis/scintillation-dsa-lorentzian-2026-07-07/results/dsa_lorentzian_components.csv`
- `pipeline/flits/batch/analysis_logic.py`
