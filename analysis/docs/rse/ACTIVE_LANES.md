# Active lanes

Owner-facing control surface for Faber2026 consolidation. One row per
workstream. Closed lanes move to the archive once their evidence is recorded.
Do not add narrative history here.

| Lane | Canonical repository/branch | Status | Next gate | Evidence | Worktree |
|---|---|---|---|---|---|
| Figure revalidation & replacement | `jakobtfaber/Faber2026` — new batch branches off `main` only | product selected; science and exact-byte approval pending | Freeze and revalidate the adopted-DM catalog, then render a new isolated `fig1-gallery` candidate under the locked data-only 4-by-3 contract | [Figure 1 and C1 decision](specs/decision-2026-07-14-figure1-and-chime-c1.md); merged PR #35 (gate); rejected packet archived at `archive/rejected-figure-candidates-20260714` | None; create a fresh isolated worktree for each new batch |
| CHIME C1 qualification | `jakobtfaber/dsa110-FLITS` — new experiment branch from `91a5120` or later verified `main` | design selected; implementation pending | Implement blinded `c1-allpairs-crossgp`; pass held-out nulls and every required `m=0.15` and `m=0.17` real-background recovery cell before unblinding | [Figure 1 and C1 decision](specs/decision-2026-07-14-figure1-and-chime-c1.md); [CHIME closeout handoff](specs/handoff-2026-07-14-chime-repair-and-figure-review-closeout.md) | None; create a clean isolated FLITS worktree |

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
