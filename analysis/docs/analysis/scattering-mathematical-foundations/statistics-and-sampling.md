# Statistical and sampled-data foundations

Audit date: 2026-09-11 (local). Code: `353d1df49febe915d4f5a53ff034e9568ac4912e`.
Scope: mathematical audit and deterministic checks, not a fit campaign.
Equations below are derived explicitly; implementation references identify where
those assumptions enter. No assertion of real-burst calibration follows.

## 1. What the detector model must predict

Let p(t;ν) be the intrinsic intensity profile, h(t;ν) a causal propagation
response with integral one, and r(t;ν) the instrumental response. The continuous
mean profile is q=p*h*r. A time-bin average is

\[
K_{fj}(\theta)=\frac{1}{\Delta t}\int_{t_j-\Delta t/2}^{t_j+\Delta t/2}
\int W_f(\nu)q(t-t_0-\delta t_{\rm DM}(\nu);\nu,\theta)\,d\nu\,dt,
\qquad \int W_f(\nu)d\nu=1.
\]

This is a measurement-model contract, not a statement that the current code
performs both integrals. Bin-integrated counts instead omit 1/Δt and require
consistent amplitude units. Actual time stamps must be identified as bin centres
or edges. Channel response W, dedispersion, averaging and masking belong in this
contract; time-bin averaging and channel dispersion smearing are different effects.

Production evaluates sampled analytic profiles or a discrete convolution. Its
power-law lag grid starts at zero, normalizes the lag kernel over the finite grid,
then discards the convolution beyond the observation window
([burstfit.py](../../../scattering/scat_analysis/burstfit.py),
`gaussian_powerlaw_convolution`, lines 202–256). That is not automatically equal
to integrating q over bins. Normalizing a truncated kernel also changes its
amplitude convention as the window changes. Free amplitudes may absorb a scale
change in the best fit; marginalized likelihoods generally do not unless their
amplitude priors are transformed consistently (section 4). The check output
`normalized_piecewise_kernel_area` tests only the continuous infinite-domain
normalization, not this finite-grid/window approximation.

The dispersion approximation uses δt proportional to δDM ν^-2 and models
intra-channel broadening by a Gaussian with the variance of a boxcar:
σ_smear=Δt_DM/√12. Adding variances is exact for Gaussian convolution;
replacing a boxcar by that Gaussian is only a moment-matching approximation.
See `FRBModel._dispersion_delay`, `_smearing_sigma` and `_estimate_noise`
([burstfit.py](../../../scattering/scat_analysis/burstfit.py), lines 680–720).
Native-channel widths, coherent/incoherent dedispersion and real covariance
still require input-specific validation.

## 2. An exact exponential–Gaussian convolution

For h(t)=H(t)e^(-t/τ)/τ and a normalized Gaussian of mean μ and width σ,

\[
q(t)=\frac{1}{2\tau}\exp\!\left[\frac{\sigma^2}{2\tau^2}
-\frac{t-\mu}{\tau}\right]
\operatorname{erfc}\!\left[\frac{\sigma^2/\tau-(t-\mu)}{\sqrt2\sigma}\right].
\]

Complete the square inside ∫₀∞G(t-u;μ,σ)e^(-u/τ)du/τ to obtain this expression.
Its integral is one, mean μ+τ and variance σ²+τ². These moments follow by adding
independent Gaussian and exponential delays. The erfcx rewrite used in
`analytic_gaussian_exp_convolution` is algebraically equivalent away from its
numerical limit branches. A deterministic direct quadrature agrees to 1.11e-16
at the checked point. This is an equation check, not proof of all extreme limits
or of bin integration. The numerical σ>100τ Gaussian shortcut is an approximation.

An exponential scale is a well-defined phenomenological parameter even when the
physical propagation law is not exponential. In a wrong response family its
fitted value is not necessarily the physical mean delay.

## 3. Gaussian noise and proper amplitude marginalization

For one channel, stack T time bins in d and N component templates in the T×N
matrix K. Assume

\[
d=Kg+\epsilon,\quad \epsilon\sim\mathcal N(0,C),\quad
g\sim\mathcal N(0,S),\quad g\perp\epsilon.
\]

Integrating the proper Gaussian gain prior gives the exact normalized density

\[
d\mid\theta\sim\mathcal N(0,\Sigma),\qquad \Sigma=C+KSK^T,
\]
\[
\log L=-\tfrac12[d^T\Sigma^{-1}d+\log\det\Sigma+T\log(2\pi)].
\]

