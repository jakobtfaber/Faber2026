# Receipt: monorepo consolidation of Faber2026-analysis into Faber2026

- **Objective:** fold the Faber2026-analysis repository into Faber2026 as a
  plain `analysis/` directory with history, retiring the submodule pin
  (owner-chartered 2026-08-07; wayfinder ticket `monorepo-consolidation`,
  landed via Faber2026-analysis PR #261).
- **Scientific phase:** none (operational). **Operational phase:**
  reconciliation, then landing (the merge of Faber2026 PR #347 is the
  landing step and is owner-confirmed separately).

## Source snapshots

- Faber2026-analysis main at `50a349219049` ("ticket: record the owner's
  ratification of the Jupyter surface (#262)"), fetched from
  `https://github.com/jakobtfaber/Faber2026-analysis.git` 2026-08-07.
- Faber2026 main at `ca661eab` (merge of PR #349, the Overleaf sync
  resolution) at branch-final time.

## Import method

```bash
git clone --no-local <analysis checkout> && git fetch origin main
git filter-repo \
  --invert-paths \
  --path docs/rse/specs/evidence/nine-sightline-anonymous-catalog-corpus-2026-07-22/evidence-bundle.tar.gz \
  --to-subdirectory-filter analysis --force
```

Two filter passes were run as analysis main advanced (through #259, then
#260/#262). The rewrite is deterministic on the shared prefix: the #259
rewrite hashed identically (`36c387b8`) across passes; the #260 rewrite
differed between passes, so #260 entered via the first pass's tip
(`06c51f4430434fb41b7de82737430113e91067e2`, the "pure filtered tip") and
the later #262 commit was cherry-picked from the second pass. Filtered
pack: 721 MiB (the ~6.3 GiB of 2026-07 purge bundles live only on
non-main refs and never entered the import).

## Exclusions and preservation

- `evidence-bundle.tar.gz` (140,061,435 bytes; the repository's only Git
  LFS object, plus one 60.6 MiB pre-LFS historical blob) is excluded from
  the imported history. Preserved:
  - `~/Data/Faber2026/preservation/nine-sightline-anonymous-catalog-corpus-2026-07-22/`
    with `PROVENANCE.md`; sha256
    `fed672e29c1d84ffd09f93de2487a1337fb722c02bd5dc718f7f97c1e593d32d`,
    verified equal for source, copy, and the LFS pointer oid.
  - As the LFS object in the archived Faber2026-analysis repository.
  - In-repo pointer: `EVIDENCE-BUNDLE-POINTER.md` beside the former path.
- Faber2026-analysis itself is to be archived read-only, never deleted:
  it remains the authority for the unfiltered history, the original
  commit ids named by `results-registry.toml` provenance refs, and the
  LFS object. `scripts/fetch_provenance_commits.py` fetches those exact
  ids from the archive remote (verified live: all eight registry commits
  fetched and resolve).

## Verification evidence

- **Tree equivalence:** `git ls-tree -r` of the filtered tip's
  `analysis/` tree vs analysis origin/main - 3,222 of 3,223 entries
  identical, sole difference the excluded bundle (both filter passes).
  Final branch delta vs analysis main enumerates exactly the authored
  changes (pointer added; `.gitattributes`, `.github/` removed;
  `lint_changed.py`, `kb/config.py`, `test_analysis_ci_partition.py`
  edited).
- **Continuous integration, real runs on the branch (Faber2026 PR #347,
  tip `eb044a06`):** Analysis continuous integration run 31219797677
  success (route, quality with the intersected lint, tests, checkout
  inventory, all four dualband cells, aggregate); Manuscript provenance
  run 31219798256 success (provenance fetch from the archive, manuscript
  suite, LaTeX compile).
- **Contract tests:** `tests/test_manuscript_workflow.py` 7/7;
  `analysis/tests/test_analysis_ci_partition.py` 7/7; zizmor pedantic
  clean over the merged workflow set.
- **Defects found and closed during validation:** a fail-open route
  (missing head object read as an empty change set, `lane=none`) fixed
  fail-closed; the changed-files lint ratchet scoped with
  `LINT_BASE_INTERSECT=06c51f44…` so the import does not whole-tree-lint
  legacy code; provenance fetch repointed to the archive remote.

## Owner approvals recorded

- 2026-08-07 chat: consolidation confirmed ("confirmed", after the
  feasibility discussion); Overleaf sync branch merge requested
  explicitly (landed as PR #349, sync branch preserved).
- Still owner-gated at this writing: merging PR #347 (the one-way
  cutover), relaxing the main ruleset, archiving Faber2026-analysis,
  and the post-merge Overleaf pull check.

## Disposition

Branch `monorepo/analysis-import` (PR #347) green and ready; final
disposition recorded at merge time. A separate lane surfaced during the
work and is preserved untouched: the local analysis checkout's `main`
branch holds unpushed commit `d1853a6` ("reconciliation map prototype
and two Casey fit owner-decision tickets") needing its own disposition
before the archive step.
