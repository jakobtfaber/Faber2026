# Receipt: Faber2026 worktree consolidation, 2026-08-04

**Objective.** Land the work stranded in every Faber2026-related Git worktree
into the canonical repositories, then remove the worktrees.

**Scientific phase.** Exploration. No scientific result was produced, changed,
or re-interpreted; scientific-content merges were deliberately left unresolved
(see the joint-fit lane below).

**Operational phase.** Capture, then reconciliation, then retirement, in that
order, with the retirement step gated on explicit owner approval.

**Status.** VERIFIED.

## Source snapshots

Enumerated with `git worktree list` in the parent, in the `analysis` submodule,
and in the `Faber2026-analysis` clone, plus a directory scan of
`~/.codex/worktrees/` and `~/Developer/scratch/worktrees/` for unregistered
leftovers.

| Path | Owning repository | Snapshot at capture |
|---|---|---|
| `~/Developer/scratch/worktrees/Faber2026-analysis-casey-raw-dynamic-spectrum` | `analysis` submodule of `Faber2026` | branch `codex/casey-raw-dynamic-spectrum-notebook` at `e258f34`, 2 modified tracked files, 93 MB untracked |
| `~/Developer/scratch/worktrees/Faber2026-analysis-casey-reviewed-joint-fit` | `Faber2026-analysis` clone | branch `codex/casey-reviewed-joint-fit` at `47db3032`, 18 modified tracked files, 4 new untracked source files, 5 MB untracked renders |
| `~/.codex/worktrees/17a4/Faber2026` | `Faber2026` | detached at `9291babd`, only `.gitignore` modified |
| `~/.codex/worktrees/d948/analysis` | orphaned; administrative directory already pruned | 2026-07-27 snapshot, 1691 files, 314 MB |

Out of scope and untouched: `~/Developer/scratch/worktrees/gpu-ffa-tile12-plan-v2`
and the `1216`, `94f9`, `a636`, `c2bf` entries under `~/.codex/worktrees/`, all
of which belong to other projects.

## Disposition

### 1. casey-raw-dynamic-spectrum — landed, then removed

Committed the two items that belong in Git and rebased onto `origin/main`:

- `docs/rse/ops/repository-map.md` — removes `dsa110-FLITS` as a live
  dependency and states that all active scientific code lives in this
  repository.
- `observations/notebooks/casey-raw-to-dynamic-spectra.ipynb`.

Landed as pull request #236, squash-merged to `main` as `05904236`, all
checks green.

Its edit to `docs/rse/specs/dsa-trigger-mjd-timing.md` was **dropped**: the
`_v3_FINAL` filename that edit removed is already absent from `main`
(`git grep -n v3_FINAL origin/main -- docs/` returns nothing).

The 93 MB of executed outputs — `chime-dynamic-spectrum.npz`,
`dsa-dynamic-spectrum.npz`, the rendered PDF, the run receipts, and the page
renders — were kept out of Git per this repository's own rule that bulk campaign
bytes do not belong in Git, and copied to
`~/Data/Faber2026/preservation/casey-raw-dynamic-spectrum-20260804/` with a
`PROVENANCE.md`.

### 2. casey-reviewed-joint-fit — rescued to a branch, not reconciled, then removed

The worktree's three commits were already on `main` by way of pull request #234
(squash-merged, so the branch tip is not an ancestor of `main`). On top of them
sat roughly 3200 uncommitted lines across 22 files: the joint-fit likelihood
work in `radio_pipeline/fitting/`, `scripts/one_event_workflow.py` and
neighbours, the configs and schema, the tests, plus four new files
(`docs/analysis/casey-fit-input-diagnostic.ipynb`,
`docs/analysis/casey-fit-performance-recovery.md`,
`scripts/build_casey_windowed_fit_inputs.py`,
`scripts/profile_casey_joint_likelihood.py`).

That work was committed as `e68a393e` on branch
`codex/casey-fit-performance-recovery`, pushed, tagged
`rescue/casey-fit-performance-recovery`, and opened as **draft** pull request
#237.

It is **not reconciled with `main`**. `git merge origin/main` conflicts in 13
files, including the fitting library, the one-event workflow, and the
timing-authority tests, because pull request #235 later rewrote the same
regions. Resolving those conflicts is scientific-content reconciliation and was
left to a reviewer rather than decided here. The draft pull request records this
explicitly.

