# Active lanes

Owner-facing control surface for Faber2026 consolidation. One row per
workstream. Closed lanes move to the archive once their evidence is recorded.
Do not add narrative history here.

| Lane | Canonical repository/branch | Status | Next gate | Evidence | Worktree |
|---|---|---|---|---|---|
| Figure revalidation & replacement | `jakobtfaber/Faber2026` — new batch branches off `main` only | decision pending | Owner picks the Figure 1 product (`fig1-gallery` vs triptych design) by stable candidate ID | Merged PR #35 (gate); rejected packet archived at `archive/rejected-figure-candidates-20260714`; [durable review contract](specs/handoff-2026-07-14-figure-review-and-replacement.md) | None; create a fresh isolated worktree for each new batch |

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
