# Implementation Plan: Predicted-Delay Profile-Residual Trigger Calibration

---
**Date:** 2026-07-31
**Author:** AI Assistant (claude-fable-5), executing the owner decision of 2026-07-29
**Status:** Draft — plan only; no campaign has run
**Related Documents:**
- [Ticket 04a — Close the scattering escalation trigger](../wayfinder/tickets/04a-close-residual-trigger.md) (owner: validate before use)
- [Ticket 04 — Close the scintillation-to-scattering coupling design](../wayfinder/tickets/04-close-scint-scattering-coupling-design.md)
- [Plan: A1 escalation-trigger injection calibration](plan-a1-trigger-calibration.md) (retired ΔlnZ twin; structural precedent)

---

## Overview

The owner resolved ticket 04a on 2026-07-29: the predicted-delay mismatch rule
— escalate to a two-screen scattering fit when the observed burst profile
disagrees with profiles simulated from the fitted one-screen model at the time
delay predicted for a second screen — may not be used for model selection
until it is validated on known one-screen and two-screen examples, reporting
(a) the false-escalation rate on one-screen truth and (b) the detection rate
on two-screen truth. This plan builds that validation as an injection
campaign, mirroring the retired ΔlnZ calibration's structure
(`simulation/trigger_calibration.py`, per-cell checkpointing) but operating in
the profile domain with the production residual-escalation machinery.

## Current State Analysis

- The escalation rule exists and is un-windowed:
  `scattering/studies/joint-refits/residual_check.py:107` (`band_residual`)
  computes a whitened band-integrated residual S/N profile
  (`P[t] = Σ_f r[f,t]/√F_valid`), scans it with a log-spaced boxcar matched
  filter (`:63 _matched_max`), and sets
  `escalate = contiguous ≥5σ AND positive-dominated` (`:147`). It searches the
  whole on-pulse window, not the predicted-delay window.
- The predicted delay exists:
  `radio_pipeline/batch/analysis_logic.py:152-154` computes
  `implied_tau_from_dnu_ms = C1/(2π·Δν_d)` with `C1 = 1.16` (`:36`, thin
  Kolmogorov). In-code caveat `:192-194`: this is the τ·Δν statistic
  re-expressed, not an independent probe — the calibration must therefore
  treat the predicted delay as an input parameter of the trigger, not as
  independent evidence.
- Replicate machinery exists and is model-agnostic:
  `radio_pipeline/fitting/ppc.py:78` (`posterior_predictive_check`) accepts a
  caller-supplied summary statistic and generates noise replicates via
  `replicate_dataset` (`:63`).
- A closed-form nested two-screen forward model exists:
  `scattering/studies/joint-refits/twoscreen.py:129` (`two_screen_perchan`),
  `K(t) = [τ₂·EMG(σ,τ₂) − τ₁·EMG(σ,τ₁)]/(τ₂−τ₁)`, single extra parameter
  `r = τ₂/τ₁`, exactly recovering the production one-screen EMG at `r→0`
  (`R_FLOOR` `:66`).
- A truth-known injector with a realistic noise recipe exists:
  `scattering/studies/beta-proof-of-concept/run_beta_poc.py:92` (`_inject`)
  with the gain envelope and per-channel S/N recipe at `:101-107`.
- The campaign-loop and reporting template exists:
  `simulation/trigger_calibration.py:191/211/229` (`null_dlnz_cell`,
  `power_dlnz_cell`, `threshold_table`) and the per-cell checkpointing driver
  `simulation/scripts/run_a1_trigger_calibration.py`.
- Frozen realistic parameters exist: the DM-locked adjudication table
  `dispersion/studies/scattering-dm-locked/results/fit_adjudication.csv`
  (7 `accepted_physical` bursts) and committed fit JSONs under
  `scattering/studies/beta-campaign/fits/`.

## Desired End State

- A calibrated operating point for the predicted-delay trigger: a table of
  false-escalation rates on one-screen truth and detection rates on
  two-screen truth, per cell of a declared grid, with a conservative
  threshold envelope — the same reporting contract the owner accepted for the
  retired ΔlnZ calibration.
- The rates land in a campaign report JSON + markdown under
  `simulation/experiments/predicted-delay-trigger/`, and ticket 04a's
  follow-up state records where the owner accepts or rejects the operating
  point. Until that owner acceptance, the rule remains unavailable for model
  selection (unchanged).

