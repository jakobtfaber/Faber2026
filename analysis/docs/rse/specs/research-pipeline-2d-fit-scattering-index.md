# Research: 2D time–frequency fitting and the scattering index in `pipeline/` (dsa110-FLITS)

**Date:** 2026-07-01
**Scope:** internal codebase
**Codebase state:** Faber2026 `80f27c7`; `pipeline/` submodule pinned at `6ce3e58` (all `file:line` anchors below are against the pinned checkout, paths relative to `pipeline/` unless noted)
**Related Documents:** pipeline ADRs `docs/adr/0004`–`0006`; `CONTEXT.md` (manuscript domain contract); `.agents/deferred-tasks.md` (pipeline)

## Question / Scope

How does the dsa110-FLITS pipeline fit 2D time–frequency (dynamic-spectrum) data,
and specifically how is the scattering index α — the exponent in τ(ν) ∝ ν^(−α) —
parameterized, constrained, fitted, validated, and consumed downstream in the
manuscript? Internal pass only; no external prior-art dimension was requested.

## Codebase Findings

### 1. Data preparation (`BurstDataset`)

`scattering/scat_analysis/pipeline/io.py` loads a burst `.npy` of shape
`(n_freq, n_time)` and prepares it for the 2D fit:

- Frequency is standardized to ascending order on load; CHIME arrays arrive
  descending and are flipped via the telescope config (`io.py:66-69`).
- Bandpass correction converts each channel to a z-score using the outer-quarter
  off-pulse samples (`io.py:131-137`); units stay S/N — no peak normalization
  (`io.py:143-146`).
- The outer 45% time buffer is trimmed (`outer_trim=0.45` default at
  `io.py:46`; applied `io.py:139-141`),
  then the array is block-averaged by integer `f_factor`/`t_factor`
  (`downsample`, `burstfit.py:1440-1449`). Production configs downsample hard:
  e.g. `scattering/configs/bursts/chime/freya_chime.yaml` uses `f_factor: 64`,
  `t_factor: 24`, `steps: 10000`, `model_scan: true`, `dm_init: 0.0`.
- The burst is centered by rolling the peak of the smoothed band-integrated
  profile to the window center (`io.py:148-154`).
- Optional on-pulse crop restricts the time axis to burst + tail + margin so
  far-off-pulse baseline structure does not dominate the likelihood and drive
  "zeta/alpha runaway" (`io.py:49-52`, `io.py:169-203`). Per-channel MAD noise
  is estimated **before** cropping, from the full window, because narrow crops
  leave too few off-pulse samples (`io.py:87-93`, `io.py:156-167`).
- The resulting `FRBModel` receives the **native** channel width
  (`telescope.df_MHz_raw`) so intra-channel DM smearing is computed at the
  dedispersion resolution, not the downsampled width (`io.py:95-101`).
- `dm_init` semantics: 0 for coherently-dedispersed data (CHIME, smearing
  removed), catalog DM for incoherently-dedispersed data (DSA)
  (`burstfit.py:682-696` docstring).

### 2. Forward model (`FRBModel`)

`scattering/scat_analysis/burstfit.py` is the canonical physics kernel (per repo
CLAUDE.md; `flits/` only wraps it). The model dynamic spectrum
(`FRBModel.__call__`, `burstfit.py:716-787`) is, per frequency channel:

    amplitude × (Gaussian pulse ⊛ scattering PBF)

- **Amplitude:** `c0 · (ν/ν_ref)^γ` with ν_ref the band median
  (`burstfit.py:735-736`).
- **Arrival time:** `t0` plus a residual cold-plasma dispersion delay from the
  fitted `delta_dm` (`burstfit.py:739-743`, `_dispersion_delay`
  `burstfit.py:674-679`). `delta_dm` is a *residual* around the DM the data was
  dedispersed at, bounded ±50 pc cm⁻³ (`DM_RESID_MAX`, `burstfit.py:71-74`).
- **Gaussian width:** intra-channel DM smearing (boxcar variance-matched,
  dt_DM/√12) hypot-combined with intrinsic width ζ (`_smearing_sigma`,
  `burstfit.py:682-696`). Smearing scales with `dm_init + delta_dm`; omitting
  the fitted residual previously let real smearing leak into ζ/τ and bias α
  (`burstfit.py:745-756`).
