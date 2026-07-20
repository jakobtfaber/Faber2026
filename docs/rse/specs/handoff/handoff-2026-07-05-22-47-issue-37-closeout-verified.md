# Handoff: FLITS issue #37 closeout — verified complete, repo clean

---
**Date:** 2026-07-05 22:47
**Author:** AI Assistant
**Status:** Handoff
**Branch:** `main` (parent Faber2026, even with `origin/main`)
**Commit:** `39cc335` (parent) · pipeline pin `13e1d00` (detached HEAD, == fork `origin/main`)

---

## Task(s)

This session consumed the Codex handoff `/tmp/faber2026-flits-issue37-handoff.md` (issue-37 closeout) and closed every remaining item. All work is **complete**; nothing is in flight.

| Task | Status | Notes |
|------|--------|-------|
| Verify handoff next-steps 1–5 (push, pin, fork branch cleanup) | ✅ Complete | All had already been done by a prior session; verified against live GitHub state rather than assumed. |
| Sort out `~/Developer/scratch/worktrees/flits-ponytail-audit-cleanup` | ✅ Complete | Classified stale (evidence below), removed via `git worktree remove`; freed local `main` fast-forwarded `9096a60` → `origin/main` (`13e1d00`). |
| Re-run `make` against new pin | ✅ Complete | `make clean && make` exit 0; no undefined refs/citations; warnings pre-existing (see Verification State). |

**Current Workflow Phase:** Validate (complete — no open implementation work)

## Verified closeout facts (issue #37)

- Upstream fix merged: `dsa110/dsa110-FLITS#43` (merge `c97177c`), closing `dsa110/dsa110-FLITS#37`. Fix commit `f8c9ffc` "Fix gain evidence baseline for single components".
- Fork route: fix ported onto fork main via `jakobtfaber/dsa110-FLITS#129` (`port/issue-37-gain-evidence`, merged, tip `13e1d00`). The submodule pins the **fork**, which is intentionally divergent from upstream — pinning `13e1d00` (not upstream `c97177c`) is the correct pointer.
- Parent pin bump `39cc335` changed only the `pipeline` gitlink (1 file, verified via `git show --stat`); pushed.
- Fork branches `fix-issue-37-evidence-kernel`, `auto-review-base/issue-37`, `port/issue-37-gain-evidence` all deleted — confirmed via GitHub branches API, not just local prune.
- `grit`: no active locks; `.grit/` ignored per `92c6488`.
- ICM memory stored: topic `context-Faber2026`, id `01KWTYTKHJ9W1EGYR86ERS6611`.

## Worktree removal evidence (flits-ponytail-audit-cleanup)

Removed autonomously on user instruction after staleness proof:

- Clean tree, zero untracked; `git cherry origin/main main` empty (0 unique commits, behind 40).
- `lsof +D` empty (no process, no cwd reference); worktree admin dir not locked.
- All file mtimes == checkout timestamp (2026-07-05 16:51) — created, never touched.
- Name matches `ponytail:ponytail-audit`, a one-shot report-only skill: expected to leave no commits.
- `lane-liveness` had returned `uncertain/unresolved_owner` — overridden only because the user explicitly authorized autonomous handling and the above signals were unanimous.

Siblings **preserved, uninventoried**: `flits-acf-lag-selector`, `flits-gate-preserve`, `flits-iso-preserve`, `flits-rerun` in `~/Developer/scratch/worktrees/` — out of this session's scope.

## Critical References

- `CLAUDE.md` (repo root) — pin semantics, build-done criteria, Overleaf manual-sync rule.
- `/tmp/faber2026-flits-issue37-handoff.md` — the consumed inbound handoff (context for what "issue-37 closeout" meant; may be tmp-cleaned).
- `pipeline/` @ `13e1d00` — the pinned commit every manuscript number must reproduce from.

## Recent Changes

- No file edits this session. Actions were: worktree removal + branch fast-forward (submodule housekeeping), and a clean rebuild (`main.pdf` regenerated, gitignored).

## Verification State / Known-Broken

- **Build:** `make clean && make` exit 0 at pin `13e1d00`; `main.pdf` 1.06 MB; **0** undefined references, **0** undefined citations.
- **Pre-existing warnings (not new):** 6 overfull hboxes — 5× one wide table alignment (97.7 pt over, `alignment at lines 57--57`), 1× math display (39.9 pt, log line 786) — plus 2 stuck-float warnings (input line 245). Pre-existing by construction: `39cc335` touched only the gitlink, so latexmk inputs are byte-identical to the last pre-bump build.
- **Uncommitted / unpushed:** this handoff file itself (untracked; siblings in `docs/rse/specs/` are committed — commit pending user go). Otherwise nothing: parent clean and even with origin; submodule clean at pin.
- **Tests:** none run this session (none applicable — no code changed; pipeline tests ran pre-merge per inbound handoff: focused joint-gain tests, ruff, 77 passed/1 skipped adjacent scattering, CI green on 3.10/3.12).

## Learnings

- The manuscript build does **not** execute pipeline code — latexmk consumes committed tex/figures/tables. A pin-only bump therefore cannot change build output; "rebuild against the new pin" is a regression check of repo-tree inputs, not of pipeline behavior.
- Submodule-pin semantics here: fork main (`jakobtfaber/dsa110-FLITS`) is the pin target; upstream fixes reach the manuscript via port-PRs onto the fork (e.g. #129), never by pointing the pin at upstream commits.
- `rtk git branch` in the submodule shows worktree-held branches with a `+` marker — quick way to spot stray worktrees holding `main`.
- `lane-liveness` returns `uncertain` when it cannot resolve an owner; unanimous secondary signals (lsof, mtimes, lock file, clean/cherry-empty) + explicit user authorization is the documented path past it.

## Action Items & Next Steps

No required work. Optional follow-ups, in priority order:

1. [ ] **Overleaf pull (user, UI-side):** GitHub `main` advanced (`92c6488`, `39cc335`); owner should pull via Overleaf GitHub Sync when convenient (sync is manual by design; git-bridge workflow disabled 2026-07-01).
2. [ ] Fix the 6 pre-existing overfull hboxes (one wide table + one display equation) if polishing for submission.
3. [ ] Inventory/triage the four remaining `flits-*` scratch worktrees (same staleness protocol as above).

**Recommended Next Skill:** none required — closeout is complete. If resuming manuscript work, start with `ai-research-workflows:using-research-workflows` to survey `docs/rse/specs/`.

## Other Notes

- Safety invariants that must survive future sessions: never reset/overwrite fork `main` (intentionally divergent, hundreds of commits ahead of upstream); keep parent commits separate from pipeline source commits; `.grit/` stays ignored, never committed; pushes to parent `main` are outward-facing (Overleaf pulls it).
- Two prior unrelated handoffs exist in `docs/rse/specs/` (freya-chime lanes, 2026-07-04/05) — separate lanes, untouched by this session.

---

**Handoff created by AI Assistant on 2026-07-05**
