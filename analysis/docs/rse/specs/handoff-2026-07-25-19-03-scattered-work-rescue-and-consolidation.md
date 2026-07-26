# Handoff: Scattered-work rescue and single-location consolidation

---
**Date:** 2026-07-25 19:03 PDT
**Author:** AI Assistant
**Status:** Handoff
**Branch:** `codex/scintillation-notebook-wayfinder` (parent Faber2026)
**Commit:** `8d492fea`

---

## Task(s)

The owner's stated objective: **make `~/Developer/repos/github.com/jakobtfaber/` the only location on this
machine holding anything related to `Faber2026`, `Faber2026-analysis`, or `dsa110-FLITS`**, with
`~/Data/Faber2026` as the sole additional location for data products. The work is scattered across
worktrees, stray clones, scratch directories, and an external drive, which the owner described as
making the material impossible to manage.

This session did **not** consolidate anything. It did the prerequisite: find every scattered copy,
prove what unique work each holds, and capture that work so consolidation can later proceed without
losing anything.

| Task | Status | Notes |
|------|--------|-------|
| Cancel the ">2 days idle" deletion clock | ✅ Complete | Owner decision; Tier 2 of the consolidation plan rewritten as an evidence-gated review queue |
| Map every location holding the three projects | ✅ Complete | See "Terrain" below; the map already existed and had never been landed |
| Rescue attempt 1 (7 targets, adversarially audited) | ✅ Complete, **failed** | Missed all parked changes; fooled by fake remote pointers; output landed in a temp scratchpad, not the intended drive |
| Rescue attempt 2 (gaps closed, re-audited) | ✅ Complete | Captures verified at `/Volumes/ArtifexBackupDrive/Faber2026-rescue-20260725-v2/` |
| Resolve the paused cherry-pick in the standalone analysis clone | ✅ Complete | 4-commit queue finished; **new commits are unpushed and uncaptured** |
| Preserve 876 unreferenced dsa110-FLITS commits | ✅ Complete (by Codex, independently verified) | 815 anchored refs; residual 34 are duplicate trees |
| Preserve the Overleaf checkout's unique history | ✅ Complete (by Codex, independently verified) | 144 anchored refs; all 75 canonical-absent commits bundled |
| Repoint **57** files referencing `Developer/overleaf/Faber2026` | 📋 Planned | **Blocks retiring the Overleaf directory** |
| Integrate captured work onto development branches | 📋 Planned | Nothing has been integrated; capture ≠ integration |
| Actually consolidate / delete anything | 📋 Planned | **Nothing has been deleted this session** |

**Current Workflow Phase:** Research → (capture/verification complete) → **Plan** for the integration
and retirement phases. Do not treat this as Implement.

## Critical References

Read these three first, in order, before doing anything:

- `analysis/docs/rse/specs/worktree-inventory-2026-07-22.md` — the pre-retirement census of 132
  worktrees. Carries a **HISTORICAL SNAPSHOT banner added this session** with the corrected
  preservation audit and a recovery map. Its counts are stale by design; the banner states current
  state (7 registered worktrees).
- `analysis/docs/rse/specs/plan-worktree-consolidation-2026-07-22.md` — the consolidation plan,
  **amended this session by owner decision** to cancel the idle-time deletion clock. Its Tier 2 proof
  gate is the rule any future retirement must satisfy.
- `worktree-reconciliation.md` (parent repo root, untracked) — the owner's own framing: this is an
  *authority reconciliation* project, not a worktree-cleanup project. It governs. Where it and the
  consolidation plan disagree, it wins.

## Terrain — where the three projects live

**Canonical, preserved, never deletion candidates** (owner directive, 2026-07-25):

```
~/Developer/repos/github.com/jakobtfaber/
├── Faber2026            8.8 GB   contains analysis/ and pipeline/ as submodules
├── Faber2026-analysis   1.3 GB
└── dsa110-FLITS         2.4 GB
~/Data/Faber2026         21 GB    data products only
```

**Leftovers inside that directory that are NOT repos** (clutter, pending owner confirmation):
`Faber2026-worktrees/` (786 MB, holds one old checkout `special-refs-20260724`),
`Faber2026-analysis-worktrees/` (0 B, empty), `Faber2026-analysis-jointtf.qjhnHz` (4 KB, one
leftover file).

