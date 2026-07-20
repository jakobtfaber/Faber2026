# Handoff: reproducibility-spine commit stranded on local `main`; iTerm Diff-pane root-caused (fix staged, not yet in effect)

---
**Date:** 2026-07-09 01:45
**Author:** AI Assistant
**Status:** SUPERSEDED 2026-07-09 03:0x — see the update block below before acting on anything here
**Branch:** `ms/appendix-c-sync-pr40`
**Commit:** `35abbbd`

---

> ## Update (2026-07-09, later the same session) — most of this document is now history
>
> Everything below was true when written. Three things have since changed, and
> acting on the original text would now be wrong:
>
> 1. **The spine commit landed.** `681cfe2` (rebased successor of `4a00aa0`) was
>    cherry-picked and merged via **PR #46** (squash `f7fcbb2`). Nothing is
>    stranded. `4a00aa0` survives only on `backup/main-pre-rebase-20260708`.
>
> 2. **The parity tests were NOT green, and then were.** Re-running them at pin
>    `f9e1c24` gave 8 passed / 1 failed — all 9 non-placeholder sightlines
>    mismatched. Cause: `budget_table_data.json` in the submodule predated PR #40
>    and #42, which rewrote `scripts/dm_budget_uncertainty.csv`. **PR #48** fixed
>    it by bumping the pin to `c69d043`. Parity is now 9/9 green and regenerating
>    `budget_table.tex` reproduces it byte-for-byte. PR #46 briefly carried a
>    "DO NOT REGENERATE" warning that was already stale at merge; **PR #51**
>    reversed it. `REPRODUCE.md` hazard 1 now records the real, durable lesson:
>    that test reads a super-repo CSV from a submodule test, so its verdict
>    belongs to the (super-repo commit, pin) *pair*.
>
> 3. **`data/` and the handoff tracking were settled by someone else.** PR #43
>    tracked these handoff docs and added `/data/` to `.gitignore`.
>
> Also corrected: the negative DM_host medians for FRB 20220310F and
> FRB 20221203A are **intentional** (posteriors consistent with zero,
> `P(DM_host<0)≈0.5`, explained in `budget_table.tex`'s `\tablecomments`). An
> earlier version of this session called them unphysical. Do not censor them.
>
> **Still open, and still cannot be done by an agent:** the iTerm Diff-pane fix
> (item 3 below). It needs iTerm2 quit, which kills every Claude session running
> under it. Prefs are already written correctly; see `~/bin/iterm-claude-diff-pane`.

---

## Task(s)

Two threads. The first was a two-part landing of the table-emitter work (submodule fixtures, then the manuscript-side spine update). The second started as an obstacle to the first — a stray editor holding `REPRODUCE.md` — and turned into root-causing a machine-wide `git difftool` process leak.

| Task | Status | Notes |
|------|--------|-------|
| Part 1 — commit `exports/` regression fixtures in `dsa110-FLITS` | ✅ Complete | `e0039c6`, pushed; verified with `git ls-remote`, now contained in `f9e1c24` |
| Part 2 — manuscript spine (`REPRODUCE.md`, `repro_manifest.csv`) | 🔄 Committed, **unpushed** | `681cfe2` on local `main`, `ahead=1` of `origin/main`. **Not in PR #41.** |
| Part 2 — `pipeline` gitlink bump | ✅ Moot | Landed upstream independently via `eeca832` (#37); recipe was overtaken mid-session |
| Root-cause stray `vimdiff` on `REPRODUCE.md` | ✅ Complete | iTerm2's builtin Claude Code workgroup, not Claude Code and not a user script |
| Disable the iTerm Diff pane | ⚠️ Written, **not in effect** | Prefs correct on disk + cfprefsd; running iTerm still serves cached old prefs |

**Current Workflow Phase:** Validate (implementation landed; verification and a landing decision remain)

## Workflow Artifacts

**Handoff Documents (this repo, `docs/rse/specs/`):**
- `handoff-2026-07-08-22-49-flits-pipeline-commits-and-repo-state.md` — covers the emitter commits and live-lane repo state. **Untracked.** Cites `4a00aa0` (see correction below).
- `handoff-2026-07-08-18-42-submodule-roundtrip-figure-refresh.md` — submodule round-trip / figure refresh. **Untracked.** Also cites `4a00aa0`.
- `handoff-2026-07-08-18-12-b7-cgm-census-resolved.md` — B7 CGM-census closure, written by the concurrent session whose rebase collided with this work.

**External memory note (different repo, not in this tree):**
- `dotfiles/memory/reference_iterm-claude-code-diff-pane.md` — full mechanism + fix for the Diff-pane leak, indexed in `dotfiles/memory/MEMORY.md`. Uncommitted; the S-009 snapshot job owns `memory/`.

## Critical References

- **`git show 681cfe2`** — the unpushed spine commit. Nothing else in the repo tells you it exists; it is reachable only from local `main`.
- `REPRODUCE.md` @ `681cfe2` — `## Regenerating the tables` (line 75) is the new section; `## Caveats and hazards` (line 112) flips hazards 1 and 2 to `RESOLVED 2026-07-08` (lines 114, 130).
- `pipeline/galaxies/foreground/` — `budget_table_emitter.py`, `foreground_table_emitter.py`, their `*_data.json` single-source inputs, and `test_*_table_emitter.py`. The tests are the substantive guarantee; the `exports/` fixtures are only the byte-exact anchor.

## Recent Changes

**Submodule `pipeline` (dsa110-FLITS), branch `agent/sightline-halo-grid-figure`:**
- `e0039c6` — adds `exports/budget_table.tex` and `exports/foreground_table.tex` (134 insertions, two files, nothing else). These are the regression fixtures the committed parity tests assert exist; without them a fresh clone failed 2 tests.
- Committed with an explicit pathspec, **not** `git add` + bare `git commit`. The submodule index already held a staged hunk in `crossmatching/plot_association_cards.py` (+6/−1) belonging to another lane; a bare commit would have swept it in. The original recipe for this task had that bug.

**Super-repo, local `main` only:**
- `681cfe2` (`docs: update reproducibility spine for generated budget/foreground tables`) — `REPRODUCE.md` (+71/−33) and `repro_manifest.csv`. Retires the `hand` writer status, documents the emitter regeneration path and the parity-test guarantees, and marks both former reproducibility hazards resolved.

## Reproducibility & Data State

- **Environment:** `pipeline/uv.lock` (currently modified in the working tree by a separate lane — do not assume the committed lock is what ran).
- **Tests:** `test_budget_table_emitter.py` + `test_foreground_table_emitter.py` → **9 passed**, run against submodule `386e886` + fixtures immediately before `e0039c6`. **Not re-run since**, and the submodule tree has since moved to `f9e1c24` and accumulated unrelated modifications. Treat the 9-passed result as stale evidence, not current status.
- **Emitter parity:** both `--check` invocations returned `OK: emitter matches …/exports/<table>.tex` at commit time.
- **Data:** untracked `data/` at repo root (`dsa110_frb_catalog.csv`, `_README.md`, `_overview.pdf`, `_overview.png`, created 2026-07-08 22:26). **Not gitignored**, so it shows as untracked. `~/Data/Faber2026/` exists and is the canonical home for research data under the machine's conventions — this directory looks misplaced, but it is not this task's lane. Decision pending; do not commit or move it without confirming ownership.
- **In-flight jobs:** none from this session.

## Verification State / Known-Broken

- **Unpushed:** `681cfe2` on local `main` (`behind=0 ahead=1`). The checked-out branch `ms/appendix-c-sync-pr40` (PR #41, open) is based on `64158aa` and **does not contain it**. `origin/main:REPRODUCE.md` still has no `## Regenerating the tables` section — the spine update is not visible to anyone but this machine.
- **Prior handoffs cite a dangling SHA.** The 18:42 and 22:49 handoffs both reference `4a00aa0` for this commit. That SHA was rebased away at 23:01 and is on **no live branch**; the live commit is `681cfe2`. `4a00aa0` survives only on `backup/main-pre-rebase-20260708`. Anyone following those handoffs will chase a commit that appears orphaned.
- **iTerm fix is written but inert.** `Workgroups` and the profile trigger both read `custom.claudeCodeNoDiff` from the on-disk plist *and* from `cfprefsd`. But iTerm2 (PID `1368`) has never quit since the write and still serves `builtin.claudeCode` from memory. A fresh `claude` session at 01:43 spawned a new Diff pane (`11782`), now holding `docs/rse/control/board/readiness.html` via `Vim 14757`. **The "open a new tab to test it" advice given earlier in the session was wrong** — that test was run and it failed.
- **The pref write is at risk.** iTerm caches `New Bookmarks` in memory and flushes on quit. Quitting it may write the cached `builtin.claudeCode` trigger back over the edit. Correct order is **quit iTerm first, then write, then relaunch** — see Action Items.
- **Submodule is dirty** with a separate lane's work: `analysis/beta_campaign/*` (4 files), `analysis/scattering-refit-2026-06/plot_jointmodel_pair.py`, `analysis/scintillation-dsa-lorentzian-2026-07-07/run_dsa_lorentzian_fits.py`, and many `scintillation/configs/bursts/*.yaml`. Super-repo shows `m pipeline` (lowercase — dirty content, gitlink unchanged at `f9e1c24`). A closeout packet classifying an earlier snapshot of these paths passed `agent-closeout-check`, but it lives in an **ephemeral scratchpad** and the dirty set has since changed.
- **Untracked and unclassified:** `data/`, `scripts/__pycache__/`, and the two handoff docs above.
- **Not journalled.** Per the repo's journal protocol (`docs/rse/protocols/journal-protocol.md`, `scripts/journal-append.sh`) active work should append to `docs/rse/protocols/journal.jsonl` every ≤10 minutes. This session did not. The board at `docs/rse/control/board/readiness.html` is correspondingly stale for this work.

## Learnings

- **iTerm2 ships the `git difftool` pane, and it holds your real files.** The recurring, previously "unidentified" `git difftool -y -x vimdiff 'HEAD'` processes come from iTerm2's compiled-in `builtin.claudeCode` workgroup (sessions: Chat, Diff, Code Review), entered by an `iTermEnterWorkgroupTrigger` on the Default profile keyed to `jobName: "claude"`. `git difftool -y` walks changed files **one at a time and blocks on each**, so an unattended Diff pane parks `vimdiff` on the first changed file forever. The right-hand buffer is the **actual worktree file**, not a temp copy — a `:wq` there writes the repo. It also holds the `.swp`, which makes `lane-liveness` report `editor_lock: true` and pin the repo at `live`.
- **A swap file newer than its file is normal here, not evidence of a crash.** `vim -r <swap>` against it exits 2 and writes nothing, because a live Vim still owns it. Conversely, a swap that *survives* the Vim's death means there really were unsaved edits — Vim deletes its own swap on a clean exit.
- **`pgrep -x iTerm2` reports "not running" when iTerm is running.** `ps -A` was also truncated in this sandbox (31 processes visible), which produced a confidently wrong "no vim session exists" conclusion early in the session. Use `pgrep -fl` / `kill -0 <pid>` and cross-check before asserting a process is absent.
- **A concurrent agent can rewrite the tree between two of your read-only commands.** Mid-inventory, another session ran `git stash push --all` and started a rebase, which recreated `REPRODUCE.md` with a new inode. It looked exactly like self-inflicted damage. `git reflog` is what disambiguated it; nothing was lost, and the stash's third parent preserved even the ignored `.swp`.
- **Check the submodule index before committing into it.** A staged hunk from another lane sitting in the index is invisible to `git status --short` at a glance and will be swallowed by a bare `git commit`.
- **`lane-liveness` can be pinned `live` by a stale ref lock.** A 35-hour-old `.git/refs/heads/entire/*.lock` left by the broken `[entire]` hook kept `git_op: true` asserted. Removed. The `[entire]` hook itself still emits `fatal: Could not read from remote repository` on every git command in the submodule — that noise is expected; verify remote state with `git ls-remote`, never with push/commit exit output.

## Action Items & Next Steps

1. [ ] **Decide how `681cfe2` lands.** It is a docs/reproducibility change sitting on local `main`, unpushed, while the open PR #41 carries manuscript content. Either `git push origin main` (fast-forward, `behind=0`, but bypasses the repo's PR precedent) or cherry-pick it onto a focused `docs/` branch and open a PR. Do **not** fold it into PR #41 without intent — it mixes a repro-spine change into an Appendix-C content PR.
2. [ ] **Correct the two prior handoffs** so they cite `681cfe2` instead of the rebased-away `4a00aa0` (both are untracked in `docs/rse/specs/`; `4a00aa0` is preserved on `backup/main-pre-rebase-20260708`).
3. [ ] **Apply the iTerm fix for real:** quit iTerm2 completely (this kills every Claude session, including any running from it), then from a non-iTerm shell run `~/bin/iterm-claude-diff-pane off`, relaunch, and confirm with `iterm-claude-diff-pane status` plus `pgrep -fl 'Vim -dO'` returning nothing after a new `claude` session starts. Rollback is `iterm-claude-diff-pane on` (`builtin.claudeCode` was deliberately left intact).
4. [ ] **Rescue the prefs backup if it still matters.** `com.googlecode.iterm2.plist.bak` (21,297 bytes) was written to this session's scratchpad, which is ephemeral. Copy it somewhere durable before relying on it, or regenerate with `defaults export com.googlecode.iterm2 <path>`.
5. [ ] **Classify `data/`** — probably belongs under `~/Data/Faber2026/` with a symlink back, per the machine's data convention. Confirm ownership first; it appeared at 22:26 from a lane this session did not author.
6. [ ] **Re-run the emitter tests** against the current submodule tree (`f9e1c24`) before trusting the 9-passed figure: `cd pipeline && uv run pytest galaxies/foreground/test_budget_table_emitter.py galaxies/foreground/test_foreground_table_emitter.py`.
7. [ ] Backfill `docs/rse/protocols/journal.jsonl` for this session and rebake the readiness board.

**Recommended Next Skill:** `ai-research-workflows:ensuring-reproducibility` — the open work is the reproducibility spine itself (`REPRODUCE.md`, `repro_manifest.csv`, the `data/` placement, and re-verifying the parity tests), which is exactly that skill's remit. Landing `681cfe2` is a prerequisite, not a separate design task.

## Other Notes

- **Do not touch the `[entire]` git hook** in `dsa110-FLITS`. It prints `fatal: Could not read from remote repository` and tries to push to remotes named `0`, `1`, `preparing`, `prepared`, `committed` on every git command. It is non-fatal noise. Its real output is buried in the middle (`386e886..e0039c6`), so always confirm remote state with `git ls-remote`.
- **`Vim 14757` currently holds `docs/rse/control/board/readiness.html`** read-only, with no swap. Harmless, but it will keep this repo reading as `live` to `lane-liveness` until it exits or iTerm restarts.
- Several separate lanes were deliberately preserved untouched this session and remain so: the submodule's scintillation/beta-campaign work, the RSE bookkeeping files (`docs/rse/control/board/readiness.html`, `docs/rse/protocols/journal.jsonl`), and the 16 regenerated `figures/dsa_scint_acf/*.pdf` that a concurrent session wrote at 18:23 and has since landed.

---

**Handoff created by AI Assistant on 2026-07-09**
