# Receipt: live-analysis worktree disposition, 2026-08-05

**Objective:** record the branch, merge status, content status, and disposition
of every `Faber2026-analysis-*` worktree left by the paused ten-unit
live-analysis batch, and decide whether to relocate them.

**Scientific phase:** not applicable — repository readiness, no numerical work.

**Operational phase:** discovery and verification only. No worktree was moved,
removed, pruned, unlocked, or deleted. No branch or tag was deleted.

**Snapshot:** analysis `origin/main` = `3760079`; parent `main` = `6c631ab6`,
parent checkout on branch `chore/install-tend` @ `76cfe4d7`; analysis submodule
shared checkout detached at `1adcf97`. Verified 2026-08-05.

---

## Governing decision

The owner superseded the ten-unit batch on 2026-08-05 at 15:16 UTC: pull
requests #251–#255 were closed with supersession comments and replaced by #256,
`live-analysis/minimal-surface-v1`. The owner's instruction in that decision was
explicit: **"do not delete branches or auto-remove worktrees."** Every
disposition below is therefore *retain*, and this receipt records why each one
is safe to retain rather than authorising any removal.

## Inventory

Eleven directories match `~/Developer/scratch/worktrees/Faber2026-analysis-*`.
Only **eight** are registered worktrees of the `analysis` submodule
(`<parent>/.git/modules/analysis`). The other three belong to a **separate
clone**, `~/Developer/repos/github.com/jakobtfaber/Faber2026-analysis`, and are
a different lane; they are listed for completeness and were not touched.

### Registered to the `analysis` submodule

| Worktree (under `~/Developer/scratch/worktrees/`) | Branch | Head | Pull request | Working tree | Disposition |
|---|---|---|---|---|---|
| `Faber2026-analysis-u01-ops-guide` | `live-analysis/u01-ops-guide` | `93a00bc` | #251 **closed**, superseded by #256 | clean | Retain. Content salvaged into #256; branch preserved by owner instruction. |
| `Faber2026-analysis-u02-jupyter-surface` | `live-analysis/u02-jupyter-surface` | `f1f5822` | #255 **closed**, superseded by #256 | clean | Retain. Content salvaged into #256. |
| `Faber2026-analysis-u03-kernel-deps` | `live-analysis/u03-kernel-deps` | `3760079` (= `origin/main`) | none opened | **dirty**: `pyproject.toml` (M), `uv.lock` (M), `tests/test_jupyter_surface.py` (untracked) | Retain. Superseded in substance by #256, which implements the same `notebook` dependency group and a *better* smoke test (ephemeral tmp-dir kernelspec, fails rather than skips). Uncommitted work is redundant, not unique. |
| `Faber2026-analysis-u04-notebook-ignore` | `live-analysis/u04-notebook-ignore` | `3760079` | none opened | **dirty**: `.gitignore` (M), `config/grandfathered-notebooks.txt` (untracked), `tests/test_notebook_policy.py` (untracked) | Retain. **Design deliberately rejected.** #256 implements a plain `*.ipynb` ignore with *no* negation patterns plus the allowlist file, per the owner's correction 3. The 18 `!`-negation lines in this worktree are the superseded approach. |
| `Faber2026-analysis-u05-session-launcher` | `live-analysis/u05-session-launcher` | `3760079` | none opened | **dirty**: `Makefile` (M), `scripts/research_session.py` (untracked), `tests/test_research_session.py` (untracked) | **Retain — sole copy. See hazard below.** |
| `Faber2026-analysis-u06-analysis-briefs` | `live-analysis/u06-analysis-briefs` | `52d4bdf` | #252 **closed**, superseded by #256 | clean | Retain. Content salvaged into #256. |
| `Faber2026-analysis-u07-wayfinder-ticket` | `live-analysis/u07-wayfinder-ticket` | `514f926` | #254 **closed** as premature | clean | Retain. The owner directed that the admission ticket be recreated only after #256 merges and smoke-test evidence exists on `main`; this branch is the draft to recreate it from. |
| `Faber2026-analysis-u10-plan-spec` | `live-analysis/u10-plan-spec` | `ecff210` | #253 **closed** as an unnecessary plan artifact | clean | Retain. Not to be relanded. |