**Everything else, all pending integration then removal:**

| Location | Size | Holds |
|---|---|---|
| `~/Developer/overleaf/Faber2026` | 1.7 GB | Retired route; 75 commits absent from canonical, 2 figure stashes |
| `~/Developer/scratch/2026-06/chime-dsa-documents-area-staging` | 421 MB | 3 unuploaded commits, 2 parked sets (one is a 313-file / 260k-line snapshot) |
| `~/Developer/scratch/preservation/` | 1.6 GB | dsa110-FLITS unreferenced 679 MB, Overleaf 197 MB, plus a pre-existing `Faber2026-science-gates-20260722` 780 MB |
| `~/Developer/scratch/faber2026-retirement-qualification-20260722.6Bd2Wy` | 2.4 GB | Records of the July cleanup |
| scratch analysis output (`window_campaign_2L`, `campaign_r4/5/6`, `perburst_figs`, `flits-local-runs`, …) | ~95 MB | Run results |
| `/Volumes/ArtifexBackupDrive/Faber2026-*` | ~29 GB | 4 side-checkouts, old archives, this session's rescue |

**Registered worktrees: 7 total** — parent root + 3 locked on the backup drive; analysis submodule
root + 1 locked on the drive; pipeline submodule root. Four of the seven live on
`/Volumes/ArtifexBackupDrive`. **`git worktree prune` while that drive is unmounted will deregister
them** — never run it detached.

## Recent Changes

- `analysis/docs/rse/specs/plan-worktree-consolidation-2026-07-22.md:1-12` — added the owner's
  cancellation banner; retitled from "Consolidation & Pruning Plan".
- `…plan-worktree-consolidation-2026-07-22.md:29-95` — Tier 2 rewritten from a prune list into an
  evidence-gated review queue with a four-part proof gate (authority status assigned; working tree
  clean; no open pull request; no unmerged unique delta proven by `range-diff`, **not** `git cherry`).
  Flagged one stale entry: the live `research/foreground-redshift-verdicts` worktree is on the backup
  drive and locked, not at the scratch path the plan named.
- `…plan-worktree-consolidation-2026-07-22.md:Tier 3/4` — added the unmounted-drive prune hazard;
  Tier 4 reworded from a 6-worktree quota to a description.
- `analysis/docs/rse/specs/worktree-inventory-2026-07-22.md:1-30` — historical-snapshot banner with
  the corrected preservation table and the recovery map for 10 empty archive slots.
- `Faber2026-analysis/docs/rse/wayfinder/map-apj-submission.md:64-73` — cherry-pick conflict resolved
  (took the incoming side; the HEAD side was empty). Added two entries to "Decisions so far":
  ticket 16 (verified Zach CHIME preprocessing baseline) and ticket 13 (trust assessment overhaul).
- Memory updated: `default-dev-workspace.md` (Overleaf checkout retired; stale hardcoded-path blocker
  corrected), new `faber2026-consolidation-target-layout.md`, index line in `MEMORY.md`.

## Reproducibility & Data State

- **Data:** `~/Data/Faber2026` (21 GB) is the canonical data location, reached by symlink from
  consumers. Untouched this session.
- **Preservation artifacts (Codex, 2026-07-25), both independently re-verified this session:**
  - `~/Developer/scratch/preservation/dsa110-FLITS-unreferenced-20260725/unreferenced-commits.bundle`
    — 703,646,038 bytes, sha256 `3933b486184b08675a20a7a3f7d1b5468c0953b8a5b1ee232b73ba979060a8a6`
    (recomputed locally, exact match). 815 refs under `refs/preserved/2026-07-25/` in the FLITS repo.
    Note the repo holds **816** refs under `refs/preserved/` in total — the extra one is
    `refs/preserved/wave3/…`, left by an earlier effort and unrelated to this preservation.
  - `~/Developer/scratch/preservation/Faber2026-overleaf-20260725/history/overleaf-comprehensive-preservation.bundle`
    — 78,223,987 bytes. 144 refs under `refs/preserved/` in the Overleaf checkout.
