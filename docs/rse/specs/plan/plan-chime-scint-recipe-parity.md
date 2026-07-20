# Implementation Plan: CHIME scintillation recipe-parity (P4c)

---
**Date:** 2026-07-12
**Author:** AI Assistant
**Status:** Draft
**Related Documents:**
- [Campaign plan: CHIME scintillation γ + modulation-index (lane B)](../plan/plan-chime-scint-gamma-campaign.md)
- Rescue evidence (dsa110-FLITS worktree `flits-scint-rescue`, branch `scint/reference-arc-rescue`):
  `scintillation/scint_analysis/reference_arc/RECIPE.md`, `GAP_ANALYSIS.md`, `ORIGIN.md`

---

## Overview

This plan implements phase **P4c** of the CHIME scintillation campaign: porting the
rescued CANFAR-era Nimmo-lineage scintillation recipe into the current
`scint_analysis/` pipeline so that the 12 up-channelized CHIME products yield
recipe-faithful scintillation-bandwidth (γ), frequency-scaling-index (α), and
modulation-index (m) numbers, and so the four legacy bursts (chromatica, freya,
hamilton, wilhelm) can be cross-validated against the rescued worked values.

The work executes the ranked deltas **P0-1 … P1-7** from
`reference_arc/GAP_ANALYSIS.md §3`, in the order of that document's *recommended
acceptance sequence* (ACF-level parity first, then cleaning mode, then regression
tests, then the science estimators, then the CHIME gates). It is informed by
`reference_arc/RECIPE.md` (the reconstructed sequence + 9 flagged ambiguities) and
the `arc_live/` Nimmo capture (canonical pipeline + the exact runtime fit functions
that resolve RECIPE ambiguity 5).

The central design fact that makes this tractable: the current
`revalidation.py` module **already** contains a clean, Nimmo-faithful ACF backbone —
`_mean_normalized_acf` / `_acf_masked` with a `first_lag` contract, the
`(xmean − offspec_mean)²` denominator, and the HWHM (γ = Δν_d) Lorentzian
(`revalidation.py:74-179`). The pipeline's *main* path (`analysis.calculate_acf`,
`analysis.py:234-333`) diverges from it (starts at lag 1, injects a synthetic
`ACF(0)=1` with a `1e-9` error). Parity is therefore mostly a matter of making the
main path reuse the reference backbone's lag/denominator contract, not of writing a
new ACF from scratch.

**Goal:** The modern pipeline is the single default estimator producing the science
numbers uniformly for all 12 bursts; a selectable `canfar_reference` mode reproduces
the rescued recipe closely enough to cross-validate the 4 legacy bursts; every fit
carries an explicit HWHM/FWHM label and passes the Levels 1-3 fit-validation
contract; and a regression test suite pins ACF values, retained lags, and legacy γ
against rescued reference values.

**Motivation:** `DATA_PROVENANCE.md §7c` requires the CHIME preprocessing provenance
to be reconstructed before any historical CHIME product is promoted from "retired
context" to a measurement. `GAP_ANALYSIS.md` shows the current pipeline cannot
reproduce the archived CANFAR numbers today — chiefly because of the ACF lag
convention (reference starts at CHIME fine-channel lag 2; the main path starts at lag
1) and the absence of a named recipe-faithful cleaning mode. This plan closes those
gaps with regression evidence.

## Current State Analysis

**Existing Implementation (current pipeline, worktree `flits-scint-rescue`):**
- `scint_analysis/revalidation.py:74-179` — the Nimmo/Pleunis ACF backbone:
  `_acf_masked` (mask-aware pairwise ACF), `_mean_normalized_acf` (two-sided,
  `first_lag` contract, lag-0 always dropped, optional `offspec_mean` denominator),
  `revalidate_dnu` (single-screen HWHM γ fit). **This is the reference-parity anchor.**
- `scint_analysis/analysis.py:234-333` — `calculate_acf`, the *main* per-sub-band ACF.
  Uses `lags = np.arange(1, max_lag_bins)` (line 283: **first lag = 1**), symmetrizes
  by inserting a **synthetic `1.0` at lag 0 with error `1e-9`** (lines 320, 325).
- `scint_analysis/analysis.py:509-648` — `calculate_acfs_for_subbands`: equal-frequency
  or equal-S/N sub-band split, per-sub-band `calculate_acf`.
- `scint_analysis/analysis.py:685-777` — `_fit_acf_models`: excludes lag 0 in the 1D fit
  (`m = (|lags|≤range) & (lags != 0)`, line 700), optional harmonic-lag mask
  (`harmonic_lag_mask`, lines 664-682), model registry tag `"lor"`, prefix `l_`,
  params `l_gamma`/`l_m` (`_baseline_registry`, lines 113-149). Fit-result dict keys are
  `fit_lor` / `fit_sn_lor` / `fit_tpl_lor` / `fit_sn_tpl_lor`.
- `scint_analysis/analysis.py:1489-1753` — `analyze_scintillation_from_acfs`: per-sub-band
  fit → best-model select → per-sub-band `(freq, bw=γ, mod=m)` → **log-space ODR power
  law `log10(Δν)=α·log10(ν)+log10(c)`, `beta0=[4.0,0.0]`** (lines 1697-1718), with an
  unweighted-ODR fallback (line 1694). `bw` is the fitted Lorentzian `l_gamma` (HWHM),
  reported directly — matching the notebooks.
- `scint_analysis/analysis.py:1830-1974` — `analyze_intra_pulse_scintillation`: **broken.**
  Default `intra_pulse_fit_model = "lorentzian_component"` (line 1862); the guard
  `if "1c" not in model_to_fit: return []` (line 1868) aborts immediately; and the
  extractor reads `l_gamma1`/`l_m1` (lines 1940, 1952) which the single-Lorentzian
  registry does not emit (it emits `l_gamma`/`l_m`).
- `scint_analysis/fitting_2d.py:306` — the 2D joint fitter's mask is
  `np.abs(lags) <= self.fit_range_mhz` — it **does not exclude lag 0**, so the injected
  `ACF(0)=1` with `1e-9` error dominates the global weighted fit.
- `scint_analysis/core.py:260-360` — `mask_rfi`: iterative frequency-domain σ-clip
  (5 passes), optional time-domain robust-z flagging; masks (never fills) missing data.
- `scint_analysis/freya_scintillation.py:425-490` — `normalize_bandpass`: per-fine-channel
  off-pulse-**mean** flat-field (divides out the PFB scallop). Does **not** divide by the
  off-pulse RMS (the reference per-channel S/N normalization does).
- `scint_analysis/chime_artifact_guards.py:123-417` — `chime_provenance_status`,
  `off_pulse_null_verdict`, `low_lag_stability_verdict`, `finalize_measurement_status`:
  all implemented and unit-tested, but **`pipeline.run()` never calls them**.
- `scint_analysis/pipeline.py:203-364` — `ScintillationAnalysis.run()`: prepare → windows →
  bandpass flat-field → baseline → noise → `calculate_acfs_for_subbands` → intra-pulse →
  `analyze_scintillation_from_acfs` → 2D fit. No CHIME gate call; `final_results` carries
  no provenance/verdict/fit-lag-policy fields.
- `scint_analysis/run_analysis.py:83-108` — writes `final_results` JSON; calls
  `plot_analysis_overview` only; **never calls `plot_intra_pulse_evolution`**
  (`plotting.py:443`).

**Rescued reference (read-only evidence, `reference_arc/`):**
- `arc_live/old_scattering_scintillation/utilities/kenzie_funcs.py:446` —
  `lorentz(x, gamma, m, c) = m²/(1+(x/γ)²)+c`; `scint_funcs.py:269-283` — `lorentz_w_c`,
  bare `lorentz`, `doublelorentz_w_c`. **γ is the HWHM; the notebooks report Δν_d = γ
  directly** (RECIPE §3g).
