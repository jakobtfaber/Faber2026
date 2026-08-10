# Handoff: Finish Faber2026 manuscript/analysis repository split

---
**Date:** 2026-07-21 21:49 PDT
**Author:** AI Assistant
**Status:** Handoff
**Parent branch:** `codex/faber2026-analysis-split` at `f63fd066`
**Analysis branch:** `codex/analysis-mount-integration` at `84da698`

---

## Task(s)

Split the large research/control surface out of `Faber2026` into the public
`Faber2026-analysis` repository, mount it at `analysis/` beside the existing
`pipeline/` submodule, and retain GitHub Sync for the existing Overleaf project.

| Task | Status | Notes |
|------|--------|-------|
| Inventory and define manuscript projection | Complete | Research and plan written; exact allowlist and fail-closed boundary test added. |
| Extract and publish analysis history | Complete | Public remote `main` exists at `520f4c4`; filtered history and sample history were validated. |
| Make analysis tools work when mounted | Complete locally | Two clean, unpushed commits: `541a467` and `84da698`. Full mounted suite passed. |
| Reduce parent to manuscript projection | In progress | Removal batches and initial gitlink are committed; 21 task-owned interface files plus the new analysis pin remain uncommitted. |
| Validate split | Mostly complete | Boundary, scientific tests, clean 37-page compile, and compile-closure checks passed. Knowledge-base indexing and closeout remain. |
| Publish and test Overleaf | Planned | Push analysis first, then parent; open focused pull request; live Overleaf import/recompile remains owner-visible validation. |

**Current Workflow Phase:** Implement, approaching Validate

## Workflow Artifacts

**Research Documents:**

- [research-faber2026-analysis-split.md](research-faber2026-analysis-split.md) — repository boundary, compile closure, size inventory, and extraction strategy.

**Plan Documents:**

- [plan-faber2026-analysis-split.md](plan-faber2026-analysis-split.md) — active four-phase implementation plan. Phases 1–2 are checked; Phase 3 is implemented but not yet checked/committed; Phase 4 is partly verified.

No experiment report, implementation summary, or validation report has yet been
created. The implementation skill expects an
`implement-faber2026-analysis-split.md` before final validation.

## Critical References

Read these first:

- `docs/rse/specs/plan-faber2026-analysis-split.md:67-169` — authoritative remaining phases, success criteria, and manual Overleaf gate.
- `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-split/manuscript-boundary.txt:1-62` — exact files permitted in the parent manuscript repository.
- `scripts/workspace.py:1-24` — mounted-workspace resolver used by rebased analysis tools; accepts `FABER2026_ROOT` and otherwise expects this repository at `Faber2026/analysis`.

## Repository Locations and Git State

### Parent manuscript repository

- Worktree to resume: `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-split`
- Branch: `codex/faber2026-analysis-split`
- HEAD: `f63fd066` (`chore: add Faber2026 analysis submodule`)
- Base/remote: `origin/main` at `a995f372`; branch is 18 commits ahead.
- The branch is not present on `origin` as of this handoff.
- Committed work includes the boundary plan/test, analysis gitlink, and 1,276 removals split into fifteen commits of at most 90 paths each (`df3024e` through `dd09051`).
- Current mounted pins: `analysis` at `84da698`; `pipeline` at `ab6af1f713496abd2ff2d71bf11edf4100871e94`.

The parent has 21 modified task-owned paths and no unrelated dirt:

- Interface/config: `.github/workflows/table-parity.yml`, `.gitignore`, `.olignore`, `AGENTS.md`, `CLAUDE.md`, `Makefile`, `README.md`, and gitlink `analysis`.
- Figure interface: `figures/ax/SKILL.md`, `figures/ax/agent.py`, `figures/catalog.yaml`.
- Manuscript/provenance wording: `main.tex`, three generated root tables, `sample_table.tex`, `twoscreen_provisional_table.tex`, and five section files.

The diff is 123 insertions and 167 deletions. It is all part of this migration;
do not discard it. `GEMINI.md` is unchanged and was not found to need path edits.

### Analysis repository

