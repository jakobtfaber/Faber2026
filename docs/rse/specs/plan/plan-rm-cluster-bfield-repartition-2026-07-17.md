# Implementation Plan: RM re-partition and intracluster B-field bound for the FRB 20230307A sightline (Kulkarni Thread 1)

---
**Date:** 2026-07-17
**Author:** AI Assistant
**Status:** Draft — predeclared cross-paper experiment record, awaiting owner sanction (CONTEXT.md §V gate; cross-paper coordination gate below)
**Related Documents:**
- [Triage: Kulkarni-persona feedback (2026-07-17)](../triage/triage-kulkarni-feedback-2026-07-17.md) — Thread 1 = "RM → intervening cluster/CGM B-field", verdict *Chase (strongest; cross-paper seam)*
- [Experiment record: X-ray/SZ mass bound (Kulkarni S1)](../experiment/experiment-cluster-xray-sz-mass-bound-2026-07-17.md) — supplies the X-ray-capped cluster mass and the truncated-prior DM bracket this plan consumes
- [Plan: S1 mass bound](../plan/plan-cluster-xray-sz-mass-bound-2026-07-17.md) — the predeclared-record precedent this plan mirrors
- [Handoff 2026-07-17 12:58](../handoff/handoff-2026-07-17-12-58-s1-landed-owner-decisions-closed.md) — declares Thread 1 the hot lane
- `CONTEXT.md` (repo root) — trust contract; every input used here is V4/V5-cleared or comes from the polarization companion
- `codetections_polarization/issues.md` — companion coordination ledger (ISSUE-008/009 precedent; Thread 1 adds ISSUE-010 at Phase 3)

---

## Overview

The polarization companion (Pandhi et al., `codetections_polarization/main.tex`,
owner-supplied draft refreshed 2026-07-17 by session `kulkarni-explore`, journal
lane `pol-companion-sync`) now carries a complete RM budget for the twelve
codetected FRBs. For FRB 20230307A (nickname *phineas*) it reports
$\mathrm{RM}_{\rm obs}=-473.49(9)$ rad m$^{-2}$ and attributes the residual after
Galactic/ionospheric/IGM foregrounds **entirely to the host**:
$\mathrm{RM}_{\rm host}=-756\pm15$ rad m$^{-2}$ (host frame),
$\mathrm{DM}_{\rm host}=464^{+56}_{-130}$ pc cm$^{-3}$,
$\langle B_{\parallel,{\rm host}}\rangle=-2.0^{+0.2}_{-0.8}\,\mu$G
(`main.tex:165`, Table `tb:host_props`). Their component equation
(`main.tex`, eq. `eq:rm_comps`) contains **no intervening term** — the word
"cluster" does not appear in their budget.

Faber2026's V4/V5-cleared census says this sightline crosses the cluster
J115120.4+714435 at $b/R_{500}=0.83$ ($z_{\rm cl}=0.200$), and after Kulkarni S1
the cluster mass is X-ray-capped ($M_{500}\le1.7\times10^{14}\,M_\odot$) with an
intracluster column of $\approx$184 pc cm$^{-3}$ (mNFW central, observer frame)
inside a 95% bracket of [84, 328] pc cm$^{-3}$ (β-model truncated-prior MC).
A magnetized ICM crossed at that impact parameter contributes
$\mathrm{RM}_{\rm cl}$ to $\mathrm{RM}_{\rm obs}$; every rad m$^{-2}$ assigned to
the cluster comes out of their $\mathrm{RM}_{\rm host}$ and moves their
$\langle B_{\parallel,{\rm host}}\rangle$. Conversely, their zero-cluster
attribution is an implicit **upper limit on the cluster field**: with our pinned
column, neglecting the cluster term is algebraically equivalent to asserting
$|\langle B_\parallel\rangle_{\rm ICM}|\lesssim0.04$–$0.16\,\mu$G along the
chord (derivation in Implementation Approach) — an order of magnitude below
typical measured cluster-outskirt fields.

This is the two-sided seam the triage doc called Thread 1: our DM$_{\rm int}$
(V4/V5-cleared, now X-ray-capped) is exactly the quantity their RM budget is
missing, and their RM is exactly the quantity that turns our capped column into
a $B_\parallel$ constraint. Both directions are quantitative and cheap; the risk
is entirely in *claim governance* (a cross-paper attribution change), which is
why this plan predeclares the decision rule and the coordination contract before
any derived number exists.

**Goal:** A predeclared, owner-sanctionable record that (a) quantifies the
cluster term the companion's RM budget omits, (b) produces the conditional
re-partition table $(\mathrm{RM}_{\rm host},\langle B_{\parallel,{\rm host}}\rangle,
\langle B_{\parallel,{\rm cl}}\rangle)$ as a function of the cluster field, and
(c) routes any manuscript change — in **either** paper — through a frozen
materiality rule plus a both-owners coordination gate.

**Motivation:** Strongest surviving Kulkarni discovery thread; unblocked on both
sides as of 2026-07-17 (S1 landed; companion refreshed with full RM data); uses
no revoked-lane quantity.

## Current State Analysis

**Companion draft (separate-active lane — read-only for this plan):**
- `codetections_polarization/main.tex:131-146` — DM/RM component equations
  (`eq:dm_comps`, `eq:rm_comps`): ion + disk + halo + IGM + host/(1+z)². No
  intervening term. $\langle B_{\parallel,{\rm host}}\rangle = 1.232\,
  \mathrm{RM}_{\rm host}/\mathrm{DM}_{\rm host}$ (`eq:b_host`).
