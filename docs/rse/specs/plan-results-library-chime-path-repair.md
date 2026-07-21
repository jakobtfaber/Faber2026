# Implementation Plan: Results-library and CHIME-path repair

---
**Date:** 2026-07-20
**Author:** AI Assistant
**Status:** Approved
**Related Documents:**
- [Research: Results-library and CHIME-path repair](research-results-library-chime-path-repair.md)
- [Action packet](../certificates/results-library-repair-2026-07-20/action-packet.json)
- [Accepted repair decision](../wayfinder/tickets/authority-13-choose-link-and-chime-path-repair.md)
---

## Overview

Repair the local results-library navigation without moving or deleting real
bytes, and remove the false single-directory assumption from current
full-resolution CHIME/FRB and DSA-110 producers. Code and link mutations are
separate phases with independent drift barriers.

**Goal:** Every managed library link resolves from the canonical checkout;
current dual-band producers require explicit CHIME/FRB and DSA-110 roots; all
excluded bytes and historical receipts remain unchanged.

**Motivation:** Eight links point to a deleted worktree, three repository links
are absent, and current producers can silently search the DSA directory for
CHIME/FRB cubes.

## Current State Analysis

- `scripts/build_results_library_inventory.py:212-224` maps one source to its
  slot root, which is wrong for the nested `diagnostics` target.
- `scripts/build_results_library_inventory.py:312-381,457-498` has no exact
  entry selection or machine receipt.
- `scripts/materialize_results_library.py:123-159` has entry selection but does
  not reject unknown or duplicate selections.
