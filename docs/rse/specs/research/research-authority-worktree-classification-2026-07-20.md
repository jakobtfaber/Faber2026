# Research: Local worktrees and preservation packets

**Date:** 2026-07-20
**Scope:** Internal, read-only filesystem and Git metadata audit
**Repository state:** Faber2026 `179ed2bf` (`main`, equal to local `origin/main`)
**Related:** [authority-03 ticket](../../wayfinder/tickets/authority-03-classify-worktrees-and-preservation-packets.md)

## Question and limits

Classify the ticket-listed local paths as registered Git worktrees, independent
repositories, preservation packets, generated builds/logs, or ordinary working
directories. Record identity, dirt, likely unique material, active ownership,
and the gate for any later consolidation.

This audit made no network calls and did not mutate, stage, clean, remove, or
extract anything. Commit comparisons use the locally cached `origin/main` refs.
Ignored-file review was bounded to counts and representative names. “No matching
process” means a process-name scan at audit time, not proof that no editor or
agent has the path open. Nothing below is deletion-approved.

## Summary

- Six `Faber2026` worktrees are registered to the parent checkout. Two are
  dirty; three clean worktrees still point to commits not present on local
  `origin/main`.
- Four pipeline-related worktrees are registered: three to the `pipeline/`
  submodule Git directory and one to the independent `dsa110-FLITS` clone. One
  is dirty; two clean lanes have unique commits; one is patch-equivalent to main
  but contains more than 21,000 ignored files.
- Four non-Git preservation directories contain explicit provenance and unique
  evidence. Their own disposal rules remain binding.
- The two `2026-07/faber2026-*` directories are independent bare repositories,
  apparently history-rewrite products. They are not working trees.
- The remaining paths are ordinary analysis, migration, handoff, build, or log
  directories. Several contain untracked source, measurements, or decision
  records and must not be treated as disposable cache.

Remote mapping: parent worktrees use `git@github.com:jakobtfaber/Faber2026.git`;
submodule worktrees use `https://github.com/jakobtfaber/dsa110-FLITS.git` with
`dsa110/dsa110-FLITS` as upstream; the independent FLITS worktree uses the same
fork over SSH and has upstream push disabled; the skill worktree uses
`git@github.com:jakobtfaber/my-skillset.git`.

## Registered Git worktrees