- `codetections_polarization/main.tex:146` — MC procedure ($10^4$ trials,
  following Pandhi et al. 2025, `2025ApJ...982..146P`): DM$_{\rm disk}$ =
  NE2025 ± 20%; DM$_{\rm halo}$ = lognormal $\log_{10}30\pm0.2$ dex;
  RM$_{\rm disk+halo}$ = Gaussian from the Hutschenreuter et al. 2022 Galactic
  RM map (A&A 657, A43; key in `codetections_polarization/ref.bib`);
  DM$_{\rm IGM}$ = Baptista et al. 2024 eq. 1;
  RM$_{\rm IGM}\sim\mathcal{N}(0,6)$ rad m$^{-2}$.
- `codetections_polarization/main.tex:165` — the phineas row of `tb:host_props`
  (values quoted in Overview).
- `codetections_polarization/issues.md` — ISSUE-008 (repeater wording),
  ISSUE-009 (z provenance) open; Thread 1 will add ISSUE-010 (Phase 3, gated).

**Faber2026 side (origin/main = `56cf4c4e`):**
- `pipeline/galaxies/foreground/data/intervening_census_registry.csv:23` — the
  pinned cluster row: J115120.4+714435 (Wen+ id 1254337), $b=603.6$ kpc,
  $b/R_{500}=0.83$, $M_{500}=1.48\times10^{14}$, $R_{500}=0.729$ Mpc,
  $z_{\rm cl}=0.200\pm0.0001$ (DESI spec), host $z=0.271$ (spec;
  Verdi-standard-confirmed 0.2710 — see project memory
  `verdi-draft-is-redshift-standard`; **no dependency on the pending
  z-propagation lane**).
- `scripts/dm_budget_uncertainty.py:556-564` (origin/main) — `CL_M500 = 1.48e14`,
  `CL_M500_XRAY_UL = 1.67e14`, `CL_Z = 0.200`, `CL_B_KPC = 603.6`; module RNG
  seed 20260707; `cluster_column_range()` (:599) is the truncated-prior β-model
  MC.
- `scripts/dm_budget_uncertainty.csv:12-13` (origin/main) — the machine-readable
  bracket this plan pins to (per the S1 learning — *thresholds come from
  pipeline outputs, not prose*): β-model p16/p50/p84 = 137/200/265; 95% CI
  [84, 328] pc cm$^{-3}$ (observer frame). The carried mNFW central is 184
  (`sections/appendix.tex`, `fig:clusters_icm` caption).
- `scripts/dm_budget_uncertainty.csv:7` — our phineas host row: DM$_{\rm host}$
  (rest) p50 = 87 [−37, 191] pc cm$^{-3}$, $P(<0)=0.236$. Note the cross-paper
  DM consistency: their host-only 464 (rest) ≈ our host 87 (rest) + our
  intervening 243 (obs; ≈292 at the cluster rest frame) modulo differing
  Galactic/IGM models — the DM seam and the RM seam are the same seam.
- `sections/results.tex:101-157` (`sec:dominant-systems`) — the manuscript's
  cluster discussion; currently contains **no RM content anywhere in
  Faber2026** (checked origin/main), so the Faber2026 surface for Thread 1 is at
  most one forward-reference sentence.

**Current behavior:** The two papers partition the same sightline differently
and neither states the tension: their RM budget has no cluster; our DM budget
has a dominant cluster. No coordination artifact exists.

**Current limitations:** Any re-partition claim touches a manuscript we do not
own. The companion's numbers are a working draft (uncommitted zip refresh);
their values may still move (notably if their depol-τ correlation is revised —
see τ firewall below).

**Predeclaration honesty note:** The companion's RM values were already read
(journal 12:19 entry) before this plan was written — blindness to
$\mathrm{RM}_{\rm obs}$ is not available. What this record freezes *before
computation* is the derived-quantity definitions, the materiality thresholds,
and the literature-comparison selection criteria (Phase 1), so the
constraining-vs-null outcome is not steerable after the fact.

## Desired End State

- A committed JSON artifact
  (`scripts/rm_cluster_repartition.json`, produced by
  `scripts/rm_cluster_repartition.py`) recording: the pinned inputs (both
  papers, with file:line provenance), the negligibility-field algebra, the
  literature comparison set with citations, and the conditional re-partition
  table.
- A record figure (`docs/rse/decks/thread1-2026-07-17/rm_repartition_sensitivity.pdf`,
  non-manuscript) showing $(\mathrm{RM}_{\rm host},
  \langle B_{\parallel,{\rm host}}\rangle)$ vs. assumed
  $\langle B_{\parallel,{\rm cl}}\rangle$ across the pinned DM bracket.
- A coordination memo (`docs/rse/specs/memo/memo-thread1-rm-repartition-<date>.md`)
  the owner can hand to the companion authors, with proposed language options
  for both manuscripts.
- A decision recorded against the frozen rule: **material** (seam enters
  cross-paper coordination), **null** (cluster term empirically negligible;
  recorded, no prose change), or **marginal** (owner adjudication — predeclared
  as such).
- No manuscript edit in either paper before the both-owners gate (below).

## What We're NOT Doing

- [ ] **Not editing `codetections_polarization/` in Phases 0–2.** The lane is
      separate-active (uncommitted owner-supplied refresh). The only permitted
      write is the append-only ISSUE-010 entry in `issues.md`, in Phase 3, after
      owner sanction.
- [ ] **Not touching any τ / scattering quantity.** The companion's new ≥3σ
      depol–RM–τ correlation consumes paper-I taus including wave-1-revoked
      fits (flagged in journal 12:19); Thread 1 uses no τ anywhere. If a
      re-partition result interacts with their correlation section, that is
      *their* edit, surfaced in the memo, not computed here.
- [ ] **Not re-attributing their depolarization $\sigma_{\rm RM}$** (0.82
      rad m$^{-2}$ for phineas, `main.tex:230`). $\sigma_{\rm RM}$ from L/I
      depolarization probes RM fluctuations across the coherent emission patch
      (≲ AU–pc transverse scale at the screen); ICM turbulence at kpc scales is
      smooth over that patch. Only the *mean* LOS RM is in scope.
