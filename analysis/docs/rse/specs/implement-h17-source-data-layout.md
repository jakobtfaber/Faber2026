# Implementation: h17 preliminary source-data layout

**Date:** 2026-07-21  
**Status:** Implemented; scientific metadata trust remains owner-gated  
**Plan:** [plan-h17-source-data-layout.md](plan-h17-source-data-layout.md)

## Outcome

The twelve canonical DSA-110/CHIME-FRB source pairs now live at:

```text
/data/Faber2026/data/dsa-110/<project-id>/<original-name>.fil
/data/Faber2026/data/chime-frb/<project-id>/<original-name>.h5
```

All 24 files were same-filesystem renames. Independent post-move verification
matched size, SHA-256, device, inode, and modification time; zero old canonical
paths remain. The three excluded files remain unchanged at their old paths.

## Repository changes

- Added a fail-closed migration/verification tool and focused parent tests.
- Regenerated the twelve CHIME raw-voltage certificates with project-scoped
  paths.
- Added the paired custody manifest, migration receipt, Zach metadata-readability
  record, and dirty-state evidence packets.
- Updated the active trust-reset plan reference.
- Updated the primary CHIME upchannelizer, experiment manifest, h17 guide, and
  machine inventory in pipeline PR
  [#214](https://github.com/jakobtfaber/dsa110-FLITS/pull/214), merge
  `5e3aa4eeb5dece3b8009b6b287e3743d98f68730`.
- Updated nineteen promoted h17 workers/diagnostics found by the broad indirect
  path search in pipeline PR
  [#215](https://github.com/jakobtfaber/dsa110-FLITS/pull/215), merge
  `d0d1e278766de4ac97af0765b7d7c58fa0fbdfbc`.

`.gitignore` was not changed: its existing anchored `/data/` rule already
excludes a checkout-local data tree.

## Evidence

- `docs/rse/certificates/h17-source-data-migration-2026-07-21/receipt.json`
- `docs/rse/certificates/h17-source-data-migration-2026-07-21/source-manifest.json`
- `docs/rse/certificates/h17-source-data-migration-2026-07-21/zach-metadata-readability.json`
- Remote journal:
  `/data/Faber2026/provenance/h17-source-data-migration-20260721.json`

## Validation

- Final live h17 verification: `24/24 verified`, zero old canonical paths,
  `3/3` exclusions preserved, and no open target handles.
- Parent targeted tests: 7 passed.
- Pipeline targeted tests: 5 passed; both pull-request Python 3.12 suites and
  Socket checks passed.
- All promoted h17 worker scripts compile.
- Active code/config exact-root search contains no retired flat source root.
- `git check-ignore -v data/test.fil` resolves to `.gitignore:20:/data/`.
- Zach metadata-only reads succeeded for both files.

## Findings and deviations

1. The migration command originally returned nonzero after successful
   verification because its remote finalizer printed a path instead of JSON.
   The journal and local receipt were already complete and verified. The
   wrapper was fixed and regression-tested; the move was not rerun.
2. `/data` is a `fuseblk` mount with fixed `root:root 0777` presentation.
   Planned per-directory `ubuntu:ubuntu 2775` metadata is not representable on
   this mount. File bytes and custody verification are unaffected.
3. Zach's DSA header exposes 6,144 channels and 32.768 microsecond sampling but
   no `refdm` field. The CHIME file exposes 871 channels, 2.56 microsecond base
   sampling, and `DM_coherent=262.4359033801` on `tiedbeam_power`. That
   attribute alone does not establish the voltage dataset's full dedispersion
   history or validate the time axis.
4. For the completed move, pre-move hashes were held in process memory and embedded as `before` records
   in the verified final receipt, but were not persisted as a separate file
   before the rename. This differs from the plan's durable pre-move-manifest
   wording. The independently repeated final verification closes custody for
   this move. On 2026-07-21 the tool was hardened for future reuse: each new
   attempt now atomically writes the complete 51-path preflight packet locally
   and remotely, verifies identical SHA-256 hashes, binds that reference into
   the attempt-specific journal, and re-checks source identities before any
   rename. This does not retroactively create evidence for the completed move.

## Remaining owner gate

Custody and paths are verified. The source layer is not yet scientifically
trusted. Owner spot-check and the square-one producer/header audit must still
establish the applied DSA dispersion measure, CHIME voltage processing history,
and exact arrival-time axis semantics before analysis begins.
