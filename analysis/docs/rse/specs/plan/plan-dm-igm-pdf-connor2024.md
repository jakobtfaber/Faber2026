# Implementation Plan: Replace Macquart DM_IGM surfaces with the Connor 2024 TNG median

---
**Date:** 2026-07-09
**Author:** Claude (Fable 5) + Codex `Faber2026-codex` (gpt-5.6-sol, repowire mesh)
**Status:** Draft
**Related Documents:**
- [Research: DM_IGM PDF / Connor 2024](../research/research-dm-igm-pdf-connor2024.md)

---

## Overview

The budget table's ⟨DM_cos⟩ column is a Macquart-relation mean at f_IGM = 0.84
sitting in the same table as a forward model calibrated to the Connor et al.
2024 TNG-300 log-normal at f_IGM = 0.76. This plan replaces every remaining
Macquart-based DM_IGM construction with a single TNG-calibrated helper, per the
user-approved decisions: **table column → TNG median @ 0.76** (relabeled),
**`dm_host_arith` comparator → TNG log-normal *mean* subtraction** (preserving
the mean-subtraction-bias pedagogy), **sensitivity path → migrated to the TNG
median**. `dm_cosmic_macquart()` survives as a cross-check utility.

**Goal:** one IGM calibration (Walker 2024 grid via Connor 2024, f_IGM = 0.76)
feeding the table, the plots, the sensitivity runs, and the comparator; all
tests green in both repos; manuscript prose consistent with the new column.

**Motivation:** removes a referee-visible inconsistency (two baryon fractions
in one table; mean point estimate beside median posteriors) and closes the two
documentation gaps found in research (ρ(z) dropping, 0.797-vs-0.827
provenance).

**Expected numeric shift** (old Macquart 0.84 → TNG median 0.76; means shown
for the comparator; computed from the grid this session):

| burst | z | old ⟨DM_cos⟩ | new median | TNG mean (comparator) |
|---|---|---|---|---|
| 20220207C | 0.043 | 36 | 32.1 | 34.0 |
| 20220310F | 0.479 | 427 | 383.5 | 391.7 |
| 20220506D | 0.300 | 262 | 232.5 | 240.1 |
| 20221113A | 0.251 | 217 | 193.3 | 200.5 |
| 20221203A | 0.510 | 456 | 410.5 | 418.7 |
| 20230307A | 0.271 | 235 | 209.2 | 216.7 |
| 20230913A | 0.302 | 264 | 234.1 | 241.7 |
| 20240203A | 0.074 | 62 | 55.7 | 58.9 |
| 20240229A | 0.287 | 250 | 222.0 | 229.6 |

Forward-model posteriors (table DM_host column, appendix table, CSV
p16/p50/p84, P(<0)) are **unchanged** — `sample_dm_cosmic()` never used the
point estimate.

## Current State Analysis

**Pipeline submodule** (detached at pin `14e0d1f`; work lands on
`origin/pin/faber2026`; conda env `flits`, py3.12):

- `galaxies/foreground/sightline_budget.py:97-98` — `F_IGM = 0.84`,
  `CHI_E = 0.875`; `:130-151` — `dm_cosmic_macquart()`; `:651` — the single
  call producing the table's cosmic value; `:727` — provenance string
  `"PREDICTED_MEAN"`; `:12` — docstring names the Macquart mean.
- `flits/batch/dm_models.py:37,56-59` — `Cosmology.dm_cosmic_slope = 780`,
  `dm_cosmic_mean()`; sole non-demo caller is
  `flits/batch/sightline_plots.py:125` (cumulative DM-ledger panel).
- `galaxies/foreground/sightline_sensitivity.py:150-155` —
  `scaled_dm_cosmic()` rescales `dm_cosmic_macquart` linearly in f_IGM ×
  `cosmic_scatter`; `:133,143` — family draws.
- `galaxies/foreground/budget_table_emitter.py:29-32,117-127,134-136,144-148`
  — reads `budget_table_data.json["rows"][i]["dm_cos"]`; caption phrase
  "Macquart mean at the host redshift" at `:54-55`; column header `:72-75`;
  CLI `:151-170` (`python -m galaxies.foreground.budget_table_emitter
  [-o PATH] [--check]`, default out `exports/budget_table.tex`).
- `galaxies/foreground/budget_table_data.json:22-237` — 12 rows; `dm_cos` int
  or null (3 placeholder-z rows null).
- Tests: `galaxies/foreground/test_sightline_budget.py:19-27` (Macquart
  properties — keep, function survives), `:165-186` (budget closure vs
  `dm_cosmic_macquart(0.30)` at `:183`);
  `test_sightline_sensitivity.py:50-74` (`:71-72` recomputes via
  `scaled_dm_cosmic`); `test_budget_table_emitter.py:32-35,49-59,68-97`
  (JSON↔CSV dm_host parity + byte-exact TeX parity).
- Namespace packages: `[tool.setuptools.packages.find] where=["."],
  namespaces=true` + pytest `pythonpath=["."]` — `galaxies.*` is importable
  from `flits/batch`.
- Guards: protected-branch commit hook (branch first), post-edit autoformatter
  (imports must land in the same edit as their first consumer), entire-ledger
  closeout, deferred-tasks + figure-review Stop gates, ponytail style.

**Faber2026 super-repo** (HEAD `45ed2d8` at plan time):

- `scripts/dm_budget_uncertainty.py:65-76` — `SIGHTLINES` with the old
  Macquart ints; `:214` — `dm_host_arith` subtracts them; `:100-119` — TNG
  grid (verified verbatim vs `tng_params_new.npy`); `:151-175` —
  `igm_lognormal_shape/params`; `:85-87` — `FIGM_MED=0.76`, `FIGM_TNG=0.797`.
- `tests/test_dm_budget_uncertainty.py:70-84` (low-z continuation — keep),
  `:87-106` (asserts TNG mean ≤ tabled Macquart value — **inverts** under the
  new median column; must be replaced), `:125-130` (f_IGM shift — keep).
- Prose: `sections/budget.tex:22-26` (eq:dmbudget writes
  ⟨DM_cosmic⟩(z)), `:34-36` (Macquart-mean sentence);
  `sections/appendix.tex:84-89` (0.797 mention), `:85-100` (IGM-marginal
  paragraph; ρ(z) never mentioned); root `budget_table.tex` (generated).
- `REPRODUCE.md:174-183` — root-table regeneration recipe;
  `.github/workflows/table-parity.yml:44-59` — CI `--check`.

## Desired End State

