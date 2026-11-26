# Decision memo: method class for the two-band scattering measurement

Date: 2026-09-11; revised after independent review. Ticket: [method-reassessment-01](../../../wayfinder/tickets/method-reassessment-01-scattering-fit-method-class.md).

## Recommendation and readiness

**Recommend family 3 provisionally:** per-band exponential pulse-broadening
scales and a descriptive two-band index as the intended headline; retain a
beta-coupled fit only as a separately validated thin-screen consistency test.
This is a direction for implementation, not a validated measurement method.
No fitted value or methods text is promoted to the manuscript. Ticket 01 stays
open because the charter asks for actual sightline causes, which these synthetic
controls do not establish.

The evidence supports two narrower conclusions. Selected model mismatches can
produce boundary posteriors, and an interior beta can occur for a mismatched
truth. The production forward model also has a discontinuity at beta=3.98.
Neither result proves the cause of a particular real-burst fit failure.

The harness completed 29 fits (arms a/b/c: 10/10/9), plus five production
controls. Nine selected thin-screen harness cases contain the injected beta
inside their 95% posterior interval; that is limited self-consistency evidence,
not calibration of those intervals or clearance of production inference.

## Evidence base

| Evidence | Scope |
|---|---|
| [Code audit](code-audit.md) | Current model/prior limitations; historical observations distinguished from current capabilities. |
| [History ledger](history-ledger.md) | Campaign history; full historical and reference verification remains incomplete. |
| [Generated results](injection-recovery-results.md) | Saved fits, corrected derived classifications, and diagnostic figures. |
| [Referee methods review](referee-methods-review.md) | Candidate-family assessment; a recommendation, not empirical validation. |
| [Independent review](codex-review.md) | Initial BLOCK, corrections and final-state review status. |

## Production discontinuity: measured behavior and limits

At beta=3.98, production switches both the convolution implementation and the
frequency exponent: alpha jumps from a left limit of 4.020202 to exactly 4.
Thus the two evaluations differ in sampling, finite-window normalization,
kernel shape and frequency scaling. The diagnostic cannot attribute the whole
jump to bin-centre sampling.

| band | sample time [ms] | tau at band centre [ms] | raw maximum difference / global peak | middle-channel centroid offset [samples] | shifted, area-normalized middle-channel maximum difference / peak |
|---|---|---|---|---|---|
| CHIME/FRB | 0.0716 | 0.2219 | 0.1696 | -0.381 | 0.0137 |
| DSA-110 | 0.0188 | 0.0074 | 0.0522 | -0.303 | 0.0332 |

Source: `results/kernel-branch-discontinuity.json`, beta 3.979 versus 3.981,
tau at 1 GHz 0.0288 ms. The first and last difference columns use different
normalizations and channel selections; they are not an isolated before/after
sampling correction. The earlier comparison against a 0.04% shape difference
used another metric/grid and has been withdrawn from this memo.

Conditional optimization of tau and the two arrival times gives log-likelihood
steps +7.2, -0.6 and -6.4 for the alpha-3, alpha-4 and thin controls when other
nuisances are fixed at truth. Starting from their posterior-median vectors gives
+3.7 (alpha 3), -1.4 (alpha 4), -4.2 (alpha 4.4), -5.7 (thin, 0.05 ms),
and -19.0 (thin, 0.2 ms). These are conditional profile differences,
not integrated posterior odds. Width and dispersion parameters remain fixed.

The alpha-3 run has 81% of equal-weight samples above beta=3.95 and none above
3.98. But original weighted mass above 3.99 is positive: 4.51e-105 (alpha 3)
and 2.73e-79 (alpha 4). Therefore “never visited” was false. Negligible posterior
weight, prior volume, missed modes and sampler behavior need separate tests;
trapping is a hypothesis, not a demonstrated mechanism.