- `code/analysis-Copy1.py:844-891` — the *intended* γ(ν) estimator: log-space ODR
  `beta0=[4.0,0.0]` with the α∈{4,3,1} physical interpretation (RECIPE §3h). No captured
  notebook ever fits α to real data (RECIPE ambiguity 2), so this ODR is the primary
  method and the notebook's unweighted log-log regression is only a cross-check.
- `arc_live/old_scattering_scintillation/zach_acf_codetections_fftsize64_downfreq1.npz` —
  a ready-made ACF fixture: keys `onburstacf` (6550,), `sub_acfs` (6, 3274),
  `sub_fcents` (6,), `sub_lags` (6, 3274), `sub_acfs_peak` (6, 3274). Executed-notebook
  ACF arrays for 6 equal-S/N sub-bands.

**Current Behavior:** the pipeline produces γ, α, and per-sub-band m(ν) for CHIME
products, but with a lag-1-start ACF and a synthetic center that neither matches the
reference recipe nor is gated by the CHIME artifact checks; m(t) is unavailable
(intra-pulse path dead); results are unlabeled as to HWHM vs FWHM convention.

**Current Limitations:**
- ACF lag convention and synthetic-center injection differ from the reference recipe →
  cannot claim historical reproduction.
- No named `canfar_reference` cleaning mode → the 4 legacy bursts cannot be
  cross-validated against the rescued numbers.
- No regression tests tying pipeline output to rescued reference values.
- HWHM/FWHM convention is implicit (RECIPE ambiguity 1: a factor-of-2 hazard).
- m(t) is unavailable; the direct `std/mean` time-chunk statistic is absent entirely.
- CHIME artifact gates exist but are not enforced → a CHIME JSON is a "measurement"
  merely because optimization succeeded.

## Desired End State

**New Behavior:**
- `calculate_acf` (and the sub-band and 2D paths) honor an explicit
  `acf.first_fit_lag` contract — `2` for CHIME up-channelized products, `1` for DSA —
  and no path feeds an invented `ACF(0)=1`/`1e-9` center into a fit.
- A selectable `preprocessing.mode: canfar_reference` cleaning path exists alongside the
  modern default, reproducing the reference LTE mask + exact on/off windows + per-channel
  off-mean subtraction and off-RMS division + reference RFI thresholds.
- Every fit result carries `gamma_hwhm_mhz`, `fwhm_mhz = 2*gamma`, and
  `reported_dnu_definition = "HWHM"`; historical-reproduction outputs report Δν_d = γ.
- γ(ν) is reported three labeled ways: `odr_logspace` (primary), `loglog_unweighted`
  (notebook cross-check), and `joint_2d` (modern).
- m(ν) (fitted √amplitude per sub-band) and m(t) (both the ACF-fitted γ/m per time slice
  **and** the direct `std/mean` time-chunk statistic) are produced and plotted.
- `pipeline.run()` computes the off-pulse ACF null and low-lag excision refits, calls
  `finalize_measurement_status`, and embeds the verdict + windows + fit-lag policy in
  `final_results`.
- A regression suite (`test_reference_arc_parity.py`) pins ACF values, retained lags, and
  legacy γ against rescued reference values, each labeled executed-notebook vs recomputed.

**Success Looks Like:**
- `pytest scintillation/scint_analysis/tests/test_reference_arc_parity.py` passes.
- A CHIME `final_results` JSON contains `measurement_status`, `reported_dnu_definition`,
  `gamma_scaling` with three named estimators, `modulation_index_time`, and `fit_lag_policy`.
- The 4-burst legacy cross-check table (γ_pipeline vs γ_reference, HWHM) is generated and
  reviewed; the freya CHIME case correctly downgrades to `diagnostic_only` under the gates.

## What We're NOT Doing

- [ ] **Re-up-channelizing baseband.** The 12 `<nick>_chime.npz` products already exist
      (`DATA_PROVENANCE.md §2a`); this plan consumes them, never regenerates the voltage→
      fine-channel transform.
- [ ] **Touching the DM-campaign lane** (`dispersion/`, `analysis/chime_dm/`).
- [ ] **Changing DSA-band defaults.** DSA configs keep `first_fit_lag: 1` and their existing
      cleaning; only the CHIME path and the opt-in `canfar_reference` mode change behavior.
- [ ] **Bumping the Faber2026 `pipeline` submodule pin.** That is a separate reviewed step
      (memory: pipeline pin lives off FLITS main; PR fixes to the `pin/faber2026` branch).
- [ ] **Adopting the v3 FWHM convention as the reported width.** HWHM (γ) is the reported
      Δν_d; `fwhm_mhz` is emitted only as a labeled convenience field (RECIPE ambiguity 1).
- [ ] **Promoting isha/hamilton/johndoeII** beyond their upper-bound/single-block status
      (`DATA_PROVENANCE.md §7c`).

**Rationale:** these boundaries keep the diff focused on the recipe-parity deltas, avoid
colliding with the DM lane and the pin-bump review, and preserve the campaign decision
that the modern pipeline is the uniform default.

## Implementation Approach

**Technical Strategy:** Port the reference recipe *behavior* into the existing modules
with minimal, config-gated diffs (repo "ponytail" style), reusing the already-correct
`revalidation` ACF backbone as the single source of truth for the lag/denominator
contract so the main and reference paths cannot drift. Every new estimator or cleaning
mode is opt-in; the modern default path is unchanged except for the lag contract and the
removal of the synthetic-center fit input. Each unit of work is test-first against a
rescued reference value or an analytic invariant.

**Key Architectural Decisions:**
1. **Decision:** Reuse `revalidation._mean_normalized_acf` as the ACF contract for the
   main path rather than editing `calculate_acf`'s lag math in two places.
   - **Rationale:** GAP P0-1 explicitly warns the two paths "cannot drift"; the reference
     backbone already implements `first_lag`, the `(xmean−offspec_mean)²` denominator, and
     lag-0 exclusion correctly and is unit-tested (`test_revalidation.py`).
   - **Trade-offs:** `calculate_acf` also produces per-lag statistical + finite-scintle
     errors that `_mean_normalized_acf` does not; so `calculate_acf` keeps its error
     machinery but takes its *retained lags* from the shared `first_fit_lag` contract and
     stops injecting the synthetic center.
   - **Alternatives considered:** duplicating a `first_lag` branch inside `calculate_acf` —
     rejected (the drift GAP warns about).
2. **Decision:** `canfar_reference` is a preprocessing *mode* selected by
   `analysis.preprocessing.mode`, not a fork of the pipeline.
   - **Rationale:** GAP P0-2 requires the modern mask-only path to remain the default and
     the reference path to be selectable and emit inspectable intermediates.
   - **Trade-offs:** a mode switch adds a branch in `core.mask_rfi`/`freya_scintillation`;
     acceptable vs a parallel module.
3. **Decision:** HWHM stays the reported Δν_d; FWHM is a derived labeled field.
   - **Rationale:** the notebooks (the numbers we cross-check against) report γ = HWHM;
     v3's `2γ` is the single largest consistency hazard (RECIPE ambiguity 1).

**Patterns to Follow:**
- Fit-validation contract Levels 1-3 on every fit — see `revalidation.compare_lorentzian_components`
  (`revalidation.py:277-426`) for the BIC + nested-F-test pattern already in use.
- Figure outputs registered via `tools/figure_manifest.write_manifest(out_dir, [(png, expectation), …])`
  so the Stop-hook figure-review gate applies (`tools/figure_manifest.py:16`; CLAUDE.md §Figure-review).
- Config-gated preprocessing that shares gating between the pipeline and the freya CLI path —
  see `pipeline._apply_bandpass_normalization` (`pipeline.py:176`).
- Test style: seeded synthetic spectra + rescued fixtures, repo-root `sys.path` insert —
  see `tests/test_revalidation.py:1-55`.

**Environment & run contract (all phases):**
- Conda env `flits` (`~/.conda/envs/flits`). Repo root is the worktree
  `~/Developer/scratch/worktrees/flits-scint-rescue` (pyproject `pythonpath = ["."]`).
