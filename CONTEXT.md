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

**Rail-aware citable β** (supersedes "provisional-citable", 2026-07-06):
A `tab:beta` row's presentation follows its posterior's rail class from the
β-coherent thin-screen campaign (pipeline ADR-0004/0006; grader
`analysis/beta_campaign/grade_beta_campaign.py`): **interior** → measured β
with percentile errors and derived α; **railed-hi (β=4)** →
exponential-consistent, quoted ONLY as a geometry-conditioned α = 4 limit
(table note d), never as a measurement, and an extended-medium (ADR-0007)
re-analysis candidate; **railed-lo / unconstrained / gate-FAIL** → not citable,
excluded from the table. The PBF shape and α = 2β/(β−2) are both derived from
β at each likelihood evaluation (co-model; §3.5). Census counts (2 interior /
9 railed rows / 1 gate-FAIL) are table facts and quotable; a population median
or class fractions beyond the counts stay withheld while the thin-vs-extended
geometry question (ADR-0007) is open.
_Avoid_: quoting a railed row's α = 4 as a measurement; quoting median β.

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
(1) Extended-medium (ADR-0007) re-analysis of the nine β=4-railed rows —
until it lands, their α = 4 stays a geometry-conditioned limit and population
statistics beyond census counts stay withheld. (2) CHIME-band Δν_d (needs a
fresh ACF pass; the two-screen table is DSA-band only). (3) Per-band
systematics pass on the three elevated-χ² railed rows (wilhelm, hamilton,
zach — roster Tier B). The measured-versus-predicted budget overlay is
**complete** (fig:budget right panel carries the measured diamonds).

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

- **Rail-aware citable β** rows populate **unified β roster** (`tab:beta`) while
  **explicit pending** governs population prose.
- **Energies trust boundary** is independent of the β roster (different quality
  inputs: c₀,γ vs τ,β).
- **Per-section sample rule** applies to both tables and narrative subsets.

## Example dialogue

> **Dev:** "Nine rows rail at β=4 — can we say the sample's median α is 4?"
> **Domain expert:** "No. A railed row's α=4 is a geometry-conditioned limit of
> the thin-screen closure, not a measurement — no median, no fractions, until
> the extended-medium re-analysis (ADR-0007) settles whether those sightlines
> rail at all. Census counts are fine; they're table facts."

## Flagged ambiguities

- **"Well-constrained"** in figures — means rail-aware citable under the β-based
  co-model (interior, or railed-hi quoted as a limit). Profile-bias
  demonstrator claim remains withheld (ADR-0003).
- **Old α values** from the free-α + fixed-exponential-PBF model are retired;
  where they survive (the sub-band validation figure) they are labeled as
  exponential-parametrization cross-checks, not turbulence indices.
- **johndoeII's interior crossing** — its z=0.77 dominant halo is foreground
  only against a placeholder host redshift; the galaxy-interior attribution is
  provisional until a spectroscopic host z exists.
