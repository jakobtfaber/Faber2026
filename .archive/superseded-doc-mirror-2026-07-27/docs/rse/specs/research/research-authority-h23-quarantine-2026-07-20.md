# Research: missing h23 quarantine

**Date:** 2026-07-20
**Scope:** Internal, bounded, read-only trace of the recorded h23 quarantine.
**Codebase state:** parent `a7c4e0df`; `pipeline/` `c611139`. The checkout was
already dirty; this report changes no other path.
**Related:** [authority-14](../../wayfinder/tickets/authority-14-trace-missing-h23-quarantine.md),
[remote custody research](research-authority-remote-custody-2026-07-20.md)

## Question / Scope

What happened after the last verified observation of
`h23:/media/ubuntu/ssd/_quarantine/jfaber-drain-20260625`? Identify the last
known path and time, direct move or removal evidence, the artifact classes, and
whether iacobus or Google Drive proves custody. Sources were limited to repository
records, `~/handoffs`, local h23 transfer logs, the live iacobus manifest and
quarantine metadata, and safe live h23 metadata plus targeted non-secret shell
history matches. No transfer, reconstruction, deletion, or large-file hashing
was performed.

## Findings

### Answer

The last positive first-party observation is **2026-07-06 21:52:22 -0700**.
The repository journal records a live verification of the h23 quarantine at
that time, and the associated inventory note names
`jfaber-drain-20260625` as present
([journal.jsonl:20](../../protocols/journal.jsonl#L20),
[machine-inventory-verification-2026-07-06.md:17-25](../notes/machine-inventory-verification-2026-07-06.md#L17)).

A live probe at **2026-07-20 20:59:25 UTC** found the parent `_quarantine`
directory, the recorded quarantine, and all three original source directories
absent. The readable `/home/ubuntu/.bash_history` contained no match for the
quarantine path or its parent. Repository history, repository logs,
`~/handoffs`, local transfer logs, and iacobus metadata contain **no later move,
deletion, mount change, or disposal receipt**. Therefore the disappearance is
unexplained. There is no first-party basis to state that the tree was deliberately
removed, moved elsewhere, or safely disposed.

### What the quarantine contained

The June 25 closeout records a same-filesystem `mv` of exactly three top-level
trees into the quarantine: `archive` (about 86 GB), `burstprop_paper` (about
42 GB), and `chime_dsa_codetections` (about 8.8 GB), about 137 GB total
([PHASE5_CLOSEOUT.md:12-26](../../../../pipeline/docs/infrastructure/PHASE5_CLOSEOUT.md#L12),
[machine_inventory.yaml:616-629](../../../../pipeline/machine_inventory.yaml#L616)).
This is the only direct move record found. It moved the trees into quarantine;
it does not explain their later disappearance.

Before that move, the Phase 2 record says h23 data were copied or found already
present on iacobus: an old CHIME archive; `dsa110-scat`; burst-property burst
data; CHIME burst products; dispersion-measure material; Stokes waterfalls;
scattering outputs; and localization metadata
([MIGRATION_LOG.md:14-32](../../../../pipeline/docs/infrastructure/MIGRATION_LOG.md#L14)).
The local rsync logs independently retain transfer totals for several principal
classes:

- `archive/OLD_CHIME_DSA_Codetections`: 83,769,236,490 bytes already present;
  zero files transferred (`~/logs/h23_transfers/OLD_CHIME_DSA_Codetections.log:31-38`).
- `archive/dsa110-scat`: 6,292,269,655 bytes and 314 files transferred
  (`~/logs/h23_transfers/h23_dsa110_scat_archive.log:528-533`).
- `burstprop_paper/bursts`: 44,586,001,025 bytes and 132 files transferred
  (`~/logs/h23_transfers/h23_burstprop_bursts.log:271-276`).
- `chime_dsa_codetections/bursts`: 8,024,536,476 bytes and 166 files transferred
  (`~/logs/h23_transfers/h23_chime_bursts.log:246-251`).
- `chime_dsa_codetections/dm_budget`: 342,625,103 bytes; 845 files transferred
  (`~/logs/h23_transfers/h23_dm_budget.log:1047-1052`).

These are copy receipts from before quarantine, not removal receipts and not a
manifest of every byte in the later 137 GB tree.

### What downstream custody proves

The iacobus manifest attributes its archive, burst arrays, dispersion-measure
material, Stokes waterfalls, metadata, and scattering results to h23 and gives
counts, sizes, and per-class sentinels
([codetections_manifest.yaml:19-40](../../../../pipeline/codetections_manifest.yaml#L19),
[codetections_manifest.yaml:51-80](../../../../pipeline/codetections_manifest.yaml#L51)).
The project data-location record then maps those merged classes into the
CHIME--DSA collection and records a July 13 size-only Drive comparison with
zero differences and 5,437 matching files
([DATA_LOCATIONS.md:17-39](../../../../pipeline/DATA_LOCATIONS.md#L17)).

This proves substantial class-level custody and lowers the risk of scientific
data loss. It does **not** prove exact parity with the vanished quarantine:

1. Phase 2 deliberately treated several iacobus destinations as supersets or
   merged namespaces, rather than byte-for-byte mirrors.
2. The manifest uses selected sentinels and aggregate class metadata, not a
   complete file-hash manifest for the 137 GB quarantine.
3. `burstprop_paper` was moved on iacobus into the separate
   `~/Research/CHIME_Morphologies/` tree on June 26 and was explicitly excluded
   from the later CHIME--DSA Google Drive upload
   ([DATA_LOCATIONS.md:45-53](../../../../pipeline/DATA_LOCATIONS.md#L45)).

Accordingly, Google Drive/iacobus establish custody for named migrated classes,
not custody of every former h23 byte. Exact-byte parity remains unproved.

### Negative searches

- `~/handoffs`: no quarantine-path, 137 GB, move, or removal trace.
- Local `~/logs/h23_transfers`: transfer receipts exist through June 25; no
  post-July-6 move/removal/disposal record.
- Iacobus: no `~/logs/h23_transfers`; the active CHIME--DSA path is absent and
  the dated July 13 recovery quarantine plus its manifest/provenance are present.
- h23: targeted safe history search returned no quarantine-path command; current
  metadata confirms absence but supplies no cause.
- Repository history: June 25 quarantine action and July 6 verification only;
  no later disposition record.

## Synthesis

Custody status must remain fail-closed: **the h23 quarantine is missing after a
last verified observation on July 6, and no first-party disposition trace was
found**. Named data classes largely survive on iacobus and, except the separate
burst-property tree, in the Drive authority chain. That is recovery coverage,
not exact parity. Do not infer safe deletion, reconstruct the quarantine, or
close the byte-level custody gap without a later receipt or a complete manifest
comparison.

## Sources

- Repository migration and custody records cited inline.
- Local read-only transfer logs under `~/logs/h23_transfers/`.
- Live read-only `ssh` metadata and targeted safe history probe on h23,
  2026-07-20 20:59:25 UTC.
- Live read-only iacobus path and manifest metadata, 2026-07-20.