- Run tests from repo root: `conda run -n flits python -m pytest <path> -v`.
  PATH-safe variant if base Anaconda shadows the env:
  `env -i HOME="$HOME" PATH="/opt/anaconda3/bin:/opt/homebrew/bin:/usr/bin:/bin" \
   /opt/anaconda3/bin/conda run -n flits python -m pytest <path> -v`.
- Branch `scint/reference-arc-rescue` (off `pin/faber2026`, confirmed ancestor of HEAD).
  Commit per task; PR to `pin/faber2026` at the end (never bump the Faber2026 gitlink).

## Implementation Phases

### Phase 1 — ACF-level parity: lag contract (P0-1) + HWHM/FWHM convention (P0-4)

**Objective:** Make the main ACF path honor an explicit `first_fit_lag` contract
(2 for CHIME, 1 for DSA), stop feeding a synthetic `ACF(0)=1`/`1e-9` center into any
fit, and label every reported width HWHM/FWHM. First milestone of the GAP acceptance
sequence: identical retained lags (starting at lag 2 for CHIME) and numerical ACF
agreement between the reference pair-loop and the compatibility ACF.

**Tasks:**

- [ ] **Write the failing test** for the lag contract (reference vs main agree, CHIME
      starts at lag 2). File: `scintillation/scint_analysis/tests/test_reference_arc_parity.py` (new)

  ```python
  import numpy as np
  from scint_analysis import analysis
  from scint_analysis.revalidation import _mean_normalized_acf

  def _clean_spectrum(seed=7, n=512, scale_chan=10):
      rng = np.random.default_rng(seed)
      white = rng.normal(0, 1, n + scale_chan)
      corr = np.convolve(white, np.ones(scale_chan) / scale_chan, mode="valid")[:n]
      return np.ma.MaskedArray(100.0 + 20.0 * corr, mask=np.zeros(n, dtype=bool))

  def test_first_fit_lag_two_matches_reference_pairloop():
      """CHIME first_fit_lag=2: main ACF retained lags and values match the
      reference _mean_normalized_acf pair-loop (recomputation, not a pinned output)."""
      spec = _clean_spectrum()
      cw = 0.006103515625  # CHIME fine-channel width (MHz), U=64 -> 0.390625/64
      acf = analysis.calculate_acf(spec, cw, max_lag_bins=64, first_fit_lag=2)
      pos = acf.lags > 0
      first_pos_lag_bins = round(float(acf.lags[pos].min()) / cw)
      assert first_pos_lag_bins == 2                      # lag 1 dropped for CHIME
      assert not np.any(np.isclose(acf.lags, 0.0))         # no synthetic center
      keep = np.ones(spec.size)
      _, ref_acf, _ = _mean_normalized_acf(spec.data, keep, cw, max_lag_mhz=64 * cw, first_lag=2)
      ref_pos = ref_acf[len(ref_acf) // 2:]
      np.testing.assert_allclose(acf.acf[pos], ref_pos[: pos.sum()], rtol=1e-6, atol=1e-9)
  ```

- [ ] **Run it, watch it fail:** `conda run -n flits python -m pytest scintillation/scint_analysis/tests/test_reference_arc_parity.py::test_first_fit_lag_two_matches_reference_pairloop -v`
  → expect FAIL (`calculate_acf` has no `first_fit_lag` kwarg; injects lag-0 center).

- [ ] **Implement** the `first_fit_lag` contract in `calculate_acf`
  (`analysis.py:234-333`). Add the kwarg, drop the extra leading lag for CHIME, and
  remove the synthetic center from the returned array.

  ```python
  # analysis.py: signature (line 234)
  def calculate_acf(spectrum_1d, channel_width_mhz, off_burst_spectrum_mean=None,
                    max_lag_bins=None, first_fit_lag=1):
      ...
      # line 283: retained positive lags start at first_fit_lag (>=1), lag 0 never kept
      lags = np.arange(max(1, int(first_fit_lag)), max_lag_bins)
      ...
      # lines 318-328: symmetrize WITHOUT a synthetic center point
      full_acf = np.concatenate((acf_vals[clean_mask][::-1], acf_vals[clean_mask]))
      full_lags = np.concatenate((-positive_lags_mhz[clean_mask][::-1],
                                  positive_lags_mhz[clean_mask]))
      full_stat_err = np.concatenate((stat_errs[clean_mask][::-1], stat_errs[clean_mask]))
      full_finite_err = np.concatenate((finite_scintle_errs[clean_mask][::-1],
                                        finite_scintle_errs[clean_mask]))
      total_diag_err = np.sqrt(full_stat_err ** 2 + full_finite_err ** 2)
      return ACF(full_acf, full_lags, acf_err=total_diag_err)
  ```

  Thread the kwarg through the sub-band builder (`calculate_acfs_for_subbands`,
  `analysis.py:509`) and the intra-pulse builder from
  `config["analysis"]["acf"].get("first_fit_lag", 1)`; pass it to each `calculate_acf`
  call (lines 608, 1907).

- [ ] **Run it, watch it pass:** same pytest node → expect PASS.

- [ ] **Write the failing test** for the 2D fitter excluding lag 0.
  File: `test_reference_arc_parity.py` (append)

  ```python
  def test_2d_fitter_excludes_zero_lag():
      from scint_analysis import fitting_2d
      lags = np.linspace(-5, 5, 101)
      acf = 0.4 / (1 + (lags / 0.3) ** 2)
      acf_results = {
          "subband_lags_mhz": [lags, lags],
          "subband_acfs": [acf, acf],
          "subband_acfs_err": [np.full_like(acf, 0.02), np.full_like(acf, 0.02)],
          "subband_center_freqs_mhz": [600.0, 700.0],
      }
      model = fitting_2d.Scintillation2DModel(acf_results, fit_range_mhz=2.0)
      for lags_i, mask in zip(model.lags_list, model.masks):
          assert not np.any(mask & np.isclose(lags_i, 0.0))
  ```

- [ ] **Run it, watch it fail:** `... ::test_2d_fitter_excludes_zero_lag -v`
  → expect FAIL (mask at `fitting_2d.py:306` keeps lag 0).

- [ ] **Implement** the lag-0 exclusion in `fitting_2d.py:306`:

  ```python
  mask = (np.abs(lags) <= self.fit_range_mhz) & (lags != 0.0)
  ```

- [ ] **Run it, watch it pass.**

- [ ] **Write the failing test** for the HWHM/FWHM labeling (P0-4).
  File: `test_reference_arc_parity.py` (append)

  ```python
  def test_result_reports_hwhm_and_fwhm_labels():
      from scint_analysis.analysis import _bandwidth_fields
      out = _bandwidth_fields(gamma_hwhm_mhz=0.25)
      assert out["reported_dnu_definition"] == "HWHM"
      assert out["gamma_hwhm_mhz"] == 0.25
      assert np.isclose(out["fwhm_mhz"], 0.5)
  ```

- [ ] **Implement** a small `_bandwidth_fields` helper in `analysis.py` and emit its keys
  into every `subband_measurements` entry (`analysis.py:1730-1741`) and the component
  summary (`analysis.py:1743-1751`); thread the same three keys through
  `revalidation.revalidate_dnu`'s caller and `fitting_2d`'s `final_results["fit_2d"]`
  (`pipeline.py:355-366`).

  ```python
  def _bandwidth_fields(gamma_hwhm_mhz, gamma_err_mhz=None):
      # RECIPE ambiguity 1: notebooks report Delta_nu_d = gamma (HWHM); v3 reports 2*gamma.
      # We report HWHM and expose FWHM only as a labeled convenience field.
      d = {"gamma_hwhm_mhz": gamma_hwhm_mhz,
           "fwhm_mhz": (2.0 * gamma_hwhm_mhz if gamma_hwhm_mhz is not None else None),
           "reported_dnu_definition": "HWHM"}
      if gamma_err_mhz is not None:
          d["gamma_hwhm_err_mhz"] = gamma_err_mhz
      return d
  ```

- [ ] **Run it, watch it pass.**