- Canonical checkout: `/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026-analysis`
- Branch: `codex/analysis-mount-integration`
- HEAD: `84da698`
- Remote `main`: `520f4c4198014015efb6717756985290f4462b3a`
- Branch is two commits ahead of `origin/main` and is not present on `origin`.
- Before this handoff document was created, the checkout was clean. This handoff file is now the only expected uncommitted path.

## Recent Changes

### Parent

- `Makefile:1-56` — keeps LaTeX build in the parent and delegates state checks, scientific tests, figure flow, knowledge base, Running Notes, and Wayfinder through `analysis/`.
- `tests/test_manuscript_boundary.py:1-80` — exact allowlist, two-gitlink, 7 MB editable-text, and 100 MB total-tree gates.
- `.gitmodules:1-6` — sibling HTTPS submodules `pipeline/` and `analysis/`.
- `figures/catalog.yaml` and `figures/ax/` — producer/review paths rebased through `analysis/`; final manuscript figure assets stay in the parent.
- `main.tex` and retained tables/sections — repository-location wording updated without changing scientific values.

### Analysis

- `scripts/workspace.py:1-24` — separates `ANALYSIS_ROOT` from the mounted manuscript root.
- `Makefile:8-32` — checks the mount and runs tests through the exact sibling `pipeline` pin with `uv --frozen --group test`.
- `scripts/figure_review.py:25-31,449-467` — keeps review state in analysis while checking only TeX reachable from parent `main.tex`; inactive draft sections no longer create false approval failures.
- `scripts/sync_state.py:42-50,79-86` — control documents remain analysis-owned while manuscript labels are read from the parent.
- Figure, budget, consistency, campaign, and DM scripts plus their tests were rebased to distinguish analysis-owned inputs from parent manuscript outputs and the sibling pipeline.

## Reproducibility & Data State

- **Seeds:** No new scientific experiment was run and no scientific seed changed. Existing deterministic seeds remain in the preserved scripts.
- **Environment:** Tests used `uv run --project pipeline --group test --frozen`; lockfile is parent `pipeline/uv.lock` at pipeline pin `ab6af1f7`. An inherited `VIRTUAL_ENV` can make `uv` select the wrong interpreter; use `env -u VIRTUAL_ENV` for the validation command.
- **Data:** No scientific datasets or values were changed. Local full-resolution data locations remain outside the repositories. This migration changes repository ownership and paths only.
- **Build artifact:** `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-split/main.pdf` is 37 pages; SHA-256 `806fc47ac58810b8ca3fc5ff1a29434d67efe306da3e0222079b495f164f79d9`.
- **Partial results / checkpoints:** None beyond the two worktrees and commits above.
- **In-flight jobs:** None. The interrupted `make kb-index` process was terminated before the computer restart; process inspection found no remaining indexer.

## Verification State / Known-Broken

> **Known-broken / unverified:** The local implementation is not published or
> merged. Live Overleaf GitHub Sync has not imported this split. The knowledge
> base rebuild was intentionally interrupted after several minutes with no
> output. Closeout checks, fresh recursive-clone validation, implementation
> summary, final validation report, and live Overleaf recompile remain undone.

- **Mounted scientific suite:** Passed — `222 passed, 1 xfailed` in 36.61 s. The expected failure is the pre-existing class-aware association lane decision; it is not caused by this split.
- **Figure approval gate:** Passed — `figure approval gate: ok`.
- **State drift gate:** Passed — all 3 generated views matched and lane/ledger rules passed offline.
- **Journal append shell test:** Passed as part of `make test-science`.
- **Parent boundary:** Passed — `3 passed`; both entries are mode `160000` when tested against the prepared index/tree contract.
- **Clean LaTeX integration:** Passed — 37 pages, 8,848,845-byte PDF, zero recorder inputs under `analysis/` or `pipeline/`.
- **Analysis extraction checks:** Earlier passed — selected hash comparisons, sample `git log --follow`, and `git fsck --full` at extraction commit `520f4c4`.
- **Knowledge base:** `make kb-index` was stopped at the user's request before restart. It had run for about four minutes without emitting output. No completion claim.
- **Uncommitted:** Parent 21-path interface/pin diff; analysis handoff file only.
- **Unpushed:** Analysis commits `541a467`, `84da698`; all 18 parent branch commits and the parent interface work.
- **PR #172:** Still open (`codex/overleaf-manuscript-bridge-map` → `main`), titled “Chart manuscript-only Overleaf bridge.” It should be closed as superseded only after the replacement parent pull request exists; do not delete its branch.
- **Manual gate:** Overleaf GitHub Sync pull and Overleaf 37-page recompile have not been attempted.

