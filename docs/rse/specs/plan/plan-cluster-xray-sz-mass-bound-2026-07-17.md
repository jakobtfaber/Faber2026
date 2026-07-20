# Implementation Plan: X-ray/SZ upper-limit mass bound for the FRB 20230307A intervening cluster (Kulkarni S1)

---
**Date:** 2026-07-17
**Author:** AI Assistant
**Status:** Draft — predeclared experiment record, awaiting owner sanction (CONTEXT.md §V gate)
**Related Documents:**
- [Triage: Kulkarni-persona feedback (2026-07-17)](../notes/triage-kulkarni-feedback-2026-07-17.md) — S1 = referee §5 = discovery Thread 2
- [Handoff: deflation + Kulkarni fold-in + attribution](../handoff/handoff-2026-07-17-11-28-deflation-kulkarni-and-attribution.md) — parent session; S1 is "recommended first"
- `CONTEXT.md` (repo root) — trust-reset contract; the census (V4) and DM budget (V5) ladders are cleared, so the cluster mass and its DM column are live inputs this plan refines

---

## Overview

The manuscript's single dominant intervening system — the cluster
J115120.4+714435 crossed by the FRB 20230307A sightline at $b/R_{500}=0.83$ —
carries an intracluster dispersion-measure column whose central value
($\approx$184 pc cm$^{-3}$, mNFW) sits inside a wide $\approx$100–560 pc cm$^{-3}$
systematic bracket, a factor of $\sim$6 end to end. The bracket's width is set
by three inputs: the richness-based $\log M_{500}=14.1$ ($\sim$0.2 dex scatter),
the assumed gas fraction ($f_{\rm gas}=0.10$–0.16), and the profile shape (mNFW
vs. isothermal $\beta$-model). The mass term drives the high end.

The Kulkarni referee note (S1) observes that this cluster is **absent** from the
all-sky X-ray (MCXC) and SZ (Planck PSZ2) catalogs the census cross-matches
against — it enters the census only through the \citet{WenHan2024} optical/IR
catalog (bib key `WenHan2024`, `bib/refs.bib`). Those non-detections are not
merely "no cross-match"; each survey has a documented selection function, so an
absence is an **upper limit** on the cluster's SZ signal ($Y_{500}$) and X-ray
luminosity ($L_X$), and therefore on $M_{500}$. If that limit falls below the
richness mass (or its $+0.2$ dex upper tail), it caps the high end of the DM
bracket and shrinks the factor-$\sim$6 column systematic that currently
dominates the FRB 20230307A budget.

This plan predeclares the experiment that converts those non-detections into an
$M_{500}$ upper limit and propagates it, through the **same** pipeline mNFW path
already used for the cluster column, into a revised DM$_{\rm ICM}$ upper bound —
with a frozen decision rule fixed **before** any survey product is inspected, so
that an unconstraining limit is reported as a null rather than spun as support.

**Goal:** A predeclared, owner-sanctionable $M_{500}$ upper limit for
J115120.4+714435 derived from Planck PSZ2 (SZ) and RASS/MCXC (X-ray) selection
functions, and the resulting DM$_{\rm ICM}$ upper bound computed through
`dm_cluster_mnfw_model`, with an explicit rule for whether/how it enters prose.

**Motivation:** Shrink the factor-$\sim$6 (100–560 pc cm$^{-3}$) cluster-column
bracket that is the single largest systematic in the intervening DM budget, using
one archival query and existing pipeline machinery, without touching any revoked
(wave-1 scattering / τ) lane.

## Current State Analysis

**Existing manuscript treatment (origin/main; local checkout is 2 behind):**
- `sections/results.tex:101-137` (`sec:dominant-systems`) — the cluster is
  J115120.4+714435, $z=0.200$, $\log M_{500}=14.1$; mNFW column $\approx$180,
  $\beta$-model central $\approx$250, full bracket $\approx$100–560 pc cm$^{-3}$
  ("factor of $\sim$6 end to end"), driven by richness $M_{500}$ ($\sim$0.2 dex),
  $f_{\rm gas}=0.10$–0.16, and profile shape.
- `sections/budget.tex:97-124` (`sec:foreground`) — cluster masses are the
  census per-candidate empirical estimates (PS1/Legacy optical + WISE stellar
  mass → Moster2013 stellar-to-halo relation); the $b\le R_{500}$ aperture
  selects this one cluster; the column uses the `WenHan2024` catalog $M_{500}$,
  $R_{500}$ through the modified-NFW profile.
