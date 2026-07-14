# Active lanes

Owner-facing control surface for Faber2026 consolidation. One row per
workstream. Closed lanes move to the archive once their evidence is recorded.
Do not add narrative history here.

| Lane | Canonical repository/branch | Status | Next gate | Evidence | Worktree |
|---|---|---|---|---|---|
| Figure revalidation & replacement | `jakobtfaber/Faber2026` — new batch branches off `main` only | decision pending | Owner picks the Figure 1 product (`fig1-gallery` vs triptych design) by stable candidate ID | Merged PR #35 (gate); open draft PR #36 (rejected packet, never merge); open PR #37 (review handoff) | `Faber2026-figure-candidates` (clean, review-only) |
| A1 trigger calibration | `jakobtfaber/dsa110-FLITS` `a1/trigger-calibration` | active | Complete the injection campaign, diagnostic controls, calibration report, and owner operating-point sign-off; merge only at that scientific gate | Branch `1e58c96`, based on post-P0 `main`; 20 focused + 235 full tests pass | `flits-a1-trigger-calibration` |
| Branch/worktree consolidation | `jakobtfaber/Faber2026` root checkout | blocked | Live Claude process releases the root; then verify the published overlay, switch to current `main`, and retire `ms/validated-fit-figure-refresh-20260714` | Merged PR #39; integrated-lane range-diff proof in the Phase 1 closure handoff | root checkout (live; do not switch or clean) |

## Archive

| Lane | Closure evidence |
|---|---|
| P0 provenance freeze | FLITS PR #170 merged (`82fc7ec`); tree-identical to independently validated post-`788b819` integration; 11 focused, 230 FLITS, and 54 parent tests passed |
| FLITS figure-branch integration (pin chain) | FLITS PR #173 merged (`788b819`); Faber2026 pin-only PR #38 merged (`251d634`); pin verified reachable from FLITS `main` |
| Figure approval gate implementation | Merged PR #35 (`af06269`, v4 lane); v1–v3 worktrees are preserved dirty experiments, not authoritative |
| July replacement figure refresh | Merged PR #34; figures subsequently rejected by owner and withheld by PR #35 |
