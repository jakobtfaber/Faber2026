# Implementation Plan: Deterministic host-DM convolution

---
**Date:** 2026-07-15
**Author:** Codex
**Status:** Implemented and validated (2026-07-15)
**Related Documents:**
- [Research: Deterministic host-DM convolution](../research/research-dm-host-convolution.md)
- [Research: DM IGM PDF / Connor 2024](../research/research-dm-igm-pdf-connor2024.md)
---

## Overview

Replace sample-and-KDE host-DM posteriors with deterministic convolution of the
current foreground PDFs. Load the current adopted-DM and V4 budget/census
products, convolve individual intervening systems, regenerate all downstream
artifacts, and retain a seeded Monte-Carlo calculation only as an independent
numerical cross-check.

**Completion note:** all implementation and automated verification phases below
were completed. FLITS landed in PR #188. The only intentionally open manual
criterion is collaborator/owner aesthetic review of the direct-PDF figure; it
does not block the numerical validation recorded in
`validation-dm-host-convolution.md`. Integration with the subsequently advanced
parent `main` preserves its observer/rest-frame distinction, provisional
redshift notes, and six incomplete-census upper-limit flags.

**Goal:** deterministic, normalized, converged host-DM PDFs whose source inputs
and manuscript artifacts are mechanically tied to the current census.

**Motivation:** the existing Monte-Carlo calculation is adequate but adds
sampling/KDE error to a one-dimensional additive problem, duplicates sightline
inputs, and smears the summed intervening column rather than convolving the
individual system PDFs.

## Current State Analysis

- `scripts/dm_budget_uncertainty.py:215-227` constructs host draws from four
  independently sampled foreground terms.
- `scripts/dm_budget_uncertainty.py:418-435` KDE-smooths a 12,000-sample subset.
- `scripts/dm_budget_uncertainty.py:70-101` duplicates current budget inputs.
- `tests/test_dm_budget_uncertainty.py:1-130` verifies the TNG interpolation but
  not host-PDF normalization, convolution correctness, or grid convergence.
- `pipeline/galaxies/foreground/data/sightline_attribution_matrix.csv:7` is one
  confirmed phineas registry row behind the V4 builder output.

## Desired End State

- Host PDFs are evaluated by deterministic convolution on a documented grid.
- The IGM mixture is marginalized by deterministic quadrature.
- Per-system intervening PDFs are convolved and their point sums are checked
  against the current budget SSOT.
- Direct PDFs, not KDEs, feed the figure.
- CSV/table/figure/prose agree with the regenerated values.
- FLITS attribution-matrix generated-artifact parity is enforced.
- Independent Monte Carlo agrees within a statistically justified tolerance.

## What We're NOT Doing

- [ ] Change the TNG/Walker/Connor IGM calibration or `f_IGM` prior.
- [ ] Impose `DM_host >= 0` or introduce a host-galaxy likelihood/prior.
- [ ] Model the unadjudicated WHL12 cluster as a second phineas column.
- [ ] Resolve shared astrophysical correlations among foreground systems.
- [ ] Replace the nonlinear beta-model cluster-profile Monte Carlo.
- [ ] Silently preserve the legacy mean-preserving lognormal parameterization
  where it conflicts with the adopted median-centered prior definition.

**Rationale:** these are scientific-model decisions separate from the numerical
replacement of the currently stated independent additive model.

## Implementation Approach

Use a `DiscretePDF` value object carrying `x0`, `dx`, and normalized density.
Evaluate lognormal PDFs through SciPy, marginalize the clipped asymmetric
`f_IGM` prior with 64-node split Gauss-Legendre quadrature (including the two
clipped endpoint masses analytically), and convolve with
`scipy.signal.fftconvolve(..., mode="full") * dx`. Component support ends at
the `1 - 1e-10` quantile and the canonical grid uses `dx=0.1 pc cm^-3`.
Reflect the foreground-sum density about exact `DM_obs`; obtain quantiles and
negative probability from the normalized numerical CDF.

Treat the quoted MW-disk estimate, the 40 pc cm^-3 MW-halo estimate, and every
individual intervening-system column as the **median** of its lognormal prior.
This matches the manuscript's stated halo convention and is the adopted
scientific interpretation for the rebuilt products. Validation must report two
effects separately: replacing finite Monte Carlo sampling/KDE with deterministic
convolution while holding priors fixed, and correcting the legacy
mean-preserving parameterization to these median-centered priors.