- `sections/appendix.tex:27-85` (`app:clusters`) — carried mNFW value
  $\approx$184 pc cm$^{-3}$; $b=603.6$ kpc, $b/R_{500}=0.83$, with a $\pm$3%
  geometry systematic (619 kpc uniform recompute); the systematic bracket is
  attributed to `app:host-forward-model`.

**Existing pipeline machinery (submodule `pipeline/`, pin `79b7b0e`):**
- `pipeline/galaxies/foreground/scattering_predict.py:443` —
  `dm_cluster_mnfw_model(m500_msun, z, impact_kpc, m500_to_m200=CLUSTER_M500_TO_M200)`
  → `dm_mnfw_projected` (line 369). This is the M_500 → DM_ICM map to reuse.
- `pipeline/galaxies/foreground/engines_extra.py:329-395` — `ClusterEngine` +
  `_standardize_cluster_columns`, which already query and parse three all-sky
  cluster catalogs via Vizier:
  - PSZ2 (Planck SZ): `J/A+A/594/A27/psz2`, mass column `MSZ` (in $10^{14}\,M_\odot$)
  - MCXC (X-ray, ROSAT-based): `J/A+A/534/A109/mcxc`, `M500`, `R500` (Mpc)
  - MCXC-II: `J/A+A/688/A187/mcxcii`, `M500`, `R500`
  - catalog set: `pipeline/galaxies/foreground/config.py:CLUSTER_VIZIER_CATALOGS`
- Regression anchors already present:
  `pipeline/galaxies/foreground/test_scattering_predict.py:183`
  (`test_dm_mnfw_projected_matches_frb_reference_value`), `:190`, `:198`, `:207`
  (monotonic + linear-in-$f_{\rm hot}$); `test_engines_extra.py:154-191`
  (PSZ2/MCXC column standardization).

**Current behavior:** The cluster $M_{500}$ is the richness/optical estimate; the
X-ray/SZ catalog absences are used only as "not cross-matched," never converted
into a mass constraint. The DM bracket high end (560) reflects the $+0.2$ dex
richness tail combined with high $f_{\rm gas}$ and the $\beta$-model shape.

**Current limitations:**
- The high end of the DM bracket is unconstrained from above by any independent
  mass measurement.
- The referee (correctly) notes the X-ray/SZ non-detections carry unused
  information.

**Data-availability finding (established while writing this plan):**
- The cluster is at RA $=177.835^\circ$, Dec $=+71.743^\circ$ → galactic
  $l=129.48^\circ$, $b=+44.61^\circ$ (astropy `SkyCoord(...).galactic`).
- **eROSITA eRASS1 DR1 does NOT cover this position.** DR1 released only the
  eROSITA-DE hemisphere ($179.9442^\circ < l < 359.9442^\circ$); $l=129.5^\circ$
  lies in the Russian (eROSITA-RU) half, which has no public data release. **The
  deep X-ray option is therefore unavailable**; the X-ray limb of S1 must rest on
  the shallow ROSAT All-Sky Survey (RASS/MCXC), and the SZ limb on Planck PSZ2.
  This materially lowers S1's expected constraining power and is the primary
  decision the owner must weigh (see Risk Assessment + the frozen decision rule).

## Desired End State

**New behavior:** For J115120.4+714435 the analysis carries an
independently-motivated $M_{500}$ **upper limit** from (a) the Planck PSZ2 SZ
selection function and (b) the RASS/MCXC X-ray flux limit, each mapped to a mass
through a peer-published scaling relation, and a DM$_{\rm ICM}$ upper bound
computed through `dm_cluster_mnfw_model` at fixed $z$ and $b$.

**Success Looks Like:**
- A committed artifact
  `pipeline/analysis/cluster_mass_bound/j115120_mass_bound.json` recording, for
  each survey: the catalog non-detection, the survey sensitivity used, the
  scaling relation + citation, and the derived $M_{500}$ upper limit with its
  assumptions.
- A DM$_{\rm ICM}$ upper bound $DM(M_{500}^{\rm UL})$ computed through the same
  mNFW path, plus its $\beta$-model counterpart, and a statement of whether it
  falls below the current 560 pc cm$^{-3}$ high end.
- A **decision recorded against the frozen rule**: either (i) the limit is
  constraining → a drafted one-sentence bracket update for `sec:dominant-systems`
  + `app:clusters`, gated on owner sanction and a clean `consistency_audit`; or
  (ii) the limit is not constraining → a null recorded in the triage doc and this
  plan, prose unchanged.
