# Research: DM measurement methods — provenance of the quoted DMs and the improvement landscape

> **Historical audit, superseded 2026-07-13.** This file describes the state
> before the controlled phase-coherence campaign. The adopted values and final
> method are recorded in [verified-dm-adoption-2026-07-13.md](../notes/verified-dm-adoption-2026-07-13.md)
> and `analysis/dm-joint-phase-v2/manuscript_dm_catalog.csv`.

**Date:** 2026-07-09
**Scope:** both — internal (DM provenance, dispersion code inventory, DM treatment in the 2D joint model) and external (DM-estimation package survey with disconfirming checks)
**Codebase state:** Faber2026 `ms/codetection-gallery` tip (main `29f7a81` + gallery lane), pipeline pin `14e0d1f`
**Related Documents:** [research-unified-12burst-figure.md](../research/research-unified-12burst-figure.md), [dm-provenance-audit-2026-07-07.md](../dm/dm-provenance-audit-2026-07-07.md), [v6-association-dm-report-2026-07-07.md](../notes/v6-association-dm-report-2026-07-07.md)

## Question / Scope

How were the DM values we currently quote for the 12 co-detections actually
measured (what code, what metric was maximized), per instrument? Is DM free in
the 2D time-frequency joint model? And which DM-estimation packages
(DM_phase, DM-power, others) should an improved from-scratch procedure use,
given CHIME singlebeam .h5 (coherent dedispersion possible) vs DSA
filterbank-only (incoherent only)?

## Codebase Findings

### 1. Up to four DMs coexist per burst — the provenance map

| Quantity | Lives in | What it is |
|---|---|---|
| DSA catalog DM (`dm`) | `pipeline/configs/bursts.yaml:21-148` | **Frozen upstream DSA-110 catalog reference** — remeasured by nothing in this repo; `dm_err: 0.1` is a uniform placeholder (v6-association-dm-report-2026-07-07.md:44) |
| DSA file-stem DM | `{nick}_dsa_I_<DM>_…npy` (data-manifest.csv) | DM the DSA cube was actually dedispersed at, **baked upstream by the DSA-110 detection pipeline (S/N-based, external to this repo)** |
| CHIME measured DM (`dm_chime`) | `pipeline/crossmatching/chime_side_inputs.json` | Arrival-time-regression measurement (8/12 constrain), used only for the CHIME↔DSA agreement check |
| CHIME file-stem DM | `{nick}_chime_I_<DM>_…npy` | Coherent-dedispersion DM of the CHIME cube ("CHIME-optimized"); **its derivation is undocumented in-repo** — the `dmphase/` directory name is misleading (`pipeline/scintillation/DATA_PROVENANCE.md:281-284`: these are the native coherently-dedispersed cubes, not DM_phase outputs) |

Example (chromatica): catalog 272.664 / DSA stem 272.368 / `dm_chime`
272.384 / CHIME stem 272.6382 — four different numbers.

**Everything the manuscript quotes traces to the catalog DM.**
`budget_table.tex` header: "DM_obs is the DSA-110 catalog dispersion measure
under the shared DSA-DM reference convention"; `sample_table.tex` prints no DM
column, and its TOA residuals are computed at the DSA DM. The V6 owner
decision (2026-07-07) pins BOTH telescopes' arrival references to the DSA
catalog DM (re-referencing CHIME at `dm_chime` would shift its ToA by up to
−12 ms), with CHIME↔DSA DM agreement reported separately
(v6-association-dm-report-2026-07-07.md:33-38,153-191).

### 2. Method history per instrument

**DSA:** the quoted DMs were never measured here — catalog values from the
upstream DSA-110 (T3/heimdall-class, S/N-maximizing) pipeline. The only
in-repo DSA DM-vs-metric code is a diagnostic, not a source:
`pipeline/scattering/scat_analysis/burstfit_robust.py:187-214`
(`dm_optimization_check`, peak-S/N vs trial DM offset). A DM_phase-based
refinement hook exists in the scattering preprocessing
(`scat_analysis/dm_preprocessing.py:22,126` — refines `dm_init`, falls back to
catalog on failure) but the campaign configs carry catalog DMs.

