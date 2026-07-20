# Research: local data and results custody

**Date:** 2026-07-20
**Scope:** Internal, read-only inventory. Local disk plus current parent and
`pipeline/` checkouts. No relinking, regeneration, movement, or data edits.
**Codebase state:** parent `179ed2bf`; `results-registry.toml` was concurrently
modified and is assessed as observed, not settled.
**Related:**
[`authority-04`](../../wayfinder/tickets/authority-04-reconcile-local-data-and-results.md),
[`results-library-INDEX`](../results-library-INDEX.md)

## Question / scope

Inventory `~/Data/Faber2026/` by artifact class. Reconcile the manuscript-facing
registry with the external results library. Explain all broken links. Find
current code/config/document references that still assume CHIME and DSA-110
cubes share the old `dsa110/DSA_bursts/` directory.

Method: bounded `find`, `du -sk`, `stat`, link-target inspection, TOML/YAML
parsing, targeted repository search, and the materializer's read-only
`--dry-run`. Existing hashes and receipts were read; large data were not
rehashed. The required knowledge-base command could not run because `scripts/kb`
was a directory containing only `__pycache__`, not an executable entry point.

## Findings

### 1. Local artifact classes

Observed sizes are allocated disk size, not logical byte totals.

| Class | Path | Observed contents | Size / count | Custody and trust |
|---|---|---|---|---|
| CHIME/FRB full-resolution derived intensity cubes | `chimefrb/CHIME_bursts/` | Exactly 12 `*_chime_I_*_cntr_bpc.npy` | 1,572,865,536 logical bytes; 1.47 GiB allocated | Canonical Mac location. Derived, not raw. Registry hashes exist; all rows pending. |
| DSA-110 full-resolution derived intensity cubes | `dsa110/DSA_bursts/` | Exactly 12 `*_dsa_I_*_cntr_bpc.npy`, one corner plot, README | 1,474,561,536 logical bytes for cubes; 2.87 GiB directory allocated | Canonical Mac location. Derived, not raw. Registry hashes exist; all rows pending. |
| CHIME upchannelized inputs | `dsa110/upchan_codetections/` | 12 upchannelized arrays, 12 frequency arrays, 12 time metadata files, builders and provenance | 1,188,693,504 logical bytes for upchannelized arrays; 1.58 GiB directory allocated | Historical generation receipt exists. Registry says checksum matches review deck; all pending. |
| Remediated two-band inputs | `dsa110/upchan_codetections_remediated_20260718/` | 12 bursts × CHIME array/frequency/mask + DSA array/mask; per-burst provenance JSON | 2.49 GiB | Separate derived lineage. `PROVENANCE_REMEDIATION.md` records input/output MD5 values and operations. Registry does not inventory these outputs. |
| Incomplete remediation v2 | `dsa110/upchan_codetections_remediated_v2_20260718/` | Three diagnostic PNGs and scripts; no campaign receipt | 456 KiB | Diagnostic/incomplete; not an authority. |
| Packaged scintillation data | `dsa110/scintillation-data/`, `dsa110/scintillation/data/` | CHIME/DSA NPZ products; 25 live symlinks | 2.83 GiB + 1.31 GiB | Mixed historical products. Registry does not enumerate these bytes. |
| Fits, diagnostics, notebooks, caches | remaining `dsa110/` subtrees | runs, catalogs, products, results, review notebook, refit variants, footprints | About 3.9 GiB | Mixed. Trust must come from per-campaign receipts, not directory presence. |
| Results library | `results-library/` | 331 regular files; 9 links; 8 broken | 98.7 MiB | Navigational/custody layer, currently stale and partially disconnected. |

The whole observed `dsa110/` tree is 14.96 GiB allocated with 777 regular files.
The CHIME split is real: the local root README names separate instrument trees,
and `dsa110/DSA_bursts/README.md` forbids CHIME files or aliases.