- [ ] **Not changing DM-side numbers.** DM$_{\rm int}$ = 243, the [84, 328]
      bracket, and the S1 mass cap are consumed as frozen inputs; no budget
      rerun.
- [ ] **Not claiming a $B_\parallel$ *measurement* of the ICM** without the
      both-owners gate — the unconditional deliverable is a sensitivity/bound
      statement, not an attribution.
- [ ] **Not modeling field reversals / turbulent suppression beyond a stated
      coherent-field convention** (the coherent $\langle B_\parallel\rangle$ is
      the density-weighted chord average; reversals lower $|{\rm RM}|$ at fixed
      field strength, making every bound quoted here conservative in the same
      direction — stated once, not simulated).
- [ ] **Not waiting on the z-propagation (Verdi) lane** — phineas $z=0.271$ is
      Verdi-confirmed unchanged.

**Rationale:** The physics is two lines of algebra on pinned inputs plus an MC
that mirrors a published procedure; every excluded item is either another
paper's edit, a revoked lane, or scope the referee did not ask for.

## Implementation Approach

**Technical Strategy:** Extend the companion's own MC budget structure by one
term — $\mathrm{RM}_{\rm cl}/(1+z_{\rm cl})^2$ with
$\mathrm{RM}_{\rm cl} = 0.812\,\langle B_{\parallel,{\rm cl}}\rangle\,
\mathrm{DM}_{\rm cl}^{\rm rest}$ — with DM$_{\rm cl}$ drawn from our
truncated-prior cluster MC, and scan $\langle B_{\parallel,{\rm cl}}\rangle$
rather than assert it. All conversions through the two pinned redshifts.

**Key frame conventions (fixed here, tested in Phase 0):**
- $z_{\rm host}=0.271$ → $(1+z_{\rm host})^2 = 1.6154$;
  $z_{\rm cl}=0.200$ → $(1+z_{\rm cl}) = 1.200$, $(1+z_{\rm cl})^2 = 1.440$.
- Budget DM$_{\rm cl}$ values are **observer frame** (`beta_model_dm` returns
  `dm_rest / (1+z)`); rest-frame column at the cluster =
  $\mathrm{DM}_{\rm cl}^{\rm obs}\times(1+z_{\rm cl})$.
- Observed-frame cluster RM contribution per unit field:
  $$\frac{\mathrm{RM}_{\rm cl}^{\rm obs}}{\langle B_{\parallel,{\rm cl}}\rangle}
  = \frac{0.812\,\mathrm{DM}_{\rm cl}^{\rm obs}(1+z_{\rm cl})}{(1+z_{\rm cl})^2}
  = 0.6767\,\mathrm{DM}_{\rm cl}^{\rm obs}
  \;\;\mathrm{rad\,m^{-2}\,\mu G^{-1}}.$$
- Their host-frame $\sigma(\mathrm{RM}_{\rm host})=15$ →
  observed-frame materiality yardstick
  $\sigma_{\rm RM}^{\rm obs} = 15/1.6154 = 9.29$ rad m$^{-2}$ (comparable to
  their RM$_{\rm IGM}$ prior width, 6 rad m$^{-2}$ — noted, not double-counted).

**The negligibility-field algebra (the unconditional deliverable):**
$B_{\rm neg}(\mathrm{DM}) \equiv \sigma_{\rm RM}^{\rm obs} /
(0.6767\,\mathrm{DM}_{\rm cl}^{\rm obs})$ — the coherent field above which the
cluster term exceeds their quoted 1σ on RM$_{\rm host}$:

| DM$_{\rm cl}^{\rm obs}$ (pc cm$^{-3}$) | source | RM$_{\rm cl}^{\rm obs}/B$ (rad m$^{-2}/\mu$G) | $B_{\rm neg}$ ($\mu$G) |
|---|---|---|---|
| 84 | 95% CI low (`csv:13`) | 56.8 | 0.163 |
| 184 | mNFW carried central | 124.5 | 0.075 |
| 200 | β-model p50 (`csv:12`) | 135.3 | 0.069 |
| 328 | 95% CI high (`csv:13`) | 222.0 | 0.042 |

(Computed at plan time from pinned inputs; Phase 0's tests re-derive every row —
any mismatch is a blocking error, mirroring the S1 registry-vs-prose lesson.)
For scale: at $\langle B_{\parallel,{\rm cl}}\rangle=0.5\,\mu$G the central
column contributes $\approx62$ rad m$^{-2}$ (obs) — 13% of RM$_{\rm obs}$ and
$\sim$7σ of their RM$_{\rm host}$ uncertainty; their zero-cluster budget is
*not* obviously safe, which is precisely what Phase 1 tests against published
outskirt fields.

**Frozen decision rule (fixed before Phase 1 literature values or any Phase 2
MC output is inspected):**

Let $\mathrm{RM}_{\rm lit}$ = the median published |RM| excess (or
$\sigma_{\rm RM}$ scatter excess, per study convention) through cluster
outskirts at normalized impact $b/R_{500}\in[0.6,1.0]$, from the Phase-1
selection (criteria below), scaled to observed frame at $z_{\rm cl}=0.2$; where
a study reports $B_\parallel$ instead, convert through our pinned central column
(184 → the 124.5 rad m$^{-2}/\mu$G row).

- **Material:** $\mathrm{RM}_{\rm lit} \ge 2\,\sigma_{\rm RM}^{\rm obs}$
  (= 18.6 rad m$^{-2}$) → the companion's no-intervening-term attribution
  understates the RM$_{\rm host}$ error; the memo + re-partition table go to the
  both-owners gate. (Note: nothing enters prose automatically; "material" opens
  coordination, not edits.)
