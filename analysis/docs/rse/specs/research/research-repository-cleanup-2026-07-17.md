# Research: Faber2026 and FLITS repository cleanup

**Date:** 2026-07-17
**Scope:** Internal repository and live GitHub state
**Related Documents:** [Branch consolidation handoff](../handoff/handoff-2026-07-14-branch-consolidation-and-next-actions.md), [CHIME/figure-review closeout](../handoff/handoff-2026-07-14-chime-repair-and-figure-review-closeout.md)
**State inspected:** Faber2026 `origin/main` at `3f27232c`; FLITS fork `origin/main` at `8e545892`; FLITS upstream `main` at `0cf513b5`

## Question / Scope

Determine why the Faber2026 GitHub repository again has dozens of branches,
which open PRs and issues are stale versus active, which root entries are actual
remote clutter versus local ignored state, and how the `pipeline/` fork relates
to `dsa110/dsa110-FLITS` without losing dirty or scientifically relevant work.

This is a classification document. It does not itself authorize deleting remote
branches, closing GitHub items, moving manuscript inputs, or changing the
submodule pin.

## Codebase and Remote Findings

### 1. The cleanup problem is real and has a clear recurrence mechanism

- Live GitHub counts are 45 branches for `jakobtfaber/Faber2026`, 30 branches
  for `jakobtfaber/dsa110-FLITS`, and 5 branches for upstream
  `dsa110/dsa110-FLITS`.
- Both personal repositories have `delete_branch_on_merge=false`, while all
  three GitHub merge modes are enabled. The branch pile-up is therefore the
  expected result of rapid PR throughput rather than evidence that 45 lanes are
  active.
- Faber2026 has one open PR and six open issues. The FLITS fork has three open
  PRs and no open issues. Upstream has one open draft PR.
- The prior consolidation policy explicitly required proof before pruning and a
  small active control surface
  ([handoff](../handoff/handoff-2026-07-14-branch-consolidation-and-next-actions.md)); that
  policy remains sound, but the counts and lane list in that document are stale.

### 2. Faber2026 branch classification

Of the 45 live branches:

- `main`, `gh-pages`, and `entire/checkpoints/v1` are infrastructure branches to
  preserve.
- 36 non-default branches point at commits associated with merged PRs. These are
  bulk-delete candidates after remote deletion is explicitly approved. The
  local worktree on `ms/review-prose-20260715` is clean, so deleting its remote
  tracking branch would not discard uncommitted bytes.