**CHIME:** three eras.
1. *Structure-max era (retracted):* the Pillar-2 campaign used a clean-room
   DM_phase reimplementation (`pipeline/dispersion/dmphasev2.py:43` —
   coherent power of the phase spectrum, `|Σ unit-phasors|²·f²`,
   `_coherent_power` :112). **Retracted** per
   `pipeline/.agents/audit-chime-side-dm.md:1-18`: a `1e-3·K_DM` unit bug made
   every delay 1000× too small, and the post-mortem verdict (:51-54) is that
   structure-max is the wrong primary tool for smooth/scattered/low-S/N CHIME
   singlebeam bursts ("flat_ratio ~2 = NON-detection of structure").
2. *Arrival-regression era (current `dm_chime`):*
   `pipeline/dispersion/chime_dm.py` — Stage 1 wide incoherent peak-S/N coarse
   search (±50 pc cm⁻³, `_coarse_dm` :73); Stage 2 per-sub-band
   **scatter-deconvolved EMG** fits (`exgauss` :32) → t₀ vs K_DM·ν⁻² weighted
   regression (`measure_dm` :116), χ²-inflated σ, `constrains_dm=False` below
   3 good sub-bands (:174,:199). Landed as pipeline PR #41: **8/12 constrain**
   (zach 261.524±0.020, casey 491.168±0.0005, freya 912.277, hamilton 518.834,
   chromatica 272.384, isha 411.215, wilhelm 601.902, phineas 609.821);
   whitney/oran/johndoeII/mahi unconstrained.
3. *Experimental cross-checks (unpromoted):* the dm-power and dm-phase
   campaigns (§3).

**Coherent dedispersion reality:** the only true coherent-dedispersion path in
the tree is `pipeline/crossmatching/chime_singlebeam.py:88-184` — lazy import
of CHIME's `baseband_analysis` (`coherent_dedisp`/`incoherent_dedisp`), which
only runs inside the CANFAR `chimefrb/baseband-analysis` docker image, on the
singlebeam .h5s that live on **h17**
(`/data/research/astrophysics/frbs/chime-dsa-codetections/`,
DATA_LOCATIONS.md:86-95; regeneration recipe in
handoff-2026-07-06-14-50-chime-sample-regeneration.md). The heavy CHIME DM
extraction producer (`dump_grid_data.py` / `extract_final_parallel.py`) is
**off-repo on h17 and never shipped** (audit-chime-side-dm.md:140-167) — a
provenance gap. **DSA has no voltage/baseband data anywhere** (data-manifest,
codetections_manifest.yaml, DATA_SOURCES.md): DSA re-measurement is
incoherent-only, on the 6144-ch × 32.768 µs Stokes-I filterbank products.

### 3. The in-repo DM_phase and DM-power implementations — already tried, but implementation-suspect

Both packages the owner asked about were run on all 24 products via **in-tree
reimplementations, not the published packages**; neither was promoted
("experimental cross-check, not promoted to citable DM_obs" on all five
memos). **Owner assessment (2026-07-09): the null/circular results should be
read as implementation and configuration failures, not as evidence the
methods are ineffective on this sample.** Supporting that reading:
`dmphasev2.py` is a clean-room rewrite (it already shipped one 1000× unit
bug); `dm_power_analysis.py` is a variant, not the published DM-power
algorithm (log-rebinned band-average score instead of the paper's
per-Fourier-frequency optimal weighting; no published-style fcut); both
searches were narrow residual windows (±2/±3) centered on the reference DM
with acceptance gates that were never validated against known-DM injections.
The upstream packages (danielemichilli/DM_phase, hsiuhsil/DM-power) have
never been run as-published on this sample.

