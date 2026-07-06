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

**Geometry-adjudicated β** (supersedes "rail-aware citable", owner decision
2026-07-06):
Rail classes from the β-coherent thin-screen campaign (interior / railed-hi /
railed-lo / unconstrained / gate-FAIL) are fit-campaign QA vocabulary and do
NOT appear in manuscript prose or tables. A posterior railing at β=4 is
evidence against the thin-screen closure for that sightline (ADR-0007's
re-open trigger — fired for nine of twelve), not a square-law detection. The
former "geometry-conditioned α = 4 limit" is retired: **no α is quoted in any
form for an ex-railed row** until per-sightline geometry model selection
(thin screen vs extended medium, informed by the CHIME+DSA two-screen
scintillation constraints) adjudicates. What survives for those rows is the
descriptive data statement — PBF consistent with the exponential limit in both
bands — with no turbulence index attached. The two interior sightlines
(freya β=3.72, phineas β=3.23) remain quotable as thin-screen-conditioned
measurements with the geometry named, pending the same adjudication. Census
counts remain quotable as campaign facts. The PBF shape and α = 2β/(β−2) are
both derived from β at each likelihood evaluation (co-model; §3.5).
_Avoid_: α = 4 quoted for an ex-railed row in any form, including as a limit;
rail-class vocabulary in manuscript text; thin-screen as an unstated default
geometry; quoting median β or class fractions.

**Scint→scattering coupling** (owner decision 2026-07-06):
Scintillation is not a parallel product. The two-screen analysis (τ·Δν_d,
screen placement) built on the completed CHIME+DSA scintillation campaign
feeds the per-sightline scattering geometry choice; scattering re-fits and
any restructured β presentation are sequenced after scintillation completes
on both bands. Preferred mechanism (pending confirmation): scint products as
constraints/priors adjudicating geometry, not extra free fit parameters.
_Avoid_: presenting scintillation and scattering as independent result silos.

**Unified β roster**:
One `tab:beta` listing every rail-aware-citable sightline (including
multiplicity cases such as FRB 20220310F), not a split table.
FRB 20220207C (zach) is **re-admitted** as a railed-hi Tier-B row — the
campaign's PPC-verified C1D1 joint fit (roster re-lock 2026-07-06, pipeline
PR #133) supersedes the Pass-2 fixed-s² C2D3-vs-C2D2 exclusion, which applied
to the retired free-α framework. FRB 20240203A (chromatica) is **excluded**
(joint-fit quality gate FAIL, χ²ᵣ ≈ 11.6/9.3).
_Avoid_: separate prose-only β for bursts that belong in the table.

**Energies trust boundary**:
A row in `tab:burst-energies` requires spectroscopic host redshift and a joint
c₀,γ fit with physical per-band amplitudes. Scattering joint-fit FAIL is
informational (energy is β-independent). Pass 2 re-admits FRB 20220506D and
FRB 20220310F via mixed-legacy c₀,γ export (eight rows total).
_Avoid_: "six energies" or "FAIL-gated" exclusion for oran/whitney.

**Per-section sample rule**:
Every analysis subset states its own burst list and exclusion reasons in text or
caption; the twelve-burst co-detection set is never assumed as the denominator.

**Explicit pending**:
(1) Geometry-selection campaign (extended-medium kernel + per-sightline model
selection, scint-informed) — supersedes the narrower "ADR-0007 re-analysis of
the nine railed rows"; blocks any α quoting for the nine ex-railed rows and
the restructured abstract/§3.5/results language. (2) CHIME-band scintillation
campaign: burst configs + first measurements for whitney/phineas/mahi/isha;
U sizing + regeneration for the six never-generated co-detections; ACF/Δν_d
across the sample (the two-screen table is DSA-band only until then).
(3) Per-band systematics pass on the three elevated-χ² rows (wilhelm,
hamilton, zach). (4) Two-screen treatment decision — scint products as
geometry-adjudicating constraints vs a fitted two-screen model (constraint
route preferred; owner confirmation pending). (5) **Manuscript not yet
reconciled to this contract** — abstract, §3.5, results, and `tab:beta` still
carry rail-class language and α = 4 limits; reconciliation is scheduled after
the geometry campaign (see `docs/rse/specs/plan-circulation-readiness.md`).
The measured-versus-predicted budget overlay is **complete** (fig:budget
right panel carries the measured diamonds).

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
> **Domain expert:** "No — and we no longer quote α=4 for those rows at all,
> not even as a limit. A rail is evidence the thin-screen closure is wrong for
> that sightline, so what's citable is only the descriptive statement (PBF
> exponential-consistent in both bands) until geometry model selection,
> informed by the two-screen scintillation constraints, adjudicates. Census
> counts are fine; they're campaign facts."

## Flagged ambiguities

- **"Well-constrained"** in figures — under the 2026-07-06 decision this can
  only mean an interior thin-screen measurement (freya, phineas) until the
  geometry campaign lands; figures using it for ex-railed rows need relabeling
  during reconciliation. Profile-bias demonstrator claim remains withheld
  (ADR-0003).
- **Old α values** from the free-α + fixed-exponential-PBF model are retired;
  where they survive (the sub-band validation figure) they are labeled as
  exponential-parametrization cross-checks, not turbulence indices.
- **johndoeII's interior crossing** — its z=0.77 dominant halo is foreground
  only against a placeholder host redshift; the galaxy-interior attribution is
  provisional until a spectroscopic host z exists.