- No revoked-lane quantity is touched; the census (V4) and budget (V5) inputs
  used are exactly those already cleared.

## What We're NOT Doing

- [ ] Not re-deriving or replacing the richness/optical $M_{500}$ point estimate
      — S1 adds an **upper limit**, it does not swap the central value.
- [ ] Not touching any wave-1 revoked lane (scattering τ fits, $\tau\cdot\Delta\nu_d$
      two-screen test, `tab:beta`, `tab:burst-energies`) — S1 lives entirely in the
      V4/V5-cleared census/budget domain.
- [ ] Not re-computing the impact parameter or the $\pm$3% geometry systematic
      (`app:clusters`); $b=603.6$ kpc and $z=0.200$ are held fixed inputs.
- [ ] Not adding or regenerating any figure (`fig:clusters_icm` is unchanged);
      S1 may only tighten the bracket **text**, not redraw the panel.
- [ ] Not building new catalog-query infrastructure — reuse `ClusterEngine` /
      Vizier and HEASARC/SkyView for RASS; no new pipeline module beyond the
      small mass-bound derivation script.
- [ ] Not entering any number into compiled prose without owner sanction — the
      predeclared record + owner sign-off is the CONTEXT.md §V gate for a new
      quantitative manuscript input.
- [ ] Not pursuing the eROSITA route — confirmed out of the public eRASS1 DR1
      footprint (see Current State).

**Rationale:** S1 is scoped as a cheap, self-contained refinement of one already-
cleared budget input. Everything above either re-opens a gated lane, changes a
fixed geometric input, or exceeds "one archival query."

## Implementation Approach

**Technical Strategy:** Treat each survey non-detection as a one-sided limit.
Convert to $M_{500}^{\rm UL}$ via a published relation, take the tightest across
surveys, and propagate through the existing mNFW cluster-DM function. Freeze the
"does it enter prose?" rule before touching survey data.

**Key Architectural Decisions:**

1. **Decision:** Use the survey **selection functions**, not a bespoke
   detection pipeline, to set the limits.
   - **Rationale:** PSZ2 and MCXC publish completeness/sensitivity as functions
     of $z$ and sky position; this is the standard, defensible, one-query path
     and avoids re-reducing X-ray photons.
   - **Trade-offs:** Coarser than a direct forced-photometry limit, but
     reproducible and citable; a direct RASS aperture limit is added as a
     cross-check in Phase 2, not the primary.
   - **Alternatives considered:** Forced eROSITA photometry (unavailable —
     footprint); joint X-ray+SZ+optical refit (S3-scale, out of scope).

2. **Decision:** Propagate the mass limit through `dm_cluster_mnfw_model`
   (`scattering_predict.py:443`), the identical function that produced the
   carried 184 pc cm$^{-3}$.
   - **Rationale:** Internal consistency — the upper bound and the central value
     share one profile code path, so the comparison to 560 is apples-to-apples.
   - **Trade-offs:** Inherits the mNFW-at-$\log M=14.1$ extrapolation caveat
     already stated in prose; that caveat is unchanged by S1.
   - **Alternatives considered:** Re-deriving the isothermal $\beta$-model column
     independently — done only as the second bracket endpoint, matching how the
     560 high end is currently produced.

3. **Decision:** Freeze a decision rule (below) before inspecting any survey
   value.
   - **Rationale:** CONTEXT.md's central discipline — an unconstraining upper
     limit must not be read as support. Predeclaration is the guard.
   - **Trade-offs:** Commits us to reporting a null; that is the point.

**Frozen decision rule (fixed before Phase 1 data inspection):**
Let $M_{\rm rich}=10^{14.1}\,M_\odot$ (central) and $M_{\rm rich}^{+}=10^{14.3}\,M_\odot$
($+0.2$ dex upper tail). Let $M_{500}^{\rm UL}=\min$(PSZ2 limit, RASS/MCXC limit)
at fixed $z=0.200$.
- **Constraining (enters prose, gated):** $M_{500}^{\rm UL} < M_{\rm rich}^{+}$
  by $\ge 0.1$ dex, AND the corresponding $DM(M_{500}^{\rm UL})$ (mNFW) is
  $\le 500$ pc cm$^{-3}$ (i.e. it demonstrably trims the 560 end). The manuscript
  change is then: replace the "$\approx$560" high end with the X-ray/SZ-capped
  value and add one clause naming the survey + relation + that it is an upper
  limit.
