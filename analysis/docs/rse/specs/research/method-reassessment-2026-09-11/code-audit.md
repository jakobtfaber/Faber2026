# Code audit: two-band scattering fitter

Date: 2026-09-11; corrected after independent review. Production revision:
237502d455dcdb9f691600b8773d589406962e52. Paths below are relative to `analysis/`.
This is a capability/limitation audit, not a diagnosis of each real sightline.

## Current findings

| Finding | Source | Interpretation and next check |
|---|---|---|
| Beta >=3.98 dispatches to the analytic exponential; alpha also jumps to 4 | `scattering/scat_analysis/burstfit.py:772`; `turbulence.py:39` | Whole-model discontinuity reproduced. Sampling alone is not its only cause. Test matched metrics across the full forward-model switch. |
| Beta box [3,4] cannot express alpha<4 | `turbulence.py:39` | Selected shallow-scaling truths can mismatch. A rail does not identify the real sightline's cause. |
| Shared-width likelihood uses an improper flat gain prior | `burstfit_joint.py:783`; `burstfit.py:817` | Differs from a fixed proper Gaussian prior. Do not compare evidences across incompatible amplitude measures. |
| Multi-component gain variance is profiled unless fixed | `burstfit_joint.py:359`; `burstfit_joint.py:863` | Fixed-variance comparison needs explicit common normalization and sensitivity checks. |
| Power-law kernel is normalized on a finite time grid | `burstfit.py:237` | Window dependence needs controlled checks; no sign or magnitude of real-burst beta bias is established here. |
| Noise estimate uses cropped outer quarters | `burstfit.py:704` | Tail contamination is a risk to test against independent off-pulse samples. |
| Residual autocorrelation flattens channels | `burstfit.py:1584` | Inspect channelwise residuals before treating the statistic as a tail-shape check. |
| Shared intrinsic-width law can trade against scattering | `burstfit_joint.py:522` | Need width/prior sensitivity, not an assumed causal explanation. |

The synthetic branch magnitudes are retained in `results/kernel-branch-discontinuity.json`.
Earlier 0.04% shape-only and tail-truncation percentages lacked a retained common-metric
calculation and are not used as quantitative evidence in the corrected decision.
Beta controls both scale frequency dependence and kernel shape. The present study
does not cleanly decompose their information contributions.

## Priors and likelihood paths

The shared-width path has a coupled beta/tau law, per-band arrival time and
residual dispersion, and a frequency-dependent intrinsic width. The multicomponent
path has a different nuisance structure. See `burstfit_joint.py:783`, `:863`,
`:970` and `:1062`. Changing paths to obtain a proper gain prior changes more than
one modeling assumption; a comparison must state that confounding.

The independent review checked the harness Gaussian gain marginalization against
a direct covariance calculation to 1.8e-15. That verifies the harness algebra,
not production calibration or validity of its prior for the intended headline.

## Current command-line capabilities

`scattering/studies/joint-refits/run_joint_fit.py:116` accepts a seed and `:392`
forwards it. The earlier “CLI passes no seed” assertion was stale and is withdrawn.
Repeatability still requires recording configuration, software, input identities,
and any separate posterior-resampling random state.

The alpha flags at `run_joint_fit.py:144-150` are deprecated beta-bound aliases;
they cannot turn this path into an alpha<4 exponential fit. `--proper-gain-prior`
and `--gain-s2` select/configure a beta-coupled component likelihood. They do not
implement independent per-band reference scales and the full proposed nuisance
contract. `radio_pipeline/fitting/joint_burst.py:594` and `:685` contain a separate
free-alpha/shared-1-GHz-scale implementation, not a validated replacement on the
campaign entry point. The proposed new path and gates are in [the memo](decision-memo.md).

## Simulation and historical records

`scattering/studies/beta-campaign/sim_gate.py:42` currently imports a retired
`analysis/analysis/beta_poc/run_beta_poc.py` location. The current driver is
`scattering/studies/beta-proof-of-concept/run_beta_poc.py`. Any earlier “passed”
simulation-gate report is historical, not proof that the current gate runs.
Repair is outside this evidence-only change.

The study now has five exact-production controls. Both thin controls use the
same production kernel for injection and fitting. Their beta offsets are real
saved outcomes, but a truth/model sampling-convention mismatch is not demonstrated.
The 29-case harness uses a different likelihood/kernel/nuisance setup; its nine
interior recoveries cannot certify production inference. Neither suite diagnoses
the actual railed sightlines.

Historical campaign runtimes, likelihood values and physical attributions in the
[history ledger](history-ledger.md) remain historical evidence, with incomplete
independent source verification. No historical free-alpha values are rehabilitated.

## Follow-up checks

1. Complete forward-model continuity (kernel, alpha law, normalization and sampling).
2. Explicit headline likelihood, priors and deterministic summaries.
3. Repeated generative calibration, competing-geometry checks and both-band predictions.
4. Actual-sightline cause diagnosis with fixed inputs and declared nuisance sensitivity.

Family 3 is a provisional recommendation. Production, manuscript and archived
fit products are not modified by this audit.