- **Scattering (M2/M3 only):** the scattering index enters **twice**, and both
  entries derive from the turbulence spectral index β:
  1. *Frequency scaling:* `alpha = p.alpha` (a derived property, see §3), then
     `tau = tau_1ghz * (freq/1.0)^(-alpha)` with freq in GHz
     (`burstfit.py:766-769`).
  2. *PBF shape:* for β within 0.02 of 4, the closed-form Gaussian⊛exponential
     (erfcx-stable with asymptotic overflow handling,
     `analytic_gaussian_exp_convolution`, `burstfit.py:117-195`); otherwise the
     thin-screen power-law-spectrum PBF — exponential at small lag with a heavy
     `t^(−β/2)` tail beyond the crossover `s_c = 2·ln(2/(4−β))` (Cordes review
     §11.2 provenance in the docstring), area-normalized, FFT-convolved
     (`gaussian_powerlaw_convolution`, `burstfit.py:198-248`; dispatch at
     `burstfit.py:771-776`; β clipped to (2.01, 3.99) at `burstfit.py:233-234`).
- Env overrides `FLITS_PBF` / `FLITS_PBF_BETA` select the PBF family through
  multiprocessing pools without signature changes (`burstfit.py:655-661`).
- **Naming collision (read carefully):** `FRBModel.beta` (constructor arg,
  default 2.0, `burstfit.py:633,648-649`) is the *dispersion-law exponent*
  ν^(−β) used in `_dispersion_delay` (`burstfit.py:679`) — entirely distinct
  from `FRBParams.beta`, the turbulence spectral index. Same letter, different
  physics.

### 3. Parameterization — the β co-model (ADR-0006)

The central architectural fact: **α is never a sampled parameter.** As of
ADR-0006 (`docs/adr/0006-beta-coherent-scattering-comodel.md`, accepted
2026-06-30), the electron-density fluctuation spectral index β
(P_n(q) ∝ q^(−β)) is fundamental; α is derived at each likelihood evaluation
through the thin-screen closure:

    alpha = 2β/(β−2)   (β ≤ 4; alpha = 4 exactly at β = 4)

- `FRBParams` fields: `c0, t0, gamma, zeta, tau_1ghz, beta, delta_dm`, with
  `beta` defaulting to Kolmogorov 11/3 (`burstfit.py:439-449`); `alpha` is a
  read-only property calling `alpha_from_beta` (`burstfit.py:460-463`).
- Closure implementation: `scattering/scat_analysis/turbulence.py` —
  `alpha_from_beta` (`turbulence.py:35-42`), constants `KOLMOGOROV_BETA = 11/3`,
  `BETA_THIN_SCREEN_MIN/MAX = 2.01/4.0`, `BETA_EXP_EPS = 0.02`
  (`turbulence.py:28-32`), inverse `beta_from_alpha_thin_screen`
  (`turbulence.py:45-52`), and legacy-α-bounds mapping
  `beta_bounds_from_alpha_bounds` (`turbulence.py:55-72`), which documents that
  **only α ≥ 4 is reachable** with β ∈ (2, 4]. Default joint bounds correspond
  to α ∈ [4, 6] (`turbulence.py:75-77`).
- Kolmogorov β = 11/3 → α = 22/5 = 4.4; square-law β = 4 → α = 4.
- Model hierarchy (`FRBFitter._ORDER`, `burstfit.py:1041-1047`;
  `burstfit_modelselect.py:54-59`): M0 `(c0,t0,gamma)` unresolved → M1 +`zeta`
  → M2 +`tau_1ghz` (β fixed at Kolmogorov default → α = 4.4) → M3 full
  `(c0,t0,gamma,zeta,tau_1ghz,beta,delta_dm)`.
- Regression tests: `tests/test_beta_comodel.py` (α derived on `FRBParams`;
  PBF/scaling coupling at and below β = 4). One-burst proof-of-concept:
  `analysis/beta_poc/run_beta_poc.py` (freya; β = 3.712 → α = 4.336 recovered
  in injection-recovery; its private kernel now aliases
  `turbulence.alpha_from_beta`, `run_beta_poc.py:46-51`).

### 4. Likelihoods

All on the 2D residual grid, per-channel noise from MAD
(`FRBModel._estimate_noise`, `burstfit.py:698-714`), dead channels masked via
`self.valid` (`burstfit.py:669-672`):

