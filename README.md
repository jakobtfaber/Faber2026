# Faber2026

Manuscript: **Scattering, Scintillation, and Energetics of Fast Radio Bursts
Codetected by CHIME/FRB and DSA-110**

This repository is the compact manuscript authority synchronized with Overleaf.
Research-control material and fitting code live in the plain `analysis/`
directory of this repository.

## Layout

```text
main.tex          root manuscript (AASTeX631)
auth.tex          author and affiliation block
sections/         manuscript sections and parked section drafts
figures/          final embedded assets
bib/refs.bib      bibliography
analysis/         research control and fitting code
```

Overleaf compiles only the root TeX, bibliography, generated tables, and final
figure assets. It does not execute the analysis code.

## Start here

Read the
[repository and provenance map](analysis/docs/rse/ops/repository-map.md).
Its repository-boundary descriptions predate consolidation; use the current
root AGENTS.md for that boundary. The map describes the scientific data chain,
authority roles,
and how to trace a manuscript claim, figure, table, or fit to its sources.

## Build

```sh
make
make watch
make clean
```

## Repository maintenance: special refs

Treat these refs as infrastructure, not ordinary development branches:

- `gh-pages` is the GitHub Pages deployment output. The `board/` deployment is
  scoped to that subdirectory; the root contains a separate published deck.
  Agents must not delete it or rewrite its history. Update it only through the
  approved, path-scoped deployment workflow.
- `entire/checkpoints/v1` is an Entire tracing metadata and checkpoint-retention
  ref, not a feature branch. Agents must not delete it, force-push it, or move
  its tip as routine cleanup. Any exceptional change needs separate owner
  approval and a recorded preservation check.

Audit either ref without checking it out or changing a local branch:

```sh
git fetch --no-tags origin \
  refs/heads/gh-pages:refs/remotes/origin/gh-pages \
  refs/heads/entire/checkpoints/v1:refs/remotes/origin/entire/checkpoints/v1
git show --stat --summary refs/remotes/origin/<ref>
git log --oneline --decorate --graph -20 refs/remotes/origin/<ref>
git log --left-right --cherry-pick --oneline \
  origin/main...refs/remotes/origin/<ref>
```

Record the remote tip from `git ls-remote --heads origin <ref>` before and
after an approved operation. For `entire/checkpoints/v1`, also compare the tip
with the Entire checkpoint ledger and do not treat unrelated ancestry as proof
that retained metadata is disposable.

## Research workspace

The current `analysis/` is a plain directory in this repository. Before the
first full provenance check in a clone, prepare the exact historical Git
objects named by the results registry:

```sh
make prepare-provenance
make test-science
```

`prepare-provenance` uses the existing `scripts/fetch_provenance_commits.py`,
as continuous integration does. It fetches missing original analysis commits
from the archived `jakobtfaber/Faber2026-analysis` repository and missing
manuscript commits from `origin`. It changes Git object availability (and fetch
metadata), not the checkout, registry, scientific trust, or data. It requires
network access when objects are missing; rerunning with all objects present
requires no fetch. A failed fetch remains a blocking preparation failure.

Validation remains offline and still checks each full commit identity and
artifact path at that commit. Preparation is explicit, never an implicit
network side effect of a validation command. The archived repository is a
historical evidence source, not an analysis runtime dependency.
