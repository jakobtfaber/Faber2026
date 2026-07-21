# Research: h17 preliminary source-data layout

**Date:** 2026-07-21
**Scope:** Internal codebase and live h17 storage
**Related Documents:** [Authority map](../wayfinder/map-project-authority-and-custody.md)

## Question / Scope

Determine whether the twelve-study-burst DSA-110 filterbanks and CHIME/FRB
singlebeam files can move into instrument- and burst-scoped directories without
losing bytes, provenance, or active consumers. The three noncanonical files are
outside the move set. Historical evidence retains the paths used when it was
created.

Researched against parent commit `49a4658a` and pipeline commit `7d26b1f7` on
2026-07-21. Live host: `h17` (`lxd110h17`).

## Codebase Findings

- Root-level `data/` is already ignored by Git through the anchored `/data/`
  rule; `./data/` would be redundant (`.gitignore:17-20`). The proposed h17
  tree is outside every Git checkout regardless.
- The parent certificate builder hard-codes the flat CHIME source directory and
  emits only CHIME records (`scripts/build_raw_voltage_certificates.py:17-54`).
- The active CHIME upchannelizer also assumes a flat directory and joins only
  the filename (`pipeline/analysis/scattering-refit-2026-06/baseband_recovery/upchannelize_chime.py:60-68`,
  `pipeline/analysis/scattering-refit-2026-06/baseband_recovery/upchannelize_chime.py:207-217`).
- The indexed CHIME experiment manifest uses the same flat root
  (`pipeline/analysis/chime-scintillation/DATA_MANIFEST.yaml:3-20`).
- The h17 workspace guide treats both source collections as children of the
  old compute workspace (`pipeline/docs/infrastructure/H17_WORKSPACE.md:12-31`,
  `pipeline/docs/infrastructure/H17_WORKSPACE.md:52-58`).
- The machine inventory still describes those old children and contains stale
  disk figures (`pipeline/machine_inventory.yaml:490-590`).
- Live h17 contains twelve canonical CHIME `.h5` files, twelve canonical DSA
  `.fil` files, one archived CHIME `.h5`, one uncertain DSA event, and a second
  Zach-named DSA file. The canonical collections occupy about 20 GB. Source and
  target are on device 2049, so each move can be an atomic rename.
- The July 15 Zach adjudication container was invalidated and terminated before
  migration. Its incomplete log and invalidation records remain under
  `/data/jfaber/p1-window-upchan-20260714/zach-adjudication-20260715/`. No open
  handle remained on Zach's CHIME file after termination.
- `/data` is a `fuseblk` mount with fixed `user_id=0,group_id=0,allow_other`
  presentation. Files and directories report `root:root 0777`; per-directory
  `ubuntu:ubuntu 2775` ownership is not representable through this mount.
- A post-move broad search found nineteen promoted h17 workers and diagnostics
  constructing the old CHIME path indirectly. These required a second focused
  pipeline change beyond the initially identified primary upchannelizer.

## Synthesis

Use lowercase project identifiers as directory keys and preserve the original
filenames. Record public Transient Name Server names and instrument identifiers
in a paired manifest rather than encoding every identifier into the path.
Pre-hash all 24 files, reject collisions or active readers, rename on the same
filesystem, then verify post-move hashes. Do not use compatibility symlinks.

This migration establishes custody and stable paths only. It must not infer a
DSA incoherent-dedispersion value or CHIME coherent/incoherent-dedispersion
state from filenames. Those fields remain explicitly unverified until the
square-one header and producer audit.

## References / Sources

- `.gitignore:17-20`
- `scripts/build_raw_voltage_certificates.py:17-54`
- `pipeline/analysis/scattering-refit-2026-06/baseband_recovery/upchannelize_chime.py:60-68`
- `pipeline/analysis/scattering-refit-2026-06/baseband_recovery/upchannelize_chime.py:207-217`
- `pipeline/analysis/chime-scintillation/DATA_MANIFEST.yaml:3-20`
- `pipeline/docs/infrastructure/H17_WORKSPACE.md:12-31`
- `pipeline/machine_inventory.yaml:490-590`