| Path | Git identity and state | Unique or ignored material | Consolidation gate |
|---|---|---|---|
| `~/Developer/repos/github.com/jakobtfaber/Faber2026/.worktrees/review-prose-89` (180 MB) | Registered to parent `.git`; branch `ms/review-prose-20260715` at `1e689335`; configured remote branch is gone. HEAD is in local `origin/main` and is 126 commits behind. **Dirty: 99 modified tracked files**, spanning context, measurements/results, many research and handoff records, logs, scripts, figure-fit settings, and manuscript sections. | No branch-only commits and no ignored files. The 99 working-tree modifications are the unique-risk surface; this audit did not interpret or diff them because that would exceed the bounded classification pass. | **Hold.** Assign an owner and partition all 99 edits by content. Land, explicitly abandon, or independently preserve each change; validate science/result edits separately from prose. Only then confirm no active owner and remove through Git worktree machinery. |
| `~/Developer/scratch/worktrees/Faber2026-jointtf-grok-revalidation` (735 MB) | Registered to parent `.git`; branch `rse/jointtf-grok-harvest-revalidation` at `1e451ad3`; no upstream configured, but `origin/rse/jointtf-grok-harvest-revalidation` contains the commit; tracked and untracked state clean. | Six commits are absent from local `origin/main` (`git cherry` reports all six as unique). 85 ignored files, represented by `.kb/kb.sqlite3`, test/lint caches, Python bytecode, and LaTeX build products. | **Hold.** Land or explicitly abandon/preserve the six commits; separately decide whether the knowledge-base database and generated manuscript build are reproducible. Then confirm no active owner and remove through Git worktree machinery. |
| `~/Developer/scratch/worktrees/Faber2026-overleaf-20260720-0837` (183 MB) | Registered to parent `.git`; branch `reconcile/overleaf-2026-07-20-0837` at `2ded8fff`, tracking `origin/main`; clean; six commits behind. HEAD is an ancestor of local `origin/main`. | Eight ignored LaTeX build files, including `main.pdf`; no untracked files. | **Candidate only, not approved.** Confirm the Overleaf reconciliation lane is closed and the ignored build is reproducible or intentionally retained; confirm no active owner; then remove through Git worktree machinery. |
| `~/Developer/scratch/worktrees/Faber2026-quarantine-20260717` (731 MB) | Registered to parent `.git`; branch `ms/quarantine-outdated-science-20260717` at `a66816fe`; clean; configured remote branch is gone. | Five commits are not ancestors or patch-equivalent commits of local `origin/main`. 69 ignored files, mainly caches, Python bytecode, and LaTeX output. | **Hold.** Reconcile the five commits against the quarantine pull request/main by content, not commit ancestry alone; preserve or land any remaining changes. Then assess ignored output and confirm owner release. |
| `~/Developer/scratch/worktrees/Faber2026-science-gates` (589 MB) | Registered to parent `.git`; branch `ms/science-gates-g1a-20260715` at `6889effc`; HEAD is in local `origin/main` and is 91 commits behind. Dirty: modified `pipeline` plus ten untracked results-library, plan, handoff, and script paths. | Six superproject files were captured by the preservation packet below. Four other untracked paths were recorded as already on main. Current submodule dirt was not recursively re-audited; packet provenance records five tracked code changes and nine untracked results-library files at capture time. | **Hold.** Land or explicitly abandon the science-gates work. Recompare current superproject and submodule dirt with the packet, because a 2026-07-17 packet is not proof that later edits are captured. Owner spot-check/science gates still apply. |
| `~/Developer/scratch/worktrees/Faber2026-scint-2l` (698 MB) | Registered to parent `.git`; branch `ms/scint-joint-candidate-20260717` at `b3bddaa4`; clean; configured remote branch is gone. | Four commits are absent and not patch-equivalent to local `origin/main`. 53 ignored files, mainly caches, bytecode, and LaTeX output. | **Hold.** Reconcile or preserve the four candidate-review commits; verify ignored review/build artifacts are reproducible; obtain lane-owner release. |
| `~/Developer/scratch/worktrees/flits-joint-tf-fits` (99 MB) | Registered worktree of the independent `~/Developer/repos/github.com/jakobtfaber/dsa110-FLITS` clone; branch `joint/tf-fit-window-resolution` at `5cffcb39`, equal to its remote branch. Dirty tracked files: `docs/entire-tracing-checkpoints.md` and `scattering/scat_analysis/burstfit.py`. | Five commits are absent and not patch-equivalent to local pipeline `origin/main`. 90 ignored files include generated JointTF figures, logs, caches, and bytecode. | **Hold.** Resolve the two tracked edits, land/preserve or reject the five commits, and inventory generated JointTF figures before owner release. |
| `~/Developer/scratch/worktrees/FLITS-quarantine-20260717` (558 MB) | Registered to the Faber2026 `pipeline/` submodule Git directory; branch `agent/quarantine-outdated-science-20260717` at `9ddb4de`; clean and equal to its remote branch. `git cherry` marks the commit patch-equivalent to local pipeline `origin/main`. | 21,303 ignored files; representative paths are `.venv`, test cache, and agent log files. A bounded sample did not establish whether all ignored files are reconstructible. | **Candidate only, not approved.** Confirm the quarantine lane/remote branch can close, and prove no ignored scientific output exists beyond reconstructible environment/cache/log data. Confirm no active owner, then remove through Git worktree machinery. |
| `~/Developer/scratch/worktrees/pipeline-archive-historical-diagnostics-20260720` (546 MB) | Registered to the Faber2026 `pipeline/` submodule Git directory; branch `codex/archive-historical-diagnostics-20260720` at `c505d07`; clean; one commit ahead of local pipeline `origin/main`. | The one commit is unique by ancestry and patch comparison. 21,322 ignored files, represented by `.venv`, test/lint caches, and agent logs; full ignored uniqueness unverified. | **Hold.** Land or preserve the archive commit; verify its intended submodule pin/consumer; audit ignored scientific outputs; confirm lane-owner release. |
| `~/Developer/scratch/recovery/flits-window-tuning-ae67bdf` (551 MB) | Registered to the Faber2026 `pipeline/` submodule Git directory; branch `codex/chromatica-cross-band-scintillation` at `3feb82e`; clean; the remote branch exists. Relative to local pipeline `origin/main`, it is 19 commits behind and four ahead. | Four commits are absent and not patch-equivalent to local pipeline `origin/main`. 20,613 ignored files, represented by `.venv`, test/lint caches, bytecode, and agent logs; scientific-output uniqueness was not exhaustively checked. The `recovery` path is itself a preservation/ownership signal. | **Hold.** Treat as an active recovery lane: reconcile or preserve all four commits, audit ignored Chromatica/window-tuning outputs, identify the recovery owner and intended consumer, then obtain explicit release before Git worktree removal. |
| `~/Developer/scratch/worktrees/my-skillset-mattpocock-install` (18 MB) | Registered to `my-skillset`; branch `chore/install-mattpocock-skills` at `f233afc`; clean; no upstream. HEAD is already in local `my-skillset` `origin/main`. | 149 ignored files. Most are caches/bytecode, but `.skill-backups/` contains timestamped pre-install skill copies and is not proven redundant. | **Candidate only, outside Faber2026 authority.** `my-skillset` owner must decide whether `.skill-backups/` remain needed and release the worktree. Do not remove from this repo’s cleanup wave. |

