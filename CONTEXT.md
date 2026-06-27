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

**Provisional-citable α**:
A scattering-index row allowed in `tab:alpha` before FINAL figure regen locks
population statistics — all-exp PBF, un-railed, PBF-insensitive, component count
confirmed (fixed-s² for Tier-B sightlines), PASS or flagged MARGINAL under the
floor-1.0 policy (ADR-0004). Population counts and exact median/fractions stay
qualitative until FINAL regen.
_Avoid_: quoting hard N=8 or median α in abstract/conclusions while provisional.

**Unified α roster**:
One `tab:alpha` listing every provisional-citable sightline (including
multiplicity cases such as FRB 20220310F), not a split “eight + ninth” table.
FRB 20220207C (zach) is **excluded** — fixed-s² C2D3 vs C2D2 not robust
(Pass 2 grill, 2026-06-27).
_Avoid_: separate prose-only α for bursts that belong in the table.

**Energies trust boundary**:
A row in `tab:burst-energies` requires spectroscopic host redshift and a joint
$c_0,\gamma$ fit with physical per-band amplitudes. Scattering joint-fit FAIL is
informational (energy is α-independent). Pass 2 re-admits FRB 20220506D and
FRB 20220310F via mixed-legacy $c_0,\gamma$ export (eight rows total).
_Avoid_: “six energies” or “FAIL-gated” exclusion for oran/whitney.

**Per-section sample rule**:
Every analysis subset states its own burst list and exclusion reasons in text or
caption; the twelve-burst co-detection set is never assumed as the denominator.

**Explicit pending**:
Abstract/conclusions state that population-level $\alpha$ statistics and the
measured-versus-predicted budget overlay remain qualitative pending FINAL figure
regeneration. Fixed-s² component adjudication is **complete** for the four Tier-B
sightlines (oran C2D1, isha C2D1, mahi weak C2D1, phineas C3D3 not robust).

**Pass 2 closeout (2026-06-27)**:
Pipeline PR #74 merged @ `c0696a6`; Faber2026 stacked PR pins submodule and
updates tex (8-row energies, zach out of `tab:alpha`, abstract/conclusions prose).

## Relationships

- **Provisional-citable α** rows populate **unified α roster** (`tab:alpha`) while
  **explicit pending** governs population prose.
- **Energies trust boundary** is independent of the α roster (different quality
  inputs: c0,γ vs τ,α).
- **Per-section sample rule** applies to both tables and narrative subsets.

## Example dialogue

> **Dev:** “tab:alpha has eight rows but the abstract says median α≈2.9 — ship it?”
> **Domain expert:** “Not until FINAL regen. Rows are provisional-citable; population
> stats stay qualitative. Name fixed-s² completion and FINAL regen in the abstract.”

## Flagged ambiguities

- **“Well-constrained”** in figures — means provisional-citable under the hybrid
  model, not FINAL PASS. Pass 2 drops zach from `tab:alpha`; profile-bias
  demonstrator claim remains withheld (ADR-0003).