Excluded from the commit as scratch: `.venv/` (763 MB, rebuildable from the
lock), `docs/analysis/.ipynb_checkpoints/`, `docs/analysis/.write-probe`, and
`tmp/pdfs/`. `tmp/` was preserved to
`~/Data/Faber2026/preservation/casey-reviewed-joint-fit-20260804/`.

A Jupyter Lab server (PID 30628, port 8899, started 2026-08-03 21:11) was
running inside this worktree. Its single kernel was idle with zero client
connections and last activity 2026-08-04 05:20 UTC, and the notebook it served
is committed on the rescued branch. The owner approved terminating it.

### 3. 17a4/Faber2026 — nothing to land, removed

Detached at `9291babd`, identical to `main`. Its only difference from `HEAD`
was `.gitignore`, and `diff` against the canonical checkout's copy showed the
two files byte-identical, so the change was already present in the canonical
workspace. Nothing was carried over.

### 4. d948/analysis orphan — verified recoverable, quarantined

An unregistered 2026-07-27 snapshot; its administrative directory under
`.git/modules/analysis/worktrees/` had already been pruned, so Git no longer
saw it.

Every one of its 1691 files was hashed with `git hash-object` and looked up in
the `analysis` object store with `git cat-file --batch-check`. **Five** blobs
were missing, all of them `__pycache__/*.pyc` byte-code artifacts. Every other
file — including all 507 untracked ones, such as the `figure_review/batches/`
trees no longer present in `main` — is byte-identical to content already in the
repository's object store.

Moved to `~/Data/Faber2026/_trash/worktree-consolidation-20260804/d948-analysis-orphan`
rather than deleted, so the step stays reversible.

## Commands used

```sh
git worktree list                              # in parent, submodule, and clone
git diff origin/main --stat                    # per worktree, scope of unique work
git merge-base --is-ancestor HEAD origin/main  # squash-merge detection
find . -type f -print0 | xargs -0 git hash-object \
  | git cat-file --batch-check                 # orphan recoverability proof
rsync -a  ... ; rsync -rcn ...                 # preserve, then verify by checksum
git worktree remove --force <path>             # after landing
```

## Verification

- **Landed work:** pull request #236 merged to `main` as `05904236` with all
  checks green; pull request #237 pushed and open as a draft, its head commit
  `e68a393e` also reachable from tag `rescue/casey-fit-performance-recovery` on
  the remote.
- **Preserved bytes:** each copy compared against its source with a file-list
  `diff` and a whole-file checksum pass (`rsync -rcn`) *before* the worktree was
  removed. Both reported no differences.
- **Orphan:** blob-presence proof above; 5 `.pyc` files are the complete set of
  unrecoverable content.
- **Final state:** `git worktree list` in all three repositories now lists only
  the canonical checkout. `~/Developer/scratch/worktrees/` retains only the
  unrelated `gpu-ffa-tile12-plan-v2`.

## Owner approvals

The owner approved, on 2026-08-04, terminating PID 30628 and removing all four
directories, with the orphan and worktree directories routed to
`~/Data/Faber2026/_trash/` rather than deleted outright.

## Still prohibited

- Deleting anything under `~/Data/Faber2026/_trash/worktree-consolidation-20260804/`
  or `~/Data/Faber2026/preservation/casey-*-20260804/` without a separate
  approval.
- Resolving the 13-file conflict between `codex/casey-fit-performance-recovery`
  and `main`, or merging pull request #237, without scientific review.
- Deleting branch `codex/casey-fit-performance-recovery` or tag
  `rescue/casey-fit-performance-recovery` while pull request #237 is open.

## Open lanes left untouched

- `Faber2026` `main` is 2 commits ahead of `origin/main`, and its `.gitignore`
  carries an uncommitted `teaching/` rule.
- The canonical `analysis` checkout holds three untracked files:
  `docs/rse/ops/faber2026-reconciliation-map-prototype.html` and the
  `owner-decision-casey-fit-plan-structure` / `owner-decision-casey-fit-runtime-gate`
  wayfinder tickets. None are in `origin/main`.
- The parent's `analysis` gitlink still points at `c02b718`, one commit behind
  the `05904236` landed here. Advancing the pin is a separately scoped step.