## Preservation packets

| Path | Classification and evidence | Consolidation gate |
|---|---|---|
| `.../worktrees/Faber2026-science-gates-preserve` (56 KB) | Non-Git safety/handoff packet. `PROVENANCE.md` names source commits and restore commands. It contains superproject status, six unique untracked files in a tar archive, pipeline status, a tracked patch, and nine pipeline untracked files in a tar archive. No checksum manifest is present. | **Hold.** Its stated rule requires the science-gates work to be committed/landed or explicitly abandoned. Before relying on it, add independent integrity/restore proof and compare it with current worktree dirt. |
| `.../worktrees/flits-gate-preserve` (3.9 MB) | Non-Git pre-removal snapshot: status, 88 KB tracked patch, 3.8 MB untracked archive, and provenance. It records a removed `feat/joint-fit-gate` worktree whose pull requests were closed unmerged; exact Phase-1 artifacts were absent from main at the 2026-07-01 audit. No checksum manifest is present. | **Hold.** Its stated rule requires a domain decision that the five missing posterior-predictive-check JSON files and component/shared-zeta outputs are regenerable or deliberately landed. |
| `.../worktrees/flits-scint-rescue-preserve` (1.6 MB) | Non-Git evidence archive for merged branch `scint/reference-arc-rescue` at `9237e4c`; 32 ignored logs/results/diagnostics. `SHA256SUMS` verification passed during this audit. | Retain as evidence until the reference-arc result has an authoritative, independently restorable home and the science owner accepts that the evidence need not remain as a standalone packet. |
| `~/Developer/scratch/Faber2026-lane-preserve-20260717` (52 KB) | Non-Git file-level safety copy from the main checkout. Provenance says three initially divergent files are older Phase-A snapshots superseded by merged work, but still requires lane-owner confirmation. | **Hold pending results-library owner confirmation** that the three older copies are superseded. No checksum manifest or restore test was found. |

## `Developer/scratch/2026-07`

| Path | Classification and evidence | Consolidation gate |
|---|---|---|
| `batchc-icloud-move` (12 KB) | Ordinary migration continuation kit, not Git: two scripts plus `CONTINUATION.md`. It records an incomplete 31.5 GB iCloud-to-Data migration and an explicit destructive symlink-replacement stop. Not Faber2026-specific. | **Hold.** Complete materialization/copy verification or explicitly abandon it; preserve the continuation record. Replacing iCloud originals remains a separate owner-approved action. |
| `chromatica-dm-window-review` (82 MB) | Ordinary analysis workspace, not Git. Contains scripts, notebook, manual-window JSON/CSV, sweep cache, PDF/SVG/PNG reviews, HTML deck, and a manifest linking the authoritative Faber2026 fit file. | **Hold.** Reconcile manual envelopes and review conclusions into the repository’s fitting/results inventory; prove generated panels are reproducible; preserve any owner eye-set windows. |
| `faber2026-cursor-rewrite/Faber2026.git` (198 MB) | Independent bare repository, remote `git@github.com:jakobtfaber/Faber2026.git`; `main` at rewritten identity `8160126`; 3,584 packed objects. No worktree dirt exists in a bare repository. Purpose inferred from name; no local provenance note found. | **Hold/unverified.** Identify the history-rewrite procedure and consumer, compare every rewritten ref with the accepted contributor-history result, and retain a recoverable pre/post mapping before removal. |
| `faber2026-full-contributor-scrub/Faber2026.git` (198 MB) | Independent bare repository with the same remote; `main` at rewritten identity `6f655af`; 3,656 packed objects. Its refs differ from the cursor rewrite. Purpose inferred from name; no local provenance note found. | **Hold/unverified.** Establish which rewrite, if either, is authoritative; verify contributor metadata and retain a ref/object backup before consolidation. |

