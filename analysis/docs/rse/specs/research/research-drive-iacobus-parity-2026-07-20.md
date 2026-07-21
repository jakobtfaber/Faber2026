# Research: Drive-to-iacobus parity

**Date:** 2026-07-20 local / 2026-07-21 UTC
**Scope:** Read-only comparison of the dated iacobus recovery quarantine with
Google Drive. Neither compared tree was changed.
**Related:**
[`authority-15`](../../wayfinder/tickets/authority-15-complete-drive-iacobus-parity.md),
[`evidence packet`](evidence/drive-iacobus-parity-2026-07-20/)

## Verdict

Content parity passes for every project-data path: 5,437 paths match by MD5,
with no size/hash differences and no unexplained one-sided path.

Strict object parity fails. Iacobus has one deliberate local-only
`PROVENANCE.md` recovery receipt. Drive has two distinct objects with the same
path for one 503,316,768-byte filterbank. Both Drive objects and the single
iacobus file have MD5 `5299fd6b9a9598777e159815262083a0`.

This result supports Drive as the processed-data authority and iacobus as its
dated recovery copy. It does not authorize deleting the iacobus quarantine or
deduplicating Drive; those are separate owner decisions.

## Compared surfaces

| Side | Exact root | Count | Logical bytes |
|---|---|---:|---:|
| iacobus | `/Users/iacobus/Research/_quarantine/CHIME_DSA_Codetections-drained-20260713` | 5,438 files | 262,364,454,211 |
| Drive | `gdrive-jakob:Research/CHIME_DSA_Codetections` | 5,438 objects | 262,867,770,271 |

Equal totals do not mean one-to-one identity. Iacobus contains 5,437 matched
data paths plus the 708-byte receipt. Drive contains the same 5,437 unique data
paths plus a second 503,316,768-byte object at one of those paths. Their byte
total difference is therefore 503,316,768 minus 708 = 503,316,060 bytes.

## Full comparison

Host: `iacobus`. Tool: rclone 1.73.5 on Darwin amd64. Start:
2026-07-21 03:01:06 UTC. Finish: 03:08:47 UTC. Elapsed: 7m27s.

The executed command was:

```text
rclone check <local_root> <remote_root> --checkers 8 \
  --combined combined.txt --match matches.txt --differ different.txt \
  --missing-on-dst local-only.txt --missing-on-src drive-only.txt \
  --error errors.txt --log-file rclone.log --log-level INFO
```

Rclone selected MD5 comparison. Results:

| Status | Count | Manifest |
|---|---:|---|
| MD5 match | 5,437 | [`matches.txt`](evidence/drive-iacobus-parity-2026-07-20/matches.txt) |
| Different size/hash | 0 | [`different.txt`](evidence/drive-iacobus-parity-2026-07-20/different.txt) |
| Local-only path | 1 | [`local-only.txt`](evidence/drive-iacobus-parity-2026-07-20/local-only.txt) |
| Drive-only unique path | 0 | [`drive-only.txt`](evidence/drive-iacobus-parity-2026-07-20/drive-only.txt) |
| Other recorded errors | 0 | [`errors.txt`](evidence/drive-iacobus-parity-2026-07-20/errors.txt) |

The complete status-prefixed path manifest is
[`combined.txt`](evidence/drive-iacobus-parity-2026-07-20/combined.txt), SHA-256
`45ca962fd818bf97ec38345eb7d31b82f6673665f1f379cd9d4a223fce95c648`.
The run exited 1 solely because the expected local receipt counts as a
difference. The final log reports 5,437 matching files, one missing destination
file, and one difference.

## Exceptions adjudicated

### Local-only recovery receipt

`PROVENANCE.md` was created on iacobus after the July 13 drain. It records the
Drive destination, account, prior size-only verification, 5,437 matched data
files, transfer dates and logs, a sentinel checksum, and the rule that the
quarantine must not be deleted before independent re-verification. It is
recovery metadata, not omitted project data, so its absence from Drive is
explained and acceptable.

### Duplicate Drive object

Drive contains two objects at:

```text
archive/OLD_CHIME_DSA_Codetections/polcal_fils/wilhelm_221203aaaa/
221203aaaa_dev_polcal_I.fil
```

Their IDs are `1IzGDQlyrgB_yyT2S0CqtsVGRDm8JbBGg` and
`1jyf9jh4MOkx-IIAHSBo-rNyn6VZ49gGq`. Both report size 503,316,768 bytes,
modification time 2024-08-24 14:06:59 UTC, and MD5
`5299fd6b9a9598777e159815262083a0`; the iacobus file has the same size and MD5.
Rclone logged the duplicate and ignored the second object during path matching.
This is a duplicate-object ambiguity, not a content mismatch. No object was
renamed, moved, or removed.

## Evidence integrity

The evidence directory contains the command, tool version, timestamps, exit
code, full manifests, compressed raw log, size summary, duplicate listing,
local comparison,
and [`SHA256SUMS`](evidence/drive-iacobus-parity-2026-07-20/SHA256SUMS). The
comparison and duplicate inspection were read-only; report files were written
only outside the compared trees and then copied into this repository.
