# Receipt: Phase 5 Track B — Batch 3, and Track A closeout (2026-07-26)

**Objective/phase:** Phase 5 of
`plan-scattered-work-integration-and-retirement.md`: Track A final item +
Track B first batch. Owner approvals verbatim: "Yes, both — close out
Track A, then start Track B." and "Approved." for the six-path batch.

## Track A closeout

Standalone `Faber2026-analysis` clone switched from the stale
`codex/nine-sightline-search-contract` branch to `main` (ff-pulled to
`2bf866b`), and the local branch deleted after re-verifying its tip
`6c0e9b36…` live on origin as
`codex/nine-sightline-cherrypick-resolution-20260725`
(`ls-remote --exit-code` immediately before deletion). A leftover
untracked duplicate of the decision packet was removed after byte-compare
against the merged copy on `main`. **Track A is now empty.**

## Preservation completed before staging

- `faber2026-retirement-qualification-20260722.6Bd2Wy` (2.4 GB, the July
  cleanup record set incl. `qualification.json`, salvage trees, mirrors,
  and the known timestamp-mismatched `validation.json`) manifest-first
  copied to
  `~/Data/Faber2026/preservation/faber2026-retirement-qualification-20260722/`
  — 764 files, sha256 manifest diff empty, manifest archived.
- Six scratch analysis-output dirs (85 MB: `window_campaign_2L`,
  `campaign_r4/5/6`, `perburst_figs`, `flits-local-runs`) routed as
  science data products to `~/Data/Faber2026/scratch-outputs-20260726/`
  with README (not trash — `window_campaign_2L` is the authoritative
  two-component scintillation table).
- chime-dsa staging capture verified against live state before staging:
  both stash tips match the capture patches, unique-commit bundle present,
  untracked payload byte-size-matched (1,212,416-byte polcal filterbank).

## Staged (nothing deleted; PROVENANCE.md at every destination)

| Source | Staged to |
|---|---|
| drive `Faber2026-preserved-bundles` (6.3 GB) | drive `_trash/…-20260726` |
| drive `Faber2026-preserved-bags` (654 MB) | drive `_trash/…-20260726` |
| drive `Faber2026-rescue-20260725-v2` (1.9 GB) | drive `_trash/…-20260726` |
| drive `Faber2026-worktrees` (emptied shell) | drive `_trash/…-20260726` |
| `~/Developer/scratch/2026-06/chime-dsa-documents-area-staging` (421 MB) | `~/Documents/_trash/Faber2026-chime-dsa-staging-20260726` |
| `~/Developer/scratch/faber2026-retirement-qualification-20260722.6Bd2Wy` | `~/Documents/_trash/faber2026-retirement-qualification-20260722` |

## Post-state (verified)

- **The backup drive root holds zero `Faber2026-*` directories** — the
  "drive = staging" rule is now satisfied; everything sits in `_trash/`
  awaiting the owner's separate delete instruction.
- `~/Developer/scratch/` retains only the follow-up sweep candidates the
  plan never enumerated: `Faber2026-lane-preserve-20260717`,
  `Faber2026-logs`, `campaign_final`, `campaign_rerun*`, `chromatica_*`,
  `autorfi_fits`, dated `2026-0*/` subdirs — unexamined, untouched,
  queued.
- Consolidation end-state largely reached: project material now lives in
  the three canonical clones, `~/Data/Faber2026` (incl. `preservation/`
  and `scratch-outputs-20260726/`), and `_trash/` staging areas.