- New module `galaxies/foreground/igm_lognormal.py` is the **only** place the
  TNG grid lives in the pipeline; `sightline_budget`, `sightline_plots`, and
  `sightline_sensitivity` all consume it.
- Budget table column relabeled $\widetilde{\mathrm{DM}}_{\mathrm{IGM}}$ with
  TNG medians @ 0.76; caption cites Walker 2024 + Connor 2024, not "Macquart
  mean".
- `dm_host_arith` = DM_obs − DM_MW − exp(μ+σ²/2)·(0.76/0.797) − DM_int.
- Manuscript prose updated; appendix gains the ρ(z) sentence and the
  0.797-provenance footnote.
- All tests pass in both repos; forward-model CSV p16/p50/p84/P(<0) identical
  to pre-change values.

## What We're NOT Doing

- [ ] Not adopting Connor's full bivariate (IGM, halo) likelihood or its
      ρ(z) covariance — the census-based DM_int adaptation stands (research
      doc, Prior Art §Halo/IGM partition); we only *document* the dropped ρ.
- [ ] Not changing the forward model (`sample_dm_cosmic`, f_IGM
      marginalization, low-z continuation) — already Connor-based.
- [ ] Not re-inferring f_IGM or touching FIGM_MED/FIGM_TNG values.
- [ ] Not deleting `dm_cosmic_macquart()` or `Cosmology.dm_cosmic_mean()` —
      both stay as labeled legacy/cross-check utilities.
- [ ] Not redesigning the sensitivity prior families (f_IGM ranges stay).
- [ ] Not adding a Deng & Zhang 2014 bib entry (no manuscript citation after
      this change; code comments suffice).
- [ ] Not touching the other session's lanes (`journal.jsonl` edits,
      unified-12burst-figure specs).

**Rationale:** ponytail-minimal, decision-complete scope; the approved swap
only.

## Implementation Approach

**Key decisions** (user-approved 2026-07-09):
1. Table point statistic = TNG **median** @ f_IGM = 0.76 — consistent with the
   host-posterior medians; alternatives (TNG mean / keep-Macquart+footnote)
   rejected for skew-mixing / leaving the inconsistency.
2. Comparator = TNG **mean** subtraction — preserves the "mean-subtraction
   biases the host low" pedagogy without Macquart.
3. Sensitivity migrates: `scaled_dm_cosmic` base swaps to the median helper
   (f_IGM rescale is linear either way: exp(μ+ln(f/0.797)) = median·f/0.797).
4. Canonical grid module lives in `galaxies/foreground/` (has `__init__.py`,
   scipy available, namespace-importable from `flits/batch`). The Faber2026
   script stays self-contained (its own verbatim grid) — a new cross-repo test
   asserts script↔module agreement at the 9 sightline redshifts.
5. Interpolation stays `scipy.interpolate.UnivariateSpline(s=0)` (cubic),
   identical to the Faber2026 script, so both repos produce identical values.
6. Rounding for JSON ints: `f"{value:.0f}"` (round-half-even) is adopted as
   the **new explicit convention** (the current JSON ints were introduced as
   static values in pipeline commit `386e886` with no recorded generator;
   round() and `.0f` agree on all current values). The Phase-5 parity test
   enforces it. Exact new ints (Codex-verified this session):
   **32, 384, 232, 193, 410, 209, 234, 56, 222**.
7. Conda invocations use the agent-safe wrapper (AGENTS.md runtime rule),
   spelled in full — a string env var is not a robust executable wrapper, so
   either type the full prefix each time or define a shell *function*:
   `crun_flits() { env -i HOME="$HOME" PATH="/opt/anaconda3/bin:/opt/homebrew/bin:/usr/bin:/bin" /opt/anaconda3/bin/conda run -n flits "$@"; }`
   (and `crun_py312` analogously). Every `conda run -n flits/py312` below
   means this wrapper, executed with cwd = `pipeline/` for pipeline commands.

**Patterns followed:** grid constants + shape/params helpers mirror
`scripts/dm_budget_uncertainty.py:100-175`; test style mirrors
`test_sightline_budget.py`; regeneration flow mirrors `REPRODUCE.md:174-183`.

**Branch/landing sequence** (two repos, standing push/PR auth):
pipeline branch `igm-tng-median` off `origin/pin/faber2026` → PR → merge →
Faber2026 branch `ms/dm-igm-median`: pin bump + script/tests/prose → PR.
Before the pin bump: `git -C pipeline merge-base --is-ancestor 14e0d1f <new>`.

## Implementation Phases

Work in the pipeline submodule happens on a worktree-checkout of
`igm-tng-median` (one agent per tree; the submodule dir itself is fine since
no other agent works there — verify with `lane-liveness` before starting).
Conda env `flits` for pipeline commands; `py312` for Faber2026 scripts.

### Phase 1 (pipeline): canonical TNG log-normal module

**Objective:** one importable source of truth for the TNG grid + median/mean.

**Tasks:**

- [ ] Branch: `git -C pipeline fetch origin && git -C pipeline switch -c
      igm-tng-median origin/pin/faber2026`
- [ ] **Write the failing test** — file
      `pipeline/galaxies/foreground/test_igm_lognormal.py` (new):

  ```python
  import math

  import pytest

  from galaxies.foreground import igm_lognormal as igm

  # (no numpy import -- unused, and the post-edit autoformatter strips it)


  def test_grid_node_median_exact():
      # z=0.3 is a grid node: median = exp(mu)*f/f_TNG with mu=5.4962193
      expect = math.exp(5.4962193) * (0.76 / 0.797)
      assert igm.dm_igm_median(0.3) == pytest.approx(expect, rel=1e-9)


  def test_mean_exceeds_median_by_lognormal_factor():
      mu, sig = igm.igm_lognormal_shape(0.3)
      assert igm.dm_igm_mean(0.3) == pytest.approx(
          igm.dm_igm_median(0.3) * math.exp(sig**2 / 2), rel=1e-12)


  def test_low_z_continuation_continuous_and_vanishing():
      # continuous at the grid edge, ~linear in z below it
      assert igm.dm_igm_median(0.1) == pytest.approx(
          igm.dm_igm_median(0.0999), rel=2e-3)
      assert igm.dm_igm_median(1e-4) < 0.5
      assert igm.dm_igm_median(2e-4) == pytest.approx(
          2 * igm.dm_igm_median(1e-4), rel=1e-3)


  def test_monotone_and_bounds():
      zs = [0.05, 0.1, 0.3, 0.5, 1.0, 3.0, 5.0]
      meds = [igm.dm_igm_median(z) for z in zs]
      assert all(a < b for a, b in zip(meds, meds[1:]))
      with pytest.raises(ValueError):
          igm.dm_igm_median(5.01)
      with pytest.raises(ValueError):
          igm.dm_igm_median(0.0)


  def test_f_igm_rescale_is_linear():
      assert igm.dm_igm_median(0.3, f_igm=0.9) == pytest.approx(
          igm.dm_igm_median(0.3, f_igm=0.45) * 2, rel=1e-12)
  ```