- Gaussian per-pixel χ² (`log_likelihood`, `burstfit.py:789-809`).
- Student-t (ν = 5 default) for outlier robustness
  (`log_likelihood_student_t`, `burstfit.py:1003-1032`).
- **Gain-marginal matched filter:** per-channel amplitude analytically
  marginalized (flat prior), so diffractive scintillation no longer inflates χ²;
  the profiled gain spectrum becomes the scintillation probe
  (`log_likelihood_gain_marginal`, `burstfit.py:811-848`; `gain_spectrum`,
  `burstfit.py:850-862`).
- **GP gain marginal:** gains given a Gaussian-process prior with Lorentzian
  frequency ACF of half-width Δν_d (the scintillation bandwidth), smooth
  envelope profiled by GLS, σ_g² by bounded 1-D ML
  (`log_likelihood_gain_marginal_gp`, `burstfit.py:864-943`;
  `_gp_amplitude_logL`, `burstfit.py:501-614`). Falls back verbatim to the flat
  marginal when Δν_d is None or too few live channels
  (`burstfit.py:897-898,922-924`).

### 5. Samplers and model selection

Two parallel selection paths over M0–M3, dispatched by `fitting_method`
(`pipeline/core.py:269-338`):

- **emcee + BIC** (default): `FRBFitter` wraps `emcee.EnsembleSampler`
  (`burstfit.py:1038-1177`), walkers = 8×ndim, `c0/zeta/tau_1ghz` sampled in
  log-space (`burstfit.py:1073`); `fit_models_bic` runs short chains
  (n_steps = 1500 default, `burstfit_modelselect.py:78`) and picks lowest
  BIC = −2 lnL_max + k ln n (`burstfit_modelselect.py:106-115`;
  `compute_bic`, `burstfit.py:1435-1437`).
- **dynesty + evidence:** `burstfit_nested.py` — `NestedSampler`, module
  defaults nlive = 500 / dlogz = 0.1 / rwalk (`burstfit_nested.py:302-311`),
  pipeline overrides nlive = 400 / dlogz = 0.5 (`pipeline/core.py:282-283`).
  Prior transform is log-uniform on `(c0, tau_1ghz, zeta)`, uniform otherwise
  (`burstfit_nested.py:167-193`); bounds come from
  `build_priors(..., absolute_bounds=True)` — deliberately **init-independent**
  so evidence-based selection cannot be skewed by the initial guess (rationale
  with an observed ΔlnZ ≈ 320 pathology: `burstfit.py:1408-1417`,
  `burstfit_nested.py:378-381`). Optional Gaussian β and log₁₀τ priors are
  folded into the log-likelihood rather than the prior transform
  (`burstfit_nested.py:263-273`). Winner by max log-evidence with pairwise
  Jeffreys-scale Bayes factors (`burstfit_nested.py:537-543`).
- Initial guess: band split into 4 subbands, per-subband EMG/exponential tail
  fits, log-space power-law regression τ ∝ ν^(−α) → α = −slope, clipped to
  [2, 6] (`burstfit_init.py:474-486`); fallback assumes α = 4.0
  (`burstfit_init.py:843,856,863`); converted to a β starting point by
  `beta_from_alpha_thin_screen` if α ≥ 4, else clamped to β = 4 with an
  explicit "MCMC starting point only" comment (`burstfit_init.py:905-914`).
  Optional Nelder-Mead MLE refinement clamps 0.1 < α < 8.0
  (`pipeline/optimization.py:37-40`, bound "carried over from the monolith").
- Convergence/quality: Gelman-Rubin R̂ (`burstfit.py:1232-1297`),
  autocorrelation burn/thin (`pipeline/optimization.py:96-134`), and
  χ²_red-driven PASS/MARGINAL/FAIL where weighted R² and normality are
  informational only — documented as deliberate to avoid spuriously failing
  faint bursts (`classify_fit_quality`, `burstfit.py:1452-1498`;
  `goodness_of_fit`, `burstfit.py:1501-1594`).

### 6. Joint CHIME+DSA fit (`burstfit_joint.py`)

The measurement that anchors the manuscript's scattering index uses the ~1 GHz
lever arm (CHIME 0.4–0.8 GHz, DSA 1.2–1.5 GHz):

- **Shared across telescopes: `tau_1ghz` and `beta`** — the first two entries
  of `JOINT_PARAM_NAMES` (`burstfit_joint.py:83-96`). Per-telescope (`_C`/`_D`
  suffixes): `c0, t0, gamma, zeta, delta_dm`. ζ stays per-band by default
  (rationale `burstfit_joint.py:26-29`).
