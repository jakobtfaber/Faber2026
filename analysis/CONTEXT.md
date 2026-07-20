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

**Trust reset** (owner decisions 2026-07-06, evening→night, three waves —
supersedes every quoting carve-out below):
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
*Wave 3 (association + DM_obs):* trust is also revoked for the TOA
association arithmetic (residuals, P_cc, the association verdicts) and for
DM_obs across all twelve bursts. Grounds: the tabulated DM_obs does not
distinguish the CHIME-side from the DSA-side measurement, their level of
agreement has never been quantified, and how each DM_obs was obtained
(instrument pipeline, dedispersion method, reference artifact) is
undocumented.
**Status 2026-07-07:** V6 has revalidated this lane for manuscript use.
Association residuals, P_cc, and verdicts may be quoted from the pinned V6
artifacts under the shared DSA-DM reference convention; the residual is a
timing/geometry consistency check, not a per-telescope-DM-corrected residual.
DM_obs provenance and CHIME--DSA agreement are documented in the V6 artifacts.
**Status 2026-07-07 (V4+V5):** the owner has cleared the foreground-census (V4)
and DM-budget (V5) ladders on the strength of the DR9/DESI-DR1/NED/PS1-STRM
re-validation of the candidate catalog — including the DESI-STAR redshift
contaminant fix on the phineas cluster J114928.5+712526 and the discovery that
all census clusters come from the Wen \& Han 2024 DESI Legacy/WISE catalog (not
the X-ray/SZ catalogs the pinned code lists). The census now presents 35 systems
(34 halos + the single cluster within $R_{500}$; 14 further foreground clusters
at $b>R_{500}$ omitted).
**Census remediation (owner adjudications 2026-07-15, FLITS #184):** the 35
catalog rows deduplicate to 28 physical systems (seven sub-arcsec same-z
cross-listed pairs, five of them confirmed: the physical confirmed census is
9 halos + the cluster, not 14 + 1); the budget adopts the B7 *empirical*
per-candidate masses (`data/census_masses/halo_rvir_ADJUDICATED.csv`) with
whitney-1473's WISE-blend mass overridden to its optical g−z estimate
(logM*=9.605; `mass_overrides.csv`); halo impact parameters are uniformly
recomputed from burst position + coordinates + adopted z (the cluster keeps
its analysis-provenance b=603.6, b/R500=0.83 — the 2.6% recompute offset
[619 kpc, 0.85] was investigated 2026-07-15: no committed input reproduces
603.6 [needs a 4.6 arcsec different position or H0≈70]; RESOLVED by carrying
it as a documented ±3% geometry systematic in Appendix B, negligible against
the factor-of-two column systematics). Budget outcome: DM_int nonzero on four sightlines
(phineas 243, casey 117, chromatica 26, whitney 6); footnote m retired;
7 of 9 physical confirmed halos pierce R_vir (b/R_vir 0.46–0.96). `tab:foreground`, the census verdicts/impact
parameters, the two-phase mNFW `DM_int` columns, and `fig:clusters_icm` are
restored for manuscript use. **Still revoked** (not unlocked by V4/V5): the
measured-scattering side of fig:budget and its measured-vs-predicted overlay
(wave-1 τ fits, V1 / plan D1), the τ·Δν_d two-screen test and scintillation
excess (the closed CHIME-band campaign qualifies only FRB 20240203A, while the
certified DSA point belongs to FRB 20220506D), the FRB 20230913A intervening
attribution (rides on revoked scint strands), `tab:beta`, and
`tab:burst-energies`.
Outside lanes that have passed their V re-validation, no analysis product
retains trust. Raw observational inputs (positions, nicknames, published host
spectroscopic redshifts) remain inputs rather than revoked products; the V
ladders audit their provenance where consumed. The twelve-burst co-detection set
stays the *working roster*, with citable association evidence now restored by V6.
Manuscript claims consuming any revoked quantity are unsupported until
re-established — after the V4+V5 clearance above that still includes the
measured-scattering side of fig:budget and its measured-vs-predicted overlay
(wave-1 τ fits, V1 / plan D1), the τ·Δν_d two-screen test, the scintillation
excess, the FRB 20230913A intervening attribution (both of its supporting
diagnostics sit on revoked scint strands), `tab:beta`, `tab:burst-energies`,
and any association or DM_obs value not tied to the V6 artifacts and
shared-DSA-DM convention. Trust is restored only through the
re-validation ladders of `docs/rse/specs/plan/plan-circulation-readiness.md` §V
(V1 fits, V3 energies, V4 census, V5 DM budget, V6 association + DM_obs).
_Avoid_: citing any fit-, census-, budget-, association-, or DM-derived
number from the current tables in new prose unless its lane has passed the
corresponding V ladder and the table/prose states the relevant convention;
treating a PPC pass under the old campaign as evidence of trust; quoting a
single undifferentiated DM_obs as if CHIME and DSA agree.

**Geometry-adjudicated β** (supersedes "rail-aware citable", owner decision
2026-07-06; quoting provisions suspended by the fit-trust reset above):
**D2–D5 design locks** (owner accepted 2026-07-10; memo
`docs/rse/specs/decision/decision-d2-d5-scattering-design-locks.md`): `tab:beta` carries
`closure_regime ∈ {inertial, endpoint-degenerate}` (no β/α turbulence quote on
endpoint rows; geometry is a separate A3 field); sub-band EMG slopes are
diagnostic only; scintillation products come from a separate ACF path (A1);
energies are band-restricted with a non-comparability disclaimer (no fixed
rest-frame variant unless elected under V3). Locks are presentation contracts —
they do not restore fit citability.
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
withheld. Owner decision 2026-07-06: the tallies are **dropped from the
manuscript** — methods may describe the thin-screen campaign qualitatively
as model-family diagnosis, but no tally is quoted as a fact. The PBF shape and α = 2β/(β−2) are both derived
from β at each likelihood evaluation (co-model; sec:jointfit).
_Avoid_: α = 4 quoted for an ex-railed row in any form, including as a limit;
rail-class vocabulary in manuscript text beyond the campaign tallies;
thin-screen as an unstated default geometry; quoting median β or class
fractions.

**Wilhelm / EMG wording guardrail (2026-07-07):** For FRB 20221203A
(`wilhelm`), do not describe the residual morphology as evidence against the
right-sided exponential/EMG branch. The beta-coherent fits drive this sightline
to the β≈4 exponential limit. The remaining issue is a coherent high-S/N DSA
bright-pulse profile residual within that preferred exponential-tail model, not
a rejected EMG/PBF family.

**Scint→scattering coupling** (owner decision 2026-07-06; A1 mechanism
adopted as a working draft 2026-07-06, trigger revised 2026-07-13, trigger
closed 2026-07-15):
Scintillation is not a parallel product. The two-screen analysis (τ·Δν_d,
screen placement) built on the CHIME+DSA scintillation campaign — once it is
complete on both bands — feeds the per-sightline scattering geometry choice;
scattering re-fits and any restructured β presentation are sequenced behind
that completion. Mechanism (A1): a modular constraint layer — scint
products enter as frozen posterior/limit products with quality flags (never
point estimates); τ·Δν_d is used probabilistically to count screens and
derive τ_near/τ_dom, marginalized over geometry constants and censoring; a
second broadening component is not fitted unless the **escalation trigger**
fires. As revised 2026-07-13, the trigger is evidence-based model
comparison, not hand-set ratio thresholds: (i) nested-sampling model
comparison preferring a two-component (stacked-Lorentzian) ACF model over a
single Lorentzian at an injection-calibrated ΔlnZ threshold, or (ii)
posterior-predictive residuals in the burst profile at the predicted
second-screen timescale. **Closed 2026-07-15:** the injection calibration
found no usable ΔlnZ operating point (1% false-escalation envelope at
ΔlnZ ≈ 5.97×10⁴, zero escalation probability across all eight power cells —
`plan-a1-trigger-calibration.md` final outcome); clause (i) is retired and
clause (ii) is the sole surviving escalation limb. The former τ_near/τ_dom
ratio thresholds (Pr(τ_near/τ_dom > 0.1) > 0.1, median ratio > 0.03) are
retired as triggers, demoted to prior-odds inputs only. Successor statistic
chartered as **A5** (N-component profile-fit justification statistic, owner
direction at A1-trigger closure) — a calibrated model-comparison criterion
for burst-profile component count, distinct from A1's screen count; design
pending, not a circulation blocker unless promoted. For extended host
media, quenching constrains an effective source-proximate scattering-depth
distribution, not a point screen distance; scint geometry sets **prior
odds** on the PBF kernel family (thin vs extended) with final selection by
evidence/model-comparison; a joint burst-shape+ACF likelihood is deferred
unless modular products conflict on a high-S/N sightline. Full decision
text: plan-circulation-readiness A1/A5.
_Avoid_: presenting scintillation and scattering as independent result
silos; treating a scint verdict as a hard geometry cut rather than prior
odds; quoting the retired τ_near/τ_dom thresholds as the current escalation
trigger; conflating A5 (profile-component count) with A1/A2/A3
(scattering-screen geometry).

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
gate: no fit-, census-, budget-, association-, or DM-derived quantity is
citable until its producing analysis passes the corresponding re-trust
ladder (V1 fits, V3 energies, V4 census, V5 DM budget, V6 association +
DM_obs); includes verifying whether the scattering-fit CHIME
inputs share the gen-1 de-chirp defect lineage found in the scintillation
products. (1) Geometry-selection campaign (extended-medium kernel + per-sightline model
selection, scint-informed) — supersedes the narrower "ADR-0007 re-analysis of
the nine railed rows"; blocks any α quoting for the nine ex-railed rows and
the restructured abstract/co-model-methods/results language. (2) CHIME-band scintillation campaign — status 2026-07-17: the objective-window campaign is
closed at dsa110-FLITS PR #192 / pin `17d9d266...`. Exactly one of 24 products,
the high-resolution FRB 20240203A record (`chromatica_hi`), is a qualified
measurement; its four resolved sub-bands support a descriptive within-band
slope. The other 23 products remain diagnostic only. The certified DSA point
is FRB 20220506D, so these measurements do not establish a cross-band scaling
law or a common screen. Historical route status: three
freya-qualification routes closed `DOCUMENTED-FAIL` in sequence — C1
(cross-fitted all-pairs estimator: 0/8 required low-modulation calibration
cells passed, nulls failed the family-wise gate, FLITS #176); P1 (windowed
fine-channelization regeneration from the coherently dedispersed baseband:
none of five predeclared window variants passed the frozen 10x common-mode
suppression screen, and windowing left the common-mode amplitude unchanged,
0.586 → 0.62–0.68, placing the structure upstream in the baseband within
each 390.625 kHz coarse channel — FLITS #179, pin #50); P2/Route B (ratio
statistic: G2 common-mode cancellation PASS, ~100x, but G1 sensitivity fail
— FLITS PR #180, pin #65). The owner declined to ratify narrowing the paper
to DSA-only scintillation (`decision-2026-07-15-p1-scope-fork.md`, owner
amendment). That scope decision is now satisfied by the closed objective-window
campaign rather than by the previously proposed successor routes. Historical
routes included P3
(delay-domain optimal quadratic estimator,
`handoff-2026-07-15-04-00-p3-optimal-estimator-dev.md`, Gate 0b forecast
first) awaiting owner sanction; external instrumental characterization
(steady calibrator through the identical baseband + upchannelization path);
voltage-domain cross-statistics (separating the multiplicative common
bandpass from source-flux modulation before detection) — each requires its
own predeclared experiment record with frozen gates before burst data is
inspected. Those routes are no longer prerequisites for reporting the reviewed
PR #192 outcome, but they do not convert any of the 23 diagnostic records into
measurements. Earlier full-sample work (burst configs for
whitney/phineas/mahi/isha; U sizing + regeneration for the six
never-generated co-detections; ACF/Δν_d across the sample) was blocked
behind a qualifying route on freya (the existing DSA-band Δν_d fits and
two-screen table are themselves revoked pending §V; the campaign
re-establishes both bands).
(3) Per-band systematics pass on the sightlines the fresh campaign flags
with elevated per-band χ² (the revoked campaign's trio — wilhelm, hamilton,
zach — is the starting hypothesis, re-derived by plan C1). (4) Two-screen
treatment decision — **working draft adopted 2026-07-06** (modular
constraint layer with prior-odds geometry and a posterior escalation
trigger; see "Scint→scattering coupling" above), **design open**: owner
re-opened all locked decisions the same night; thresholds, trigger form,
and interface contract remain under discussion. (5) **Manuscript not yet
reconciled to this contract** — wave 1: abstract, observations (§2), the
co-model methods (sec:jointfit / sec:beta-scattering-methods), results,
discussion, conclusions, and `tab:beta` still carry rail-class language
and/or α = 4 limits, and the multiplicity-bias demonstration
(the abstract's closing claim, conclusions item 7) plus
fig:jointmodel_montage and fig:scint_screens are built on revoked fits;
wave 2: the budget section (§3 — census verdicts, dominant-systems and
cluster analyses, scint excess, τ·Δν_d test), results §4.1, and conclusions
items 1–3/5–6 carry census/budget claims now unsupported. Reconciliation is
scheduled per plan F1 (see `docs/rse/specs/plan/plan-circulation-readiness.md`).
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

- **Figure 1** is locked (owner decision 2026-07-14,
  `decision-2026-07-14-figure1-and-chime-c1.md`) as `fig1-gallery`: a
  data-only 4-by-3 MJD-ordered twelve-burst gallery (CHIME/FRB + DSA-110
  dynamic spectra with time/frequency marginals, no fitted model or
  scintillation annotation). This chooses the product, not the bytes — a
  fresh isolated batch and hash-bound owner approval of the exact candidate
  are still required; the earlier rejected-candidate `fig1-gallery` stays
  `needs_revision` and must not be promoted.
- **Figure wishlist** (`docs/rse/specs/misc/figure-wishlist.md`) lists other
  intended figures not yet (re)inserted; live draft `\fbox` floats with
  `\label{fig:…}` sit in `sections/observations.tex` and
  `sections/results.tex`. Do not `\includegraphics` revoked campaign PDFs
  until the listed gate clears; strip draft boxes before circulation
  (referee M9).
- **Operational state** is generated, not hand-maintained: canonical source
  is `docs/rse/program-state.toml` (its `[owner_view]` block is the board
  summary), evidence tracked in `docs/rse/evidence-ledger.toml`;
  `scripts/sync_state.py` regenerates `docs/rse/ACTIVE_LANES.md` and the
  `owner-view.json` the readiness board renders. Design:
  `docs/rse/specs/plan/plan-hybrid-control-system.md` (landed PR #59).
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
- **johndoeII's interior crossing** — RESOLVED 2026-07-15: the V4-verified
  census registry carries no johndoeII candidates at all; the interior-crossing
  attribution (and its DM_int=70 column) came from the Wave-2-revoked legacy
  candidate list through the registry-empty fallback bug fixed in FLITS
  PR #183. The budget now tabulates DM_int=0 (note u, host z unknown); the
  galaxy-interior narrative is removed from Results and the budget table.
