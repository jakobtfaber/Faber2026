# Implementation Plan: Split Faber2026 analysis workspace

---
**Date:** 2026-07-21
**Author:** Codex
**Status:** In Progress
**Related Documents:**
- [Research: Faber2026 analysis repository split](research-faber2026-analysis-split.md)
---

## Overview

Create public repository `jakobtfaber/Faber2026-analysis`, preserve selected
history with `git-filter-repo`, and mount it at `analysis/` in `Faber2026`.
Retain a fail-closed manuscript projection in the parent: all TeX sources,
generated root tables, bibliography/class files, final compiled figures,
figure catalog, minimal automation, and exact `pipeline/` and `analysis/` pins.

**Goal:** Restore reliable Overleaf GitHub Sync without losing the navigable
research-control workspace or its provenance.

**Motivation:** The manuscript closure is about 8.8 MB total and 0.44 MB
editable, while research/control material makes the repository about 257 MB and
exceeds Overleaf's 7 MB editable-text limit.

## Current State Analysis

- `.gitmodules:1-3` — one working `pipeline/` gitlink.
- `main.tex:28,92-97,134-141` — root compile graph.
- `Makefile:1-66` — manuscript build and analysis operations are mixed.
- `.github/workflows/root-science-tests.yml:20-35` and
  `.github/workflows/table-parity.yml:29-60` — CI already checks out submodules
  recursively but assumes analysis scripts/tests at the parent root.
- `figures/catalog.yaml:1-4` — parent-side final-figure contract.

## Desired End State

`Faber2026` contains manuscript sources, final embedded figure assets, a small
boundary manifest/checker, and sibling gitlinks `pipeline/` and `analysis/`.
`Faber2026-analysis` contains the existing analysis products, control docs,
scripts, tests, figure-review state, and noncompiled figure assets. Parent CI
runs analysis tools from the mounted submodule while testing the exact pinned
pair.

## What We're NOT Doing

- Rewriting or force-pushing `Faber2026` history.
- Moving any file observed in the current tracked LaTeX source closure.
- Moving final embedded figure PDFs out of the parent.
- Changing scientific results, generated table contents, or manuscript claims
  beyond repository-location wording.
- Merging the superseded native-Git bridge PR.
- Depending on Overleaf to initialize either submodule.

## Implementation Approach

1. Filter a fresh clone, never the canonical checkout.
2. Flatten the old parent `analysis/` contents into the new repository root so
   local paths such as `analysis/dm-joint-phase-v2/` remain stable.
3. Preserve broad figure history in the analysis repository, then remove the
   current copies of final parent-owned assets from its tip.
4. Publish and validate the analysis repository before creating the parent
   gitlink.
5. Enforce the parent boundary with a machine-readable allowlist and automated
   size/compile checks.

## Implementation Phases

### Phase 1: Record and test the boundary

**Objective:** Make the intended split executable before moving files.

**Tasks:**

- [x] Add `manuscript-boundary.txt` listing the retained compile inputs and parent
  operational files, one path per line.
- [x] Add `tests/test_manuscript_boundary.py` asserting that `pipeline` and
  `analysis` are mode `160000`, forbidden control directories are absent from
  the parent, retained files exist, parent editable text is below 7,000,000
  bytes, and the parent tree is below 100,000,000 bytes.
- [x] Run `python3 -m pytest tests/test_manuscript_boundary.py -q` before the split;
  expect failure because `analysis/` is still a directory and the control paths
  remain in the parent.

**Verification:** The test fails only on the stated pre-migration invariants.

### Phase 2: Extract and publish analysis history

**Objective:** Create the analysis repository without altering parent history.

**Tasks:**

- Fresh-clone the migration branch into a temporary directory.
- Run `git filter-repo --dry-run` selecting `analysis/`,
  `codetections_polarization/`, `data/`, `docs/`, `figure_review/`, `figures/`,
  `logs/`, `outputs/`, `quarantine/`, `scripts/`, `tests/`, and root
  control/provenance files; apply `--path-rename analysis/:`.
- Inspect `.git/filter-repo/fast-export.filtered` for the selected path set.
- Repeat in a fresh clone without `--dry-run`; remove final parent-owned assets,
  `figures/catalog.yaml`, and `figures/ax/` from the analysis tip while retaining
  their history.
- Add an analysis README, `.gitignore`, and Makefile documenting the required
  mount at `Faber2026/analysis` and sibling `../pipeline` contract.
- Run `git fsck --full`, compare current selected-file hashes, and verify sample
  history with `git log --follow -- docs/rse/control/BOARD.md`.