- [ ] **Run, watch it fail** (cwd `pipeline/`): `conda run -n flits python -m
      pytest galaxies/foreground/test_igm_lognormal.py -v` → collection error,
      `igm_lognormal` module not found
- [ ] **Implement** — file `pipeline/galaxies/foreground/igm_lognormal.py`
      (new; grid verbatim from `tng_params_new.npy`, mirrors
      `scripts/dm_budget_uncertainty.py:100-175`):

  ```python
  """TNG-300-calibrated log-normal IGM DM column (Walker 2024 via Connor 2024).

  Bivariate (IGM, halo) log-normal fit to a mock FRB survey in IllustrisTNG-300
  (Walker et al. 2024); IGM marginal (mu_IGM, sig_IGM) tabulated in the Connor
  et al. 2024 reproduction package (tng_params_new.npy, arXiv:2409.16952).
  f_IGM rescaling shifts the log-median by ln(f_igm / F_IGM_TNG); the baseline
  0.797 follows Connor's released implementation (frbdm_mcmc_jit.py), which
  differs from the 0.827 quoted in the paper TeX -- the code produced the
  published posteriors. Below the z=0.1 grid edge, mu(z) is continued along the
  Macquart-relation redshift dependence int_0^z (1+z')/E(z') dz' (exact as
  z->0; matches tabulated increments to 1.5% over 0.1<z<0.3) and sigma is held
  at its grid-edge value. Same construction as the Faber2026 forward model
  (scripts/dm_budget_uncertainty.py); test_igm_lognormal.py guards agreement.
  """
  from __future__ import annotations

  import math

  import numpy as np
  from scipy import integrate, interpolate

  F_IGM_CONNOR = 0.76   # Connor et al. 2024 posterior median (N=68 sample)
  F_IGM_TNG = 0.797     # TNG baseline in Connor's released implementation

  TNG_ZGRID = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0])
  TNG_MU_IGM = np.array([4.37380909, 5.07264111, 5.4962193, 5.80209722, 6.04344301,
                         6.40614181, 6.78312432, 7.19849362, 7.48250248, 7.86255147,
                         8.11920163, 8.30542453])
  TNG_SIG_IGM = np.array([0.33479241, 0.29198339, 0.25434913, 0.22449515, 0.20123352,
                          0.17974651, 0.16545537, 0.14851468, 0.13239113, 0.11009793,
                          0.09384749, 0.08155763])
  _MU_SPL = interpolate.UnivariateSpline(TNG_ZGRID, TNG_MU_IGM, s=0)
  _SIG_SPL = interpolate.UnivariateSpline(TNG_ZGRID, TNG_SIG_IGM, s=0)

  _OMEGA_M, _OMEGA_L = 0.3111, 0.6889  # Planck 2018, matches the super-repo script


  def _macquart_integral(z: float) -> float:
      val, _ = integrate.quad(
          lambda x: (1.0 + x) / math.sqrt(_OMEGA_M * (1.0 + x) ** 3 + _OMEGA_L),
          0.0, z, limit=200)
      return val


  _I_ZMIN = _macquart_integral(float(TNG_ZGRID[0]))


  def igm_lognormal_shape(z: float) -> tuple[float, float]:
      """(mu, sigma) of ln DM_IGM at redshift z, at f_IGM = F_IGM_TNG."""
      z = float(z)
      if not 0.0 < z <= float(TNG_ZGRID[-1]):
          raise ValueError(f"z={z} outside supported range (0, 5]")
      if z >= float(TNG_ZGRID[0]):
          return float(_MU_SPL(z)), float(_SIG_SPL(z))
      mu = float(TNG_MU_IGM[0]) + math.log(_macquart_integral(z) / _I_ZMIN)
      return mu, float(TNG_SIG_IGM[0])


  def dm_igm_median(z: float, f_igm: float = F_IGM_CONNOR) -> float:
      """Median DM_IGM(z) [pc/cm^3], log-median shifted by ln(f_igm/F_IGM_TNG)."""
      mu, _ = igm_lognormal_shape(z)
      return math.exp(mu) * (f_igm / F_IGM_TNG)


  def dm_igm_mean(z: float, f_igm: float = F_IGM_CONNOR) -> float:
      """Log-normal mean exp(mu + sigma^2/2) [pc/cm^3], f_IGM-rescaled."""
      mu, sig = igm_lognormal_shape(z)
      return math.exp(mu + 0.5 * sig * sig) * (f_igm / F_IGM_TNG)
  ```

- [ ] **Run, watch it pass:** (from `pipeline/`) `conda run -n flits python -m
      pytest galaxies/foreground/test_igm_lognormal.py -v` → 5 passed
- [ ] **Commit:** `git -C pipeline commit -m "feat(foreground): TNG-300
      log-normal IGM helper (Walker 2024 via Connor 2024)" --
      galaxies/foreground/igm_lognormal.py galaxies/foreground/test_igm_lognormal.py`

**Verification:**
- [ ] `conda run -n flits python -c "from galaxies.foreground.igm_lognormal
      import dm_igm_median; print(f'{dm_igm_median(0.479):.1f}')"` (cwd
      `pipeline/`) → `383.5`

### Phase 2 (pipeline): budget point estimate → TNG median

**Objective:** the table's cosmic value comes from the new helper.

**Tasks:**

- [ ] **Make the existing closure test fail first** — edit
      `pipeline/galaxies/foreground/test_sightline_budget.py:183` (fixture
      variable is `b`, per `:165-186`) from
      `pytest.approx(sb.dm_cosmic_macquart(0.30))` to:

  ```python
  from galaxies.foreground.igm_lognormal import dm_igm_median
  # (import at top of file, same edit)
  assert b["dm_cosmic"] == pytest.approx(dm_igm_median(0.30))
  ```

- [ ] **Run, watch it fail:** `conda run -n flits python -m pytest
      galaxies/foreground/test_sightline_budget.py -v` → the closure test fails
      (budget still returns the Macquart value, 261.665… at z=0.30)