Hold production consistency-test interpretation near the boundary until the
**complete forward model**, including alpha, is continuous under one declared
sampling/normalization convention. A follow-up should test a common maximum-error
metric across resolved and unresolved tails, aiming below 0.1% of peak. The
existing boundary tests pass but explicitly permit the alpha jump; shifting the
time grid alone cannot satisfy the stronger requirement.

## Arm a: limited thin-screen recovery

The harness uses its own continuous kernel, proper Gaussian gain prior, one
shared width law and one residual dispersion parameter. Production differs.
Most configurations share one noise seed; only beta=3.67, tau=1 ms has four
noise realizations. The following are selected recoveries, not a calibration
experiment.

| truth | tau_1GHz | beta posterior (16, 50, 84 percent) | class | truth in 68 percent | truth in 95 percent |
|---|---|---|---|---|---|
| thin, beta 3.30 | 1 ms | 3.295, 3.302, 3.308 | interior | yes | yes |
| thin, beta 3.30 | 0.15 ms | 3.281, 3.292, 3.302 | interior | yes | yes |
| thin, beta 3.67 | 1 ms (seed 1) | 3.666, 3.673, 3.680 | interior | yes | yes |
| thin, beta 3.67 | 1 ms (seed 2) | 3.670, 3.677, 3.684 | interior | no (upper edge) | yes |
| thin, beta 3.67 | 1 ms (seed 3) | 3.658, 3.664, 3.671 | interior | yes | yes |
| thin, beta 3.67 | 1 ms (seed 4) | 3.652, 3.659, 3.666 | interior | no | yes |
| thin, beta 3.67 | 0.15 ms | 3.643, 3.653, 3.662 | interior | no | yes |
| thin, beta 3.90 | 1 ms | 3.893, 3.902, 3.911 | interior | yes | yes |
| thin, beta 3.90 | 0.15 ms | 3.855, 3.870, 3.886 | interior | no | yes |
| exponential, alpha 4 (control) | 1 ms | 3.984, 3.993, 3.998 | ceiling-rail (63 percent within 0.01 of 4) | n/a | n/a |

The three short-scale cases are **0.15 ms**, despite rounded filenames ending
`tau1e-04`. Their 1.4-GHz scales are about 0.83, 1.04 and 1.15 samples.
All nine thin cases are interior; truth is inside the 95% interval in 9/9 and
the 68% interval in 5/9. The short-scale beta medians are 0.008–0.030 low.
The cause has not been isolated. These results do not clear production inference.

## Arm b: synthetic mismatch stress tests

F1 is the coupled thin-kernel harness; F2 uses an exponential kernel with free
frequency exponent. Both retain the harness nuisance model. The legacy `thick`
case is a **generic heavy-tail stress test**, not a verified physical
extended-medium kernel: the implemented density integrates to 2 and has infinite
mean. Its retained divisor 1.2337 is an arbitrary scale convention. The
composite contains a thin tail with infinite mean too, so no summed-mean-delay
index exists; the previous 4.16 claim is withdrawn.

Original injected arrays and fitted outputs are unchanged. Derived classifications
remove the composite alpha/shape target and heavy-tail/composite tau coverage.
For the heavy-tail case, alpha=4 is only the exponent of its input scale law.
It is not a mean-delay index. Original case identifiers are retained for traceability.