- **Rescue captures:** `/Volumes/ArtifexBackupDrive/Faber2026-rescue-20260725-v2/`, folders `01-` to
  `06-`. Each holds `state.json`, `MANIFEST.json`, `unique-commits.bundle`, `stashes/`,
  `worktree.diff`, `staged.diff`, `untracked-list.txt`, `untracked.tar.gz`, `unreachable.txt`,
  `fake-remote-namespaces.txt`.
- **In-flight jobs:** none. Both workflows (`wf_8836e016-140` and its resume) completed.

## Verification State / Known-Broken

- **Tests:** none run this session. No code was changed — only documents, one merge resolution, and
  read-only capture. Do not read this handoff as evidence any test suite passes.
- **Uncommitted / unpushed — this is the largest risk in the handoff:**
  - `Faber2026-analysis` (standalone, `6c0e9b3`) — **4 commits from the resolved cherry-pick are
    unpushed AND absent from every rescue archive**, which was captured before they existed. The
    branch is 5 ahead / 4 behind `origin/codex/nine-sightline-search-contract`. **Deleting or
    resetting that clone right now destroys the cherry-pick resolution.**
  - Parent `Faber2026` — 13 dirty entries including untracked `worktree-reconciliation.md`,
    `update-072326-1535.md`, `docs/rse/ops/`, `docs/rse/specs/`, `graphify-out/`. Two of the five
    "modified" entries are submodule pointer moves, not content edits — the pin is deliberate; do not
    commit it as a side effect.
  - `analysis` submodule — 5 untracked docs, including the two files this session edited.
  - `pipeline` submodule — 1 untracked file,
    `galaxies/foreground/data/expanded_catalog_cross_references.csv`.
- **Unverified:** the four backup-drive side-checkouts were captured but their audit agent died
  (`verify:backupdrive`, connection closed). Their captures were re-run and completed, but treat
  their completeness as **claimed, not independently audited**.
- **Nothing has been deleted or uploaded this session.**

## Learnings

The single most important pattern, learned three times the hard way:

- **Archiving by reference does not capture work that nothing references.** Every "this copy is
  clean" verdict collapsed under checking. First run missed **all** parked changes (`git stash`)
  across every repo. It then treated `refs/remotes/local/*` and `refs/remotes/local-owner/*` as
  proof of off-machine backup — they are **fake**: no configured remote, no URL, nothing behind them.
  That silently dropped branch `codex/resolve-trust-assessment-v2` (`06d21dc`, `ef3211b`). Finally,
  even the corrected run recorded 876 unreferenced FLITS commits as one-line summaries only, not
  content — including `32cdbae3`, "statistical 1-vs-2-vs-3 Lorentzian component selection", 216 added
  lines across `revalidation.py` and its test.
- **`git fsck --unreachable` under-reports.** It treats reflog entries as protective roots. Plain
  invocation found 774; `--no-reflogs` found 876. The 102-commit difference included real work.
- **A validation file proves nothing unless its timestamp covers the artifacts.** The earlier
  cleanup's `validation.json` reports `all_manifest_artifacts_present: true` but was captured
  `2026-07-22T22:54Z`, while the bundles it appeared to bless were written `2026-07-24 13:51`. Ten
  archive slots in `/Volumes/ArtifexBackupDrive/Faber2026-preserved-bundles/` are **completely empty**.
- **`git bundle verify` must be run from inside the bundle's own repository.** Run elsewhere it
  reports missing prerequisites and looks like corruption. This produced one false alarm here.
- **`git cherry` lies in these repos.** They rebase and squash-merge, so it reports already-upstream
  commits as unique. Use `range-diff` or content comparison. This is encoded in the Tier 2 proof gate.
- **Reports state absolutes where evidence is conditional.** Codex reported "could not preserve: 0"
  while 34 FLITS commits remained unreferenced. All 34 turned out to be duplicate trees, so the
  conclusion held — but the phrasing invited no follow-up where "34, all duplicates" would have.
- **Interrupting a turn kills its subagents.** A mid-turn message stopped the FLITS capture agent at
  00:28:18; it was retried automatically and succeeded.
- **The repowire mesh does not see this project.** Its daemon runs on port 8377 and rejects every
  request for lack of an authorization header — command line and tool path alike — and no credential
  exists in `~/.repowire/` or the keychain. Its own status output shows
  `✗ claude-code (hooks not installed)` while every other backend is set up. Monitoring gap, not a
  data risk. Fix with `repowire setup`, then confirm with a live call, not the status output.
