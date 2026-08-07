# Research: Code and manuscript authority surfaces

**Date:** 2026-07-20 13:44 PDT
**Scope:** Internal, read-only audit of the estate paths named in
[`authority-02-reconcile-code-and-manuscript-surfaces.md`](../../wayfinder/tickets/authority-02-reconcile-code-and-manuscript-surfaces.md).
No fetch, pull, checkout, reset, stage, clean, removal, or repository write was
performed. Live GitHub facts came from read-only GitHub REST API calls.

## Question / Scope

What is the evidence-backed relationship among live GitHub, the canonical Mac
checkout, its `pipeline/` submodule and upstreams, the independent Overleaf
checkout, the named Faber2026 and FLITS worktrees, and the named file-only
preservation surfaces? For Git surfaces this audit records identity, branch or
detached commit, divergence, dirt, submodule pin, unique commits/files, and
ownership evidence. File-only directories are identified here only to avoid
mistaking them for repositories; their final role belongs to the separate
classification decision.

The repository knowledge-base command could not run: `scripts/kb` is presently
an empty directory although `Makefile` still invokes `python3 scripts/kb index`
([`Makefile:40-46`](../../../../Makefile)). The permitted fallback was exhaustive
read-only Git and filesystem inspection.

## Method and evidence boundary

Git state was sampled at `2026-07-20T13:44:27-07:00` with:

```sh
git -C <path> rev-parse --show-toplevel --git-dir --git-common-dir HEAD
git -C <path> symbolic-ref -q --short HEAD
git -C <path> remote -v
git -C <path> status --short --branch
git -C <path> rev-list --left-right --count origin/main...HEAD
git -C <path> diff --name-status origin/main...HEAD
git -C <path> ls-tree HEAD pipeline
```

