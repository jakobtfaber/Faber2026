# Scattering physics: source audit and derivation

Audit date: 2026-09-11. Scope: mathematical foundations, no fits or production changes.

**Findings:** an exponential response does not uniquely identify a density-spectrum index β=4. The production exponential/power-law join is an approximation, not the exact thin-screen solution. The reassessment's heavy-tail kernel is Williamson's **short-time asymptote**, extrapolated outside its domain. Its divisor 1.2337 has a physical origin in the **full** solution; it does not give the truncated formula a finite mean.

## Sources actually inspected

Page numbers below are printed pages; arXiv references use preprint pagination. PDFs were retrieved through the Traycer browser and inspected locally; Williamson pp. 61–62 were also checked visually because extracted equations were incomplete.

| Source | Verified location and scope |
|---|---|
| [Lambert & Rickett (2000), *Radio Scintillation due to Discontinuities in the Interstellar Plasma Density*](https://arxiv.org/abs/astro-ph/9911366), [PDF](https://arxiv.org/pdf/astro-ph/9911366), [published DOI](https://doi.org/10.1086/308505) | Full text. Eq. (1), p. 2: spectrum with inner/outer cutoffs; Eq. (6), pp. 5–6: density spectrum to phase structure function; Eqs. (7)–(8), p. 6: literal β=4 has outer-scale/logarithmic dependence. §4, p. 7: inertial-range bandwidth exponent applies to screen and extended geometries. This is the **2000 paper**, not Lambert & Rickett 1999. |
| [Cordes & Lazio (2001), *Anomalous Radio-Wave Scattering from Interstellar Plasma Structures*](https://arxiv.org/abs/astro-ph/0005493v2), [PDF](https://arxiv.org/pdf/astro-ph/0005493v2), [DOI](https://doi.org/10.1086/319442) | Full text. Eqs. (6)–(11), p. 6: angular distribution to delay distribution and geometry. Eqs. (13)–(17), p. 7: isotropic Gaussian gives exponential. Eqs. (19)–(24), pp. 7–8: finite screen, truncated exponential and flattening of mean-delay scaling. |
| [Williamson (1972), *Pulse broadening due to multiple scattering in the interstellar medium*](https://doi.org/10.1093/mnras/157.1.55), [NASA ADS PDF](https://adsabs.harvard.edu/pdf/1972MNRAS.157...55W) | Full text. Assumptions pp. 56–58; mean Eq. (5), p. 59; full thick-slab response Eq. (12), p. 61; **small-time approximation immediately below Fig. 6, p. 62**; full-sightline response Eq. (21), p. 65; Laplace transforms p. 68. Publisher route encountered security verification; ADS PDF succeeded. |
| [Cordes et al., *Fundamental Noise Processes for Pulsar Timing Arrays*, author-hosted page](https://hosting.astro.cornell.edu/~cordes/FNP/), [2026 June 19 PDF](https://hosting.astro.cornell.edu/~cordes/FNP/FNP_LRR_revision_2026June19.pdf) | Full relevant sections. Eqs. (9.2)–(9.8), pp. 64–65: structure function and image. Eq. (11.1), p. 83: image to temporal response; Fig. 40 and §11.2, p. 85: inner-scale limits and approximate crossover. Author page says under review; this is an author-hosted review/preprint, **not verification of every original paper it cites**. |

The repository's `Cordes2025` bibliography entry supplies neither URL nor version. The accessible author version is dated **2026 June 19**, with page updated 2026 August 28. Do not silently call that inspected document the 2025 version.

Not independently verified: Ostashov & Shishov's original tail/crossover derivation. The [publisher record](https://doi.org/10.1007/BF01033759) exposes metadata and references, but its article body requires subscription access. It dates volume 20, pp. 581–585 to **1977**, whereas the Cordes review cites 1978. Lambert & Rickett (1999), [DOI 10.1086/307181](https://doi.org/10.1086/307181), was located, but the publisher full-text route returned a bot challenge. Neither paper's equation numbers are asserted here. Lee & Jokipii (1975) and Williamson (1975) were not independently inspected.

## 1. Density spectrum → phase differences

Use β only for the **three-dimensional electron-density spectrum**, not a temporal spectral exponent or Williamson's geometric β. Let

\[
P_{\delta n_e}(q)=C_n^2q^{-\beta},\qquad q_o\ll q\ll q_i,
\quad \ell_o\sim q_o^{-1},\quad\ell_i\sim q_i^{-1}.
\]

Factors of 2π in scale definitions depend on the wavenumber convention. For cold-plasma phase at wavelength λ, a slab contributes

\[
\phi(\boldsymbol x)=-r_e\lambda\int dz\,\delta n_e(\boldsymbol x,z).
\]

The overall sign does not affect the structure function. Under statistical homogeneity and the long-path/short-longitudinal-correlation approximation, integration through the slab selects the spectrum at longitudinal wavenumber zero. For isotropy,

\[
D_\phi(b)=\langle[\phi(\boldsymbol x+\boldsymbol b)-\phi(\boldsymbol x)]^2\rangle
\propto \lambda^2{\rm SM}\int_0^\infty dq\,q^{1-\beta}[1-J_0(qb)],
\qquad {\rm SM}=\int C_n^2 dz.
\]

This is Lambert & Rickett Eq. (6), pp. 5–6, with constants suppressed. A geometrically thin screen need not be thinner than a density correlation length: their approximation assumes slab thickness larger than the outer scale but much smaller than source distance. A different longitudinal projection needs a new derivation. For a spherical incident wave, transverse separation must be projected to the screen; source/screen distances cannot be omitted when predicting amplitudes.

Set u=qb. The dimensionless integral converges at zero only when β<4, because its integrand behaves as u^(3−β); at infinity it converges when β>2. Therefore the cutoff-independent result is

\[
\boxed{D_\phi(b)\propto\lambda^2{\rm SM}\,b^{\beta-2},\qquad 2<\beta<4,\quad\ell_i\ll b\ll\ell_o.}
\]

This convergence check is derived here from the inspected source integral. It is not a license to apply the power law at β=4 or β>4.

## 2. Phase differences → angular image → time response

For Gaussian phase increments, their characteristic function gives the ensemble field coherence

\[
\Gamma(b)=\exp[-D_\phi(b)/2].
\]

Gaussian **phase increments** are an additional statistical assumption; they do not mean Gaussian **scattering angles**. The normalized angular density of screen deflections is the two-dimensional Fourier transform

\[
B(\boldsymbol\vartheta)=\frac{k^2}{(2\pi)^2}\int d^2b\,
e^{-ik\boldsymbol b\cdot\boldsymbol\vartheta}\Gamma(b),\qquad k=2\pi/\lambda.
\]

The transform relation is Cordes et al. Eq. (9.8), p. 65; normalization and choice of screen coordinates are explicit here. In the ideal scale-free limit, define Dφ(r_diff)=1, m=β−2 and x=b/r_diff. Then

\[
B(\vartheta)=\frac{k^2r_{\rm diff}^2}{2\pi}\int_0^\infty x\,dx\,
J_0(k r_{\rm diff}\vartheta x)e^{-x^m/2}.
\]

Let D be source–observer distance, d the observer–screen distance and D_eff=d(D−d)/D. For the screen **deflection** angle ϑ, geometric delay is t=Aϑ² with A=D_eff/(2c). The observed image angle instead satisfies θ=(D−d)ϑ/D. Mixing those angles gives an incorrect geometric factor. Cordes & Lazio Eqs. (7)–(11), p. 6, use the complementary source–screen distance convention.

The temporal pulse-broadening density is

\[
p(t)=\int d^2\vartheta\,B(\boldsymbol\vartheta)\delta(t-A\vartheta^2)
=\frac{\pi}{A}B(\sqrt{t/A}),\qquad t\ge0
\]

for an isotropic screen. This follows directly from Cordes & Lazio Eq. (9), and agrees with Cordes et al. Eq. (11.1), p. 83. It assumes an unresolved point source, small-angle geometric excess paths, no significant extra plasma delay across those paths, and an ensemble intensity envelope. It is not a model of individual interference speckles.

Thus a thin screen specifies geometry, **not one universal p(t)**. The Hankel transform specifies the exact idealized response; a matched exponential/power-law curve does not replace that derivation.

## 3. Frequency scaling: what α measures

When the diffractive scale remains in the inertial interval,

\[
r_{\rm diff}\propto\lambda^{-2/(\beta-2)},\qquad
\vartheta_d\sim(kr_{\rm diff})^{-1}\propto\lambda^{\beta/(\beta-2)},
\]
\[
\boxed{\tau_{\rm scale}\propto\vartheta_d^2\propto\nu^{-\alpha},\qquad
\alpha=\frac{2\beta}{\beta-2},\qquad2<\beta<4.}
\]

Here τ_scale is a consistently defined response scale, for example a fixed quantile or a core width in a self-similar family. It is **not automatically the mean delay**. The inverse β=2α/(α−2) is valid only in this regime. Kolmogorov β=11/3 gives α=22/5=4.4.

Required conditions: strong scattering for the adopted broadened-envelope description; stationary spectral strength and geometry across frequency; diffractive scales well inside the same inertial interval; fixed image-shape parameters; no changing transverse aperture or additional competing scale. Isotropy is sufficient for the scalar transform above; a fixed anisotropy need not destroy the frequency exponent. This derivation assumes Euclidean distances; cosmological applications require the appropriate screen-frame wavelength, distance factors and time dilation, not a change to the local exponent by assertion.

**The exponent alone does not establish a thin screen.** Lambert & Rickett (2000), §4 p. 7, explicitly obtain the same inertial-range scintillation-bandwidth exponent in screen and extended geometries. A fixed distributed medium can preserve the exponent while changing the response shape and amplitude. Consequently “extended medium” and “β>4” are not synonyms.

## 4. Endpoint, inner/outer scales, and exponential counterexamples

| Regime | Consequence |
|---|---|
| r_diff ≪ ℓ_i | Expand 1−J₀(qb)≈(qb)²/4: Dφ∝λ²b²∫q^(3−β)dq. With a finite inner cutoff this yields r_diff∝λ⁻¹, angular width ∝λ², and core delay scale ∝λ⁴. This can happen at **β=11/3**. Cordes et al. Eq. (9.6), p. 65 and Fig. 40, p. 85 explicitly show this limit. |
| β=4 with finite outer scale | The integral has logarithmic outer-scale sensitivity. Lambert & Rickett Eqs. (7)–(8), p. 6 give Dφ∝λ²b² ln[1+4/(q_ob)²] as an approximation to the exact Bessel expression. Literal β=4 is not an exact global square law. |
| β>4 | The small-q part is outer-scale dominated. The cutoff-free b^(β−2) argument fails; directly continuing α=2β/(β−2) is unjustified. A saturated α=4 branch would be a separately declared effective model, not a β measurement or a uniquely derived extended geometry. |
| Finite ℓ_i, otherwise inertial core | The ideal power-law tail eventually cuts off. The mean can be finite even when the core remains close to the zero-inner-scale response. Fig. 40 and §11.2, p. 85 of Cordes et al. demonstrate this distinction. |
| Finite transverse screen | Cordes & Lazio Eqs. (22)–(24), p. 8 give a truncated exponential with a frequency-independent geometric cutoff; the mean-delay exponent approaches zero in the narrow-screen limit. The untruncated exponential's τ and the truncated mean are different observables. |

If Dφ(b)=Cb² over the relevant baselines, Γ is Gaussian and B is an isotropic Gaussian. Substitution into the delay integral gives p(t)=τ⁻¹e^(−t/τ). That implication is exact in the idealized model. Its converse is **not** “β=4”: density spectra with a dominant inner scale or effectively one correlation scale produce the same square-law limit. Exact global square-law structure functions are themselves idealizations; a stationary finite-variance field's structure function eventually saturates.

Likewise, a late exponential tail is not unique to a thin screen: Williamson's thick-slab and full-sightline solutions both have exponential late tails (pp. 61–65). Anisotropy, refraction, distributed scattering and multiple screens alter the full response. Arbitrarily convolving two isolated-screen kernels is not automatically the correct spatial two-screen model: geometric paths are conditioned to reach the observer, as in Cordes & Lazio Eqs. (4)–(5), p. 5.

Free exponential scales in each observing band are therefore permissible **descriptive parameters**. Their ratio does not by itself identify β, and a descriptive index below four alone does not prove which physical assumption failed.

## 5. Production piecewise response versus physical solution

Inspected code: [`turbulence.py`](../../../scattering/scat_analysis/turbulence.py) and [`gaussian_powerlaw_convolution` in burstfit.py](../../../scattering/scat_analysis/burstfit.py). Before discrete normalization it implements, with s=t/τ and s_c=2 ln[2/(4−β)],

\[
g_\beta(s)=\begin{cases}e^{-s},&s\le s_c,\\
e^{-s_c}(s/s_c)^{-\beta/2},&s>s_c.
\end{cases}
\]

Cordes et al. §11.2 p. 85 gives the angular asymptote B(ϑ)∝ϑ⁻β and hence p(t)∝t^(−β/2). Crucially, its crossover statement is an approximation **as β approaches four from below**. It does not supply a normalized, exact, all-β piecewise Green function. The original Ostashov–Shishov crossover derivation remains inaccessible in this audit.

Independent consequences of the displayed implementation:

- Its infinite-domain dimensionless area is Nβ=1−e^(−s_c)+e^(−s_c)s_c/(β/2−1), not one. A physical density would be gβ(t/τ)/(τNβ). Production instead normalizes over a finite sampled lag grid before convolution and crops the convolution; its result is not generally globally unit-normalized.
- The first derivative usually jumps at s_c: log slopes −1 and −β/(2s_c). The exact Hankel-transform solution has no imposed join.
- A direct analytic counterexample is β=3. Then Γ(b)=exp[−b/(2r_diff)], whose transform gives p(t)=[2t_*]⁻¹(1+t/t_*)^(−3/2), t_*=A/(4k²r_diff²). This is normalized, smooth and algebraic from the onset; it is not the implemented piecewise function. Its 1/e time is (e^(2/3)−1)t_*. This identity is derived here from the preceding Hankel transform, not attributed to an uninspected paper.
- For 2<β<4 and no inner cutoff, the tail is normalizable but ∫tp(t)dt diverges. A τ fitted to this family cannot be called a mean delay. A finite observing window does not turn the infinite physical mean into a finite one; it changes the measured/truncated quantity.
- The code changes both kernel and α at β≥3.98. The unsaturated left-limit α is 4.020202…, while the branch sets four. That is a numerical model switch, not an identified physical transition. Its effects are documented in the reassessment; they are not remeasured here.

Before a β fit supports a turbulence claim, compare its complete forward response against the actual transform solution under a declared inner-scale and geometry model. Self-injection with the same surrogate can establish recovery within that surrogate, but cannot establish the physical mapping.

## 6. The heavy-tail stress kernel has a specific missing completion

The reassessment [`pbf_thick`](../../rse/specs/research/method-reassessment-2026-09-11/injection_recovery.py) evaluates

\[
h(t)=\sqrt{\frac{\pi\tau_w}{4t^3}}\exp\left[-\frac{\pi^2\tau_w}{16t}\right],\qquad
\tau_w=\tau_{\rm input}/1.2337.
\]

This is **exactly the small-time expression on Williamson (1972), p. 62, below Fig. 6**. It describes the early response of a thick scattering slab near the source or observer, with slab extent small compared with the source–observer distance. His assumptions include angular Brownian diffusion, small angles, strong multiple scattering, and geometric delays dominating direct group-delay fluctuations (pp. 56–58). It is not a general Kolmogorov solution, nor the full-sightline solution in his Eq. (21).

Williamson's full Eq. (12), p. 61 is

\[
p_W(t)=\sqrt{\frac{\pi\tau_w}{4t^3}}
\sum_{n=1,3,5,\ldots}(-1)^{(n-1)/2}n\,
e^{-n^2\pi^2\tau_w/(16t)}
=\frac{4}{\pi\tau_w}\sum_{n=1,3,5,\ldots}(-1)^{(n-1)/2}n\,e^{-n^2t/\tau_w}.
\]

The first representation converges rapidly at small t; the second exposes the large-t exponential. Keeping only n=1 in the **small-t series** gives the implemented h. At large t, the omitted terms are essential; dividing h by two repairs area only, not its wrong late-time shape.

Independent derivation/check, consistent with Williamson's Laplace transform on p. 68:

\[
\widetilde h(s)=2e^{-(\pi/2)\sqrt{\tau_ws}},\quad
\widetilde p_W(s)=\operatorname{sech}[(\pi/2)\sqrt{\tau_ws}],
\]
\[
\int h\,dt=2,\quad\langle t\rangle_h\text{ diverges};\qquad
\int p_W\,dt=1,\quad\langle t\rangle_W=\frac{\pi^2}{8}\tau_w.
\]

Since π²/8=1.233700550…, **1.2337 is the full thick-slab mean/decay-scale ratio**, also obtained from Williamson Eqs. (5) and (13). It is not arbitrary historically; applying it to h fails because h lacks the rest of the solution. In the full-sightline geometry, Williamson Eq. (21), p. 65 and p. 68 instead give transform π√(τs)/sinh[π√(τs)] and mean π²τ/6. Geometry must be stated before naming a conversion factor.

This corrects the interpretation, not the saved synthetic arrays: the existing heavy-tail experiment remains a misspecified-kernel stress test. It cannot be reported as recovery or rejection of the complete Williamson medium. No replacement fit has been run.

Independent numerical check: integration of the two convergent series gives area 1.000000000000000 and mean 1.233700550136170 at τ_w=1. Numerical Laplace integrals at s=0.1, 1 and 4 agree with the stated hyperbolic-secant transform within 10⁻¹⁰. These are equation checks, not burst fits.

## Consequences for the reassessment

Read as task context: [decision memo](../../rse/specs/research/method-reassessment-2026-09-11/decision-memo.md), [referee methods review](../../rse/specs/research/method-reassessment-2026-09-11/referee-methods-review.md), and [final independent review](../../rse/specs/research/method-reassessment-2026-09-11/claude-final-review.md). Their previous scientific assertions were not used as source verification.

1. Retain the distinction between descriptive per-band exponential scales and physical β inference.
2. Replace “exponential uniquely β=4” with the conditional square-law/isotropic-image derivation.
3. Call the production joined response a surrogate until its physical approximation error is quantified; fixing numerical continuity alone cannot validate it.
4. Describe the heavy-tail error as extrapolation of a verified short-time asymptote. Record the full-solution origin of 1.2337; do not call its origin arbitrary.
5. Keep an observed width, an exponential decay constant, a response quantile, and a mean delay distinct. Means and their two-band ratios do not exist for the current untruncated heavy-tail families.
6. Neither a boundary posterior nor an interior β identifies geometry, turbulence, or the cause of a real-burst mismatch without an adequate forward model and checks against competing explanations.

No scientific-fit validation, manuscript promotion, production correction, or inference about an individual sightline is established by this source audit.