| truth | F1 (thin-screen, beta) | F1 class | F2 (exponential, alpha) | F2 class | other parameters at a prior edge |
|---|---|---|---|---|---|
| exponential, alpha 3.2 (shallower than nu^-4) | 4.000, 4.000, 4.000 | ceiling-rail (100 percent within 0.01 of 4) | 3.188, 3.198, 3.209 (truth 3.2 covered) | interior | none |
| exponential, alpha 5.0 (steeper than nu^-4) | 3.595, 3.602, 3.609 (implied alpha 4.50) | interior | 4.977, 4.991, 5.005 (truth 5.0 covered) | interior | none |
| generic heavy-tail stress, scale exponent 4.0 | 3.157, 3.161, 3.165 (implied alpha 5.45) | interior | 4.007, 4.021, 4.035 (truth 4.0 covered) | interior | residual DM at the upper box edge (100 percent) in both models |
| two screens, exponential alpha 4 convolved with thin beta 3.67 | 3.000, 3.000, 3.000 | floor-rail | 5.995, 5.998, 5.999 | ceiling-rail (alpha box) | residual DM at the upper box edge (100 percent) in both models |
| thin beta 3.67 plus an unmodelled second component (40 percent, +0.45 ms, redder) | 3.665, 3.672, 3.680 (truth 3.67 covered) | interior | 4.257, 4.270, 4.283 (input scale exponent 4.40 not covered; descriptive index differs by 0.13) | interior | none |

These controls show that a rail can indicate mismatch, while an interior beta
does not prove a thin screen. The heavy-tail and composite arrays also drive
residual dispersion to its prior edge. All-parameter boundary checks and
posterior predictions are therefore required. The single second-component
geometry tested here cannot settle real component-count ambiguities.
The finite CHIME window truncates the longest tails; conclusions apply to these
exact grids, not arbitrary observing windows or sightlines.

## Arm c: signal-to-noise and gain-prior scale

Nine new cases plus the reused arm-a baseline appear below; the scale-10 baseline is shown in both sweeps. The signal-to-noise
100 baseline uses scale 10, matching the 30/300 cases. Scale denotes the prior
standard deviation relative to the injected gain root-mean-square amplitude;
its square is the variance.

| sweep | value | model | shape posterior (16, 50, 84 percent) | truth in 95 percent |
|---|---|---|---|---|
| band-summed peak S/N | 30 | F1 | beta 3.650, 3.672, 3.697 | yes |
| | 100 | F1 | beta 3.666, 3.673, 3.680 | yes |
| | 300 | F1 | beta 3.669, 3.671, 3.673 | yes |
| gain-prior scale s / g_rms | 0.1 | F1 | beta 3.826, 3.835, 3.843 | no (0.17 high) |
| | 1 | F1 | beta 3.667, 3.674, 3.681 | yes |
| | 10 (reused signal-to-noise 100 baseline above) | F1 | beta 3.666, 3.673, 3.680 | yes |
| | 100 | F1 | beta 3.666, 3.672, 3.679 | yes |
| | 0.1 | F2 | alpha 4.203, 4.215, 4.227 | no (0.18 low) |
| | 1 | F2 | alpha 4.298, 4.312, 4.325 | no (0.08 low) |
| | 10 | F2 | alpha 4.299, 4.313, 4.326 | no (0.08 low) |
| | 100 | F2 | alpha 4.299, 4.312, 4.325 | no (0.08 low) |

In this configuration the narrow gain prior shifts beta by +0.17 and F2 alpha
by -0.18 relative to its input exponent. Scales 1–100 span **two decades** and
leave the medians nearly unchanged. This motivates sensitivity checks; it does
not choose or validate the prior for a different production headline model.

## Exact production controls

The thin controls inject with the same production forward model used for fitting.
Their offsets therefore cannot be assigned to a truth/model sampling mismatch.
Five current records use 200 live points and the shared-width production path.