- **Not constraining (null, prose unchanged):** $M_{500}^{\rm UL} \ge M_{\rm rich}^{+}$
  (the surveys are simply blind to a cluster this light at $z=0.2$). Report:
  "the PSZ2/RASS non-detections are consistent with the richness mass and do not
  tighten the column bracket," recorded in the triage doc; **no** number changes.
- Either way the JSON artifact is committed and the outcome is logged; only the
  constraining branch produces a (gated) prose diff.

**Patterns to Follow:**
- Cluster catalog query + column standardization — `engines_extra.py:329-395`.
- mNFW cluster DM + regression-anchored tests —
  `scattering_predict.py:443`, `test_scattering_predict.py:183-207`.
- Predeclared-artifact + frozen-gate discipline — mirrors the A1-trigger
  calibration record referenced in `CONTEXT.md` ("Scint→scattering coupling").

## Implementation Phases

For this numerical/archival work the "failing test" is an assertion against a
known reference value, an analytic invariant, or a published catalog number
(`ai-research-workflows:hardening-research-code`). Each phase commits its
artifact + test.

### Phase 0: Data-availability & footprint confirmation (gate)

**Objective:** Lock down which surveys can actually constrain the mass, and
confirm the cluster's absence from each all-sky catalog at its exact position.

**Tasks:**
- [ ] **Write the failing check** for footprint/coverage in a new
      `pipeline/analysis/cluster_mass_bound/test_availability.py`:

  ```python
  from astropy.coordinates import SkyCoord
  def test_erass1_dr1_excludes_cluster():
      g = SkyCoord("11h51m20.4s", "+71d44m35s").galactic
      # eRASS1 DR1 = eROSITA-DE hemisphere 179.9442 < l < 359.9442 deg
      assert not (179.9442 < g.l.deg < 359.9442)  # l=129.48 -> RU half, no public DR
  ```
- [ ] **Run it, watch it pass** (documents the finding, not a code change):
      `uv run --project pipeline --frozen python -m pytest pipeline/analysis/cluster_mass_bound/test_availability.py -v`
- [ ] **Query the three all-sky cluster catalogs** at the cluster position with a
      generous radius and record the (expected empty) result:

  ```python
  from astropy.coordinates import SkyCoord
  import astropy.units as u
  from pipeline.galaxies.foreground.engines_extra import ClusterEngine
  coord = SkyCoord("11h51m20.4s", "+71d44m35s")
  hits = ClusterEngine().query(coord, 10 * u.arcmin)  # PSZ2 + MCXC + MCXC-II
  # expect: empty (cluster is WenHan2024-only) -> confirms the non-detection premise
  ```
- [ ] **Record** the availability matrix (eROSITA: OUT; PSZ2: in-footprint,
      non-detection; MCXC/RASS: in-footprint, non-detection; direct RASS at
      position: available via HEASARC/SkyView) into
      `pipeline/analysis/cluster_mass_bound/availability.md`.

**Dependencies:** Vizier/HEASARC reachable (network); pipeline env
(`uv run --project pipeline`).

**Verification:**
- [ ] `pytest .../test_availability.py -v` passes (eROSITA excluded).
- [ ] `ClusterEngine().query(...)` returns empty at this position (non-detection
      confirmed), logged in `availability.md`.

### Phase 1: SZ (Planck PSZ2) upper limit

**Objective:** Convert the PSZ2 non-detection into $M_{500}^{\rm UL,SZ}$ at
$z=0.200$ via the Planck $M_{500}$–$Y_{500}$ selection function.

**Tasks:**
- [ ] **Write the failing test** anchoring the PSZ2 completeness limit at
      $z=0.2$ against the published Planck PSZ2 completeness (Planck 2016 XXVII,
      MMF3 union, $\sim$80% completeness), in
      `pipeline/analysis/cluster_mass_bound/test_mass_bound.py`:

  ```python
  def test_psz2_completeness_limit_z02_order_of_magnitude():
      # Planck PSZ2 (2016 XXVII) 80% completeness at z~0.2 is a MASSIVE-cluster
      # threshold: M500 ~ few x 1e14 .. ~1e15 Msun depending on sky noise.
      m_ul = psz2_mass_upper_limit(z=0.200, ra_deg=177.835, dec_deg=71.743)
      assert 2e14 < m_ul < 1.2e15   # sanity band; exact value from noise map
  ```