## Other build and log directories

| Path | Classification | Consolidation gate |
|---|---|---|
| `~/Developer/scratch/faber_build` (0 B) | Empty ordinary build directory; not Git. | Candidate only after confirming no process expects the path. No matching named process was seen. |
| `~/Developer/scratch/flits_pr_build` (44 KB) | Ordinary source/build staging directory; four files (`auto_rfi_flag.py`, `build_window_notebook.py`, `window_refit.py`, `window_tuning.ipynb`). Not a generated-only directory by evidence. | **Hold.** Diff all four against pipeline/main and the active recovery/worktree lanes; land or preserve unique source/notebook work. |
| `~/Developer/scratch/Faber2026-logs` (5.2 MB) | Ordinary delegation/audit log directory; prompts, standard output/error logs, model results, JSON audits, and a closeout packet. Not Git. | **Hold pending provenance review.** Link any decision-bearing audits/results from repo-local handoffs; check for sensitive/transient content; then owner decides retention. |

## Kulkarni profile, handoffs, and backup

| Path | Classification and evidence | Consolidation gate |
|---|---|---|
| `~/scratch/kulkarni-profile/Faber2026` (40 KB) | Ordinary subdirectory inside an independent Git repository rooted at `~/scratch/kulkarni-profile`, branch `main` at `cdd391b`. The parent repository has no configured remote. Both Faber2026 Markdown reports are untracked; other untracked prompts, code, and logs exist beside them. | **Hold.** Decide the authoritative home for both manuscript reports, commit or copy them with the associated prompts/method, and establish repository backup/remote custody. |
| `~/handoffs` (2.7 MB) | Ordinary mixed handoff staging directory, not Git. Faber2026/FLITS material includes manuscript handoffs, author decisions, code encoded as base64, run YAML/shell files, provenance/reproduction manifests, figure data, virial-radius diagnostics, and time-of-arrival reconstruction code/results. | **Hold.** Inventory each packet against repo-local `docs/rse/specs/`, pipeline code, and results. Promote unique source/data/provenance; verify hashes or reproducibility; only then classify individual files. Directory-wide deletion is unsafe. |
| `~/Backups/faber2026-integrate-dsa-acf-push-20260708.bundle` (1.2 MB) plus README | Valid thin Git preservation bundle. Live `git bundle verify` passed. It contains annotated tag `archive/integrate-dsa-acf-push-20260708` and requires commits `29c00b3` and `7478397`; README records a successful fresh-clone restore and an intentional discard decision for the old branch. No other Faber2026-named backup was found within three levels of `~/Backups`. | Preserve as the documented fallback unless backup policy explicitly retires it after confirming the annotated tag, prerequisite commits, and an independent verified backup remain available. |

## Active ownership evidence

A bounded process-name scan found no command line containing the listed
worktree/scratch names. This does **not** release ownership: IDEs and agents may
hold directories without spelling the path in their process command. Branch
names, provenance files, dirty state, remote refs, and named lane owners remain
the stronger ownership signals. Every candidate removal therefore still needs
an explicit current-owner check.

## Deletion policy inferred from the evidence

No directory is deletion-approved by this research. A later consolidation wave
must satisfy all applicable gates:

1. Git worktree is clean, or every tracked/untracked change is landed,
   explicitly abandoned, or independently preserved and restore-tested.
2. Every commit absent from the authoritative main branch is reconciled by
   content. Squash/rebase history requires patch or tree comparison, not branch
   ancestry alone.
3. Ignored scientific outputs, owner-set windows, logs, and skill backups are
   inventoried separately from reconstructible caches/environments/builds.
4. Preservation packets pass checksum and restore checks and have an accepted
   authoritative destination; packet-specific disposal rules are satisfied.
5. No active agent/process/lane owns the path, and the owner explicitly releases
   decision-bearing or scientifically unique material.
6. Registered worktrees are removed through their owning Git repository; bare
   repositories and ordinary directories are never treated as worktrees.

## Evidence commands

Read-only commands used: `git worktree list --porcelain` for the parent,
pipeline, independent FLITS clone, and my-skillset; `git status --short
--branch`; `git rev-parse`; `git rev-list --left-right --count`; `git cherry`;
`git branch -r --contains`; `git ls-files --others --ignored
--exclude-standard`; bounded `find`, `stat`, and `du`; `tar -tzf`; `shasum -c`;
`git bundle verify`; and a bounded process-name scan.
