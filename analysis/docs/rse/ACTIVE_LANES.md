# Active lanes

Owner-facing control surface for Faber2026 consolidation. One row per
workstream. Closed lanes move to the archive once their evidence is recorded.
Do not add narrative history here.

| Lane | Canonical repository/branch | Status | Next gate | Evidence | Worktree |
|---|---|---|---|---|---|
| Figure revalidation & replacement | `jakobtfaber/Faber2026` — new batch branches off `main` only | product selected; science and exact-byte approval pending | Freeze and revalidate the adopted-DM catalog, then render a new isolated `fig1-gallery` candidate under the locked data-only 4-by-3 contract | [Figure 1 and C1 decision](specs/decision-2026-07-14-figure1-and-chime-c1.md); merged PR #35 (gate); rejected packet archived at `archive/rejected-figure-candidates-20260714` | None; create a fresh isolated worktree for each new batch |
| CHIME C1 qualification | `jakobtfaber/dsa110-FLITS` — branch `scint/c1-allpairs-crossgp` (PR #176) + `scint/eligibility-caveats` (PR #177) | **C1 DOCUMENTED-FAIL (blinded NO-GO, 2026-07-14)**: 0/8 gated cells, nulls fail, no unblinded fit; caveat hygiene done; PRs open | Merge PRs #176/#177, then open the `p1-window-upchan` successor lane (windowed re-upchannelization on h17, plan Phase 3) — estimator tuning on the retained product is closed by the stop rule | [Figure 1 and C1 decision](specs/decision-2026-07-14-figure1-and-chime-c1.md); [C1 calibration experiment record](specs/experiment-chime-scint-c1-calibration.md); [revival plan v1.1](specs/plan-chime-scint-corrected-products-revival.md) | `flits-caveat-hygiene` worktree (pushed); dirty regenerated B4 outputs remain a separate lane in the main pipeline tree — commit/revert independently |

## Archive

| Lane | Closure evidence |
|---|---|
| P0 provenance freeze | FLITS PR #170 merged (`82fc7ec`); tree-identical to independently validated post-`788b819` integration; 11 focused, 230 FLITS, and 54 parent tests passed |
| FLITS figure-branch integration (pin chain) | FLITS PR #173 merged (`788b819`); Faber2026 pin-only PR #38 merged (`251d634`); pin verified reachable from FLITS `main` |
| Figure approval gate implementation | Merged PR #35 (`af06269`, v4 lane); v1–v3 worktrees are preserved dirty experiments, not authoritative |
| July replacement figure refresh | Merged PR #34; figures subsequently rejected by owner and withheld by PR #35 |
| Rejected July candidate packet | PR #36 closed without merge; immutable packet preserved by tag `archive/rejected-figure-candidates-20260714` at `ba63448` |
| A1 trigger calibration | Campaign and controls completed as diagnostic-only evidence; artifacts consolidated by FLITS PR #174 (`91a5120`); no qualified CHIME measurement |
| Branch/worktree consolidation | Root checkout returned to clean `main`; consolidation and CHIME publication landed through Faber2026 PRs #39–#41 |
