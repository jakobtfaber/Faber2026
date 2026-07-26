# Receipt: final deletion of _trash staging areas (2026-07-26)

**Objective/phase:** step "(2)" of the owner instruction "Let's proceed
with (1) and then after that (2)" — final `rm` of both `_trash` staging
areas — plus the owner's "Approved." confirming the follow-up-sweep nine
joined the deletion scope. This closes the scattered-work consolidation.

## Pre-delete red-team verification (all passed at the door)

- **Bundles (5):** sha256 re-computed and matched recorded values —
  rewrite mirrors `4ef7e35f…`/`3c469e6d…`, Overleaf comprehensive
  `ae6fa3a0…`, supplement `eb0208ee…`, local-history `d7a342bf…`;
  `git bundle verify` OK on all five (Overleaf bundles verified from the
  live clone before its deletion).
- **Manifest copies re-hashed at destination:** worktree-retirement
  receipts (7,719 files vs archived MANIFEST), preserved-bags (21),
  preserved-bundles (138), rescue-v2 (221), science-gates (8),
  FLITS-unreferenced (11), Overleaf dir (only surplus = known
  supplement), qualification (765 files, direct source-vs-destination
  hash compare; MANIFEST.sha256 now archived at destination).
- **Special-refs clone:** tip `3a58378f…2a97a` confirmed live on origin
  by full-hash `ls-remote --exit-code` (an initial `branch -r
  --contains` miss was the clone's single-branch fetch refspec, not
  missing data).
- **Preserved-checkouts (drive):** frozen in `_trash` since the batch-2
  verdict; per-entry tip-coverage evidence retained in the archived
  PROVENANCE files.
- **Records archived first:** all 18 PROVENANCE/manifest records from
  both `_trash` roots copied to
  `~/Data/Faber2026/preservation/deletion-records-20260726/`.

## Deleted (explicit enumerated paths, owner-authorized)

- `/Volumes/ArtifexBackupDrive/_trash/`: preserved-bags, preserved-bundles,
  preserved-checkouts (+emptyshell), rescue-20260725-v2, worktrees dir,
  batch-3 PROVENANCE (~25 GB; drive used fell 119→94 GiB).
- `~/Documents/_trash/`: overleaf clone, special-refs clone, chime-dsa
  staging, qualification record set, both rewrite-mirror dirs,
  lane-preserve, logs, filterbank logs, mission-control prototype,
  scratch-preservation, scratch-receipts, jointtf/worktree shells, and
  the two staging PROVENANCE files (~5.3 GB; note `~/Documents` is the
  iCloud File Provider view, so reclaimed space follows iCloud sync).

Both `_trash` areas verified empty post-delete.

## Post-state

Consolidation end-state reached: Faber2026 project material now lives
only in the three canonical clones and `~/Data/Faber2026` (including
`preservation/` and `scratch-outputs-20260726/`). The backup drive holds
no Faber2026 content. Untouched separate lanes remain as listed in
`receipt-phase5-followup-sweep-2026-07-26.md`.