| truth | true alpha | beta posterior (2.5, 16, 50, 84, 97.5 percent) | resampled mass above 3.95 / 3.98 | class (production rule) | derived alpha | flip check: ln L step across 3.98 with tau and arrival times re-optimised |
|---|---|---|---|---|---|---|
| exponential, alpha 3.0 | 3.0 | 3.911, 3.946, 3.969, 3.977, 3.980 | 0.81 / 0.00 | interior | 4.03 | +3.7 (higher conditional optimum; not posterior odds) |
| exponential, alpha 4.0 (the model's own end-member) | 4.0 | 3.753, 3.804, 3.860, 3.918, 3.968 | 0.07 / 0.00 | interior | 4.15 | -1.4 (conditional check only) |
| thin screen, beta 3.67 (DSA-band tau about 0.6 sample) | 4.40 | 3.506, 3.538, 3.571, 3.606, 3.637 | 0.00 / 0.00 | interior | 4.55 | not diagnostic (posterior far from switch); step -5.7; truth 3.67 lies outside the 95 percent interval, 0.10 low |
| exponential, alpha 4.4 (same scaling as the thin control, no power-law tail) | 4.40 | 3.673, 3.708, 3.748, 3.786, 3.824 | 0.00 / 0.00 | interior | 4.29 | not diagnostic (posterior far from switch); step -4.2; the thin-screen equivalent of alpha 4.4 is beta 3.67, which lies outside the 95 percent interval, 0.08 high |
| thin screen, beta 3.67, tau_1GHz 0.2 ms (DSA-band tau 2.4 samples) | 4.40 | 3.605, 3.620, 3.640, 3.659, 3.674 | 0.00 / 0.00 | interior | 4.44 | not diagnostic (posterior far from switch); step -19.0; truth 3.67 sits at the upper end of the 95 percent interval, 0.03 low |

The 0.10-to-0.03 beta offset reduction when increasing tau is observed, but these
two runs do not separate noise, resolution, nuisance-prior volume, gain treatment
and sampling error. No production convergence or repeated-generative calibration
has been established. The alpha-4.4 exponential case and thin control have different
kernels despite similar scale laws; opposite beta offsets are observations, not
a clean decomposition of shape versus frequency-ratio information.

## Family ranking

| Family | Assessment | Remaining limitation |
|---|---|---|
| 1. Coupled beta with additional physical kernels | Highest implementation/calibration cost | Additional geometry does not by itself resolve all scaling or identification failures. |
| 2. Per-band exponential scales, descriptive index | Simplest intended headline; explicit model dependence | Not implemented/validated by this study; an exponential scale is not universally a physical delay. |
| 3. Family 2 plus separately validated thin-screen test | Provisional preference: preserves a conditional physical interpretation | Requires both headline validation and a repaired/calibrated comparison path. |

Provisional ranking: 3 > 2 > 1. The study tests neither the complete family-3
contract below nor competing physical geometries, and does not establish that
family 3 is science-ready.

## Intended implementation contract and deferred gates

The intended future entry point is a dedicated per-band exponential path in
`analysis/scattering/studies/joint-refits/run_joint_fit.py`, backed by a new
likelihood in `scattering/scat_analysis/burstfit_joint.py`. **It does not exist
in the required form today.** Current alpha flags merely map to beta bounds;
proper-gain switches route to a different beta-coupled component model. The
separate `radio_pipeline` free-alpha implementation is not this contract.

Provisional contract for that follow-up, to be tested before campaign adoption:

- Independent positive exponential scales at 600 MHz and 1.4 GHz, with log-uniform
  bounds 1e-4–1e3 ms. Within each band use tau(nu)=tau_ref(nu/nu_ref)^(-alpha_band),
  independent alpha_band uniform [2,6]. This adds within-band nuisance exponents;
  the empirical cross-band index is derived from the two reference scales,
  not identified with either within-band exponent. Compare fixed exponent 4 as
  a sensitivity case. These choices are provisional priors, not findings.
- Per-band/component intrinsic widths (log-uniform 1e-4–1e3 ms), constant within
  each band initially; independent per-band residual dispersion uniform
  [-0.1,0.1] pc cm^-3; ordered arrival times uniform in the declared fit window.
  Component counts are discrete candidate models, with both plausible counts
  retained when unresolved. Test width laws and enlarged dispersion bounds.
- Proper Gaussian channel-gain prior with a fixed variance declared before
  evidence comparison, under one common amplitude normalization. Select its
  scale through the follow-up's injection/sensitivity study; the current harness
  does not justify a universal value. Compare one decade either side.
- Derive alpha_emp=ln(tau_C/tau_D)/ln(1.4/0.6) from joint posterior draws.
  Unresolved tails produce limits, with injection-tested resolution criteria;
  an arbitrary “few samples” threshold is not an established limit procedure.
- Repair and test full production continuity before using the beta-coupled
  comparison. Match gain/nuisance conventions where comparisons require them.
  Prior-bound sensitivity must use a mathematically defined model outside the
  original beta box, not unsupported extension of the present mapping.

| Validation gate | Current state / required follow-up |
|---|---|
| Equation and implementation | Gain algebra checked in the harness; implement and independently test the stated headline likelihood and complete kernel continuity. |
| Recovery and calibration | Selected synthetic recoveries only; repeated injections across prior draws/noise and real-burst morphology, including unresolved tails, before interval/limit claims. |
| Prior sensitivity | Limited harness gain sweep; test headline and comparison priors, bounds, widths, dispersion and component counts. |
| Posterior predictions | Required in both bands, including tail beyond three scales where observed; not established for the proposed model. |
| Competing geometry | Required explicit alternative-geometry comparison or justified non-identifiability; generic heavy-tail arrays do not satisfy it. |
| Actual sightline causes | Unresolved; complete per-sightline diagnostics before assigning mismatch, inference or resolution causes. |
| Independent final review | Initial BLOCK resolved by independent final review for provisional draft publication only; scientific validation remains open. |

Only after these gates may the manuscript report reference scales/limits and a
flagged descriptive index. Beta or a count of thin-screen-consistent sightlines
requires the separate validated comparison. No abstract/population beta claim
follows from this study.

## Scope and remaining work

Eleven scattering claim rows remain blocked; chromatica remains documented_fail.
Ticket 07 stays parked. Neither production fixes nor real-burst reruns are part
of this evidence correction. The charter's actual-sightline cause assignment is
explicitly **unfinished**, not silently waived; ticket 01 remains open.

Follow-ups: complete-model continuity and regression tests; implement/test the
headline contract; repeated calibration and actual-sightline diagnosis; repair
`scattering/studies/beta-campaign/sim_gate.py` importing the retired
`analysis/analysis/beta_poc/run_beta_poc.py` path (current driver lives at
`scattering/studies/beta-proof-of-concept/run_beta_poc.py`). Historical ledger
discrepancies remain unresolved. Manuscript methods text is a separately scoped
change after validation and owner scientific review.

## Reproducibility

From `analysis/`, using the project environment:

```sh
export MPLCONFIGDIR=${TMPDIR:-/tmp}/mpl
.venv/bin/python docs/rse/specs/research/method-reassessment-2026-09-11/injection_recovery.py --check-kernel
.venv/bin/python docs/rse/specs/research/method-reassessment-2026-09-11/injection_recovery.py --nproc 11 --nlive 400
.venv/bin/python docs/rse/specs/research/method-reassessment-2026-09-11/production_path_injection.py --nproc 2 --nlive 200
.venv/bin/python docs/rse/specs/research/method-reassessment-2026-09-11/kernel_switch_check.py
.venv/bin/python docs/rse/specs/research/method-reassessment-2026-09-11/make_report.py
```

Existing fit records are skipped. For interpretation-only regeneration use
`injection_recovery.py --refresh-classifications` followed by `make_report.py`.
Fit outputs remain original; classification changes do not rewrite their
posterior samples. Historical harness equal-weight resampling was unseeded;
new runs seed it, so exact reproduction of old resampled quantiles is not
promised. Production records use a simulation seed plus one for nested sampling.
Older missing tau metadata is resolved explicitly through the named case inventory
when rebuilding flip controls. No long fits were rerun for these corrections.

## Review status

Initial independent review: **BLOCK**. [Review record](codex-review.md).
The revised evidence is **APPROVED for provisional draft publication only** by
[the independent Claude review](claude-final-review.md). Both requested textual
corrections are applied. Scientific validation is not approved; ticket 01 remains open.
