# Research: Replacing Macquart-style DM_IGM PDF surfaces with Connor et al. 2024

**Date:** 2026-07-09
**Scope:** both (internal codebase + external prior art)
**Related Documents:** none (first doc in the `dm-igm-pdf` lane)
**Codebase state:** Faber2026 `45ed2d8` (2026-07-09), pipeline submodule at the
current pin; working tree carries one uncommitted comment fix in
`sections/budget.tex` (dm-budget-parity lane) unrelated to these findings.
**Method note:** collaborative two-agent pass — Codex peer `Faber2026-codex`
(gpt-5.6-sol, repowire mesh) digested the paper TeX and ran the adversarial
completeness sweep; Claude mapped the codebase and verified provenance against
the reproduction repository.
**Citations:** author-year names below resolve to `bib/refs.bib` keys:
`Connor2024`, `Walker2024` (bib/refs.bib:592), `Macquart2020`, `McQuinn2014`,
`James2022`. Deng & Zhang 2014 is cited in code comments only — it has **no
bib entry**; add one if the replacement keeps referencing it in the manuscript.

## Question / Scope

The request: replace the Macquart et al. 2020 / Zhang et al. 2021 style
construction of P(DM_IGM | z) in the Faber2026 DM-budget analysis with the
Connor et al. 2024 methodology (arXiv:2409.16952v2; TeX source at
`~/Downloads/arXiv-2409.16952v2/main.tex`, line anchors below refer to it).

Scoping result: **the forward model already adopts Connor et al. 2024**; the
question reduces to (i) inventorying exactly which surfaces remain
Macquart-based, (ii) verifying our existing Connor adoption against the paper
and its reproduction repository, and (iii) naming what a replacement of the
remaining surfaces entails. Zhang et al. 2021 is **not used anywhere** in the
repo (no citation, no lookup-style PDF; confirmed by grep and by the Codex
sweep), so "replace Zhang" is moot.

## Codebase Findings

### Already Connor-based (nothing to replace)

- `scripts/dm_budget_uncertainty.py:100-119` — the forward model's diffuse
  cosmic term is the IGM marginal of the `Walker2024` bivariate (IGM, halo)
  log-normal fit to IllustrisTNG-300, with the 12-point (z, mu_IGM, sigma_IGM)
  grid hard-coded. **Verified this session:** the grid matches
  `tng_params_new.npy` (columns 2 and 4) in Connor's reproduction repo
  byte-for-value (`frb_baryon_connor2024/main/src/tng_params_new.npy`).
- `scripts/dm_budget_uncertainty.py:85-87,169-196` — f_IGM = 0.76 (+0.10/−0.11)
  marginalized as a two-sided normal, shifting the log-median by
  ln(f_IGM / f_IGM,TNG) with `FIGM_TNG = 0.797`.
- `scripts/dm_budget_uncertainty.py:121-166` — deliberate, documented Macquart
  continuation of mu(z) below the TNG grid edge (z < 0.1), reproducing tabulated
  log-median increments to 1.5% over 0.1 < z < 0.3. This is an extension of the
  Connor calibration, not a competing PDF; it should stay.
- Prose already reflects this: `sections/budget.tex:44-67`,
  `sections/appendix.tex:69-121`.

### Still Macquart-based (the actual replacement surface)

1. **Point-estimate ⟨DM_cos⟩ column** —
   `pipeline/galaxies/foreground/sightline_budget.py:94-98` (`F_IGM = 0.84`,
   `CHI_E = 0.875`) and `:131-151` (`dm_cosmic_macquart()`, the Deng &
   Zhang 2014 / `Macquart2020` mean integral). Feeds the ⟨DM_cos⟩ column
   of `budget_table_data.json` → `budget_table.tex` (root copy + manuscript
   prose quoting those values). Reproduces the tabled values exactly (e.g.
   z = 0.479 → 426.944 → 427; verified by Codex against JSON line 48).