- [ ] **Set the CHIME configs' lag contract.** Add `first_fit_lag: 2` under `analysis.acf`
  in the CHIME burst configs (`configs/bursts/*_chime.yaml`, `*_chime_hi.yaml`); DSA configs
  stay at the default `1`. Verify freya: `configs/bursts/freya_chime_hi.yaml` gains
  `acf.first_fit_lag: 2`.

- [ ] **Commit:** `git commit -m "scint: explicit ACF first_fit_lag contract + HWHM/FWHM labels (P0-1, P0-4)"`

**Dependencies:** none (reuses `revalidation` backbone already present).

**Verification:**
- [ ] `conda run -n flits python -m pytest scintillation/scint_analysis/tests/test_reference_arc_parity.py -v -k "first_fit_lag or zero_lag or hwhm"` → all PASS.
- [ ] `conda run -n flits python -m pytest scintillation/scint_analysis/tests/test_analysis.py scintillation/scint_analysis/tests/test_revalidation.py -q` → no regressions.

### Phase 2 — `canfar_reference` cleaning mode (P0-2)

**Objective:** Add a selectable preprocessing mode that reproduces the reference cleaning
sequence (fixed LTE mask; exact on/off windows; per-channel off-mean subtraction **and
off-RMS division**; reference mean/std RFI thresholds), keeping the modern mask-only path
as the default and emitting the cleaned spectrum + masks as inspectable intermediates.

**Tasks:**

- [ ] **Write the failing test** for per-channel S/N normalization (off-mean subtracted,
      off-RMS divided) — the reference `I_norm=(I_on−μ_off)/σ_off` (RECIPE §3c;
      `scint_wilhelm.ipynb:84`). File: `test_reference_arc_parity.py` (append)

  ```python
  def test_canfar_reference_snr_normalization():
      from scint_analysis.core import DynamicSpectrum
      from scint_analysis import freya_scintillation as fs
      rng = np.random.default_rng(3)
      nchan, nt = 64, 300
      gain = np.linspace(1.0, 3.0, nchan)[:, None]        # per-channel bandpass
      power = gain * rng.normal(0.0, 1.0, (nchan, nt)) + 10.0 * gain
      ds = DynamicSpectrum(np.ma.MaskedArray(power, mask=np.zeros_like(power, bool)),
                           frequencies=np.linspace(600, 800, nchan), times=np.arange(nt) * 8e-5)
      out = fs.normalize_snr_per_channel(ds, off_pulse_lims=(0, 200))
      off = out.power[:, 0:200]
      # each channel's off-pulse mean ~0 and off-pulse std ~1 after (x-mu)/sigma
      assert np.allclose(np.ma.mean(off, axis=1).filled(0), 0.0, atol=0.15)
      assert np.allclose(np.ma.std(off, axis=1).filled(1), 1.0, atol=0.15)
  ```

- [ ] **Run it, watch it fail:** `... ::test_canfar_reference_snr_normalization -v`
  → FAIL (`normalize_snr_per_channel` does not exist; only mean flat-field exists).

- [ ] **Implement** `normalize_snr_per_channel` in `freya_scintillation.py` (peer of
  `normalize_bandpass`, `:425`), subtracting the off-pulse mean and dividing by the
  off-pulse RMS per channel, masking gain-starved channels (reuse `normalize_bandpass`'s
  floor guard). Port of RECIPE §3c.

  ```python
  def normalize_snr_per_channel(spectrum, off_pulse_lims, *, min_off_bins=_MIN_BANDPASS_OFF_BINS):
      """Reference per-channel S/N flat-field: (I - mu_off)/sigma_off per channel.
      RECIPE §3c / scint_wilhelm.ipynb:84. Distinct from normalize_bandpass, which
      divides by mu_off only (leaves the noise scale channel-dependent)."""
      start, end = int(off_pulse_lims[0]), int(off_pulse_lims[1])
      if end - start < min_off_bins:
          raise ValueError(f"S/N normalization needs >= {min_off_bins} off-pulse bins")
      off = spectrum.power[:, start:end]
      mu = np.ma.filled(np.ma.mean(off, axis=1), np.nan)
      sig = np.ma.filled(np.ma.std(off, axis=1), np.nan)
      bad = ~(np.isfinite(mu) & np.isfinite(sig) & (sig > 0))
      sig_safe = np.where(bad, 1.0, sig)
      normed = (spectrum.power.data - mu[:, None]) / sig_safe[:, None]
      base = (np.zeros(spectrum.power.shape, bool)
              if spectrum.power.mask is np.ma.nomask or np.isscalar(spectrum.power.mask)
              else spectrum.power.mask.copy())
      mask = base | np.broadcast_to(bad[:, None], spectrum.power.shape)
      from .core import DynamicSpectrum
      return DynamicSpectrum(np.ma.MaskedArray(normed, mask=mask),
                             spectrum.frequencies.copy(), spectrum.times.copy())
  ```

- [ ] **Run it, watch it pass.**

- [ ] **Write the failing test** for the fixed LTE (730-760 MHz) mask and the mode switch.
  File: `test_reference_arc_parity.py` (append)

  ```python
  def test_canfar_reference_mode_masks_lte_band():
      from scint_analysis.core import DynamicSpectrum
      freqs = np.linspace(600, 800, 400)
      power = np.ma.MaskedArray(np.ones((400, 100)), mask=np.zeros((400, 100), bool))
      ds = DynamicSpectrum(power, frequencies=freqs, times=np.arange(100) * 8e-5)
      cfg = {"analysis": {"preprocessing": {"mode": "canfar_reference",
                                            "lte_exclude_mhz": [730.0, 760.0]},
                          "rfi_masking": {"manual_burst_window": [40, 60],
                                          "manual_noise_window": [0, 30]}}}
      out = ds.mask_rfi(cfg)
      lte = (freqs >= 730.0) & (freqs <= 760.0)
      assert out.power.mask[lte].all()
  ```

- [ ] **Run it, watch it fail:** FAIL (no `preprocessing.mode` branch; no LTE mask).

- [ ] **Implement** the mode branch in `core.mask_rfi` (`core.py:260`): when
  `config["analysis"]["preprocessing"]["mode"] == "canfar_reference"`, (a) zero+mask the
  fixed LTE band from `lte_exclude_mhz` (default `[730.0, 760.0]`, `baseband_analysis_core.py:2246`),
  (b) use the reference mean/std RFI thresholds (`thres_mean=5, thres_std=3`,
  `baseband_analysis_analysis.py:86-87`) instead of the modern `freq_threshold_sigma`,
  (c) leave the modern path untouched when the key is absent. Emit the cleaned spectrum +
  channel/time masks to `self.cache_dir/<burst>_canfar_clean.npz` for inspection when
  `pipeline_options.save_intermediate_steps` is set (wire in `pipeline.prepare_data`,
  `pipeline.py:130`).

- [ ] **Run it, watch it pass.**

- [ ] **Wire the S/N normalization into the mode** in `pipeline._apply_bandpass_normalization`
  (`pipeline.py:176`): in `canfar_reference` mode call `normalize_snr_per_channel`; else keep
  `normalize_bandpass`. Add `preprocessing.mode` to `_config_fingerprint`'s tracked block
  (already covers the whole `analysis` dict, `pipeline.py:52` — verify).

- [ ] **Commit:** `git commit -m "scint: canfar_reference cleaning mode (LTE mask, S/N norm, ref RFI thresholds) (P0-2)"`

**Dependencies:** Phase 1 (shares the ACF contract for the emitted intermediates).

**Verification:**
- [ ] `... pytest ...test_reference_arc_parity.py -v -k canfar` → PASS.
- [ ] Modern default unchanged: `... pytest ...test_core.py ...test_freya_scintillation.py -q` → no regressions.
- [ ] With `save_intermediate_steps: true` on `freya_chime_hi.yaml` + `preprocessing.mode: canfar_reference`, `<burst>_canfar_clean.npz` is written and loadable.

### Phase 3 — Reference-parity regression tests (P0-3)

**Objective:** Pin cleaned spectra, retained lag arrays, ACF values, and fitted notebook γ
against rescued-recipe values — not merely current outputs. For each expected value, record
whether it is an **executed-notebook output** or a **recomputation** of the rescued source.

