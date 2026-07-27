# Local-branch consolidation receipt — 2026-07-27

**Objective:** owner directive (2026-07-26/27 session): investigate every
local branch in the three project checkouts, integrate anything still worth
landing into `main`, then delete, leaving only `main`, `overleaf/*`,
`entire/*`, and `gh-pages`.

**Phase:** reconciliation → retirement (complete).

## Scope and snapshots

Three local checkouts on jakob-mbp under
`~/Developer/repos/github.com/jakobtfaber/Faber2026`:

| Repo | Checkout | Branches before (this wave) | After |
|---|---|---|---|
| jakobtfaber/Faber2026 (parent) | repo root | 96 (2026-07-26 audit) → 41 | `main`, `entire/5e3c6b3-e3b0c4`, `entire/checkpoints/v1` |
| jakobtfaber/Faber2026-analysis | `analysis/` | 84 | `main` |
| jakobtfaber/dsa110-FLITS | `pipeline/` | 47 | `main`, `entire/checkpoints/v1` |

Remote branches were not touched. `gh-pages` exists only as a remote ref.

## Zero-data-loss backups (all verified complete-history bundles)

In `analysis/archive/` (untracked; not committed — 4.6 GB total):

- `local-branches-backup-20260726.bundle` (791M, parent, pre-first-wave, by
  the 2026-07-26 session)
- `analysis-repo-local-branches-20260727.bundle` (861M) ·
  `flits-repo-local-branches-20260727.bundle` (683M) — pre-deletion
- `parent-final-purge-20260727.bundle` (859M) ·
  `analysis-final-purge-20260727.bundle` (683M) ·
  `flits-final-purge-20260727.bundle` (655M) — fresh tips immediately before
  the final purge

Every deleted tip is recoverable from these bundles.

## Classification criteria

1. Merged pull request for the head branch (squash-merge aware — `git
   cherry` is unreliable here; blob/content identity used as the signal).
2. Tree identity vs `origin/main` (two-dot) — catches squash-merged
   leftovers the three-dot test misses.
3. Closed-unmerged pull request + objective met by a later merged PR →
   rejected lane.
4. FLITS pre-rewrite branches (14, no merge base with the rewritten main):
   two-dot tree comparison; none tree-identical; preserved in bundles; the
   pre-rewrite mainline is also on the `upstream` remote as
   `archive/pre-rewrite-main`.

Detailed per-branch evidence: `branch-disposition-receipt-20260726.json`
(parent, by the 2026-07-26 session),
`branch-disposition-receipt-analysis-20260727.json`,
`branch-disposition-receipt-flits-20260727.json`, and
`branch-consolidation-deletions-20260727.txt` (exact `branch -D` record).

## Integrations executed (content verified absent from main)

- **Faber2026-analysis #136 (merged):** removed the five superseded
  automated-cleaner RFI tickets; BOARD realigned to the manual-route
  disposition and the scint-redo-01 charter.
- **Faber2026 #259:** README "Start here" pointer to the repository
  provenance map, salvaged from `publish/repository-provenance-map-followup`
  (no PR existed; rest of the branch already on main).
- **dsa110-FLITS #236:** `galaxies/foreground/config.py` registrations for
  GSC2.4.2 / CatWISE2020 / unWISE, salvaged from
  `codex/b4-figure-review-20260720` commit `c6cd1c3`; the cross-reference
  CSV itself was already on main in a richer landed form.

## Flagged-then-discarded (justifications)

- **Host-DM repair lanes** (parent `codex/host-dm-repair{,-v2}`,
  `codex/host-dm-current-paired-20260723`; analysis
  `codex/host-dm-repair-v2`, `codex/host-dm-current-provenance-20260723`):
  repair PRs #204 (parent) and #56 (analysis) were closed unmerged, and the
  wayfinder ticket 07 resolution (2026-07-22, owner-accepted) retained the
  current priors and host-DM headline — the deterministic-PDF/appendix-table
  repair was evaluated and not adopted. Content preserved in bundles.
- **FLITS `agent/dm-phase-v2` lane:** the operative first-pass DM catalog
  (`dm-joint-phase-v2/manuscript_dm_catalog.csv`) is tracked on
  Faber2026-analysis `main` — deleting the branch does not touch the
  operative artifact. The whole DM adjudication is first-pass pending the
  scint-redo re-derivation.
- **FLITS `codex/archive-historical-diagnostics-20260720`:** an unmerged
  ~320k-line pruning; adopting mass deletions was declined — bundle keeps
  the branch.
- **`pewter-maxwell` (parent):** 1414-file offline experimental burst
  dataset; data belongs under `~/Data`, not the manuscript repo; preserved
  in bundles.
- **RFI prototype/preservation lanes (all repos):** rejected or mooted by
  the 2026-07-26 owner disposition (manual bad-channel maps are the sole
  authority).
- **2026-07-17-era figure/scintillation draft branches (`ms/*`)**: rejected
  or superseded (fig1 batch rejection; two-component first-pass demotion).

## Still prohibited / untouched

- No remote branch deleted; no force-push to any shared ref; `gh-pages` and
  `entire/*` untouched per the owner's keep-list; the analysis and pipeline
  submodule gitlinks in the parent were not bumped by this work (the
  analysis pin now trails analysis `main` by the #136 ticket cleanup —
  a separately scoped pin-bump step).

## Disposition

Complete once Faber2026 #259 and dsa110-FLITS #236 merge and their branches
are deleted locally (remote branch auto-delete not used).
