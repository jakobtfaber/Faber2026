# Faber2026 manuscript context

Overleaf-synced LaTeX for the CHIME/FRB–DSA-110 co-detection dispersion- and
scattering-budget paper. Numbers and figures are produced by **dsa110-FLITS**
(`pipeline/` submodule); fit-domain jargon lives in
[`pipeline/CONTEXT.md`](pipeline/CONTEXT.md).

## Language

**Co-detection sample**:
The twelve bursts seen by both CHIME/FRB and DSA-110 — the manuscript superset
for association, DM budget, and foreground census.
_Avoid_: treating any subset table as implicitly covering all twelve.

**Trust reset** (owner decisions 2026-07-06, evening, two waves — supersedes
every quoting carve-out below):
*Wave 1 (fits):* trust is revoked for ALL burst-data fits performed to date —
the joint scattering fits (every β, τ₁GHz, component multiplicity, and PPC
verdict; interior posteriors included, so freya β=3.72 and phineas β=3.23 are
NOT quotable), the sub-band EMG fits, the scintillation ACF fits (Δν_d), and
the spectral amplitudes c₀,γ with every derived energy.
*Wave 2 (census + budget):* trust is also revoked for the foreground census
(the 49-candidate catalog cross-match, its foreground/background/inconclusive
verdicts, impact parameters, and halo-mass proxies) and for the entire DM
budget decomposition (NE2001/YMW16 disk terms, the 40 pc cm⁻³ halo prior,
the Macquart mean, the mNFW/two-phase DM_int columns, host residuals, and
the negative-residual Macquart-scatter bound).
What retains trust, among analysis products: TOA association arithmetic and
DM_obs only. Observational inputs (positions, nicknames, published host
spectroscopic redshifts) are inputs rather than revoked products; V3/V4
audit their provenance where consumed.
Manuscript claims consuming any revoked quantity are unsupported until
re-established — that now includes `tab:budget`, `tab:foreground`,
fig:budget (both panels), the dominant-systems and cluster analyses, the
host-dominated 10/11 comparison, the τ·Δν_d two-screen test, the
scintillation excess, the FRB 20230913A intervening attribution (both of its
supporting diagnostics sit on revoked strands), `tab:beta`, and
`tab:burst-energies`. Trust is restored only through the re-validation
ladders of `docs/rse/specs/plan-circulation-readiness.md` §V (V1 fits, V3
energies, V4 census, V5 DM budget).
_Avoid_: citing any fit-, census-, or budget-derived number from the current
tables in new prose; treating a PPC pass under the old campaign as evidence
of trust.

**Geometry-adjudicated β** (supersedes "rail-aware citable", owner decision
2026-07-06; quoting provisions suspended by the fit-trust reset above):
Rail classes from the β-coherent thin-screen campaign (interior / railed-hi /
railed-lo / unconstrained / gate-FAIL) are fit-campaign QA vocabulary and do
NOT appear in manuscript prose or tables. A posterior railing at β=4 is
evidence against the thin-screen closure for that sightline (ADR-0007's
re-open trigger — fired for ten of twelve posteriors: the nine railed
`tab:beta` rows plus gate-FAIL chromatica, the campaign report's 10-member
candidate set), not a square-law detection. The
former "geometry-conditioned α = 4 limit" is retired: **no α is quoted in any
form for an ex-railed row** until per-sightline geometry model selection
(thin screen vs extended medium, informed by the CHIME+DSA two-screen
scintillation constraints) adjudicates. What survives for those rows is the
descriptive data statement — PBF consistent with the exponential limit in both
bands (for the elevated-χ² trio, subject to pending (3)'s per-band systematics
caveat) — with no turbulence index attached; the statement is itself
fit-derived, so it too awaits §V re-validation before use. The two interior sightlines
(freya β=3.72, phineas β=3.23) remain quotable as thin-screen-conditioned
measurements with the geometry named, pending the same adjudication —
**suspended**: under the fit-trust reset the interior rows are not quotable
either until the fits are re-established. Rail-class tallies of the retired
fit campaign (2 interior / 9 railed / 1 gate-FAIL) remain quotable only as
facts about that campaign, never about the sky — these tallies are distinct
from the *foreground census*, which is wave-2 revoked; class fractions stay
withheld, and whether the tallies appear in manuscript prose is an owner
call at reconciliation. The PBF shape and α = 2β/(β−2) are both derived
from β at each likelihood evaluation (co-model; sec:jointfit).
_Avoid_: α = 4 quoted for an ex-railed row in any form, including as a limit;
rail-class vocabulary in manuscript text beyond the campaign tallies;
thin-screen as an unstated default geometry; quoting median β or class
fractions.