Correctness criteria are analytic Gaussian convolution, probability
conservation/non-negativity, lognormal moments, IGM quadrature convergence,
`dx=0.1` versus `dx=0.05` host-summary convergence, and agreement with an
independent 500,000-draw Monte-Carlo oracle at tolerances derived from sampling
and grid resolution.

## Implementation Phases

### Phase 1: FLITS generated-artifact parity

**Objective:** close the known V4 attribution-matrix drift before consuming the
current census downstream.

**Tasks:**
- [x] Add a failing test in
  `pipeline/galaxies/foreground/test_attribution_matrix.py` that loads the
  committed CSV and asserts frame equality with `build_attribution_matrix()`
  after stable column/row ordering.
- [x] Run `cd pipeline && uv run pytest galaxies/foreground/test_attribution_matrix.py -q`;
  expect failure at phineas `n_confirmed` 16 versus 17.
- [x] Add a module entry point to
  `pipeline/galaxies/foreground/attribution_matrix.py:202-205`, then run
  `cd pipeline && uv run python -m galaxies.foreground.attribution_matrix`
  to regenerate the committed matrix. The pre-change module defines the writer
  but has no CLI entry point, so this task makes the recorded command real.
- [x] Rerun the focused test; expect pass.
- [x] Commit and publish the focused FLITS change, then update the parent
  gitlink only after the FLITS PR is merged.

**Verification:**
- [x] `cd pipeline && uv run pytest galaxies/foreground/test_attribution_matrix.py -q`

### Phase 2: Deterministic PDF engine and correctness anchors

**Objective:** implement independently verifiable normalized convolution.

**Tasks:**
- [x] Add failing tests to `tests/test_dm_budget_uncertainty.py` for:
  normalized/nonnegative densities; an analytic Normal+Normal mean and variance;
  lognormal mean recovery; IGM 32/64/128-node quadrature convergence; and exact
  reflection/shift of a toy foreground PDF.
- [x] Test explicitly that quoted disk, halo, and intervening point values are
  the medians of their lognormal priors.
- [x] Run `pytest tests/test_dm_budget_uncertainty.py -q`; expect import failures
  for the new API.
- [x] Add `DiscretePDF`, `normal_pdf`, `lognormal_pdf`, `igm_mixture_pdf`,
  `convolve_pdfs`, `host_pdf_from_foreground`, `pdf_quantile`, and `pdf_cdf_at`
  to `scripts/dm_budget_uncertainty.py` using `dx=0.1`, tail mass `1e-10`, and
  64-node split Gauss-Legendre quadrature.
- [x] Rerun the focused tests and deliberately perturb one analytic expected
  variance to observe a red test before restoring it.

**Verification:**
- [x] `pytest tests/test_dm_budget_uncertainty.py -q`

### Phase 3: Current-input loader and per-system convolution

**Objective:** remove the duplicated sightline roster and rebuild from current
authoritative products.

**Tasks:**
- [x] Add failing tests that `load_sightlines()` matches all nine
  redshift-constrained budget rows to exact `adopted_dm` values and rejects
  roster mismatch; add a test that grouped per-system point columns round to
  each nonzero budget `dm_int`.
- [x] Implement loaders for
  `analysis/dm-joint-phase-v2/manuscript_dm_catalog.csv`,
  `pipeline/galaxies/foreground/budget_table_data.json`, and
  `scripts/dm_budget_intervening_systems.csv`.
- [x] Replace `host_posterior()` with `host_distribution()` that convolves disk,
  halo, IGM, and every individual intervening system.
- [x] Add `dx=0.1` versus `dx=0.05` convergence assertions of <0.25 pc cm^-3
  for p16/p50/p84 and <2e-4 for `P(host<0)`; loosen only if an a-priori grid
  bound, not observed output, justifies a different tolerance.
- [x] Add a fixed-seed 500,000-draw independent oracle test with probability
  tolerance `5 * sqrt(0.25/N) + 2e-4` and quantile tolerance derived from the
  empirical order-statistic interval plus 0.1 pc cm^-3 grid resolution.
- [x] Run a second comparator using the legacy mean-preserving prior centering
  so the numerical-method delta and prior-centering delta are reported
  separately.

**Verification:**
- [x] `pytest tests/test_dm_budget_uncertainty.py -q`
- [x] `python scripts/dm_budget_uncertainty.py --check-inputs`

### Phase 4: Regenerate and synchronize manuscript artifacts

**Objective:** make every rendered number and description follow the new PDFs.

