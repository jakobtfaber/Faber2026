# Implementation Plan: h17 preliminary source-data layout

---
**Date:** 2026-07-21
**Author:** AI Assistant
**Status:** Approved
**Related Documents:**
- [Research: h17 preliminary source-data layout](research-h17-source-data-layout.md)
---

## Overview

Move the 24 canonical preliminary source files into a stable h17 tree organized
by instrument and lowercase project identifier. Preserve byte identity, create
a machine-readable receipt, and update active consumers. The owner approved the
layout and the exact bounded move set on 2026-07-21.

**Goal:** Twelve complete DSA-110/CHIME-FRB source pairs exist under
`/data/Faber2026/data/`, with verified hashes and no active reference to the old
flat source roots.

**Motivation:** Source custody must be intelligible before dispersion-measure,
arrival-time, morphology, scintillation, or foreground analysis begins.

## Current State Analysis

- `.gitignore:17-20` already excludes checkout-local `data/`.
- `scripts/build_raw_voltage_certificates.py:17-54` emits CHIME-only records
  using the old flat root.
- `pipeline/analysis/scattering-refit-2026-06/baseband_recovery/upchannelize_chime.py:60-68`
  and `:207-217` locate CHIME files in that flat root.
- `pipeline/analysis/chime-scintillation/DATA_MANIFEST.yaml:3-20` indexes a file
  relative to the old flat root.
- `pipeline/docs/infrastructure/H17_WORKSPACE.md:12-31` and
  `pipeline/machine_inventory.yaml:490-590` document the old layout.

## Desired End State

Each project identifier has exactly one canonical source file per instrument:

```text
/data/Faber2026/data/dsa-110/<project-id>/<original-name>.fil
/data/Faber2026/data/chime-frb/<project-id>/<original-name>.h5
```

A checked-in paired manifest records paths, sizes, hashes, public names, and
instrument identifiers. Dedispersion state remains unverified where producer
evidence has not yet been examined.

## What We're NOT Doing

- [ ] Moving or deleting the archived CHIME file, uncertain 20220912A DSA file,
      or second Zach-named DSA file.
- [ ] Moving derived `.npy`, fit, or diagnostic products.
- [ ] Rewriting historical provenance paths.
- [ ] Adding compatibility symlinks.
- [ ] Declaring dispersion measures, time axes, or headers validated.

## Implementation Approach

Use a tracked mapping as the allowlist. Preflight must prove 24 sources exist,
24 targets do not exist, all sources and targets share device 2049, and no
source has an open handle. Generate SHA-256 hashes before any rename. Create
burst directories, use `mv -n` for same-filesystem atomic renames, then require
post-move size and hash equality. On any mismatch, stop and use the receipt's
old/new mapping to rename completed files back.

The pipeline change and parent certificate change are separate commits. The
parent submodule pin moves only after the pipeline commit validates.

## Implementation Phases

### Phase 1: Freeze the allowlist and preflight

**Objective:** Make an incorrect or partial move impossible.

**Tasks:**

- [x] Add `scripts/h17_source_data_layout.py` with the exact twelve-record
      mapping and pure functions producing old/new paths.
- [x] Add `tests/test_h17_source_data_layout.py` asserting 12 unique project
      identifiers, 24 unique source paths, 24 unique target paths, expected
      extensions, and the Zach paths.
- [x] Run `pytest -q tests/test_h17_source_data_layout.py`; first observe import
      failure, then implement the mapping and require PASS.
- [x] Run the script's read-only `preflight` over SSH. Require 24 existing
      sources, zero existing targets, device 2049 throughout, zero open handles,
      and a complete pre-move SHA-256 manifest.

**Verification:** `python3 scripts/h17_source_data_layout.py preflight --host h17`
exits zero and writes no remote files.

### Phase 2: Move and verify bytes

**Objective:** Atomically relocate only the allowlisted files.

**Tasks:**

- [x] Create `/data/Faber2026/data/{dsa-110,chime-frb}/<project-id>`. The
      `fuseblk` mount fixes displayed ownership/mode at `root:root 0777`, so the
      planned per-directory `ubuntu:ubuntu 2775` metadata is not representable.
- [x] Run `python3 scripts/h17_source_data_layout.py migrate --host h17
      --receipt docs/rse/certificates/h17-source-data-migration-2026-07-21/receipt.json`.
- [x] For each allowlisted file, use `mv -n <old> <new>`; stop on any collision.
- [x] Generate the post-move receipt and require all 24 sizes and hashes to equal
      the pre-move values.
- [x] Confirm the three excluded files remain at their original paths.

**Verification:** `python3 scripts/h17_source_data_layout.py verify --host h17`
reports `24/24 verified`, `0 old canonical paths`, and `3/3 exclusions preserved`.

