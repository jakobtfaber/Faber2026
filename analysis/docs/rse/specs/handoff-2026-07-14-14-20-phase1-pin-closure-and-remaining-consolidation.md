# Handoff: Phase 1 pin-chain closure; remaining consolidation state

---
**Date:** 2026-07-14 14:20
**Author:** Claude Code (Fable 5)
**Status:** Handoff
**Branch (root checkout):** `ms/validated-fit-figure-refresh-20260714` at `0c931ff` (superseded; deliberately untouched — see Dirty-state boundary)
**Faber2026 `origin/main`:** `251d634` (merged PR #38)
**FLITS fork `origin/main`:** `788b819` (merged PR #173)

---

## Task(s)

This session picked up `handoff-2026-07-14-branch-consolidation-and-next-actions.md` and executed its ordered plan as far as the one-way doors allowed.

| Task | Status | Notes |
|------|--------|-------|
| Verify consolidation-handoff state against live repos | ✅ Complete | Two supersessions found (see Learnings) |
| Phase 1: land FLITS figure branch on FLITS `main` | ✅ Complete | FLITS PR [#173](https://github.com/jakobtfaber/dsa110-FLITS/pull/173) merged as `788b819` (merge commit; tree byte-identical to old pin `67bdd014`) |
| Phase 1: move parent pin via focused pin-only PR | ✅ Complete | Faber2026 PR [#38](https://github.com/jakobtfaber/Faber2026/pull/38) merged as `251d634`; verified `merge-base --is-ancestor`: pin reachable from FLITS `main` |
| Phase 2: figure-approval consolidation | ✅ Superseded/complete | Closed by merged PR #35 (gate, v4 lane) before this session; v1–v3 dirty worktrees remain "preserve, do not use" |
| Phase 3: P0 provenance PR #170 | 🔄 Blocked (separate-active) | In-flight writer state found in `flits-p0-provenance-repair` — do not touch (see Verification State) |
| Phase 4: A1 `a1/trigger-calibration` | 📋 Parked | Unchanged; 6 ahead / 0 behind FLITS `main` at inspection (pre-#173) |
| Phase 5: prune proven-integrated lanes | 📋 Planned | Only this session's own two landing worktrees were removed (both fully merged); everything else preserved |
| Phase 6: `docs/rse/ACTIVE_LANES.md` | 📋 Drafted | Ready-to-commit draft embedded below in Other Notes |

**Current Workflow Phase:** Validate → next session continues consolidation closures (Phases 3, 5, 6)

## Workflow Artifacts

- `docs/rse/specs/handoff-2026-07-14-branch-consolidation-and-next-actions.md` — the master consolidation plan this session executed (still untracked in the root checkout; carry it to an intentional lane, Phase 5 step 4)
- `docs/rse/specs/handoff-2026-07-14-figure-review-and-replacement.md` — figure-review/rejection handoff; committed on branch `docs/figure-review-handoff-20260714`, open PR [#37](https://github.com/jakobtfaber/Faber2026/pull/37) (separate live lane — do not duplicate its work)
- `docs/rse/journal.jsonl` — three new entries this session (lane `branch-consolidation`: working, done) on top of one pre-existing dirty line

## Critical References

1. `docs/rse/specs/handoff-2026-07-14-branch-consolidation-and-next-actions.md` — the ordered plan; Phases 3/5/6 remain
2. `docs/rse/specs/handoff-2026-07-14-figure-review-and-replacement.md` (read from PR #37's branch if the local worktree is gone) — governs everything figure-related; owner decisions still pending
3. This document — supersessions and the P0 lane blocker

## Recent Changes

All published changes went through PRs; no source files were edited in place.

- FLITS fork `main`: PR #173 merged `fix/dm-locked-joint-figures-v2` (15 commits: DM-locked joint-fit campaign, scintillation fit freeze, Oran qualification; `scattering/scat_analysis/burstfit_joint.py` + analysis artifacts)
- Faber2026 `main`: PR #38, single gitlink-only commit `8fbd83e` (`pipeline` `67bdd014` → `788b8196`, tree byte-identical)
- `docs/rse/journal.jsonl` (root checkout, uncommitted): appended lane `branch-consolidation` entries

## Verification State / Known-Broken

- **Tests (all green, this session):**
  - 19 focused FLITS tests at `67bdd01` in a clean worktree (`test_fit_adjudication.py`, `test_driver_guards.py`, `test_oran_dsa_measurement.py`, `test_burstfit_joint_gain.py`) — matches PR #34's recorded evidence
  - FLITS PR #173 CI: 4/4 checks passed
  - Pin PR #38: `make test-science` 54 passed + 1 documented xfail (class-aware association lane not re-landed — explicit owner decision); `figure_review.py verify` ok; journal-append test ok; `latexmk` 31-page build; CI green
- **BLOCKER — P0 lane is separate-active, not clean:** worktree `~/Developer/scratch/worktrees/flits-p0-provenance-repair` (branch `reval/p0-provenance`, PR [#170](https://github.com/jakobtfaber/dsa110-FLITS/pull/170)) has an **unpushed commit** `dad9786` ("feat(reland): restore scint/DM analysis lane onto rewritten main") plus 8 dirty paths (adjudication scripts, `tests/test_adjudication_imports.py`, `tests/test_fit_generations.py`, `.gitignore`, `analysis/fit_generations.yaml`, untracked `galaxies/foreground/data/frozen_census/`). `lane-liveness` verdict: `uncertain` (recent edits). The 2026-07-14 consolidation handoff recorded this branch as clean, so a writer has been active since. **Do not merge main into the branch, push, or merge PR #170 until this writer's state is resolved (identify writer → let it finish or adopt its state deliberately).**
- **Uncommitted / unpushed (root checkout, preserved deliberately):** modified `docs/rse/journal.jsonl` (1 pre-existing + 3 session lines; working copy is a strict superset of `origin/main`'s — carry is a clean 4-line append), modified `docs/rse/board/readiness.html` (protocol rebake after journaling; board already deployed to gh-pages), and untracked consolidation handoff + this handoff. Root stays on the superseded branch until these are carried to an intentional lane (Phase 5 step 4).
- **Unverified:** none introduced. The rejected July figures remain `needs_revision` (draft PR #36); nothing in this session approves or promotes any figure.

## Learnings

- **Two supersessions of the consolidation handoff, verified live:** (1) Faber2026 PR #35 merged the figure-approval gate (v4 lane, `af06269`) — Phase 2's "one implementation on main" is already satisfied; v1–v3 dirty worktrees are now formally "preserve, do not use". (2) The owner **rejected** the July replacement figures; draft PR #36 freezes all 39 candidates as `needs_revision` and `main` compiles placeholders. Figure work is owner-decision-gated (Figure 1 product choice first), not agent-executable.
- **Merge-commit strategy made the pin move trivial:** FLITS `main` was an ancestor of the figure branch, so merging produced `788b819` with a tree byte-identical to `67bdd014` (`git diff 67bdd014 788b8196` empty). The pin-only PR was therefore provably manuscript-neutral.
- **A third live agent lane exists:** PR #37 (figure-review handoff docs) appeared mid-session; its worktree `Faber2026-figure-review-handoff` shows the doc untracked locally but committed on its remote branch. Expect concurrent writers on this repo today; re-fetch and re-check PR lists before every shared-ref action.
- `scripts/journal-append.sh` is not executable — invoke with `bash scripts/journal-append.sh <agent> <lane> <state> <note>`.
- The FLITS `entire` checkpoint hook emits a harmless `fetch failed: '0'` warning on worktree operations (misconfigured sync remote); ignore it.
- Local test recipe that matches CI: focused pytest via `env -i HOME="$HOME" PATH="/opt/anaconda3/bin:/opt/homebrew/bin:/usr/bin:/bin" /opt/anaconda3/bin/conda run -n flits python -m pytest …`; parent-side `make test-science` uses `uv run --project pipeline --frozen`.

## Action Items & Next Steps

1. [ ] **Resolve the P0 lane writer** (`flits-p0-provenance-repair`): identify who owns commit `dad9786` + the dirty adjudication/test edits (journal, agent handoffs, `lane-liveness` again). Only when quiescent and adopted/pushed deliberately: bring FLITS `main` (now `788b819`) into `reval/p0-provenance` non-destructively, rerun the provenance / frozen-census / fit-generation / budget-parity checks named in PR #170, merge. Budget-table parity spans both repos (memory: `budget-table-parity-spans-two-repos`).
2. [ ] **Carry the root dirt to an intentional lane** (Phase 5 step 4): one focused docs PR off `main` with (a) the 4 appended journal lines, (b) `handoff-2026-07-14-branch-consolidation-and-next-actions.md`, (c) this handoff, (d) the rebaked `docs/rse/board/readiness.html`, (e) `docs/rse/ACTIVE_LANES.md` from the draft below (update P0/pin rows to current state first). Then switch the root checkout to `main` and retire `ms/validated-fit-figure-refresh-20260714` (its unique commit `0c931ff` restored figures the owner later rejected — record supersession by PRs #34+#35 as the proof).
3. [ ] **Phase 5 pruning with recorded proof:** prune the missing `/private/tmp/faber2026-refresh/parent-merge` registration; remove clean proven-integrated worktrees/branches (`ms/pin-flits-171-20260714`, `ms/qualified-oran-scintillation-20260714`, `agent/reland-state-sync-20260714`) using range-diff/patch-equivalence (repo squash-merges — `git cherry` lies here; memory: `branch-staleness-needs-range-diff-not-cherry`). Preserve: `ci/root-science-tests` (2 unique commits), v1–v3 approval worktrees (dirty), `Faber2026-figure-candidates` (draft PR #36), `Faber2026-figure-review-handoff` (PR #37 lane), all `overleaf-*` branches, FLITS `scint/*` evidence lanes.
4. [ ] **A1 campaign** (`a1/trigger-calibration`): confirm still 0 behind the new FLITS `main` `788b819` before resuming; single worktree; merge only at its scientific gate.
5. [ ] Figure revalidation remains **owner-gated**: first decision is the Figure 1 product (`fig1-gallery` vs triptych) by stable candidate ID, per the figure-review handoff. No agent may promote figures without per-candidate owner approval + receipts.

**Recommended Next Skill:** `ai-research-workflows:validating-implementations` for the P0 PR #170 closure once its lane is quiescent; `ai-research-workflows:using-research-workflows` to re-survey `docs/rse/specs/` on session start.

## Other Notes

**Landing worktrees from this session were removed after merge** (proof: PRs #173/#38 merged; local branches deleted with `git branch -d`, which verified ancestry): `flits-dm-locked-landing`, `Faber2026-pin-landing`.

**Ready-to-commit `docs/rse/ACTIVE_LANES.md` draft** (update statuses at commit time — pin lane is now CLOSED, move to archive):

```markdown
# Active lanes

Owner-facing control surface (branch-consolidation handoff, Phase 6). One row
per workstream. Closed lanes move to the archive section once their evidence
link is recorded. Do not add narrative history here.

| Lane | Canonical repository/branch | Status | Next gate | Evidence | Worktree |
|---|---|---|---|---|---|
| Figure revalidation & replacement | `jakobtfaber/Faber2026` — new batch branches off `main` only | decision pending | Owner picks the Figure 1 product (`fig1-gallery` vs triptych design) by stable candidate ID | Merged PR #35 (gate); draft PR #36 (rejected packet, never merge); `docs/rse/specs/handoff-2026-07-14-figure-review-and-replacement.md` | `Faber2026-figure-candidates` (clean, review-only) |
| P0 provenance freeze | `jakobtfaber/dsa110-FLITS` `reval/p0-provenance` | blocked | In-flight writer state resolved: unpushed reland commit `dad9786` + dirty adjudication/test files | FLITS PR #170 | `flits-p0-provenance-repair` (dirty — do not touch) |
| A1 trigger calibration | `jakobtfaber/dsa110-FLITS` `a1/trigger-calibration` | active (parked) | Resume after P0 closure; merge only at scientific completion gate | Consolidation handoff Phase 4 | none expected |
| Branch/worktree consolidation | `jakobtfaber/Faber2026` docs lane | active | Phase 5 pruning with recorded proof; root checkout returned to `main` | `docs/rse/specs/handoff-2026-07-14-branch-consolidation-and-next-actions.md` | root checkout (transitional) |

## Archive

| Lane | Closure evidence |
|---|---|
| FLITS figure-branch integration (pin chain) | FLITS PR #173 merged (`788b819`); Faber2026 pin-only PR #38 merged (`251d634`); pin verified reachable from FLITS `main` |
| Figure approval gate implementation | Merged PR #35 (`af06269`, v4 lane); v1–v3 worktrees are preserved dirty experiments, not authoritative |
| July replacement figure refresh | Merged PR #34; figures subsequently rejected by owner and withheld by PR #35 |
```

### Dirty-state boundary (unchanged from the consolidation handoff)

Root `docs/rse/journal.jsonl` + the two untracked handoff docs are the only root dirt; preserved. The three `figure-approval` worktrees (126/11/100 dirty paths) were not touched. The `Faber2026-figure-review-handoff` worktree's untracked doc is PR #37's lane — not ours. No branch, remote branch, or dirty worktree was deleted; the only removals were this session's own two fully-merged landing worktrees.

---

**Handoff created by Claude Code (Fable 5) on 2026-07-14**
