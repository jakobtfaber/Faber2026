# Handoff: Fig 1 nside=32 skymaps + association-card font standardization

---
**Date:** 2026-07-08 07:26
**Author:** AI Assistant
**Status:** Handoff
**Branch:** docs/clarify-chance-coincidence (Faber2026); main (dsa110-FLITS)
**Commit:** f139c7b (Faber2026 local == origin, 0/0); a825ace (dsa110-FLITS main)

---

## Task(s)

Two manuscript-figure tasks, both landed on their GitHub remotes; the Overleaf-side propagation is the only open thread.

| Task | Status | Notes |
|------|--------|-------|
| Higher-res NE2025 Fig 1 skymaps (nside=8 → nside=32) | ✅ Complete | Computed on h17, merged to Faber2026 `main` via PR #23 → PR #25 (`eeed373`). |
| Association-card font fix (DejaVu Sans → CM serif) | ✅ Complete | dsa110-FLITS PR #141 merged (`a825ace`). |
| Regenerate 12 association-card PDFs into Overleaf | 🔄 In Progress | PDFs written to local Overleaf checkout, **not committed/pushed**. See Known-Broken. |
| Overleaf pull of nside=32 skymaps + referee `main.tex` | 📋 Planned (user action) | Requires manual Overleaf-side "Pull GitHub changes". |

**Current Workflow Phase:** Validate (figures produced + visually verified; propagation to Overleaf pending)

## Critical References

- `scripts/plot_ne2025_mw_properties.py` (Faber2026) — the NE2025 all-sky figure generator. Now parametrized: `--nside` / `--nproc` / `--xsize`, nside-keyed cache + figure names. Default stays nside=8.
- `crossmatching/plot_association_cards.py` (dsa110-FLITS) — association-card generator. Now imports `use_flits_style()`; **hardcodes** `MANUSCRIPT_OUTDIR = ~/Developer/overleaf/Faber2026/figures/association_cards` (line ~46) and writes PDFs straight into the Overleaf checkout.
- `flits/plotting.py:use_flits_style()` (dsa110-FLITS) — the canonical figure style: Computer Modern serif (`cmr10`), `mathtext.fontset=cm`, `text.usetex=False`. This is the manuscript figure standard; `pipeline/matplotlibrc` is its standalone-script equivalent.

## Recent Changes

- `scripts/plot_ne2025_mw_properties.py` — added argparse (`--nside`/`--nproc`/`--xsize`); nside-keyed cache (`ne2025_allsky_cache_nside{N}.npz`) and figure names; `xsize` bump for finer maps. Committed in PR #23, now on Faber2026 `main`.
- `sections/observations.tex` — Fig 1 `\includegraphics` now points at `figures/ne2025_mw_characterization_nside32.pdf` (in the referee-restructured file this is ~line 90, under `\label{fig:ne2025_mw}` / `sec:obs-mw`).
- `crossmatching/plot_association_cards.py:15-24` — replaced `plt.style.use("default")` + DejaVu rcParams with `from flits.plotting import use_flits_style; use_flits_style()`, keeping card-specific small font sizes (8/9/7/6) + `pdf.fonttype:42`. +6/−1. On dsa110-FLITS `main`.

## Reproducibility & Data State

- **NE2025 figure:** regenerated via `python scripts/plot_ne2025_mw_properties.py --nside 32 --nproc <cores>`. Cache `scripts/ne2025_allsky_cache_nside32.npz` (277 KB, 12,288 sightlines) committed — re-plotting is instant, no recompute. Env: `base` conda on this Mac (has `healpy`+`mwprop`), or on **h17** a dedicated `ne2025` conda env (python 3.12, `healpy matplotlib pandas numpy` + pip `mwprop adjustText mpmath scipy`). h17 clone at `~/Faber2026`.
- **h17 timing:** nside=32 = ~50 min real on 40 cores (per-pixel ~3× slower under 40-way contention — `mwprop`/mpmath is memory-bandwidth bound; load ran ~46 on 40 cores, oversubscribed). For nside=64 cap `--nproc 36`.
- **Association cards:** regenerate via the fixed script; inputs are 4 committed JSONs in `crossmatching/` (`toa_crossmatch_results.json`, `association_report.json`, `chime_side_inputs.json`, `notebook_reproduction_fixture.json`). Env: conda `flits`. Run with the clone on `sys.path` so the fixed script is used. Scratch clone retained at `<scratchpad>/flits-clone`.