- Additive log-likelihood `ll_C + ll_D`, each band evaluated as M3
  (`_JointLogLikelihood.__call__`, `burstfit_joint.py:607-628`).
- Sampler: dynesty, nlive = 600 / dlogz = 0.5 / rwalk
  (`burstfit_joint.py:877-880`), with an ndim ≥ 12 nlive warning
  (`burstfit_joint.py:972-976`).
- β bounds resolved from explicit → legacy α bounds → default (~α ∈ [4, 6])
  (`_resolve_beta_bounds`, `burstfit_joint.py:858-866`).
- **α is reported, not sampled:** derived percentiles appended from the β
  posterior, reporting-only (`_append_derived_alpha_percentiles`,
  `burstfit_joint.py:831-855`).
- Five likelihood variants (`burstfit_joint.py:930-968`): standard 12-vector;
  gain-marginal 8-vector; gain + scintillation-GP 10-vector (adds Δν_d);
  gain + shared frequency-evolving width (ζ(ν) = ζ_1GHz·ν^x_ζ, 8-vector) —
  carrying an explicit **x_ζ–α degeneracy caveat**: check posterior covariance
  before trusting α (`burstfit_joint.py:148-152`), and this variant is the CLI
  default (`burstfit_joint.py:884-886`); and multi-component N-per-band with a
  proper finite gain prior and ordered/min-separation transform
  (`burstfit_joint.py:183-192,195-367,539-593`).

### 7. Priors and floors on the index — layer inventory

Several layers constrain the index, in different vocabularies:

| Layer | Constraint | Anchor |
|---|---|---|
| Sampled box prior | β ∈ (2.01, 4.0) | `burstfit.py:1396` |
| Physical Gaussian prior | β ~ N(μ, σ); deprecated α-alias converts the mean via β(α) | `burstfit.py:1300-1350` |
| Orchestrator defaults | `alpha_mu = 4.4`, `alpha_sigma = 0.6`, optional `alpha_fixed` (CLI `--alpha-*`) | `pipeline/core.py:252-254,915-1073` |
| NE2001-informed path (pre-co-model, optional) | α ∈ [max(2, μ−3σ), min(6, μ+3σ)], defaults μ = 4.0, σ = 0.5 | `priors_physical.py:277-286,214-215` |
| Init clip | α ∈ [2, 6] (subband estimate), fallback 4.0 | `burstfit_init.py:486,843` |
| MLE refine clamp | 0.1 < α < 8.0 | `pipeline/optimization.py:40` |
| Gate floor (ADR-0004) | α ≥ 1.0 hard; [1.0, 2.0) = sub-Kolmogorov MARGINAL; rail flag within 0.1 of a bound | `analysis/scattering-refit-2026-06/gate_joint_committed.py:28-31` |
| Validation thresholds | GOOD 3.0–5.0, MARGINAL 1.0–6.0 (canonical single source) | `flits/fitting/VALIDATION_THRESHOLDS.py:50-54` |

### 8. Outputs and downstream lifecycle

- Per-burst single-telescope results serialize to `{name}_fit_results.json`
  (`build_safe_results`, `pipeline/core.py:38-79`; write at
  `pipeline/core.py:667-670`): `best_key`, `best_params`, per-model
  log-evidence/percentiles, `goodness_of_fit`, convergence stats.
- Joint-fit artifacts under `analysis/scattering-refit-2026-06/`: the mixed-PBF
  era `joint_json/*.json` (superseded for citation) and the canonical all-exp
  `_a1_fits/*.json` (fields include `alpha` percentiles, `tau_1ghz`,
  `beta_C/beta_D`, `pbf_*`, `log_evidence`, `gain_s2`, `shared_zeta`), plus
  paired PPC JSONs and per-burst gate verdicts `*_joint_gate.json`
  (aggregate `joint_gate_verdicts.{md,csv}`).
- **ADR-0004** (accepted 2026-06-24): joint-gate α floor lowered 1.5 → 1.0;
  [1.0, 2.0) reclassified sub-Kolmogorov MARGINAL rather than FAIL; motivated
  by johndoeII (α ≈ 1.37 mixed-era, 1.53 all-exp).