A nonzero prior mean gives mean Km and leaves the covariance unchanged.
The current zero-centred Gaussian allows negative component gains: a modeling
choice, not a physically positive intensity prior. A positive/truncated prior
would require a different integral and normalization.

For C=σ²I and S=s²I, write M=KᵀK, b=Kᵀd and A=M+σ²I/s². The matrix inverse
and determinant identities give

\[
\log L=-\tfrac12\left[\frac{d^Td-b^TA^{-1}b}{\sigma^2}
+T\log(2\pi\sigma^2)+\log\det(I+s^2M/\sigma^2)\right].
\]

This equals the full-rank implementation in
[`_gain_marginal_multi_band_impl`](../../../scattering/scat_analysis/burstfit_joint.py)
(lines 214–392). Independent evaluation of the two formulas agrees exactly at
the retained full-rank check. The s²/σ² ratio is dimensionally accompanied by
KᵀK; changing template units requires changing gain-prior units.

**Noise assumptions remain unvalidated for the real data.** Known, independent
Gaussian errors are assumptions; σ estimated from the same cropped data is a
plug-in estimate. Residual time/channel correlations, tail-contaminated noise
windows, baselines and selection of masks can invalidate that likelihood.
Marginalizing gain does not by itself establish a calibrated chi-squared test.

### A new, explicit limitation: rank truncation changes the model

The proper covariance remains positive definite whenever C is positive definite,
even when K has collinear columns. There is no mathematical need to discard a
small template direction merely because M is ill-conditioned. The docstring’s
claim that singular M makes the solved system diverge does not apply to
A=M+σ²I/s²: for fixed positive σ² and finite positive s², A is positive definite
and has a finite inverse. Finite-precision conditioning still needs care; it is
not a justification for unbounded statistical approximation error. The code replaces
all but the leading direction when λ_min(M)/λ_max(M)<1e-6.
The relevant contribution to the covariance is s²λ/σ², not that ratio alone.

Counterexample through the actual helper: K=diag(1,10^-4), d=(0,100), σ²=1,
s²=10^12. The smaller M eigenvalue is 10^-8, but its prior-induced variance is
10^4. Exact log L=-20.7586; implemented rank-one fallback log L=-5015.6534,
a difference of -4994.8948. Thus the fallback is not the stated full Gaussian
marginal for all inputs. This does not establish its impact on any real burst;
it establishes that the approximation needs its own error bound and diagnostics.
At exact rank one the omitted zero directions contribute nothing; the concern
is nonzero directions discarded at a fixed threshold.

## 4. Improper priors, normalization and evidence

For a scalar gain with formal flat density c, completing the square yields

\[
L_{\rm flat}=c(2\pi\sigma^2)^{-(T-1)/2}(K^TK)^{-1/2}
\exp[-(d^Td-(d^TK)^2/(K^TK))/(2\sigma^2)].
\]

The arbitrary c cannot define an absolute Bayesian evidence. It can cancel in
some comparisons with identical nuisance measures/dimensions and fixed data,
not universally across component counts or amplitude conventions.
The shared-width implementation drops the full data normalization
−T log(2πσ²)/2. That term cancels for fixed σ, data and masks; comparisons with
different data/noise or a fully normalized path need it restored consistently.
See `log_likelihood_gain_marginal`
([burstfit.py](../../../scattering/scat_analysis/burstfit.py), lines 817–856).

Under K→aK the formal flat integral gains a 1/|a| factor unless the gain prior's
measure transforms. Under a proper Gaussian, equivalent predictions require
s→s/|a|. Therefore “free gain absorbs normalization” is a best-fit statement,
not an automatic statement about evidence or posterior shape.

For full column rank N and large s²,

\[
\log L_{s^2}=\text{terms independent of }s^2-\frac N2\log s^2+o(1).
\]

The sign is **negative**. The helper's docstring instead writes a positive term
and claims it cancels in any evidence difference. Neither statement holds in
general, especially if N differs. Increasing s² by 100 for N=2 changes the checked
log likelihood by -4.60517004, agreeing with -log 100. The production equations
have the correct determinant sign; the docstring interpretation is wrong.
No production code or comments are edited by this audit.

If s² is optimized for each θ, L(θ,s²_hat(θ)) is a profiled objective. Integrating
it over θ is not the hierarchical evidence
∫L(θ,s²)π(θ)π(s²)dθds². A fixed stated variance or proper hyperprior has a defined
meaning; optimization does not supply the missing prior measure.

