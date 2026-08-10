# Handoff: Kulkarni S1 landed (PR #108), fig1 batch rejected-with-direction, ledger backlog cleared (PR #107)

---
**Date:** 2026-07-17 12:58 PDT
**Author:** AI Assistant
**Status:** Handoff
**Branch (primary checkout):** `main` @ `c8e5639b` — **four behind** `origin/main` (`56cf4c4e` = PR #108 tip). Deliberately NOT pulled: the checkout holds two live separate lanes (below).
**Work branches this session:** `docs/ledger-specs-20260717` (merged squash `05eb3a67`, PR #107, cleaned up); `ms/s1-xray-mass-cap-20260717` (merged squash `56cf4c4e`, PR #108, cleaned up).

---

## Task(s)

Session arc: resumed from `handoff-2026-07-17-11-28-deflation-kulkarni-and-attribution.md`; the
owner then said they were "at a loss on the remaining owner decisions," so the
session reduced each to a concrete choice, obtained the decisions, and executed
them end-to-end.

| Task | Status | Notes |
|------|--------|-------|
| Docs-only ledger PR (six backlog specs + S1 plan) | ✅ Complete | PR #107 merged `05eb3a67`; local identical copies removed |
| Charter Kulkarni S1 (predeclared record + frozen decision rule) | ✅ Complete | `plan-cluster-xray-sz-mass-bound-2026-07-17.md` |
| Owner decision: fig1-model-toa batch | ✅ Complete | **Rejected `needs_revision` with direction** (see below); recorded hash-bound via `scripts/figure_review.py decide` |
| Owner decision: S1 sanction | ✅ Complete | Sanctioned; executed same session |
| S1 execution (Phases 0–3: PSZ2 + RASS + DM propagation) | ✅ Complete | SZ null; X-ray caps M500 at the catalog value |
| S1 Phase 4 gate-edge → owner adjudication | ✅ Complete | Owner chose **constraining, conservative endpoint** (M500 ≤ 1.7×10¹⁴, worst-case ECF) |
| Land the bracket change | ✅ Complete | PR #108 merged `56cf4c4e`; adversarial review 0 defects (8/8), CI 4/4 green twice |
| `ask-791f955b` closure | ✅ Complete | Already closed on the daemon (410) — no action was needed |
| Land S1 code+tests into FLITS submodule | 📋 Planned | Deferred: submodule working tree is the live joint-tf lane |
| Kulkarni S2 / S3 / discovery threads | 📋 Planned | Thread 1 just became hot (see Learnings) |

**Current Workflow Phase:** Validate (S1 lane closed; next lanes are planning-stage).

## Workflow Artifacts

**Produced this session (all on origin/main):**
- `plan-cluster-xray-sz-mass-bound-2026-07-17.md` — S1 predeclared record, v1.1 with the gate-edge adjudication trail.
- `experiment-cluster-xray-sz-mass-bound-2026-07-17.md` — full measurement + adjudication record (ADJUDICATED header is authoritative; analytic mid-sections are marked superseded).
- This handoff (untracked, primary checkout).
- `scripts/cluster_xray_sz/{rass_limit.py,harden_and_phase3.py}` — untracked durable copies of the S1 analysis scripts (the scratchpad originals die with the session); destined for `pipeline/analysis/cluster_mass_bound/` (action item 2).

**Consumed:** `handoff-2026-07-17-11-28-…`, `triage-kulkarni-feedback-2026-07-17.md` (S1 row now marked DONE on origin), `CONTEXT.md`, `decision-2026-07-14-figure1-and-chime-c1.md`.

## Critical References

- `docs/rse/specs/experiment/experiment-cluster-xray-sz-mass-bound-2026-07-17.md` (origin/main) — what was measured, the two frozen-rule ambiguities, and the owner's adjudication. Read before touching anything cluster/bracket related.
- `CONTEXT.md` — trust contract, unchanged this session; S1 stayed inside the V4/V5-cleared domain.
- `figure_review/batches/2026-07-17-fig1-model-toa/manifest.json` — carries the recorded rejection + re-render direction for the OPERON lane.

## Recent Changes (all merged to origin/main)

- `scripts/dm_budget_uncertainty.py:555-620` — `CL_M500_XRAY_UL = 1.67e14` + one-sided truncated-lognormal mass prior in `cluster_column_range()` (rejection resampling; cap=inf reproduces the old stream exactly).
- `scripts/dm_budget_uncertainty.csv` — only the two B2 cluster summary rows changed ([84,328]); all nine B1 host rows byte-identical.
- `main.tex:62-65`, `sections/results.tex:116-129`, `sections/conclusions.tex:22-27`, `sections/appendix.tex:70-75` — bracket 100–560 (factor ~6) → **≈80–330 (factor ~4)**, with the new RASS-cap sentence in results (cites `Piffaretti2011`, added to `bib/refs.bib`).
- DM_int centrals (243 etc.), `tab:budget`, approved figure bytes: untouched.

## Reproducibility & Data State

- **Seed:** `dm_budget_uncertainty.py` module RNG 20260707 (unchanged); truncated MC is seed-deterministic; untruncated control reproduces the published [96,563].
- **Environment:** `uv run --project pipeline --frozen` throughout; submodule pin `79b7b0e` (unchanged — the pin was NOT bumped).
- **S1 chain:** rate UL 0.066 ct/s (3σ aperture at θ500=3.57′, p10 exposure 689 s) × ECF (0.8–1.2)×10⁻¹¹ → L_X < (6.1–9.1)×10⁴³ → M500 ≤ (1.30–1.67)×10¹⁴ via MCXC regression (slope 0.619, intercept 0.328, round-trip 1.9% median); FlatΛCDM(70, 0.3), z=0.200, b=603.6 kpc. Queries: Vizier PSZ2/1RXS-BSC/FSC/MCXC + SkyView `RASS-Cnt Broad`.
- **Registry mass:** `pipeline/galaxies/foreground/data/intervening_census_registry.csv:23` — M500=1.48e14 (log 14.17); the prose "logM=14.1" is a rounding of this.

## Verification State / Known-Broken

- **Merged work:** consistency_audit clean; root science tests 97 passed/1 xfailed; latexmk clean; CI 4/4 green on both PR #108 commits; adversarial subagent review 0 defects.
- **Primary checkout: four behind origin, dirty with THREE separate lanes — do not pull, do not sweep:**
  1. **OPERON model-TOA/joint-tf lane (live):** `sections/toa.tex`, `scripts/plot_codetection_data_grid.py`, `pipeline` (submodule drift), untracked `figure_review/batches/`, `figures/toa_offset_decomposition.pdf`, and the repository-cleanup spec quartet + `research-flits-branch-audit-2026-07-17.md`. Mid-repair: its 11:42 journal entry diagnosed RFI-contaminated fit inputs (mask-unaware `downsample()`); refits of casey/chromatica/wilhelm pending.
  2. **Polarization-companion lane (new, separate-active):** `codetections_polarization/*` dirty + 2 untracked — refreshed 12:19 by session `kulkarni-explore` (lane `pol-companion-sync`) from an **owner-supplied zip**. Preserve.
  3. **This session's residue:** this handoff + `scripts/cluster_xray_sz/` (untracked, join the next docs PR).
- Shared-append `docs/rse/protocols/journal.jsonl` + baked `docs/rse/control/board/readiness.html` dirty as always (multi-lane log; never sweep into a task commit).
- **Unverified/deferred:** the S1 scripts are not yet tests in the pipeline (action item 2); the fig1 re-render has not been produced yet (OPERON side).

## Learnings

- **The frozen-rule thresholds must be computed from pipeline inputs, not prose.** S1's gate was written from the prose-rounded logM=14.1; the registry's 1.48e14 shifted the intended threshold by 0.07 dex and flipped the verdict at one systematic endpoint. Surfacing the gate-edge to the owner (rather than self-adjudicating either way) was the correct move and produced a clean decision trail. Future predeclared rules: pin thresholds to the machine-readable source of truth.
- **Truncating a prior renormalizes BOTH ends** — the bracket's low edge moved 96→84 as a consequence of conditioning on M ≤ cap, verified robust across seeds by the reviewer. Expect referee questions to be answerable from the experiment record.
- **PSZ2 is useless below ~2.5×10¹⁴ at z≈0.2** (empirical catalog floor) and **eROSITA DR1 excludes l<180°** (RU half) — for any future mass bound on this or nearby systems, RASS aperture photometry + MCXC regression is the workable stack, and the position-local exposure (from 1RXS neighbour ExpTime) is the load-bearing input.
- **Figure-review rejections are recorded with `scripts/figure_review.py decide`** (hash-bound, in the batch manifest) — not by editing the manifest by hand.
- **`kulkarni-explore` is a concurrent session on this repo** (journal lane `pol-companion-sync`) — check the journal for its entries before starting Kulkarni-adjacent work to avoid duplication.

## Action Items & Next Steps

1. [ ] **Thread 1 (RM → cluster B-field) is now the hot lane.** The refreshed polarization companion carries full RM data for FRB 20230307A (journal 12:19 entry: RM_obs=−473.49, their host-attributed RM_host=−756±15, B_∥=−2.0 μG, **no intervening term in their RM budget**) while our budget now attributes 243 pc cm⁻³ to the intervening cluster with an X-ray-capped mass. That seam — re-partitioning RM between host and cluster given DM_int — is exactly Kulkarni Thread 1, unblocked on both sides. Needs: a predeclared lane + coordination with the companion-paper owners before any attribution claim; coordinate with `kulkarni-explore` (it owns the companion-sync lane).
2. [ ] **Land S1 code+tests** as `pipeline/analysis/cluster_mass_bound/` on a FLITS branch (sources: `scripts/cluster_xray_sz/`; tests per plan Phases 0–3) once the joint-tf lane parks its submodule working tree. Not a pin-bump side effect — its own reviewed step.
3. [ ] **fig1-gallery re-render** (OPERON side): observed-peak markers only, pin-matched provenance, new batch + hashes; owner then reviews the new batch.
4. [ ] **Primary-checkout sync** after lanes 1–2 (of Verification State) commit/park: `git pull --ff-only` (currently 4 behind).
5. [ ] **Kulkarni S2** (a-priori crossing probability; small, self-contained, needs predeclared method) and **S3** (f_IGM decircularization; larger, defer to V5 follow-up).
6. [ ] **Next docs PR** picks up this handoff + `s1-scripts/` (and any specs the other lanes release).

**Recommended Next Skill:** `ai-research-workflows:planning-implementations` — charter Thread 1 (RM→cluster B-field) as a predeclared cross-paper lane; its plan must pin thresholds to pipeline values (see Learnings) and define the coordination contract with the polarization companion.

## Other Notes

- Owner decisions this session (all executed): fig1 batch → reject-with-direction; S1 → sanction; S1 gate-edge → constraining-conservative. The decision trail lives in the batch manifest, the plan v1.1, and the experiment record.
- Standing authorization covered all pushes/PRs/merges; squash-merge precedent maintained; no force-pushes; `overleaf-*` branches untouched.
- Project memory gained `verdi-draft-is-redshift-standard` from a concurrent session (johndoeII z=0.5535; propagation lane not chartered) — redshift-touching work should read that memory first.
- Board deployed through the session: https://jakobtfaber.github.io/Faber2026/board/ (journal entries at 11:57, 12:0x, 12:2x, 12:4x cover the arc).

---

**Handoff created by AI Assistant on 2026-07-17.**
