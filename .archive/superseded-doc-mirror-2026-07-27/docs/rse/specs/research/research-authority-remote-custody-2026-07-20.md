# Research: remote and institutional custody

**Date:** 2026-07-20
**Scope:** Internal and live, read-only custody verification of h17, iacobus,
Google Drive, h23, HPCC, and CANFAR. No transfer, mutation, scheduler work,
service start, or credential action.
**Codebase state:** parent `a7c4e0df`; `pipeline/` `c611139`. The checkout was
already dirty; this report treats those concurrent edits as observed, not
settled.
**Related:**
[`authority-06`](../../wayfinder/tickets/authority-06-reverify-remote-custody.md),
[`machine inventory`](../../../../pipeline/machine_inventory.yaml),
[`2026-07-06 verification`](../notes/machine-inventory-verification-2026-07-06.md)

## Question / scope

Reconcile current remote custody with the June machine inventory and July
verification. Verify roles, paths, sizes, counts, sampled parity, and transfer
receipts. Explain h17 growth, the iacobus post-transfer quarantine, the missing
h23 quarantine, and access limits.

Method: bounded `ssh -o BatchMode=yes` probes using `hostname`, `test`, `stat`,
`du`, `find`, and read-only file reads; read-only `rclone size`, `lsd`, `md5sum`,
and `check`; local certificate date inspection. Sizes from `du -sk` are allocated
KiB; Google Drive size is logical bytes. No large file was downloaded or hashed.
The documented `python3 scripts/kb search` command could not run because
`scripts/kb` contains only bytecode caches, not an executable entry point.

## Codebase Findings

### Current custody summary

| Surface | Declared role | Live result | Custody status |
|---|---|---|---|
| h17 | Active compute and artifact cache | Workspace present: 77,474,984 KiB, 13,795 files. Twelve raw singlebeam HDF5 files remain in `chime_singlebeam/`. | Live compute custody verified; not data or code authority. |
| iacobus | Former staging source | Active source path absent. Drained tree present under dated quarantine: 256,229,092 KiB, 5,438 files, 994 directories. | Recovery copy verified present; retain. |
| Google Drive | Processed-data authority | 262,867,770,271 bytes (244.815 GiB), 5,438 objects, expected eight top-level directories. | Authority reachable. Current sampled parity passes; full current parity not established. |
| h23 | Retired source | Recorded 137 GB quarantine absent. Original codetection paths also absent. Residual root is 9,786,008 KiB and contains only five non-codetection directories. | Exact retired bytes unverified and presently missing from recorded path. |
| HPCC | Retired batch host | Quarantine present: 5,854,608 KiB, 68,693 files, including 22 migrated JSON files. Original path is a symlink to quarantine. | Retired quarantine verified; no second live tree. |
| CANFAR | Institutional VOSpace storage and compute | Local proxy certificate expired 2026-07-18 17:52:46 UTC. No VOSpace probe attempted. | Explicitly unverified. |