For the independent Overleaf history, tracked trees were compared by pathname
and Git blob identity, which does not require a shared commit ancestor. GitHub
default branches and tips were verified from the repository and branch REST
resources: [Faber2026 repository](https://api.github.com/repos/jakobtfaber/Faber2026),
[Faber2026 main](https://api.github.com/repos/jakobtfaber/Faber2026/branches/main),
[FLITS fork](https://api.github.com/repos/jakobtfaber/dsa110-FLITS),
[FLITS fork main](https://api.github.com/repos/jakobtfaber/dsa110-FLITS/branches/main),
and [FLITS upstream main](https://api.github.com/repos/dsa110/dsa110-FLITS/branches/main).
No remote refs were downloaded into a local repository. Consequently, local
`origin/*` divergence is explicitly described as local-ref evidence; live tips
are reported separately.

## Codebase findings

### 1. Live GitHub and canonical Faber2026

- GitHub's default branch is `main`; its live tip was
  `179ed2bf268cd40d090b4312effee2ec7ce1f61a`.
- The canonical checkout
  `/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026` is the
  same repository (`git@github.com:jakobtfaber/Faber2026.git`), on `main` at
  exactly that commit. Its local `origin/main` also equals HEAD: `0 behind / 0
  ahead`.
- The checkout is not a clean replica: 19 tracked paths were modified and 47
  untracked paths existed at sampling. They span configuration, analysis
  results, provenance, figure-review evidence, manuscript-support files, new
  operational pages, and this authority-ticket lane. This is concurrent local
  ownership, not commit divergence; preserve it.
- HEAD records `pipeline` at `c6111390ce9c159483a844417f5fd9d187e13f5b`.
  The initialized checkout is clean, detached at exactly that pin.

The repository declares the nested repository to be Jakob Faber's FLITS fork,
not the organization upstream ([`.gitmodules:1-3`](../../../../.gitmodules)). Its
policy calls that fork the manuscript pipeline source and says not to retarget
the submodule to the organization repository
([`PIPELINE.md:3-16`](../../../../PIPELINE.md)). It also explains why Overleaf does
not provide the pipeline checkout ([`PIPELINE.md:5-7`](../../../../PIPELINE.md)).

### 2. Pipeline fork, pin, and organization upstream

| Surface | Identity and state | Relationship |
|---|---|---|
| Canonical `pipeline/` | `jakobtfaber/dsa110-FLITS`; detached, clean `c6111390` | Equals the Faber2026 gitlink and its stale local `origin/main` |
| Live fork default branch | `jakobtfaber/dsa110-FLITS`, `main` at `5bf5ac30` | One commit ahead of the manuscript pin |
| Organization upstream | `dsa110/dsa110-FLITS`, `main` at `0cf513b5` | Live fork is 110 commits ahead, 0 behind |
| Standalone Mac clone | same fork; `main` at `fed4a02c` | Local `origin/main` says 93 behind; 11 tracked files dirty; no unique commits versus that local ref |

The single live fork commit beyond the manuscript pin is
`5bf5ac30752fc4a60658b3012939e11e195e46dd`, “analysis: Chromatica (FRB
20240203A) end-to-end re-analysis record (#209).” Its 19 changed files are all
under `analysis/chromatica-e2e-2026-07-20/`, so it does not change pipeline code,
but it does add analysis evidence. The current Faber2026 pin therefore remains
content-behind the fork by that bounded analysis record; advancing the pin is
still a reviewed manuscript provenance decision, as the pin policy requires
([`PIPELINE.md:20-36`](../../../../PIPELINE.md)).

The standalone clone's dirt is substantive: crossmatching code/results,
codetection data loading, scintillation core/guards, and tests. Its current
branch is 93 commits behind its local fork-main ref. It is neither a clean
replica nor a safe source for an unqualified pin update.

### 3. Independent Overleaf checkout

`/Users/jakobfaber/Developer/overleaf/Faber2026` is a separate, clean Git
checkout with the same configured remote, on `main` at `25c8ca78545e`. The
project instructions explicitly warn that it syncs independently and must be
ordered carefully relative to GitHub ([`AGENTS.md:78-81`](../../../../AGENTS.md)).

Its history is not merely behind:

- HEAD and its stale local `origin/main` have no merge base with the canonical
  repository's current history.
- The live GitHub API returns “No commit found” for `25c8ca78`; that object is
  not available from the current GitHub repository.
- Tree comparison against canonical `179ed2bf` finds 1,030 canonical-only
  paths, 57 Overleaf-only paths, 196 common paths, and 89 common paths with
  different blobs.
- All 57 Overleaf-only paths are local history content: 55 under `docs/` and 2
  under `codetections_polarization/`. They include old research handoffs,
  fit/contact-sheet artifacts, and `codetections_polarization/main.pdf` plus its
  ZIP; they are not proof that Overleaf has newer manuscript prose.
- The 89 changed common paths include `main.tex`, 11 `sections/*.tex` files,
  bibliography and generated tables, 12 association cards, 12 joint-model
  figure sets, the host-dispersion-measure figure, and the sightline-halo grid.
- Its recorded gitlink is the older `9017707e`; the initialized nested checkout
  is clean and detached there. This does not alter the policy fact that
  Overleaf's bridge ignores submodules ([`PIPELINE.md:5-7`](../../../../PIPELINE.md)).

Therefore Overleaf is an independent, history-orphaned manuscript working copy,
not a fast-forwardable GitHub replica. Any propagation must reconcile the 89
changed common paths and decide whether any of the 57 Overleaf-only paths remain
valuable. A blind pull, push, or merge cannot establish authority.

### 4. Registered Faber2026 worktrees

Counts below are against the canonical repository's local `origin/main` at
`179ed2bf`; “dirty” separates modified tracked paths from untracked paths.

| Path / branch | HEAD; divergence | Dirt | Unique committed content and ownership evidence |
|---|---|---|---|
| `.worktrees/review-prose-89` / `ms/review-prose-20260715` | `1e689335`; 126 behind, 0 ahead | 99 tracked, 0 untracked | No unique commits. Despite the old handoff calling it clean after merged PR #89, it now carries broad concurrent modifications across context, research documents, scripts, results, and manuscript sections. Current dirt outranks the old label. |
| `Faber2026-jointtf-grok-revalidation` / `rse/jointtf-grok-harvest-revalidation` | `1e451ad3`; 11 behind, 6 ahead | clean | 6 unique commits, 60 changed paths: JointTF v2 revalidation docs, roster, triptychs, fit artifacts, scripts, tests. This is the explicitly named dedicated revalidation lane in the current handoff ([`handoff-2026-07-19-23-24-jointtf-grok-harvest-revalidation.md:149`](../handoff/handoff-2026-07-19-23-24-jointtf-grok-harvest-revalidation.md)). |
| `Faber2026-overleaf-20260720-0837` / `reconcile/overleaf-2026-07-20-0837` | `2ded8ffd`; 6 behind, 0 ahead | clean | No unique commit or file versus local main. It is a clean reconciliation worktree, not the independent Overleaf checkout itself. |
| `Faber2026-quarantine-20260717` / `ms/quarantine-outdated-science-20260717` | `a66816fe`; 59 behind, 5 ahead | clean | 5 unique commits, 19 paths. Moves three provisional tables into quarantine, changes manuscript references/tests/provenance, and pins FLITS `23fbd295`. Preserve until its science-disposition owner resolves it. |
| `Faber2026-science-gates` / `ms/science-gates-g1a-20260715` | `6889effc`; 91 behind, 0 ahead | 1 modified submodule, 10 untracked | No unique superproject commits, but unique untracked results-library documents plus dirty FLITS code. Its preservation packet says the worktree remains active and enumerates six unique superproject files plus real tau-consistency code (`/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-science-gates-preserve/PROVENANCE.md:3-24`). |
| `Faber2026-scint-2l` / `ms/scint-joint-candidate-20260717` | `b3bddaa4`; 69 behind, 4 ahead | clean | 4 unique commits, 70 paths: candidate review batch, provenance, summary builder, review tooling, tests; pins FLITS `17d9d266`. The branch is gone remotely, so the registered worktree is the named local holder. |

The parent gitlink differs across these historical science lanes (`f9d7dfe0`,
`23fbd295`, `af78543d`, and `17d9d266`). Their manuscript changes and their
pipeline pins must be evaluated together; treating only the superproject diff
would sever provenance.

### 5. FLITS worktrees and preserved FLITS lanes

| Path / branch | HEAD; divergence from local fork `origin/main` | Dirt | Unique content / custody |
|---|---|---|---|
| `pipeline-archive-historical-diagnostics-20260720` / `codex/archive-historical-diagnostics-20260720` | `c505d073`; 0 behind, 1 ahead | clean | One unique commit, 94 paths: an active archival-diagnostics change. It is registered under the canonical submodule's Git directory. |
| `flits-joint-tf-fits` / `joint/tf-fit-window-resolution` | `5cffcb39`; 28 behind, 5 ahead | 2 tracked | Five unique commits, 10 paths for PL-PBF, relaxed-alpha comparison, time-of-arrival corrections, and fit-speed kernels. Dirty `scattering/scat_analysis/burstfit.py` plus checkpoint ledger means the committed branch does not capture the full lane. Registered under the standalone FLITS clone. |
| `FLITS-quarantine-20260717` / `agent/quarantine-outdated-science-20260717` | `9ddb4def`; 16 behind, 1 ahead | clean | One unique commit, 19 paths; paired pipeline quarantine lane for the Faber quarantine worktree. Registered under the canonical submodule Git directory. |
| `flits-gate-preserve` | file-only preservation packet | n/a | Explicitly preserves a removed dirty `feat/joint-fit-gate` worktree: 88 KB tracked patch and 3.8 MB untracked archive. Its two PRs closed unmerged, exact artifacts are absent from main, and its source says HOLD (`/Users/jakobfaber/Developer/scratch/worktrees/flits-gate-preserve/PROVENANCE.md:3-26`). |
| `flits-scint-rescue-preserve` | file-only evidence archive | n/a | Preserves 32 ignored/generated files from `scint/reference-arc-rescue` at `9237e4c`; code merged upstream as PR #51, evidence archive has a recorded SHA-256 (`/Users/jakobfaber/Developer/scratch/worktrees/flits-scint-rescue-preserve/PROVENANCE.md:3-15`). |

These are two different worktree families. The archive/quarantine worktrees
share the canonical submodule Git directory; `flits-joint-tf-fits` shares the
standalone clone's Git directory. They are separate checkouts even when commits
are shared. The repository already records this non-interchangeability
([`handoff-2026-07-08-22-49-flits-pipeline-commits-and-repo-state.md:129-147`](../handoff/handoff-2026-07-08-22-49-flits-pipeline-commits-and-repo-state.md)).

### 6. Named non-worktree surfaces

| Surface | Repository identity / contents | Authority consequence |
|---|---|---|
| `Faber2026-science-gates-preserve` | Not Git. Provenance plus tracked patch and two tar archives. | Safety copy of still-active, unique superproject and FLITS work; source says HOLD until landed or abandoned (`/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-science-gates-preserve/PROVENANCE.md:26-35`). |
| `Faber2026-lane-preserve-20260717` | Not Git. Provenance plus three results-library files. | Its source identifies older Phase-A snapshots and requires owner confirmation before disposal (`/Users/jakobfaber/Developer/scratch/Faber2026-lane-preserve-20260717/PROVENANCE.md:1-27`). |
| `faber2026-cursor-rewrite/Faber2026.git` | Bare same-remote repository; `main` `81601263`, 22 branches, tree `eaa4ebba`; pin `75cb2a8d`. | History-rewrite staging repository, not a checkout. |
| `faber2026-full-contributor-scrub/Faber2026.git` | Bare same-remote repository; `main` `6f655af9`, 22 branches, the same tree `eaa4ebba`; pin `75cb2a8d`. | A second rewritten-history repository. Different commit identities but byte-identical main trees prove these are rewrite artifacts, not independent manuscript trees. |
| `Faber2026-logs` | Not Git; agent transcripts, prompts, result JSON, and closeout logs. | Evidence/log surface only; no branch, pin, or manuscript tree. |
| `faber_build` | Empty directory at sampling. | No code or manuscript identity was present. Emptiness alone is not removal authorization. |
| `scratch/kulkarni-profile/Faber2026` | Not a Faber2026 Git checkout. It is an untracked subdirectory inside unrelated repository `kulkarni-profile`; contains two Markdown reports. | Do not count as a manuscript clone or merge it through Faber2026 Git. |
| `~/handoffs` | Not Git; mixed Faber2026/FLITS handoffs, scripts, JSON/CSV evidence, encoded code, and figure-reproduction material. | File-level evidence/staging surface only; requires artifact-by-artifact reconciliation. |
| `~/Backups/faber2026-integrate-dsa-acf-push-20260708.*` | README plus thin Git bundle holding tag `archive/integrate-dsa-acf-push-20260708` at `c0760602`. | Recoverable branch archive. Its README says the deleted branch was reviewed as duplicate/regressive and gives restoration prerequisites (`/Users/jakobfaber/Backups/faber2026-integrate-dsa-acf-push-20260708.README.md:1-20`). |

## Synthesis

1. **Current GitHub manuscript commit authority is unambiguous, but the local
   working tree is not clean.** Live `main`, canonical HEAD, and canonical
   `origin/main` all equal `179ed2bf`. Commit authority does not erase 66 local
   dirty/untracked paths with concurrent ownership.
2. **The reproducibility pin is precise but one analysis commit behind fork
   main.** Canonical Faber2026 and its clean submodule agree on `c6111390`.
   Fork `main` adds only the named Chromatica analysis record at `5bf5ac30`; the
   organization upstream is contained by the fork at the sampled live refs.
3. **Overleaf is the central manuscript hazard.** It is clean, but clean means
   only internally unmodified. Its HEAD is absent from current GitHub history,
   it has no shared history with the current canonical checkout, and its tree
   differs in manuscript prose and figures. It must be reconciled as a separate
   content source, never treated as “GitHub but behind.”
4. **Unique code/manuscript work remains distributed.** The JointTF,
   quarantine, scintillation candidate, archive-diagnostics, and joint-fit lanes
   contain unique commits. Review-prose, science-gates, standalone FLITS, and
   joint-fit lanes contain dirt. Preservation packets carry additional unique
   files from removed or active worktrees.
5. **No consolidation action is supported by this evidence alone.** The next
   authority decision must name, at minimum, how to reconcile Overleaf's 89
   changed common paths; whether to land or supersede each unique branch; how to
   preserve current dirt; and whether the single analysis-only FLITS advance
   should become the next manuscript pin.

## References / sources

- Live GitHub REST resources linked in “Method and evidence boundary.”
- Repository identity and pin policy:
  [`.gitmodules`](../../../../.gitmodules), [`PIPELINE.md`](../../../../PIPELINE.md),
  [`AGENTS.md`](../../../../AGENTS.md).
- Preservation provenance:
  `/Users/jakobfaber/Developer/scratch/worktrees/Faber2026-science-gates-preserve/PROVENANCE.md`,
  `/Users/jakobfaber/Developer/scratch/worktrees/flits-gate-preserve/PROVENANCE.md`,
  `/Users/jakobfaber/Developer/scratch/worktrees/flits-scint-rescue-preserve/PROVENANCE.md`,
  and `/Users/jakobfaber/Developer/scratch/Faber2026-lane-preserve-20260717/PROVENANCE.md`.
- Local Git observations are reproducible with the commands recorded above and
  the exact paths and commits in each table. Divergence may change as concurrent
  agents continue working; no local ref was refreshed during this audit.