- **Ten empty archive slots have a recovery map**, in the inventory banner: 2 recoverable from branch
  `codex/host-dm-repair-v2`, 4 from still-present commit objects (`ac58513`, `5292337`, `a9ac20c`,
  `ef3211b`), 1 from merged `dsa110-FLITS` PR #72, and **2 unresolved** (`analysis-review-pr36`, no
  surviving ref, `gh pr view 36` failed).

## Action Items & Next Steps

1. [ ] **Push the standalone `Faber2026-analysis` branch.** Its 4 cherry-pick commits exist in exactly
       one place. Everything else waits behind this. Then decide the 5-ahead / 4-behind divergence
       with `origin/codex/nine-sightline-search-contract` — a separate call, do not merge blindly.
2. [ ] **Repoint the 57 files referencing `Developer/overleaf/Faber2026`** — 30 under Faber2026
       (including its `analysis/` and `pipeline/` submodule working copies), 20 under the standalone
       Faber2026-analysis, 7 under dsa110-FLITS. Notable ones: `AGENTS.md` in both Faber2026 and
       Faber2026-analysis, `REPRODUCE.md`, `repro_manifest.csv`,
       `scripts/manuscript/regenerate_budget_figures.sh`,
       `docs/rse/specs/runbook-overleaf-propagation-2026-07-08.md`. Get the live list with:
       `rg -l 'Developer/overleaf/Faber2026' <each repo>`. Note
       `crossmatching/plot_association_cards.py` no longer hardcodes that path — it uses
       `ROOT.parent / "figures" / "association_cards"`; older notes claiming otherwise are stale.
       This is the only remaining blocker on retiring the Overleaf directory.
3. [ ] **Integrate the captured work onto development branches.** Per the owner: the backup-drive
       side-checkouts "likely contain work that has not been committed and should be committed to the
       development branches of one of our three development repos." Three sit on named branches; the
       fourth, `Faber2026-rfi-route-validation`, is detached — the owner approved creating
       `research/rfi-route-validation` for it. **That branch has not been created** (it fell under a
       halt instruction).
4. [ ] **Decide where the preservation artifacts terminate.** Both the backup drive and
       `~/Developer/scratch/` are staging under the owner's rule, not storage. ~29 GB on the drive and
       1.6 GB in `scratch/preservation/` currently have no terminal disposition. Note that
       `scratch/preservation/` also holds a pre-existing 780 MB `Faber2026-science-gates-20260722`
       from an earlier effort, which nothing in this session examined.
5. [ ] **Then, and only then, retire copies** — each through the Tier 2 four-part proof gate, with
       explicit owner approval naming exact paths. No date, idle time, or disk-size figure may drive a
       deletion decision.

**Recommended Next Skill:** `ai-research-workflows:planning-implementations` — the integration and
retirement phases need a written plan before execution, because they cross three repositories and
several one-way doors. Do **not** jump to `implementing-plans`.

## Other Notes

- **Instruction hierarchy.** The owner's `worktree-reconciliation.md` framing outranks the
  consolidation plan. The owner has repeatedly and correctly rejected reasoning of the form "this is
  backed up, therefore it can be deleted" — that argument was made this session about the canonical
  `dsa110-FLITS` and `Faber2026-analysis` clones and was wrong. Being captured is not a reason to
  remove a working repository.
- **Phase discipline.** Capture, integration, and retirement are separate phases. This session
  completed capture only. Several near-misses came from a verdict in one phase being read as
  permission in the next.
- **The first rescue attempt's output is gone**, and that is fine — it went to a temporary session
  scratchpad under `/private/tmp/claude-501/…`, never to the drive, because a destination parameter
  arrived empty. Superseded entirely by the `-v2` captures. Do not go looking for it.
- **Verification records** written this session via `verify-gate`: `561eb27e6d1a`, `fb90e56a50ee`,
  `5619c0d9abf6`, `fade886bc878`, `3794a143c3f0`, `e0e3a7931350`, `74fa3d2dee95`, `486876565695`,
  `b35648c3fd9c`, `8ce9db1813e7`.

---

**Handoff created by AI Assistant on 2026-07-25**