- Create public repository with
  `gh repo create jakobtfaber/Faber2026-analysis --public --source <filtered> --remote origin --push`.

**Verification:** Remote `main` equals the validated local filtered commit and
fresh cloning succeeds.

### Phase 3: Replace parent paths with the analysis gitlink

**Objective:** Produce the minimal synchronized parent tree.

**Tasks:**

- Remove the selected analysis/control paths and all non-allowlisted figure
  assets from the migration branch using path-specific `git rm` commands.
- Add `https://github.com/jakobtfaber/Faber2026-analysis.git` at `analysis/`.
- Rewrite `README.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.gitignore`,
  `.olignore`, and `Makefile` for the two-submodule boundary.
- Update retained manuscript comments/prose and generated-table provenance paths
  from `scripts/`/`docs/` to `analysis/scripts/`/`analysis/docs/` or the public
  repository URL.
- Update parent workflows to use `analysis/tests/` and `analysis/scripts/` while
  checking out both submodules recursively.
- Run the boundary test; expect pass.

**Verification:** `git ls-tree HEAD analysis pipeline` reports mode `160000` for
both and no retained TeX dependency is inside either gitlink.

### Phase 4: Validate and publish

**Objective:** Prove the split preserves the manuscript and repository contract.

**Tasks:**

- Run `latexmk -C` then
  `latexmk -pdf -interaction=nonstopmode -halt-on-error -recorder main.tex`.
- Compare PDF page count and inspect source closure; require 37 pages and no
  inputs under `analysis/` or `pipeline/`.
- Run parent boundary tests and analysis scientific tests from the mounted
  checkout.
- Run `make kb-index` through the analysis-mounted command.
- Run `agent-closeout-check` for both repositories with explicit touched paths
  and dirty-state packets.
- Commit/push analysis first, then commit/push the parent branch and open a
  focused pull request. Close PR #172 as superseded without deleting its branch.

**Verification:** Both remotes contain the reported commits; parent checks pass;
the pull request is open and scoped to the split.

## Success Criteria

### Automated Verification

- `python3 -m pytest tests/test_manuscript_boundary.py -q` passes.
- `latexmk` produces a 37-page PDF without reading either submodule.
- Parent editable material is below 7,000,000 bytes and total tree bytes below
  100,000,000 bytes.
- `git ls-tree HEAD analysis pipeline` reports two gitlinks.
- `git -C analysis fsck --full` and parent `git fsck --full` pass.
- Fresh clones with `--recurse-submodules` resolve both public repositories.

### Manual Verification

- Overleaf GitHub Sync pulls the migration successfully.
- Overleaf recompiles the project and shows the expected 37-page manuscript.

## Testing Strategy

The boundary test is written before migration and must fail on the old layout,
then pass after the split. Existing scientific tests run from the parent with
their paths rebased through `analysis/`, preserving access to the exact pipeline
pin and manuscript artifacts. The final clean LaTeX build is the integration
test for the manuscript projection.

## Migration Strategy

Publish the analysis remote first. Parent removal and gitlink addition occur in
one branch but may be split into GitHub commits below 100 changed paths if live
Overleaf Sync requires incremental pulls. Rollback is a normal parent-branch
revert; the original files remain in parent history and the analysis repository
is additive. No shared history is rewritten.

## Risk Assessment

1. **GitHub Sync rejects the second gitlink.** Medium likelihood, high impact.
   Mitigation: pipeline proves current tolerance; validate before merging and
   revert the parent branch if the live pull fails.
2. **Path-dependent analysis tools break.** Medium likelihood, medium impact.
   Mitigation: run them from the parent root with paths through `analysis/` and
   retain sibling `pipeline/` access.
3. **A future manuscript dependency is moved.** Low likelihood, high impact.
   Mitigation: keep all section drafts and root TeX; enforce the recorded `.fls`
   closure and figure allowlist.
4. **Large parent diff exceeds GitHub Sync transaction limits.** Medium
   likelihood, medium impact. Mitigation: validate the final branch first, then
   split parent removals into sub-100-path commits if the live integration
   requires incremental synchronization.

## References

- [Research: Faber2026 analysis repository split](research-faber2026-analysis-split.md)
- `.gitmodules:1-3`
- `main.tex:28,92-121,134-141`
- `Makefile:1-66`
- `.github/workflows/root-science-tests.yml:20-35`
- `.github/workflows/table-parity.yml:29-60`
- `figures/catalog.yaml:1-4`
