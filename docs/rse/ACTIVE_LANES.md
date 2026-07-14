# Active lanes

Owner-facing control surface for Faber2026 consolidation. One row per
workstream. Closed lanes move to the archive once their evidence is recorded.
Do not add narrative history here.

| Lane | Canonical repository/branch | Status | Next gate | Evidence | Worktree |
|---|---|---|---|---|---|
| Figure revalidation & replacement | `jakobtfaber/Faber2026` — new batch branches off `main` only | decision pending | Owner picks the Figure 1 product (`fig1-gallery` vs triptych design) by stable candidate ID | Merged PR #35 (gate); open draft PR #36 (rejected packet, never merge); open PR #37 (review handoff) | `Faber2026-figure-candidates` (clean, review-only) |
| P0 provenance freeze | `jakobtfaber/dsa110-FLITS` `reval/p0-provenance` | active — writer/CI in progress | Existing writer finishes CI and explicitly releases the lane; then independent validation and merge adjudication | FLITS PR #170 at `3673457` (2026-07-14 14:27 PDT); checks in progress at last inspection | `flits-p0-provenance-repair` (clean at pushed head; do not touch until released) |
| A1 trigger calibration | `jakobtfaber/dsa110-FLITS` `a1/trigger-calibration` | active (parked) | Confirm ancestry against current FLITS `main`; resume after P0 closure; merge only at scientific completion gate | Consolidation handoff Phase 4 | none expected |
| Branch/worktree consolidation | `jakobtfaber/Faber2026` `docs/consolidation-active-lanes-20260714` | active | Land focused docs PR; then prune only lanes with recorded equivalence proof | `docs/rse/specs/handoff-2026-07-14-branch-consolidation-and-next-actions.md` | `Faber2026-consolidation-docs-codex` |

## Archive

| Lane | Closure evidence |
|---|---|
| FLITS figure-branch integration (pin chain) | FLITS PR #173 merged (`788b819`); Faber2026 pin-only PR #38 merged (`251d634`); pin verified reachable from FLITS `main` |
| Figure approval gate implementation | Merged PR #35 (`af06269`, v4 lane); v1–v3 worktrees are preserved dirty experiments, not authoritative |
| July replacement figure refresh | Merged PR #34; figures subsequently rejected by owner and withheld by PR #35 |