2. **Second, independent Macquart constructor in the batch pipeline** —
   `pipeline/flits/batch/dm_models.py:37,56-59`: an executable Macquart mean
   with a hard-coded `dm_cosmic_slope = 780`, consumed by
   `pipeline/flits/batch/sightline_plots.py:123-131` for the cumulative
   cosmic/IGM ledger in the sightline plots. Found by the Codex sweep; a
   replacement that only touches `sightline_budget.py` would leave the plots
   inconsistent with the table.
3. **Prior-predictive sensitivity path** —
   `pipeline/galaxies/foreground/sightline_sensitivity.py:41-105,133,150-155,179`:
   samples f_IGM ranges plus a multiplicative log-normal `cosmic_scatter`,
   rescaling `dm_cosmic_macquart()` to feed DM_host prior predictives. Distinct
   from the table point estimate; a replacement must decide whether this
   sensitivity machinery migrates to the TNG log-normal or is retired.
4. **`dm_host_arith` provenance column** —
   `scripts/dm_budget_uncertainty.py:214` subtracts the Macquart mean; kept in
   the CSV/figure as the "old mean-subtraction" comparator. If ⟨DM_cos⟩
   changes, this column changes with it (it reads `SIGHTLINES`, whose
   `DM_cosmic_mean` values at `:65-76` are copied from the V5 budget table).
5. **Tests that construct/consume the Macquart means** —
   `pipeline/galaxies/foreground/test_sightline_budget.py:19-27,183`;
   `pipeline/galaxies/foreground/test_sightline_sensitivity.py:71-72,97`;
   `tests/test_dm_budget_uncertainty.py:70-106,125-130`.