- **Null:** $\mathrm{RM}_{\rm lit} < \sigma_{\rm RM}^{\rm obs}$
  (= 9.29 rad m$^{-2}$) → the cluster term is empirically negligible at this
  impact parameter; record the null in this plan + the triage doc; no
  manuscript change on either side; thread closed.
- **Marginal** ($9.29 \le \mathrm{RM}_{\rm lit} < 18.6$): owner adjudication
  with the full record — predeclared as an adjudication, not an agent choice.

**Phase-1 literature selection criteria (frozen now, applied before reading
values):** peer-reviewed; statistical (≥10 background/embedded sightlines) or a
mass-matched simulation calibrated to RM data; reports RM (or $B_\parallel$) vs.
normalized impact parameter covering $b/R_{500}\in[0.6,1.0]$; prefer mass range
overlapping $\sim10^{14}$–$3\times10^{14}\,M_\odot$; ≥3 independent studies or
all that exist if fewer. Candidate pool (fixed as the *starting* search set;
studies may be added only by the criteria, never removed for their values):
Clarke et al. 2001/2004; Bonafede et al. 2010 (Coma); Böhringer et al. 2016;
Govoni et al. 2017; Stuardi et al. 2021; Osinga et al. 2022 & 2025 (statistical
RM vs. $r/R_{500}$); Anderson et al. 2021.

**Both-owners coordination gate (the cross-paper contract):**
1. **Interface freeze:** the companion values consumed are exactly the
   `tb:host_props` phineas row + the MC prior specification of the 2026-07-17
   owner-supplied draft; they are copied into the JSON artifact with
   provenance. If the companion draft's row changes, the record version-bumps
   and Phase 2 re-runs before any further step.