- **DM-power** (`pipeline/dispersion/dm_power_analysis.py`): residual-DM grid
  (default ±3, step 0.05) around the reference; metric = SVD-channel-weighted,
  log-frequency-rebinned on-pulse Fourier power minus off-pulse
  (`dm_power_curve` :59, `_profile_power_subtract` :487,
  `_log_rebin_positive_power` :493); per-log-bin Gaussian/parabola peak fits,
  inverse-variance combined, bootstrap σ (`fit_dm_power_result` :119).
  Results: **0/24 constrained** (h17 manifest memo) — near-flat curves,
  peak SNR 1.4–2.5 on DSA; every result demoted by
  `mark_diagnostic_candidate_only` :273.
- **DM_phase** (`pipeline/dispersion/dm_phase_analysis.py` driving
  `dmphasev2.DMPhaseEstimator`): fcut (50, 1500) Hz, ±2 window, bootstrap
  parabola peak; accept gate = non-edge peak ∧ slope_ratio ≤ 1.10 ∧
  (peak_snr ≥ 3 ∨ |residual| ≤ 0.05) (`dm_phase_analysis.py:80-90`).
  Results: **13/24 accepted**, but the accepted σ is pinned at the
  0.025 grid floor and candidates sit within 0.01–0.3 of the reference the
  ±2 search was centered on — the accepts are largely **reference
  confirmations**, matching the circularity warning in
  audit-chime-side-dm.md:55-57.

### 4. DM in the 2D joint model — free, per band (owner's belief confirmed)

- `FRBParams.delta_dm` (`scattering/scat_analysis/burstfit.py:448`) — a
  residual-DM nuisance around the fixed pre-dedispersion baseline `dm_init`
  (CHIME 0.0 = coherently dedispersed; DSA = catalog DM). Free only in the
  full model M3 (:471-477).
- It enters the forward model twice: dispersive arrival delay
  (`_dispersion_delay` :671, applied :736-740) and per-channel intra-channel
  smearing with `dm_init + delta_dm` (:749, `_smearing_sigma` :679-693).
  The smearing previously used `dm_init` only — a fitted CHIME `delta_dm≈4.7`
  with zero modeled smearing leaked into ζ/τ and **biased α**
  (JOINT_FIT_STATE.md:76, "LIVE alpha-corruption channel"); fixed 2026-06.
- Joint CHIME+DSA fit: per-band `delta_dm_C`/`delta_dm_D` and per-band
  t0 — bands tied only through shared (τ_1GHz, β)
  (`burstfit_joint.py:83-96,153-162,617,626`). Prior: uniform
  ±`DM_RESID_MAX=50` (`burstfit.py:73,1399-1402`) — narrowed from ±3000 after
  a runaway `delta_dm_D=−1777` fit (SCINT_INTEGRATION_PLAN.md:78-88); the
  physical-prior path uses ±5 (`priors_physical.py:285`).
- The **(α, delta_dm) degeneracy ridge is documented**
  (MULTICOMPONENT_PLAN.md:119-130,174 — oran runs α=1.44 vs 5.96 on the same
  data along the ridge), with a fix-DM cross-check protocol (johndoeII's
  shallow α survived it, SCINT_INTEGRATION_PLAN.md:98-102).
- Sub-band EMG consistency fits do **not** float DM
  (`burstfit_robust.py:237-289` — fixed `dm_init` smearing, free (amp, μ, τ)).

### 5. Open provenance sores (confirmed contradictions)

1. **chromatica: DSA product dedispersed at 272.368 vs catalog 272.664**
   (0.30 pc cm⁻³) — unresolved; no source decides which is right. The stem is
   suspiciously close to `dm_chime` 272.384 and shares ".368" with zach.
2. **Stale "SUSPENDED / CHIME DMs nulled" banner at the pin**
   (`crossmatching/association.py:223`, `association_report.json:8`) while
   `chime_side_inputs.json` carries 8 live `dm_chime` — the V6 fix sits on an
   **unmerged** FLITS branch (`agent/v6-dm-provenance-toa`, 9175b92).
