# Choose the results-library and CHIME-path repair batch

- Type: `wayfinder:grilling` (HITL)
- Status: resolved
- Assignee: —
- Blocked by: [Choose the data and results authority policy](authority-09-choose-data-results-authority.md)
- Map: [Project authority and custody](../map-project-authority-and-custody.md)
- Delegation: [Standing delegated decision authority](../standing-delegation-2026-07-20.md)
- Triage: `ready-for-human`

## Question

Given the ratified data/results authority policy, which repair wave should
relink the eight results-library navigation entries, reconcile the catalog and
inventory, and update current CHIME path authorities? Choose the exact current
producer/config/document set, required regeneration receipts, and exclusions
for immutable historical records. Decide whether remediated and packaged input
lineages receive registry identifiers in the same wave or a later one.

## Answer

Resolved 2026-07-20 under the
[standing delegated decision authority](../standing-delegation-2026-07-20.md).
The accepted recommendation is one bounded repair batch with phase barriers.
This decision authorizes planning and implementation preparation only; it does
not itself relink, move, delete, materialize, or promote any bytes or claims.

### Stable identities

- A **result ID** is the claim-level ID in `results-registry.toml`.
- A **library slot ID** is the navigation/container ID in
  `results_library_catalog.yaml`.
- A slot may contain zero or more results. Catalog entries carry explicit
  `result_ids`; registry rows carry explicit `library_slots`. Do not force a
  false one-to-one mapping.
- A derived input lineage receives its own **input ID**. Input identity and
  byte certification do not imply scientific trust.

### Repair batch

1. **Freeze the action packet.** Record the parent commit, pipeline pin,
   catalog and registry hashes, exact source/destination list, inode/type/link
   state, byte or tree manifests, owners, open-file/process checks, dry-run,
   exclusions, rollback, and observation time. Stop on drift.
2. **Repair Git authorities first.** Add exact-target selection and a
   machine-readable receipt to the inventory builder; retain the materializer's
   `--only` fail-closed behavior. Introduce separate `chime_full_root` and
   `dsa_full_root` inputs. No current producer may use one mixed directory.
3. **Land and validate the parent and pipeline changes separately.** The
   pipeline pin changes only through its own reviewed step. Regenerate the
   input certificates and verify all 36 recorded hashes, sizes, frequency
   orders, and paths before any link mutation.
4. **Repair navigation from a clean canonical `main` checkout.** Replace only
   the eight broken catalog links, create the two cataloged-but-missing links,
   and restore only the three already-materialized source links listed below.
   Re-run a dry-run after every class and retain rollback targets.
5. **Regenerate inventory and receipt.** The generated inventory must name the
   canonical checkout, exactly match the accepted catalog, contain no deleted
   worktree target, resolve every managed link, enumerate every real-directory
   exception, and pass fresh readability plus manifest checks.

The eight exact broken-link replacements retain their existing slot IDs:

- `scintillation.chime`
- `dispersion.chime-dm`
- `foreground.tau-consistency-catalog`
- `foreground.budget-exports`
- `foreground.v3-energetics`
- `manuscript.figures`
- `manuscript.repro-manifest`
- `review.figure-review`

Create the two missing catalog links for
`scintillation.chime-window-2026-07-17` and
`archive.outdated-science-2026-07-17` only after their sources and intended
trust tags revalidate.

Restore these three repository-side links to already-real library bytes only
after full tree-manifest comparison:

- `scattering.dm-locked-2026-07-14`: `fit_summaries`
- `scattering.dm-locked-2026-07-14`: `ppc`
- `dispersion.dm-joint-phase-v2-parent`: `diagnostics`

### Exact current authority set

Parent producers and configuration in scope:

- `scripts/results_library_catalog.yaml`
- `scripts/build_results_library_inventory.py`
- `scripts/materialize_results_library.py`
- `scripts/build_l0_certificates.py`
- `scripts/plot_codetection_gallery.py`
- `scripts/plot_codetection_triptych.py`
- `scripts/plot_codetection_data_grid.py`
- `scripts/audit_fig1_frequency_axes.py`
- `scripts/audit_fig1_residual_drift.py`
- `analysis/dm-joint-phase-v2/code/scripts/run_joint_dm_phase.py`
- `figures/catalog.yaml`

Parent registry and current documents in scope:

- `docs/rse/control/results-registry.toml`
- generated `docs/rse/certificates/l0-certificates.json`
- `docs/rse/specs/results-library-INDEX.md`
- `repro_manifest.csv`

Pipeline producers, configuration, and current custody documents in scope:

- `dispersion/dm_power_analysis.py`
- `dispersion/dm_campaign/configs/battery.yaml`
- `flits/batch/codetection_data.py`
- `DATA_LOCATIONS.md`
- `DATA_SOURCES.md`
- `machine_inventory.yaml`
- `scintillation/DATA_PROVENANCE.md`

All dual-band interfaces must name both full-resolution roots. DSA-only paths
remain valid. CHIME upchannelized, remediated, and packaged products remain
under their distinct derived-lineage roots; they are not moved into
`chimefrb/CHIME_bursts`.

### Input identifiers

Receipted remediated and packaged input lineages receive registry identifiers
in this same batch, not later:

- `input.remediated-20260718.<nick>` for each complete two-band remediation
  packet;
- `input.scintillation-package.<package-id>.<nick>.<band>` for each package
  with a complete manifest and provenance receipt.

Each row records exact files, sizes, SHA-256 hashes, producing commit/pin,
source input IDs, operation, mask/frequency metadata, receipt path, trust, and
current/superseded state. Incomplete or mixed packages receive no fabricated
row; they remain listed as exceptions until a complete manifest exists.

### Fail-closed exclusions

- Do not run the two `would-conflict-both-real` materializations:
  `scintillation.dsa-lorentzian-2026-07-07` and
  `dispersion.pipeline-results-root`. Their bytes require independent
  comparison and adjudication.
- Preserve `scattering/jointmodel` exactly. Its inventory-only
  `scattering.jointmodel-latest` entry came from an unmerged JointTF branch;
  record it as an unmanaged hold rather than importing, deleting, or promoting
  it in this batch.
- Do not rewrite dated handoffs, protocol journal entries, Claude execution
  records, figure-review evidence, stored result provenance, archived refit
  configurations, migration audits, or other executed historical receipts.
- Do not alter `historical/2026-07-20-pipeline-diagnostics`, Drive objects,
  CANFAR objects, h17 outputs, or the live external FLITS-runs link.
- No byte deletion, cross-authority move, trust promotion, manuscript claim
  change, service restart, or science adoption is part of this repair.

### Acceptance

Live checks at `2026-07-21T04:39:33Z` reproduced the eight stale links, the
stale 19-entry inventory rooted in a deleted worktree, the current 18-entry
catalog, three `would-relink-src` cases, and two
`would-conflict-both-real` cases. The batch is accepted only when task-scoped
tests pass, both repositories are clean at their recorded commits, every
managed link resolves, all manifests verify, dry-run reports no unplanned
mutation, and the post-action receipt proves every exclusion remained
unchanged.