2. **Claim ownership:** the ICM $B_\parallel$ bound/attribution naturally lives
   in the **companion** (RM is their measurement; Faber2026 supplies
   DM$_{\rm cl}$ and the mass cap, citable as paper I + the S1 record).
   Faber2026's own surface is at most one sentence in `sec:dominant-systems`
   forward-referencing the companion. Neither edit lands without **both** the
   repo owner's sanction and the companion lead's (Ayush Pandhi's) agreement.
3. **Transport:** the owner carries `memo-thread1-…md` to the companion
   authors; the agent drafts it (Phase 3) and appends ISSUE-010 to
   `codetections_polarization/issues.md` (append-only; the file is the
   established coordination ledger and the pol-companion lane's only permitted
   write).
4. **Standing:** consistent with the standing push/PR authorization, all
   Thread-1 commits are docs/scripts-side; nothing in `sections/` or
   `codetections_polarization/main.tex` moves under this plan's authority
   alone.

**Patterns to Follow:**
- Predeclared record + frozen gate: `plan-cluster-xray-sz-mass-bound-2026-07-17.md`.
- Root-side analysis script + tests: `scripts/dm_budget_uncertainty.py` +
  `tests/test_dm_budget_uncertainty.py` (no submodule write — the FLITS working
  tree is the live joint-tf lane).
- Seeded MC + machine-readable CSV/JSON output: same script.

## Implementation Phases

### Phase 0: Pin verification + frame algebra (pre-sanction; no new data)

**Objective:** Machine-verify every pinned input and the conversion algebra, so
the record cannot repeat S1's prose-rounding trap.

**Tasks:**
- [ ] **Write the failing tests** in `tests/test_rm_cluster_repartition.py`:

  ```python
  import csv, math
  from pathlib import Path

  from scripts.rm_cluster_repartition import (
      PINNED, rm_per_microgauss_obs, b_negligibility,
  )

  REGISTRY = Path("pipeline/galaxies/foreground/data/intervening_census_registry.csv")

  def test_registry_row_matches_pins():
      # S1 lesson: thresholds from the machine-readable source, never prose.
      rows = [r for r in csv.DictReader(REGISTRY.open())
              if r["type"] == "cluster" and r["tns"] == "FRB 20230307A"]
      assert len(rows) == 1
      r = rows[0]
      assert float(r["m500_1e14msun"]) == PINNED["m500_1e14"] == 1.48
      assert float(r["impact_kpc"]) == PINNED["b_kpc"] == 603.6
      assert float(r["best_z"]) == PINNED["z_cl"] == 0.200
      assert float(r["host_z_spec"]) == PINNED["z_host"] == 0.271

  def test_budget_csv_bracket_matches_pins():
      rows = {row[0]: row[1:] for row in csv.reader(
          Path("scripts/dm_budget_uncertainty.csv").open())}
      assert [int(x) for x in rows["cluster_95CI_lo_hi"]] == [84, 328]
      assert [int(x) for x in rows["cluster_beta_model_p16_p50_p84"]] == [137, 200, 265]

  def test_frame_algebra():
      # RM_cl(obs)/B = 0.812 * DM_obs * (1+z_cl) / (1+z_cl)^2 = 0.6767 * DM_obs
      assert math.isclose(rm_per_microgauss_obs(184.0), 124.5, rel_tol=5e-3)
      assert math.isclose(rm_per_microgauss_obs(84.0), 56.8, rel_tol=5e-3)
      assert math.isclose(rm_per_microgauss_obs(328.0), 222.0, rel_tol=5e-3)

  def test_negligibility_fields():
      # sigma_RM_host(obs) = 15 / (1+0.271)^2 = 9.29 rad/m^2
      assert math.isclose(b_negligibility(184.0), 0.075, abs_tol=0.002)
      assert math.isclose(b_negligibility(84.0), 0.163, abs_tol=0.003)
      assert math.isclose(b_negligibility(328.0), 0.042, abs_tol=0.002)
  ```
- [ ] **Run, watch fail:** `uv run --project pipeline --frozen python -m pytest tests/test_rm_cluster_repartition.py -v` (module absent).
- [ ] **Implement the minimal module** `scripts/rm_cluster_repartition.py`: a
      `PINNED` dict (every value above with a `# file:line` provenance comment,
      including the companion row: `rm_obs=-473.49`, `rm_obs_err=0.09`,
      `rm_host=-756`, `rm_host_err=15`, `dm_host=464`,
      `b_host_mug=-2.0` ← `codetections_polarization/main.tex:165`),
      `rm_per_microgauss_obs(dm_obs)`, `b_negligibility(dm_obs)`.
- [ ] **Run, watch pass. Commit:**
      `git commit -m "feat(thread1): pinned inputs + frame algebra for RM re-partition" -- scripts/rm_cluster_repartition.py tests/test_rm_cluster_repartition.py`

**Dependencies:** none (all inputs already on origin/main or in the companion
draft). Executable pre-sanction — it inspects nothing new.

**Verification:**
- [ ] All four tests pass; the plan's table is reproduced by code, not prose.

### Phase 1: Literature outskirt-RM comparison (post-sanction)

**Objective:** Fix $\mathrm{RM}_{\rm lit}$ per the frozen selection criteria and
classify material / null / marginal.

**Tasks:**
- [ ] **Apply the frozen criteria** to the candidate pool (+ any study the
      criteria admit); for each admitted study record: citation, sample size,
      mass range, the RM (or $B_\parallel$) excess at $b/R_{500}\in[0.6,1.0]$,
      and the conversion to observed-frame rad m$^{-2}$ at $z_{\rm cl}=0.2$
      (studies quote local-universe RMs; the $(1+z_{\rm cl})^{-2}$ dilution is
      applied to *our* predicted contribution, not to their local values —
      i.e., convert their $B_\parallel$ through the 124.5 row, or their RM
      through $\times1/1.44$ only when the study's clusters are proxies for the
      $z=0.2$ screen; state the choice per study in the artifact).
- [ ] **Record** the admitted set + $\mathrm{RM}_{\rm lit}$ (median) into the
      JSON artifact via a `literature` block in
      `scripts/rm_cluster_repartition.py`.
- [ ] **Write the classification test** (against the frozen thresholds, not the
      hoped-for outcome):

  ```python
  def test_classification_is_computed_from_frozen_thresholds():
      from scripts.rm_cluster_repartition import classify, SIGMA_RM_OBS
      assert math.isclose(SIGMA_RM_OBS, 9.29, abs_tol=0.01)
      assert classify(rm_lit=25.0) == "material"
      assert classify(rm_lit=5.0) == "null"
      assert classify(rm_lit=12.0) == "marginal"
  ```
- [ ] **Run, watch pass. Commit** with the artifact.

**Dependencies:** Phase 0; owner sanction (this is the first data inspection).

**Verification:**
- [ ] Every admitted/rejected candidate has a criteria-based reason logged.
- [ ] The classification is emitted by `classify(rm_lit_measured)`, printed in
      the script's `main()`, and recorded in the JSON.

### Phase 2: Conditional re-partition MC (post-sanction)

**Objective:** The quantitative table: what happens to their
$\mathrm{RM}_{\rm host}$ and $\langle B_{\parallel,{\rm host}}\rangle$, and what
$\langle B_{\parallel,{\rm cl}}\rangle$ is implied, as a function of the cluster
field, with DM uncertainties propagated.

**Tasks:**
- [ ] **Write the failing regression test** anchoring the $f=0$ (no-cluster)
      corner to the companion's published row — the MC must reproduce *their*
      analysis before extending it:

  ```python
  def test_zero_cluster_corner_reproduces_companion():
      from scripts.rm_cluster_repartition import repartition_mc
      out = repartition_mc(b_cl_grid=[0.0], n=10_000, seed=20260707)
      row = out[0.0]
      # their tb:host_props: RM_host = -756 +/- 15, B_host = -2.0 +0.2/-0.8
      assert abs(row["rm_host_p50"] - (-756)) < 30      # tolerance: our
      assert abs(row["b_host_p50"] - (-2.0)) < 0.3      # foreground models
      # differ in detail (NE2025 access etc.); tighten after first run,
      # or record the residual as a model-difference systematic.
  ```
- [ ] **Run, watch fail. Implement `repartition_mc`:** mirror their MC
      (`main.tex:146` priors, $10^4$ trials) with the added term; DM$_{\rm cl}$
      drawn by reusing `cluster_column_range()` imported from
      `scripts/dm_budget_uncertainty.py` (same truncated prior, module seed
      20260707); $\langle B_{\parallel,{\rm cl}}\rangle$ scanned over
      `[0, ±0.1, ±0.25, ±0.5, ±1.0] μG` (both signs — the cluster field
      direction is unknown and RM$_{\rm obs}<0$ makes sign consequential).
      If the Hutschenreuter et al. 2022 map is not fetchable offline,
      substitute a Gaussian pinned to the values their draft implies for this
      sightline and record the substitution in the artifact (their
      RM$_{\rm disk+halo}$ prior is recoverable from RM$_{\rm obs}$ −
      RM$_{\rm IGM}$ − RM$_{\rm host}$/(1+z)² closure on their own MC medians).
- [ ] **Run, watch pass** (or record the residual as the model-difference
      systematic if outside tolerance — do not tune to force agreement).
- [ ] **Emit** the re-partition table into the JSON + the record figure
      `docs/rse/decks/thread1-2026-07-17/rm_repartition_sensitivity.pdf`
      (three panels: RM$_{\rm host}$, $B_{\rm host}$, and implied
      RM$_{\rm cl}^{\rm obs}$ vs. $B_{\rm cl}$, with the [84, 328] DM band
      shaded) — per the visibility preference, this ships with the PR.
- [ ] **Commit.**

**Dependencies:** Phases 0–1.

**Verification:**
- [ ] Zero-cluster corner agrees with (or has a recorded systematic against)
      their published row.
- [ ] Seeded: two consecutive runs byte-identical JSON.
- [ ] The figure exists and is referenced from the memo.

### Phase 3: Coordination memo + gated ledger entry (post-sanction)

**Objective:** Package for the both-owners gate; no manuscript edits.

**Tasks:**
- [ ] **Draft** `docs/rse/specs/memo/memo-thread1-rm-repartition-2026-07-XX.md`:
      the seam in one paragraph; the negligibility table; the classification;
      the re-partition table + figure; two proposed language options for the
      companion (add an intervening term with the S1-capped column; or keep
      host-only and state the implied ICM-field ceiling) and the one-sentence
      Faber2026 forward reference; explicit statement of what each option does
      to their $\langle B_{\parallel,{\rm host}}\rangle=-2.0$ headline.
- [ ] **Append ISSUE-010** to `codetections_polarization/issues.md` (append-only
      edit, ISSUE-008/009 format): assignee Jakob (raise with Ayush), pointing
      at the memo; acceptance criteria = both-owner decision recorded.
- [ ] **Surface to owner** for sanction of the memo hand-off; log the decision
      in this plan's Review History.

**Dependencies:** Phases 1–2; owner availability.

**Verification:**
- [ ] Memo self-contained (a companion author needs no repo access to evaluate
      it).
- [ ] `git diff` shows `issues.md` touched only by appended lines.

### Phase 4: Gated prose (both papers; only after both-owners agreement)

**Objective:** Land whichever language option the owners choose.

**Tasks:**
- [ ] Faber2026 side (if chosen): one sentence in
      `sections/results.tex` (`sec:dominant-systems`, after the bracket
      sentence at :116-129): "The magnetized counterpart of this column is
      examined in the polarization companion (Pandhi et al. in prep.), where
      attributing even a $0.1\,\mu$G coherent intracluster field re-partitions
      the sightline's rotation measure at the $\sim$1σ level of the
      host-attributed term." (exact wording per memo outcome); then
      `python3 scripts/consistency_audit.py` and `latexmk -pdf`; focused
      `ms/…` branch + PR per precedent.
- [ ] Companion side: their edit, their repo/draft — out of this plan's
      authority; tracked via ISSUE-010 only.

**Dependencies:** Phase 3 gate passed by both owners.

**Verification:**
- [ ] Constraining branch: audit + latexmk clean; diff = one sentence.
- [ ] ISSUE-010 closed with the recorded decision.

## Success Criteria

### Automated Verification
- [ ] `uv run --project pipeline --frozen python -m pytest tests/test_rm_cluster_repartition.py -v` passes (all phases' tests).
- [ ] `python3 scripts/rm_cluster_repartition.py` reproduces the JSON artifact
      byte-identically from a clean checkout (seeded).
- [ ] Zero-cluster corner test passes or carries a recorded model-difference
      systematic (never silently tuned).
- [ ] Phase 4 (Faber2026 branch only): `python3 scripts/consistency_audit.py`
      clean; `latexmk -pdf` no undefined refs.

### Manual Verification
- [ ] Frozen thresholds were not moved after Phase-1 values were read (diff the
      plan's rule section against the merged version).
- [ ] Literature admissions/rejections follow the frozen criteria (spot-check
      two).
- [ ] The memo's language options are faithful to the numbers (owner read).
- [ ] Both-owners gate recorded before any manuscript edit (either paper).

### Reproducibility & Correctness
- [ ] Every pinned value carries file:line provenance in `PINNED`.
- [ ] Seeds fixed (20260707); MC trial count recorded; environment
      `uv run --project pipeline --frozen`.
- [ ] Frame conventions unit-tested (`test_frame_algebra`).

## Testing Strategy

**Unit:** pin-verification (registry, CSV), frame algebra, negligibility
fields, classification thresholds, zero-cluster reproduction, seed determinism.
**Integration:** full script run → JSON + figure in one pass.
**Manual:** memo review; literature spot-checks; cross-paper number agreement
(their row vs. our artifact copy).

## Risk Assessment

1. **Risk:** Companion draft values move under us (working, uncommitted draft).
   - **Likelihood:** Medium. **Impact:** Medium (stale memo).
   - **Mitigation:** Interface freeze in the artifact + version-bump rule
     (coordination contract item 1).
2. **Risk:** Published outskirt-RM literature is heterogeneous (different mass
   ranges, conventions) → $\mathrm{RM}_{\rm lit}$ is contestable.
   - **Likelihood:** High. **Impact:** Medium (classification disputes).
   - **Mitigation:** Frozen selection criteria + per-study conversion recorded;
     the marginal band routes genuine ambiguity to the owner instead of
     forcing a call.
3. **Risk:** Our foreground models vs. theirs (NE2025 / Galactic RM map access)
   make the zero-cluster corner irreproducible offline.
   - **Likelihood:** Medium. **Impact:** Low-Medium.
   - **Mitigation:** The closure-recovery substitution (Phase 2) with the
     substitution recorded; the corner test tolerance is honest and the
     residual becomes a stated systematic.
4. **Risk:** Cross-paper governance failure — a number escapes into either
   manuscript before agreement.
   - **Likelihood:** Low (this plan exists to prevent it). **Impact:** High.
   - **Mitigation:** The both-owners gate is the only path to Phase 4; the
     ISSUE-010 ledger entry makes the pending state visible on the companion
     side too.

## Edge Cases and Error Handling

1. **Case:** A study reports outskirt RM consistent with zero at
   $b/R_{500}\approx0.8$. **Behavior:** it still enters the median (nulls are
   data); $\mathrm{RM}_{\rm lit}$ may then land in the null branch — that is a
   legitimate thread closure, not a failure.
2. **Case:** `cluster_column_range()` import breaks because the local checkout
   is behind origin (it is, by 4). **Behavior:** the script asserts
   `CL_M500_XRAY_UL` exists on import and fails with "run from origin/main ≥
   56cf4c4e" — Phase 0 must run on a synced tree (after the parked lanes
   clear) or in a fresh worktree from origin/main; the worktree path is the
   default so Thread 1 does not wait on the checkout sync.
3. **Error:** Galactic RM map unreachable. **Handling:** the recorded
   substitution (Phase 2); never silently swap priors.

## Documentation Updates

- [ ] This plan's Review History on every gate decision.
- [ ] `triage-kulkarni-feedback-2026-07-17.md` Thread-1 row updated with the
      outcome.
- [ ] ISSUE-010 in the companion ledger (Phase 3).

## Timeline Estimate

Phase 0: small. Phase 1: moderate (literature assembly is the long pole).
Phase 2: moderate. Phase 3: small. Phase 4: small, gated on humans.

## Open Questions

*(None. The two decisions that could have sat here — which paper carries the
$B_\parallel$ claim, and what happens on a marginal literature comparison — are
resolved by the coordination contract (companion carries it) and the frozen
marginal→owner-adjudication branch respectively.)*

---

## References

- [Triage: Kulkarni feedback](../triage/triage-kulkarni-feedback-2026-07-17.md) · [S1 plan](../plan/plan-cluster-xray-sz-mass-bound-2026-07-17.md) · [S1 experiment record](../experiment/experiment-cluster-xray-sz-mass-bound-2026-07-17.md) · [Handoff 12:58](../handoff/handoff-2026-07-17-12-58-s1-landed-owner-decisions-closed.md)
- Files analyzed: `codetections_polarization/main.tex` (:131-146 budget, :165 phineas row, :230 σ_RM, :146 MC priors); `codetections_polarization/issues.md`; `pipeline/galaxies/foreground/data/intervening_census_registry.csv:23`; `scripts/dm_budget_uncertainty.py:556-620` (origin/main); `scripts/dm_budget_uncertainty.csv:7,12-13` (origin/main); `sections/results.tex:101-157` (origin/main)
- External: Pandhi et al. 2025 (`2025ApJ...982..146P`, MC procedure); Hutschenreuter et al. 2022 (A&A 657, A43; Galactic RM map; bib key in `codetections_polarization/ref.bib`); Baptista et al. 2024 (DM_IGM); the Phase-1 candidate pool (Clarke 2001/2004; Bonafede 2010; Böhringer 2016; Govoni 2017; Stuardi 2021; Osinga 2022, 2025; Anderson 2021)

---

## Review History

### Version 1.0 — 2026-07-17
- Initial predeclared cross-paper record for Kulkarni Thread 1.
- Pinned every input to machine-readable sources (registry row 23, budget CSV
  rows 7/12/13, budget-script constants, companion `tb:host_props` row) per the
  S1 prose-rounding lesson.
- Froze the materiality rule (9.29 / 18.6 rad m$^{-2}$ observed-frame
  thresholds), the literature selection criteria, and the both-owners
  coordination gate before any derived quantity was computed.
- Declared the predeclaration honesty note: companion RM values were already
  in-context; the freeze protects the derived comparison.
- **Status: awaiting owner sanction** for Phases 1–3 (Phase 0 is pure pin
  verification and may run pre-sanction).

### Version 1.1 — 2026-07-17 (same day)
- **Owner sanctioned Phases 1–3** ("bring this home"); Phases 0–3 executed the
  same session (`rse/thread1-execution-20260717`).
- Phase 0: 12 pin/algebra/rule/corner tests green
  (`tests/test_rm_cluster_repartition.py`). Two pin-level discoveries: the
  registry carries nine cluster rows for this sightline (the excluded b>R500
  systems and the near-miss) — the budget-eligible flag selects the pinned
  row; and the closure median is −5.506 (the plan's prose said −5.52, a
  hand-arithmetic slip caught by the test, thresholds unaffected).
- Phase 1: criteria applied to the candidate pool. Admitted (3): Böhringer,
  Chon & Kronberg 2016 (144±43 rad m⁻², 0.5–1.0 r500 bin, 1722 RMs, mean mass
  ~3×10¹⁴); Osinga et al. 2022/2025 (28±4 beyond-R500 floor; within-R500
  aggregate 209±37; 124 Planck clusters); Anderson et al. 2021 (Fornax,
  6×10¹³, ~17). Rejected (4, criteria-based): Clarke 2001 (no normalized
  profile), Bonafede 2010 / Govoni 2017 / Stuardi 2021 (<10 sightlines).
  RM_lit(obs) = median 28/1.44 = **19.4 rad m⁻² ≥ 18.6 → MATERIAL** (gate-edge:
  4% over threshold; an owner-run Undermind sweep may add studies — additions
  re-run the median per the frozen criteria).
- Phase 2: MC executed (seed 20260707, byte-deterministic). Zero-cluster
  corner reproduces the companion row (−755.8 / −2.02 vs −756 / −2.0).
  Headline rows: ±0.5 μG moves RM_host by ~7σ of their quoted error; the
  DM-side correction alone (B_cl=0) gives ⟨B∥,host⟩ ≈ −4.5 μG with ~9% of
  draws unable to absorb the cluster column. Artifact:
  `scripts/rm_cluster_repartition.json`; figure:
  `thread1-figures/rm_repartition_sensitivity.pdf`.
- Phase 3: coordination memo drafted
  (`memo-thread1-rm-repartition-2026-07-17.md`, Options A/B); ISSUE-010
  appended to the companion ledger (working tree, pol-companion lane).
- **Phase 4 remains gated**: material classification opens coordination, not
  edits; awaiting the companion-lead decision (both-owners gate).

### Version 1.2 — 2026-07-17 (Undermind literature sweep; criteria unchanged)

- Owner ran the pre-agreed Undermind deep search (query as issued in-session;
  report archived as `undermind-cluster-outskirts-rm-2026-07-17.md`, 9 candidates).
  Selection criteria were NOT modified; this pass applies them to the
  expanded candidate set, with every load-bearing value re-verified against
  the paper full text (ar5iv/arXiv HTML, 2026-07-17).
- **Corrections to already-admitted entries (verified):**
  - Böhringer 0.5–1.0 r500: the paper's Table 1 (Galactic-corrected
    112 ± 43; uncorrected 114 ± 43) and its running text (144 ± 43) disagree.
    Table adopted: 144 → **112**. (v1.0 had taken the text value; the
    discrepancy is internal to the paper, surfaced by the sweep.)
  - The v1.0 "Osinga 2022+2025" entry conflated the 2022 depolarization
    paper with the 2024/25 RM-scatter paper and used the beyond-R500 floor
    (28) as a bound. The 2024/25 paper tabulates the exact 0.5–1.0 R500 bin
    for **background** sources (the FRB's class), cluster rest frame:
    **51 ± 6**. Floor replaced by the direct value; the 2022 depol paper is
    moved to `rejected` (per-source fits, not a population excess).
  - Anderson 2021: error corrected 5.0 → 2.4 (their bootstrap 95%);
    n_sightlines 100 → 76 (sources inside 1°); value unchanged.
- **Admitted additions (criteria met):** Khadir et al. 2025 (A3581,
  M500 = 2.15e14, 111 background RMs, direct R500-normalized corrected
  profile; ~8 [5–12 figure estimate] across the bin); Loi et al. 2025
  (Fornax densest grid, 503 background sources, outer annuli ≈ 0.86–1.10
  R500 via external R_vir conversion; ~11.5 after removing the authors'
  ~6 rad m⁻² non-cluster floor); Alonso-López et al. 2025 (Shapley SC core,
  34 cluster-region sources, printed excess 27.2 ± 5.0, overlapping-halo
  caveat).
- **Rejected additions (reasons recorded in the dict):** Anderson et al.
  2024 (splashback aperture not mappable to the bin; no M500 convention);
  Kim, Kronberg & Tribble 1991 (Abell-radius bins, no modern convention);
  Osinga et al. 2022 (depolarization, split out of the v1.0 entry).
- **Re-run of the frozen rule:** admitted set {8, 11.5, 17, 27.2, 51, 112};
  median 22.1 local → **15.35 rad m⁻² observed**. Thresholds unchanged
  (material ≥ 18.57, null < 9.29) → classification **MARGINAL** → owner
  adjudication branch (v1.0 §rule). Tests 12/12 green; JSON + figure
  regenerated; zero-cluster corner still reproduces the companion row.
- **Structural sensitivity recorded for the adjudication:** Fornax enters
  twice (Anderson 2021 and Loi 2025 are the same system). Counting Fornax
  once — under either study — gives median 27.2 → 18.9 observed →
  **material** (the criteria as frozen contain no system-independence
  clause, so the mechanical rule counts both; the owner may adjudicate
  either way). Excluding Alonso-López (overlapping halos) instead gives
  median 17 → 11.8 → marginal. A printed-values-only reading (Böhringer,
  Osinga, Alonso-López, Anderson) gives 39.1 → 27.2 → material.
- Memo literature table + classification paragraph updated to match
  (marginal, adjudication pending, double-count sensitivity stated).
  ISSUE-010's "material" wording in the companion ledger intentionally NOT
  amended yet — it will be corrected in the same pass as the adjudication
  outcome to avoid a second churn of the pol-lane file.
- **Status: owner adjudication pending** (material vs marginal-stands vs
  null); Phase 4 both-owners gate unchanged.

### Version 1.3 — 2026-07-17 (marginal-branch adjudication, owner-delegated)

- The owner delegated the v1.2 marginal adjudication ("I'm leaving this to
  you", 2026-07-17, in-session).
- **Decision: one system, one vote.** Entries sharing a physical system
  collapse to their mean before the median. Rationale: the median is meant
  to summarize independent systems; Fornax appearing as two admitted studies
  (Anderson 2021, Loi 2025) is a sampling artifact of the literature, not
  two pieces of evidence. The criteria's silence on independence was an
  oversight in v1.0, resolved here as adjudication — the selection criteria
  and thresholds are untouched.
- **Robustness of the decision:** the median is 27.2 whether the Fornax
  collapse takes the mean (14.25), Anderson alone (17), or Loi alone (11.5)
  — every one-vote reading lands on the same median, so the collapse-rule
  choice cannot tune the outcome.
- **Result:** median 27.2 local → **18.89 rad m⁻² observed** ≥ 18.57 →
  **MATERIAL**, by a 1.7% margin. That gate-edge margin is recorded
  prominently: the classification label is boundary-sensitive, and the
  memo's operative results (±0.5 μG ⇒ ~7σ shift in RM_host; DM-side
  correction doubling ⟨B∥,host⟩) are independent of the literature median.
- Implementation: `system` keys on the two Fornax entries;
  `rm_lit_obs()` groups by system (mean within, median across); dilution
  test rewritten to mirror the grouping; new pin test records the
  adjudicated outcome (fails loudly if a value change silently flips it).
  13/13 tests green; JSON + figure regenerated; corner reproduces.
- Memo classification paragraph, triage row, ISSUE-010 (amendment line),
  and the transmittal draft updated to "adjudicated material (boundary)".
- **Status:** Phase 4 both-owners gate unchanged — awaiting the
  companion-lead decision on Options A/B.