- [ ] **Run it, watch it fail:** function undefined.
- [ ] **Implement `psz2_mass_upper_limit`** in
      `pipeline/analysis/cluster_mass_bound/mass_bound.py`: read the Planck PSZ2
      completeness (survey noise $\sigma$ at the position from the released
      MMF3 noise map, or the tabulated completeness-vs-$z$ curve), invert the
      Planck $M_{500}$–$Y_{500}$–$z$ scaling (Planck 2014 XX; $Y_{500}\propto
      M_{500}^{5/3}E(z)^{2/3}$ with the calibrated $(1-b)$ bias) at the
      detection threshold → $M_{500}^{\rm UL,SZ}$. Cite the relation + the
      completeness product in the docstring.
- [ ] **Run it, watch it pass.**
- [ ] **Commit:** `git commit -m "feat(cluster-mass): PSZ2 SZ upper-limit mass for J115120.4+714435"`

**Dependencies:** Phase 0; Planck PSZ2 completeness product (Vizier
`J/A+A/594/A27` supplementary, or the Planck Legacy Archive noise map).

**Verification:**
- [ ] `pytest .../test_mass_bound.py::test_psz2_completeness_limit_z02_order_of_magnitude -v` passes.
- [ ] $M_{500}^{\rm UL,SZ}$ and its inputs written to the JSON artifact.

### Phase 2: X-ray (RASS/MCXC) upper limit

**Objective:** Convert the RASS/MCXC X-ray non-detection into
$M_{500}^{\rm UL,X}$ via the MCXC $L_{500}$–$M_{500}$ relation.

**Tasks:**
- [ ] **Write the failing test** anchoring the $L_X$–$M_{500}$ inversion against
      a known MCXC cluster (round-trip: feed an MCXC cluster's catalog $L_{500}$
      back through the relation, recover its catalog $M_{500}$ to <15%):

  ```python
  def test_lx_to_m500_roundtrip_on_known_mcxc_cluster():
      # e.g. a mid-z MCXC entry with tabulated L500, M500 (Piffaretti+ 2011)
      m = lx_to_m500(L500_erg_s=REF_L500, z=REF_Z)
      assert abs(m - REF_M500) / REF_M500 < 0.15
  ```
- [ ] **Run it, watch it fail.**
- [ ] **Implement `lx_to_m500`** in `mass_bound.py` using the MCXC
      $L_{500}$–$M_{500}$ relation (Arnaud/Pratt, as adopted by Piffaretti et al.
      2011 for MCXC), with $E(z)$ evolution; cite in docstring.
- [ ] **Run it, watch it pass.**
- [ ] **Implement `rass_flux_upper_limit`**: obtain a RASS soft-band
      (0.1–2.4 keV) count-rate/flux upper limit at the position — primary path:
      aperture photometry on the RASS exposure + broad-band count maps via
      HEASARC/SkyView at $(l,b)=(129.5,+44.6)$; fallback: the RASS-FSC detection
      limit (Vizier `IX/29`) as a position-averaged bound. Convert flux →
      $L_X(z=0.200)$ (fixed cosmology) → `lx_to_m500` → $M_{500}^{\rm UL,X}$.
      Write a test asserting flux→$L_X$ uses the same cosmology as the budget.
- [ ] **Run it, watch it pass. Commit:**
      `git commit -m "feat(cluster-mass): RASS/MCXC X-ray upper-limit mass for J115120.4+714435"`

**Dependencies:** Phase 0; RASS products (HEASARC/SkyView); MCXC relation
(Piffaretti et al. 2011).

**Verification:**
- [ ] `pytest .../test_mass_bound.py -k "lx or rass" -v` passes.
- [ ] $M_{500}^{\rm UL,X}$ + RASS flux limit + cosmology written to the JSON.

### Phase 3: Propagate to DM_ICM upper bound

**Objective:** Map $M_{500}^{\rm UL}=\min(\text{SZ},\text{X-ray})$ to a
DM$_{\rm ICM}$ upper bound through the existing mNFW path, and compare to the
current 560 pc cm$^{-3}$ high end.

