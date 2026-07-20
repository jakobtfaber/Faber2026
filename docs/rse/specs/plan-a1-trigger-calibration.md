# Implementation Plan: A1 Escalation-Trigger Injection Calibration (ΔlnZ operating point)

---
**Date:** 2026-07-13
**Author:** AI Assistant (claude-fable-5), owner direction 2026-07-13
**Status:** Campaign complete; calibrated trigger failed the power requirement (2026-07-14)
**Related Documents:**
- [Plan: Circulation readiness — A1 charter](plan-circulation-readiness.md) (A-lane, trigger text revised 2026-07-13)
- [Plan: Trust-reset revalidation — V1 contract / ADR-0008](plan-trust-reset-revalidation.md)
- [Plan: CHIME scint recipe parity (P4c)](plan-chime-scint-recipe-parity.md)
- [Plan: CHIME scint γ campaign](plan-chime-scint-gamma-campaign.md)

---

## Final outcome (2026-07-14)

All 68 declared calibration cells completed and are preserved in the pinned
pipeline, but the planned trigger did not reach a usable operating point. The
conservative 1% false-escalation envelope is
`Delta ln Z = 59699.69283336272`, and all eight two-component power cells have
zero escalation probability. The implementation and calibration campaign are
complete; owner sign-off on this trigger is not warranted. See
[`report-chime-scintillation-inventory-2026-07-14.md`](report-chime-scintillation-inventory-2026-07-14.md)
and the canonical pipeline inventory for the full qualification record.

## Owner direction on closure (2026-07-15, in-session; wording ratified by the owner same day)