- [ ] **Implement** — `pipeline/galaxies/foreground/sightline_budget.py`, all
      in one edit (autoformatter constraint — import + consumer together):
  - `:651` `dm_cosmic = math.nan if z_is_placeholder else
    dm_cosmic_macquart(float(z_frb))` →
    `dm_cosmic = math.nan if z_is_placeholder else dm_igm_median(float(z_frb))`
  - **new** import added to both branches of the existing try/except import
    block at `:57-65` (there is no igm_lognormal import yet): relative branch
    `from .igm_lognormal import dm_igm_median`, direct-script branch
    `from galaxies.foreground.igm_lognormal import dm_igm_median`.
  - `:727` `"PREDICTED_MEAN"` → `"PREDICTED_MEDIAN_TNG"`
  - docstring `:12`: `DM_cosmic  <DM_cosmic>(z) Macquart relation mean (pure
    astropy)` → `DM_cosmic   median TNG-300 log-normal IGM column at
    f_IGM=0.76 (igm_lognormal.py); Macquart mean retained as cross-check`
  - `:96-98` comment above `F_IGM`: append `Used only by
    dm_cosmic_macquart(), which is retained as a cross-check; the budget's
    cosmic term now comes from igm_lognormal.dm_igm_median.`
  - **remaining "mean/cosmic" label surfaces** (Codex sweep) — same edit:
    `:79-82` placeholder comment ("the Macquart <DM_cosmic> and" → "the IGM
    median and"), `:438-445` verdict dict key stays `"cosmic/IGM"` but any
    "mean" wording in the surrounding comment updates, `:837-866` markdown
    table header/format strings mentioning the cosmic mean → median, `:916-930`
    figure label `"cosmic/IGM <DM>"` → `"cosmic/IGM (TNG median)"`.
  - **regenerate the checked-in outputs** this module writes
    (`:1100-1120`): `results/sightline_dm_scattering_budget.md` + `.svg` —
    exact command (cwd `pipeline/`, main guard `:1085-1138`; documented in
    `docs/.../handoff-2026-06-27-02-03-figure-regen-phase1.md:56`):
    `conda run -n flits python -m galaxies.foreground.sightline_budget`;
    the `.svg` regeneration triggers the figure-review gate → Read + verdict
    in `results/figures.review.json`.
- [ ] **Run, watch it pass:** `conda run -n flits python -m pytest
      galaxies/foreground/test_sightline_budget.py -v` → all pass (the
      `:19-27` Macquart property tests still pass — the function is unchanged)
- [ ] **Commit:** `git -C pipeline commit -m "feat(foreground): budget cosmic
      term = TNG median @ f_IGM=0.76" -- galaxies/foreground/sightline_budget.py
      galaxies/foreground/test_sightline_budget.py
      results/sightline_dm_scattering_budget.md
      results/sightline_dm_scattering_budget.svg results/figures.review.json`

**Dependencies:** Phase 1.

**Verification:**
- [ ] `conda run -n flits python -m pytest galaxies/foreground/ -v` → green.

### Phase 3 (pipeline): plots + sensitivity migrate

**Objective:** the DM-ledger panel and the prior-predictive path consume the
same helper.

**Tasks:**

- [ ] **Failing test** — edit
      `pipeline/galaxies/foreground/test_sightline_sensitivity.py:71-72`: the
      expected value recomputes via the *new* base:

  ```python
  from galaxies.foreground.igm_lognormal import dm_igm_median
  # (top of file, same edit; the fixture budget's redshift is 0.30 per :50-74)
  expected_cosmic = dm_igm_median(0.30, f_igm=draw["f_igm"]) * draw["cosmic_scatter"]
  ```

- [ ] **Run, watch it fail:** `conda run -n flits python -m pytest
      galaxies/foreground/test_sightline_sensitivity.py -v`
- [ ] **Implement** — `pipeline/galaxies/foreground/sightline_sensitivity.py:150-155`:

  ```python
  def scaled_dm_cosmic(z: float, f_igm: float, cosmic_scatter: float) -> float:
      """Prior-drawn cosmic DM: TNG median rescaled to the drawn f_IGM, times
      the multiplicative scatter knob (median scales linearly in f_IGM)."""
      if not math.isfinite(float(z)) or float(z) <= 0.0:
          return math.nan
      return float(igm_lognormal.dm_igm_median(float(z), f_igm=float(f_igm))
                   * float(cosmic_scatter))
  ```

  with `from galaxies.foreground import igm_lognormal` added at `:13` in the
  same edit. (Note: `igm_lognormal_shape` raises above z=5;
  `placeholder_z_max` ≤ 2.0 across all families, so no clamp is needed.)
- [ ] **Run, watch it pass:** same pytest command → green.
- [ ] **Plots** — `pipeline/flits/batch/sightline_plots.py:125`:

  ```python
  from galaxies.foreground.igm_lognormal import dm_igm_median
  # (top of file, same edit as the consumer below)
  dmcos = np.array([dm_igm_median(zz) if zz > 0 else 0.0 for zz in zg])
  ```

  (`zg = np.linspace(0, z_frb, 300)` includes z=0, which the helper rejects —
  map it to 0.0, the exact z→0 limit.)
- [ ] **Mark the legacy constructor** — `pipeline/flits/batch/dm_models.py:56-57`
      docstring: `"""Macquart relation mean <DM_cosmic>(z) [pc/cm^3] (legacy
      cross-check; production ledger uses galaxies.foreground.igm_lognormal)."""`
- [ ] **Smoke the panel** (note: `flits-batch summary` does NOT reach
      sightline_plots — `flits/batch/cli.py:88-96,198-207` reads
      ResultsDatabase/summary_plots): drive the plot function directly —
      build one sightline via the module's own loader
      (`sightline_from_results` / `plot_sightline` in
      `flits/batch/sightline_plots.py`, cf. `flits/batch/io_adapters.py`),
      save the figure to a scratch path, **Read the PNG**, and write the
      figure-review verdict if the output lands in a manifest-tracked dir.
- [ ] **Regenerate the checked-in sensitivity artifacts**
      (`sightline_sensitivity.py:359-377` writes
      `results/sightline_budget_sensitivity_{draws,summary}.csv`,
      `_summary.md`, `_priors.yaml`, `_knobs.png`): `conda run -n flits
      python -m galaxies.foreground.sightline_sensitivity` (same seed
      20260619 default) — values shift with the new base; commit them with
      this phase; `_knobs.png` triggers the figure-review gate.
- [ ] **Run the full affected suites:** `conda run -n flits python -m pytest
      galaxies/ flits/batch -v` (batch tests import sightline_plots).
- [ ] **Commit:** `git -C pipeline commit -m "feat: DM ledger + sensitivity on
      TNG median; Macquart marked legacy" -- flits/batch/sightline_plots.py
      flits/batch/dm_models.py galaxies/foreground/sightline_sensitivity.py
      galaxies/foreground/test_sightline_sensitivity.py
      results/sightline_budget_sensitivity_draws.csv
      results/sightline_budget_sensitivity_summary.csv
      results/sightline_budget_sensitivity_summary.md
      results/sightline_budget_sensitivity_priors.yaml
      results/sightline_budget_sensitivity_knobs.png results/figures.review.json`

**Dependencies:** Phases 1 **and 2** — the sensitivity regeneration flows
through `load_current_budgets()` (`sightline_sensitivity.py:381-388`), which
calls the live budget code, so Phase 2's swap must land first.

**Verification:**
- [ ] `conda run -n flits python -c "import numpy as np; from
      galaxies.foreground.sightline_sensitivity import scaled_dm_cosmic;
      print(f'{scaled_dm_cosmic(0.3, 0.76, 1.0):.1f}')"` → `232.5`

### Phase 4 (pipeline): table data + emitter + regeneration + PR

**Objective:** the shipped table artifacts carry the new column.

**Tasks:**

- [ ] **Recompute the 9 ints** (`.0f`, the new explicit convention):
      `conda run -n flits python -c "from galaxies.foreground.igm_lognormal
      import dm_igm_median as m; [print(z, f'{m(z):.0f}') for z in
      (0.043,0.479,0.300,0.251,0.510,0.271,0.302,0.074,0.287)]"` — expected
      **32, 384, 232, 193, 410, 209, 234, 56, 222** (verified this session);
      any deviation from these exact ints is an abort-and-investigate.
- [ ] **Edit `pipeline/galaxies/foreground/budget_table_data.json`:**
      the 9 non-null `dm_cos` row values → the recomputed ints; update the
      `_comment` (`:2`) to name the new provenance: `dm_cos = median of the
      TNG-300 log-normal IGM column at f_IGM=0.76
      (galaxies/foreground/igm_lognormal.py); regenerated 2026-07-09`.
- [ ] **Edit the emitter** — `pipeline/galaxies/foreground/budget_table_emitter.py`:
  - `:54-55` caption phrase `$\langle\mathrm{DM_{cos}}\rangle$ is\nthe Macquart
    mean at the host redshift` → `$\widetilde{\mathrm{DM}}_{\mathrm{IGM}}$ is
    the median of the TNG-300-calibrated log-normal IGM column
    (\citealt{Walker2024}; adopted via \citealt{Connor2024}) at
    $f_{\mathrm{IGM}}=0.76$, the same calibration sampled by the host forward
    model (Appendix~\ref{app:host-forward-model})`
  - `:72-75` column header `\colhead{$\langle\mathrm{DM_{cos}}\rangle$}` →
    `\colhead{$\widetilde{\mathrm{DM}}_{\mathrm{IGM}}$}`
  - `:60-62` caption's `P(\mathrm{DM_{cosmic}}\,|\,z)` → `P(\mathrm{DM_{IGM}}\,|\,z)`
    (the sampled distribution *is* the IGM marginal; matches the Phase-6
    equation renames).
  - `:18` docstring: delete the stale `--emit-tex` claim (confirmed absent
    from `sightline_budget.py` — fix while touching the file).
- [ ] **Failing→passing regeneration:** `conda run -n flits python -m
      galaxies.foreground.budget_table_emitter --check` → exits nonzero
      (bytes differ); then regenerate: `conda run -n flits python -m
      galaxies.foreground.budget_table_emitter` (writes
      `exports/budget_table.tex`); re-run `--check` → clean.
- [ ] **Emitter tests:** `conda run -n flits python -m pytest
      galaxies/foreground/test_budget_table_emitter.py -v` — the dm_host↔CSV
      parity (`:68-97`) is untouched (dm_host unchanged); byte parity
      (`:49-59`) passes against the regenerated export.
- [ ] **Supersession note** (pipeline-side stale doc):
      `docs/superpowers/plans/2026-06-19-sightline-budget-sensitivity.md:387`
      — prepend `> Superseded 2026-07-09: the Macquart-based sensitivity
      construction below predates the TNG-median migration
      (Faber2026 docs/rse/specs/plan/plan-dm-igm-pdf-connor2024.md).`
- [ ] **Commit + PR:** `git -C pipeline commit -m "feat(foreground):
      TNG-median dm_cos column + caption/header" --
      galaxies/foreground/budget_table_data.json
      galaxies/foreground/budget_table_emitter.py exports/budget_table.tex
      docs/superpowers/plans/2026-06-19-sightline-budget-sensitivity.md
      docs/entire-tracing-checkpoints.md` (ledger staged explicitly; if the
      post-commit hook dirties it again, one `--no-verify` tail commit); push
      `igm-tng-median`; `gh pr create --repo jakobtfaber/dsa110-FLITS --base
      pin/faber2026 --title "TNG-median IGM column (Connor 2024) replaces
      Macquart point estimate"`; merge on green CI.

**Dependencies:** Phases 1-3.

**Verification:**
- [ ] Local emitter tests green on the pipeline PR (`table-parity.yml` lives
      in **Faber2026**, `.github/workflows/table-parity.yml:1` — it runs on
      the Phase-5/6 super-repo PR, not here); `git -C pipeline merge-base
      --is-ancestor 14e0d1f <merge-sha>` → exit 0.

### Phase 5 (Faber2026): pin bump + comparator + tests

**Objective:** super-repo consumes the new pin; comparator switches to TNG
mean; tests assert cross-repo agreement.

**Tasks:**

- [ ] Branch: `git fetch origin && git switch -c ms/dm-igm-median origin/main`
      (Faber2026). Re-check HEAD immediately before committing (shared tree;
      another session is active).
- [ ] Pin bump: `git -C pipeline fetch origin && git -C pipeline checkout
      <merge-sha>`; `git add pipeline`.
- [ ] **Failing test** — replace
      `tests/test_dm_budget_uncertainty.py:87-106` (the now-inverted
      mean≤Macquart check) with an exact cross-repo parity assertion:

  ```python
  def test_sightline_dm_cos_matches_tng_median_and_pinned_table():
      # Cross-repo parity: SIGHTLINES dm_cos == round-half-even TNG median
      # AND == the pinned pipeline table's dm_cos, keyed by burst name.
      table = json.loads(
          (Path(__file__).parent.parent / "pipeline" / "galaxies" /
           "foreground" / "budget_table_data.json").read_text())
      json_cos = {r["burst"]: r["dm_cos"] for r in table["rows"]}
      for name, z, _obs, _mw, dm_cos, _int, _mass in dbu.SIGHTLINES:
          mu, _ = dbu.igm_lognormal_shape(z)
          med = math.exp(mu) * (dbu.FIGM_MED / dbu.FIGM_TNG)
          assert dm_cos == int(f"{med:.0f}"), name
          assert dm_cos == json_cos[name], name
      # (json, Path imports at top of file, same edit)


  def test_dm_host_arith_uses_tng_mean():
      row = dbu.SIGHTLINES[2]  # FRB 20220506D, z=0.300
      r = dbu.host_posterior(row)
      mu, sig = dbu.igm_lognormal_shape(0.300)
      mean = math.exp(mu + 0.5 * sig**2) * (dbu.FIGM_MED / dbu.FIGM_TNG)
      expect = row[2] - row[3] - mean - row[5]
      assert r["dm_host_arith"] == pytest.approx(expect, rel=1e-9)
  ```

- [ ] **Run, watch both fail:** `conda run -n py312 python -m pytest
      tests/test_dm_budget_uncertainty.py -v` (old ints, old arith).
- [ ] **Implement** — `scripts/dm_budget_uncertainty.py`:
  - `:65-76` `SIGHTLINES` `DM_cosmic_mean` entries → the 9 new ints from
    Phase 4 (rename the tuple-comment header `DM_cosmic_mean` →
    `DM_cos_median_tng`); update `:61-63` block comment (V5 provenance line →
    `dm_cos = TNG median @ f_IGM=0.76, matching budget_table_data.json on the
    pin`).
  - `:199-218` `host_posterior()`: replace the arith line

    ```python
    mu_a, sig_a = igm_lognormal_shape(z)
    dm_cos_mean = math.exp(mu_a + 0.5 * sig_a**2) * (FIGM_MED / FIGM_TNG)
    ...
    "dm_host_arith": dm_obs - dm_mw - dm_cos_mean - dm_int,  # TNG-mean subtraction
    ```

    (the tuple's `dm_cos_mean` element is no longer read here — it feeds only
    the new parity test; keep docstring `:5-10` updated: "subtracts the *mean*
    of the TNG-calibrated log-normal" replacing the Macquart wording; also
    update `:188-191` comment in `sample_dm_cosmic` — the "old Macquart point
    estimate" phrase → "the tabled TNG median (kept for provenance; not used
    to set the scale)").
- [ ] **Run, watch them pass**, then **regenerate:** `conda run -n py312
      python scripts/dm_budget_uncertainty.py` → new
      `scripts/dm_budget_uncertainty.csv` + `figures/dm_host_posteriors.{pdf,png}`.
- [ ] **Assert posteriors unchanged** (parsed, not grepped): define
      `SCRATCH=$(mktemp -d)`, then before the rerun
      `cp scripts/dm_budget_uncertainty.csv "$SCRATCH/pre.csv"`; after:

  ```bash
  python3 - "$SCRATCH/pre.csv" scripts/dm_budget_uncertainty.csv <<'EOF'
  import csv, sys
  pre, post = (list(csv.DictReader(open(p))) for p in sys.argv[1:3])
  assert len(pre) == len(post), (len(pre), len(post))  # zip would truncate
  keep = ("dm_host_p16", "dm_host_p50", "dm_host_p84", "p_host_negative")
  for a, b in zip(pre, post):
      if not a.get("burst"): continue
      assert all(a[k] == b[k] for k in keep), (a["burst"], a, b)
  print("posteriors identical")
  EOF
  ```

      Only `dm_host_arith` may differ. If any posterior column moves,
      **abort and investigate** (RNG path must be untouched).
- [ ] **Root table regeneration:** per `REPRODUCE.md:174-183`, from
      `pipeline/`: `uv run python -m galaxies.foreground.budget_table_emitter
      --out ../budget_table.tex`; then `conda run -n flits python -m pytest
      galaxies/foreground/test_budget_table_emitter.py -v`.
- [ ] **Commit** (pathspec-scoped; exclude other-session lanes):
      `git commit -m "feat(budget): TNG-median IGM column + TNG-mean
      comparator (Connor 2024)" -- pipeline budget_table.tex
      scripts/dm_budget_uncertainty.py scripts/dm_budget_uncertainty.csv
      figures/dm_host_posteriors.pdf figures/dm_host_posteriors.png
      tests/test_dm_budget_uncertainty.py`

**Dependencies:** Phase 4 merged.

**Verification:**
- [ ] `conda run -n py312 python -m pytest tests/ -v` → green.
- [ ] The parsed pre/post CSV comparison above printed `posteriors identical`.

### Phase 6 (Faber2026): manuscript prose + documentation gaps

**Objective:** prose matches the new column; the two research-doc gaps close.

**Tasks:**

- [ ] `sections/budget.tex:34-36`: replace `The\ncosmological mean
      $\langle\mathrm{DM_{cosmic}}\rangle(z)$ follows the Macquart\nrelation
      \citep{Macquart2020}.` with:

  ```latex
  The cosmological point estimate is the median of the TNG-300-calibrated
  log-normal IGM column at $f_{\mathrm{IGM}}=0.76$ (\citealt{Walker2024}, via
  \citealt{Connor2024}; Appendix~\ref{app:host-forward-model}), the same
  calibration the forward model samples; the \citet{Macquart2020} mean is
  retained in the pipeline only as a cross-check.
  ```

- [ ] `sections/budget.tex:22-26` (eq:dmbudget) — **rename to the IGM
      marginal**, not just de-bracket: since the identified halos (DM_X) are
      carried by the separate DM_int term (`budget.tex:52-55`), the cosmic
      symbol in the decomposition *is* the IGM column:
      `\langle\mathrm{DM_{cosmic}}\rangle(z)` → `\mathrm{DM_{IGM}}(z)`.
      Apply the same rename where the evaluation subtracts it:
      `budget.tex:62-63` (`\mathrm{DM_{cosmic}}` in the per-draw host
      equation) and `appendix.tex:72-73` (same equation). Narrative uses of
      "the diffuse cosmic term" stay. Then sweep:
      `rtk grep -n "DM_{cos" sections/*.tex` and resolve each remaining hit
      to either `\mathrm{DM_{IGM}}` (equation/symbol context) or unchanged
      prose ("cosmic") — the total-column definition sentence at
      `budget.tex:52-55` keeps `\mathrm{DM_{cos}}=\mathrm{DM_{IGM}}+\mathrm{DM_X}`
      by construction.
- [ ] `sections/budget.tex:1-14` header comment — update the stale summary
      lines (decomposition now names DM_IGM; point estimate is the TNG median
      at f_IGM=0.76; the NE2025 line was fixed in the dm-budget-parity lane).
- [ ] `sections/appendix.tex:84` — after the double-count sentence, insert:

  ```latex
  Using the IGM marginal alone also drops the (IGM, halo) covariance
  $\rho(z)$ of the bivariate fit; the identified-halo term is carried
  deterministically by the census, so no cross-covariance is propagated.
  ```

- [ ] `sections/appendix.tex:89` — footnote at the `f_{\rm IGM,TNG}=0.797`
      mention:

  ```latex
  \footnote{The published text of \citet{Connor2024} quotes a TNG baseline of
  $0.827$; their released analysis code (\texttt{frb\_baryon\_connor2024})
  implements $0.797$, which produced the published posteriors. We follow the
  implementation.}
  ```

- [ ] Stale-doc annotation:
      `docs/rse/specs/plan/plan-trust-reset-revalidation.md:1102` — prepend
      `> Superseded 2026-07-09: the independent Macquart oracle below predates
      the TNG-median column (plan-dm-igm-pdf-connor2024.md).` (the pipeline-side
      equivalent lands in Phase 4's explicit supersession task).
- [ ] **Compile:** `make` (repo root; aastex build) → clean; grep the log for
      `undefined` citations (Walker2024/Connor2024 already in `bib/refs.bib`).
- [ ] **Commit** on the same branch; push; `gh pr create` (base `main`) with
      the phase-4 PR linked; journal + rebake + redeploy board.

**Dependencies:** Phase 5.

**Verification:**
- [ ] `make` exits 0; `rtk grep -n "Macquart mean" sections/ budget_table.tex`
      → no hits outside the retained cross-check sentence.

### Phase 7: end-to-end validation

**Objective:** prove the two repos agree and nothing else moved.

**Tasks:**

- [ ] Pipeline: `conda run -n flits python -m pytest` (full suite, from
      `pipeline/`) → green.
- [ ] Faber2026: `conda run -n py312 python -m pytest tests/ -v` → green.
- [ ] Cross-repo value check (the parity the research doc promised):
      `conda run -n flits python -c "..."` printing
      `galaxies.foreground.igm_lognormal.dm_igm_median(z)` for the 9 z's must
      equal `scripts/dm_budget_uncertainty.py`'s
      `exp(igm_lognormal_shape(z)[0])*(0.76/0.797)` to 1e-9 — one-off script,
      output pasted into the PR description.
- [ ] Figure sanity (owner preference: every substantive step ships figures):
      attach the regenerated `figures/dm_host_posteriors.png` (orange crosses
      shift up by +2 to +37 pc/cm^3 = old Macquart mean minus new TNG mean,
      per sightline; posteriors static) to the PR/journal.
- [ ] `ai-research-workflows:validating-implementations` against this plan
      before calling the lane done.

## Success Criteria

### Automated Verification

- [ ] `conda run -n flits python -m pytest` green in `pipeline/` (includes
      new `test_igm_lognormal.py`, updated budget/sensitivity/emitter tests).
- [ ] `conda run -n py312 python -m pytest tests/ -v` green in Faber2026.
- [ ] `python -m galaxies.foreground.budget_table_emitter --check` exits 0
      (pipeline `exports/`), and again with `--out ../budget_table.tex`
      against the root copy.
- [ ] CI `table-parity.yml` green on the Faber2026 PR (the workflow lives only
      in the super-repo; the pipeline PR relies on local emitter tests).
- [ ] `git diff <pre>..<post> -- scripts/dm_budget_uncertainty.csv` touches
      only the `dm_host_arith` column (posterior columns byte-identical).
- [ ] `rtk grep -rn "dm_cosmic_macquart" pipeline/galaxies
      pipeline/flits --include='*.py' | grep -v test | grep -v "def
      dm_cosmic_macquart"` → no production call sites remain.

### Manual Verification

- [ ] Rendered `budget_table.tex`: column header reads
      $\widetilde{\mathrm{DM}}_{\mathrm{IGM}}$; caption cites Walker+Connor;
      the 9 values match the Phase-4 command output.
- [ ] `figures/dm_host_posteriors.png`: orange crosses moved up slightly;
      dark posterior points identical to the previous version.
- [ ] Compiled PDF: budget section reads coherently (median point estimate +
      mean-subtraction comparator story); appendix footnote renders.

### Reproducibility & Correctness

- [ ] Seeds unchanged (`RNG = default_rng(20260707)`, `N_DRAW = 200_000`);
      posterior invariance is the regression proof.
- [ ] Numerical criterion: grid-node median exact to rel 1e-9 vs
      exp(μ)·(0.76/0.797); cross-repo agreement to 1e-9 at the 9 sightline
      redshifts; JSON ints reproduce under `f"{v:.0f}"`.
- [ ] Exact regeneration commands captured above (emitter CLI, script rerun),
      matching `REPRODUCE.md:174-183`.

## Testing Strategy

Per-phase unit tests above. Additional coverage:

**Integration:** emitter byte-parity + dm_host↔CSV parity
(`test_budget_table_emitter.py`) exercised after both the pipeline JSON edit
(Phase 4) and the Faber2026 root regeneration (Phase 5); full-suite runs in
Phase 7.

**Manual:** compiled-PDF read of budget section + table + appendix; posterior
figure before/after comparison.

**Test data:** none new — inline dicts/tmp_path fixtures already used by the
pipeline tests; the TNG grid is constants.

## Migration Strategy

Old Macquart helpers stay in place (marked legacy/cross-check), so rollback is
localized: revert the pin bump commit (Faber2026) and/or revert the pipeline
PR merge on `pin/faber2026`. The generated artifacts (JSON, both
budget_table.tex, CSV, figures) are regenerable from either state via the
commands above — no data migration.

## Risk Assessment

1. **Risk:** rounding-convention mismatch (383.5 → 384 vs 383) between the
   plan's reference table and the implementation.
   - Likelihood: Medium; Impact: Low.
   - Mitigation: Phase 4 pins values from the *command output* with
     `f"{v:.0f}"`; the Phase 5 parity test enforces the same convention
     cross-repo.
2. **Risk:** pipeline post-edit autoformatter strips a new import.
   - Likelihood: Medium; Impact: Medium (NameError at runtime).
   - Mitigation: every import lands in the same edit as its first consumer
     (called out per task); suite runs after each phase.
3. **Risk:** shared-tree collisions with the active unified-12burst session
   (journal.jsonl, specs, possibly main HEAD movement).
   - Likelihood: Medium; Impact: Medium.
   - Mitigation: pathspec-only commits, `lane-liveness` + HEAD re-check
     immediately before each Faber2026 commit, branch-first everywhere.
4. **Risk:** the spline extrapolation/continuation drifts between repos
   (different scipy versions in `flits` vs `py312`).
   - Likelihood: Low; Impact: Medium.
   - Mitigation: Phase 7 cross-repo 1e-9 check; both use
     `UnivariateSpline(s=0)` on identical arrays.
5. **Risk:** prose claims elsewhere quote old ⟨DM_cos⟩ values.
   - Likelihood: Low (results.tex quotes DM_int/DM_host, not DM_cos values —
     verified in the dm-budget-parity audit).
   - Mitigation: Phase 6 grep for the 9 old ints in `sections/` before PR.

## Edge Cases and Error Handling

1. **Case:** placeholder-z sightlines (3 rows).
   - Expected: `dm_cos` stays null/NaN — `:651` keeps the `z_is_placeholder`
     guard; JSON rows untouched.
2. **Case:** z below the TNG grid (0.043, 0.074).
   - Expected: Macquart-shape continuation inside `igm_lognormal_shape`,
     identical to the forward model's; covered by
     `test_low_z_continuation_continuous_and_vanishing`.
3. **Case:** z=0 in the plot grid (`np.linspace(0, z_frb, 300)`).
   - Expected: mapped to 0.0 explicitly (exact limit); helper raises on z≤0
     by design.
4. **Case:** sensitivity placeholder_z draws up to 2.0.
   - Expected: within (0, 5] — no clamp needed; helper raises above 5 as a
     guard against silent extrapolation.
5. **Error:** emitter `--check` mismatch after regeneration.
   - Handling: CI/table-parity fails the PR; regenerate rather than hand-edit
     (files carry GENERATED headers).

## Documentation Updates

- [ ] `REPRODUCE.md` budget-table section: one line noting the column is now
      the TNG median (regeneration commands unchanged).
- [ ] Pipeline `docs/superpowers/plans/2026-06-19-...md:387` superseded note
      (Phase 4).
- [ ] `docs/rse/specs/plan/plan-trust-reset-revalidation.md:1102` superseded note
      (Phase 6).
- [ ] Journal entries + readiness-board redeploy at each phase boundary
      (owner protocol).

## Open Questions

None — the three design decisions were resolved by the owner on 2026-07-09
(median column / TNG-mean comparator / migrate sensitivity), and all
structural facts were verified against the code this session.

---

## References

**Research Documents:**
- [Research: DM_IGM PDF / Connor 2024](../research/research-dm-igm-pdf-connor2024.md)

**Files Analyzed:**
- `pipeline/galaxies/foreground/sightline_budget.py`,
  `sightline_sensitivity.py`, `budget_table_emitter.py`,
  `budget_table_data.json`, `test_sightline_budget.py`,
  `test_sightline_sensitivity.py`, `test_budget_table_emitter.py`
- `pipeline/flits/batch/dm_models.py`, `sightline_plots.py`
- `scripts/dm_budget_uncertainty.py`, `tests/test_dm_budget_uncertainty.py`
- `sections/budget.tex`, `sections/appendix.tex`, `budget_table.tex`,
  `REPRODUCE.md`, `.github/workflows/table-parity.yml`

**External:**
- Connor et al. 2024, arXiv:2409.16952v2 (TeX at
  `~/Downloads/arXiv-2409.16952v2/`); reproduction repo
  `liamconnor/frb_baryon_connor2024` (cached via opensrc)

---

## Review History

### Version 1.0 — 2026-07-09
- Initial plan; design decisions resolved via owner Q&A (median / TNG-mean
  comparator / migrate sensitivity). Structural facts gathered collaboratively
  (Codex: emitter/JSON/test contracts; Claude: implementation files + value
  computation).

### Version 1.1 — 2026-07-09
- Codex adversarial review (mesh thread `ask-9bd53df7`), 11 issues folded in:
  fixture-variable fixes in test snippets; corrected import-block wording;
  added the missed relabel surfaces (`sightline_budget.py:79-82,438-445,
  837-866,916-930`) and checked-in generated artifacts (results MD/SVG,
  sensitivity CSV/MD/YAML/PNG); replaced the wrong `flits-batch summary`
  smoke with a direct plot-function drive; strengthened the Phase-5 test to
  true cross-repo parity (reads the pinned JSON); replaced the grep-based CSV
  check with a parsed pre/post comparison; pinned the exact new ints
  (32, 384, 232, 193, 410, 209, 234, 56, 222) and named `.0f` the new
  rounding convention (old ints had no recorded generator, commit `386e886`);
  moved table-parity CI expectations to the super-repo PR; standardized the
  agent-safe conda wrapper; extended Phase 6 to the DM_IGM equation renames
  (budget.tex eq + :62-63, appendix.tex:72-73, emitter `P(DM_IGM|z)`) and the
  budget.tex header comment.

### Version 1.2 — 2026-07-09
- Second rigor round (Claude self-review + Codex phase-order simulation,
  mesh thread `ask-a73a1670`). Independent confirmations: the 9 ints re-derived
  to 4 decimals (32.10, 383.53, 232.45, 193.25, 410.50, 209.23, 234.07, 55.66,
  222.01); exp(σ²/2) ∈ [1.0201, 1.0576]; no old DM_cos ints quoted in prose;
  no checked-in test goes red between phases as sequenced; all v1.1 anchors
  verified. Fixes folded: Phase-2 and Phase-3 commit pathspecs now name every
  regenerated artifact (results MD/SVG, sensitivity CSV/MD/YAML/PNG,
  `figures.review.json`); Phase 3 depends on Phase 2 (sensitivity regeneration
  calls the live budget via `load_current_budgets()`); Phase 4 gained the
  explicit pipeline supersession-note task and names the entire ledger in its
  pathspec; `$SCRATCH` defined + row-count assert added to the CSV comparison
  (zip truncation guard); conda wrapper spelled as a shell function; Phase-1
  fail-command and Phase-5 stale grep bullet cleaned; unused numpy import
  dropped from the test snippet; Phase-5 branch bases on `origin/main`
  explicitly; 262.3→261.665 corrected; figure-shift range corrected to
  +2…+37 pc/cm³; "both PRs" CI criterion scoped to the Faber2026 PR.