**Scint→scattering coupling** (owner decision 2026-07-06):
Scintillation is not a parallel product. The two-screen analysis (τ·Δν_d,
screen placement) built on the CHIME+DSA scintillation campaign — once it is
complete on both bands — feeds the per-sightline scattering geometry choice;
scattering re-fits and any restructured β presentation are sequenced behind
that completion. Preferred mechanism (pending confirmation): scint products as
constraints/priors adjudicating geometry, not extra free fit parameters.
_Avoid_: presenting scintillation and scattering as independent result silos.

**Unified β roster** (suspended by the fit-trust reset — the row facts below
are history of the revoked campaign, not citable trust states):
One `tab:beta` listing every geometry-adjudicated-citable sightline (including
multiplicity cases such as FRB 20220310F), not a split table.
FRB 20220207C (zach) is **re-admitted** as a railed-hi Tier-B row — the
campaign's PPC-verified C1D1 joint fit (roster re-lock 2026-07-06, pipeline
PR #133) supersedes the Pass-2 fixed-s² C2D3-vs-C2D2 exclusion, which applied
to the retired free-α framework. FRB 20240203A (chromatica) is **excluded**
(joint-fit quality gate FAIL, χ²ᵣ ≈ 11.6/9.3).
_Avoid_: separate prose-only β for bursts that belong in the table.

**Energies trust boundary** (suspended by the fit-trust reset):
A row in `tab:burst-energies` requires spectroscopic host redshift and a joint
c₀,γ fit with physical per-band amplitudes. Scattering joint-fit FAIL is
informational (energy is β-independent). Pass 2 re-admits FRB 20220506D and
FRB 20220310F via mixed-legacy c₀,γ export (eight rows total). Under the
fit-trust reset no energy is currently citable; the fresh-read audit also
flagged a γ_D pile-up at ≈−5 (possible prior rail) and a selection-rule
contradiction (gate-FAIL 20240203A tabulated under a "quality-passing"
criterion) — both must be resolved in the re-validation pass.
_Avoid_: "six energies" or "FAIL-gated" exclusion for oran/whitney.

**Per-section sample rule**:
Every analysis subset states its own burst list and exclusion reasons in text or
caption; the twelve-burst co-detection set is never assumed as the denominator.