## What We're NOT Doing

- Not sampling posteriors per injection. The trigger, as owner-worded,
  compares the observation with profiles simulated from the *fitted*
  one-screen model; the calibration fits each injection by maximum likelihood
  (Nelder–Mead on the gain-marginal likelihood) and generates replicates from
  that fitted model plus noise (`ppc.py:63`), not from posterior draws.
  Because every null-arm injection runs the full inject→fit→statistic path,
  the empirical null quantiles are rate-calibrated by construction; plug-in
  (no-refit) replicates bias the per-injection p-value in the conservative
  direction for false escalation. A small nested-sampling anchor set
  (Phase 5) measures the ML-vs-posterior-median model discrepancy as a
  separate check; it is not a replicate-arm correction.
- Not calibrating multi-component morphologies. Truth is single-component;
  production bursts carry 1–5 components, and structured multi-component fit
  residuals are exactly where spurious escalation is most plausible. The
  calibrated rates transfer only to single-component-adequate fits; the
  multi-component transfer is untested and must be stated in the report.
- Not calibrating across band geometries. The statistic's null distribution
  depends on the number of samples the window spans, so the campaign
  calibrates one declared CHIME-like geometry (2.56 microsecond sampling,
  where the physically motivated escalation cases live); invoking the rule
  on a different grid requires either matching geometry or a new arm.
- Not modifying `residual_check.py`, `joint_fit_diagnostics.py`, or anything
  under the controlled-run contract (`controlled_run.py:492-533` re-compares
  regenerated diagnostics, model-grid arrays, and panel hashes; nothing here
  may touch that path).
- Not porting or invoking the wave-optics simulator (`simulation/engine.py`)
  for truth generation; the closed-form two-screen kernel is exact for the
  exponential-PBF family under test and is nested in the production model,
  which the wave-optics route is not.
- Not deciding the operating point. The campaign measures; the owner accepts.
- Not wiring the trigger into production fit code. That happens only after
  owner acceptance, as its own reviewed change.

## Implementation Approach

New package `simulation/predicted_delay_trigger.py` plus a checkpointed driver
`simulation/scripts/run_predicted_delay_calibration.py`, both structured as
their ΔlnZ twins. Each calibration cell:

1. Build a truth waterfall on a DSA-like band grid: one-screen EMG
   (`null` arm) or closed-form two-screen kernel (`power` arm), with the
   `run_beta_poc` gain envelope and per-channel noise.
2. ML-fit the one-screen model (τ, σ, t₀, amplitude per component; α fixed to
   truth) with per-row analytic gain marginalization.
3. Compute the trigger statistic: matched-filter maximum of the whitened
   band-integrated residual profile restricted to the predicted-delay window
   `[t_peak + τ_pred·(1−w), t_peak + τ_pred·(1+w)]`, with τ_pred set from the
   injected second-screen τ₂ (power arm) or scanned over the same grid of
   τ_pred values (null arm — a one-screen case has no true τ₂, so the null
   rate must be measured at every τ_pred the rule could be invoked with).
4. Accumulate null samples → per-cell (1−rate) quantiles and a conservative
   max-envelope (`threshold_table` pattern); apply the same statistic to the
   power arm → detection rates.

Design decisions resolved now, recorded for the owner's review of the plan:
window half-width `w = 0.5` — a recorded reversible default covering ±50 %
uncertainty in τ_pred from the Δν_d measurement (the C1-convention spread at
`analysis_logic.py:29-36` is far larger, ×6–×20, and is treated instead by
calibrating the null at every τ_pred ratio the rule could be invoked with);
grids in Phase 4, with the null ratios covering the sub-τ₁ regime because a
resolved Δν_d implies a *nearer, smaller-τ* screen
(`analysis_logic.py:192-194`), so real invocations put the window over the
structured on-pulse residuals, the most escalation-prone region; truth on a
CHIME-like grid (2.56 microsecond sampling) where the casey-like τ₁ spans
~57 samples — on the DSA grid the same τ₁ is 0.15 samples and the campaign
would be vacuous; α fixed at 4.0 in truth and fit (production convention;
freeing α is a sensitivity extension, not the base campaign). τ₁(1 GHz) =
0.019 ms is used directly as screen 1's optical depth — a recorded deviation
from `twoscreen_stage0_inject.py:72`, which treats 0.019 ms as the composite
delay and derives `tau1 = tau_real/(1+r)`.