## 5. Priors are part of the scientific model

A uniform unit-cube coordinate transformed as
x=exp[log a+u log(b/a)] gives π(x)=1/[x log(b/a)] on [a,b], not a flat prior in x.
The normalizing bounds matter for evidence and weakly resolved τ.
See `_JointPriorTransform`, `_joint_prior_spec_gain_shared_zeta`,
`_joint_prior_spec_gain_multi`, `build_priors` and `_clamp_t0_priors_to_window`.
Some arrival-time bounds depend on initial fits/windows; this data dependence
must be reported rather than described as a wholly pre-specified prior.

For α=2β/(β−2), β=2α/(α−2) and |dβ/dα|=4/(α−2)².
A uniform β prior therefore induces a nonuniform α prior. Production additionally
maps the entire β≥3.98 interval to α=4 and an exponential response. For a uniform
[3,4] β prior, that branch carries prior probability 0.02 concentrated at one
response family. Posterior mass there depends on this chosen prior weight.
An edge fraction is not a Bayes factor or an astrophysical diagnosis.

Sorting N independent uniform arrival times produces density N!/W^N on the
ordered region, not 1/W^N. The minimum-spacing transform first shrinks the usable
width to W-(N−1)δ, then sorts and adds offsets; it specifies a uniform ordered,
separated prior with that normalization when usable width is positive. It also
excludes closer components by prior choice. The fallback for nonpositive usable
width collapses times and no longer represents an N-separated-component model.
See `_JointPriorTransformOrdered` (lines 630–686). Component-count evidence must
use the induced normalized prior; do not add/remove a factorial by intuition.

## 6. What nested sampling establishes—and what it does not

Define X(l)=∫1[L(θ)>l]π(θ)dθ. For a proper prior the evidence is
Z=∫₀¹L(X)dX. With n independent uniform draws inside the constrained prior, the
largest remaining fractional volume has distribution P(t<x)=x^n, hence
p(t)=n t^(n−1) and E(log t)=−1/n. This order-statistic derivation explains the
shrinkage rule and also its assumption: constrained draws must actually cover
the allowed region. A random-walk implementation approximates that condition.

The repository uses dynesty static nested sampling, random-walk proposals and
weighted posterior summaries (`fit_joint_scattering`, lines 1190–1240).
A stopping tolerance on estimated remaining evidence is not proof that a mode
was found, that interval coverage is correct, or that the forward model is
physical. Preserve weighted samples and likelihoods; test branch-restricted
integrations or alternate exploration only when diagnosing a mode concern.
A better conditional optimum is not larger integrated probability.

Primary software reference: [dynesty source repository](https://github.com/joshspeagle/dynesty)
(the project pins 3.1.0 in `analysis/pyproject.toml`). Its upstream citation is
Speagle (2020), MNRAS 493, 3132. The publisher/ADS route encountered human
verification during this audit; the original article was not inspected here.
The mathematical explanation above is the explicit derivation, not a claim to
have checked every statement against that inaccessible paper.

## 7. Identifiability and validation design

For an exponential plus Gaussian, the first two moments contain μ+τ and σ²+τ².
With μ and σ free, separation of τ relies on higher-order shape information;
poor time resolution can remove that information. A narrow posterior can then
reflect the assumed kernel, nuisance priors or bounds, rather than a uniquely
measured delay. Two-band α_emp is a logarithmic scale ratio; if one scale is only
bounded, an ordinary symmetric α interval is generally not warranted.

Validation must separate:

1. Equation checks against integrals/matrix identities and limiting cases.
2. Discretization checks against high-resolution bin/channel integration.
3. Sampler checks on a *fixed* valid likelihood, with known targets and modes.
4. Repeated generative calibration: draw parameters from the declared prior,
   simulate independently, infer, and test posterior rank/interval behavior.
5. Model adequacy: independent physical alternatives and observed residuals.
6. Real-burst identification: assess nuisance, window, resolution and prior effects.

Self-consistent simulation/recovery is necessary but can share the same error.
Nine selected recoveries do not execute steps 3–6. Fixing a continuity defect
would not by itself validate the physical response or statistical calibration.

## Reproduce the bounded checks

From the repository root:

```sh
MPLCONFIGDIR=/tmp/faber2026-mpl analysis/.venv/bin/python analysis/docs/analysis/scattering-mathematical-foundations/checks.py
```

[Check output](check-results.json). These are deliberately small equation checks
and a counterexample; they access no burst data and run no fitting campaign.