- `cursor/results-library-catalog-yaml-7b14` backs open PR
  [#102](https://github.com/jakobtfaber/Faber2026/pull/102). The PR already has
  an owner comment stating that it is superseded by merged PR #103 and should be
  closed. It is a close-then-delete candidate.
- The literal remote branch `HEAD` is an accidental branch at an old Overleaf
  commit, not Git's symbolic remote HEAD. It is a deletion candidate.
- `ms/provisional-joint-scint-twoscreen-20260715` and
  `ms/validated-fit-figure-refresh-20260714` are superseded branches from closed
  PRs #95 and #33. Their replacement work is preserved by merged PRs #97 and
  #34. They are deletion candidates after the closed-PR provenance is accepted
  as sufficient retention.
- `infra/owner-board` has no PR and retains an eight-file, 308-addition control
  plane diff. Much of its intent appears superseded by the hybrid control system,
  but it is not safe for bulk deletion until its unique scripts are reviewed.
- `overleaf-2026-07-11-2125` has no PR and differs from current main only by two
  executable hook files. It needs comparison against the live Overleaf checkout
  before deletion.

The 36 merged-PR deletion candidates are:

```text
agent/chime-artifact-report
agent/v3-energetics-contract
chore/ignore-claude-science
docs/active-lanes-p0-closure-20260714
docs/c1-calibration-verdict
docs/chime-common-mode-research
docs/chime-successor-routes
docs/dm-host-convolution-handoff-20260715
docs/gate0-and-ratifications
docs/journal-p1-landing
docs/owner-queue-resolution
docs/p2-routeb-predeclaration
docs/p3-gate0b-result
docs/p3-handoff
docs/p3-predeclare
docs/p3-prime-amendment
docs/p4-handoff
docs/p4-predeclare
docs/provisional-propagation-handoff-20260715
docs/samplewide-p3p4-handoff
feat/hybrid-control-system
ms/alpha4-method-wording
ms/dm-host-convolution-20260715
ms/f3-consistency-audit
ms/provisional-joint-scint-twoscreen-reviewed-20260715
ms/review-prose-20260715
ms/v4-census-gap-20260715
ms/writing-style-review-2026-07
pin/pipeline-1085de0
pin/pipeline-2242124
pin/pipeline-479d2c8
pin/pipeline-563645c
scint/p4-closeout
state/close-flag-day-lanes
state/f3-closeout
state/fix-lane-pr-semantics
```

Deleting those 36, the accidental `HEAD`, the two superseded closed-PR branches,
and the PR #102 branch after closing it would reduce Faber2026 from 45 branches
to 5 without touching `infra/owner-board` or the Overleaf lane.

### 3. Faber2026 issue classification

The canonical state file says GitHub state must be fetched live while scientific
lane status remains in `program-state.toml`
([program-state.toml:1-10](../program-state.toml)). The tracker has drifted from
that canonical state:

- Close #54: `hybrid-control-system` is `done`, PR #59 is merged, and its next
  action is `none` ([program-state.toml:22-33](../program-state.toml)).
- Close #68: P3 is `done` and terminal after merged FLITS PR #181
  ([program-state.toml:50-61](../program-state.toml)).
- Close #75: P4 is `done` with a terminal documented failure after merged FLITS
  PR #182 ([program-state.toml:64-75](../program-state.toml)).
- Close #55 after recording that its Route B lane is terminal and both successor
  lanes P3/P4 are complete. The generated owner view already calls Route B a
  documented failure ([ACTIVE_LANES.md:13-15](../ACTIVE_LANES.md)).
- Keep #56 open: A5 remains `proposed` ([program-state.toml:78-83](../program-state.toml))
  and active FLITS PR #193 is implementing evidence-selected component counts.
  The issue should be updated to link that PR rather than closed.
- Keep #58 open: the canonical lane is still `proposed`
  ([program-state.toml:106-111](../program-state.toml)). A fresh local review
  batch exists, but its manifest decisions are all `pending`; owner approval has
  not occurred.

### 4. Root clutter is mostly local state, not 45 GitHub-visible junk entries

- The README deliberately keeps the AASTeX root, author block, sections,
  figures, bibliography, and submodule at their present locations
  ([README.md:10-27](../../../README.md)).
- The remote root has 24 tracked files. Most apparent local clutter is already
  ignored: LaTeX build products, agent runtime directories, `.worktrees/`, and
  `graphify-out/` ([.gitignore:1-55](../../../.gitignore)).
- `.pytest_cache/`, `.ruff_cache/`, `logs/`, and `outputs/` are local generated
  state but are not ignored at the repository level. Adding explicit root ignore
  rules is a low-risk cleanup candidate. Existing contents must not be deleted
  as part of that edit.
- `fig1_preview.png`, `figure_review/batches/`, and
  `figures/toa_offset_decomposition.pdf` are untracked active review/science
  artifacts. They are not cleanup trash.
- The one clearly stale tracked root document is `language_audit.md`: it records
  now-obsolete line numbers and claims, and a July 17 handoff already marks it
  historical. It should move under `docs/rse/specs/archive/` or be replaced by a
  current generated audit in a separate reviewed change.
- Moving the root-generated `*_table.tex` files is not a housekeeping edit.
  Their emitters, manuscript `\input` paths, reproducibility manifest, and
  Overleaf layout all depend on those paths. Treat any `tables/` reorganization
  as its own migration.

### 5. The FLITS fork contains upstream; it is not behind

- The submodule intentionally uses the personal fork
  ([.gitmodules:1-3](../../../.gitmodules)); the repository policy says the fork
  is the manuscript authority and explicitly says not to retarget the submodule
  to the org remote ([PIPELINE.md:3-14](../../../PIPELINE.md)).
- Fork `main` contains upstream `main`: it is 60 commits ahead and 0 behind.
  Therefore no upstream commit is missing from the fork.
- The net fork/upstream delta is 445 files, roughly 751k additions and 177k
  deletions, dominated by campaign result products as well as code. A wholesale
  fork-main-to-upstream-main PR would be difficult to review and is not a safe
  alignment operation.
- `PIPELINE.md` currently says the fork is “300+ commits ahead”
  ([PIPELINE.md:9-14](../../../PIPELINE.md)); the live first-parent topology now
  shows nine fork-main merge commits after upstream main and a raw rev-list gap
  of 60. The prose should describe the policy without a drifting numeric count.
- Alignment should mean: periodically fetch upstream, prove the fork is not
  behind, curate upstreamable code into focused PRs, and keep manuscript pins on
  named fork-main commits. It should not mean retargeting the submodule or
  merging all manuscript campaign artifacts upstream.

### 6. The current manuscript pin is content-correct but topologically awkward

- Faber2026 `origin/main` pins FLITS `79b7b0e`, and the local parent checkout has
  the same gitlink. The submodule appears modified only because
  `crossmatching/toa_crossmatch_results.json` is dirty inside it.
- `79b7b0e` was the head of merged FLITS PR #189. GitHub squash-merged that PR as
  `221f26a`; both commits have the identical tree object
  `253d8ad30dc259351096e0d685aa34ded025b0a2`.
- No live fork branch contains `79b7b0e`, although the commit is still fetchable
  from GitHub. The pin therefore resolves today but is not reachable from a
  named branch.
- A pin-only change from `79b7b0e` to `221f26a` is a zero-content topology
  normalization. Advancing to current fork `main` at `8e54589` additionally
  imports merged PR #191 (the interactive CHIME window-tuning notebook and
  helpers) and is a separate behavior/provenance decision.