### Not registered to the submodule — separate clone, different lane

| Worktree | Branch | Head | Status |
|---|---|---|---|
| `Faber2026-analysis-ci-depth` | `codex/ci-depth-analysis` | `ff3090da` | clean; PR #243 merged. Owned by the `Faber2026-analysis` standalone clone. Untouched. |
| `Faber2026-analysis-ci-efficiency` | `codex/ci-efficiency` | `f463056e` | clean; PR #246 merged. Untouched. |
| `Faber2026-analysis-diagnostic-package` | `codex/repair-diagnostic-anchor` | `e177eac5` | clean; PR #245 merged. Untouched. |

### Created by this session

| Worktree | Branch | Head | Pull request | Disposition |
|---|---|---|---|---|
| `<analysis>/.worktrees/ci-gate-repair` | `ci/repair-routing-gate` | `fffb603` | #257 | Retain until #257 merges. |
| `<analysis>/.worktrees/worktree-receipt` | `receipt/live-analysis-worktree-disposition` | this commit | this pull request | Retain until merged. |

---

## Hazard: U5's launcher exists in exactly one place, uncommitted

`scripts/research_session.py` and `tests/test_research_session.py` (25 passing
tests as of the 07:57 handoff) are **not in #256** — verified by
`git ls-tree origin/live-analysis/minimal-surface-v1 scripts/research_session.py`
returning empty — and are not committed on any branch, local or remote. They
exist only as untracked files in
`~/Developer/scratch/worktrees/Faber2026-analysis-u05-session-launcher`.

The owner deferred this unit rather than rejecting it: #256's body says
`research_session.py` / `make session` land "only after repeated manual sessions
prove the pattern." Deferred work that lives solely in an untracked working tree
has no recovery path if that directory is cleaned — `git` cannot restore what it
never recorded.

This receipt does not commit that work, because doing so would create a branch
the owner did not ask for during an active supersession. It records the exposure
so the decision is explicit rather than accidental.

**Owner decision required:** preserve U5's launcher on a branch (no pull
request), or accept that it is discardable.

---

## Relocation: not performed, and the stated target is wrong

The task instruction was to relocate these worktrees to `<repo>/.grit/worktrees/`.
That is not the applicable convention, on three independent grounds:

1. `.grit/worktrees/` is **grit's** private coordination state — a lock registry
   plus per-agent worktrees, used only in the *no-shared-orchestrator* case where
   independent harnesses edit one repository concurrently. Entering that
   directory without `grit claim` puts checkouts inside a claim registry that
   knows nothing about them.
2. The general convention for an in-repository agent worktree is
   `<repo>/.worktrees/<name>` — globally ignored, and what this session used for
   its own two worktrees.
3. The owner's 15:16 decision says not to auto-remove worktrees. `git worktree
   move` is not removal, but relocating eleven directories — three of which
   carry uncommitted work and three of which belong to a different clone — is a
   state change with no benefit during an active supersession.

`~/Developer/scratch/worktrees/` is additionally a recognised staging area in
this project's own prior receipt,
[`receipt-worktree-consolidation-2026-08-04.md`](receipt-worktree-consolidation-2026-08-04.md),
which drains it deliberately rather than treating its contents as misplaced.

**Disposition: leave all eleven directories where they are.** Relocation, if
wanted, belongs in a consolidation pass that also updates that receipt.

---

## Verification

- Registration checked with `git worktree list` against
  `<parent>/.git/modules/analysis`; the three unregistered directories were
  traced through their `.git` pointer files to the standalone clone's
  `.git/worktrees/`.
- Working-tree state per worktree from `git -C <path> status --short`, with
  `.venv/` excluded as rebuildable.
- Pull-request states read live from the GitHub API, including each closure
  comment, on 2026-08-05.
- U5 uniqueness established by `git ls-tree` against
  `origin/live-analysis/minimal-surface-v1` and by the absence of any commit on
  `live-analysis/u05-session-launcher`, whose head is still `origin/main`.

## Actions still prohibited

No worktree may be removed, pruned, unlocked, or moved, and no branch or tag
deleted, without separate owner approval naming the exact paths. Nothing in this
receipt grants that approval.