- **ADR-0005** (locked 2026-06-26): citable-α roster. Tier A (fully
  adjudicated): casey 2.40, wilhelm 2.56, chromatica 3.28, zach 3.32,
  freya 4.36. Tier B (provisional): johndoeII 1.53, oran 2.66, phineas 3.32.
  whitney 5.12 is the multiplicity exemplar. Machine-readable:
  `analysis/scattering-refit-2026-06/citable_alpha_roster.json`, consumed by
  `galaxies/foreground/tau_consistency.py` (path constant `:23`, roster read
  `:103-126`; the all-exp joint-fit α posteriors are loaded separately at
  `:201-226`) for the τ(ν) budget overlay.
- **Manuscript (Faber2026 repo):** no pipeline script emits the α/β LaTeX
  tables — they are hand-authored from the roster. `alpha_table.tex` is fully
  populated (8 rows matching ADR-0005); `beta_table.tex` is an **empty stub**
  ("values pending pipeline regeneration under the β-based co-model",
  `beta_table.tex:20-23`) — yet `sections/results.tex:84` inputs the empty
  `beta_table.tex` while the populated `alpha_table.tex` is not `\input`
  anywhere. Prose treatment of the closure and its sign caveat:
  `sections/intro.tex:20-28`, `sections/beta_scattering_methods.tex:32-47`,
  `sections/budget.tex:203-244`, `sections/discussion.tex:52-59`,
  `sections/results.tex:61-82,105-108`.

### Gaps and observations (light; design decisions deferred to planning)

> **Post-pin update (2026-07-02):** gaps 2–6 below (and the fixed-α degradation
> paths described in gap 4) were fixed upstream in dsa110-FLITS PR #98
> (`43f4c824`), which postdates the `6ce3e58` pin this doc describes. The
> descriptions below remain accurate for the pinned checkout. Gap 1 (the
> extended-medium β > 4 branch) and gap 7 (β-table regen) remain open.

1. **Central open science decision — α < 4 is unrepresentable in the
   implemented closure.** dα/dβ < 0 on the thin-screen branch, so α ≥ 4 always;
   yet 6 of the 8 roster sightlines have α < 4 (casey 2.40 … johndoeII 1.53).
   A shallow empirical α is therefore *not* a sub-Kolmogorov β; it signals
   extended-medium/thick-screen geometry, whose branch α = 8/(6−β) for β > 4 is
   documented in the repo's paper notes
   (`papers/Bhat_MultiFreqObsPulseBroadening_2004.md:55`) but unimplemented.
   Tracked as an open `@decision` (`.agents/deferred-tasks.md:37`; also
   ADR-0006 "future work" and `run_beta_poc.py:74-75,341-347`).
2. **Mixed multi-component wiring gap:** `build_mixed_model_order` appends
   `alpha_{idx}` for M3 components (`burstfit.py:1221-1223`) but the mixed
   likelihood branch reads `beta_{suffix}` with a Kolmogorov fallback
   (`burstfit.py:355`) — a sampled index parameter the model never reads.
   Unexercised: no test or config references the mixed path.
3. **`ncomp>1` shared-PBF path likely crashes:** its priors dict is built
   without a `"beta"` entry (`pipeline/core.py:443-478`) while `"beta"` is in
   the `M3_multi` order (`burstfit.py:1181`), so `_init_walkers` would
   `KeyError` (`burstfit.py:1099`). Independently of that, the branch also
   tuple-unpacks `sampler, mcmc_diag = fitter.sample(...)`
   (`pipeline/core.py:430,497`) while `FRBFitter.sample` returns a single
   sampler object (`burstfit.py:1177-1178`) — a second crash on the same path.
   Also unexercised (static analysis; not run).
4. **Deprecated α-alias σ untransformed:** `apply_physical_priors` converts the
   α-prior mean via `beta_from_alpha_thin_screen` but reuses σ_α as σ_β
   (`burstfit.py:1333-1335`); |dβ/dα| = 4/(α−2)² ≈ 0.694 at α = 4.4, so the
   effective β prior is ~44% wider than the stated α-space intent. Separately,
   `alpha_fixed` on the emcee paths produces `alpha_prior = (μ, None)`
   (`pipeline/core.py:404`; same pattern at `core.py:331` in the BIC model-scan
   branch and `core.py:461` in the multi-component branch), and
   `gaussian_prior` compares `sigma <= 0.0`
   (`burstfit.py:101`) → `TypeError` if that path is ever exercised (the
   nested path handles `alpha_fixed` correctly by removing β from the vector,
   `burstfit_nested.py:366-372`).