## Implementation Phases

### Phase 1 — Trigger statistic (pure functions, test-first)

**Objective:** `predicted_delay_statistic(...)` computing the windowed
matched-filter residual maximum, with exact-window unit tests.

1. Write the failing test `simulation/tests/test_predicted_delay_trigger.py`:

```python
import numpy as np
from simulation.predicted_delay_trigger import predicted_delay_statistic

def test_statistic_finds_injected_bump_only_inside_window():
    rng = np.random.default_rng(0)
    nf, nt, dt = 16, 4096, 0.00256  # ms, CHIME-like native sampling
    resid = rng.normal(0.0, 1.0, (nf, nt))
    t = np.arange(nt) * dt
    t_peak, tau_pred = 5.0, 3.0
    bump = np.exp(-0.5 * ((t - (t_peak + tau_pred)) / (2 * dt)) ** 2)
    resid += 4.0 * bump[None, :] / np.sqrt(nf)
    inside = predicted_delay_statistic(
        resid, valid=np.ones((nf, nt), bool), time_ms=t,
        t_peak_ms=t_peak, tau_pred_ms=tau_pred, window_frac=0.5)
    outside = predicted_delay_statistic(
        resid, valid=np.ones((nf, nt), bool), time_ms=t,
        t_peak_ms=t_peak, tau_pred_ms=1.0, window_frac=0.5)
    assert inside.matched_snr > outside.matched_snr
    assert inside.window_ms == (t_peak + 0.5 * tau_pred,
                               t_peak + 1.5 * tau_pred)

def test_statistic_is_invariant_to_masked_channels():
    rng = np.random.default_rng(1)
    nf, nt = 16, 256
    resid = rng.normal(0.0, 1.0, (nf, nt))
    valid = np.ones((nf, nt), bool); valid[3] = False
    t = np.arange(nt) * 0.00256
    a = predicted_delay_statistic(resid, valid, t, 1.0, 2.0, 0.5)
    resid2 = resid.copy(); resid2[3] = 1e6
    b = predicted_delay_statistic(resid2, valid, t, 1.0, 2.0, 0.5)
    assert a.matched_snr == b.matched_snr
```

Also add `"simulation/tests"` to the pytest `testpaths` list in
`pyproject.toml` in this phase — the directory is not currently collected,
so without this the "full suite stays green" criterion would silently never
run these tests.

Run: `uv run --group test --frozen python -m pytest simulation/tests/test_predicted_delay_trigger.py -q` — watch both fail (module absent).

2. Implement `simulation/predicted_delay_trigger.py`:

```python
"""Injection calibration of the predicted-delay profile-residual trigger.

Owner decision 2026-07-29 (ticket 04a): the rule is unavailable for model
selection until its false-escalation and detection rates are measured on
truth-known one- and two-screen examples.  Statistic: whitened
band-integrated residual profile (residual_check.py convention,
P[t] = sum_f r[f,t]/sqrt(F_valid)), matched-filter maximum restricted to
[t_peak + tau_pred*(1-w), t_peak + tau_pred*(1+w)].
"""
from __future__ import annotations
import dataclasses
import numpy as np

MATCHED_WIDTHS = (1, 2, 4, 8, 16)  # residual_check.py:63 log-spaced boxcars

@dataclasses.dataclass(frozen=True)
class TriggerStatistic:
    matched_snr: float
    best_width: int
    window_ms: tuple[float, float]
    n_window_samples: int

def predicted_delay_statistic(residual, valid, time_ms, t_peak_ms,
                              tau_pred_ms, window_frac):
    whitened = np.where(valid, residual, 0.0)
    n_valid = np.maximum(valid.sum(axis=0), 1)
    profile = whitened.sum(axis=0) / np.sqrt(n_valid)
    lo = t_peak_ms + tau_pred_ms * (1.0 - window_frac)
    hi = t_peak_ms + tau_pred_ms * (1.0 + window_frac)
    sel = (time_ms >= lo) & (time_ms <= hi)
    if not sel.any():
        return TriggerStatistic(float("nan"), 0, (lo, hi), 0)
    best_snr, best_w = -np.inf, 0
    window = profile[sel]
    for w in MATCHED_WIDTHS:
        if w > window.size:
            break
        kernel = np.ones(w) / np.sqrt(w)
        scanned = np.convolve(window, kernel, mode="valid")
        peak = float(scanned.max()) if scanned.size else -np.inf
        if peak > best_snr:
            best_snr, best_w = peak, w
    if not np.isfinite(best_snr):
        return TriggerStatistic(float("nan"), 0, (lo, hi), int(sel.sum()))
    return TriggerStatistic(best_snr, best_w, (lo, hi), int(sel.sum()))
```