3. **`dm_err = 0.1` uniform placeholder** — no measured DSA DM uncertainty
   exists anywhere; agreement tests ride a 1 pc cm⁻³ floor.
4. **CHIME file-stem DMs underived in-repo**; off-repo h17 extraction
   artifacts unpinned/unchecksummed (dm-provenance-audit-2026-07-07.md:40).

## Prior Art

| Package / method | Metric | Notes for our use | Source |
|---|---|---|---|
| **DM_phase** (Seymour, Michilli & Pleunis 2019) | Coherent power of the phase spectrum (structure-max) | CHIME baseband-pipeline standard; needs temporal structure; already reimplemented in-tree and found non-informative on our smooth/scattered singlebeam sample | ascl:1910.004 |
| **DM-power** (Lin et al. 2022/23) | Multi-timescale Fourier power, optimally weighted per Fourier frequency | ~10⁻³ pc cm⁻³ on sims; authors warn intrinsic frequency-dependent structure mimics dispersive delay; in-tree variant constrained 0/24 on our data | arXiv:2208.13677; github.com/hsiuhsil/DM-power |
| **fitburst** (Fonseca et al. 2024, ApJS 271:49) | Full 2D dynamic-spectrum forward model; **DM fittable jointly** with scattering; removes intra-channel smearing via 2D upsampling | CHIME/FRB's own production morphology tool (Cat-2 uses it); the external analogue of our burstfit M3/joint model; natural external benchmark | arXiv:2311.05829; chime-frb-open-data |
| **scatfit** (Jankowski 2022) | Profile-domain scattering fits with DM refinement | Profile-level; overlaps our sub-band EMG machinery | ascl:2208.003; github.com/fjankowsk/scatfit |
| **CHIME baseband pipeline** (Michilli et al. 2021, ApJ 910:147) | Coherent dedispersion + structure-max refinement; catalog-update beamforming refines DM by S/N-max incoherently | What produced our singlebeam h5s upstream | arXiv:2311.00111 (catalog update) |
| **Six-method cross-validation** (Wang et al. 2026) | Compares peak-flux max, S/N max, forward-derivative max, power-spectrum optimization, kurtosis max, entropy min on 2874 bursts of FRB 20240114A | Single-component bursts: inter-method scatter ~0.18 pc cm⁻³; complex/drifting morphologies: up to ~4.8 pc cm⁻³ divergence; sad-trombone drift mimics 1–6 pc cm⁻³ of DM; **recommends multi-method cross-validation and morphology-dependent systematic uncertainties** | arXiv:2607.03877 |
| ML DM estimators (2026) | Learned regression | Exists as landscape; not production-grade for precision DM_obs | ScienceDirect S2213133726000909 |

**Disconfirming findings (sought explicitly):** structure-optimizing methods
are undefined for structureless (smooth/scattered) bursts — our own audit's
retraction rationale matches Wang et al.'s morphology-dependence result;
DM-power's authors concede drift/structure contamination; any single-metric DM
on a multi-component burst (whitney) inherits up-to-several pc cm⁻³ of
morphology-driven ambiguity.

## Synthesis

1. **The quoted DMs are inherited, not measured.** DSA: frozen catalog values
   with placeholder errors, dedispersion metric = upstream S/N-max. CHIME:
   quoted DM_obs is also the DSA catalog value (V6 convention); the measured
   `dm_chime` (arrival regression) exists for 8/12 as an agreement check only.
   The owner's memory of "a metric we decided to maximize" corresponds to
   three superseded/parallel layers: upstream S/N-max (DSA products),
   retracted structure-max (CHIME Pillar-2), current scatter-deconvolved
   arrival regression (CHIME `dm_chime`).
2. **Both packages the owner named were only ever run as in-tree
   reimplementations, and those runs are implementation-suspect** (owner
   assessment; see §3): DM-power-variant constrained nothing (0/24),
   DM_phase-variant accepts were circular reference-confirmations. Morphology
   (smooth/scattered/low-S/N) plausibly contributes — the retraction audit
   and the cross-validation literature both say structure-max needs structure
   — but the methods cannot be judged on this sample until the published
   packages are run as-released and validated on known-DM injections.
