# Handoff: PR #42/#43 merged and validated; a concurrent closeout session owns everything else

---
**Date:** 2026-07-09 11:13 (UTC) / 04:13 (PDT)
**Author:** AI Assistant
**Status:** Handoff — my two deliverables merged; all other open items are being actively closed by a *separate live session*, by owner instruction ("let the live session finish; I'll just verify + report")
**Branch (my writes):** none local — git is in **coarse protection mode** this session, so every commit went to the remote via the GitHub API. Local checkout is parked on `ms/appendix-c-sync-pr40` @ `ad04f61` (stale; not mine).
**origin/main tip at handoff:** `733a369` (*docs: mark B4 done in referee-response matrix (#62)*)
**pipeline submodule pin on main:** `6c87890`

---

## Why this handoff exists / scope

I was asked to pick up from a pasted handoff and "complete all remaining open
items." Tracing every item with fresh evidence showed the repo had already moved
far past that handoff, and — critically — **a second Claude session is actively
closing out the repo right now.** In the span of this session it advanced `main`
from `bf0f902` through PR **#62**, opened PRs **#59/#63/#64**, re-pinned the
submodule twice, and wrote its own open-items handoff (PR #64). Per owner
decision, I **stopped writing** and this handoff records: (a) the two items I did
close and validate, (b) the true current state, and (c) an explicit pointer to
the other session's handoff for everything still open — so the two documents do
not fork.

**Do not treat this as the authority on the open items.** PR #64's handoff
(`handoff-2026-07-09-03-50-open-items-ci-gate-and-agent-identity.md`) is. This
document is the *provenance record for PRs #42/#43 and a map of the concurrency
situation.*

## Task(s)

| Task | Status | Notes |
|------|--------|-------|
| Merge PR **#42** — IGM spline low-z guard | ✅ Merged `8cef432` (squash) | **Independently revalidated before merge** (see Verification). Changes two *published* numbers. |
| Merge PR **#43** — track 07-08 handoffs, gitignore `/data/` | ✅ Merged `dbe8f29` (squash) | Required a remote `.gitignore` conflict resolution (`66f2133`) — union of `/data/` + main's `__pycache__/`. |
| Journal the two merges | ✅ `bf0f902` | Two JSONL entries appended via API. |
| Auditor corrections to my own claims | ✅ Fixed inline | Three: full-file CSV diff (not `head -11`); emitter "has a test" was false (no test file on disk); `52acde3` gloss corrected. See Learnings. |
| Handoff items 1,3,4,6 (toa B3, serialize, `data/`, referee #36 prose) | ✅ Already done / moot | #44 landed B3; concurrent writer gone; #43 did `data/`; referee doc already cites `765a40a` with correct 102–237 kpc range. |
| Handoff item 5 — drop/push `681cfe2` | ✅ Done by **other session** | Journal 03:02: "Dropped superseded 681cfe2 from local main (content landed via #46/#51)". |
| Handoff item 8 — budget_table emitter + parity | ✅ Done by **other session** | Emitter existed upstream but its `budget_table_data.json` was **stale (pre-#40 model)**; other session regenerated it, re-pinned `f9e1c24 → c69d043 → 6c87890`, landed repro spine (#48/#58), added CI gate (PR #59, open). |
| Read-only verification pass of the full closeout | 📋 **Deferred by owner** | To run once the live session stops. Read-only; no collision risk. |

**Current Workflow Phase:** Validate

## Workflow Artifacts

**Handoffs (read in this order):**
- **PR #64** → `docs/rse/specs/handoff-2026-07-09-03-50-open-items-ci-gate-and-agent-identity.md` — **the authority on all open items.** Covers PRs #59, #63, the iTerm Diff-pane fix, and `repro_manifest.csv` verification. On branch `docs/handoff-open-items`, not yet on `main`.
- This file — provenance for PRs #42/#43 and the concurrency map.
- Already on `main`: `handoff-2026-07-09-02-15-igm-spline-fix-pr42-and-concurrent-writer.md` (the one I picked up from — its items are now all resolved).

**Runbook (on PR #63, not on main):**
- `docs/rse/specs/runbook-2026-07-09-agent-identity-and-merge-gate.md` — owner-only steps to split the agent principal from the owner so review becomes a real gate.

## Critical References

- `REPRODUCE.md`, **hazard 1** — the cross-repository trap: the parity test lives in the `pipeline` submodule but reads `scripts/dm_budget_uncertainty.csv` from the super-repo, so its verdict is a property of the **(super-repo commit, submodule pin) pair**. Read before touching either side. This is exactly the trap that made item 8 non-trivial.
- `scripts/dm_budget_uncertainty.py` + `scripts/dm_budget_uncertainty.csv` — the authoritative host-DM posterior generator and its output (the numbers PR #42 changed). Seed `np.random.default_rng(20260707)`, `N_DRAW=200_000`.
- `tests/test_dm_budget_uncertainty.py` — the 10 correctness tests PR #42 added (analytic z→0 limit, seam continuity, `DM_IGM ≤ DM_cos` invariant, out-of-range guard). Not regression pins.

## Recent Changes (mine — all on `main` via API)

- `8cef432` (#42) — `scripts/dm_budget_uncertainty.py:105-160` guarded IGM calibration below `z=0.1`; `budget_table.tex`, `sections/appendix.tex` prose revert "generally exceed" → "exceed"; new `tests/test_dm_budget_uncertainty.py`.
- `dbe8f29` (#43) — added the two 07-08 handoff docs; `.gitignore` gained `/data/`.
- `66f2133` — merge commit on PR #43's branch resolving the `.gitignore` conflict (kept `/data/` + main's `__pycache__/`).
- `bf0f902` — `docs/rse/journal.jsonl` +2 entries logging #42/#43.

## Reproducibility & Data State

- **Seeds:** `np.random.default_rng(20260707)`, `N_DRAW=200_000` — unchanged by PR #42; the RNG stream is identical, so the seven on-grid sightlines reproduce bit-identically and only the two below-grid rows moved.
- **Environment for #42 validation:** conda `py312` at `~/.conda/envs/py312` (numpy 2.4.6, scipy 1.17.1, pytest 9.0.3). **Gotcha:** `conda run -n py312` panics (`pyo3_runtime.PanicException`); invoke the interpreter directly at `/Users/jakobfaber/.conda/envs/py312/bin/python`.
- **Environment for the emitter/pipeline side:** `pipeline/uv.lock`, `requires-python >=3.12`; `cd pipeline && uv run --frozen …`.
- **Data:** `data/` = 4 symlinks into `~/Data/Faber2026/dsa110/catalog/`; gitignored on `main`, 0 tracked files. No action.
- **In-flight jobs:** none of mine.

## Verification State / Known-Broken

- **PR #42 — verified by me, with fresh output:**
  - `pytest tests/test_dm_budget_uncertainty.py` → **10 passed** (re-ran; not inherited).
  - Regenerated `dm_budget_uncertainty.csv` from seed → **byte-identical across all 13 content lines** (header + 9 FRB rows + both `cluster_*` aggregate rows). *(Auditor caught my first pass diffing only `head -11`; the full-file diff is clean.)*
  - Row-by-row vs pre-fix `main`: **only** FRB 20220207C (`P(<0)` 0.185→0.125) and FRB 20240203A (0.010→0.007) moved; seven on-grid rows bit-identical.
  - `budget_table.tex` cells match the CSV (`$51^{+36}_{-43}$`, `$106^{+30}_{-36}$`).
- **Uncommitted / unpushed:** local checkout on `ms/appendix-c-sync-pr40` @ `ad04f61`, behind `main`, carrying an `M sections/toa.tex` that is **redundant with #44 on main** (verified byte-identical to `main:sections/toa.tex`) and untracked `__pycache__/`. Not mine; left untouched.
- **Open PRs at handoff (all the other session's; each polled `mergeable=True, mergeable_state=clean` via the single-PR API at 2026-07-09T11:2x UTC — note the list-PRs endpoint returns `mergeable=null` because GitHub computes it lazily, so poll each PR individually):**
  - **#59** `ci/table-parity-gate` — CI gate on cross-repo parity; its own `parity` check is green. Files: `.github/workflows/table-parity.yml`, `.gitignore`.
  - **#63** `docs/agent-identity-runbook` — docs-only; step 3 depends on #59 landing first.
  - **#64** `docs/handoff-open-items` — the open-items handoff itself.
- **Weakest claim in the repo (from PR #64, unverified by anyone):** `repro_manifest.csv`'s `run_command` column — 25 rows, none executed from a fresh clone. This backs the ApJ Data Availability statement.
- **This handoff was landed on `main`** additively at commit `a569d59` (parent `8146b11`, clean fast-forward) after the owner approved; it touches only this file + one `journal.jsonl` line and no submodule pin.

## Learnings

- **Item 8 was a trap disguised as a chore.** The pasted handoff said "build the budget_table emitter." It *already existed* in the pinned submodule — but its `budget_table_data.json` snapshot predated the #40/#42 IGM rebase, so its `exports/budget_table.tex` encoded the **old** host-DM model (e.g. 20240229A `211` vs the correct `197`). Adopting it would have *reverted* the numbers #42 just fixed. The reconciliation crosses the submodule boundary (a deliberately-reviewed pin per `CLAUDE.md`) and was correctly an author/other-session task, not an autonomous manuscript edit.
- **A drift guard that compares a generator to its own output is blind by construction** (recorded by the other session in `REPRODUCE.md` via #58, enforced in CI via #59). `budget_table_emitter --check` compares the emitter to `pipeline/exports/<table>.tex` — both from the same submodule-local JSON — so it stayed green through the entire drift window. Only a check reaching into the super-repo's CSV sees it.
- **Concurrency, not parallelism, was the right call.** Fanning out `cc-dispatch`/`codex-dispatch` subagents into a repo being actively closed out would recreate the exact multi-writer tangle the last four handoffs existed to untangle — collisions on files edited that minute, no shared orchestrator. Serialization is worth it only when there is work *only you can do* and a writer is *blocking* it; neither held. The load-reducing move was to stop, not to add writers.
- **Three of my own claims needed auditor correction** — a discipline note for the next session: (1) I first diffed the regenerated CSV with `head -11`, silently excluding the two cluster aggregate rows; full-file diff was required. (2) I stated the emitter "has a test" from its *docstring* alone — `tests/test_budget_table_emitter.py` is **not on disk** (tracked or present). (3) I glossed commit `52acde3` as "the REPRODUCE.md pin fix"; it is actually "record that `--check` is blind to cross-repo drift" — the pin fix was the separate `4a48a679`. **Verify before asserting; a docstring/summary is a claim, not evidence.**
- **`git ls-remote` / GitHub API is the source of truth here, not local git.** Coarse protection mode blocks local `.git` writes and the local checkout lags origin by many commits; every state check in this session went through the API.
- **Attribution cannot distinguish the two sessions** — both authenticate as `jakobtfaber` and commit as `Jakob Faber <jfaber@caltech.edu>`. The only reliable "who did what / is anyone still active" signal is commit/PR **timestamps** and the `docs/rse/journal.jsonl` agent tags. `main` has no branch protection (PR #63 is the proposed fix).

## Action Items & Next Steps (priority order)

1. **Let the live closeout session finish** (owner decision). At handoff its newest commit was ~41 min old and 3 PRs were open — it may be quieting but was not confirmed stopped. Do not dispatch writers into it.
2. **Once it stops, run the deferred read-only verification pass** and report: confirm PRs #59/#63/#64 land cleanly, the `(super-repo, pin)` pair is parity-green at the final tip, and the `main` history is internally consistent. Recommended skill: `ai-research-workflows:validating-implementations` (read-only; no plan file needed — validate against `REPRODUCE.md` hazard 1 + the parity CI).
3. **Land this handoff on `main`** via the GitHub API (coarse mode blocks local commit) — but only after the tree has a single owner, to avoid a `journal.jsonl` / docs fork. Additive-only; no submodule bump.
4. **Reconcile the local checkout** — it is parked on `ms/appendix-c-sync-pr40` with a redundant `toa.tex` mod. `git fetch && git checkout main && git reset --hard origin/main` once the owner confirms nothing local is owed (item 5 content already landed remotely).
5. **Owner-only, cannot be agent-done** (from PR #64): apply the iTerm Diff-pane fix (quit iTerm2), execute `repro_manifest.csv`'s `run_command` rows from a fresh clone, and decide whether to narrow merge authorization in `CLAUDE.md` + add branch protection.

**Recommended Next Skill:** `ai-research-workflows:validating-implementations` — for the deferred read-only verification of the whole closeout once the concurrent session stops.

## Other Notes

- **Standing push/PR authorization** (`CLAUDE.md`, owner grant 2026-07-08) was exercised for PRs #42/#43 only: squash-merges matching the `… (#NN)` convention, no force-push, no shared-history rewrite, no submodule pointer bump. Commits used inline `GIT_AUTHOR_*`/`GIT_COMMITTER_*` = `Jakob Faber <jfaber@caltech.edu>`, matching repo history.
- **Git identity is still not configured in-repo**; coarse protection mode remains active (narrow the host grant to the single `Faber2026` directory to restore fine-grained git).

---

**Handoff created by AI Assistant on 2026-07-09**