3. Re-run the tests — watch them pass. Commit.

### Phase 2 — Truth generators (nesting-exact, test-first)

**Objective:** one- and two-screen truth waterfalls sharing one code path,
with the `r→0` nesting identity asserted.

1. Failing tests (append to the Phase 1 test file):

```python
from simulation.predicted_delay_trigger import make_truth_waterfall

def test_two_screen_truth_nests_to_one_screen_just_above_r_floor():
    # r must exceed twoscreen.R_FLOOR = 1e-6, else the kernel short-circuits
    # to the identical one-screen call and the test compares EMG with itself.
    one = make_truth_waterfall(seed=7, r=0.0, snr=15.0)
    nested = make_truth_waterfall(seed=7, r=1e-5, snr=15.0)
    np.testing.assert_allclose(one.clean, nested.clean, rtol=1e-3)

def test_truth_waterfall_snr_matches_request():
    tw = make_truth_waterfall(seed=3, r=0.0, snr=20.0)
    peak_channel = tw.clean.max(axis=1).argmax()
    measured = tw.clean[peak_channel].max() / tw.noise_std[peak_channel]
    assert 15.0 < measured < 25.0
```

2. Implement `make_truth_waterfall` in the same module: gain-envelope recipe
   copied from
   `scattering/studies/beta-proof-of-concept/run_beta_poc.py:101-107`
   (`(f/median f)**-1.5` envelope, lognormal scintillation `exp(N(0, 0.2))`,
   `sigma = max(clean)/snr`); band grid CHIME-like: 0.4–0.8 GHz, 32
   channels, 2.56 microsecond sampling, 4096 time samples. Kernel =
   `two_screen_perchan` imported from
   `scattering/studies/joint-refits/twoscreen.py:129` for `r > 0`, the
   production `analytic_gaussian_exp_convolution`
   (`scattering/scat_analysis/burstfit.py:121`) for `r == 0`. τ(ν) scaling
   is written inline in the GHz convention of those modules —
   `tau(f) = tau_1ghz_ms * f_ghz**(-4.0)` — deliberately NOT via
   `broaden.tau_per_freq`, whose `freqs_mhz`/`ref_freq_mhz=1000` convention
   silently produces a ~10¹¹ error if handed a GHz-valued grid. All times in
   this module are milliseconds; the only seconds surface is the
   `joint_burst.py:240` bound, converted explicitly where cited. Truth
   defaults: σ = 0.055 ms, τ₁(1 GHz) = 0.019 ms → τ₁(0.6 GHz) ≈ 0.147 ms
   ≈ 57 samples (resolvable; the same τ₁ on the DSA grid is 0.15 samples,
   which is why the DSA geometry is excluded from the base campaign).
   Import note: `scattering/studies/joint-refits` is not a package — load
   `twoscreen.py` via `importlib.util.spec_from_file_location` anchored at
   the repository root (pattern of
   `scattering/studies/joint-refits/likelihood_equivalence.py:72`).
3. Run, watch pass, commit.

### Phase 3 — ML refit of the one-screen model (test-first)

**Objective:** `fit_one_screen(waterfall) -> FittedModel` — Nelder–Mead on
the per-row gain-marginal Gaussian likelihood with (t₀, σ, τ₁) free and
α fixed at 4.0.

1. Failing test:

