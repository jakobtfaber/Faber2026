# Research: Faber2026 analysis repository split

**Date:** 2026-07-21
**Scope:** Internal codebase and live GitHub state
**State inspected:** `Faber2026` `origin/main` at `a995f37233614d917f9c1ab413f7928b035ae08d`
**Related Documents:** [Overleaf native Git contract](../research/research-overleaf-native-git-contract-2026-07-21.md)

## Question / Scope

Determine the safe boundary between the Overleaf-synchronized manuscript and a
new public `jakobtfaber/Faber2026-analysis` repository mounted at `analysis/`.
The split must preserve analysis history, keep the manuscript build independent
of submodule contents, and reduce the parent below Overleaf GitHub Sync limits.

## Codebase Findings

### Existing repository contract

- `pipeline/` is already an HTTPS git submodule (`.gitmodules:1-3`). Live
  GitHub Sync has therefore demonstrated that the current integration tolerates
  an unexpanded gitlink even though Overleaf documents nested submodules as
  unsupported.
- The repository README already describes a manuscript-root plus analysis
  submodule model and states that Overleaf ignores `pipeline/`
  (`README.md:10-27`). `.olignore:13-19` excludes repository metadata and the
  pipeline from Overleaf's project projection.
- The visible manuscript claims that the repository includes detailed analysis
  products under `analysis/dm-joint-phase-v2/` (`main.tex:113-121`). Mounting
  the new repository at `analysis/` preserves that path locally while requiring
  the prose to identify it as the companion repository rather than material
  available inside Overleaf.

### Exact manuscript boundary

- `main.tex` directly inputs the author block and seven primary sections
  (`main.tex:28,92-97`) and the appendix and bibliography
  (`main.tex:134-141`). Nested section inputs add four manuscript sections and
  generated tables.
- A clean `latexmk -pdf -interaction=nonstopmode -halt-on-error -recorder
  main.tex` build at the inspected commit produced 37 pages and an 8,848,733
  byte PDF. The recorded tracked source closure is 40 files totaling 8,786,229
  bytes: manuscript sources, bibliography/class files, generated root tables,
  eleven compiled section files, and eighteen final PDFs.
- The compile-required editable material is about 0.44 MB. The largest required
  input is the binary `figures/codetection_data_grid.pdf` at 7,433,536 bytes;
  it does not cause the 7 MB editable-text failure.

### Analysis/control boundary

- Strong move candidates comprise `analysis/`, `codetections_polarization/`,
  `data/`, `docs/`, `figure_review/`, `logs/`, `outputs/`, `quarantine/`,
  `scripts/`, and the existing scientific `tests/`: 1,059 tracked paths and
  about 164 MB at the inspected commit.
- Root control/provenance files `CONTEXT.md`, `OWNER_QUEUE.md`, `PIPELINE.md`,
  `REPRODUCE.md`, `language_audit.md`, and `repro_manifest.csv` also belong to
  the analysis workspace. The parent needs short replacements or links only.
- `figures/` contains 213 tracked paths and about 84 MB, while only eighteen
  PDFs are compiled. The remaining figure sources, diagnostics, and historical
  assets belong in the analysis repository. `figures/catalog.yaml` and
  `figures/ax/` remain in the parent because they declare and operate the final
  manuscript figure interface (`figures/catalog.yaml:1-4`), but their producer
  paths must point through `analysis/`.

### Automation coupling

- The current Makefile mixes the LaTeX build (`Makefile:1-16`) with scientific
  tests, figure review, knowledge-base, Running Notes, and Wayfinder commands
  (`Makefile:18-66`). The parent should keep the LaTeX build and delegate the
  other commands to scripts mounted under `analysis/`.
- Both GitHub workflows already initialize submodules recursively
  (`.github/workflows/root-science-tests.yml:20-24`,
  `.github/workflows/table-parity.yml:29-34`). Their paths must be rebased from
  `scripts/` and `tests/` to `analysis/scripts/` and `analysis/tests/` while
  continuing to run from the parent checkout so sibling `pipeline/` and final
  manuscript artifacts remain visible.
- Retained manuscript prose and generated-table comments refer to `scripts/`,
  `docs/`, and analysis products. These references require mechanical updates
  to `analysis/scripts/`, `analysis/docs/`, or the public analysis repository
  URL; compilation does not depend on the comments.

### Git and GitHub state

- The canonical checkout was clean but on the superseded native-Git bridge PR
  branch, four commits ahead and ten behind `origin/main`. The split must use a
  new branch and worktree based directly on current `origin/main`.
- `jakobtfaber/Faber2026-analysis` did not exist. Live `gh api user`
  authentication succeeded as `jakobtfaber`; the parent repository is public,
  so the new analysis repository should also be public.
- `git-filter-repo` is installed. A fresh clone can select the analysis/control
  paths and rewrite `analysis/` to the new repository root without rewriting
  the canonical checkout. The filtered result must be checked with `git fsck`,
  tree inventory, and sample path history before publication.

## Synthesis

The failure is a repository-boundary problem, not a manuscript-size problem.
The stable design is a small Overleaf-synchronized manuscript super-repository
that pins two sibling submodules: `pipeline/` and `analysis/`. The analysis
submodule contains control documents, source products, tests, scripts, review
artifacts, and noncompiled figures. The parent remains the authority for TeX,
generated tables, final embedded figures, and the exact pair of analysis pins.

History preservation requires filtering a fresh clone, publishing the analysis
repository first, then replacing the selected parent paths with a gitlink in a
new parent branch. No force push or canonical-checkout history rewrite is
required. The prior native-Git bridge plan is superseded rather than merged.

## References / Sources

- Code: `.gitmodules:1-3`, `.olignore:13-19`, `README.md:10-27`,
  `main.tex:28,92-121,134-141`, `Makefile:1-66`,
  `.github/workflows/root-science-tests.yml:20-35`,
  `.github/workflows/table-parity.yml:29-60`, `figures/catalog.yaml:1-4`
- External: [Overleaf GitHub synchronization limitations](https://docs.overleaf.com/integrations-and-add-ons/git-integration-and-github-synchronization/github-synchronization#known-limitations),
  [Overleaf plan limits](https://docs.overleaf.com/getting-started/free-and-premium-plans/plan-limits)
