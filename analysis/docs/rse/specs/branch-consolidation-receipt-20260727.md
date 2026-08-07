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

## Addendum — remote branch sweep (2026-07-27, owner-authorized)

Owner authorization (verbatim): "delete the old remote branches in all three
repos, keep main/gh-pages/entire/overleaf-*".

Before deleting, every live remote head was fetched and captured in three
additional complete-history bundles in `analysis/archive/`:
`parent-remote-refs-20260727.bundle`, `analysis-remote-refs-20260727.bundle`,
`flits-remote-refs-20260727.bundle`.

29 live remote branches deleted (2 parent, 17 analysis, 10 FLITS; exact list
in the session deletion log; every tip bundle-preserved). Kept:
`main`, `gh-pages`, `entire/*`, `overleaf-2026-07-11-2125` (Overleaf sync),
and `chore/ignore-codacy-instructions` (open PR #260 — delete after merge).
Verified post-sweep via `ls-remote`: Faber2026 = {chore/ignore-codacy-instructions,
entire/checkpoints/v1, gh-pages, main, overleaf-2026-07-11-2125};
Faber2026-analysis = {main}; dsa110-FLITS = {entire/checkpoints/v1, main}.
This supersedes the "Remote branches were not touched" line above.

## Addendum 2 — frozen-evidence carve-out (2026-07-27)

The sweep deleted dsa110-FLITS `archive/foreground-source-freeze-pr231`
(tip `c913175e567d`), which is the **frozen-evidence anchor** for the
Figure 3 source-verification binding: the root-science tests resolve
`c913175e:galaxies/foreground/data/intervening_census_registry.csv`, and
that commit is deliberately *not* an ancestor of pipeline `main`. Parent CI
failed; the branch was restored from the pre-sweep bundle and verified back
on the remote at the same tip. Standing rule: **branches named as
frozen-source bindings in tests, the results registry, or gate tickets are
CI dependencies, not clutter — exempt from any branch keep-list.** The
second CI failure had the same root as analysis #140: the certified-route
test still hard-coded the removed ladder tickets; fixed there.

Companion machine scope: the h17 inventory recorded at
[`h17-inventory-2026-07-27.md`](h17-inventory-2026-07-27.md) — untouched by
this consolidation; any h17 retirement is a separately chartered lane.

## Addendum 3 — results-registry orphan repair (2026-07-27)

The pin-bump run of the root-science tests failed again: the results
registry (`docs/rse/control/results-registry.toml`) pins provenance
commits by SHA, and the sweep had orphaned two of them. A full sweep of
every 40-character SHA in the registry and its claim-owners file against
the surviving refs of all three remotes found exactly these two; all other
cited commits remain reachable.

- dsa110-FLITS `9175b92529b3` (association sample_roster / sample_table /
  pcc_sum provenance; was the tip of swept branch
  `codex/provenance-dm-associations-9175b925`) → restored from the local
  clone as `archive/provenance-dm-associations-9175b925`.
- Faber2026 `8d492feaa426` (budget_table.tex artifact provenance; was on
  swept branches `codex/scintillation-notebook-wayfinder` /
  `pewter-maxwell`) → restored as `archive/registry-budget-table-8d492fea`.
  This one was not flagged by CI (the validator only resolves pipeline
  pins) but is a registry citation all the same.

Correction (same day): the first sweep counted a commit as reachable if
*any* remote's refs contained it, so it missed a third orphan reachable
only from the `upstream` org remote — which the fork-cloning CI cannot
see. The corrected, re-runnable check restricts containment to `origin/*`
of the repository each registry entry names (strict per-repository sweep:
0 unreachable after the restorations).

- dsa110-FLITS `6c878906156d` (association cards_figures and
  mw.foreground_characterization pins; reachable only via
  `upstream/dm-campaign-2026-07` / `upstream/pin/faber2026`) → restored to
  the fork as `archive/registry-cards-mw-6c878906`.

All three archive refs join the frozen-evidence carve-out of Addendum 2.