**Tasks:**
- [ ] **Write the failing regression test** re-anchoring the carried central
      value, then asserting the limit trims the bracket:

  ```python
  from pipeline.galaxies.foreground.scattering_predict import dm_cluster_mnfw_model
  def test_carried_central_reproduces():
      dm = dm_cluster_mnfw_model(m500_msun=10**14.1, z=0.200, impact_kpc=603.6)
      assert abs(dm - 184.0) < 15.0   # carried mNFW value, app:clusters
  def test_upper_limit_trims_bracket():
      dm_ul = dm_cluster_mnfw_model(m500_msun=M500_UL, z=0.200, impact_kpc=603.6)
      assert dm_ul < 560.0            # by construction if UL < richness+tail
  ```
- [ ] **Run `test_carried_central_reproduces`, watch it pass** (guards the
      profile path is unchanged; tolerance covers the $f_{\rm hot}$/$m500\_to\_m200$
      defaults — tighten to the exact carried number once reproduced).
- [ ] **Implement `dm_icm_upper_bound`** in `mass_bound.py`: call
      `dm_cluster_mnfw_model` at $M_{500}^{\rm UL}$ (mNFW endpoint) and the
      isothermal $\beta$-model column at the same $M_{500}^{\rm UL}$ (β endpoint),
      both at $z=0.200$, $b=603.6$ kpc; record both.
- [ ] **Run `test_upper_limit_trims_bracket`.** If it *fails* (i.e. $DM_{\rm UL}
      \ge 560$), that is the **null branch** — record it; do not force a pass.
- [ ] **Commit:** `git commit -m "feat(cluster-mass): propagate M500 upper limit to DM_ICM bound"`

**Dependencies:** Phases 1–2; `dm_cluster_mnfw_model` (pin `79b7b0e`).

**Verification:**
- [ ] `test_carried_central_reproduces` passes (184 ± tol).
- [ ] JSON artifact carries $DM(M_{500}^{\rm UL})$ for both profile endpoints.

### Phase 4: Decision & (gated) prose update

**Objective:** Apply the frozen decision rule; produce either a gated prose diff
or a recorded null.

**Tasks:**
- [ ] **Evaluate the frozen rule** against the JSON artifact
      ($M_{500}^{\rm UL}$ vs $M_{\rm rich}^{+}=10^{14.3}$; $DM_{\rm UL}$ vs 500).
- [ ] **Constraining branch:** draft the minimal edit to
      `sections/results.tex:114-117` — replace "$\approx$560" with the capped
      value and add one clause: "…capped from above at
      $M_{500}<M_{500}^{\rm UL}$ by the Planck PSZ2 / RASS non-detection
      ($Y$–$M$ / $L_X$–$M$ relations, citations per Phase 1–2)…"; mirror the
      caption number in `sections/appendix.tex` (`fig:clusters_icm` caption
      bracket). Then run `python3 scripts/consistency_audit.py` (the prose
      contract; the 100–560 bracket is an anchored value — update
      `SAMPLE_COUNT_EXPECTATIONS`/anchors as needed) and `latexmk -pdf`.
      **Do not open a PR until owner sanction is recorded.**
- [ ] **Null branch:** append the null outcome to
      `docs/rse/specs/notes/triage-kulkarni-feedback-2026-07-17.md` (S1 row) and to
      this plan's Review History; prose unchanged.
- [ ] **Commit** (branch, not merged) and surface for owner sanction per the
      standing authorization + §V gate.

**Dependencies:** Phases 0–3; owner sanction (external).

**Verification:**
- [ ] Constraining branch: `python3 scripts/consistency_audit.py` clean;
      `latexmk -pdf` no undefined refs; diff limited to the two bracket numbers +
      one clause + citations.
- [ ] Null branch: triage doc + plan updated; `git diff --stat` shows no `.tex`
      change.

## Success Criteria

### Automated Verification

- [ ] `uv run --project pipeline --frozen python -m pytest pipeline/analysis/cluster_mass_bound/ -v` passes.
- [ ] `test_carried_central_reproduces` reproduces the carried mNFW column
      (184 ± tol) — proves the profile path is untouched.
- [ ] File `pipeline/analysis/cluster_mass_bound/j115120_mass_bound.json` exists
      and records, per survey: non-detection, sensitivity, relation+citation,
      $M_{500}^{\rm UL}$.
- [ ] `python3 scripts/consistency_audit.py` clean (incl. retired-language
      sweep) — run standalone, CI does not.
- [ ] Constraining branch only: `latexmk -pdf` clean, no undefined refs.

### Manual Verification

