# Referee assessment of the scattering method (2026-09-11)

Role: physical-soundness reviewer, acting as a skeptical ApJ referee on FRB scattering.
Read: `sections/budget.tex` L123–400, `sections/results.tex` L275–304,
`sections/emg_alpha4_appendix.tex`, `sections/twoscreen_formalism.tex`,
`sections/discussion.tex` L52–88, `main.tex` abstract L30–86, and
`analysis/CONTEXT.md` (fit-trust reset L160–200, geometry-adjudicated β L282–329,
scint→scattering coupling L330–369). Campaign outcomes are taken from the project record as stated in the task and
were not re-derived here.

## Verdict

**Major revision of method framing. The β-coupled thin-screen co-model is not
a defensible headline measurement for this sample; its rails are predictable
from the model's own construction.** The physics motivating it is correct as
far as it goes, but the model can express only one failure mode (a posterior
piled on a prior wall), and roughly 8 of 12 posteriors are on or near a wall.
That is a diagnosis of the thin-screen inertial-range assumption, not a
measurement of turbulence.

**Recommended method family: the hybrid (family 3).** Report per-band
pulse-broadening times under a fixed one-sided exponential kernel, a
descriptive two-band index with explicit mismatch flags, and upper limits
where a band is unresolved. Keep the β-coupled fit as a per-sightline
closure test ("consistent / not consistent with a single thin inertial-range
screen"), quoting a β only where the interior posterior survives the checks in
§2 below.

## Terms used once

- *Pulse-broadening function (PBF)*: the impulse response of the scattering
  medium; the observed profile is the intrinsic pulse convolved with it.
- *Structure function* $D_\phi(\rho)$: mean-square phase difference between two
  rays separated by $\rho$; a power-law density spectrum with index $\beta$
  gives $D_\phi\propto\rho^{\beta-2}$ in the inertial range.
- *Inner scale* $l_i$: the smallest turbulent eddy; below it $D_\phi$ becomes
  quadratic (square-law) whatever $\beta$ is.
- *Diffractive scale* $r_d$: the separation at which $D_\phi=1$; it shrinks as
  scattering strengthens and as frequency drops.
- *Thin screen* vs *extended medium*: scattering concentrated at one distance
  vs spread along the path; both change the PBF shape.
- *Railed posterior*: one whose mass piles against a prior boundary.

## 1. Is the β-coupled co-model defensible as the headline?

**No, for five compounding reasons.**

**(a) The mapping is one-parameter where the physics has at least three.**
`sec:jointfit` (L172–206) derives both the PBF shape and
$\alpha=2\beta/(\beta-2)$ from $\beta$ alone. That is exact only for a single,
infinite, isotropic thin screen with negligible inner scale, in the inertial
range. Each dropped condition breaks the mapping differently:

- *Inner scale.* When $r_d<l_i$, $\alpha\to4$ and the PBF becomes exponential
  regardless of $\beta$ (the paper says this, L216–223). But $r_d$ shrinks with
  scattering strength, so the sightlines with the best-measured $\tau$ are the
  ones most likely to be inner-scale dominated. The `endpoint-degenerate`
  label (L224–226) correctly refuses to call a $\beta=4$ pile-up a square-law
  detection, but it names one physical cause for a rail that has several.
- *Finite or extended screen; multiple screens.* A finite (truncated) screen
  gives $\alpha<4$, down to $\approx3$ (Cordes & Lazio 2001); an extended
  medium changes the PBF onset and tail (Williamson-type kernels) with $\alpha$
  nominally unchanged, so shape mismatch is absorbed into $\tau$ in each band
  and therefore into the inferred index; two screens with different $\tau(\nu)$
  make the effective index frequency-dependent and the PBF a convolution of two
  kernels, not a member of the family. All three routes produce empirical
  $\alpha<4$, which the model forbids by construction (L338–339). Every such
  sightline must rail at $\beta=4$. The DM budget itself supplies at least
  four sightlines with foreground halos (`sec:results-budget` L48–54), so the
  two-screen case is not hypothetical here.
- *Intrinsic morphology.* `sec:multicomp` (L371–379) states that an unmodeled
  component biases $\beta$; it does not address the second, larger degeneracy:
  an intrinsic width $\zeta$ that varies with frequency within a band (common
  in FRBs) mimics a $\tau(\nu)$ trend, and the gain marginalization removes
  amplitude structure but not shape structure. With $\zeta$ frequency-independent
  per band, the index is partly an intrinsic-width index.

**(b) The [3,4] box makes both rails predictable.** With $\alpha$ confined
to $[4,6]$, any sightline whose empirical two-band ratio implies
$\alpha\lesssim4$ (routes above, or an unresolved DSA-band $\tau$ held near the
sample time) rails at $\beta=4$; any whose ratio implies $\alpha\gtrsim6$
(CHIME-band $\tau$ inflated by unresolved components or residual DM smearing,
or DSA-band $\tau$ pushed to zero) rails at $\beta=3$. The observed
3+3 ceiling, 2 floor, 4 interior split is exactly what a bounded
reparameterization of $\alpha$ on $[4,6]$ produces on a sample with the usual
literature spread of empirical indices ($\sim$3–5). The lower bound $\beta=3$
is not physically motivated in the text (L337–339, "by default"); a
$\beta=3$ rail ($\alpha=6$) has no interpretation offered anywhere.

**(c) The shape information is too weak to rescue the index.** From
`eq:tailmass`, the power-law tail of a Kolmogorov PBF ($\beta=11/3$) carries
$\approx12\%$ of the kernel beyond $s_c=2\ln6\approx3.6\,\tau$, where the
exponential has fallen to $e^{-3.6}\approx3\%$ of peak. Seeing that tail
against noise needs profile S/N of order 100 after gain marginalization,
which few of these bursts have in both bands. The $\beta$ constraint therefore
comes almost entirely from the cross-band $\tau$ ratio, i.e. from precisely
the quantity contaminated by (a).

**(d) The lever arm cannot separate $\beta=3.67$ from $\beta=4$ at plausible
S/N.** $\beta=3.67$ gives $\alpha=4.4$; $\beta=4$ gives $\alpha=4$. Over the
full 0.4–1.4 GHz span, $\Delta\ln\tau=0.4\times\ln3.5\approx0.5$; between the
band centres (0.6 and 1.4 GHz) it is $0.4\times\ln2.33\approx0.34$, a 40%
difference in the $\tau_{\rm CHIME}/\tau_{\rm DSA}$ ratio. A $3\sigma$
separation needs the combined fractional error on the two $\tau$ values below
$\approx11\%$, with the intrinsic width, component count, and residual DM
fixed. At $\alpha\approx4$ the DSA-band $\tau$ is $\sim30\times$ smaller than
at 600 MHz; for it to be measured to 10% it must span many samples, which
pushes the 400 MHz $\tau$ to tens of ms, where CHIME components become
unresolvable and the component ambiguity dominates. The window in which both
bands resolve $\tau$ cleanly is narrow, and band-limited bursts shrink the
effective lever arm below the nominal band edges. The manuscript never states the time resolution of the fit
products; it must.

**(e) The α-free diagnostic already answers the question.** If a fixed
exponential kernel with $\alpha$ free is preferred by evidence on several
sightlines, the data are saying $\alpha\ne\alpha(\beta)$. Within the paper's
own logic (L189–194) that is evidence against thin-screen inertial-range
closure on those sightlines. The co-model is then a rejected hypothesis, which
is a legitimate and interesting result, but not a headline measurement.

What the co-model *is* good for: a clean null hypothesis. A sightline whose
posterior sits interior with white residuals in both bands and survives §2
supports "consistent with a single thin inertial-range screen with
$\beta\approx x$." Four such candidates exist; that is this model's ceiling.

## 2. Would I accept a β from a posterior at the box wall?

**No.** A railed posterior's location is set by the prior edge, not the data.
It is evidence that the model cannot accommodate the sightline within its
allowed range, and nothing more. Minimum I would demand before *any* $\beta$
(interior or railed) is quoted:

1. **Prior sensitivity.** Refit with the box moved and widened (e.g. $[2.5,4]$,
   and $[3,5]$ with a saturated plateau $\alpha=4$, exponential PBF for
   $\beta\ge4$). If the mode moves with the wall, it is not a measurement. The
   plateau variant turns the ceiling into an interior region, so posterior mass
   on the plateau vs the inertial branch becomes a reportable odds ratio.
2. **Simulation-based calibration per sightline.** Inject $\beta\in\{3.3, 3.67,
   3.9, 4.0\}$ with that burst's morphology, S/N, channelization, masking and
   time resolution; show rank statistics are uniform and, specifically, that a
   true $\beta=3.67$ does *not* rail at 4 at that burst's S/N. Without this the
   "interior" label is untested.
3. **Posterior predictive checks in both bands**: residual dynamic spectra,
   collapsed profiles, and a dedicated tail check at $t>3\tau$ where the family
   members differ.
4. **Evidence comparison against the fixed-exponential α-free model** at one
   fixed gain-prior variance $s^2$, with the sensitivity of $\Delta\ln Z$ to
   $s^2$ tabulated. Where the α-free model wins, the co-model is rejected for
   that sightline and no $\beta$ is quoted.
5. **An extended-medium alternative** (a thick-medium kernel, or a two-kernel
   convolution for the four foreground-halo sightlines) fitted as a competing
   family, so a rail can be attributed to geometry rather than left as
   "endpoint-degenerate."
6. **A resolution check**: the DSA-band $\tau$ posterior compared with the
   product sample time and intra-channel smearing; if $\tau_{\rm DSA}$ is
   within a few samples, the sightline yields a limit, not an index.

## 3. What this dataset can defensibly claim

- **Per-band $\tau$ under a fixed exponential kernel**, quoted at each
  band's reference frequency (600 MHz and 1.4 GHz), never extrapolated to
  1 GHz, with uncertainties that include the $\zeta$–$\tau$ degeneracy and the
  component-count ambiguity as a systematic (both candidate counts fitted,
  spread reported). This is the community standard (CHIME catalog, ASKAP/CRAFT,
  DSA-110 papers) and is directly comparable.
- **Upper limits** where $\tau$ is unresolved in a band (posterior consistent
  with the sample time), stated as limits.
- **A descriptive two-band index** $\alpha_{\rm emp}=\ln(\tau_C/\tau_D)/
  \ln(\nu_D/\nu_C)$ with flags: `alpha<4` (single thin inertial-range screen
  excluded; finite/extended/multi-screen or morphology), `count-ambiguous`,
  `one-band-limit`. The sub-band slopes (`sec:subband`) belong here as
  consistency checks, exactly as L279–292 already frames them.
- **Attribution by amplitude, not index.** The comparisons the paper actually
  needs (`sec:scattering` L126–130, `sec:results-budget` L86–91) are
  $\tau_{\rm obs}$ vs $\tau_{\rm int}$ from the halo model and vs the NE2025
  Galactic prediction. Those need a $\tau$ at a frequency, not a $\beta$.
- **Screen-location constraints from $\tau\,\Delta\nu_d$** only where a
  certified decorrelation bandwidth and a $\tau$ exist for the *same burst and
  band*: currently FRB 20220506D (DSA) and FRB 20240203A (CHIME). The product
  needs no $\alpha$ at all if $\tau$ is taken in the same band as $\Delta\nu_d$;
  `sec:disc-screen-attribution` L64–69 should say so.

Wording I would accept: "We measure the pulse-broadening time in each band
under a one-sided exponential kernel. The ratio of the two gives a descriptive
two-band index $\alpha_{\rm emp}=x\pm y$. Because the exponential kernel
corresponds to a square-law structure function, $\alpha_{\rm emp}$ is not a
turbulence spectral index; values inconsistent with $\alpha\ge4$ indicate that
a single thin screen with an inertial-range spectrum does not describe the
sightline. A $\beta$-coupled thin-screen fit is consistent with N of 12
sightlines." No $\beta$ in the abstract unless that N survives §2.

## 4. Ranking the three method families

| Family | Referee acceptability | Honesty | Effort |
|---|---|---|---|
| 1. β-coupled, add extended kernel | Medium. Reviewers will demand the §2 calibration for both geometries and expect "not identifiable at this S/N" on most sightlines; the $\alpha\ge4$ floor and inner-scale degeneracy remain. | Medium: still cannot express $\alpha<4$ except by rejection. | High: new kernels, evidence grids, SBC ×2. |
| 2. Per-band τ + empirical α, fixed exponential kernel, mismatch flags | High. This is how the field reports; referees will ask for the $\alpha<4$ caveat and the $\zeta$–$\tau$ treatment. | High, once "descriptive" is stated and the methods stop calling it "physically inconsistent." | Low: the α-free machinery exists. |
| 3. Hybrid: family 2 as headline, β-coupled as closure test | Highest. Numbers are comparable; the physical claim is proportionate; rails become a finding ("N of 12 sightlines are not described by a single thin inertial-range screen") rather than a measurement. | Highest. | Moderate: family 2 plus items 1, 2, 4, 6 of §2 on the interior candidates only. |

**Recommendation: family 3.** It keeps the paper's genuine methodological
contribution (the co-model as a stated null hypothesis, and the demonstration
that a free-α exponential fit is a different model with a different meaning)
without letting a model whose rails are predictable carry the results. Family 1 becomes worthwhile only if two-screen scintillation constraints
supply geometry priors for most sightlines; today they exist for two.

## 5. Methods statements to change regardless of method choice

1. `sec:jointfit` L189–194 and abstract L49–54: "physically inconsistent ...
   biases the inferred scaling." Inconsistent *as a turbulence model*; as a
   descriptive kernel it is the literature standard. Rewrite to distinguish
   descriptive index from spectral index; the abstract cannot carry this
   sentence if per-band $\tau$ is the headline.
2. L163–170 and abstract L48–49: "Co-detection breaks this degeneracy." Only
   when $\tau$ is resolved in both bands and $\zeta$ is separately
   constrained; state the conditions and the S/N estimate of §1(d).
3. L179–180, L200–201: "for a thin screen" / "under the thin-screen
   assumption." Enumerate all assumptions: single, infinite, isotropic thin
   screen, negligible inner scale, inertial range; state that the mapping is
   one-to-one only under all of them.
4. L216–227: rename `endpoint-degenerate` to a neutral `boundary` (or
   `closure-not-determined`) and list every route to a $\beta=4$ pile-up
   (inner scale, finite screen, extended medium, multiple screens, unresolved
   DSA-band $\tau$, morphology). Add the $\beta=3$ boundary and its routes.
5. L337–339: justify the lower bound $\beta=3$ physically or call it a
   convenience; remove "by default" or list every box used.
6. L339–342: a factor of 4 in induced prior density on $\alpha$ is not
   "mildly favoring"; state it as a factor of 4 and report the prior-sensitivity
   refit of §2 item 1.
7. L328–332: $s^2$ "profiled at its maximum-marginal-likelihood value" makes
   the evidence a profile, not a marginal, likelihood. State the single fixed
   $s^2$ used for all evidence comparisons and tabulate $\Delta\ln Z(s^2)$,
   since the record shows component-count evidences move with it.
8. L360–365: a Durbin–Watson window of 1–3 admits lag-1 autocorrelation of
   $\pm0.5$; tighten or justify. State whether $\chi^2_{\rm red}<0.3$ rejects.
9. L378–379, L389–397: state the evidence threshold for adding a component;
   where visual audit overrides evidence, say so per sightline and carry the
   4-vs-6 ambiguity as a $\tau$ systematic rather than a resolved choice.
10. L397–399: "A clean single-component co-detection ... validates the
    method." One clean case validates nothing about the multi-component or
    railed cases; replace with injection-recovery results.
11. L208–214: the model can signal an incomplete closure only by piling on a
    prior wall; say that explicitly.
12. State the time and frequency resolution of every fit product, per band and
    per product type (coherent vs incoherent), next to the smearing formula at
    L237–252.
13. `emg_alpha4_appendix.tex` L20–22, L71, L82–89: "self-consistency
    requirement rather than a modeling choice" and "commits a fit to
    $\tau\propto\nu^{-4}$ by definition" overstate; the kernel is a shape, the
    scaling a separate assumption. Cite the finite-screen and multi-screen
    routes to $\alpha<4$ as physical alternatives, not as "violated
    assumptions." Minor: the piecewise family in `eq:pbf-family` is not unit-
    normalized as written (at $\beta=3$ the pieces sum to $\approx1.44$), so
    `eq:tailmass` is a tail mass, not a fraction, until divided by the norm.
14. `sec:disc-screen-attribution` L64–69: the $\tau\,\Delta\nu_d$ product needs
    $\tau$ in the same band as $\Delta\nu_d$, not an $\alpha$-fixed refit;
    simplify.
15. `sec:subband` L270–273: sub-band EMG fits are the correct descriptive
    product; stop describing them as "the family the joint fit is designed to
    avoid privileging" if family 2/3 is adopted.

## Unverified in this review

Campaign posterior classes, the α-free preference, and the $s^2$ sensitivity
were taken from the task statement and `analysis/CONTEXT.md`, not from fit
artifacts. The S/N estimates in §1(d) are order-of-magnitude scalings from the
stated bands, not a computed Fisher analysis on these bursts. Fitting code was not read.