```python
from simulation.predicted_delay_trigger import fit_one_screen

def test_ml_fit_recovers_truth_on_low_noise_one_screen():
    tw = make_truth_waterfall(seed=11, r=0.0, snr=200.0)
    fit = fit_one_screen(tw)
    assert abs(fit.tau1_ms - tw.truth["tau1_ms"]) / tw.truth["tau1_ms"] < 0.10
    assert abs(fit.t0_ms - tw.truth["t0_ms"]) < 0.05
```

2. Implement using `scipy.optimize.minimize(method="Nelder-Mead")` over
   `(t0, log sigma, log tau1)`; per-row amplitude solved analytically by
   least squares against the unit-area kernel (the OLS gain recovery of
   `scattering/scat_analysis/joint_model_grid.py:15`); return the fitted
   model waterfall alongside parameters. Bounds as in
   `radio_pipeline/fitting/joint_burst.py:240`
   (`tau ∈ (1e-6, 5e-3) s`), enforced by log-parameterization plus a
   penalty on exit.
3. Run, watch pass, commit.

### Phase 4 — Campaign cells, grids, and report (checkpointed)

**Objective:** `null_cell`/`power_cell`/`rate_table` and the driver
`simulation/scripts/run_predicted_delay_calibration.py` with per-cell
checkpoint files, mirroring `run_a1_trigger_calibration.py`.

1. Failing test for the decision wrapper (statistic → replicate p-value):

```python
from simulation.predicted_delay_trigger import trigger_pvalue

def test_null_pvalues_are_uniformish():
    rng = np.random.default_rng(5)
    tw = make_truth_waterfall(seed=int(rng.integers(2**31)), r=0.0, snr=15.0)
    fit = fit_one_screen(tw)
    p = trigger_pvalue(tw, fit, tau_pred_ms=3 * fit.tau1_band_ms,
                      window_frac=0.5, n_replicates=200, seed=99)
    assert 0.0 <= p <= 1.0
```

   `trigger_pvalue` computes the observed statistic on
   `(data − fitted model)/noise`, then for each of `n_replicates` draws a
   replicate `fitted model + N(0, noise)` dataset
   (`radio_pipeline/fitting/ppc.py:63` recipe), re-computes the statistic on
   `(replicate − fitted model)/noise`, and returns the exceedance fraction.
   The replicate arm deliberately does NOT re-fit; the anchor set in Phase 5
   measures the resulting anti-conservatism.
2. Grids (declared here; the driver hard-codes them exactly as the ΔlnZ
   campaign did at `run_a1_trigger_calibration.py:52-60`). The null ratio
   set contains every power-arm ratio, because the physically motivated
   real-use regime is `tau_pred < τ₁` (a resolved Δν_d implies a nearer,
   smaller-τ screen) and the false-escalation envelope is meaningless if it
   never measures the window positions the power arm and real invocations
   use:
   - null arm: `snr ∈ {8, 15, 30}` ×
     `tau_pred/tau1_band ∈ {0.1, 0.3, 1.0, 3.0, 6.0}` × 200 injections;
     seeds `SEED0 + cell_index * 1000 + injection`.
   - power arm: `snr ∈ {8, 15, 30}` × `r ∈ {0.1, 0.3, 1.0, 3.0}` × 200
     injections, `tau_pred = r · tau1_band` (truth-informed prediction).
   - `SEED0 = 20260731`.
3. `rate_table(null_results, power_results, rates=(0.005, 0.01, 0.05))`:
   per-cell null quantiles, conservative max-envelope across null cells
   (`trigger_calibration.py:229` pattern, including the ≥50 %-finite guard
   and never-silently-dropped NaN accounting), and per-power-cell detection
   fraction at each envelope.
4. Driver: argparse over `--out`, `--cells` (default all), `--nproc`
   (default 4, hard cap; the workstation must not saturate); per-cell
   checkpoint JSON in `<out>.cells/`; final report JSON + markdown summary
   at `simulation/experiments/predicted-delay-trigger/`.
5. Smoke test (committed, small): 2 injections × 2 cells end-to-end via
   `pytest -m slow` marker; full campaign run is an operational step, not a
   test.

### Phase 5 — Nested-sampling anchor and closure report

**Objective:** measure the ML-surrogate bias and assemble the owner-facing
report.

