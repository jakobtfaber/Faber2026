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

**Provisional-citable β**:
A turbulence-spectrum row allowed in `tab:beta` before FINAL figure regen locks
population statistics — un-railed, component count confirmed (fixed-s² for Tier-B
sightlines), PASS or flagged MARGINAL. The PBF shape and frequency-scaling index
α = 2β/(β−2) are both derived from β at each likelihood evaluation (co-model;
§3.5). Population counts and exact median/fractions stay qualitative until FINAL
regen.
_Avoid_: quoting hard N or median β in abstract/conclusions while provisional.

**Unified β roster**:
One `tab:beta` listing every provisional-citable sightline (including
multiplicity cases such as FRB 20220310F), not a split table.
FRB 20220207C (zach) is **excluded** — fixed-s² C2D3 vs C2D2 not robust
(Pass 2 grill, 2026-06-27).
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
Abstract/conclusions state that population-level β statistics and the
measured-versus-predicted budget overlay remain qualitative pending FINAL figure
regeneration. Fixed-s² component adjudication is **complete** for the four Tier-B
sightlines (oran C2D1, isha C2D1, mahi weak C2D1, phineas C3D3 not robust).

**Pass 2 closeout (2026-06-27)**:
Pipeline PR #74 merged @ `c0696a6`; Faber2026 stacked PR pins submodule and
updates tex (8-row energies, zach out of `tab:alpha`, abstract/conclusions prose).

**β-model revision (2026-06-29)**:
Joint-fit methodology revised: the fundamental parameter is the turbulence
spectral index β (P_n(q) ∝ q^(−β)), from which both the PBF shape (via
D_φ(ρ) ∝ ρ^(β−2)) and the frequency-scaling index α = 2β/(β−2) follow. The
old free-α + fixed-exponential-PBF approach is physically inconsistent (Cordes
et al. 2025). `tab:alpha` → `tab:beta`; `fig:alpha_pbf` dropped. Pipeline
re-run for β values is pending; table rows and component counts are preserved.

## Relationships

- **Provisional-citable β** rows populate **unified β roster** (`tab:beta`) while
  **explicit pending** governs population prose.
- **Energies trust boundary** is independent of the β roster (different quality
  inputs: c₀,γ vs τ,β).
- **Per-section sample rule** applies to both tables and narrative subsets.

## Example dialogue

> **Dev:** "tab:beta has eight rows but we haven't re-run the pipeline — ship it?"
> **Domain expert:** "Not until FINAL regen under the β-based likelihood. Rows are
> provisional-citable; population stats stay qualitative. Name fixed-s² completion
> and FINAL regen in the abstract."

## Flagged ambiguities

- **"Well-constrained"** in figures — means provisional-citable under the β-based
  co-model, not FINAL PASS. Pass 2 drops zach from `tab:beta`; profile-bias
  demonstrator claim remains withheld (ADR-0003).
- **β values** — pending pipeline re-run with the turbulence-spectrum likelihood.
  Old α values from the free-α + fixed-exponential-PBF model are not valid inputs
  for conversion to β.