## Learnings

- The Overleaf error was caused by the repository boundary, not the manuscript closure: compile-required editable files are far below 7 MB, while research/control material dominated the parent.
- Overleaf already tolerates the existing unexpanded `pipeline` gitlink. The selected design keeps GitHub Sync and adds a second unexpanded `analysis` gitlink; Overleaf does not need to initialize either submodule.
- Moving scripts one directory deeper broke the old single-root assumption. Mounted tools require separate analysis, manuscript, and pipeline roots; `scripts/workspace.py` is the shared contract.
- The original figure approval check scanned every draft section. After noncompiled figure assets moved out, that produced false failures. It now follows the TeX graph reachable from `main.tex`.
- The parent test reads Git's index with `git ls-files --stage`, so membership/pin checks should be run after staging the intended parent interface when validating the final commit.
- `uv run --project pipeline --frozen` did not install the test dependency group. The working command includes `--group test` and clears inherited `VIRTUAL_ENV` when necessary.
- Initializing the `pipeline` submodule in the migration worktree was required before mounted tests could run.
- The parent removal history is intentionally split into sub-100-path commits to reduce GitHub Sync transaction risk. Do not squash those commits before the live sync test unless there is a concrete reason.

## Action Items & Next Steps

1. [ ] Resume in `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-analysis-split`; confirm parent dirt and both submodule pins before editing.
2. [ ] In the analysis repository, add this handoff to the task-scoped changes, create `docs/rse/specs/implement-faber2026-analysis-split.md`, and finish/check the plan only as each gate truly completes.
3. [ ] Diagnose or rerun `make kb-index`; do not wait indefinitely without inspecting its process/output. Record whether it passes or remains a named blocker.
4. [ ] Run `git fsck --full` in both repositories and make a fresh clone with `--recurse-submodules` after the analysis integration branch is remotely available.
5. [ ] Run `agent-closeout-check` for both repositories with explicit touched paths and dirty-state packets, as required by `AGENTS.md`.
6. [ ] Commit the analysis handoff/remaining documentation, push `codex/analysis-mount-integration`, open a focused pull request to analysis `main`, verify checks, and merge it without rewriting history.
7. [ ] Update the parent `analysis` gitlink to the merged analysis `main` commit if it changed; inspect/stage the exact 21 parent paths; rerun boundary, mounted science, and clean LaTeX checks; commit.
8. [ ] Push `codex/faber2026-analysis-split`, open the parent pull request, verify checks and diff scope, then close PR #172 as superseded without deleting its branch.
9. [ ] Merge only after checks are green and the intended commit structure is preserved.
10. [ ] Use the existing Overleaf GitHub Sync integration to import the merged parent, recompile, and confirm the expected 37-page manuscript. This is the final manual gate.

**Recommended Next Skill:** `ai-research-workflows:implementing-plans` to finish
the remaining implementation/publish tasks, followed by
`ai-research-workflows:validating-implementations` before merge and Overleaf
verification.

## Other Notes

- The existing Overleaf project identity should be preserved. History/comments were explicitly not migration requirements.
- Do not switch back to the abandoned native-Git bridge design unless the two-gitlink GitHub Sync test fails and the owner chooses that fallback.
- Do not modify or bump `pipeline/` as a side effect. Its pin is deliberate.
- The canonical parent checkout is not the active implementation location; use the dedicated worktree named above.

---

**Handoff created by AI Assistant on 2026-07-21 21:49 PDT**
