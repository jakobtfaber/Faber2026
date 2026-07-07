# Plan: circulation readiness — Faber2026

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
content, not future work.
---

Lanes: **[FLITS]** pipeline repo (separate lane — changes land as FLITS PRs,
then a pin bump here) · **[data]** h17 + `~/Data` campaign work ·
**[ms]** this repo's tex/figures · **[decision]** owner call.

## A. Methodology reset — geometry selection replaces rail taxonomy

- [ ] A1 **[decision]** Two-screen treatment: scint products (τ·Δν_d, screen
      placement) as geometry-adjudicating constraints/priors (recommended) vs
      a fitted two-screen scattering model. Blocks A2 design.
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

## B. Scintillation campaign completion (both bands) — hard circulation gate

- [ ] B1 **[FLITS]** Burst configs for whitney/phineas/mahi/isha (casey
      pattern; burst bins from the 2026-07-06 builder: ~1020/~1079/~29/~55).
      First measurement run doubles as the end-to-end loader test.
- [ ] B2 **[data]** U sizing (NE2025 MW-floor rule, freya precedent in
      PROVENANCE.md) + CHIME regeneration for the six never-generated
      co-detections: zach, oran, wilhelm, johndoeii, hamilton, chromatica.
- [ ] B3 **[data]** mahi 700–725 MHz RFI inspection before any measurement
      uses that sub-band range.
- [ ] B4 **[FLITS/data]** CHIME-band ACF/Δν_d measurements across the sample
      (two-screen table is DSA-band only until this lands).
- [ ] B5 **[FLITS]** Two-screen analysis rebuilt on joint CHIME+DSA scint
      (τ·Δν_d per band, screen-placement constraints per sightline).
- [ ] B6 **[FLITS]** Housekeeping: refresh `scintillation/DATA_PROVENANCE.md`
      (gen-2 md5s, h17 path), commit the h17-side tooling
      (`extract_time0_metadata.py`, generic npz builder) into the FLITS tree.

## C. Scattering re-fit under geometry selection (needs A + B)

- [ ] C1 **[FLITS]** Re-fit campaign across the twelve co-detections with
      geometry adjudication; PPC verification as in the thin-screen campaign.
- [ ] C2 **[FLITS]** Per-band systematics pass on the elevated-χ² trio
      (wilhelm, hamilton, zach).
- [ ] C3 **[ms]** Pin bump + table/figure regeneration from the campaign.

## D. Sightline analysis & foreground comparison (needs C)

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

- [ ] F1 **[ms]** Restructure abstract, observations (§2), §3.5, results,
      discussion, conclusions around geometry selection; purge rail-class
      vocabulary and all α=4-limit quoting (CONTEXT.md contract). β-language
      purge unblocks post-C; final content pass needs D/E (spine).
- [ ] F2 **[ms]** `tab:beta` rework: geometry-adjudicated quoting; descriptive
      exponential-consistency statements for ex-railed rows. Post-C3.
- [ ] F3 **[ms]** Consistency audit (mechanical): per-section sample counts,
      retired-language sweep, table/figure provenance vs pinned pipeline,
      cross-refs. Can run now on non-β sections.
- [ ] F4 **[ms]** Referee-mode full read-through. Sensible after F1; a
      structural pass on intro/observations/toa/budget can run now.
- [ ] F5 **[ms]** Prose polish (line-level), after F3/F4 triage.
- [ ] F6 **[ms]** `auth.tex`: core co-author list (names/order/affiliations —
      owner input pending).
- [ ] F7 **[decision]** `codetections_polarization/` disposition (companion
      materials? wire in, relocate, or leave).

## G. Release mechanics (last)

- [ ] G1 Push accumulated main commits (outward gate: Overleaf pulls main).
- [ ] G2 Clean `make` from a fresh clone + submodule init at the final pin.
- [ ] G3 Overleaf UI pull + visual check of the compiled PDF.

## Dependency spine

A1 → A2/A3 · B1–B4 → B5 · (A, B5) → C1+C2 → C3 (C2 gates Tier B→A
promotion, so it precedes the pin bump) · C3 → {F2, D} · D → E → F1 →
F4/F5 → G. F3 and a structural F4 pass on non-β sections are parallelizable
now; F6/F7 anytime.
