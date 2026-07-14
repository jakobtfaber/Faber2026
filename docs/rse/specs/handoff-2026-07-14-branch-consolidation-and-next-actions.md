# Handoff: Branch consolidation and the next safe actions

---
**Date:** 2026-07-14
**Author:** Codex
**Status:** Handoff; consolidation work is not complete
**Scope:** `jakobtfaber/Faber2026` and its `pipeline/` submodule, `jakobtfaber/dsa110-FLITS`
**Parent checkout at inspection:** `ms/validated-fit-figure-refresh-20260714` at `0c931ff`
**Parent `origin/main`:** `fcc67fb` (merged PR #34)
**FLITS `origin/main`:** `0cf513b` (merged PR #171)
**Inspection basis:** local refs/worktrees refreshed on 2026-07-14; public GitHub PR pages checked the same day
---

## Why this handoff exists

The repository has accumulated enough branches, worktrees, rewritten-history
artifacts, figure-review experiments, and parent/submodule transitions that the
branch names no longer provide a reliable picture of what is active. The owner
does not need another undifferentiated branch list. The immediate goal is to
reduce the control surface without losing uncommitted work or silently changing
the scientific state.

This document gives one ordered course of action. It also corrects earlier
assessments that became stale during the 2026-07-14 merges.

## Owner summary: what to do next

Declare a temporary **consolidation freeze**:

- do not create new science branches or worktrees;
- do not bulk-delete branches merely because their names look old;
- do not remove any dirty worktree;
- finish the parent/submodule figure-publication chain first;
- then merge the already-open P0 provenance PR;
- keep A1 as the only longer-running development campaign;
- only after those closures, prune proven-integrated branches and worktrees.

The owner should need to track only three FLITS development lanes:

| Order | Canonical FLITS branch | State | Next gate |
|---|---|---|---|
| 1 | `fix/dm-locked-joint-figures-v2` | **Develop/publish now.** Tip `67bdd01`; 15 commits ahead of FLITS `origin/main`; no open PR was visible on the fork. Faber2026 `main` already pins this tip. | Open a focused FLITS PR, validate it, merge it, then move the parent pin to the resulting commit on FLITS `main`. |
| 2 | `reval/p0-provenance` | **Open PR #170.** Three commits ahead and two behind FLITS `origin/main` at inspection. | Bring current `main` into the branch without rewriting shared history, rerun its focused tests, review, and merge. |
| 3 | `a1/trigger-calibration` | **Active but parked behind closure work.** Six commits ahead of FLITS `origin/main`; no open PR visible. | Continue the calibration campaign only after lanes 1 and 2 are closed. Do not merge until its scientific completion gate is met. |

There is also one temporary Faber2026 stabilization lane: consolidate the three
dirty `figure-approval` worktrees into one reviewed implementation. This is
control-plane work around the figures, not a fourth science campaign.

## Material corrections to the earlier assessment

1. **The parent figure PR is already merged.** Faber2026 PR
   [#34](https://github.com/jakobtfaber/Faber2026/pull/34) merged into `main` as
   `fcc67fb`. Faber2026 currently shows zero open PRs.
2. **The figure publication chain is nevertheless not closed.** Parent
   `origin/main` pins FLITS commit `67bdd014`, the tip of
   `origin/fix/dm-locked-joint-figures-v2`. That branch is 15 commits ahead of
   FLITS `origin/main` (`0cf513b`) and has no visible open PR. The manuscript
   therefore depends on a feature-branch commit that has not landed on FLITS
   `main`.
3. **The root checkout is stale, not the authority.** It remains on the
   superseded v1 branch at `0c931ff`, five commits behind and one unique commit
   ahead of parent `origin/main`. It pins FLITS `05088fa`, while merged parent
   `main` pins the newer `67bdd014`.
4. **The figure-approval worktrees are not clean.** Three worktrees are based
   at `fcc67fb` but contain substantial uncommitted or staged state. They must be
   quarantined and reconciled, not pruned.
5. **Repository identity matters.** The submodule's `origin` is the fork
   `jakobtfaber/dsa110-FLITS`; `upstream` is `dsa110/dsa110-FLITS`. The fork has
   open PR #170. The upstream repository separately has draft PR #49. Do not
   combine their PR numbering or branch state.

## Current topology

```text
Faber2026 origin/main @ fcc67fb  (PR #34 merged)
└── pipeline gitlink @ 67bdd014
    └── origin/fix/dm-locked-joint-figures-v2 @ 67bdd014
        └── 15 commits ahead of FLITS origin/main @ 0cf513b

Current root checkout @ 0c931ff  (superseded v1 branch)
└── pipeline worktree detached @ 05088fa
```

The important distinction is that `67bdd014` is fetchable from the fork and is
scientifically used by merged Faber2026 `main`, but it is not yet on FLITS
`main`. Accessibility is not the same as integration.

## Parent working-tree inventory

The counts below are from `git status --porcelain` at inspection. A zero count
means clean; it does not by itself authorize deletion.

| Worktree / branch | Dirty paths | Classification | Action |
|---|---:|---|---|
| Root: `ms/validated-fit-figure-refresh-20260714` | 1 | Superseded branch; the sole dirt is `docs/rse/journal.jsonl`. The branch still has one unique commit relative to `origin/main`. | Preserve the journal line and this handoff. Do not switch/reset until both are carried to an intentional lane. Then retire the branch after confirming PR #34 contains the desired figure bytes. |
| Missing `/private/tmp/faber2026-refresh/parent-merge`: `ms/validated-fit-figure-refresh-20260714-v2` | n/a | Prunable worktree metadata; branch is an ancestor of `origin/main`. | Safe to prune the stale worktree registration after no process references the path. Branch deletion is a separate cleanup step. |
| `Faber2026-figure-approval` | 126 | High-risk mixed state: 94 modified, 22 deleted, 3 untracked, and 7 partially staged paths. Mostly figure assets, with source/test changes. | Quarantine. Inventory and compare against v2/v3; never delete or sweep into a commit. |
| `Faber2026-figure-approval-v2` | 11 | Uncommitted approval framework: `Makefile`, seven TeX sections, `scripts/figure_review.py`, tests, and `figure_review/`. | Quarantine. Treat as a candidate implementation, not cleanup. |
| `Faber2026-figure-approval-v3` | 100 | Staged approval framework and immutable candidate packet; 92 added paths and 8 modified paths. | Likely the most complete candidate, but canonical status is **decision pending** until compared with v1/v2 and ownership is confirmed. |
| `Faber2026-pin-flits-171`: `ms/pin-flits-171-20260714` | 0 | Patch-equivalent to work already on `origin/main`; its remote branch is gone. | Cleanup candidate after the figure/pin chain is closed. |
| `Faber2026-qualified-oran`: `ms/qualified-oran-scintillation-20260714` | 0 | Ancestor of `origin/main`. | Cleanup candidate. |
| `Faber2026-reland-state-sync`: `agent/reland-state-sync-20260714` | 0 | Three commits are patch-equivalent to `origin/main`, despite rewritten topology. | Cleanup candidate after recording that patch-equivalence is the proof. |
| `Faber2026-root-science-tests`: `ci/root-science-tests` | 0 | Two genuinely unique commits. | Preserve and review as its own focused PR/development decision; not stale cleanup. |

### Dirty-state boundary

The root `docs/rse/journal.jsonl` modification predates this handoff and was not
edited. The three figure-approval worktrees are also pre-existing shared work.
Their staged state is an ownership signal. Do not unstage, restore, regenerate,
or delete their files as part of general branch maintenance.

## The figure-approval decision gate

The v2/v3 worktrees introduce a fail-closed, two-PR figure workflow:

1. an immutable candidate packet is reviewed by stable candidate ID;
2. owner decisions are recorded explicitly;
3. only approved bytes are promoted into manuscript figure targets;
4. receipts bind the reviewer decision, figure hash, adopted-DM catalog hash,
   source revision, and pipeline revision;
5. `make test-science` rejects protected TeX inclusions without a matching
   receipt.

This is substantive manuscript governance, not disposable scaffolding. It also
creates a real decision because PR #34 already merged the replacement figures
before this approval framework landed.

The required owner decision is:

> Is the approval gate prospective, or must the figures merged in PR #34 be
> reviewed and receipted retroactively before they remain manuscript-active?

Until that is answered, the approval worktrees are **decision pending**, not
completed and not stale. A consolidating agent may compare and package the
implementations, but must not infer approval from tests, previous agent visual
review, or the fact that PR #34 merged.

## FLITS working-tree inventory

All listed FLITS worktrees were clean at inspection, but clean is not equivalent
to deletable:

| Worktree branch | Classification |
|---|---|
| Detached submodule checkout at `05088fa` | Stale relative to the merged parent pin `67bdd014`; update only through an intentional parent checkout transition. |
| `scint/chime-additive-likelihood` | Historical experiment/evidence lane; retain until its result is summarized and branch disposition is verified. |
| `scint/chime-endtoend-calibration` | Historical experiment/evidence lane; same rule. |
| `scint/recovered-notebook-replay` | Historical experiment/evidence lane; same rule. |
| `scint/chime-recovery-qualified` | Historical experiment/evidence lane; same rule. |
| `scint/chime-scallop-calibration` | Historical experiment/evidence lane; same rule. |
| Detached `flits-pr52-merge` | Cleanup candidate only after confirming no current plan or handoff cites its exact checkout. |
| `scint/reference-arc-rescue` | Historical experiment/evidence lane; preserve until its null/rescue conclusion is captured in the canonical record. |

The correct consolidation target is not to keep seven operational worktrees
forever. It is to preserve the branch commits and durable conclusions, then
remove redundant worktree checkouts. Do that only after lane-by-lane provenance
review; the fork's 2026-07 history rewrite makes naive ancestry checks
insufficient for some branches.

## Ordered execution plan

### Phase 0 — freeze and protect

Status: **in progress by policy; no mutations performed by this handoff.**

1. Stop creating new branches/worktrees except a short-lived, focused landing
   lane when required to publish reconciled work.
2. Record each active writer and worktree before changing shared refs.
3. Preserve the root journal change and all three dirty approval worktrees.
4. Use the fork (`jakobtfaber/dsa110-FLITS`) as the parent submodule authority;
   consult upstream separately.

### Phase 1 — close the FLITS figure branch

Status: **required; not started.**

1. Inspect `origin/fix/dm-locked-joint-figures-v2` from a clean FLITS worktree
   at tip `67bdd014`.
2. Confirm the 15-commit branch has the expected scope and no unrelated
   rewritten-history payload.
3. Rerun the focused FLITS tests used for PR #34, plus the repository-required
   CI suite. PR #34 recorded 19 focused FLITS tests passing; treat that as prior
   evidence, not a substitute for the FLITS PR gate.
4. Open a focused PR from `fix/dm-locked-joint-figures-v2` to FLITS `main`.
5. Review and merge without force-pushing concurrent work.
6. Record the resulting FLITS `main` commit. If GitHub produces a new merge or
   squash commit, the parent pin must move from `67bdd014` to that commit.
7. Open one focused Faber2026 pin-only PR, verify `make test-science`, compile
   `main.tex`, inspect the affected figures, merge, and return a clean parent
   checkout to `main`.

Completion condition: Faber2026 `main` pins a commit reachable from FLITS
`main`, and no manuscript figure depends only on an unmerged FLITS branch.

### Phase 2 — consolidate the figure-approval work

Status: **decision pending; dirty shared work exists.**

1. Compare v1, v2, and v3 at the path and content level, including staged and
   unstaged layers. Do not assume v3 is a strict superset solely because it has
   more staged paths.
2. Identify the writer/intent of each worktree from journal or agent handoff
   context.
3. Choose one canonical implementation only after proving it preserves all
   wanted source, tests, candidate hashes, previews, and review metadata.
4. Resolve the prospective-versus-retroactive approval decision above.
5. Validate the canonical implementation in a clean worktree and publish it via
   one focused PR.
6. Only after merge and byte-level comparison may the redundant approval
   worktrees be removed.

Completion condition: exactly one approval implementation is on `main`, its
policy scope is explicit, review packets are preserved, and all redundant dirty
worktrees have either been safely incorporated or intentionally archived.

### Phase 3 — finish P0 provenance

Status: **open PR.**

1. Resume FLITS PR [#170](https://github.com/jakobtfaber/dsa110-FLITS/pull/170),
   branch `reval/p0-provenance`.
2. Bring current `main` into the branch using a non-destructive strategy. At
   inspection it was three commits ahead and two behind.
3. Rerun the provenance, frozen-census/adjudication, fit-generation inventory,
   and budget-table parity checks named in the PR.
4. Address review/CI findings, merge, and remove the branch only after the PR is
   confirmed merged.

Completion condition: P0.2-P0.4 are on FLITS `main`; the PR is closed as merged;
no follow-up is disguised as completion.

### Phase 4 — continue A1 as the sole long-running campaign

Status: **active, not ready to merge.**

1. Keep `a1/trigger-calibration` as the single canonical A1 branch.
2. Confirm it remains based on the current post-reland main before new work.
   The refreshed ref was six commits ahead and zero behind at inspection.
3. Use one worktree. Do not fork per diagnostic or per agent.
4. Merge only after the campaign's scientific completion and validation gates
   are satisfied.

Completion condition: the A1 plan records a validated result and the branch is
either merged or explicitly blocked by an external/scientific gate.

### Phase 5 — prune proven-integrated parent worktrees and branches

Status: **pending Phases 1-3.**

Recommended order:

1. prune only the missing `/private/tmp/faber2026-refresh/parent-merge`
   registration;
2. remove clean worktrees whose branches are proven integrated:
   `ms/pin-flits-171-20260714`,
   `ms/qualified-oran-scintillation-20260714`, and
   `agent/reland-state-sync-20260714`;
3. preserve `ci/root-science-tests` until its two unique commits are reviewed;
4. carry the root journal line and this handoff to an intentional clean lane,
   then retire the superseded root v1 branch;
5. remove v1/v2/v3 approval worktrees only after Phase 2 closes;
6. delete remote branches only after a fresh PR lookup and either ancestry,
   patch-equivalence, or supersession proof is recorded.

Do not use a single `git worktree prune` plus bulk branch deletion as a substitute
for the above classification.

### Phase 6 — replace branch archaeology with one control file

Status: **pending.**

Create or update `docs/rse/ACTIVE_LANES.md` with only these fields:

| Field | Meaning |
|---|---|
| Lane | Human-readable workstream |
| Canonical repository/branch | The only branch new work may target |
| Status | `active`, `blocked`, `decision pending`, or `cleanup` |
| Next gate | One concrete condition, not a narrative |
| Evidence | PR, commit, plan, or handoff link |
| Worktree | The single expected checkout, if any |

Do not turn this file into another full history. Closed lanes should move to a
short archive section or disappear after their PR/evidence link is recorded.

## Branches that require later individual disposition

These are not part of the immediate three-lane execution sequence, but local
inspection shows unique or potentially valuable work. They must not be swept
away during cleanup:

- `ci/root-science-tests` — two unique commits;
- `docs/loop-orchestration` — two commits ahead of its old base;
- `infra/owner-board` — board/control-surface work on a substantially old base;
- `ms/association-summary-reconcile-20260713` — manuscript/figure reconciliation;
- `ms/verified-dm-integration` — DM integration work;
- the three dirty `ms/figure-approval-gate-*` worktrees described above.

All other old manuscript, research-packet, reconciliation, and scintillation
branches remain **cleanup candidates**, not authorized deletions. The next audit
must verify each against current `main`, closed PRs, and patch-equivalence after
the active closures. This is especially important for branches created across
the FLITS history rewrite.

## Do-not-do list

- Do not delete any dirty worktree.
- Do not reset, restore, unstage, or regenerate the approval worktrees in bulk.
- Do not infer owner figure approval from PR merge, tests, or agent visual review.
- Do not force-push a branch that may have another writer.
- Do not merge a parent manuscript PR while accidentally changing the
  `pipeline/` gitlink.
- Do not leave Faber2026 `main` permanently pinned to a FLITS feature branch.
- Do not confuse `jakobtfaber/dsa110-FLITS` PRs with `dsa110/dsa110-FLITS` PRs.
- Do not classify a clean worktree as stale without checking unique commits,
  patch-equivalence, PR state, and handoff references.
- Do not start another scientific campaign until the figure and P0 closures are
  complete.

## Definition of a manageable repository

The consolidation is complete only when all of the following are true:

- the normal Faber2026 checkout is clean and on current `main`;
- Faber2026 `main` pins a commit reachable from FLITS `main`;
- the figure-approval policy is explicit and exactly one implementation remains;
- P0 PR #170 is merged or has a concrete external blocker;
- A1 is the only long-running development campaign;
- unique root-science-test work is either PR'd or explicitly deferred;
- no dirty worktree is deleted or silently absorbed;
- redundant clean worktrees are removed;
- remote branches are deleted only with recorded proof;
- `docs/rse/ACTIVE_LANES.md` is the owner-facing control surface;
- the owner can answer “what is active?” without reading `git branch -a`.

## Verification commands for the next agent

Run from the Faber2026 root unless a command uses `-C pipeline`:

```bash
git status --short --branch
git worktree list --porcelain
git ls-tree origin/main pipeline
git submodule status

git -C pipeline fetch origin --prune
git -C pipeline status --short --branch
git -C pipeline worktree list --porcelain
git -C pipeline rev-list --left-right --count \
  origin/main...origin/fix/dm-locked-joint-figures-v2
git -C pipeline rev-list --left-right --count \
  origin/main...origin/reval/p0-provenance
git -C pipeline rev-list --left-right --count \
  origin/main...origin/a1/trigger-calibration
```

Use a live PR query in addition to local refs. At handoff time the public state
was:

- Faber2026: zero open PRs; PR #34 merged;
- `jakobtfaber/dsa110-FLITS`: one open PR, #170;
- FLITS PR #171 merged as `0cf513b`;
- `dsa110/dsa110-FLITS`: separate upstream state, including draft PR #49.

## Verification performed for this handoff

- inspected parent and submodule remotes;
- refreshed FLITS fork refs with `git fetch origin --prune`;
- inspected parent and FLITS worktree registrations and cleanliness;
- counted branch divergence from current remote `main` refs;
- checked ancestry and patch-equivalence for the principal clean parent cleanup
  candidates;
- inspected the figure-approval README and file layout without modifying it;
- checked the public GitHub PR pages for Faber2026, the FLITS fork, and upstream;
- confirmed parent `origin/main` pins `67bdd014`, while the current root checkout
  pins `05088fa`;
- preserved the pre-existing `docs/rse/journal.jsonl` modification unchanged.

No scientific code, figures, TeX, submodule pin, branch, worktree, PR, or remote
branch was changed by creation of this handoff. Documentation-only verification
does not close any of the implementation phases above.
