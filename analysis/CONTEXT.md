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
A scattering-index row allowed in `tab:alpha` before FINAL gate verdicts lock —
all-exp PBF, un-railed, PBF-insensitive, component count confirmed, PASS or
flagged MARGINAL under the floor-1.0 policy (ADR-0004). Population counts and
exact median/fractions stay qualitative until FINAL regen.
_Avoid_: quoting hard N=8 or median α in abstract/conclusions while provisional.

**Unified α roster**:
One `tab:alpha` listing every provisional-citable sightline (including
multiplicity cases such as FRB 20220310F), not a split “eight + ninth” table.
_Avoid_: separate prose-only α for bursts that belong in the table.

**Energies trust boundary**:
A row in `tab:burst-energies` requires spectroscopic host redshift and a joint
$c_0,\gamma$ fit with physical per-band amplitudes. Scattering joint-fit FAIL is
informational (energy is α-independent); oran/whitney are withheld pending
all-exp $c_0,\gamma$ re-export, not because scattering FAIL excludes energy.
_Avoid_: “eight energies” or “FAIL-gated” exclusion when the tabulated sample is six.

**Per-section sample rule**:
Every analysis subset states its own burst list and exclusion reasons in text or
caption; the twelve-burst co-detection set is never assumed as the denominator.

**Explicit pending**:
Abstract/conclusions may state that FINAL per-sightline quality verdicts and
figure regeneration follow the all-exp gate pass — honest blocker, not vague
“in progress.”

## Relationships

- **Provisional-citable α** rows populate **unified α roster** (`tab:alpha`) while
  **explicit pending** governs population prose.
- **Energies trust boundary** is independent of the α roster (different quality
  inputs: c0,γ vs τ,α).
- **Per-section sample rule** applies to both tables and narrative subsets.

## Example dialogue

> **Dev:** “tab:alpha has nine rows but the abstract says median α≈2.9 — ship it?”
> **Domain expert:** “Not until FINAL regen. Rows are provisional-citable; population
> stats stay qualitative. Name the gate pass in the abstract instead.”

## Flagged ambiguities

- **“Well-constrained”** in figures — means provisional-citable under the hybrid
  model, not FINAL PASS. zach stays in `tab:alpha` as an ordinary α measurement;
  the profile-bias demonstrator claim is withheld (ADR-0003).