6. **Prose and docs** — `sections/budget.tex:34-36` ("cosmological mean …
   follows the Macquart relation"), the table caption emitted by
   `pipeline/galaxies/foreground/budget_table_emitter.py` ("the Macquart mean
   at the host redshift"), `sections/intro.tex:8` (contextual citation);
   non-manuscript docs that reproduce the construction and would go stale:
   `pipeline/docs/superpowers/plans/2026-06-19-sightline-budget-sensitivity.md:387-416`
   and the proposed independent Macquart oracle in
   `docs/rse/specs/plan/plan-trust-reset-revalidation.md:1102-1141`.

### Completeness (adversarial sweep)

Codex swept the whole repo including the `pipeline/` submodule
(case-insensitive: macquart, sigma_dm, F z, deng, zhang, dm_cosmic, dm_igm,
p_delta; plus tests/, docs/, figure scripts; mesh thread `ask-8cd3d887`). My
initial three-item inventory was **NOT confirmed** — items 2, 3, 5, and the
docs in item 6 above are the sweep's additions, folded in. The sweep also
cleared the false positives: Macquart–Koay hits in `scattering_predict.py` and
`sigma_dm` hits in `chime_dm.py`/`burstfit_robust.py` concern scattering and
measurement error, not cosmic-DM PDFs; Zhang hits are bibliographic/energy
uses; `pipeline/results/sightline_dm_scattering_budget.md:3` is an output
label, not a constructor. No active P(Delta)/fixed-F or Zhang-style lookup
implementation exists beyond the retired descriptions already noted.

### Cross-repo coupling (standing constraint)

- `budget_table.tex` is emitter-generated **in the pipeline submodule** but its
  parity test reads a Faber2026 CSV; the pipeline gitlink tracks a divergent
  dsa110-FLITS branch, never `main`. Any change to `sightline_budget.py`
  therefore lands as: PR to the pin's branch → regenerate
  `budget_table_data.json` + `budget_table.tex` → pin bump in Faber2026 →
  rerun `scripts/dm_budget_uncertainty.py` → CSV + figures + prose update
  (repo memories: budget-table-parity-spans-two-repos,
  pipeline-pin-lives-off-flits-main).

## Prior Art

All anchors are `main.tex:<line>` in `~/Downloads/arXiv-2409.16952v2/`.

- **PDF construction** (641-666): P_cos(DM_IGM, DM_X | z) is a *correlated
  bivariate* log-normal fitted to per-sightline IGM/halo columns from TNG300-1
  ray-traced mocks; the FRB likelihood is a double integral of P_cos × a
  log-normal P_host with DM_host = [DM_ex − DM_IGM − DM_X](1+z_s). A standalone
  P(DM_IGM | z) is a *marginal* of this object, not the paper's full
  likelihood.
- **f_IGM rescaling** (668-682): log-variances held at TNG values; medians
  shift as mu_IGM += ln(f_IGM / f_IGM,TNG), mu_X += ln(f_X / f_X,TNG).
  **Discrepancy found and resolved:** the TeX quotes baselines 0.827 / 0.138,
  but the reproduction repo's implementation uses **0.797 / 0.131**
  (`frb_baryon_connor2024/main/src/frbdm_mcmc_jit.py:115,140`) — the code that
  produced the published posteriors. Our `FIGM_TNG = 0.797` follows the
  implementation and is the defensible choice; record this provenance wherever
  the number is cited.
- **Inferred f_IGM** (106-120, 836-840): full N = 68 sample gives
  f_IGM = 0.76 (+0.10/−0.11) — the value we adopt; DSA-only 0.70 ± 0.13;
  z ≤ 0.8 subset 0.75 (+0.07/−0.08). Constraint driven by the low-DM "cliff"
  (no z > 0.1 source with DM_ex/z < 800; 286-304, 714-728); quoted errors
  inflated 30% for single-simulation model uncertainty (729-734).
- **Halo/IGM partition** (251-255, 498-520, 645-662): the paper integrates the
  joint (DM_IGM, DM_X) statistically, including their covariance rho(z); it
  specifies **no per-object DM_X subtraction or double-count guard**. Our
  pattern — IGM marginal + separately measured per-sightline DM_int census —
  is a *downstream adaptation*, not Connor's stated likelihood. The covariance
  between IGM and halo columns is dropped in our adaptation; this is already
  acknowledged implicitly in `scripts/dm_budget_uncertainty.py:26-32` but the
  rho-dropping is not stated in the manuscript.
- **Critique of the alternatives** (864-899): the fixed-F form
  sigma_DM = F z^{−1/2} (`Macquart2020`, `McQuinn2014`, `James2022`) assumes
  Poisson halo intersections, while TNG shows filament/sheet/void structure
  dominating with no z^{−1/2} scaling; the standard p(Delta) also cannot
  partition IGM from halos. Zhang et al. (cited as 2020 in the Connor TeX) /
  Walker-style snapshot ray-tracing gets means right but systematically
  mis-estimates *variance* from snapshot gaps (664-666) — the disconfirming
  context for any Zhang-style lookup PDF.
- **Reusable products** (1073-1081): reproduction repo
  https://github.com/liamconnor/frb_baryon_connor2024 (analysis + figure code,
  `data/frbsample_connor0924.csv`); the TeX itself never names
  `tng_params_new.npy` nor publishes the coefficient grid — reuse must trace
  through the repo (which we already do, verbatim).
- **Stated limitations** (278-282, 710-712, 729-734, 792-793, 829-834,
  861-862): single-simulation baseline (overfitting risk), selection modeled
  only via a DM < 1500 cutoff, no host-DM redshift evolution, priors
  mu_host ~ U(0,7) and f_IGM, f_X ~ U(0,1) with f_IGM + f_X ≤ 1 (plus a ≤ 0.98
  sensitivity variant). No explicit low-z validity boundary is claimed in the
  TeX — the z ≥ 0.1 limit is a property of the tabulated grid, which our low-z
  continuation already handles explicitly.

## Synthesis

The headline is that the manuscript's *forward model* already is the
state-of-the-art Connor et al. 2024 analysis — verified this session down to
the exact calibration grid and the implementation-vs-TeX baseline discrepancy.
What remains Macquart-based is narrow and enumerable:

1. **The ⟨DM_cos⟩ point-estimate column** (pipeline `sightline_budget.py`) is
   the primary replacement target: a Macquart *mean* at f_IGM = 0.84
   sitting next to a forward model at f_IGM = 0.76 — two different baryon
   fractions in the same table. The natural replacement is a Connor-consistent
   point statistic (median exp(mu(z)) or the log-normal mean at f_IGM = 0.76)
   from the same TNG grid + low-z continuation the forward model already uses.
   Choosing median vs mean, and whether the column keeps the name ⟨DM_cos⟩,
   is a planning decision (the mean of the skewed log-normal exceeds the
   median by exp(sigma²/2) ≈ 1.02–1.06 here).
2. **The replacement is wider than one function:** besides
   `sightline_budget.py`, the pipeline carries a second independent Macquart
   constructor (`flits/batch/dm_models.py`, hard-coded slope 780, feeding the
   sightline plots) and a prior-predictive sensitivity path
   (`sightline_sensitivity.py`) built on `dm_cosmic_macquart()` — all three
   must move together or the plots/sensitivity outputs diverge from the table.
   Knock-on surfaces span two repos: emitter + JSON + test fixtures in the
   pipeline (PR to the pin's branch, pin bump), then
   `SIGHTLINES`/`dm_host_arith` + CSV + figures + prose/caption/f_IGM-to-zero
   claims (currently 0.733/0.742) in Faber2026, plus the two stale-doc
   surfaces named in finding 6.
3. **Gaps worth naming in planning:**
   - The manuscript never states that our adaptation drops the (IGM, halo)
     covariance rho(z) of the bivariate fit — one sentence in the appendix
     would close it.
   - The TeX-vs-code baseline discrepancy (0.827/0.138 vs 0.797/0.131) is
     worth a provenance footnote wherever f_IGM,TNG = 0.797 is quoted.
   - Whether the ⟨DM_cos⟩ replacement changes any headline number: the swap
     0.84 → 0.76 alone shifts the mean column by ≈ −9.5%, which moves
     `dm_host_arith` (a displayed comparator) but not the forward-model
     posteriors (already at 0.76).

**Light recommendation** (design deferred to planning): replace
`dm_cosmic_macquart()`'s role in the budget table with the TNG-calibrated
median at f_IGM = 0.76, relabel the column, keep `dm_cosmic_macquart()` itself
as a cross-check utility, and fold the two documentation gaps above into the
same change. Next step: `ai-research-workflows:planning-implementations`.

## References / Sources

- Code: `pipeline/galaxies/foreground/sightline_budget.py:94-98,131-151`;
  `pipeline/flits/batch/dm_models.py:37,56-59`;
  `pipeline/flits/batch/sightline_plots.py:123-131`;
  `pipeline/galaxies/foreground/sightline_sensitivity.py:41-105,133,150-155,179`;
  `pipeline/galaxies/foreground/budget_table_emitter.py`;
  `pipeline/galaxies/foreground/test_sightline_budget.py:19-27,183`;
  `pipeline/galaxies/foreground/test_sightline_sensitivity.py:71-72,97`;
  `scripts/dm_budget_uncertainty.py:61-76,85-87,100-196,214`;
  `tests/test_dm_budget_uncertainty.py:70-106,125-130`;
  `sections/budget.tex:34-36,44-67`; `sections/appendix.tex:69-121`;
  `sections/intro.tex:8`; `budget_table.tex` (root, generated).
- External: Connor et al. 2024, arXiv:2409.16952v2 (`Connor2024`; TeX anchors
  above); reproduction repo
  https://github.com/liamconnor/frb_baryon_connor2024
  (`src/frbdm_mcmc_jit.py:115,140`, `src/tng_params_new.npy`,
  `data/frbsample_connor0924.csv`); `Walker2024` (bib/refs.bib:592; TNG-300
  bivariate log-normal calibration); `Macquart2020` (mean relation; superseded
  scatter form); Deng & Zhang 2014 (mean integral; code-comment
  citation, no bib entry); `McQuinn2014`, `James2022`
  (F-parameter scatter forms, superseded).
- Mesh threads: `ask-2262c5e4` (paper digest), `ask-8cd3d887` (completeness
  sweep), both closed by `Faber2026-codex`.