## Verification State / Known-Broken

- **Tests:** not run (figure-only changes; no runtime surface). Both figures **visually verified** by rendering — nside=32 skymaps resolve the Galactic plane; `association_card_casey` renders in CM serif matching Fig 1/Fig 2.
- **Uncommitted / unpushed (the one open lane):** the **11–12 regenerated association-card PDFs** in `~/Developer/overleaf/Faber2026/figures/association_cards/` are modified in that local checkout, **not committed, not pushed**. That checkout's `origin` is `github.com:jakobtfaber/Faber2026.git` (same repo, separate working copy) — so the new cards reach nobody until committed + pushed there, then Overleaf pulls. **Count drifted 12 → 11** between turns (another lane touched one) — reconcile before committing; do not assume all 12 are the CM-serif versions.
- **Unverified:** whether Overleaf's GitHub sync actually tracks `main` (assumed, not confirmed with the user). If it tracks a different branch, the skymap pull won't show until the figure reaches that branch.

## Learnings

- **Overleaf ≠ auto-sync.** Overleaf GitHub Sync is on-demand (UI: Menu ▸ GitHub ▸ Pull GitHub changes) and tracks **one branch (assume `main`)**. The nside=32 figure had to be brought to `main` (not just the feature branch) via a dedicated merge before Overleaf could see it.
- **Stale-PR "MERGEABLE/CLEAN" is a trap.** PR #23's branch was cut from an older base; a later `merge-tree` showed a *clean* 24-file diff that would have **deleted** the live session's jointmodel fit artifacts and reverted budget prose. Fix: rebase the PR branch onto current base → figure-only 5-file diff. Always inspect the *merge delta*, not just the mergeable flag.
- **Never operate `git --git-dir` against the live submodule git-dir.** Doing so to build a pipeline branch collided with another agent's index and left my commit polluting their branch ref (`agent/sightline-halo-grid-figure`). Recovery: `reset --soft` the ref back to origin (preserves their dirty tree). Correct approach = a fresh standalone clone in scratch, isolated from the shared refs/index.
- **`lane-liveness` gates edits.** The main checkout and the `pipeline` submodule both returned `verdict: live` (active co-writer). Rule held: do not rebase/pull/stash a live tree; isolate work in a worktree/clone and let the owner integrate.
- **The font "standard" is `flits.plotting.use_flits_style()`** — CM serif cmr10. Fig 3 (association cards) was the *only* figure bypassing it; Fig 1/Fig 2 were already correct.

## Action Items & Next Steps

1. [ ] **Reconcile the Overleaf association-card lane** (`~/Developer/overleaf/Faber2026/figures/association_cards/`): confirm all 12 PDFs are the CM-serif regenerations (count drifted to 11 — regenerate any missing), then commit + push to `Faber2026`. This is a one-way door — get explicit user go.
2. [ ] **User: Overleaf Pull.** In Overleaf, Menu ▸ GitHub ▸ Pull GitHub changes, then recompile — brings the nside=32 skymaps, the referee `main.tex` edits, and (once pushed) the CM-serif cards.
3. [ ] **Confirm which branch Overleaf syncs** (assumed `main`). If not `main`, the skymap/card updates won't appear until they reach that branch.
4. [ ] Optional cleanup: delete scratch clone `<scratchpad>/flits-clone` once the Overleaf cards are pushed.

**Recommended Next Skill:** `ai-research-workflows:ensuring-reproducibility` (to lock the figure-regeneration provenance), or none — the remaining work is git/Overleaf propagation, not a research-workflow phase.

## Other Notes

- **Separate lanes left untouched** (do not sweep into any commit): 4 active pipeline worktrees — `agent/sightline-halo-grid-figure` (main submodule checkout, dirty, live), `provenance/data-manifest`, `agent/v6-dm-provenance-toa`; plus the co-writer's referee-response work that landed as `c330d77` and reconciled the local `docs/clarify` branch to origin (now 0/0).
- **PRs this session:** Faber2026 #23 (fig→docs/clarify, merged), #24 (fig→main, closed as subsumed), #25 (docs/clarify→main, merged, `eeed373`); dsa110-FLITS #141 (font fix, merged, `a825ace`).
- Do **not** merge a stale figure PR without re-checking the merge delta (see Learnings).

---

**Handoff created by AI Assistant on 2026-07-08**
