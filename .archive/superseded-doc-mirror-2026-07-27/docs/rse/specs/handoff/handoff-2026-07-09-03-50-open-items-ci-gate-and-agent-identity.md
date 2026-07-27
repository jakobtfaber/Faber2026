# Handoff: open items — CI parity gate, agent identity, iTerm Diff pane

---
**Date:** 2026-07-09 03:50 (PDT)
**Author:** AI Assistant (Claude Opus 4.8)
**Status:** Handoff
**Branch:** `docs/handoff-open-items` (cut from `origin/main` @ `733a369`)
**Commit:** `733a369` — *docs: mark B4 done in referee-response matrix (#62)*
**Submodule pin:** `pipeline` → `6c87890`

---

Scope: **open items only.** The completed work of this session (PRs #46, #51,
#54, #58; the budget-table drift and its reversal; the pin history
`f9e1c24` → `c69d043` → `6c87890`) is already recorded on `main` in
`REPRODUCE.md` hazard 1 and in the earlier handoffs. This document covers what
is *not* done.

## Task(s)

| Task | Status | Notes |
|------|--------|-------|
| PR **#59** — `table-parity` CI gate | 🔄 Open, awaiting review | `MERGEABLE/CLEAN`; its own `parity` check is **green**. Deliberately not self-merged. |
| PR **#63** — agent-identity runbook | 🔄 Open, awaiting review | `MERGEABLE/CLEAN`, docs-only. Its step 3 depends on #59 landing first. |
| Apply the iTerm Diff-pane fix | 📋 Blocked on owner | Prefs are written; requires quitting iTerm2 (PID **1368**) to take effect. Cannot be done by any agent. |
| Verify `repro_manifest.csv` `run_command` from a fresh clone | 📋 Not started | 25 rows; nobody has executed them from a clean checkout. |
| Narrow the merge authorization in `CLAUDE.md` | 📋 Declined this round | Offered and not selected; agents may still merge. See *Learnings*. |

**Current Workflow Phase:** Validate

## Workflow Artifacts

**Runbook:**
- [`runbook-2026-07-09-agent-identity-and-merge-gate.md`](../runbook/runbook-2026-07-09-agent-identity-and-merge-gate.md) — owner-only steps to split the agent principal from the owner and make review a real gate. **On PR #63, not yet on `main`.**

**Prior handoffs (already on `main`):**
- `handoff-2026-07-09-01-45-repro-spine-stranded-and-iterm-diff-pane.md` — carries a SUPERSEDED block; its content landed via #46/#51.
- `handoff-2026-07-08-22-49-flits-pipeline-commits-and-repo-state.md`
- `handoff-2026-07-08-18-42-submodule-roundtrip-figure-refresh.md`

## Critical References

- `REPRODUCE.md`, **hazard 1** — the cross-repository trap. `test_dm_host_matches_forward_model` lives in the `pipeline` submodule but reads `scripts/dm_budget_uncertainty.csv` from the super-repo, so its verdict is a property of the **(super-repo commit, submodule pin) pair**, not of either repo alone. Read this before touching either side.
- `.github/workflows/table-parity.yml` (**PR #59 only**) — the gate that makes that pair machine-checked.
- `docs/rse/specs/runbook/runbook-2026-07-09-agent-identity-and-merge-gate.md` (**PR #63 only**) — why a merge gate needs two principals before it means anything.

## Recent Changes

Both live on open PRs; neither is on `main`.

- `.github/workflows/table-parity.yml:1-61` (**#59**) — new. Checks out `pipeline` at the gitlink SHA of the commit under test, runs the two parity test files, then runs `--check --out ../<table>.tex` against the manuscript's tables. Actions pinned `actions/checkout@v7`, `astral-sh/setup-uv@v7` — note `setup-uv` publishes **no floating `v8` major** (only `v8.3.2`), so `@v8` fails to resolve.
- `.gitignore:45-46` (**#59**) — `/.github/` → `/.github/*` + `!/.github/workflows/`. The old rule (formerly line 42) ignored `.github/` alongside the agent-state dirs (`.codex/`, `.cursor/`, `.entire/`, `.remember/`, `.superpowers/`), which made **any** workflow uncommittable. Git cannot re-include a path whose parent directory is excluded, hence the `/*` form.
- `docs/rse/specs/runbook/runbook-…-agent-identity-and-merge-gate.md` (**#63**) — new, docs-only.

## Reproducibility & Data State

- **Environment:** `pipeline/uv.lock`, `requires-python >=3.12`. Invoke as `cd pipeline && uv run --frozen …`.
- **Data:** `data/` is 4 symlinks into `~/Data/Faber2026/dsa110/catalog/`; all resolve. It is gitignored on `main` (`.gitignore:20`, `/data/`) and holds 0 tracked files. No action needed.
- **Pin under test:** super-repo `733a369` × `pipeline` `6c87890`.
- **In-flight jobs:** none.

## Verification State / Known-Broken

- **Tests:** green. At pin `6c87890`: **9 passed**; both emitters' `--check` exit 0; `budget_table_emitter` output is byte-identical to `origin/main:budget_table.tex`. Re-verified directly this session, not inherited from a document.
- **CI:** `parity` passes on PR #59's own run (job `parity`, 33 s, 0 deprecation annotations). Confirmed it genuinely executed — the log shows `pipeline pin: 6c87890`, `9 passed`, and `OK: emitter matches ../budget_table.tex`.
- **Red-when-it-should-be:** at the drifted pin `f9e1c24` against `main`'s CSV, the parity test raises `AssertionError: FRB 20220207C: table 51^+37_-49 vs forward-model 51^+36_-43`, and `--check --out ../budget_table.tex` exits 1 — while **bare `--check` exits 0**. The gate is not theater.
- **Uncommitted / unpushed:** the main checkout sits on `ms/appendix-c-sync-pr40`, **18 behind / 3 ahead** of `main`, with no open PR. It carries `M sections/toa.tex` and an untracked `docs/referee_response_status_2026-07-09.md` that this session did not author — left untouched.
- **Unverified:** `repro_manifest.csv`'s `run_command` column. 25 rows — 11 `writer_verified=yes`, 13 `candidate`, 1 `unresolved`. **No row has been executed from a fresh clone.** This is the weakest claim backing the ApJ Data Availability statement.

## Learnings

- **A drift guard that compares a generator to its own output is blind by construction.** `--check` compares an emitter to `pipeline/exports/<table>.tex`; both derive from the same submodule-local `budget_table_data.json`. It stayed green through the entire drift window. Only a check that reaches across into the super-repo's CSV can see it. This is now recorded in `REPRODUCE.md` (PR #58) and enforced in CI (PR #59).
- **`--check` compares against whatever `--out` names**, not a hardwired path (`budget_table_emitter.py:153-156`). That is what lets the workflow point it at the manuscript's real table instead of `exports/`.
- **The review gate was never real.** PR #46 was opened `09:36:14Z`, warned *"⚠️ Hold this until the emitter's data file is fixed"* at `09:40:19Z`, and merged at `09:46:27Z` with **zero reviews**. Attribution cannot resolve it: agents authenticate as `jakobtfaber` and commit as `Jakob Faber <jfaber@caltech.edu>`, identical to the owner in `git log`, in the PR timeline, and in the merge event. `main` has **no branch protection** (`GET …/branches/main/protection` → 404). PR #63 is the fix; policy text in `CLAUDE.md` is not a gate.
- **`jakobtfaber-2` is already authenticated and holds `admin:org`** — far more authority than an agent should ever carry. Do not reuse that token as the agent principal.
- **iTerm2 stores `Workgroups` as a data blob**, so `defaults read com.googlecode.iterm2 Workgroups | grep claudeCodeNoDiff` returns nothing even when the key is correct. Use `defaults export … -` and parse with `plistlib`. This exact false negative cost time this session.
- **`pgrep -x iTerm2` reports not-running even when it is.** Use `ps -Ao pid,comm | grep '/iTerm.app/Contents/MacOS/iTerm2$'`.
- The `integrate/dsa-acf-push-20260708` lane, previously flagged as *decision pending*, **resolved itself** — branch gone locally and on the remote, worktree removed. Nothing owed.

## Action Items & Next Steps

1. [ ] **Review and merge PR #59** (`ci/table-parity-gate`). Its `parity` check is green. Do not merge #63's step-3 dependency before this — branch protection can only require a status check GitHub has already observed, and the context name is the **job id `parity`**, not the workflow name `table-parity`.
2. [ ] **Review and merge PR #63** (the identity runbook), then work its steps 1–4. Only the owner can do them.
3. [ ] **Apply the iTerm fix.** Quit iTerm2 (PID `1368`) → from a **non-iTerm** shell run `~/bin/iterm-claude-diff-pane off` → relaunch → verify with `~/bin/iterm-claude-diff-pane status` and `pgrep -fl 'Vim -dO'` (expect none after a fresh `claude` session).
   - **Hazard:** iTerm2 has been running since before the prefs were written and holds its own `NSUserDefaults` copy in memory, which it may flush on quit and clobber the change. Re-run `off` *while iTerm is quit*, then relaunch, and check `status` again.
   - **Blast radius:** quitting iTerm2 (1368) kills **five** live `claude` sessions — `89356` (the one that wrote this handoff), `21369` and `88240` (other `Faber2026` sessions), `4835` (`coherent-fold`), and `97691` (`undermind-mcp`). Verified by `kill -0` + `lsof -d cwd` at 03:50. **PIDs go stale the moment a session `--resume`s**, so re-derive them rather than trusting this list: `ps -Ao pid,ppid,comm | grep 'claude$'`, then `lsof -a -p <pid> -d cwd -Fn`. (An earlier handoff named `34193` for `undermind-mcp`; that PID is now dead and the session is `97691`.)
   - **Rollback:** `~/bin/iterm-claude-diff-pane on`, or full prefs restore from `~/backups/iterm2/com.googlecode.iterm2.plist.pre-nodiff-20260708.bak` (md5 `f62e488197c913e2f607cf8ac85920b1`) via `defaults import` while iTerm is quit.
4. [ ] **Verify the manifest from a fresh clone.** Clone to a scratch dir, `git submodule update --init`, and execute each `run_command`. Expect the 13 `candidate` rows to be where it breaks. Promote what survives to `writer_verified=yes`; that is what the Data Availability statement rests on.
5. [ ] Decide whether to narrow `CLAUDE.md`'s standing authorization from "push branches and open/merge pull requests" to *open, never merge*. It was offered this session and not selected.

**Recommended Next Skill:** `ai-research-workflows:validating-implementations` — for item 4, the fresh-clone manifest verification, which is a validation task with a clear pass/fail per row.

## Other Notes

- **Five `Vim -dO` diff panes are live right now** (PIDs 17590, 36944, 73286, 89326, 98903). Three are parked on `pipeline`; one holds `docs/rse/specs/decision/decision-2026-07-08-stage3-g1-axis.md` with the **real worktree file** on the right-hand side — a `:wq` there writes the repo. One belongs to a different repo entirely (`undermind-mcp`). They are the symptom item 3 removes. Committing a file before killing its pane makes any clobber a `git checkout --` away.
- The `table-parity` gate **cannot** catch a pin that is self-consistent but wrong — e.g. `c69d043`, the divergent squash that PR #53 had to back out of. It only catches a pair whose numbers disagree.
- The negative `DM_host` medians for FRB 20220310F and FRB 20221203A (both *z*≈0.5) are **intentional**. Their posteriors are consistent with zero (`P(DM_host<0)≈0.5`) and `budget_table.tex`'s `\tablecomments` explains them. Do not "fix" them by censoring at zero. (I called them unphysical earlier in this session; that was wrong.)

---

**Handoff created by AI Assistant on 2026-07-09**