**Explicit pending**:
(0) Re-validation framework (plan §V) — the trust reset makes this the first
gate: no fit-, census-, or budget-derived quantity is citable until its
producing analysis passes the corresponding re-trust ladder (V1 fits, V3
energies, V4 census, V5 DM budget); includes verifying whether the scattering-fit CHIME
inputs share the gen-1 de-chirp defect lineage found in the scintillation
products. (1) Geometry-selection campaign (extended-medium kernel + per-sightline model
selection, scint-informed) — supersedes the narrower "ADR-0007 re-analysis of
the nine railed rows"; blocks any α quoting for the nine ex-railed rows and
the restructured abstract/co-model-methods/results language. (2) CHIME-band scintillation
campaign: burst configs + first measurements for whitney/phineas/mahi/isha;
U sizing + regeneration for the six never-generated co-detections; ACF/Δν_d
across the sample (the existing DSA-band Δν_d fits and two-screen table are
themselves revoked pending §V; the campaign re-establishes both bands).
(3) Per-band systematics pass on the sightlines the fresh campaign flags
with elevated per-band χ² (the revoked campaign's trio — wilhelm, hamilton,
zach — is the starting hypothesis, re-derived by plan C1). (4) Two-screen treatment decision — scint products as
geometry-adjudicating constraints vs a fitted two-screen model (constraint
route preferred; owner confirmation pending). (5) **Manuscript not yet
reconciled to this contract** — wave 1: abstract, observations (§2), the
co-model methods (sec:jointfit / sec:beta-scattering-methods), results,
discussion, conclusions, and `tab:beta` still carry rail-class language
and/or α = 4 limits, and the multiplicity-bias demonstration
(fig:whitney_mult, the abstract's closing claim, conclusions item 7) plus
fig:jointmodel_montage and fig:scint_screens are built on revoked fits;
wave 2: the budget section (§3 — census verdicts, dominant-systems and
cluster analyses, scint excess, τ·Δν_d test), results §4.1, and conclusions
items 1–3/5–6 carry census/budget claims now unsupported. Reconciliation is
scheduled per plan F1 (see `docs/rse/specs/plan-circulation-readiness.md`).
The measured-versus-predicted budget overlay exists in the draft, but both
sides are now revoked (measured diamonds = wave-1 τ fits; predicted bars =
wave-2 census/budget products) — re-derived after C + V4/V5 (plan D1).

**Pass 2 closeout (2026-06-27)**:
Pipeline PR #74 merged @ `c0696a6`; Faber2026 stacked PR pins submodule and
updates tex (8-row energies, zach out of `tab:alpha`, abstract/conclusions prose).

**β-model revision (2026-06-29) — campaign complete (2026-07-06)**:
Joint-fit methodology revised: the fundamental parameter is the turbulence
spectral index β (P_n(q) ∝ q^(−β)), from which both the PBF shape (via
D_φ(ρ) ∝ ρ^(β−2)) and the frequency-scaling index α = 2β/(β−2) follow. The
old free-α + fixed-exponential-PBF approach is physically inconsistent (Cordes
et al. 2025). `tab:alpha` → `tab:beta`; `fig:alpha_pbf` dropped. The
β-coherent thin-screen campaign (pipeline PRs #133/#134) re-fit all 12
co-detections with PPC verification: freya β=3.72 and phineas β=3.23
interior; 9 railed-hi table rows; chromatica gate-FAIL. Report:
`pipeline/analysis/beta_campaign/CAMPAIGN_REPORT.md`.

## Relationships

- **Geometry-adjudicated β** governs what `tab:beta` (**unified β roster**) may
  quote, while **explicit pending** governs population prose;
  **scint→scattering coupling** sequences the re-fit that will repopulate it.
- **Energies trust boundary** is independent of the β roster (different quality
  inputs: c₀,γ vs τ,β).
- **Per-section sample rule** applies to both tables and narrative subsets.

## Example dialogue

> **Dev:** "Nine rows rail at β=4 — can we say the sample's median α is 4?"
> **Domain expert:** "No — and under the fit-trust reset nothing from those
> fits is citable at all, not even the descriptive statement. The fits must
> first pass the plan-§V re-trust ladder on verified inputs; then geometry
> model selection, informed by re-validated two-screen scintillation
> constraints, decides what any surviving statement or index means. The
> rail tallies describe the retired fit campaign, not the sky."

## Flagged ambiguities

- **"Well-constrained"** in figures — after the fit-trust reset the term has
  no citable referent: nothing qualifies until a fit passes §V and geometry
  adjudication. Figures using it need relabeling during reconciliation.
  Profile-bias demonstrator claim remains withheld (ADR-0003).
- **Old α values** from the free-α + fixed-exponential-PBF model are retired;
  where they survive (the sub-band validation figure) they are labeled as
  exponential-parametrization cross-checks, not turbulence indices; under the
  fit-trust reset the sub-band fits themselves are also uncitable pending §V.
- **johndoeII's interior crossing** — its z=0.77 dominant halo is foreground
  only against a placeholder host redshift; the galaxy-interior attribution is
  provisional until a spectroscopic host z exists — and now doubly suspended:
  the census verdict itself is Wave-2 revoked pending V4.