The ΔlnZ **screen-escalation** trigger is retired as calibrated-unusable (this
plan's Final outcome). The owner's standing requirement is a different
statistic: **a calibrated model-comparison criterion that justifies fitting N
profile components instead of 1** — burst-morphology component count, not
scattering-screen count (the two are distinct; multi-component morphology does
not imply multiple screens). Component counts are currently set by per-burst
visual morphology vetting; the successor statistic puts that on quantitative
footing. Chartered as **A5** in
[plan-circulation-readiness.md](plan-circulation-readiness.md); the dynesty
evidence engine built here (`acf_evidence.py`) is reusable groundwork for the
profile-domain comparison.


## Overview

The revised A1 escalation trigger (owner direction 2026-07-13) replaces hand-set
τ_near/τ_dom thresholds with evidence-based model comparison: a second
broadening component may be fitted only when (i) nested-sampling model
comparison on the frequency ACF prefers a two-component model over a single
Lorentzian at a ΔlnZ threshold set by an injection-calibrated false-escalation
rate on single-screen simulated dynamic spectra, or (ii) posterior-predictive
residuals appear in the burst profile at the predicted second-screen timescale.
This plan builds the ΔlnZ evidence engine, the correlated-lag likelihood that
prevents the second component from feeding on ACF sample variance, the
single-screen injection campaign, and the calibration report whose operating
point is the owner's remaining A1 sign-off input
(plan-circulation-readiness.md:74-76).

**Goal:** A merged FLITS PR chain delivering `acf_evidence.py` (dynesty 1-vs-2
component ACF comparison), an injection-calibrated ΔlnZ threshold table with
false-escalation and detection-power curves, a trigger-verdict function wired
to the PPC limb, and the calibration recorded as an ADR-0008 calibration entry
— so the owner can sign off A1 on a measured operating point.

**Motivation:** The 2026-07-06 draft trigger used uncalibrated numbers
(Pr > 0.1 at ratio 0.1, median > 0.03). With few scintles per subband, ACF
sample variance mimics extra components; an uncalibrated evidence cut is just
a different arbitrary number. Injection calibration on truth-known
single-screen spectra makes the threshold a measured quantity with a stated
false-escalation rate, consistent with the V1 re-trust contract's
injection-recovery rung (plan-trust-reset-revalidation.md:707-728).

## Current State Analysis

All code paths below are in the dsa110-FLITS repo (`pipeline/` submodule
checkout, working branch `dm-campaign-2026-07`; the dedicated pin branch is
`origin/pin/faber2026` = `dm-campaign-2026-07` + the PR #162 reference-arc
docs capture).

**Existing Implementation:**
- `scintillation/scint_analysis/analysis.py:234` — `calculate_acf`: canonical
  ACF with per-lag errors; lags start at 1 (`:283`); lag-0 is a synthetic 1.0
  symmetry token with `1e-9` placeholder error (`:320-327`); finite-scintle
  error `|ACF|·N_scintles^{-1/2}` with `N_scintles = BW/Δν_DC` (`:287-316`),
  combined with the SEM statistical error in quadrature (`:330-331`) —
  **diagonal only**, no lag covariance.
- `analysis.py:42,52,77` — Lorentzian component `m²/(1+(x/γ)²)`, generalised
  Lorentzian, fixed-width self-noise Gaussian; γ is HWHM and is reported as
  Δν_d directly (`:299-304`), no FWHM conversion.
- `analysis.py:685-770` — `_fit_acf_models`: lmfit Nelder fits, lag-0 excluded
  (`:700`), harmonic-comb masking for CHIME upchan (`:664`, `:701-707`).
- `revalidation.py:260,277` — `_n_lorentzian_model(n)` (sum of n Lorentzians +
  constant) and `compare_lorentzian_components` (BIC ΔBIC>6 AND nested F-test
  p<0.05, one-sided positive-lag fit `:323-332`). This is the existing
  component-count selector — frequentist, no evidence integral.
- `scattering/scat_analysis/burstfit_nested.py:306,419-449` — dynesty
  `NestedSampler` usage pattern: `logz[-1]`, `logzerr[-1]`, weight
  normalization. dynesty is the declared optional extra
  (`pyproject.toml:36`). This is the sampler pattern to reuse.
- `simulation/engine.py:84` — `FRBScintillator` two-screen wave-optics
  simulator; `simulation/wave_optics.py:59` — Kolmogorov phase screens;
  `simulation/recovery_campaign.py:123,146` — `recover_dnu_stacked` /
  `dnu_recovery_curve` Δν injection-recovery harness; `noise.py:110` —
  `NoiseDescriptor.sample` radiometer noise.
- `chime_artifact_guards.py:177` — `off_pulse_null_verdict` and the 35.19 kHz
  instrumental-artifact guard (freya-CHIME is the documented instrumental
  control).
- Reference two-screen ACF form `lor1+lor2+lor1·lor2+c` with width ordering
  `gamma2 = gamma1·factor, factor>1.01` exists only in the rescue capture:
  `git show scint/reference-arc-rescue:scintillation/scint_analysis/reference_arc/arc_live/...`
  (`analysis-Copy1.py:51-55,574-575`; RECIPE §3g).

**Current Behavior:** component count is chosen by BIC+F-test per subband,
aggregated by plurality (`analysis.py:1385`); nothing computes an evidence
ratio, nothing calibrates a decision threshold against injections, and nothing
connects the component count to a two-screen escalation decision.

**Current Limitations:**
- No Bayesian evidence for ACF component count; BIC on correlated ACF points
  with an asymptotic penalty is not a calibrated decision rule.
- ACF errors are diagonal; neighbouring-lag correlation (scintles are smooth
  over ~γ) lets a flexible second component absorb sample variance.
- The Δν injection-recovery harness reports a known recovered/injected ratio
  ≈ 0.29 (plan-trust-reset-revalidation.md:569-578, paired with the τ ratio
  ≈ 2.5 — a C₁ definitional-mismatch signature); any calibration grid must be
  stated in the production HWHM convention and checked against this bias.

## Desired End State

**New Behavior:** For any burst/subband set that has passed the P4c
measurement-status gates, `escalation_trigger_verdict` returns
`escalate ∈ {True, False}` with machine-readable reasons: ΔlnZ (2-vs-1
component, correlated-lag likelihood) against the injection-calibrated
threshold, OR a PPC `lag1_acf` failure at the predicted second-screen
timescale; a railed second component returns `model_family_rejection`, never a
detection. The calibration campaign has produced
`reports/a1_trigger_calibration.json` + figures, and ADR-0008 carries the
calibration entry.

**Success Looks Like:**
- ΔlnZ threshold table at 0.5%, 1%, 5% false-escalation rates over the
  (Δν_d/Δchan, S/N, N_subband) grid, with the 1% row nominated as the
  operating point.
- Detection-power curves: escalation probability vs γ₂/γ₁ and m₂²/m₁² for
  injected two-screen spectra.
- freya-CHIME instrumental control does **not** escalate; casey-DSA (4
  equal-S/N subbands) runs end-to-end as the real-data validation target.
- Owner sign-off request contains one figure + one table, nothing else needed.

## What We're NOT Doing

- [ ] Not re-fitting any real burst for science: every real-data run in this
      plan is `diagnostic_only` until V1 rungs pass (trust reset).
- [ ] Not implementing the A1 prior-odds layer (τ·Δν_d screen counting) or
      the A2 extended-medium PBF kernel — separate A-lane items.
- [ ] Not replacing `compare_lorentzian_components`; BIC+F-test remains as a
      cheap cross-check alongside ΔlnZ.
- [ ] Not building a full dynamic-spectrum-domain likelihood; the A1 text
      allows "finite-scintle (correlated-lag) covariance **or** an equivalent
      dynamic-spectrum-domain likelihood" — we implement the MC covariance and
      record the dynamic-spectrum route as the fallback if the covariance
      proves ill-conditioned beyond repair (Risk 2).
- [ ] Not bumping the Faber2026 `pipeline` gitlink — pin bumps are their own
      reviewed step.
- [ ] Not deciding the false-escalation rate for the owner: the report gives
      the 0.5/1/5% thresholds; the sign-off picks one (1% is the recommended
      default in the report text).

**Rationale:** the deliverable the owner is blocked on is the calibrated
operating point, nothing wider; A2/A3 explicitly proceed against the A1 draft
in parallel (plan-circulation-readiness.md:74).

## Implementation Approach

**Technical Strategy:** New module `scintillation/scint_analysis/acf_evidence.py`
computes lnZ for M1 (single Lorentzian + constant + optional fixed-width
self-noise Gaussian) and M2 (reference two-screen form
`lor1 + lor2 + lor1·lor2 + c`, width-ordered) on the one-sided,
lag-0-excluded ACF under a multivariate-normal likelihood with a Monte-Carlo
correlated-lag covariance. `simulation/trigger_calibration.py` drives the
injection campaign: single-screen dynamic spectra through the **production**
ACF path (`calculate_acfs_for_subbands`) — the sim_gate pattern — mapping the
ΔlnZ null distribution to thresholds; two-screen injections give power.
Verdict wiring in `analysis.py` combines ΔlnZ, rail state of the second
component, and the rung-iv PPC limb.

**Key Architectural Decisions:**
1. **Decision:** dynesty static `NestedSampler`, `nlive=500`, `dlogz=0.1`,
   following `burstfit_nested.py:419-449`.
   - **Rationale:** existing dependency and extraction pattern; 5–7 parameter
     models on ~10²-point ACFs are cheap.
   - **Trade-offs:** slower than BIC; acceptable because the campaign runs on
     h17 and per-burst production use is one comparison per subband set.
   - **Alternatives considered:** ultranest (new dependency), importance
     nested sampling (unneeded at this dimension).
2. **Decision:** M2 is the reference physical two-screen form
   `lor1 + lor2 + lor1·lor2 + c` (RECIPE §3g), not a plain sum of two
   Lorentzians.
   - **Rationale:** two multiplicative screens modulate multiplicatively; the
     cross term is the physical prediction and matches the rescued recipe —
     uniform-methods rule keeps one form across the sample.
   - **Trade-offs:** slightly stronger model (cross term); the calibration
     absorbs this into the null distribution, which is the point.
   - **Alternatives considered:** plain `lor1+lor2+c`
     (revalidation `_n_lorentzian_model(2)`) — kept as the BIC cross-check
     form only.
3. **Decision:** Correlated-lag covariance by Monte Carlo: M=500 matched
   single-screen realizations (fitted γ̂, band, S/N, channelization) through
   the production ACF path; Ledoit-Wolf shrinkage to the quadrature diagonal;
   likelihood via Cholesky of the shrunk covariance.
   - **Rationale:** the existing `_mean_noise_acf` MC (`analysis.py:399`) and
     `NoiseDescriptor` already establish the matched-realization pattern; an
     analytic scintle covariance would itself need MC validation.
   - **Trade-offs:** covariance conditioned on the *fitted* single-screen γ̂
     (null-hypothesis conditioning — correct for a false-escalation test).
   - **Alternatives considered:** diagonal-only (defeats the A1 requirement),
     dynamic-spectrum likelihood (heavier; recorded as fallback).
4. **Decision:** Priors, fixed here so the evidence is defined:
   M1/M2 γ₁ log-uniform [0.5·Δchan, BW/4]; m₁², m₂² uniform [0.01, 2];
   c uniform [−0.5, 0.5]; M2 width ratio f = γ₂/γ₁ log-uniform [3, 300];
   self-noise Gaussian amplitude uniform [0, 1] with σ_self fixed from the
   pulse-energy interval (RECIPE §6).
   - **Rationale:** ratio ≥ 3 encodes "genuinely distinct scale" (below that
     the components are same-screen ambiguity, which is trigger limb (ii)'s
     job, not (i)'s); upper bound 300 spans channel-resolution to band-scale.
   - **Trade-offs:** evidence depends on prior volume; the calibration report
     re-runs the grid's central cell with f ∈ [1.5, 1000] and tabulates the
     threshold shift as the prior-sensitivity entry.
   - **Alternatives considered:** ratio ≥ 1.01 (reference bound — fitting
     convenience, not a detection prior).
5. **Decision:** Operating point defined per subband-set comparison (the
   burst-level ΔlnZ is the sum over that burst's valid subbands), threshold
   from the max-over-grid null quantile (conservative envelope), reported at
   0.5/1/5% false-escalation.
   - **Rationale:** per-burst is the unit that escalates; the envelope over
     the grid avoids interpolating thresholds between calibration cells.
   - **Trade-offs:** conservative for easy cells; that is the correct
     direction for a trigger whose false fire re-opens two-screen fitting.
   - **Alternatives considered:** per-cell interpolated thresholds (fragile
     off-grid).

**Patterns to Follow:**
- dynesty evidence extraction — `scattering/scat_analysis/burstfit_nested.py:444-449`
- sim-through-production-path gating — `simulation/sim_fit_bridge.py:48-62`, sim_gate pattern
- one-sided lag-0-excluded ACF fitting — `revalidation.py:323-332`
- matched-noise MC — `analysis.py:399`, `noise.py:110`
- test conventions — pytest, `scintillation/scint_analysis/tests/`, `xfail_strict`

**Repo/branch mechanics:** branch `a1/trigger-calibration` off
`origin/pin/faber2026` in `~/Developer/repos/github.com/jakobtfaber/dsa110-FLITS`
(same convention as P4c; plan-chime-scint-recipe-parity.md:228-229). PRs to
`pin/faber2026`. No Faber2026 gitlink bump. Heavy campaign compute on h17.

## Implementation Phases

Phases 1–2 are pure evidence-engine work and can start now. Phase 3 depends on
P4c Phase 1 (lag/HWHM contract) only for constants already frozen in that
plan; Phase 5 depends on ADR-0008 existing (V1 P1.5) to receive the
calibration entry, and on P4c Phase 6 gates for real-data runs.

### Phase 1: ΔlnZ evidence engine (`acf_evidence.py`)

**Objective:** dynesty lnZ for M1 and M2 on a one-sided ACF with a supplied
covariance; validated on synthetic ACFs with known truth.

**Tasks:**
- [x] **Write the failing test** for single-screen truth preferring M1
  - File: `scintillation/scint_analysis/tests/test_acf_evidence.py` (new)

  ```python
  import numpy as np
  from scint_analysis.acf_evidence import compare_acf_evidence, lorentzian_1, two_screen_model

  def _synth_acf(rng, gammas=(0.4,), mods=(0.8,), c=0.0, n=120, dlag=0.05, sig=0.02):
      lags = dlag * np.arange(1, n + 1)
      acf = c + sum(m**2 / (1.0 + (lags / g) ** 2) for g, m in zip(gammas, mods))
      if len(gammas) == 2:
          acf += (mods[0]**2 / (1 + (lags/gammas[0])**2)) * (mods[1]**2 / (1 + (lags/gammas[1])**2))
      return lags, acf + rng.normal(0, sig, n), np.full(n, sig)

  def test_single_screen_prefers_m1():
      rng = np.random.default_rng(11)
      lags, acf, err = _synth_acf(rng)
      res = compare_acf_evidence(lags, acf, cov=np.diag(err**2),
                                 channel_width_mhz=0.05, band_width_mhz=6.0,
                                 nlive=300, dlogz=0.5, seed=11)
      assert res["dlnz"] < 3.0          # no strong two-screen preference
      assert res["m1"]["logz_err"] < 0.5

  def test_two_screen_prefers_m2():
      rng = np.random.default_rng(12)
      lags, acf, err = _synth_acf(rng, gammas=(0.15, 1.8), mods=(0.7, 0.6))
      res = compare_acf_evidence(lags, acf, cov=np.diag(err**2),
                                 channel_width_mhz=0.05, band_width_mhz=6.0,
                                 nlive=300, dlogz=0.5, seed=12)
      assert res["dlnz"] > 5.0
      g = res["m2"]["params_median"]
      assert g["gamma2"] > 3.0 * g["gamma1"]   # width ordering held
  ```

- [x] **Run it, watch it fail:**
  `pytest scintillation/scint_analysis/tests/test_acf_evidence.py -v`
  → FAIL (module `acf_evidence` not found)
- [x] **Implement the minimal engine**
  - File: `scintillation/scint_analysis/acf_evidence.py` (new)

  ```python
  """Nested-sampling evidence comparison for ACF component count (A1 trigger, limb i).

  Models are stated in the production HWHM convention (gamma = HWHM = Delta nu_d,
  analysis.py:299-304). Lag-0 is never included (analysis.py:283; the symmetric
  lag-0 point is a synthetic token). One-sided positive lags only, matching
  revalidation.py:323-332.
  """
  import numpy as np
  from dynesty import NestedSampler

  def lorentzian_1(lags, gamma, m2, c):
      return c + m2 / (1.0 + (lags / gamma) ** 2)

  def two_screen_model(lags, gamma1, m2_1, f, m2_2, c):
      # lor1 + lor2 + lor1*lor2 + c ; gamma2 = f*gamma1, f > 1 enforced by prior.
      # Cross term: two multiplicative screens (reference recipe, RECIPE.md §3g).
      l1 = m2_1 / (1.0 + (lags / gamma1) ** 2)
      l2 = m2_2 / (1.0 + (lags / (f * gamma1)) ** 2)
      return c + l1 + l2 + l1 * l2

  def _mvn_loglike_factory(lags, acf, cov):
      from scipy.linalg import cholesky, solve_triangular
      chol = cholesky(cov, lower=True)
      def loglike_for(model, unpack):
          def loglike(theta):
              r = acf - model(lags, *unpack(theta))
              z = solve_triangular(chol, r, lower=True)
              return -0.5 * float(z @ z)
          return loglike
      return loglike_for

  def _run(loglike, prior_transform, ndim, nlive, dlogz, seed):
      rng = np.random.default_rng(seed)
      s = NestedSampler(loglike, prior_transform, ndim, nlive=nlive, rstate=rng)
      s.run_nested(dlogz=dlogz, print_progress=False)
      r = s.results
      w = np.exp(r.logwt - r.logz[-1])
      med = {i: float(np.interp(0.5, np.cumsum(w) / w.sum(), r.samples[:, i]))
             for i in range(ndim)}
      return {"logz": float(r.logz[-1]), "logz_err": float(r.logzerr[-1]),
              "samples": r.samples, "weights": w, "median_by_dim": med}

  def compare_acf_evidence(lags, acf, cov, channel_width_mhz, band_width_mhz,
                           nlive=500, dlogz=0.1, seed=0, f_lo=3.0, f_hi=300.0):
      lags = np.asarray(lags, float); acf = np.asarray(acf, float)
      assert np.all(lags > 0), "one-sided positive lags, lag-0 excluded"
      g_lo, g_hi = 0.5 * channel_width_mhz, band_width_mhz / 4.0
      llf = _mvn_loglike_factory(lags, acf, np.asarray(cov, float))

      def pt1(u):  # gamma (log-U), m2 (U), c (U)
          return np.array([g_lo * (g_hi / g_lo) ** u[0],
                           0.01 + 1.99 * u[1], -0.5 + u[2]])
      def pt2(u):  # gamma1, m2_1, f (log-U), m2_2, c
          return np.array([g_lo * (g_hi / g_lo) ** u[0], 0.01 + 1.99 * u[1],
                           f_lo * (f_hi / f_lo) ** u[2], 0.01 + 1.99 * u[3],
                           -0.5 + u[4]])

      m1 = _run(llf(lorentzian_1, lambda t: t), pt1, 3, nlive, dlogz, seed)
      m2 = _run(llf(two_screen_model, lambda t: t), pt2, 5, nlive, dlogz, seed + 1)
      pm = m2["median_by_dim"]
      m2["params_median"] = {"gamma1": pm[0], "m2_1": pm[1], "f": pm[2],
                             "gamma2": pm[0] * pm[2], "m2_2": pm[3], "c": pm[4]}
      return {"m1": m1, "m2": m2, "dlnz": m2["logz"] - m1["logz"],
              "dlnz_err": float(np.hypot(m1["logz_err"], m2["logz_err"]))}
  ```

- [x] **Run it, watch it pass:**
  `pytest scintillation/scint_analysis/tests/test_acf_evidence.py -v` → 2 PASS
- [x] **Write the failing test** for the rail guard (second component pinned
  at prior edge ⇒ flagged)

  ```python
  def test_rail_flag_on_prior_edge():
      rng = np.random.default_rng(13)
      lags, acf, err = _synth_acf(rng)                      # single screen truth
      res = compare_acf_evidence(lags, acf, cov=np.diag(err**2),
                                 channel_width_mhz=0.05, band_width_mhz=6.0,
                                 nlive=300, dlogz=0.5, seed=13)
      assert "rail_flags" in res["m2"]
      assert set(res["m2"]["rail_flags"]) <= {"gamma1", "f", "m2_1", "m2_2", "c"}
  ```

- [x] **Implement** `_edge_mass_flags(samples, weights, bounds, edge_frac=0.05,
  mass_frac=0.30)` in `acf_evidence.py` using the ADR-0008 rail constants
  (EDGE_WIDTH_FRAC=0.05, EDGE_MASS_FRAC=0.30;
  plan-trust-reset-revalidation.md:497-500), attach as
  `m2["rail_flags"]`; posterior mass within 5% of a prior edge exceeding 30%
  flags that parameter.

  ```python
  def _edge_mass_flags(samples, weights, bounds, edge_frac=0.05, mass_frac=0.30):
      flags = []
      w = weights / weights.sum()
      for i, (name, lo, hi, log) in enumerate(bounds):
          x = np.log(samples[:, i]) if log else samples[:, i]
          l, h = (np.log(lo), np.log(hi)) if log else (lo, hi)
          edge = edge_frac * (h - l)
          if w[(x < l + edge) | (x > h - edge)].sum() > mass_frac:
              flags.append(name)
      return flags
  ```

- [x] **Run, watch pass; commit:**
  `git commit -m "feat(scint): dynesty 1-vs-2 component ACF evidence engine with rail flags"`

**Dependencies:** dynesty installed (`pip install -e .[nested]`).

**Verification:**
- [ ] `pytest scintillation/scint_analysis/tests/test_acf_evidence.py -v` → all PASS
- [ ] `pytest scintillation/scint_analysis/tests -q` — existing suite unaffected

### Phase 2: Correlated-lag ACF covariance (`acf_covariance.py`)

**Objective:** MC covariance of the ACF estimator under a matched
single-screen null, with shrinkage; replaces the diagonal in the Phase-1
likelihood.

**Tasks:**
- [x] **Write the failing test**
  - File: `scintillation/scint_analysis/tests/test_acf_covariance.py` (new)

  ```python
  import numpy as np
  from scint_analysis.acf_covariance import mc_acf_covariance

  def test_covariance_psd_and_diagonal_scale():
      cov, diag_ref = mc_acf_covariance(
          gamma_hwhm_mhz=0.4, mod_index=0.8, band_width_mhz=6.0,
          channel_width_mhz=0.05, snr=25.0, n_real=200, max_lag_bins=120,
          seed=42, return_diag_reference=True)
      assert cov.shape == (119, 119)                      # lags 1..119
      np.linalg.cholesky(cov)                             # PSD
      # MC diagonal within a factor 3 of the production quadrature diagonal
      ratio = np.sqrt(np.diag(cov)) / diag_ref
      assert np.median(ratio) < 3.0 and np.median(ratio) > 1.0 / 3.0

  def test_offdiagonal_correlation_positive_at_short_lag_separation():
      cov = mc_acf_covariance(gamma_hwhm_mhz=0.4, mod_index=0.8,
                              band_width_mhz=6.0, channel_width_mhz=0.05,
                              snr=25.0, n_real=200, max_lag_bins=120, seed=42)
      corr = cov / np.sqrt(np.outer(np.diag(cov), np.diag(cov)))
      k = 3   # neighbours within ~gamma are correlated
      assert np.median(np.diag(corr, k=k)) > 0.2
  ```

- [x] **Run, watch fail** (module missing).
- [x] **Implement** `mc_acf_covariance`
  - File: `scintillation/scint_analysis/acf_covariance.py` (new)

  ```python
  """MC correlated-lag covariance for the ACF estimator (A1 limb-i likelihood).

  Null-conditioned: realizations are single-screen with the *fitted* gamma-hat,
  matched band/channelization/SNR — correct conditioning for a false-escalation
  test. Realizations use direct Lorentzian-spectrum synthesis: a complex
  Gaussian field whose power spectrum is the FT of a Lorentzian gives an
  exponential-intensity spectrum with Lorentzian ACF of HWHM gamma (RECIPE
  convention) — the same statistical family the wave-optics engine produces at
  far greater cost; engine cross-check is in the Phase-3 campaign.
  """
  import numpy as np
  from .analysis import calculate_acf

  def _one_realization(rng, n_chan, gamma_bins, mod_index, snr):
      # Complex field with Lorentzian |E(nu)|^2 ACF: exponential filter on white field
      k = np.fft.rfftfreq(2 * n_chan)
      filt = np.exp(-np.abs(k) * 2 * np.pi * gamma_bins)   # FT of Lorentzian HWHM=gamma_bins
      field = np.fft.irfft((rng.normal(size=k.size) + 1j * rng.normal(size=k.size))
                           * np.sqrt(filt), n=2 * n_chan)[:n_chan]
      inten = field ** 2
      inten = 1.0 + mod_index * (inten - inten.mean()) / inten.std()
      noise = rng.normal(0.0, 1.0 / snr, n_chan)
      return np.clip(inten, 0, None) + noise

  def mc_acf_covariance(gamma_hwhm_mhz, mod_index, band_width_mhz,
                        channel_width_mhz, snr, n_real=500, max_lag_bins=120,
                        seed=0, shrink=None, return_diag_reference=False):
      rng = np.random.default_rng(seed)
      n_chan = int(round(band_width_mhz / channel_width_mhz))
      gamma_bins = gamma_hwhm_mhz / channel_width_mhz
      acfs, diag_ref = [], None
      for _ in range(n_real):
          spec = _one_realization(rng, n_chan, gamma_bins, mod_index, snr)
          acf_obj = calculate_acf(spec, channel_width_mhz,
                                  off_burst_spectrum_mean=0.0,
                                  max_lag_bins=max_lag_bins)
          pos = acf_obj.lags > 0
          acfs.append(acf_obj.acf[pos][:max_lag_bins - 1])
          if diag_ref is None:
              diag_ref = acf_obj.err[pos][:max_lag_bins - 1]
      A = np.array(acfs)
      cov = np.cov(A, rowvar=False)
      lam = shrink if shrink is not None else _ledoit_wolf_lambda(A)
      cov = (1 - lam) * cov + lam * np.diag(np.diag(cov))
      cov += 1e-12 * np.eye(cov.shape[0])
      return (cov, diag_ref) if return_diag_reference else cov

  def _ledoit_wolf_lambda(A):
      n, p = A.shape
      X = A - A.mean(0)
      S = X.T @ X / n
      var_s = ((X[:, :, None] * X[:, None, :] - S) ** 2).sum(0).sum() / n**2
      off = (S - np.diag(np.diag(S)))
      return float(np.clip(var_s / (off ** 2).sum(), 0.0, 1.0))
  ```

  (Exact attribute names for lags/values on the `ACF` container follow
  `core.py:412-428`; adjust `.acf`/`.err` accessors to the real API at
  implementation time — the test pins the behavior either way. If the
  `(X[:,:,None]*X[:,None,:])` Ledoit-Wolf accumulation is too memory-heavy at
  p≈120, n≈500, chunk over rows.)
- [x] **Run, watch pass.**
- [x] **Wire into Phase 1:** `compare_acf_evidence(..., cov=...)` already
  accepts the matrix; add a convenience
  `evidence_with_mc_covariance(acf_obj, snr, n_real, seed)` in
  `acf_evidence.py` that (a) fits the single-Lorentzian γ̂ via the existing
  `_fit_acf_models` lor entry (`analysis.py:685`), (b) builds the matched
  covariance, (c) runs the comparison. Test: end-to-end on a synthetic
  spectrum, asserting `dlnz < 5` for single-screen truth **with** the MC
  covariance in the few-scintle regime (the guard the diagonal case can't
  give):

  ```python
  def test_mc_covariance_suppresses_sample_variance_escalation():
      # few-scintle regime: 6 MHz band, gamma=1.0 -> ~6 scintles
      rng = np.random.default_rng(21)
      spec = _single_screen_spectrum(rng, gamma_mhz=1.0, band=6.0, dchan=0.05, snr=50)
      res = evidence_with_mc_covariance(spec, channel_width_mhz=0.05,
                                        snr=50.0, n_real=200, seed=21,
                                        nlive=300, dlogz=0.5)
      assert res["dlnz"] < 5.0
  ```

- [x] **Commit:** `git commit -m "feat(scint): MC correlated-lag ACF covariance with shrinkage; wired to evidence engine"`

**Dependencies:** Phase 1.

**Verification:**
- [ ] `pytest scintillation/scint_analysis/tests/test_acf_covariance.py -v` → PASS
- [ ] Cholesky succeeds on all grid cells exercised in tests (no LinAlgError).

### Phase 3: Single-screen injection generator through the production path

**Objective:** truth-known single- and two-screen dynamic spectra rendered to
per-subband ACFs via `calculate_acfs_for_subbands` (sim_gate pattern), in the
production HWHM convention and the P4c channelization contract.

**Tasks:**
- [x] **Write the failing test**
  - File: `simulation/tests/test_trigger_injections.py` (new)

  ```python
  import numpy as np
  from simulation.trigger_calibration import inject_single_screen, inject_two_screen

  def test_single_screen_recovers_injected_hwhm():
      out = inject_single_screen(dnu_hwhm_mhz=0.4, band_width_mhz=6.0,
                                 channel_width_mhz=0.05, snr=50.0,
                                 num_subbands=4, seed=7)
      assert out["acfs"] and all(a.lags[a.lags > 0].min() > 0 for a in out["acfs"])
      med = np.median([a.delta_nu_dc for a in out["acfs"]])
      # within the documented finite-scintle scatter; absolute bias tracked
      # against the P1.2 dnu-recovery calibration entry
      assert 0.15 < med < 1.0

  def test_two_screen_injection_exposes_both_scales():
      out = inject_two_screen(dnu1_hwhm_mhz=0.15, dnu2_hwhm_mhz=1.5,
                              m2_ratio=1.0, band_width_mhz=6.0,
                              channel_width_mhz=0.05, snr=50.0,
                              num_subbands=1, seed=8)
      assert out["truth"]["f"] == 10.0
  ```

- [x] **Run, watch fail.**
- [x] **Implement** `simulation/trigger_calibration.py`:
  `inject_single_screen` composes the Phase-2 `_one_realization` spectrum
  generator (fast path) with `calculate_acfs_for_subbands`
  (`analysis.py:509`) using a minimal config dict mirroring
  `test_acf_extraction.py:58`'s fixture; `inject_two_screen` multiplies two
  independent single-screen intensity fields (screen multiplicativity —
  same physics as the M2 cross term) before adding radiometer noise.
  Every output carries `{"truth": {...}, "acfs": [...], "convention":
  "HWHM", "channel_width_mhz": ..., "first_fit_lag": 1}`.
  Cross-check task: one cell (γ=0.4 MHz) regenerated with the wave-optics
  engine (`simulation/engine.py:84` `FRBScintillator`, single screen) and its
  ACF compared to the fast path (KS distance on ACF values < 0.15); marked
  `@pytest.mark.slow`.
- [x] **Run, watch pass; commit:**
  `git commit -m "feat(sim): truth-known single/two-screen ACF injections through production path"`

**Dependencies:** Phase 2 (shares the spectrum generator); P4c Phase-1
constants (first_fit_lag=1 DSA / 2 CHIME) — read from the P4c contract, both
exercised in tests.

**Verification:**
- [ ] `pytest simulation/tests/test_trigger_injections.py -v` → PASS
- [ ] `pytest -m slow simulation/tests/test_trigger_injections.py -v` (engine
      cross-check) → PASS on h17.

### Phase 4: Calibration campaign — null distribution, thresholds, power

**Objective:** the ΔlnZ operating-point table and power curves;
`reports/a1_trigger_calibration.json` + figures.

**Tasks:**
- [x] **Write the failing test** (campaign kernel, small-n smoke)
  - File: `simulation/tests/test_trigger_calibration_campaign.py` (new)

  ```python
  import numpy as np
  from simulation.trigger_calibration import null_dlnz_cell, threshold_table

  def test_null_cell_produces_finite_dlnz_sample():
      d = null_dlnz_cell(dnu_hwhm_mhz=0.4, snr=25.0, band_width_mhz=6.0,
                         channel_width_mhz=0.05, num_subbands=4,
                         n_real=8, seed=3, nlive=200, dlogz=1.0)
      assert len(d) == 8 and all(np.isfinite(x) for x in d)

  def test_threshold_table_monotone():
      fake = {("c1",): [-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 8.0]}
      t = threshold_table(fake, rates=(0.005, 0.01, 0.05))
      assert t[0.005] >= t[0.01] >= t[0.05]
  ```

- [x] **Run, watch fail; implement** `null_dlnz_cell` (n_real injections →
  per-burst summed ΔlnZ over subbands, each with its matched MC covariance)
  and `threshold_table` (envelope: max over cells of the (1−rate) quantile).
- [x] **Run, watch pass; commit.**
- [x] **Campaign driver** `simulation/scripts/run_a1_trigger_calibration.py`:
  grid Δν_d/Δchan ∈ {2, 5, 10, 30, 100} × S/N ∈ {10, 25, 50, 100} ×
  num_subbands ∈ {1, 4, 8}, n_real=200 per null cell (≈ 2.4×10⁴ nested runs;
  h17, joblib over cells, seeds = `seed0 + cell_index*1000 + real_index`);
  power grid f ∈ {3, 10, 30, 100} × m₂²/m₁² ∈ {0.25, 1.0} at the central
  noise cell, n_real=100. Prior-sensitivity rerun of the central cell with
  f-prior [1.5, 1000]. Output `reports/a1_trigger_calibration.json`:
  `{"thresholds": {...}, "null_quantiles_by_cell": ..., "power_curves": ...,
  "prior_sensitivity": ..., "seeds": ..., "git_sha": ..., "convention":
  "HWHM", "recommended_operating_point": {"rate": 0.01, "dlnz": <measured>}}`.
  Figures (matplotlib, saved to `reports/figures/`): null ΔlnZ distributions
  per cell (contact sheet), threshold-vs-rate, power vs f.
- [ ] **Run the campaign on h17**; exact command in the report:
  `python simulation/scripts/run_a1_trigger_calibration.py --n-real 200 --out reports/a1_trigger_calibration.json`
- [ ] **Commit** results + figures:
  `git commit -m "feat(sim): A1 trigger calibration campaign — dlnz operating point"`

**Dependencies:** Phases 1–3. h17 access for the full grid (local smoke uses
n_real=8, nlive=200).

**Verification:**
- [ ] `pytest simulation/tests/test_trigger_calibration_campaign.py -v` → PASS
- [ ] `python -m json.tool reports/a1_trigger_calibration.json` parses; the
      `recommended_operating_point.dlnz` field is finite and > 0.
- [ ] Contact-sheet figures exist under `reports/figures/`.

### Phase 5: Trigger verdict wiring + ADR-0008 calibration entry

**Objective:** one function returning the escalation verdict; calibration
recorded in ADR-0008.

**Tasks:**
- [ ] **Write the failing test**
  - File: `scintillation/scint_analysis/tests/test_escalation_trigger.py` (new)

  ```python
  from scint_analysis.acf_evidence import escalation_trigger_verdict

  CAL = {"dlnz_threshold": 6.2, "rate": 0.01}   # loaded from reports JSON in prod

  def test_escalates_on_dlnz():
      v = escalation_trigger_verdict(dlnz=9.0, rail_flags=[], ppc_pvalues={"lag1_acf": 0.5},
                                     calibration=CAL)
      assert v["escalate"] and v["reasons"] == ["dlnz"]

  def test_rail_is_model_family_rejection_not_detection():
      v = escalation_trigger_verdict(dlnz=9.0, rail_flags=["f"], ppc_pvalues={"lag1_acf": 0.5},
                                     calibration=CAL)
      assert not v["escalate"] and v["verdict"] == "model_family_rejection"

  def test_ppc_limb_escalates_independently():
      v = escalation_trigger_verdict(dlnz=1.0, rail_flags=[], ppc_pvalues={"lag1_acf": 0.01},
                                     calibration=CAL)
      assert v["escalate"] and v["reasons"] == ["ppc_lag1_acf"]

  def test_non_detection_is_censored_not_single_screen():
      v = escalation_trigger_verdict(dlnz=1.0, rail_flags=[], ppc_pvalues={"lag1_acf": 0.5},
                                     calibration=CAL)
      assert not v["escalate"] and v["verdict"] == "no_escalation_censored"
  ```

- [ ] **Run, watch fail; implement** `escalation_trigger_verdict` in
  `acf_evidence.py`:

  ```python
  def escalation_trigger_verdict(dlnz, rail_flags, ppc_pvalues, calibration):
      reasons = []
      if rail_flags:
          return {"escalate": False, "verdict": "model_family_rejection",
                  "reasons": [], "rail_flags": list(rail_flags)}
      if dlnz >= calibration["dlnz_threshold"]:
          reasons.append("dlnz")
      p = ppc_pvalues.get("lag1_acf")
      if p is not None and not (0.05 <= p <= 0.95):
          reasons.append("ppc_lag1_acf")
      if reasons:
          return {"escalate": True, "verdict": "escalate", "reasons": reasons}
      return {"escalate": False, "verdict": "no_escalation_censored", "reasons": []}
  ```

  (PPC band [0.05, 0.95] = rung-iv contract, plan-trust-reset-revalidation.md
  P1.3; `lag1_acf` is the registered statistic named as two-screen-sensitive.)
- [ ] **Run, watch pass; commit.**
- [ ] **ADR-0008 calibration entry**: append to
  `docs/adr/0008-re-trust-validation-contract.md` (once V1 P1.5 has authored
  it; if not yet merged, this task blocks on that PR and says so in the PR
  description) a "Calibration entries" row: A1 trigger ΔlnZ operating point,
  the JSON path, git SHA, grid, rate, and the freya-CHIME control result.
- [ ] **Real-data validation runs (diagnostic-only):** casey DSA (4 equal-S/N
  subbands — the ACF-review exemplar) and freya-CHIME (instrumental control;
  P4c Phase-6 artifact gates + `off_pulse_null_verdict`,
  `chime_artifact_guards.py:177`, must run first). Required outcomes: casey
  produces a finite verdict object; freya-CHIME does **not** escalate
  (`escalate == False` or gates withhold measurement status). Both stamped
  `diagnostic_only` in outputs.
- [ ] **Commit; open the PR chain** to `pin/faber2026`.

**Dependencies:** Phases 1–4; ADR-0008 existence for the entry (V1 P1.5);
P4c Phase 6 for the freya-CHIME gate path.

**Verification:**
- [ ] `pytest scintillation/scint_analysis/tests/test_escalation_trigger.py -v` → PASS
- [ ] freya-CHIME control: verdict JSON shows no escalation.
- [ ] `gh pr list --head a1/trigger-calibration` shows the PR(s) targeting `pin/faber2026`.

### Phase 6: Owner sign-off packet (manuscript repo)

**Objective:** the one-figure-one-table decision packet; A1 close-out edits
staged for the owner.

**Tasks:**
- [ ] Copy the operating-point figure + threshold table into
  `docs/rse/specs/report-a1-trigger-calibration.md` (Faber2026 repo) with:
  recommended rate 1%, measured ΔlnZ threshold, power at f=10 / m₂²=m₁²,
  prior-sensitivity delta, freya-CHIME control result, casey validation
  result, and the exact reproduction command + git SHA.
- [ ] Update the readiness board owner-view "Needs you" item to "Sign off A1
  ΔlnZ operating point — packet ready"; rebake + deploy
  (`python3 scripts/render_journal_panel.py`, `bash scripts/deploy-board.sh`).
- [ ] Journal the delivery (`scripts/journal-append.sh claude-code A done ...`).
- [ ] On owner sign-off (their action): amend
  plan-circulation-readiness.md A1 status to closed and record the chosen
  rate; A2/A3 then consume the trigger as specified.

**Dependencies:** Phase 5 merged.

**Verification:**
- [ ] `report-a1-trigger-calibration.md` exists and names a finite ΔlnZ.
- [ ] Board shows the sign-off item; journal entry present.

## Success Criteria

### Automated Verification

- [ ] `pytest scintillation/scint_analysis/tests/test_acf_evidence.py scintillation/scint_analysis/tests/test_acf_covariance.py scintillation/scint_analysis/tests/test_escalation_trigger.py simulation/tests/test_trigger_injections.py simulation/tests/test_trigger_calibration_campaign.py -v` — all PASS
- [ ] Full suite unbroken: `pytest -q` (or `nox`) in dsa110-FLITS
- [ ] `python -m json.tool reports/a1_trigger_calibration.json` parses;
      `recommended_operating_point.dlnz` finite
- [ ] `git -C ~/Developer/repos/github.com/jakobtfaber/dsa110-FLITS merge-base --is-ancestor origin/pin/faber2026 a1/trigger-calibration` (branch off the pin lane)

### Manual Verification

- [ ] Null ΔlnZ contact sheet looks unimodal per cell, no pathological tails
      (visual-vetting rule: inspect the figures, not just quantiles)
- [ ] freya-CHIME instrumental control does not escalate
- [ ] casey-DSA verdict object is physically sensible (γ̂ within the
      ACF-review ballpark)
- [ ] Owner: pick the false-escalation rate and sign off A1

### Reproducibility & Correctness (research code)

- [ ] Seeds explicit per cell (`seed0 + cell_index*1000 + real_index`); grid,
      priors, git SHA, and exact command embedded in the JSON report
- [ ] Numerical correctness anchors: two-screen synthetic with f=10 gives
      ΔlnZ > 5 (Phase 1 test); MC covariance diagonal within ×3 of the
      production quadrature diagonal (Phase 2 test); injected HWHM recovered
      within documented finite-scintle scatter (Phase 3 test), cross-checked
      against the P1.2 Δν-recovery calibration entry (known ratio ≈ 0.29
      issue — if unresolved by V1 at campaign time, the campaign states its
      truth grid in *estimator* units, which cancels the definitional offset
      inside the null/power comparison)
- [ ] Campaign re-run of one cell on a clean h17 env reproduces the cell
      threshold within the quoted MC error

## Testing Strategy

**Unit Test Coverage (summary, written in-phase):** evidence engine truth
recovery both directions; rail-edge flagging; covariance PSD/shrinkage/scale;
injection truth-carrying and convention stamping; threshold monotonicity;
verdict logic all four branches.

**Integration Tests:**
- [ ] `evidence_with_mc_covariance` end-to-end on synthetic spectra (Phase 2)
- [ ] slow-marked wave-optics vs fast-path ACF consistency (Phase 3)
- [ ] small-n campaign smoke producing a parseable JSON (Phase 4)

**Manual Testing:**
- [ ] casey-DSA and freya-CHIME diagnostic runs (Phase 5)
- [ ] Figure inspection per the visual-vetting rule

**Test Data Requirements:** none external — all synthetic; real-data runs use
the existing casey/freya products already on disk (diagnostic-only).

## Migration Strategy

Additive: new modules + one new verdict entry point. Nothing existing changes
behavior; `compare_lorentzian_components` (BIC+F-test) remains untouched as
the cross-check. **Rollback:** revert the PR chain; no data products depend on
it until A3 consumes the verdict. **Backward Compatibility:** full — no
existing API modified.

## Risk Assessment

1. **Risk:** MC covariance ill-conditioned in few-scintle cells (p ≈ 120 lags,
   strong correlation).
   - **Likelihood:** Medium — **Impact:** Medium
   - **Mitigation:** Ledoit-Wolf shrinkage + jitter (Phase 2); if Cholesky
     still fails, truncate `max_lag_bins` to ≈ 4γ̂/Δchan (fit range already
     behaves this way in `_fit_acf_models`); dynamic-spectrum-domain
     likelihood is the recorded fallback (out-of-scope note).
2. **Risk:** The known Δν-recovery definitional bias (ratio ≈ 0.29,
   V1 P1.2) contaminates the truth grid.
   - **Likelihood:** Medium — **Impact:** Medium
   - **Mitigation:** grid stated in estimator units (γ̂ from the production
     path), so null and power distributions are internally consistent; the
     absolute mapping is deferred to the P1.2 calibration entry and
     cross-referenced, not duplicated.
3. **Risk:** Instrumental ACF features (35.19 kHz CHIME comb) escalate
   spuriously on real data.
   - **Likelihood:** Medium — **Impact:** High
   - **Mitigation:** trigger runs only behind the P4c Phase-6
     measurement-status gates + `harmonic_lag_mask`; freya-CHIME control is a
     required Phase-5 outcome.
4. **Risk:** Campaign compute exceeds interactive patience (~2.4×10⁴ nested
   runs).
   - **Likelihood:** High — **Impact:** Low
   - **Mitigation:** h17 batch (campaign convention of the γ-campaign plan);
     per-cell checkpointing in the driver; smoke path (n_real=8, nlive=200)
     keeps CI fast.
5. **Risk:** ADR-0008 not yet authored when Phase 5 lands.
   - **Likelihood:** Medium — **Impact:** Low
   - **Mitigation:** the calibration entry task explicitly blocks on V1 P1.5
     and says so in the PR; the JSON report is self-contained either way.

## Edge Cases and Error Handling

1. **Case:** All subbands of a burst fail measurement-status gates.
   - **Expected Behavior:** no verdict; burst reported `censored` (A1: a
     non-detection never claims single-screen).
   - **Implementation:** verdict wiring only consumes gate-passing ACFs
     (Phase 5).
2. **Case:** dynesty fails to converge (dlogz plateau) on a pathological ACF.
   - **Expected Behavior:** cell/burst flagged `evidence_failed`, excluded
     from thresholds, counted in the report.
   - **Implementation:** wrap `run_nested` in try/except + iteration cap in
     `_run`; failures logged with seed for replay.
3. **Case:** Second component converges to f → f_lo (same-scale degeneracy).
   - **Expected Behavior:** `rail_flags` includes `f`; verdict =
     `model_family_rejection` (same-screen ambiguity belongs to limb (ii)).
   - **Implementation:** `_edge_mass_flags` (Phase 1) + verdict logic
     (Phase 5).
4. **Error:** Covariance Cholesky failure at likelihood time.
   - **Handling:** raise `ValueError` naming the cell parameters; campaign
     driver catches, applies the lag-truncation fallback, and records which
     path produced the cell.

## Performance Considerations

- **Expected Load:** ≈ 2.4×10⁴ null + 8×10² power nested runs, each 3–5
  params, ~10² data points → seconds each; tens of h17 core-hours total.
- **Performance Targets:** full campaign < 12 h wall on h17 with joblib over
  cells; local smoke < 5 min.
- **Optimization Strategy:** covariance computed once per cell (not per
  realization); `nlive=500` production / 200 smoke.

## Documentation Updates

- [ ] Module docstrings in `acf_evidence.py`, `acf_covariance.py`,
      `trigger_calibration.py` (convention + provenance citations as written
      in the phase tasks)
- [ ] ADR-0008 calibration entry (Phase 5)
- [ ] `docs/rse/specs/report-a1-trigger-calibration.md` (Phase 6)
- [ ] Readiness board owner-view + journal (Phase 6)

## Timeline Estimate

- Phase 1–2: one focused session (evidence + covariance, all synthetic)
- Phase 3: half session
- Phase 4: half session code + overnight h17 campaign
- Phase 5–6: one session including real-data controls and the packet
- Total: ~3 working sessions + one h17 batch window

**Note:** estimates only; the campaign grid can shrink (drop num_subbands=8)
if the batch window is tight.

## Open Questions

*(none — priors, grid, rates, model forms, and fallbacks are fixed above;
the only deferred choice, the false-escalation rate, is by design the owner's
sign-off input, with 1% as the recommended default)*

---

## References

**Research Documents:**
- [Plan: Circulation readiness](plan-circulation-readiness.md) — A1 charter (`:38-76`), dependency spine (`:236`)
- [Plan: Trust-reset revalidation](plan-trust-reset-revalidation.md) — V1 contract rungs (`:707-728`), P1.2 recovery criterion (`:548-585`), P1.3 PPC (`:587-688`), rail constants (`:497-500`)
- [Plan: CHIME scint recipe parity](plan-chime-scint-recipe-parity.md) — lag contract (`:135-139`), HWHM fields (`:336-364`), branch mechanics (`:228-229`)
- [Plan: CHIME scint γ campaign](plan-chime-scint-gamma-campaign.md) — phase structure, uniform-methods rule

**Files Analyzed (dsa110-FLITS, checkout `pipeline/`):**
- `scintillation/scint_analysis/analysis.py` (ACF, models, fit engine, subband driver)
- `scintillation/scint_analysis/revalidation.py` (n-Lorentzian, BIC+F selector)
- `scintillation/scint_analysis/freya_scintillation.py` (Nimmo-style path)
- `scintillation/scint_analysis/chime_artifact_guards.py` (instrumental gates)
- `scattering/scat_analysis/burstfit_nested.py` (dynesty pattern)
- `simulation/{engine,wave_optics,recovery_campaign,sim_fit_bridge,noise}.py`
- `pyproject.toml` (dynesty extra, pytest config)
- Rescue capture (branch `scint/reference-arc-rescue`): `reference_arc/RECIPE.md`, `GAP_ANALYSIS.md`, `arc_live/.../analysis-Copy1.py` (two-screen form `:51-55`, width ordering `:574-575`)

**External Documentation:**
- dynesty NestedSampler API (evidence + logzerr extraction)
- Conventional Bayes-factor interpretation scales (context only for ΔlnZ
  magnitudes; the operating point is injection-calibrated, not scale-quoted)

---

## Review History

### Version 1.0 — 2026-07-13
- Initial plan created from the two-agent research sweep (FLITS code surface + spec constraints), per the 2026-07-13 owner direction on the revised A1 trigger.

### Version 1.2 — 2026-07-13 (Phases 3–4 implemented; campaign launched)
- Commits `4854569` (injections + campaign kernel/driver), `e077611` (grid
  fix). Tests: injections 2/2, campaign kernel 3/3 (incl. slow smoke);
  driver `--smoke` end-to-end locally and on h17; parallel == sequential by
  seed.
- **Deviation 3:** tests live in root `tests/` (repo convention;
  `simulation/tests/` does not exist).
- **Deviation 4:** calibration band scales with subband count
  (`num_subbands × 120` channels) — the plan's fixed 6 MHz band starved the
  8-subband arm below `calculate_acf`'s 20-channel minimum; first h17 launch
  failed that whole arm instantly (200/200 `evidence_failed`, caught by the
  failure accounting) and was killed, fixed, relaunched at `e077611`.
- Full grid (60 null + 8 power cells, n=200/100) running on h17
  (`~/a1-trigger-calibration`, conda env `flits-a1-312`, 36 workers, nohup;
  log `/tmp/a1_campaign.log`; per-cell checkpoints under
  `reports/a1_trigger_calibration.cells/`).
- Watch item for the analysis: one smoke null realization hit ΔlnZ ≈ +24 —
  if the full null tail is that heavy, the suspect is covariance
  conditioning (MC covariance synthesizes plain 1-D spectra; injections go
  through the full dynamic-spectrum render with time-integrated noise).
  The n=200 null distributions decide.

### Version 1.1 — 2026-07-13 (Phases 1–2 implemented)
- Branch `a1/trigger-calibration` off `origin/pin/faber2026`, worktree
  `~/Developer/scratch/worktrees/flits-a1-trigger`. Commits `37a98cf`
  (Phase 1), `9872147` (Phase 2), pushed.
- Verification: evidence tests 4/4 (28 s), covariance tests 3/3 (9 s under
  rwalk), scint-suite regression 145 passed / 1 pre-existing skip.
- **Deviation 1:** `_run_nested` uses `sample="rwalk"` + a `maxcall` cap with
  a RuntimeError `evidence_failed` path. dynesty's default uniform-ellipsoid
  proposal stalled (>15 min, reproducible by seed) on the M2 likelihood
  plateau (large γ₁ × large f ⇒ near-constant model); random walks degrade
  gracefully there. This implements Edge Case 2 earlier than planned.
- **Deviation 2:** the planned `test_forced_rail_is_flagged` (truth-γ outside
  the prior, full nested run) was replaced by a direct deterministic unit test
  of `_edge_mass_flags` (edge-pile fires, interior stays quiet): the
  out-of-prior misfit gives a ~10⁵ log-likelihood dynamic range and
  correspondingly long nested runs — wrong cost for CI; the integration path
  is still covered by `test_rail_flag_field_present_and_valid`.
- Phase-2 realization physics: exponential-PBF field synthesis (HWHM =
  1/(2πτ_s), C₁ = 1) rather than the plan's exponential-filter sketch — the
  physical single-screen case, same statistical family.
