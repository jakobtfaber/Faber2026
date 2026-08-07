# Receipt: Phase 5 Track A — Batch 2 (2026-07-26)

**Objective/phase:** Phase 5 Track A of
`plan-scattered-work-integration-and-retirement.md`, second batch.
**Owner approvals (verbatim):** "Let's proceed with the Track A batches
queued" (also recorded as overriding the five-per-session retirement cap
for this sitting) and "All nine approved" for the exact paths below.

## Preservation performed before staging (all hash-verified)

- Pushed three uncovered tips: parent
  `codex/expanded-foreground-phase-two-review` = `2b33c052…2505`; FLITS
  `codex/figure3-deterministic-pdf` = `c46c8e50…8889`; parent
  `docs/special-ref-maintenance-20260724` = `3a58378f…2a97a`.
- **Sole-copy rescue:** pipeline commit `8179bbb9…a417` ("data: source
  Verdi host redshift roster") existed only in the nested
  `parent-work/pipeline` submodule store; pushed to FLITS
  `rescue/pr174-parent-work-pipeline-20260726`.
- Submodule pointer drifts verified in canonical stores: `dc265bc0`
  (standalone Faber2026-analysis), `eb550d9a` (parent analysis module +
  standalone), `f3c8d22a` (parent pipeline module).
- Loose file `jointtf-pin-closeout.json` copied to
  `~/Data/Faber2026/preservation/jointtf-pin-closeout-20260726.json`
  (sha256 `5210f8d1…7edf`, source-identical).

## Gate evidence

Per-entry tip coverage proven by `branch -r --contains` after fetch (see
the PROVENANCE.md files for the per-entry mapping); working trees clean or
drift-receipted; zero open files (`lsof +D` = 0 on both roots); no
removals of registered worktrees in this batch (all nine are plain
directories or standalone clones). Stale plan-queue note: the "25+
analysis ticket worktrees" under `~/Developer/scratch/worktrees/` no
longer exist — the directory holds only an unrelated dotfiles lane,
untouched.

## Actions (all staged, nothing deleted)

| # | Source | Staged to |
|---|---|---|
| 1–7 | `/Volumes/ArtifexBackupDrive/Faber2026-preserved-checkouts/{tickets-02-03, protected-corpus-15, wayfinder18, jointtf-pin.r6tIac, jointtf-preserve.YrLfOn, .tmp-final-pin.pk7WwE, .tmp-pr174.Lj4gff}` (~13.5 GB) | `/Volumes/ArtifexBackupDrive/_trash/Faber2026-preserved-checkouts-20260726/` + PROVENANCE.md (drive-local rename, no copy) |
| 8 | `~/…/jakobtfaber/Faber2026-worktrees/special-refs-20260724` (786 MB clone) | `~/Documents/_trash/Faber2026-special-refs-20260724/` + PROVENANCE.md |
| — | emptied `Faber2026-worktrees/` shell | `~/Documents/_trash/Faber2026-worktrees-emptyshell-20260726/` |
| 9 | `Faber2026-analysis-worktrees/` (empty), `Faber2026-analysis-jointtf.qjhnHz` (4 KB, in rescue-v2 04) | `~/Documents/_trash/` |
| — | emptied drive `Faber2026-preserved-checkouts/` shell | drive `_trash/…-emptyshell-20260726` |

## Post-state (verified)

- `~/Developer/repos/github.com/jakobtfaber/` no longer contains any
  `Faber2026-*worktrees*` or `*.qjhnHz` leftovers — only the canonical
  clones (plus unrelated repos).
- Remote preservation leftovers are byte-covered at
  `~/Data/Faber2026/preservation/` since Phase 4 (Track B candidates),
  and the emptied `Faber2026-worktrees/` dir (its `parent/`+`analysis/`
  subdirs emptied in batch 1).
- Deletion of anything in `_trash/` remains a separate explicit owner
  instruction.