- Parent mixed-root interfaces are documented in
  [the research report](research-results-library-chime-path-repair.md#full-resolution-roots).
- Pipeline mixed-root interfaces include four approved direct consumers outside
  the original list; owner approved that bounded correction.
- The historical joint-DM runner and its pinned provenance remain immutable.

## Desired End State

- Catalog sources can name an exact nested library destination.
- Builder and materializer reject unknown or duplicate `--only` values.
- Builder emits a JSON receipt naming Git identities, selection, link states,
  raw payloads, resolved targets, and file/tree manifests.
- Current dual-band code exposes only `chime_full_root` and `dsa_full_root`;
  no compatibility `data_root` remains.
- The 8 broken, 2 missing, and 3 repository links match the action packet.
- Generated inventory has exactly the 18 catalog IDs and the canonical root.
- Incomplete input lineages are explicit exceptions, not fabricated IDs.

## What We're NOT Doing

- [ ] Move or delete real bytes.
- [ ] Adjudicate either both-real conflict.
- [ ] Change JointTF, historical diagnostic, Drive, CANFAR, or h17 bytes.
- [ ] Rewrite the provenance-pinned joint-DM snapshot or its receipt.
- [ ] Promote trust, change manuscript claims, restart services, or regenerate
      manuscript figures.

## Implementation Approach

Use exact catalog entry selection plus source-specific destinations. Every live
link phase starts with action-packet hash, inode/payload, process, and manifest
checks. Mutation uses only symlink replacement/creation; real paths are never
passed to deletion or movement code.

The pipeline change starts on `codex/results-library-chime-path-repair` at the
recorded pin `c6111390`. It lands independently. The parent submodule pointer is
updated only to the reviewed pipeline commit.

## Implementation Phases

The Python runner for every command below is:

```bash
env -i HOME=/Users/jakobfaber \
  PATH=/opt/anaconda3/bin:/opt/homebrew/bin:/usr/bin:/bin \
  /opt/anaconda3/bin/conda run -n py312 python
```

### Phase 1: Exact library mechanics

**Objective:** Make every proposed link action exact, selectable, receipted,
and fail-closed before touching the live library.

**Tasks:**

- [x] Add `tests/test_results_library_repair.py` with temporary catalogs and
  trees asserting:
  - `diagnostics` maps to `slot/diagnostics`, not the slot root;
  - unknown and duplicate selections raise `SystemExit`;
  - a broken symlink is detected through `is_symlink()`, even when `.exists()`
    is false;
  - both-real paths remain conflicts;
  - receipts contain raw payload, resolved target, type, size, and manifest.
- [x] Run the focused test and observe failure:
  `env -i HOME=/Users/jakobfaber PATH=/opt/anaconda3/bin:/opt/homebrew/bin:/usr/bin:/bin /opt/anaconda3/bin/conda run -n py312 python -m pytest tests/test_results_library_repair.py -q`.
- [x] Add optional, validated `destinations` to `CatalogEntry` and
  `results_library_catalog.yaml`; add `select_entries()` and receipt helpers in
  `scripts/build_results_library_inventory.py`.
- [x] Add builder `--only` and `--receipt`; require known unique IDs. Preserve
  full-catalog behavior when `--only` is absent.
- [x] Make materializer selection use the same known-unique validation while
  retaining its existing entry-level `--only` boundary.
- [x] Run the focused test until it passes.
- [x] Run both live dry-runs and confirm exactly the action-packet classes plus
  the two excluded conflicts; perform no writes.

**Verification:**

```bash
env -i HOME=/Users/jakobfaber PATH=/opt/anaconda3/bin:/opt/homebrew/bin:/usr/bin:/bin /opt/anaconda3/bin/conda run -n py312 python -m pytest tests/test_results_library_repair.py -q
env -i HOME=/Users/jakobfaber PATH=/opt/anaconda3/bin:/opt/homebrew/bin:/usr/bin:/bin /opt/anaconda3/bin/conda run -n py312 python scripts/build_results_library_inventory.py --dry-run
env -i HOME=/Users/jakobfaber PATH=/opt/anaconda3/bin:/opt/homebrew/bin:/usr/bin:/bin /opt/anaconda3/bin/conda run -n py312 python scripts/materialize_results_library.py --dry-run
```

### Phase 2: Parent full-resolution roots

**Objective:** Route every current parent producer to instrument-specific
full-resolution roots without altering the frozen joint-DM snapshot.

**Tasks:**

- [x] Update focused tests first:
  `tests/test_codetection_gallery.py`, `tests/test_codetection_triptych.py`,
  `tests/test_codetection_data_grid.py`,
  `tests/test_fig1_residual_drift_audit.py`,
  `tests/test_l0_axis_conventions.py`, and new lightweight routing assertions
  for frequency-axis and current joint-DM runners. Each fixture places CHIME
  and DSA files in different directories and asserts wrong-root lookup fails.
- [x] Run those tests and observe signature/routing failures.
- [x] Replace mixed-root constants, signatures, and command-line options in:
  `scripts/build_l0_certificates.py`,
  `scripts/plot_codetection_gallery.py`,
  `scripts/plot_codetection_triptych.py`,
  `scripts/plot_codetection_data_grid.py`,
  `scripts/audit_fig1_frequency_axes.py`,
  `scripts/audit_fig1_residual_drift.py`, and the approved direct consumer
  `scripts/audit_fig1_axes.py`.
- [x] Add `scripts/run_joint_dm_phase.py` as the current split-root producer.
  Leave `analysis/dm-joint-phase-v2/code/` and its provenance hashes unchanged;
  update only current run instructions to distinguish the historical snapshot.
- [x] Update `figures/catalog.yaml` and `repro_manifest.csv` to name both roots.
- [x] Regenerate L0 certificates with explicit roots; assert all 36 entries,
  hashes, sizes, frequency orders, and paths match the prior certified content
  except correction of any stale CHIME path emitted by the old builder.
- [x] Run the focused parent tests until they pass.

**Verification:**

```bash
env -i HOME=/Users/jakobfaber PATH=/opt/anaconda3/bin:/opt/homebrew/bin:/usr/bin:/bin /opt/anaconda3/bin/conda run -n py312 python -m pytest \
  tests/test_codetection_gallery.py tests/test_codetection_triptych.py \
  tests/test_codetection_data_grid.py tests/test_fig1_residual_drift_audit.py \
  tests/test_l0_axis_conventions.py tests/test_figure_flow.py -q
```

### Phase 3: Pipeline full-resolution roots

**Objective:** Land an independently tested pipeline interface that never
loads both instruments from one directory.

**Tasks:**

- [x] Create pipeline branch
  `codex/results-library-chime-path-repair` at `c6111390`; verify the submodule
  was clean immediately before checkout.
- [x] Extend `pipeline/tests/test_codetection_data.py`,
  `pipeline/tests/test_dm_power.py`, and
  `pipeline/tests/test_adaptive_arrival.py` first. Assert telescope-to-root
  routing, unknown-telescope failure, missing-band failure, and separate default
  roots.
- [x] Run the focused pipeline tests and observe failures.
- [x] Replace the mixed root in `pipeline/dispersion/dm_power_analysis.py`,
  `pipeline/dispersion/dm_phase_analysis.py`,
  `pipeline/dispersion/dm_campaign/configs/battery.yaml`,
  `pipeline/dispersion/dm_campaign/run_battery.py`,
  `pipeline/dispersion/dm_campaign/adaptive_arrival.py`,
  `pipeline/dispersion/dm_campaign/run_adaptive_arrival.py`, and
  `pipeline/flits/batch/codetection_data.py`.
- [x] Update only current custody statements in `pipeline/DATA_LOCATIONS.md`,
  `pipeline/DATA_SOURCES.md`, `pipeline/machine_inventory.yaml`, and
  `pipeline/scintillation/DATA_PROVENANCE.md`; preserve historical receipts.
- [x] Run focused and relevant pipeline suites, commit only pipeline paths,
  push the branch, and land it through its own review step.

**Verification:**

```bash
env -i HOME=/Users/jakobfaber PATH=/opt/anaconda3/bin:/opt/homebrew/bin:/usr/bin:/bin /opt/anaconda3/bin/conda run -n py312 python -m pytest \
  pipeline/tests/test_codetection_data.py pipeline/tests/test_dm_power.py \
  pipeline/tests/test_adaptive_arrival.py -q
```

### Phase 4: Stable identities and current documentation

**Objective:** Make result/slot relationships explicit without inventing input
lineage.

**Tasks:**

- [x] Add failing catalog/registry tests asserting every catalog entry has an
  explicit `result_ids` list and every registry row has an explicit
  `library_slots` list; referenced IDs and slots must exist.
- [x] Add only evidence-backed mappings. Use empty lists where no claim-level
  relationship is established.
- [x] Add explicit input exceptions for the 12 remediation records and 3 Freya
  package manifests; create no `input.*` row because required producing Git
  identity/provenance is absent.
- [x] Update `docs/rse/specs/results-library-INDEX.md` and current custody docs
  with exact-selection and receipt commands.
- [x] Run registry/catalog and L0 checks until they pass.

### Phase 5: Live link repair and inventory regeneration

**Objective:** Apply only the 13 symlink actions after all code gates pass.

**Tasks:**

- [x] Recheck parent/pipeline identities, all action-packet hashes, source
  manifests, eight old link inodes/payloads, ten absent paths, excluded-tree
  manifests, `lsof`, and producer processes. Stop on any drift.
- [x] Replace only the eight broken library links using builder `--only` IDs;
  emit and validate a JSON receipt.
- [x] Create only the two missing library links after revalidating their source
  manifests; emit and validate a second receipt.
- [x] Restore only the two DM-locked repository links and the nested
  `diagnostics` link through materializer `--only`; validate exact resolved
  targets and source manifests.
- [x] Regenerate the full 18-entry inventory from the canonical checkout.
  Enumerate real-directory exceptions and the unmanaged JointTF hold.
- [x] Verify all managed links resolve, catalog IDs equal inventory IDs, the
  canonical roots are recorded, every excluded manifest is unchanged, and a
  final dry-run proposes no unplanned mutation.
- [x] Write the implementation and validation receipts; resolve the Wayfinder
  task only after every check passes.

## Success Criteria

### Automated Verification

- [x] All focused parent and pipeline tests pass.
- [x] Every managed link resolves to its action-packet target.
- [x] Inventory contains exactly 18 catalog IDs and the canonical checkout.
- [x] All 36 L0 certificates retain accepted hashes, sizes, and frequency order.
- [x] Excluded-tree manifests equal their action-packet preimages.
- [x] Historical joint-DM runner and provenance hashes are unchanged.
- [x] Final dry-runs show no unknown mutation and both-real conflicts remain
      fail-closed.

### Manual Verification

No visual or scientific judgment is required. This batch changes navigation and
path interfaces only. Any later scientific trust adoption remains separately
owner-gated.

## Testing Strategy

Tests are written before each interface change. Temporary directories exercise
link and root routing; no test uses the live library as a mutation target. Live
checks are read-only until Phase 5 and are compared to the frozen action packet.

## Migration Strategy

The pipeline lands first. The parent then records the reviewed pipeline pin.
Parent command-line callers migrate atomically from `--data-root`/`--data-dir`
to `--chime-full-root` plus `--dsa-full-root`.

**Rollback:** Restore symlink payloads or absence exactly as recorded; decode
the inventory preimages and verify their hashes before replacement; revert code
commits normally. Never modify real result bytes.

## Risk Assessment

1. **Wrong nested destination** — high impact; prevented by explicit catalog
   destinations and temp-tree tests.
2. **Unlisted caller breakage** — high impact; corrected by the owner-approved
   five-file scope expansion and exhaustive call-site search.
3. **Historical provenance rewrite** — high impact; frozen snapshot excluded
   and hash-checked.
4. **Concurrent filesystem drift** — medium likelihood; every live phase has an
   exclusive preflight and stop rule.

## Edge Cases and Error Handling

- Broken symlink: inspect with `is_symlink()`/`lstat`, never only `.exists()`.
- Unknown or duplicate ID: exit before creating parent directories or links.
- Both source and destination real: report conflict and perform no action.
- Incomplete lineage: list an exception and create no stable input ID.
- Unknown telescope: raise an error; never fall back to a shared directory.

## References

- [Research report](research-results-library-chime-path-repair.md)
- [Action packet](../certificates/results-library-repair-2026-07-20/action-packet.json)
- [Accepted repair decision](../wayfinder/tickets/authority-13-choose-link-and-chime-path-repair.md)
- All files cited in the implementation phases

## Review History

### Version 1.0 — 2026-07-20

- Initial plan after owner approval of the five-consumer scope correction and
  preservation of the provenance-pinned historical runner.
