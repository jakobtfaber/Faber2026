# Plan: circulation readiness — Faber2026

> **ARCHIVED 2026-07-18 (owner decision).** Superseded as the canonical task
> list by the manuscript-aligned board, [`../BOARD.md`](../BOARD.md); open
> decisions live on the wayfinder map
> ([`../wayfinder/map-apj-submission.md`](../wayfinder/map-apj-submission.md)).
> Frozen as history — do not update statuses here. The letter+number stage
> codes below are legacy; the board carries their descriptive names.

---
**Date:** 2026-07-06
**Status:** Active — gates set by owner decision (this date)
**Owner decisions recorded:** (a) circulation waits on the full scintillation
campaign (DSA **and** CHIME) and the two-screen analysis built on it; (b) the
rail-taxonomy presentation is retired — geometry model selection replaces it
(objections 1–4; CONTEXT.md "Geometry-adjudicated β" + "Scint→scattering
coupling"); (c) after the
re-fit: sightline analysis, galaxy/cluster foreground comparison, and a
synthesized propagation-vs-intrinsic interpretation are all pre-circulation
content, not future work; (d) 2026-07-06 evening: trust revoked for all
burst-data fits performed to date — the §V re-validation ladder governs
re-entry; (e) 2026-07-06 evening, second wave: trust also revoked for the
foreground census and the DM budget decomposition (V4/V5) — only TOA
association arithmetic and DM_obs remain trusted; (f) 2026-07-06: rail
tallies dropped from the manuscript; codetections_polarization/ stays as
companion-paper materials; co-author list to be drafted from Law2024 +
CHIME/FRB overlap for pruning; (g) 2026-07-06 late evening: A1 working
draft adopted — modular constraint layer, prior-odds geometry, posterior
escalation trigger (text under A1 below); (h) 2026-07-06, same night:
owner re-opened every locked decision — (b)–(g) stand as **working
choices, all revisable**, none final until the owner closes them. §V
expansion:
[plan-trust-reset-revalidation.md](plan-trust-reset-revalidation.md);
(i) 2026-07-06 night, third wave: trust also revoked for TOA association
arithmetic and DM_obs (all twelve, both telescopes) — the retained set is
now empty; V6 added.
---

Lanes: **[FLITS]** pipeline repo (separate lane — changes land as FLITS PRs,
then a pin bump here) · **[data]** h17 + `~/Data` campaign work ·
**[ms]** this repo's tex/figures · **[decision]** owner call.

## A. Methodology reset — geometry selection replaces rail taxonomy

- [ ] A1 **[decision]** Two-screen treatment — **working draft, open**
      (adopted 2026-07-06 after adversarial iteration — Codex GPT-5.5
      review — then re-opened the same night: owner keeps all design
      decisions unlocked; every element revisable. **Trigger revised
      2026-07-13, owner direction:** escalation is now evidence-based
      model comparison, not hand-set ratio thresholds — amended text
      below):
      > Adopt A1 as a modular scintillation-to-scattering constraint layer,
      > not a hard two-screen fit by default. Scintillation products enter
      > as frozen posterior/limit products with quality flags, not point
      > estimates. The τΔν statistic is used probabilistically to count
      > screens and derive τ_near/τ_dom, marginalized over geometry
      > constants and censoring. A second broadening component is not
      > fitted unless the **escalation trigger** fires, defined as either:
      > (i) nested-sampling model comparison on the frequency ACF prefers a
      > two-component (stacked-Lorentzian) model over a single Lorentzian —
      > with the noise floor and zero-lag self-noise spike included in both
      > models, and a finite-scintle (correlated-lag) covariance or an
      > equivalent dynamic-spectrum-domain likelihood, so the extra
      > component cannot feed on ACF sample variance — at a ΔlnZ threshold
      > set by an injection-calibrated false-escalation rate on
      > single-screen simulated dynamic spectra (V1 injection-recovery
      > machinery); or (ii) posterior-predictive residuals in the burst
      > profile at the predicted second-screen timescale. A two-component
      > ACF detection escalates; a non-detection does not establish a
      > single screen (a host-side screen with Δν_d below channel
      > resolution is censored, not absent). The former τ_near/τ_dom
      > thresholds (Pr > 0.1 at ratio 0.1, median > 0.03) are retired as
      > triggers and demoted to prior-odds inputs. For
      > extended host media, quenching constrains an effective
      > source-proximate scattering-depth distribution, not a point screen
      > distance. Scintillation geometry informs prior odds for thin vs
      > extended PBF families; final kernel selection remains
      > evidence/model-comparison based. Joint burst-shape+ACF likelihood
      > is deferred unless modular products conflict on a high-S/N
      > sightline.
      A2/A3 design work may proceed against the draft, tracking its
      revisions. Remaining owner call: sign off the revised trigger once
      the injection calibration reports its ΔlnZ operating point.
      **2026-07-15 closure of the trigger sub-input:** the injection
      calibration completed with no usable operating point (1 %
      false-escalation envelope at ΔlnZ ≈ 5.97×10⁴, zero escalation
      probability in all eight power cells —
      [plan-a1-trigger-calibration.md](plan-a1-trigger-calibration.md)
      Final outcome). Clause (i) is retired; clause (ii)
      (posterior-predictive residuals) remains the only escalation limb.
      There is no ΔlnZ operating point to sign off. Successor statistic
      chartered as A5 per owner direction.
- [ ] A2 **[FLITS]** Extended-medium (Williamson uniform-LOS) PBF kernel,
      β-coupled, per band (ADR-0007 un-deferred by the rail evidence: 10/12
      posteriors hit its re-open trigger — the nine tabled railed rows plus
      gate-FAIL chromatica; CAMPAIGN_REPORT's 10-member candidate set).
- [ ] A3 **[FLITS]** Per-sightline geometry model selection (thin vs extended,
      evidence/BIC), scint-informed per A1. Interior rows (freya, phineas)
      re-adjudicated under the same machinery.
- [ ] A4 **[FLITS]** ADR amendment recording the owner decision: rail classes
      are campaign QA only; α=4-limit quoting retired; ADR-0007 sequencing
      superseded. (CONTEXT.md here already updated 2026-07-06.)
- [ ] A5 **[FLITS]** N-component profile-fit justification statistic
      (chartered 2026-07-15, owner direction at A1-trigger closure): a
      calibrated model-comparison criterion that says a burst is better
      characterized by N profile components than by 1 — burst-morphology
      component count, distinct from scattering-screen count. Replaces
      visual-only morphology vetting as the justification for per-burst
      component choices; injection-calibrated like A1's campaign, reusing
      the dynesty evidence engine (`acf_evidence.py`) in the profile
      domain. Design pending; not a circulation blocker unless the owner
      promotes it.

## B. Scintillation campaign completion (both bands) — hard circulation gate

- [ ] B1 **[FLITS]** Burst configs for whitney/phineas/mahi/isha (casey
      pattern; burst bins from the 2026-07-06 builder: ~1020/~1079/~29/~55).
      First measurement run doubles as the end-to-end loader test.
- [ ] B2 **[data]** U sizing (NE2025 MW-floor rule, freya precedent in
      PROVENANCE.md) + CHIME regeneration for the six never-generated
      co-detections: zach, oran, wilhelm, johndoeii, hamilton, chromatica.
- [ ] B3 **[data]** mahi 700–725 MHz RFI inspection before any measurement
      uses that sub-band range.
- [ ] B4 **[FLITS/data]** CHIME-band ACF/Δν_d measurements across the sample,
      run under the V1 contract (the existing DSA-band-only two-screen table
      rests on revoked fits).
- [ ] B5 **[FLITS]** Two-screen analysis rebuilt on joint CHIME+DSA scint
      (τ·Δν_d per band, screen-placement constraints per sightline);
      includes re-running the revoked DSA-band ACF fits under the V1
      contract so the τ·Δν_d cross-check of V1(v) is itself re-validated.
- [ ] B6 **[FLITS]** Housekeeping: refresh `scintillation/DATA_PROVENANCE.md`
      (gen-2 md5s, h17 path), commit the h17-side tooling
      (`extract_time0_metadata.py`, generic npz builder) into the FLITS tree.

## V. Trust reset & re-validation framework (owner decisions 2026-07-06 evening→night, three waves)

Wave 1: trust revoked for ALL burst-data fits to date — joint scattering
fits (every β, τ₁GHz, multiplicity, PPC verdict, interior rows included),
sub-band EMG fits, scintillation ACF fits (Δν_d), spectral amplitudes c₀,γ
and all energies. Wave 2: trust also revoked for the foreground census
(cross-matches, verdicts, impact parameters, halo-mass proxies) and the DM
budget decomposition (Galactic disk/halo terms, Macquart mean, mNFW DM_int
columns, host residuals). Wave 3: trust also revoked for the TOA
association arithmetic (residuals, P_cc, verdicts) and DM_obs (all twelve,
both telescopes — per-telescope values, their agreement, and their
acquisition method are undocumented). Retained: nothing among analysis
products; raw observational inputs only. The twelve-burst set stays the
working roster; its citable association evidence awaits V6.
Downstream, now unsupported until inputs re-qualify: tab:budget,
tab:foreground, fig:budget both panels, the dominant-systems and cluster
analyses, the host-dominated 10/11 comparison, the τ·Δν_d two-screen test,
the scintillation excess, the FRB 20230913A attribution (both diagnostics
revoked), tab:beta, tab:burst-energies, the multiplicity-bias demonstration
(fig:whitney_mult, the abstract's closing claim, conclusions item 7),
fig:jointmodel_montage, and fig:scint_screens.

- [ ] V1 **[FLITS]** Author the re-trust validation contract (ADR): a fit is
      citable only with (i) verified input-data lineage (gen-2+,
      md5-provenanced), (ii) synthetic-injection recovery of known truth
      under each candidate geometry (`simulation/` + `sim_fit_bridge`),
      (iii) prior-rail behavior test — a rail is model-family rejection,
      never a quotable limit, (iv) PPC pass, (v) an independent cross-check
      (sub-band slope or τ·Δν_d consistency) itself produced under this
      contract — cross-checks are re-run, never inherited from the revoked
      campaign.
- [ ] V2 **[data]** Verify whether the CHIME dynamic spectra consumed by the
      scattering joint fits share the gen-1 de-chirp defect lineage found in
      the upchannelized scintillation products; per-burst scattering-input
      provenance table.
- [ ] V3 **[FLITS]** Energies pipeline under the same contract; resolve the
      γ_D ≈ −5 pile-up (prior-bound check) and the tab:burst-energies
      selection-rule contradiction (gate-FAIL 20240203A tabulated under a
      "quality-passing" criterion; note-a redshift provenance vs §2's
      placeholder trio).
- [x] V4 **[FLITS]** *(cleared 2026-07-07 — owner, on the DR9/DESI-DR1/NED/PS1-STRM re-validation; see CONTEXT.md trust-reset status)* Census re-validation: per-candidate provenance audit
      (coordinate match, objID lookups, redshift class and source, PS1-STRM
      reliability), independent re-derivation of impact parameters and
      b/R_vir · b/R_500, re-run of the foreground/background/inconclusive
      verdict logic, halo-mass proxy provenance. Deliverable: a re-verified
      tab:foreground with per-candidate evidence, plus per-sightline audit
      figures.
- [x] V5 **[FLITS]** *(cleared 2026-07-07 — owner, with V4; measured-scattering side of fig:budget stays revoked, plan D1)* DM-budget re-validation: verify model implementations
      against references (NE2001/YMW16 per sightline, halo prior, Macquart
      relation with stated f_IGM/χ_e, mNFW/two-phase columns vs published
      profiles), re-derive host residuals and the prior-predictive
      negative-residual analysis on the V4-verified census. Deliverable: a
      re-verified tab:budget + fig:budget left panel.
- [x] V6 **[FLITS]** *(cleared 2026-07-07 — report: v6-association-dm-report-2026-07-07.md; quotable under the shared DSA-DM convention)* Association + DM_obs re-validation (wave 3): document
      per-burst, per-telescope DM_obs provenance (instrument pipeline,
      dedispersion method — e.g. structure-maximizing vs S/N-maximizing —
      producing artifact, uncertainty); quantify CHIME-vs-DSA DM agreement
      per burst (ΔDM with uncertainties, figure); re-derive the TOA
      association arithmetic (residuals, P_cc) from raw positions and
      timestamps under the V1 contract. Deliverable: per-burst DM/TOA
      provenance table + agreement figure; re-certifies the co-detection
      sample membership itself. Expanded as Phase 6 of
      [plan-trust-reset-revalidation.md](plan-trust-reset-revalidation.md).

## C. Scattering re-fit under geometry selection (needs V + A + B)

- [ ] C1 **[FLITS]** Re-fit campaign from scratch across all twelve
      co-detections under the V1 contract with geometry adjudication — a
      fresh campaign on verified inputs, not a patch of the nine railed rows.
- [ ] C2 **[FLITS]** Per-band systematics pass on the sightlines C1 flags
      with elevated per-band χ² (the revoked campaign's trio — wilhelm,
      hamilton, zach — is the starting hypothesis, re-derived by C1).
- [ ] C3 **[ms]** Pin bump + table/figure regeneration from the campaign.

## D. Sightline analysis & foreground comparison (needs C + V4/V5)

- [ ] D1 Re-derive measured-vs-predicted foreground scattering per sightline
      under the adjudicated geometries (currently thin-screen-conditioned).
- [ ] D2 Galaxy / galaxy-cluster foreground comparison as first-class results
      (clusters_icm, galaxies_cgm lanes), per-sightline attribution verdicts.

## E. Synthesis (needs D)

- [ ] E1 Synthesized interpretation: role of each foreground medium class in
      shaping the signal; what is propagation vs intrinsic per sightline.
- [ ] E2 Intrinsic emission properties where separable (energies table is the
      seed; extend as the geometry-adjudicated fits permit).

## F. Manuscript reconciliation & polish

- [ ] F1 **[ms]** Restructure abstract, observations (§2), the co-model
      methods (sec:jointfit / sec:beta-scattering-methods), results,
      discussion, conclusions around geometry selection; purge rail-class
      vocabulary and all α=4-limit quoting (CONTEXT.md contract); rewrite
      the census/budget prose (budget §3.2–3.4, results §4.1, discussion
      opening, conclusions items 1–3/5–6, abstract census/budget sentences)
      on the V4/V5-re-verified products. β-language purge unblocks post-C;
      census/budget rewrite post-V4/V5 + D; final content pass needs D/E
      (spine).
- [ ] F2 **[ms]** `tab:beta` rework: geometry-adjudicated quoting; descriptive
      exponential-consistency statements for ex-railed rows. Post-C3.
- [ ] F3 **[ms]** Consistency audit (mechanical): per-section sample counts,
      retired-language sweep, table/figure provenance vs pinned pipeline,
      cross-refs. Can run now on non-β sections.
- [ ] F4 **[ms]** Referee-mode full read-through. Sensible after F1; a
      structural pass on intro/observations/toa/budget can run now.
- [ ] F5 **[ms]** Prose polish (line-level), after F3/F4 triage.
- [ ] F6 **[ms]** `auth.tex`: draft a candidate core co-author list from the
      Law2024 (DSA-110) and CHIME/FRB 2018 author lists for owner pruning
      (approach decided 2026-07-06), then typeset the pruned list.
- [x] F7 **[decision]** `codetections_polarization/` — resolved 2026-07-06:
      companion-paper materials, intentionally parked; keep as-is, no action.

## G. Release mechanics (last)

- [ ] G1 Push accumulated main commits (outward gate: Overleaf pulls main).
- [ ] G2 Clean `make` from a fresh clone + submodule init at the final pin.
- [ ] G3 Overleaf UI pull + visual check of the compiled PDF.

## Dependency spine

V1/V2 → every scattering and scintillation re-fit · V1/V3 → energies ·
V4 → every census-derived claim and V5's host-residual re-derivation
(V5's implementation checks can start now) · V5 → every budget-derived
claim · V6 → every association/DM_obs quote and the citable sample
membership (parallelizable now) · A1 → A2/A3 · B1–B4 → B5 (B measurements
themselves run under the V1 contract) · (V, A, B5) → C1+C2 → C3 (C2
resolves per-band misfits before the pin bump) · C3 → F2 · C3 + V4/V5 → D
· D → E → F1 → F4/F5 → G.
V1–V4, V6, V5's implementation half, F3, and a structural F4 pass on non-β
sections are parallelizable now; A4, B6, F6/F7 anytime.
