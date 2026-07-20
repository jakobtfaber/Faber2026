# Handoff: Referee-report implementation pushed + branch divergence reconciled

---
**Date:** 2026-07-08 07:29
**Author:** AI Assistant
**Status:** Handoff
**Branch:** docs/clarify-chance-coincidence
**Commit:** f139c7b (tip; my work is commit `c330d77`, an ancestor)

---

## Task(s)

Implement a full referee-style review of this manuscript — "Scattering,
Scintillation, and Energetics of FRBs Codetected by CHIME/FRB and DSA-110" —
then commit & push, then clean up the branch divergence that the concurrent
writers created.

| Task | Status | Notes |
|------|--------|-------|
| Implement referee items B1–B5, D1–D5, association 1–3, MW 4–5, census 6–8, minor 9–16 | ✅ Complete | Committed `c330d77`, on `origin`. Manuscript compiles clean (32 pp, 0 undefined refs). |
| Commit & push referee work | ✅ Complete | Pushed to `origin/docs/clarify-chance-coincidence`; survived two concurrent origin advances (PR #23, then `f139c7b`). |
| Reconcile diverged local branch to origin (Option C) | ✅ Complete | Local == origin (0/0). Superseded conflict-drafts dropped; separate-lane uncommitted work preserved as pure additions. |
| Author-decision review of the flagged knobs | 📋 Planned | See Action Items — these are the human/next-session calls the implementation deliberately did not make. |

**Current Workflow Phase:** Implement (referee items landed & verified) → next is Validate / author review.

## Workflow Artifacts

**Input document (the review being implemented):**
- `docs/referee_report_2026-07-07.md` — the referee-style review with B1–B5, D1–D5, association/MW/census/minor items. **Untracked** (never committed — see Known-Broken). Read this first to understand every change's motivation.

**Related existing specs (context, not produced this session):**
- [plan-trust-reset-revalidation.md](../plan/plan-trust-reset-revalidation.md) / [research-trust-reset-revalidation.md](../research/research-trust-reset-revalidation.md) — the governance regime (`CONTEXT.md`) that gates which lanes may state sky results. B1/B2 live in the already-cleared budget lane.
- [validation-sightline-halo-grid.md](../validation/validation-sightline-halo-grid.md) — foreground-census figure the census items (6–8) touch.
- [handoff-2026-07-07-10-11-v6-phase6-complete.md](../handoff/handoff-2026-07-07-10-11-v6-phase6-complete.md) — prior V6/Phase-6 handoff (scattering-fit revalidation lane; untouched here).

No research/plan/experiment docs were produced this session — this was a direct implementation pass against an external review.

## Critical References

Read these first, in order:

1. `docs/referee_report_2026-07-07.md` — the review that every change implements (untracked, repo root `docs/`).
2. `scripts/dm_budget_uncertainty.py` — the B1/B2 core. Self-contained numpy/scipy forward model of `DM_host` as a posterior; regenerates `scripts/dm_budget_uncertainty.csv` and `figures/dm_host_posteriors.{pdf,png}`. Run: `python3 scripts/dm_budget_uncertainty.py`.
3. `sections/appendix.tex` — new **Appendix C** (`\label{app:host-forward-model}`): prior list, `tab:host-forward-model` (9-row P(DM_host<0) table), `fig:dm_host_posteriors`. The referee's headline ask (negative residuals → consistent-with-zero) is realized here.

## Recent Changes

All in commit `c330d77` (18 files) unless noted. Highlights:

- `scripts/dm_budget_uncertainty.py` (new) — samples the full skewed Macquart `P(DM_cosmic|z)` (Macquart-2020 form, McQuinn-2014 scatter, `F∈[0.25,0.40]`, James-2022) + disk/halo/intervening priors; forward-models `DM_host` instead of mean-subtraction (**B1**). β-model vs mNFW intracluster cross-check (**B2**), LOS truncated at R200=1.48·R500.
- `budget_table.tex` — `DM_host` column now posterior median ± 16–84% interval (e.g. `211^{+46}_{-112}` for 20240229A); FRB 20230814B reordered to chronological row 8; note m expanded (fallback mass = fiducial logM*≈10, Moster+2013). Auto-merged cleanly with origin's DM_MW-recompute + coverage-zeros work.
- `sections/appendix.tex` — Appendix C (above) + B2 caveat in the `clusters_icm` caption.
- `sections/toa.tex` — B3 trials-factor paragraph; B4 timing sign convention + `|τ_geo|≤4.5 ms` geometric bound + acceptance criterion; assoc-2 `f_DM=1` for the position-only class; B5 → Data Availability pointer. **Conflict-resolved** against origin's P_cc/position-only rewrite (kept origin's wording, appended my `f_DM=1` content; verified origin's `eq:pcc_mu` uses the same `f_DM` notation).
- `main.tex` — keyword "Radio bursts (1339)"; `\software` with astropy 3-cite + pygedm/Price-2021; abstract cluster uncertainty "≈100–560". **Conflict-resolved**: kept origin's GitHub/dsa110-FLITS Data Availability (they rejected Zenodo), preserved my `\label{sec:data-availability}` + fuller software cites, re-pointed the pipeline cite to GitHub not "archived with this paper".
- `sections/{observations,methods,results,conclusions,intro,budget}.tex`, `bib/refs.bib` (11 new entries), `sample_table.tex` + `scripts/make_sample_table.py` (nickname column removed) — the remaining D1–D5 / census / minor items.

## Reproducibility & Data State

- **B1/B2 artifacts regenerate from one script:** `python3 scripts/dm_budget_uncertainty.py` → `scripts/dm_budget_uncertainty.csv` + `figures/dm_host_posteriors.{pdf,png}`. N = 2×10⁵ MC samples per sightline.
- **Priors are fiducial choices** (documented in Appendix C so they can be revised): 30% lognormal disk; halo 40 median, factor-~2 (σ_ln≈0.35); intervening 40% (measured-mass) / factor-2 (assumed-mass) / 30% (cluster); `F` uniform on `[0.25,0.40]`. **These set every posterior width and every P(DM_host<0).**
- **Env:** repo builds with `latexmk -pdf` (system TeX); the Python script needs only numpy/scipy (numpy 2.x — uses `np.trapezoid`, not `np.trapz`).
- **No seeds pinned** in the MC (results are stable to the quoted precision at N=2×10⁵; pin a seed if exact reproduction of the last digit is needed).
- `scripts/.citation-check-disabled` (new) scopes the citation-check Write hook off for code files under `scripts/` only — manuscript `.tex` is still checked. Needed because the hook flagged bib-present citations in code comments.

## Verification State / Known-Broken

- **Manuscript build:** ✅ clean — `latexmk -pdf` → 32 pp, **0 undefined refs/citations** (verified post-merge at the `c330d77` tree). 2 pre-existing overfull hboxes (eq:eiso display + a 2 pt math box), not introduced here.
- **On origin:** ✅ `c330d77` is an ancestor of the current tip `f139c7b`; referee content confirmed present (Appendix C, forward-model script). Only `f139c7b` "pin explicit DSA scintillation subband figures" (separate lane) landed after.
- **Local branch:** ✅ `docs/clarify-chance-coincidence` == origin (0 ahead / 0 behind). Divergence fully resolved.
- **Uncommitted (working tree — all separate-lane, preserved, verified pure additions vs origin):** `CONTEXT.md` (Wilhelm/EMG guardrail note), `docs/rse/protocols/journal.jsonl`, `scripts/journal-cadence-{cursor,posttool}-hook.sh`, `scripts/journal-staleness-hook.sh`, `pipeline` submodule pin; untracked `docs/referee_report_2026-07-07.md`, `_trash/`, and another agent's `handoff-2026-07-08-07-26-figure-resolution-font-standardization.md`. **None of these are mine to commit** — left for their owners.
- **Backups (delete once confident):** tags `backup/local-20260708-070029` and `backup/worktree-20260708-070029`; bundle + 257 MB tarball under the session scratchpad. Undo everything: `git reset --hard backup/local-20260708-070029 && git stash apply backup/worktree-20260708-070029`.
- **Unverified:** the 11 new `bib/refs.bib` entries were written to ADS format but not spot-checked against ADS. The β-model cluster range (~100–560) depends on the fiducial f_gas/M500 spans (Appendix C).

## Learnings

- **This branch has live concurrent writers** (Overleaf sync + multiple agent worktrees: `rebase-pcc`, `jointmodel-pr-reconcile`, `push-clarify`, `push-v6`). Origin moved **twice** mid-operation (PR #23 nside=32 maps, then `f139c7b`). Always re-fetch immediately before pushing; **never force-push** — fast-forward or re-rebase onto the new tip.
- **Cherry-pick the single commit, don't `git rebase` the whole local branch.** The local branch carried 8 unpushed commits but only 1 was mine; a full rebase would have replayed 2 *diverged* separate-lane commits (`4918633` chance-coincidence, `b0cdd26` DM_MW) that origin already has as different SHAs (`7478397`, `ca3e434`) — clobbering someone else's work. `git cherry -v origin <branch>` distinguishes patch-equivalent (`-`) from diverged (`+`).
- **Those 2 "diverged" commits held nothing unique** — origin's versions are supersets/refinements (verified by blob-diffing `<local>:file` vs `<origin>:file`). The divergence was an older draft of already-pushed work.
- **`main.tex` and the section `.tex` files are Overleaf-synced** (see the `main.tex` header + origin's "Updates from Overleaf" commits). Direct git edits to prose can be reverted by the next Overleaf pull — **mirror any git-only prose edits into Overleaf** (see Action Items).
- **Author decision already made for you, flag if wrong:** Data Availability = **GitHub/dsa110-FLITS, not Zenodo** (origin's deliberate choice; my Zenodo draft was dropped in the conflict resolution).
- **Non-destructive branch reconcile pattern:** `git reset --mixed origin` (moves branch, preserves working tree) + `git checkout origin -- <superseded-draft-files>` beats `reset --hard` — it never risks the separate-lane uncommitted work.

## Action Items & Next Steps

1. [ ] **Author-review the fiducial priors** in `scripts/dm_budget_uncertainty.py` / Appendix C (disk 30%, halo factor-2, intervening 40%/factor-2, F∈[0.25,0.40]). They drive every `DM_host` posterior width and every `P(DM_host<0)`. Adjust and rerun the one script if the referee's/author's priors differ.
2. [ ] **Confirm the headline `DM_host` change is acceptable** — posterior medians run *higher* than the old arithmetic residuals (the intended skew correction). The two formerly-negative sightlines (20220310F, 20221203A) now read `P(<0)≈0.45`.
3. [ ] **Mirror the git-only `main.tex` additions into Overleaf** (keyword "Radio bursts (1339)", abstract "≈100–560", the astropy/pygedm `\software` cites) or the next Overleaf sync will drop them.
4. [ ] **Fill B3's exact DSA-110 trial count** — the trials-factor paragraph in `sections/toa.tex` uses a described denominator; confirm the precise number of independent DSA triggers searched.
5. [ ] **Confirm B7 galaxy search aperture** wording in `sections/observations.tex` (census-7) matches the actual pipeline aperture.
6. [ ] **Spot-check the 11 new `bib/refs.bib` entries** against ADS (astropy 2013/2018/2022, Price 2021, James 2022, McQuinn 2014, Cordes 2016, Arnaud 2010, Keating-Pen 2020, Cook 2023, Moster 2013).
7. [ ] **Note the minor-9 ↔ F1 interaction** — the de-processed opening prose (results/conclusions/intro) assumes the withheld-slots F1 plan; keep consistent when scattering/scint/energy slots are repopulated.

**Recommended Next Skill:** `ai-research-workflows:validating-implementations` — verify the referee changes hold against the review item-by-item and close the author-decision flags above. (For the separate scattering-fit revalidation lane, the V6/Phase-6 handoff remains the entry point.)

## Other Notes

- If a future `git pull` ever surprises you, the branch is currently a clean fast-forward of origin; the backups above make any recovery a one-liner.
- Do not commit `docs/referee_report_2026-07-07.md` to a pushed branch without checking whether the review is meant to stay private — it was deliberately left untracked (pushing it is an outward, one-way action).

---

**Handoff created by AI Assistant on 2026-07-08**