3. **The strongest existing asset is the arrival-regression estimator**
   (`chime_dm.py`): scatter-deconvolved EMG sub-band t₀ vs ν⁻² regression is
   the right metric family for scattered bursts and already constrains 8/12 on
   CHIME with honest σ and quality gates. It has never been pointed at the
   DSA filterbanks.
4. **The 2D joint model already floats per-band residual DM** with documented
   degeneracy handling — its `delta_dm` posterior is a third, model-conditional
   DM constraint, currently unused for DM provenance.
5. **Owner constraints on the improved procedure (2026-07-09):**
   (i) **uniform methodology across all 12 bursts** — no per-burst
   cherry-picking of methods (the reconciliation with the morphology caveat:
   run every method on every burst, quote one uniformly-chosen primary, and
   report the inter-method scatter as a per-burst systematic — uniformity in
   procedure, morphology expressed as uncertainty, not method choice);
   (ii) **visual vetting is a first-class acceptance criterion** — every
   estimator run must emit per-burst diagnostic figures and contact sheets
   for side-by-side owner inspection; goodness-of-fit or gate numbers alone
   are not sufficient to accept or reject a DM.
6. **Gap analysis for an improved from-scratch procedure:** (a) validate every
   estimator on known-DM synthetic injections into real off-pulse noise
   before trusting any verdict (this also adjudicates the "incorrectly
   implemented" question about the in-tree variants); (b) run the published
   DM_phase and DM-power as-released, uniformly on all 24 products; (c)
   measure DSA DMs (arrival regression on the 6144-ch filterbanks) to replace
   frozen catalog values and placeholder errors; (d) close the CHIME 4/12
   unconstrained via 2D forward modeling (fitburst-style / our M3) and/or
   coherent re-extraction on h17; (e) joint-model `delta_dm` posterior as a
   consistency layer; machine-readable per-burst provenance table (feeds the
   promised data-release table); (f) resolve the chromatica 272.368/272.664
   discrepancy and the stale SUSPENDED banner (merge or re-land the V6 fix on
   the pin's branch).

Design decisions (which method becomes the uniform primary, injection-test
pass criteria, whether to rerun coherent extraction) belong to planning
(`ai-research-workflows:planning-implementations`).

## References / Sources

- Code: `pipeline/configs/bursts.yaml:21-148`;
  `pipeline/dispersion/{chime_dm.py,dm_power_analysis.py,dm_phase_analysis.py,dmphasev2.py}`;
  `pipeline/crossmatching/{chime_singlebeam.py,chime_side_inputs.json,association.py}`;
  `pipeline/scattering/scat_analysis/{burstfit.py,burstfit_joint.py,burstfit_robust.py,dm_preprocessing.py,priors_physical.py}`;
  `pipeline/analysis/chime_dm/plot_dm_grid.py`.
- Docs: `pipeline/.agents/audit-chime-side-dm.md`;
  `docs/rse/specs/{dm-provenance-audit-2026-07-07.md,v6-association-dm-report-2026-07-07.md}`;
  dm-power/dm-phase memos (5) in `docs/rse/specs/`;
  `pipeline/analysis/scattering-refit-2026-06/{JOINT_FIT_STATE.md,SCINT_INTEGRATION_PLAN.md,MULTICOMPONENT_PLAN.md}`;
  `pipeline/analysis/beta_campaign/CAMPAIGN_REPORT.md`.
- External: Seymour, Michilli & Pleunis 2019 (ascl:1910.004); Lin et al.
  2022 (arXiv:2208.13677); Fonseca et al. 2024 (arXiv:2311.05829, ApJS
  271:49); Jankowski 2022 (ascl:2208.003); Michilli et al. 2021 (ApJ 910:147);
  CHIME/FRB catalog update (arXiv:2311.00111); Wang et al. 2026
  (arXiv:2607.03877).