No Mac raw CHIME voltage files were found or expected here. The registry itself
says the only raw CHIME data are twelve singlebeam voltage HDF5 files on h17 and
calls these 36 local arrays derived products
([results-registry.toml:512](../../control/results-registry.toml#L512)).

### 2. Registry versus results library

These are different inventories, with no stable cross-key:

- `results-registry.toml` declares itself the canonical inventory for
  manuscript-facing results ([lines 1-7](../../control/results-registry.toml#L1)).
  Observed: 61 rows: 25 manuscript results plus 36 derived-input certificates;
  14 trusted, 40 pending, 7 revoked; 53 current, 8 superseded.
- The catalog contains 18 campaign/navigation entries and a separate trust
  vocabulary ([results_library_catalog.yaml:5](../../../../scripts/results_library_catalog.yaml#L5)).
  It distinguishes real-byte `materialize` from repository-backed `link_only`
  slots ([lines 18-20](../../../../scripts/results_library_catalog.yaml#L18)).
- No registry row mentions `results-library`, and no library record carries a
  registry result ID. Registry artifact paths mostly point into git or directly
  to the three local input classes. Therefore neither surface proves the other
  is current.

The 36 registry input paths all exist. Existing recorded SHA-256 values were not
recomputed. Sizes are uniform for CHIME full-resolution (131,072,128 bytes each)
and DSA-110 (122,880,128 bytes each); CHIME upchannelized arrays range from
83,607,680 to 132,117,376 bytes. Example path, hash, pending trust, and unresolved
builder identity are recorded together at
[results-registry.toml:523-539](../../control/results-registry.toml#L523).
The same pattern continues through Zach
([lines 1153-1169](../../control/results-registry.toml#L1153)).

The registry's generator is currently unsafe for the split layout:
`build_l0_certificates.py` sets one `DSA` root and reads CHIME full-resolution
files from it (`scripts/build_l0_certificates.py:36-38,102,113`). Its emitted
`docs/rse/certificates/l0-certificates.json` therefore preserves obsolete CHIME
paths. The registry has been manually corrected to `chimefrb/CHIME_bursts/`, but
the producer has not.

### 3. Results-library drift

The generated external inventory is not current authority:

- Generated `2026-07-20T14:09:06Z` from deleted worktree
  `Faber2026-jointtf-grok-revalidation`, not this checkout.
- It has 19 entries; the current catalog has 18. Inventory-only
  `scattering.jointmodel-latest` is unrepresented in the current catalog.
- It reports missing source paths because its recorded worktree is gone.
- Current disk also has uncataloged `historical/2026-07-20-pipeline-diagnostics/`
  (12.6 MiB) with `ARCHIVE.md` and `SHA256SUMS`. This is the strongest receipt in
  the library: source baseline, replacement, archive policy, and per-file SHA-256.
- Current materializer dry-run reports two `would-conflict-both-real` cases
  (`scintillation...results`, `pipeline/results`), plus three
  `would-relink-src` cases (two DM-locked sources and DM-joint diagnostics).
  This means disk and catalog do not presently encode a single clean Phase-B
  direction. No action was taken.

The builder derives link targets from the checkout used to run it
([build_results_library_inventory.py:312-325](../../../../scripts/build_results_library_inventory.py#L312)).
That explains why link-only slots captured an expendable worktree. The repo
pointer says refresh must be run from this checkout
([results-library-INDEX.md:16-22](../results-library-INDEX.md#L16)), but the
external index instead names another deleted scratch checkout.

### 4. Exactly eight broken links

All eight are `link_only` navigation links. Every stored target is under deleted
`~/Developer/scratch/worktrees/Faber2026-results-library-b/`. Their present
canonical source exists in this checkout. Thus this is navigation breakage, not
evidence that the source bytes were lost.

| Broken library link | Stored target suffix | Present canonical source | Current source size / cheap hash |
|---|---|---|---|
| `manuscript/repro_manifest.csv` | `repro_manifest.csv` | `repro_manifest.csv` | 32 KiB; SHA-256 `2edfc00e857ae46a08b434ed2fbfed5f744cd95522d5b5824281b87284acf6af` |
| `manuscript/figures` | `figures` | `figures/` | 96.2 MiB; no tree hash computed |
| `scintillation/chime-diagnostic` | `pipeline/analysis/chime-scintillation` | same repo-relative path | 20.2 MiB; diagnostic-only by catalog |
| `foreground/tau_consistency_catalog.csv` | `pipeline/galaxies/foreground/data/tau_consistency_catalog.csv` | same repo-relative path | 4 KiB; SHA-256 `1df14886479bff1942a5b7c3aa3b3fae51452ae3a567f322007c97b740eafa6b` |
| `foreground/v3-energetics` | `analysis/v3_energetics` | same repo-relative path | 20 KiB; partial by catalog |
| `foreground/tex-exports` | `pipeline/exports` | same repo-relative path | 16 KiB; manuscript-live by catalog |
| `review-ledger/figure_review` | `figure_review` | same repo-relative path | 45.2 MiB; live by catalog |
| `dispersion/chime-dm` | `pipeline/analysis/chime_dm` | same repo-relative path | 2.0 MiB; mixed by catalog |

Catalog declarations for these links are at
[results_library_catalog.yaml:68-76](../../../../scripts/results_library_catalog.yaml#L68),
[109-138](../../../../scripts/results_library_catalog.yaml#L109), and
[160-200](../../../../scripts/results_library_catalog.yaml#L160).

The ninth results-library link is live:
`compute-scratch/FLITS_RUNS/flits-local-runs` points to
`~/Developer/scratch/flits-local-runs` (about 65 MiB in the stale inventory).

### 5. Obsolete CHIME path references

#### Broken operational authorities

These default to one co-mingled `dsa110/DSA_bursts` directory while processing
both telescopes. They now fail for CHIME unless explicitly overridden or fed a
separately assembled directory:

- `scripts/plot_codetection_gallery.py:13,44,164-177`
- `scripts/plot_codetection_triptych.py:48,55,311,414`; consequently
  `scripts/plot_codetection_data_grid.py:40,349`
- `scripts/audit_fig1_residual_drift.py:31,66-70,187`
- `scripts/audit_fig1_frequency_axes.py:18,128-139,225`
- `analysis/dm-joint-phase-v2/code/scripts/run_joint_dm_phase.py:259`
- `pipeline/dispersion/dm_power_analysis.py:21,345-373,796-814`
- `pipeline/dispersion/dm_campaign/configs/battery.yaml:3`
- `pipeline/flits/batch/codetection_data.py:68-79`
- `pipeline/analysis/scattering-refit-2026-06/refit-2026-07-07/scripts/{inspect_profiles.py:18,refit_runner.py:28}`
- `pipeline/analysis/scattering-refit-2026-06/scint_census/scint_subband_alpha.py:35`
- Four historical refit configs still point to CHIME cubes in the old tree:
  `casey_chime_run.yaml:15`, `hamilton_chime_run.yaml:15`,
  `wilhelm_chime_run.yaml:15`, `zach_chime_run.yaml:15`.
- `scripts/build_l0_certificates.py:36-38,102,113,150` as described above.

Current figure fit artifacts for Hamilton and Zach already point into
`chimefrb/CHIME_bursts`; the Casey artifact uses the equivalent session-mounted
`chimefrb` path. Those are not obsolete.

#### Broken current documentation/metadata authorities

- `figures/catalog.yaml:165,182` declares the Figure 1 producer's sole external
  input as the old mixed directory.
- `repro_manifest.csv:36-37,39` says 24 or 6 dual-band inputs all live there.
- `pipeline/DATA_SOURCES.md:60-67,93-95` still calls the local directory a
  24-cube CHIME+DSA store and gives a combined sync recipe.
- `pipeline/scintillation/DATA_PROVENANCE.md:235-237` makes the same 24-cube
  claim.
- `pipeline/machine_inventory.yaml:182-185,772-778` models the old combined
  custody surface.
- Generated `docs/rse/certificates/l0-certificates.json` retains old CHIME
  `local_path` values and should not be used as current location authority.

#### Harmless historical references

These correctly describe past state or preserve executed provenance and should
not be read as current run instructions: dated handoffs, Claude Science frame
transcripts/execution logs, archived refit configs/results, protocol journal
entries, and migration audit code. A targeted search found them under
`docs/rse/specs/handoff/`, `docs/rse/claude-science/frames/`,
`docs/rse/protocols/journal.jsonl`, old `pipeline/analysis/scattering-refit-*`
outputs, and `pipeline/scripts/migration/audit_arc_delta.py`.

DSA-only references remain valid. CHIME upchannelized and packaged
scintillation products also legitimately remain under `dsa110/`; the split
applies specifically to the full-resolution CHIME cubes.

## Synthesis

1. The local bytes are not one authority. Full-resolution derived cubes now
   have clean instrument custody; upchannelized, remediated, packaged, and
   result products remain separate derived lineages with different receipts.
2. The registry is the manuscript claim ledger. The results library is a
   campaign navigation/materialization layer. They are complementary but
   currently unreconciled: no shared IDs, stale generated inventory, and no
   registry coverage for remediated/packaged inputs or library custody.
3. The exact eight failures are stale absolute symlinks to a deleted worktree.
   Their canonical repo sources still exist. Repair requires an authorized
   relink/refresh wave, not data recovery.
4. The CHIME directory split is only partially propagated. Several current
   producers and authority documents still require a co-mingled directory.
   Historical records can remain unchanged if explicitly treated as history.
5. Trust stays fail-closed. Existence and recorded hashes establish byte
   identity, not raw status or scientific acceptance. All 36 derived-input
   registry rows remain pending; the two-band campaign remains blocked in the
   registry ([results-registry.toml:500-510](../../control/results-registry.toml#L500)).

## Unverified / deliberately deferred

- No large-array hash was recomputed. Recorded SHA-256/MD5 values remain claims
  from the registry and receipts.
- No deep semantic audit of all 777 `dsa110/` files or 331 library files.
- No remote h17/CANFAR/Drive custody verification; separate authority tickets
  cover those surfaces.
- No proof that every historical result-library materialization was complete.
  The current dry-run conflicts prevent that inference.
- No trust promotion. Owner spot-check and science gates remain separate.

## Sources

- [`docs/rse/control/results-registry.toml`](../../control/results-registry.toml)
- [`scripts/results_library_catalog.yaml`](../../../../scripts/results_library_catalog.yaml)
- [`scripts/build_results_library_inventory.py`](../../../../scripts/build_results_library_inventory.py)
- [`scripts/materialize_results_library.py`](../../../../scripts/materialize_results_library.py)
- [`docs/rse/specs/results-library-INDEX.md`](../results-library-INDEX.md)
- Local: `~/Data/Faber2026/{README.md,chimefrb/README.md,dsa110/DSA_bursts/README.md}`
- Local receipts: `dsa110/upchan_codetections/PROVENANCE.md`,
  `dsa110/upchan_codetections_remediated_20260718/PROVENANCE_REMEDIATION.md`,
  `results-library/historical/2026-07-20-pipeline-diagnostics/{ARCHIVE.md,SHA256SUMS}`