**Tasks:**

- [ ] **Stage the fixture.** Copy the ready ACF fixture
  `reference_arc/arc_live/old_scattering_scintillation/zach_acf_codetections_fftsize64_downfreq1.npz`
  into `scintillation/scint_analysis/tests/fixtures/` (small, 334 KB). Provenance note in a
  `tests/fixtures/PROVENANCE.md`: keys `sub_acfs (6,3274)`, `sub_lags (6,3274)`,
  `sub_fcents (6)` are **executed-notebook outputs** (the zach `measure_scintillation.ipynb`
  6-sub-band ACFs, fftsize=64 downfreq=1).

- [ ] **Write the parity test** — recompute γ per sub-band from the fixture ACFs with the
      reference HWHM Lorentzian and assert the γ(ν) trend + a stored recomputed value.
      File: `test_reference_arc_parity.py` (append)

  ```python
  from pathlib import Path
  FIX = Path(__file__).parent / "fixtures" / "zach_acf_codetections_fftsize64_downfreq1.npz"

  def test_zach_subband_gamma_recompute_from_notebook_acfs():
      """EXPECTED VALUES = RECOMPUTATION: fit the reference HWHM Lorentzian to the
      zach notebook's executed sub-band ACF arrays. Assert (a) 6 sub-bands,
      (b) gamma > 0 and monotone-ish increase with frequency (alpha>0), and
      (c) each gamma within the recorded band of a stored recomputed reference."""
      from scint_analysis.revalidation import _lorentz_w_c
      from lmfit import Model
      d = np.load(FIX, allow_pickle=True)
      sub_acfs, sub_lags, fcents = d["sub_acfs"], d["sub_lags"], d["sub_fcents"]
      assert sub_acfs.shape[0] == 6
      gammas = []
      for acf, lags in zip(sub_acfs, sub_lags):
          pos = lags > 0
          x, y = lags[pos], acf[pos]
          m = Model(_lorentz_w_c)
          r = m.fit(y, x=x, gamma=float(x[np.argmax(y < y[0] / 2)] or x[1]),
                    m=float(np.sqrt(max(y[0], 1e-3))), c=0.0)
          gammas.append(abs(r.params["gamma"].value))
      gammas = np.array(gammas)
      assert np.all(gammas > 0)
      alpha = np.polyfit(np.log10(fcents), np.log10(gammas), 1)[0]
      assert alpha > 0.0        # scint bandwidth grows with frequency
  ```

  (The concrete per-sub-band γ reference values are filled in from the first passing run
  and frozen as a recomputation baseline with a stated ±20% fit-stability tolerance, per
  GAP acceptance step 3.)

- [ ] **Run it, watch it fail then pass:** `... ::test_zach_subband_gamma_recompute_from_notebook_acfs -v`
  (fails until the fixture is staged + `_lorentz_w_c` import path is correct).

- [ ] **Write the executed-notebook γ pin** for freya. The Freya notebook labels `gamma1`
  directly as Δν (`scint_freya.ipynb:929`, HWHM). Record the reported value + stderr as an
  **executed-notebook output** constant and assert the current pipeline (CHIME `first_fit_lag=2`,
  `canfar_reference` cleaning) lands within a stated tolerance on the same product.
  File: `test_reference_arc_parity.py` (append)

  ```python
  # EXECUTED-NOTEBOOK OUTPUT: scint_freya.ipynb:929 reports Delta_nu = gamma1 (HWHM).
  FREYA_NOTEBOOK_GAMMA_KHZ = 35.19   # value + method transcribed from the worked cell
  FREYA_TOL_KHZ = 15.0               # fit-stability + cleaning-mode tolerance (GAP step 3/4)

  @pytest.mark.slow
  def test_freya_chime_gamma_brackets_notebook_value():
      """End-to-end freya CHIME product through the parity path lands within
      FREYA_TOL of the executed-notebook HWHM. Marked slow (loads the real npz)."""
      ...  # load configs/bursts/freya_chime_hi.yaml with canfar_reference + first_fit_lag=2,
          # run ScintillationAnalysis, read component gamma_hwhm_mhz*1e3, assert |Δ|<FREYA_TOL_KHZ
  ```

  (Guarded by data availability: `pytest.importorskip`/`skipif` on the freya npz path so CI
  without the data collects-and-skips rather than errors.)

- [ ] **Write the ACF-value parity test** (GAP acceptance steps 1-2): same cleaned spectrum
  through the reference pair-loop (`_acf_masked`) and the compatibility ACF (`calculate_acf`)
  agree on retained lags (start at lag 2) and ACF values within a float tolerance — this is
  the Phase-1 test generalized to the staged cleaned-spectrum fixture; recomputation.

- [ ] **Commit:** `git commit -m "scint: reference_arc parity regression tests + fixtures (P0-3)"`

**Dependencies:** Phases 1-2.

**Verification:**
- [ ] `... pytest scintillation/scint_analysis/tests/test_reference_arc_parity.py -v` → PASS
      (slow/data-gated tests skip cleanly without the burst npz).
- [ ] `tests/fixtures/PROVENANCE.md` states executed-notebook vs recomputation for each value.

### Phase 4 — Sub-band γ(ν) scaling estimator: primary ODR + notebook cross-check (P1-5)

**Objective:** Report the frequency-scaling index α three labeled ways — `odr_logspace`
(primary; `analysis-Copy1.py:844-873`), `loglog_unweighted` (notebook cross-check), and
`joint_2d` (modern `fitting_2d`). RECIPE ambiguity 2: no notebook fits α to real data, so
the log-space ODR is the real estimator and the notebook's unweighted log-log regression is
only a corroborating cross-check.

**Tasks:**

- [ ] **Write the failing test** that both estimators recover an injected α and are reported
      under named keys. File: `test_reference_arc_parity.py` (append)

  ```python
  def test_gamma_scaling_reports_odr_and_loglog(monkeypatch):
      from scint_analysis import analysis
      freqs = np.array([450., 550., 650., 750., 850., 950.])
      alpha_true = 4.0
      gammas = 0.05 * (freqs / 600.0) ** alpha_true
      # minimal acf_results with pre-fit per-subband measurements injected
      out = analysis.estimate_gamma_scaling(freqs, gammas,
                                            gamma_errs=0.05 * gammas, ref_freq=600.0)
      assert set(out) >= {"odr_logspace", "loglog_unweighted"}
      assert abs(out["odr_logspace"]["alpha"] - alpha_true) < 0.3
      assert abs(out["loglog_unweighted"]["alpha"] - alpha_true) < 0.3
      assert out["odr_logspace"]["method"] == "log-space ODR (analysis-Copy1.py:844)"
  ```

- [ ] **Run it, watch it fail:** FAIL (`estimate_gamma_scaling` does not exist).

- [ ] **Implement** `estimate_gamma_scaling(freqs, gammas, gamma_errs=None, ref_freq=...)`
  in `analysis.py`, factoring the existing ODR block (`analysis.py:1697-1718`) into the
  `odr_logspace` branch and adding the notebook `loglog_unweighted` branch
  (`np.polyfit(log10(freq), log10(gamma), 1)`, unweighted — `scint_wilhelm.ipynb:240`).
  Each branch returns `{"alpha", "alpha_err", "c", "bw_at_ref_mhz", "method"}`.

  ```python
  def estimate_gamma_scaling(freqs, gammas, gamma_errs=None, ref_freq=600.0):
      freqs = np.asarray(freqs, float); gammas = np.asarray(gammas, float)
      lf, lg = np.log10(freqs), np.log10(gammas)
      # --- primary: log-space ODR (analysis-Copy1.py:844-873); handles x/y errors ---
      from scipy.odr import ODR, Model as ModelODR, RealData
      sy = (np.asarray(gamma_errs, float) / (gammas * np.log(10))
            if gamma_errs is not None else None)
      use_w = sy is not None and np.all(np.isfinite(sy)) and np.all(sy > 0)
      odr = ODR(RealData(lf, lg, sy=sy if use_w else None),
                ModelODR(lambda B, x: B[0] * x + B[1]), beta0=[4.0, 0.0]).run()
      odr_out = {"alpha": float(odr.beta[0]), "alpha_err": float(odr.sd_beta[0]),
                 "c": float(10 ** odr.beta[1]),
                 "bw_at_ref_mhz": float(10 ** (odr.beta[0] * np.log10(ref_freq) + odr.beta[1])),
                 "method": "log-space ODR (analysis-Copy1.py:844)"}
      # --- cross-check: notebook unweighted log-log regression (scint_wilhelm.ipynb:240) ---
      b, a = np.polyfit(lf, lg, 1)
      ll_out = {"alpha": float(b), "alpha_err": float("nan"), "c": float(10 ** a),
                "bw_at_ref_mhz": float(10 ** (b * np.log10(ref_freq) + a)),
                "method": "unweighted log-log polyfit (scint_wilhelm.ipynb:240)"}
      return {"odr_logspace": odr_out, "loglog_unweighted": ll_out}
  ```