**Tasks:**
- [x] Run `conda run -n flits python scripts/dm_budget_uncertainty.py` to write
  `scripts/dm_budget_uncertainty.csv` and `figures/dm_host_posteriors.{pdf,png}`.
- [x] Run `conda run -n flits python scripts/render_budget_table.py`.
- [x] Update `sections/appendix.tex:90-190` to describe deterministic
  convolution/quadrature, direct PDF plotting, individual-system convolution,
  and the regenerated numerical summaries.
- [x] Update `repro_manifest.csv` with the deterministic method and exact
  producer command.
- [x] Add generated-artifact parity tests for the CSV summaries and ensure the
  root table renderer remains byte-exact.
- [x] Inspect the PNG visually and compile the manuscript with
  `latexmk -pdf -g -interaction=nonstopmode -halt-on-error main.tex`.

**Verification:**
- [x] `pytest tests/test_dm_budget_uncertainty.py tests/test_render_budget_table.py -q`
- [x] `python scripts/render_budget_table.py --check`
- [x] `latexmk -pdf -g -interaction=nonstopmode -halt-on-error main.tex`

### Phase 5: Reproducibility and publication

**Objective:** independently reproduce, record provenance, and publish scoped PRs.

**Tasks:**
- [x] Record runtime, lock/environment, code commits, input SHA-256 hashes,
  grid parameters, quadrature order, cluster RNG seed, and exact commands in
  `docs/rse/specs/implement/implement-dm-host-convolution.md`.
- [x] Reproduce from fresh FLITS and parent worktrees and compare CSV/table bytes
  plus numerical summaries.
- [x] Write `docs/rse/specs/validation/validation-dm-host-convolution.md` against this plan.
- [x] Run `agent-closeout-check` for both repositories, commit only scoped paths,
  push under the standing policy, and open focused PRs.

**Verification:**
- [x] Clean-worktree reproduction matches committed CSV and table byte-for-byte.
- [x] `agent-closeout-check --repo <FLITS-worktree>` and
  `agent-closeout-check --repo <Faber2026-worktree>` pass.

## Success Criteria

### Automated Verification

- [x] All analytic/invariant/convergence/cross-method tests pass.
- [x] Every PDF is nonnegative and integrates to 1 within `1e-10` after normalization.
- [x] Fine-grid summaries meet the predeclared convergence tolerances.
- [x] Current input rosters and intervening totals pass parity checks.
- [x] Generated CSV, budget table, and figure regenerate successfully.
- [x] Manuscript compiles without a LaTeX error.

### Manual Verification

- [ ] Owner confirms the direct-PDF figure is visually interpretable and that
  removal of KDE bumps matches the intended presentation.
- [ ] Owner reviews scientifically material changes in phineas/casey host
  intervals caused by individual-system convolution.

### Reproducibility & Correctness

- [x] Exact environment, code, input hashes, and commands are recorded.
- [x] Analytic and independent Monte-Carlo references validate the convolution.
- [x] Validation separates deterministic-vs-Monte-Carlo agreement under
  identical median-centered priors from the scientific shift caused by
  correcting the legacy prior centering.
- [x] A clean worktree reproduces the committed artifacts.

## Testing Strategy

Unit tests cover analytic PDFs, normalization, convolution, quadrature,
reflection, input parity, and per-system aggregation. Integration tests cover
all nine sightlines, the root budget-table overlay, and artifact regeneration.
The independent Monte-Carlo oracle is validation-only and never feeds the
published values.

## Migration Strategy

The existing script path and output filenames remain stable. Downstream callers
continue to consume the same CSV columns. Rollback is a normal revert of the
two focused PRs.

## Risk Assessment

1. **Grid truncation or FFT normalization error.** High impact, low likelihood;
   controlled by analytic moments, tail bounds, normalization, and fine-grid
   convergence.
2. **Scientific interval changes from per-system convolution.** Medium impact;
   report exact deltas and require owner review rather than hiding them.
3. **Census/input drift.** High impact; eliminate the hard-coded roster and
   enforce roster plus rounded-total parity.
4. **Parent/submodule race.** Medium likelihood; land FLITS first and pin only
   its reviewed merge commit.

## References

- [Research: Deterministic host-DM convolution](../research/research-dm-host-convolution.md)
- [Research: DM IGM PDF / Connor 2024](../research/research-dm-igm-pdf-connor2024.md)
- `scripts/dm_budget_uncertainty.py`
- `tests/test_dm_budget_uncertainty.py`
- `scripts/render_budget_table.py`
- `pipeline/galaxies/foreground/attribution_matrix.py`
