# Implementation: repository content audit

**Date:** 2026-07-22
**Plan:** [repository content audit](plan-repository-content-audit-2026-07-22.md)

## Completed

- Consolidated the populated knowledge index at `analysis/.kb/kb.sqlite3`;
  archived the empty replacement database.
- Moved parent and pipeline obsolete-science trees to
  `.archive/outdated-science/2026-07-17`.
- Updated generators, constants, tests, catalog entries, tombstones, and active
  documentation to use archive paths and vocabulary.
- Moved three known sign-bug Casey figures out of the live deck.
- Archived the completed outdated-science workflow cluster and two unreferenced
  completed implementation records.
- Repaired default manuscript-root discovery in the results-library inventory
  script; added a regression test.
- Relinked the external results-library archive slot and wrote
  `results-library-archive-relink-2026-07-22.json`.
- Kept compatibility symlinks, review snapshots, reference-arc evidence,
  transcripts, and cited logs after reference tracing proved they remain useful.

## Verification

- Analysis: 23 targeted tests passed; Ruff passed.
- Pipeline: 15 targeted tests passed; Ruff passed.
- Knowledge index rebuilt: 3,398 documents; 14,278 chunks; search passed.
- `git diff --check` passed in all three repositories.