1. Anchor set: 3 cells (null snr 15 × tau_pred/τ₁ ∈ {0.3, 3.0}; power
   snr 15 × r = 0.3) × 10 injections re-fit with the production nested path
   (`fit_joint_scattering`-equivalent single-band configuration, nlive 500),
   computing the same `trigger_pvalue` from the nested median model. This
   measures the ML-vs-posterior-median model discrepancy — a fidelity check
   on the surrogate fit, not a replicate-arm calibration correction (the
   null quantiles are rate-calibrated by construction; see Implementation
   Approach). Deliverable: per-injection paired (ML, nested) statistic table
   and the rank correlation; a mean absolute p-value shift > 0.05 flags the
   ML surrogate as unusable and stops the campaign report at PRELIMINARY.
2. Report `simulation/experiments/predicted-delay-trigger/README.md`: the
   two owner-required rates per cell, the envelope table, the anchor
   comparison, and the explicit statement that the rule remains unavailable
   until owner acceptance.
3. Queue the acceptance decision: follow-up entry in ticket 04a
   (`docs/rse/wayfinder/tickets/04a-close-residual-trigger.md`) with an
   owner decision card pointing at the report — the campaign does not
   self-accept.

## Success Criteria

### Automated Verification
- `uv run --group test --frozen python -m pytest simulation/tests/test_predicted_delay_trigger.py -q` — all Phase 1–4 tests pass.
- `uv run --group test --frozen python -m pytest -q` — full suite stays green (no controlled-run contract surface touched).
- Driver smoke: `run_predicted_delay_calibration.py --cells null:snr-15:taupred-3 --injections 2 --out /tmp/pd_smoke` exits 0 and writes a checkpoint cell file.
- Report generator asserts every declared cell present and ≥50 % finite samples per cell, else exits non-zero.

### Manual Verification
- Owner reviews the rate table and either accepts an operating point or
  rejects the trigger (recorded in ticket 04a).
- Visual spot-check of 3 null and 3 power injections (waterfall, fitted
  model, residual profile with the predicted-delay window drawn) — plots
  emitted by the driver per anchor cell.

## Risk Assessment

- **Sub-sample second screens.** Power-arm cells with
  `τ₂ = r·τ₁(band) < 2·dt` are flagged in the report as
  resolution-limited rather than counted as detection failures; at the
  CHIME-like grid this affects no declared cell (smallest τ₂ ≈ 0.015 ms ≈
  5.7 samples), and the driver asserts it at startup.
- **ML fit non-convergence.** Failed fits record NaN statistics; the
  ≥50 %-finite per-cell guard (inherited from `threshold_table`) turns
  systematic failure into a loud error, never a silent drop.
- **Surrogate infidelity.** The Phase 5 anchor's 0.05 mean-|Δp| threshold
  stops the report at PRELIMINARY rather than shipping a miscalibrated
  envelope.
- **Geometry transfer.** The calibration is declared valid only for the
  CHIME-like grid; the report states this restriction, and any DSA-grid
  invocation requires a new arm (the casey-like τ₁ is 0.15 samples there,
  so a DSA arm also needs a different truth configuration).

## Testing Strategy

- Unit: statistic windowing/masking exactness (Phase 1), nesting identity
  and S/N normalization of truth generation (Phase 2), truth recovery of the
  ML fit (Phase 3), p-value bounds (Phase 4).
- Integration: 2×2-cell smoke campaign through the real driver.
- Manual: anchor-cell diagnostic plots; owner rate-table review.

## References

- `docs/rse/wayfinder/tickets/04a-close-residual-trigger.md` — owner decision this plan executes.
- `docs/rse/specs/plan-a1-trigger-calibration.md` — retired ΔlnZ twin (structure + retirement rationale).
- Code anchors: `scattering/studies/joint-refits/residual_check.py:63,107,147`; `radio_pipeline/batch/analysis_logic.py:29-36,152-154,192-194`; `radio_pipeline/fitting/ppc.py:63,78`; `scattering/studies/joint-refits/twoscreen.py:66,129`; `scattering/studies/beta-proof-of-concept/run_beta_poc.py:85-107`; `simulation/trigger_calibration.py:191,211,229`; `simulation/scripts/run_a1_trigger_calibration.py:52-60`; `scattering/scat_analysis/joint_model_grid.py:15`; `radio_pipeline/scattering/broaden.py:141`; `dispersion/studies/scattering-dm-locked/results/fit_adjudication.csv`.
