# Research: foreground-census alignment with provisional propagation fits

## Question

Do the V4 foreground halo/cluster census and the best-so-far scattering and
scintillation products show a geometrical alignment or a plausible causal
relationship along any of the twelve co-detection sightlines?

## Sources and trust boundary

- `pipeline/galaxies/foreground/budget_table_data.json:1-18` is the
  registry-authoritative V4 budget source. Its `u` flag means the absence of an
  eligible system is coverage-limited, not a foreground exclusion.
- `pipeline/galaxies/foreground/foreground_table_data.json:1-15` is the
  deduplicated confirmed/inconclusive census used by the manuscript.
- `scripts/dm_budget_intervening_systems.csv` lists the budget-eligible systems
  individually and prevents a count of cross-listed candidates from being
  mistaken for a count of physical structures.
- `analysis/provisional_propagation/results.json` contains the frozen joint-fit
  values and records that the component-level two-screen calculation is pending
  the policy-required $\alpha=4$ consistency refits.

The old sightline-attribution matrix is not used because its joint-fit values
and statuses predate the July 14 residual adjudication.

## Findings

FRB 20230307A (Phineas) is the strongest plausible foreground contributor. Its
covered sightline contains three budget-eligible galaxy halos and the confirmed
cluster J115120.4+714435 at $b/R_{500}=0.83$. The fiducial foreground model gives
$\tau_{\rm int}=0.015$ ms, about 22% of the provisional
$\tau_{1\,\mathrm{GHz}}=0.0676$ ms. This is consistent with a partial foreground
contribution, not with the foreground model explaining all of the broadening.
If a future policy-compliant two-screen analysis supports multiple layers, the
identified foreground structure is a plausible scattering-screen candidate,
but the present products do not locate a screen.

FRB 20220310F (Whitney) has a confirmed foreground halo at approximately
101 kpc, but its fiducial $\tau_{\rm int}=3.6\times10^{-4}$ ms is only about
0.5% of the provisional fitted broadening. The alignment is real; a dominant
causal role for that halo in the observed scattering is disfavored by the
current foreground model.

The other five accepted-fit sightlines have no budget-eligible foreground
system, but every one is outside the deep-imaging footprints. They therefore
cannot serve as clean foreground-free controls. Two have especially close
inconclusive projected candidates: FRB 20221113A at 16 kpc and FRB 20230325A at
60 kpc. Redshift validation is the decisive next observation for both.

FRB 20240229A (Casey) and FRB 20240203A (Chromatica) contain confirmed foreground
halos but lack usable accepted propagation fits. For Casey the fiducial
foreground prediction is roughly eleven times the retained morphology-only fit
value, a tension that makes fit revalidation urgent rather than supporting a
causal claim. Chromatica has no retained joint fit.

## Interpretation

There is no defensible sample-wide correlation test: only seven propagation
fits are accepted, only two of the four budget-positive foreground sightlines
have accepted fits, and most foreground-negative rows are coverage-censored.
The supported result is therefore a descriptive alignment ledger. It identifies
Phineas as a plausible partial foreground contribution, Whitney as a small
fiducial contribution, Isha and Freya as high-value redshift follow-up targets,
and Casey as a fit-versus-budget tension. None of these categories establishes
causation.

## Self-review

The comparison uses the same observer-frame 1-GHz millisecond convention for
the tabulated foreground and joint-fit scattering values. Ratios are diagnostic
only: the foreground calculation is a fiducial model, and the joint-fit
posterior samples/covariance and most DSA bandwidth certifications remain
unavailable. Coverage censoring and fit adjudication are retained as explicit
columns so zeros are not interpreted as exclusions.