- [ ] **Run it, watch it pass.**

- [ ] **Wire it into `analyze_scintillation_from_acfs`** (`analysis.py:1720-1751`): keep the
  existing ODR as `odr_logspace`, add `loglog_unweighted`, and (when `fit_2d` ran) surface
  `joint_2d` from `final_results["fit_2d"]["alpha"]`; store all under
  `final_results["components"][name]["gamma_scaling"]` with method labels. Preserve the
  legacy `scaling_index`/`power_law_fit_report` keys for existing consumers.

- [ ] **Add a labeled-estimator overview figure.** Extend `plotting.plot_analysis_overview`
  (mod/γ-vs-freq panel, `plotting.py:300`) to overplot the three α lines with a legend;
  register via `tools/figure_manifest.write_manifest` with an expectation string naming the
  three estimators.

- [ ] **Commit:** `git commit -m "scint: three-estimator gamma(nu) scaling (ODR primary + notebook loglog + joint2d) (P1-5)"`

**Dependencies:** Phases 1, 3.

**Verification:**
- [ ] `... pytest ...test_reference_arc_parity.py -v -k scaling` → PASS.
- [ ] A CHIME `final_results` JSON's `components.scint_scale.gamma_scaling` has all three
      named estimators with `alpha` + `method`.

### Phase 5 — Modulation index m(ν) and m(t) (P1-6)

**Objective:** Emit both modulation-index definitions (RECIPE §4): m(ν) = fitted √amplitude
per sub-band (already present, keep), and m(t) via **both** the ACF-fitted per-time-slice γ/m
(repair the dead intra-pulse path) **and** the direct `std/mean` sliding time-chunk statistic
(`scinttools_v3.analyze_modulation_over_time`). Report both, labeled.

**Tasks:**

- [ ] **Write the failing test** proving the intra-pulse path runs (not aborts) and reads the
      correct param names. File: `test_reference_arc_parity.py` (append)

  ```python
  def test_intra_pulse_runs_with_single_lorentzian(chime_like_ds_and_cfg):
      from scint_analysis import analysis
      ds, cfg, burst_lims, noise_desc = chime_like_ds_and_cfg
      cfg["analysis"]["acf"]["intra_pulse_time_bins"] = 4
      res = analysis.analyze_intra_pulse_scintillation(ds, burst_lims, cfg, noise_desc)
      assert isinstance(res, list) and len(res) >= 1     # no longer aborts
      assert all(np.isfinite(r["bw"]) for r in res)       # l_gamma read correctly
  ```

- [ ] **Run it, watch it fail:** FAIL — the guard `if "1c" not in model_to_fit: return []`
  (`analysis.py:1868`) aborts, and `l_gamma1`/`l_m1` (lines 1940, 1952) are wrong keys.

- [ ] **Implement** the three-part repair in `analyze_intra_pulse_scintillation`
  (`analysis.py:1830-1974`):
  - line 1862: default `model_to_fit = fit_config.get("intra_pulse_fit_model", "fit_lor")`
    (the actual single-Lorentzian fit key emitted by `_fit_acf_models`).
  - lines 1868-1872: replace the `"1c"` abort with a check that the resolved model is a
    single-component Lorentzian/Gaussian (`model_to_fit.endswith(("lor", "gauss"))`);
    otherwise log and fall back to `"fit_lor"`.
  - lines 1940, 1952: read `l_gamma`/`l_m` (unnumbered), `g_sigma`/`g_m` for Gaussian —
    matching `_baseline_registry` (`analysis.py:121`). Emit `_bandwidth_fields` per slice.

- [ ] **Run it, watch it pass.**

- [ ] **Write the failing test** for the direct `std/mean` time-chunk statistic.
  File: `test_reference_arc_parity.py` (append)

  ```python
  def test_direct_modulation_over_time_std_over_mean():
      from scint_analysis import analysis
      rng = np.random.default_rng(5)
      nchan, nt = 128, 60
      # constant-modulation burst: each time column has std/mean ~ 0.5
      cols = np.abs(rng.normal(1.0, 0.5, (nt, nchan)))
      power = np.ma.MaskedArray(cols.T, mask=np.zeros((nchan, nt), bool))
      m_t = analysis.modulation_index_over_time(power, burst_lims=(0, nt),
                                                chunk_bins=3, overlap_bins=2)
      assert m_t["method"] == "direct std/mean (scinttools_v3.analyze_modulation_over_time)"
      assert np.nanmedian(m_t["m"]) > 0.2 and len(m_t["time_idx"]) > 1
  ```

- [ ] **Run it, watch it fail:** FAIL (`modulation_index_over_time` does not exist).

- [ ] **Implement** `modulation_index_over_time(power, burst_lims, chunk_bins, overlap_bins)`
  in `analysis.py` — sliding time-chunk `m = chunk_std/chunk_mean` on the frequency-averaged
  intensity (RECIPE §4; `scinttools_v3.py:611-735`). Returns
  `{"time_idx", "time_s"?, "m", "method": "direct std/mean (...)"}`.

- [ ] **Run it, watch it pass.**

- [ ] **Wire both into the pipeline + output.** In `pipeline.run()` (`pipeline.py:313-324`),
  when `acf.enable_intra_pulse_analysis`, also compute `modulation_index_over_time` and store
  it on `self.modulation_over_time`; embed `final_results["modulation_index_time"]` with both
  `acf_fitted` (from `intra_pulse_results`) and `direct_std_mean` sub-dicts. In
  `run_analysis.py:98-108`, call `plotting.plot_intra_pulse_evolution` (`plotting.py:443`)
  when `intra_pulse_results` exist, and register the PNG via `write_manifest`.

- [ ] **Commit:** `git commit -m "scint: repair m(t) intra-pulse path + add direct std/mean m(t); keep fitted m(nu) (P1-6)"`

**Dependencies:** Phase 1 (`_bandwidth_fields`, fit keys).

**Verification:**
- [ ] `... pytest ...test_reference_arc_parity.py -v -k "intra_pulse or modulation"` → PASS.
- [ ] `... pytest ...test_analysis.py -q` → no regressions.
- [ ] A run with `enable_intra_pulse_analysis: true` writes `final_results["modulation_index_time"]`
      with both `acf_fitted` and `direct_std_mean`, and emits the intra-pulse PNG + manifest.

### Phase 6 — Enforce CHIME artifact gates in the pipeline (P1-7)

**Objective:** Make `pipeline.run()` compute the off-pulse ACF null and low-lag excision
refits, call `finalize_measurement_status`, and embed the verdict + mitigation records +
systematic scan + windows + fit-lag policy in `final_results`. A CHIME JSON must not be a
`measurement` merely because optimization succeeded.

**Tasks:**