The canonical model names Google Drive as data authority, iacobus as staging,
h17 as active compute, and h23/HPCC as retired hosts
([machine_inventory.yaml:12-25](../../../../pipeline/machine_inventory.yaml#L12)).
That role model still fits, but its paths and counts are stale in several places.

### h17: growth is compute drift, not authority growth

The June inventory recorded about 65 GB and 2,275 files
([machine_inventory.yaml:568-590](../../../../pipeline/machine_inventory.yaml#L568));
the July 6 note described about 72 GB and active regeneration
([machine-inventory-verification-2026-07-06.md:20-23](../notes/machine-inventory-verification-2026-07-06.md#L20)).
The current workspace is 73.89 GiB allocated and 13,795 files: roughly 8.9 GiB
and 11,520 files above the June snapshot.

The stable large holdings remain the arc archive (37,091,269 KiB; 1,924 files),
twelve raw HDF5 files (13,974,912 KiB), `numpy/` (8,796,909 KiB), and DSA
filterbanks (6,881,344 KiB). Growth is explained by later compute products:
`upchan_codetections/` is now 3,313,036 KiB and 101 files versus 473 MB and 11
files in June ([machine_inventory.yaml:543-562](../../../../pipeline/machine_inventory.yaml#L543));
new or expanded `manifest_cubes/` is 2,976,104 KiB, `results/` 1,442,913 KiB,
`_integration_work/` 1,308,703 KiB, `dm_campaign/` 397,031 KiB, and
`experiments/` 173,826 KiB. Top-level modification times run through July 14.
The defective no-dedispersion quarantine remains at
`upchan_codetections/DEFECTIVE_nodedisp_20260703`.

This is expected working-state drift on the declared active compute host
([machine_inventory.yaml:484-504](../../../../pipeline/machine_inventory.yaml#L484)).
It does not promote h17 into a processed-data authority. Its `results/` and logs
are working artifacts unless separately receipted and promoted.

### iacobus and Google Drive: drain verified, full present-day parity open

The old live staging path `/Users/iacobus/Research/CHIME_DSA_Codetections` is
absent. Its dated recovery copy is live at
`/Users/iacobus/Research/_quarantine/CHIME_DSA_Codetections-drained-20260713/`.
It contains the expected eight data directories, `codetections_manifest.yaml`,
and `PROVENANCE.md`. The quarantine is 244.36 GiB allocated with 5,438 regular
files. The older iCloud mirror also remains: 228,903,080 KiB and 1,546 files.

The quarantine receipt says the source was moved there, never deleted, after a
July 13 `rclone check --size-only`: zero differences and 5,437 matching files;
remote size 244.815 GiB and 5,438 objects. It names the upload period, script,
logs, sentinel, and disposal gate. The transfer logs still exist under
`~/logs/gdrive_transfers/`. This closes the June inventory's deferred-upload
record ([machine_inventory.yaml:270-278](../../../../pipeline/machine_inventory.yaml#L270))
and agrees with the current data-location authority note
([DATA_LOCATIONS.md:17-28](../../../../pipeline/DATA_LOCATIONS.md#L17)).

Current live checks independently confirm the same Drive size and object count,
the expected eight top-level directories, and identical MD5 for
`metadata/interveners.ipynb` on quarantine and Drive:
`fabc288f97f826cc087cc29befe3a1d2`. A bounded full `rclone check --size-only`
did not finish within 120 seconds. Before timeout it reported the expected local-
only `PROVENANCE.md` and a duplicate Drive object named
`archive/OLD_CHIME_DSA_Codetections/polcal_fils/wilhelm_221203aaaa/221203aaaa_dev_polcal_I.fil`.
Therefore today's evidence is size/count plus sampled parity, not a new full-tree
parity receipt. Keep the quarantine until an independent full comparison resolves
the duplicate-object ambiguity; do not infer safe disposal from equal totals.

### h23: the recorded quarantine is missing

The inventory says h23 was retired after a partial 137 GB move into
`/media/ubuntu/ssd/_quarantine/jfaber-drain-20260625`, with archive,
`burstprop_paper`, and codetection children
([machine_inventory.yaml:599-629](../../../../pipeline/machine_inventory.yaml#L599)).
Today `/media/ubuntu/ssd/_quarantine` itself is absent. The three original
children beneath `/media/ubuntu/ssd/jfaber/` are also absent.

The residual root is 9.33 GiB allocated and contains exactly the expected
non-codetection top-level directories: `dsa110-continuum`, `frb_inventory`,
`nihari`, `scratch`, and `tools`. The three old CHIME quarantine candidate paths
from the July addendum are still absent. `/dataz/dsa110/T3` is only 99 KiB, not
the inventory's 59 TB claim; the separate candidates tree remains present, but
is pipeline state, not the missing quarantine. The July addendum already
identified the T3/path error
([machine-inventory-verification-2026-07-06.md:87-106](../notes/machine-inventory-verification-2026-07-06.md#L87)).

No read-only evidence explains when or why the 137 GB quarantine disappeared.
Its migrated classes are represented in the iacobus/Drive custody chain, but
that does not prove exact parity for every former h23 byte. Treat the h23
quarantine as missing and unavailable at its recorded path unless another
receipt or copy is found. No cleanup or reconstruction was attempted.

### HPCC: retired quarantine is intact

`/home/jfaber/_quarantine/flits-20260625` is present at 5.58 GiB allocated with
68,693 files. Its top level contains `dsa110-FLITS`, `venv`, `bin`, and small
runner files. The expected `_a1_fits` directory still contains 22 JSON files,
matching the migration record
([machine_inventory.yaml:28-47](../../../../pipeline/machine_inventory.yaml#L28)).
The parent quarantine README records the move-only date and restore command.

`/home/jfaber/flits` also exists, but it is only a symbolic link to the
quarantine, not a duplicate active tree. This reconciles the apparent
contradiction with HPCC's retired role and the inventory's 5.5 GB estimate
([machine_inventory.yaml:656-701](../../../../pipeline/machine_inventory.yaml#L656)).
No scheduler query or job was run.

### CANFAR: explicitly unverified

The inventory names CANFAR as institutional VOSpace custody and records the
certificate path and July 18 expiry
([machine_inventory.yaml:729-738](../../../../pipeline/machine_inventory.yaml#L729)).
Local certificate inspection confirms `notAfter=Jul 18 17:52:46 2026 GMT`.
Because it is expired, no `vls`, `vcp`, or CANFAR compute probe was attempted;
no renewal or credential request was made. The July 6 counts and prior 24/24
hash result remain historical evidence only
([machine-inventory-verification-2026-07-06.md:57-64](../notes/machine-inventory-verification-2026-07-06.md#L57)).
Current CANFAR paths, sizes, counts, and bytes remain unverified until
`authority-05` restores read-only access.

## Synthesis

1. Google Drive remains the reachable processed-data authority. Iacobus is now
   a dated recovery quarantine, not an active staging source. Current size,
   count, and one sentinel agree; full current parity remains open.
2. h17's growth is attributable to raw input retention and July compute/output
   subtrees. It remains active scratch and cache custody, not authority.
3. h23 is the material custody gap. Both its recorded quarantine and original
   codetection paths are absent. The surviving Drive/iacobus chain reduces loss
   risk but does not close exact-byte provenance.
4. HPCC is correctly retired: its quarantine is intact and its old path is only
   a compatibility link to that quarantine.
5. CANFAR stays fail-closed and unverified. Historical counts and hashes cannot
   be presented as a July 20 live result.

No remote disposition, consolidation, deletion, transfer, or trust promotion is
authorized by this research.

## Sources

- [`pipeline/machine_inventory.yaml`](../../../../pipeline/machine_inventory.yaml)
- [`pipeline/DATA_LOCATIONS.md`](../../../../pipeline/DATA_LOCATIONS.md)
- [`docs/rse/specs/notes/machine-inventory-verification-2026-07-06.md`](../notes/machine-inventory-verification-2026-07-06.md)
- Live read-only probes on h17, iacobus, h23, and HPCC, 2026-07-20
- Live read-only `rclone` metadata and sentinel hash on iacobus, 2026-07-20
- Local `openssl x509 -noout -dates` on `~/.ssl/cadcproxy.pem`, 2026-07-20