### Phase 3: Update active authorities and consumers

**Objective:** Make the new tree the only active path contract.

**Tasks:**

- [x] Update `pipeline/analysis/scattering-refit-2026-06/baseband_recovery/upchannelize_chime.py`
      so `_fetch_h5(name, relpath, scratch)` checks
      `/data/Faber2026/data/chime-frb/<name>/<filename>` before CANFAR fallback.
- [x] Add a focused pipeline test proving Zach and Freya resolve to burst-scoped
      paths without touching the filesystem.
- [x] Update `pipeline/analysis/chime-scintillation/DATA_MANIFEST.yaml`,
      `pipeline/docs/infrastructure/H17_WORKSPACE.md`, and the h17 section of
      `pipeline/machine_inventory.yaml`.
- [x] Commit and validate the primary pipeline change independently (PR #214).
- [x] Update the nineteen promoted h17 workers and diagnostics found by the
      exhaustive indirect-path search (follow-up PR #215).
- [x] Update `scripts/build_raw_voltage_certificates.py`, regenerate its output,
      and add the paired source manifest and move receipt under
      `docs/rse/certificates/h17-source-data-migration-2026-07-21/`.
- [x] Bump the parent submodule pin to merged pipeline commit `d0d1e278`.
- [x] Leave `.gitignore` unchanged because `/data/` already passes
      `git check-ignore -v data/test.fil`.

**Verification:** targeted parent and pipeline tests pass; exhaustive search of
active code/config finds no old flat source root.

### Phase 4: Closeout

**Objective:** Prove the new authority is usable and preserved.

**Tasks:**

- [x] Run a metadata-only open of Zach's `.h5` and SIGPROC header read of
      Zach's `.fil` from their new paths; do not perform scientific analysis.
- [x] Re-run the remote verification and no-open-handle checks.
- [x] Run `make kb-index` in the parent repository (full build plus final
      incremental pass: 48/48 changed chunks embedded).
- [x] Run `agent-closeout-check` for both repositories with every touched
      runtime/config path.
- [ ] Commit task-scoped changes; follow the configured publish policy.

**Verification:** all automated checks below pass. Owner manual review remains
required before calling the source layer scientifically trusted.

## Success Criteria

### Automated Verification

- [x] 24/24 target files match pre-move SHA-256 hashes and sizes.
- [x] Zero canonical source files remain at old paths.
- [x] Three excluded files remain byte-untouched at old paths.
- [x] `pytest -q tests/test_h17_source_data_layout.py` passes.
- [x] Targeted pipeline path-resolution test passes.
- [x] `git check-ignore -v data/test.fil` reports `.gitignore:20:/data/`.
- [x] No active code/config contains the old flat CHIME or DSA source roots.

### Manual Verification

- [ ] Owner accepts the paired manifest and twelve directory names.
- [ ] Owner spot-checks Zach headers before raw/input-source trust closes.

## Testing Strategy

Unit tests cover mapping uniqueness, path construction, and burst-scoped CHIME
lookup. Remote integration checks cover existence, collisions, device identity,
open handles, hashes, exclusions, and metadata-only readability.

## Migration Strategy

The script writes a pre-move manifest before mutation and a post-move receipt
after verification. Rollback renames only receipt-listed targets back to their
old paths after proving the old paths are absent and no target has an open
handle. No directory cleanup occurs in this wave.

## Risk Assessment

1. **Active reader:** high impact. Preflight fails on any open source handle.
2. **Wrong burst mapping:** high impact. Mapping is allowlisted and unit-tested;
   filenames remain unchanged.
3. **Partial migration:** medium likelihood. Verification is per-file and the
   receipt supplies exact rollback paths.
4. **Historical provenance drift:** medium impact. Historical evidence is not
   rewritten; the receipt links old and new locations.

## Edge Cases and Error Handling

- Existing target: abort before any move.
- Missing source: abort before any move.
- Cross-device target: abort; do not copy.
- Hash mismatch: stop and mark migration failed; do not update authorities.
- Unresolved/extra file: leave untouched and list under exclusions.

## References

- [Research: h17 preliminary source-data layout](research-h17-source-data-layout.md)
- `.gitignore`
- `scripts/build_raw_voltage_certificates.py`
- `pipeline/machine_inventory.yaml`
- `pipeline/docs/infrastructure/H17_WORKSPACE.md`
- `pipeline/analysis/chime-scintillation/DATA_MANIFEST.yaml`
- `pipeline/analysis/scattering-refit-2026-06/baseband_recovery/upchannelize_chime.py`

## Review History

### Version 1.0 — 2026-07-21

- Owner approved the bounded move, lowercase project identifiers, no symlinks,
  exclusion preservation, and invalidation of the stale Zach run.