- [ ] **Write the failing test** that a CHIME run embeds a `measurement_status` verdict and
      demotes to `diagnostic_only` when the off-pulse null fails.
      File: `test_reference_arc_parity.py` (append)

  ```python
  def test_pipeline_embeds_measurement_status(monkeypatch):
      from scint_analysis import pipeline
      p = _minimal_chime_pipeline()          # small synthetic CHIME-flagged config+data
      # force a failing off-pulse null: off-pulse median width ~ on-pulse width
      monkeypatch.setattr(pipeline.ScintillationAnalysis, "_off_pulse_dnu_slices",
                          lambda self, *a, **k: [self._on_dnu_mhz] * 5)
      p.run()
      ms = p.final_results["measurement_status"]
      assert ms["status"] == "diagnostic_only"
      assert "off_pulse_null" in ms["failed_checks"]
      assert p.final_results["fit_lag_policy"]["first_fit_lag"] == 2
  ```

- [ ] **Run it, watch it fail:** FAIL (`run()` never calls the guards; no keys emitted).

- [ ] **Implement** a `_finalize_chime_status` step in `pipeline.run()` after
  `analyze_scintillation_from_acfs` (`pipeline.py:335`). Reuse the resolved
  `self.burst_lims`/`self.off_pulse_lims` (already exposed for exactly this,
  `pipeline.py:28-30`) and the `subband_channel_slices` recorded by the ACF builder
  (`analysis.py:562`) to slice off-pulse spectra on the identical channel boundaries. Compute
  off-pulse widths via `revalidation.revalidate_dnu` (same machinery), low-lag excision refits
  (drop k=1..N leading positive lags), then:

  ```python
  from . import chime_artifact_guards as guards
  provenance = guards.chime_provenance_status(self.config)
  null = guards.off_pulse_null_verdict(on_dnu, off_dnu_list)
  stab = guards.low_lag_stability_verdict(on_dnu, dnu_by_excision)
  status = guards.finalize_measurement_status(provenance, off_pulse_null=null,
                                              low_lag_stability=stab)
  self.final_results["measurement_status"] = status
  self.final_results["chime_provenance"] = provenance
  self.final_results["off_pulse_null"] = null
  self.final_results["low_lag_stability"] = stab
  self.final_results["fit_lag_policy"] = {
      "first_fit_lag": self.config["analysis"]["acf"].get("first_fit_lag", 1),
      "harmonic_mask": self.config["analysis"]["fitting"].get("harmonic_mask", {}),
      "reported_dnu_definition": "HWHM"}
  ```

  Non-CHIME telescopes get the `finalize_measurement_status` no-op branch (already handled,
  `chime_artifact_guards.py:401`). Gate the whole block behind `telescope == "chime"` to keep
  DSA output untouched.

- [ ] **Run it, watch it pass.**

- [ ] **Enrich `run_analysis.py` result provenance** (`run_analysis.py:83-96`): serialize
  `measurement_status`, `chime_provenance`, `off_pulse_null`, `low_lag_stability`, and
  `fit_lag_policy` alongside `final_results` (already dumped as one dict — verify the
  `NumpyJSONEncoder` covers the new nested numpy scalars).

- [ ] **Commit:** `git commit -m "scint: enforce CHIME artifact gates + embed measurement_status/fit_lag_policy in results (P1-7)"`

**Dependencies:** Phases 1, 4 (on_dnu comes from the parity-mode fit; reuses `revalidate_dnu`).

**Verification:**
- [ ] `... pytest ...test_reference_arc_parity.py -v -k measurement_status` → PASS.
- [ ] `... pytest ...test_chime_artifact_guards.py ...test_pipeline_wiring.py -q` → no regressions.
- [ ] Freya CHIME end-to-end (Phase 3 slow test data) yields `measurement_status.status ==
      "diagnostic_only"` with `off_pulse_null`/`low_lag_stability` in `failed_checks` (the
      documented freya failure), while a clean burst (e.g. casey) yields `measurement`.

## Success Criteria

### Automated Verification
- [ ] `conda run -n flits python -m pytest scintillation/scint_analysis/tests/test_reference_arc_parity.py -v` passes (data-gated `slow` tests skip cleanly without burst npz).
- [ ] `conda run -n flits python -m pytest scintillation/scint_analysis/tests -q` passes (no regressions in existing suites).
- [ ] `conda run -n flits ruff check scintillation/scint_analysis` passes.
- [ ] File `scintillation/scint_analysis/tests/test_reference_arc_parity.py` exists with tests for: first_fit_lag contract, 2D lag-0 exclusion, HWHM/FWHM labels, canfar_reference S/N norm + LTE mask, zach sub-band γ recompute, three-estimator scaling, intra-pulse repair, direct m(t), measurement_status embedding.
- [ ] File `scintillation/scint_analysis/tests/fixtures/PROVENANCE.md` labels each expected value executed-notebook vs recomputation.
- [ ] A CHIME `final_results` JSON contains `measurement_status`, `fit_lag_policy`, `reported_dnu_definition`, `gamma_scaling` (3 named estimators), `modulation_index_time` (both defs).

### Manual Verification
- [ ] The γ(ν) three-estimator overview PNG and the intra-pulse m(t)/Δν(t) PNG pass the
      figure-review Stop gate (read each PNG, write `figures.review.json` verdicts) — no
      figure is "validated" until looked at (CLAUDE.md §Figure-review).
- [ ] **Owner sign-off on the 4-burst legacy cross-check table**: γ_pipeline (HWHM) vs
      γ_reference for chromatica, freya, hamilton, wilhelm, with the reference source
      (notebook cell / recomputation) named per row, and the freya `diagnostic_only`
      downgrade shown as expected-not-a-regression.
- [ ] Uniform-methods check (owner rule): the modern default path is applied identically to
      all 12 bursts; `canfar_reference` appears only as a cross-validation column for the 4
      legacy bursts, not as a per-burst method swap.

### Reproducibility & Correctness (research code)
- [ ] Seeds pinned in every synthetic-data test; the zach fixture carries a SHA-256 in
      `tests/fixtures/PROVENANCE.md` (matched to `reference_arc/SHA256SUMS.arc_live`).
- [ ] Numerical correctness criteria: (a) Phase-1 ACF parity is an exact-recompute assertion
      (`rtol=1e-6`) against the reference pair-loop; (b) injected-α recovery within 0.3
      (Phase 4); (c) legacy γ within a stated fit-stability + cleaning tolerance
      (Phase 3, `FREYA_TOL_KHZ`).
- [ ] The parity suite reproduces in a clean `flits` env from repo root.

## Testing Strategy

**Unit Test Coverage (written in-phase, all in `test_reference_arc_parity.py`):**
- [ ] ACF `first_fit_lag` contract + reference pair-loop agreement; 2D lag-0 exclusion; HWHM/FWHM labels (Phase 1).
- [ ] canfar_reference S/N normalization + LTE mask + mode switch (Phase 2).
- [ ] zach sub-band γ recompute from executed-notebook ACFs; ACF-value parity; freya executed-notebook γ pin (Phase 3).
- [ ] Three-estimator γ(ν) scaling with named methods (Phase 4).
- [ ] Intra-pulse repair (runs, correct param keys) + direct std/mean m(t) (Phase 5).
- [ ] Pipeline embeds measurement_status + fit_lag_policy; diagnostic_only demotion (Phase 6).
- Mock external dependencies: burst npz loads are data-gated (`skipif`/`importorskip`); no network.

**Integration Tests:**
- [ ] End-to-end `ScintillationAnalysis.run()` on `freya_chime_hi.yaml` (canfar_reference +
      first_fit_lag=2) produces the full enriched `final_results` (slow, data-gated).
- [ ] Modern default path on a DSA config is byte-behavior-unchanged (regression guard via existing `test_pipeline_wiring.py`).

**Manual Testing:**
- [ ] 4-burst legacy cross-check table generated and owner-reviewed.
- [ ] Figure-review verdicts written for the two new PNGs.

**Test Data Requirements:**
- `tests/fixtures/zach_acf_codetections_fftsize64_downfreq1.npz` (staged from `reference_arc/arc_live`).
- Real burst npz under `~/Data/Faber2026/dsa110/scintillation/data/` for slow integration tests (data-gated).

## Migration Strategy