5. **Dead/stale α vocabulary:** orchestrator sets `priors["alpha"]` entries the
   sampler never reads (`pipeline/core.py:402-409,459-466`); several docstrings
   and the pipeline CLAUDE.md still say M3 "adds alpha". Cosmetic but
   confusing; the submodule is pinned, so fixes belong upstream in dsa110-FLITS,
   not here.
6. **Hardcoded ν⁻⁴ reference:** subband profile diagnostics fix α = 4
   (`burstfit_robust.py:275,326`) regardless of the fitted β — fine as a
   reference overlay, worth knowing when reading those plots.
7. **Manuscript mid-migration:** empty `beta_table.tex` is inputted while the
   populated `alpha_table.tex` is orphaned (§8) — blocked on the β-model
   pipeline re-run, consistent with the `@decision` items in
   `.agents/deferred-tasks.md:31,37`.

## Synthesis

The 2D fit is a per-channel amplitude × (Gaussian ⊛ PBF) forward model evaluated
on the full time–frequency grid against MAD-estimated per-channel noise, with
data reduced to z-scored, downsampled, burst-centered (optionally on-pulse
cropped) dynamic spectra. The scattering index is not an independent knob
anywhere in the current model: since ADR-0006, the turbulence index β is the
single sampled parameter, and it simultaneously fixes the τ(ν) scaling
(α = 2β/(β−2)) and the PBF shape (exponential at β = 4, heavy-tailed power-law
below). Two model-selection paths (emcee+BIC, dynesty+evidence) choose among
M0–M3, and the flagship measurement is the joint CHIME+DSA fit sharing
(τ_1GHz, β) across a ~1 GHz lever arm, with α derived from the β posterior for
reporting. Downstream, gate policy (ADR-0004) and the citable roster (ADR-0005)
were built in the older free-α era; the manuscript is mid-migration from the
populated α-first table to a β-first table awaiting a pipeline re-run.

The load-bearing tension: the implemented thin-screen closure can only produce
α ≥ 4, while most roster sightlines have empirical α < 4. Resolving that
(extended-medium β > 4 branch, or presenting shallow α as
family-misspecification evidence as the manuscript prose currently does) is the
open decision that any planning pass should treat as the first fork. Secondary
cleanups (mixed/multi-component wiring, α-alias σ transform, stale α
vocabulary) are upstream dsa110-FLITS work, not manuscript-repo work, since
`pipeline/` is a pinned submodule.

## References / Sources

- Code (pinned `pipeline/` @ `6ce3e58`):
  `scattering/scat_analysis/burstfit.py` (forward model, likelihoods, priors,
  emcee fitter, GOF), `turbulence.py` (β↔α closure),
  `burstfit_nested.py` (dynesty), `burstfit_modelselect.py` (BIC),
  `burstfit_joint.py` (joint CHIME+DSA), `burstfit_init.py` (initial guesses),
  `priors_physical.py` (NE2001 priors), `pipeline/{core,io,optimization,diagnostics}.py`
  (orchestration), `burstfit_robust.py`, `dm_preprocessing.py`,
  `analysis/scattering-refit-2026-06/gate_joint_committed.py` (gate),
  `analysis/beta_poc/run_beta_poc.py`, `tests/test_beta_comodel.py`.
- Decision records: `docs/adr/0004-l1-sub-kolmogorov-alpha-floor.md`,
  `docs/adr/0005-citable-alpha-roster.md`,
  `docs/adr/0006-beta-coherent-scattering-comodel.md`;
  `.agents/deferred-tasks.md`. Note: upstream dsa110-FLITS `main` (`2d30a4f9`,
  PR #97, 2026-07-01 — postdates the `6ce3e58` pin) adds a rationale addendum
  to ADR-0006 deriving why an exponential PBF (EMG kernel) forces α = 4 by
  definition and why free-α exponential fits measure family misspecification.
- Manuscript (Faber2026 @ `80f27c7`): `alpha_table.tex`, `beta_table.tex`,
  `sections/{intro,beta_scattering_methods,budget,discussion,results,observations}.tex`.
- External physics provenance cited *in code comments* (not independently
  reviewed): Cordes 2025 review §11.2; Bhat et al. 2004; Lorimer & Kramer 2005.