- [ ] The SZ and X-ray scaling relations are peer-published and correctly
      inverted (spot-check against the source papers' figures).
- [ ] The RASS flux limit at $(l,b)=(129.5,+44.6)$ is the actual position-local
      limit (exposure-weighted), not a survey-average misapplied.
- [ ] The frozen decision rule was applied to the data as written — no post-hoc
      threshold adjustment.
- [ ] **Owner sanction** recorded before any prose change lands (CONTEXT.md §V
      gate for a new quantitative manuscript input).

### Reproducibility & Correctness (research code)

- [ ] Cosmology, catalog versions (PSZ2 `J/A+A/594/A27`, MCXC `J/A+A/534/A109`,
      RASS product ID), scaling-relation constants, and exact query commands
      captured (`ai-research-workflows:ensuring-reproducibility`).
- [ ] Numerical-correctness anchors: $L_X$–$M$ round-trip on a known MCXC
      cluster (<15%); carried mNFW central reproduced (184 ± tol); monotonicity
      $DM(M_{500})$ increasing (existing `test_dm_cluster_mnfw_model_*`).
- [ ] The JSON artifact reproduces from a clean pipeline env.

## Testing Strategy

**Unit Test Coverage (written test-first, in-phase):** footprint exclusion;
PSZ2 completeness-limit sanity band; $L_X$–$M$ round-trip; RASS flux→$L_X$
cosmology consistency; carried-central reproduction; bracket-trim (or its
documented failure = null).

**Integration Tests:**
- [ ] End-to-end: position → `ClusterEngine` (empty) → survey limits →
      $M_{500}^{\rm UL}$ → `dm_cluster_mnfw_model` → JSON, in one script run.

**Manual Testing:**
- [ ] Cross-check $M_{500}^{\rm UL,SZ}$ against the Planck PSZ2 completeness
      figure at $z=0.2$.
- [ ] Confirm the RASS exposure at the position is representative (not a gap).

**Test Data Requirements:** one reference MCXC cluster row (tabulated $L_{500}$,
$M_{500}$, $z$) hard-coded as the round-trip anchor; PSZ2 completeness curve /
noise value at the position.

## Risk Assessment

1. **Risk:** eROSITA unavailable → RASS-only X-ray limit too shallow to beat the
   richness mass → **null result** (surveys blind to a $\log M=14.1$ cluster at
   $z=0.2$).
   - **Likelihood:** Medium-High. RASS is shallow; PSZ2 at $z=0.2$ is a
     massive-cluster ($\gtrsim$few$\times10^{14}$) detector.
   - **Impact:** Medium. A null is still a legitimate, honest outcome that
     retires the referee's suggestion with evidence; it costs one query. It does
     **not** produce a wrong number.
   - **Mitigation:** The frozen decision rule makes the null a first-class,
     reportable outcome; no effort is wasted defending an unconstraining limit.
     Surface this expectation to the owner **before** sanction so the cost/value
     is understood up front.

2. **Risk:** Misapplying a survey-average sensitivity instead of the
   position-local limit → a falsely tight (or loose) bound.
   - **Likelihood:** Medium. **Impact:** High (wrong number in prose).
   - **Mitigation:** Phase 0 records the position-local noise/exposure; the
     manual-verification gate requires confirming the local value; the
     round-trip test guards the relation inversion.

3. **Risk:** The mNFW profile is not validated at $\log M_{500}=14.1$ (already
   flagged in prose) — the DM upper bound inherits that model risk.
   - **Likelihood:** High (known). **Impact:** Low (S1 does not worsen it; the
     caveat is already stated and the β-model endpoint brackets it).
   - **Mitigation:** Report both mNFW and β-model endpoints, as the current
     bracket already does.

## Edge Cases and Error Handling

**Edge Cases:**
1. **Case:** `ClusterEngine` returns a *nearby* PSZ2/MCXC cluster (not the target).
   - **Expected Behavior:** Treat as no detection of *this* system; do not adopt
     a neighbor's mass.
   - **Implementation:** Match within a tight radius + $\Delta z$ before claiming
     a detection; Phase 0 logs any nearby entry.
2. **Case:** RASS exposure gap at the position → no meaningful flux limit.
   - **Expected Behavior:** Drop the X-ray limb, report SZ-only, note the gap.
   - **Implementation:** Phase 2 checks exposure > threshold before computing.

**Error Scenarios:**
1. **Error:** Vizier/HEASARC unreachable.
   - **Handling:** Phase 0 halts with a clear message; no partial artifact.

## Documentation Updates

- [ ] `pipeline/analysis/cluster_mass_bound/availability.md` — the data-
      availability matrix + eROSITA-footprint finding.
- [ ] Docstrings on `psz2_mass_upper_limit`, `lx_to_m500`,
      `rass_flux_upper_limit`, `dm_icm_upper_bound` citing every relation.
- [ ] Triage doc S1 row updated with the outcome (constraining or null).

## Timeline Estimate

- Phase 0: small (footprint + catalog query, mostly done in-plan).
- Phase 1: moderate (PSZ2 completeness inversion).
- Phase 2: moderate (RASS photometry + $L_X$–$M$).
- Phase 3: small (reuse existing function).
- Phase 4: small (rule application + gated diff or null).

**Note:** Estimates; the RASS position-local limit is the main unknown.

## Open Questions

*(None — the eROSITA-availability question that would otherwise sit here was
resolved in Current State: the position is outside the public eRASS1 DR1
footprint, so the plan proceeds on PSZ2 + RASS/MCXC with a predeclared null
branch.)*

---

## References

**Research / triage / handoff:**
- [Triage: Kulkarni-persona feedback (2026-07-17)](../notes/triage-kulkarni-feedback-2026-07-17.md)
- [Handoff: deflation + Kulkarni + attribution (2026-07-17)](../handoff/handoff-2026-07-17-11-28-deflation-kulkarni-and-attribution.md)

**Files Analyzed:**
- `sections/results.tex` (`sec:dominant-systems`, lines 101-137)
- `sections/budget.tex` (`sec:foreground`, lines 85-124)
- `sections/appendix.tex` (`app:clusters`, lines 27-85)
- `pipeline/galaxies/foreground/scattering_predict.py` (`dm_cluster_mnfw_model`, :443)
- `pipeline/galaxies/foreground/engines_extra.py` (`ClusterEngine`, `_standardize_cluster_columns`, :329-395)
- `pipeline/galaxies/foreground/config.py` (`CLUSTER_VIZIER_CATALOGS`)
- `CONTEXT.md` (trust reset; V4 census / V5 budget clearances)

**External Documentation (scaling relations & surveys):**
- Planck 2014 XX — $M_{500}$–$Y_{500}$ SZ scaling; Planck 2016 XXVII — PSZ2 catalog + completeness.
- Piffaretti et al. 2011 — MCXC meta-catalog + $L_{500}$–$M_{500}$; Arnaud/Pratt et al. — L–M calibration.
- Voges et al. 1999 — RASS; RASS-FSC (Vizier `IX/29`) for the position flux limit.
- `WenHan2024` (bib key, `bib/refs.bib:3`) — the DESI Legacy/WISE cluster catalog supplying the richness mass.
- eROSITA-DE DR1 (Merloni et al. 2024) — eRASS1 footprint ($179.9442^\circ<l<359.9442^\circ$); position excluded.

---

## Review History

### Version 1.0 — 2026-07-17
- Initial predeclared experiment record for Kulkarni S1.
- Established the eROSITA eRASS1 DR1 footprint exclusion ($l=129.5^\circ$, RU
  half) — X-ray limb rests on RASS/MCXC, SZ limb on PSZ2.
- Froze the constraining-vs-null decision rule before any survey data inspection.
- **Status: awaiting owner sanction** before Phase 1 data inspection (CONTEXT.md
  §V gate for a new quantitative manuscript input).

### Version 1.1 — 2026-07-17 (same day)
- Owner sanctioned; Phases 0–3 executed
  (`experiment-cluster-xray-sz-mass-bound-2026-07-17.md`).
- Phase 4 hit a gate edge: two rule ambiguities discovered at application time
  (the plan's $M_{\rm rich}=10^{14.1}$ was a prose rounding of the registry's
  $1.48\times10^{14}$, shifting the intended margin threshold from $10^{14.2}$
  to $10^{14.27}$; and the ECF-endpoint convention was unpinned). Surfaced to
  the owner rather than self-adjudicated.
- **Owner adjudication: constraining, conservative endpoint**
  ($M_{500}\le1.7\times10^{14}$, worst-case ECF). Prose bracket re-derived by
  truncating the mass prior in `scripts/dm_budget_uncertainty.py`: ≈80–330
  pc cm$^{-3}$ (factor ~4), landed via `ms/s1-xray-mass-cap-20260717`.
- Deferred: landing `pipeline/analysis/cluster_mass_bound/` code+tests in the
  FLITS submodule (its working tree carries the live joint-tf lane; the
  scratchpad scripts and this record preserve reproducibility meanwhile).