**Migration Steps:**
1. Land Phases 1-3 (parity backbone + tests) — no default-behavior change beyond the CHIME
   lag contract, which is set per-config.
2. Land Phases 4-6 (estimators + gates) — additive result keys; legacy keys preserved.
3. Regenerate the 12-burst campaign run (P4d) on the new path; the DSA numbers are unchanged.

**Rollback Plan:** each phase is a standalone commit; revert the phase commit. The
`canfar_reference` mode and `first_fit_lag` are opt-in config keys — reverting a config
restores prior behavior without code changes.

**Backward Compatibility:** modern default cleaning + ODR scaling + fitted m(ν) are unchanged;
DSA configs default to `first_fit_lag: 1`; legacy `scaling_index`/`power_law_fit_report` keys
are retained alongside the new `gamma_scaling` block.

## Risk Assessment

1. **Risk:** Removing the synthetic `ACF(0)=1` center destabilizes existing fits that leaned
   on it as an anchor.
   - **Likelihood:** Medium — **Impact:** Medium
   - **Mitigation:** the 1D fit already excludes lag 0 (`analysis.py:700`); only the 2D fit
     consumed the center. Phase-1 tests assert the 2D mask now excludes it; run the full
     existing suite as a regression guard before committing.
2. **Risk:** `canfar_reference` S/N division amplifies noise in gain-starved channels.
   - **Likelihood:** Medium — **Impact:** Low
   - **Mitigation:** reuse `normalize_bandpass`'s floor guard to mask (never divide by)
     non-positive/gain-starved channels; emit the cleaned intermediate for inspection.
3. **Risk:** The legacy γ tolerance (`FREYA_TOL_KHZ`) is set too tight and the parity test
   flaps, or too loose and it is not a real check.
   - **Likelihood:** Medium — **Impact:** Medium
   - **Mitigation:** freeze the tolerance from the first clean run as fit-stability + cleaning
     spread (GAP acceptance step 3/4), document the basis in the test, and mark the
     end-to-end variant `slow`/data-gated.
4. **Risk:** Reference `f_res`/grid ambiguities (RECIPE ambiguities 3-4: freya's CHIME
   `f_res=30.518 kHz` is a DSA number; 0.39101 vs 0.390625) leak a wrong absolute Δν scale.
   - **Likelihood:** Low — **Impact:** High
   - **Mitigation:** derive the CHIME fine-channel width from the product's own `delta_f`/U
     (`DATA_PROVENANCE.md §2a`, `0.390625/U`), never from the notebook constant; assert the
     channel width used in a parity test.

## Edge Cases and Error Handling

**Edge Cases:**
1. **Case:** Sub-band with <2 valid measurements for the power law.
   - **Expected Behavior:** report `"Fit failed: <2 measurements"` (existing, `analysis.py:1656`); the new estimators inherit the same guard.
2. **Case:** Off-pulse window too short for S/N normalization or the null test.
   - **Expected Behavior:** `normalize_snr_per_channel` raises loudly (mirrors `normalize_bandpass`); the null test returns `null_pass=None` (inconclusive), which does not force a downgrade (`finalize_measurement_status`).
3. **Case:** Non-CHIME (DSA) burst.
   - **Expected Behavior:** `first_fit_lag=1`, no gate downgrade, no `canfar_reference` unless explicitly configured — verified by keeping the gate block behind `telescope == "chime"`.

**Error Scenarios:**
1. **Error:** Fixture missing / burst npz absent in CI.
   - **Handling:** `skipif`/`importorskip` data-gates; recompute-from-fixture tests use the staged small npz which ships in-repo.

## Performance Considerations
- ACF fits are light and stay local (bounded workers per the campaign plan); the off-pulse
  null adds ≤5 extra 1D ACF fits per burst — negligible. No re-up-channelization or wide MCMC
  is in scope, so nothing routes to h17 from this plan.

## Documentation Updates
- [ ] `tests/fixtures/PROVENANCE.md` (new) — fixture origin + SHA-256 + executed-notebook-vs-recompute labels.
- [ ] Docstrings on every new function citing the reference source (RECIPE §/line, `analysis-Copy1.py:line`).
- [ ] `DATA_PROVENANCE.md §7c` — once parity lands, update the "reconstruct provenance before promoting" note to point at the parity suite as the satisfied gate (confirmed-stale-doc fix, in-lane).

## Timeline Estimate
- Phase 1 (P0-1 + P0-4): ~160-270 LOC. Phase 2 (P0-2): ~220-350 LOC. Phase 3 (P0-3): ~180-300 LOC + fixture. Phase 4 (P1-5): ~90-150 LOC. Phase 5 (P1-6): ~120-190 LOC. Phase 6 (P1-7): ~140-220 LOC.
- **Total: ~910-1480 LOC** (implementation + focused tests, excluding the staged binary fixture).

**Note:** estimates from `GAP_ANALYSIS.md §3`; may shift as parity tolerances are frozen.

## Open Questions

*(none — all resolved from RECIPE / GAP / code and stated inline)*

---

## References

**Research / evidence documents:**
- `reference_arc/RECIPE.md` (reconstructed sequence + 9 ambiguities), `GAP_ANALYSIS.md` (ranked deltas + acceptance sequence), `ORIGIN.md` (provenance).
- `plan-chime-scint-gamma-campaign.md` (campaign context / loop mechanics).

**Files Analyzed (worktree `flits-scint-rescue`):**
- `scintillation/scint_analysis/analysis.py`, `revalidation.py`, `core.py`, `pipeline.py`, `fitting_2d.py`, `run_analysis.py`, `chime_artifact_guards.py`, `freya_scintillation.py`, `plotting.py`.
- `scintillation/scint_analysis/reference_arc/code/analysis-Copy1.py:844-891`; `arc_live/old_scattering_scintillation/utilities/kenzie_funcs.py:446`, `scint_funcs.py:269-283`; `arc_live/old_scattering_scintillation/zach_acf_codetections_fftsize64_downfreq1.npz`.
- `scintillation/DATA_PROVENANCE.md §2a, §5, §7c/d`; `scintillation/configs/bursts/freya_chime_hi.yaml`; `pyproject.toml`; `tests/test_revalidation.py`; `tools/figure_manifest.py`.

**External Documentation:**
- Nimmo et al. 2025 (arXiv:2406.11053); Pradeep et al. 2025 / Pleunis et al. 2025 (arXiv:2505.04576 §5.1).

---

## Review History

- 2026-07-12 Phase 1 executed (codex) + adversarial verify (fable): initial REFUTED —
  centerless ACF broke the noise-template path (length mismatch + positional
  normalization anchor); fixed + template-enabled regression added; re-verify
  CONFIRMED-FIXED; committed 9de9aa8.
- 2026-07-13 Phase 2 CONFIRMED-GOOD (committed 186ccf7). Phase 3 initially
  REFUTED on the freya xfail attribution: 'scallop not ported' rejected —
  35.19 kHz is the documented instrumental-artifact value
  (chime_artifact_guards.py:7) and the rescued freya fit is unconstrained
  (3836±2132 kHz); xfail relabeled, PROVENANCE corrected, committed 4e7f3e0.
- **Campaign amendment:** P4d must include a freya_chime_hi factor-isolation
  sweep — one knob at a time: canfar_reference on/off at fixed lag;
  first_fit_lag in {1,2,3}; assert the pipeline fine-channel width equals the
  notebook's 30.51757812 kHz grid (RECIPE ambiguity 3) — before any scallop
  porting is scheduled.
- **Phase 4 amendment (from re-verify):** the power-law ODR block overflows
  `10**log_c` / `10**log_b_ref` (`analysis.py:1746,1751`) on ill-conditioned
  sub-band sets. `estimate_gamma_scaling` MUST carry `c` in log-space (or
  `np.errstate` + clip) and assert finiteness of `bw_at_ref_mhz`; add an
  ill-conditioned 2-subband test case asserting a finite or explicitly-flagged
  result, never inf.


### Version 1.0 — 2026-07-12
- Initial plan created (P4c recipe-parity, deltas P0-1…P1-7 from GAP_ANALYSIS).