- Active FLITS PRs #192 and #193 are clean and green. They should not be folded
  into a housekeeping pin update before their scientific review and merge.

### 7. FLITS PR and branch disposition

- Keep PR #192 (`scint/window-tuning-campaign`) and PR #193
  (`joint/tf-fit-window-resolution`) open; both target fork `main`, are mergeable,
  and have passing checks.
- Close fork PR #190 as superseded by merged results-library PR #189 and
  Faber2026 PR #103; its companion Faber2026 PR #102 is already explicitly
  marked superseded.
- Upstream draft PR #49 is not clutter. It cleanly reverts the invalid DM-phase
  v1 campaign from upstream `pin/faber2026`; the invalid tree is still present
  on that branch, and the PR's CI is green. It needs a deliberate merge or an
  explicit replacement, not silent closure.
- The FLITS fork has 13 non-permanent branch tips associated with merged PRs,
  but several PRs merged into `pin/faber2026` or another feature branch rather
  than fork `main`. Treat these as review candidates, not a bulk-delete set.
  `pin/faber2026` is a long-lived integration branch and must be preserved even
  though its tip is associated with merged PRs. Each other branch needs either
  fork-main ancestry, patch-equivalence, or a named surviving integration ref
  before deletion.
- Seven fork branches have no current head PR and require lane-by-lane review:
  `a1/trigger-calibration`, `agent/dm-phase-v2`,
  `feat/chime-scint-common-mode-correction`, `fix/dm-locked-joint-figures`,
  `fix/scint-component-track-plot`, `reval/p0-provenance`, and the metadata
  branch `entire/checkpoints/v1`. Do not bulk-delete this set.

### 8. Dirty-state boundary

The Faber2026 root is two commits behind `origin/main` and has modified
manuscript, generated board, journal, plotting, and submodule paths plus multiple
untracked plans and figure-review artifacts. The submodule itself has a modified
TOA crossmatch result. A science-gates worktree also contains substantial
untracked results-library work. These are owned/concurrent changes, not cleanup
debris. No pull, reset, checkout, regeneration, or worktree removal is safe as
part of branch maintenance.

## Synthesis

The repositories do not have 75 active development branches. They have a small
number of active lanes plus a large residue of merged PR branches because
automatic branch deletion is disabled. The immediate cleanup can safely be
split into four independently reviewable actions:

1. Close the explicitly superseded PRs (#102 and #190), close four terminal
   Faber2026 issues, and update the two still-active issues.
2. Enable automatic deletion of merged head branches in both personal repos,
   then delete only the exact proven merged/superseded branch sets.
3. Add root-local ignore rules and archive the stale language audit in a focused
   Faber2026 PR without touching active dirty artifacts.
4. Normalize the submodule pin to the tree-equivalent FLITS PR #189 merge commit,
   separately from any later advance to PR #191 or the active #192/#193 work.

The fork/upstream relationship is currently ancestry-aligned. Its governance is
not: too much manuscript-specific result data has accumulated on the fork to
make a 60-commit upstream sync reviewable. Future upstreaming should be focused
and code-only where possible.

## References / Sources

- Code and policy: [`.gitmodules`](../../../.gitmodules),
  [`PIPELINE.md`](../../../PIPELINE.md), [`README.md`](../../../README.md),
  [`.gitignore`](../../../.gitignore),
  [`docs/rse/program-state.toml`](../program-state.toml), and
  [`docs/rse/ACTIVE_LANES.md`](../ACTIVE_LANES.md).
- Live GitHub: [Faber2026](https://github.com/jakobtfaber/Faber2026),
  [FLITS fork](https://github.com/jakobtfaber/dsa110-FLITS), and
  [FLITS upstream](https://github.com/dsa110/dsa110-FLITS), inspected
  2026-07-17 through authenticated GitHub API queries and local fetched refs.
