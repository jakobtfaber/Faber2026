# Reverify remote and institutional custody

- Type: `wayfinder:research` (AFK)
- Status: resolved
- Assignee: —
- Blocked by: —
- Map: [Project authority and custody](../map-project-authority-and-custody.md)
- Triage: `ready-for-agent`

## Question

What Faber2026 code, data, results, logs, and quarantines currently exist on
h17, iacobus, Google Drive, h23, HPCC, and CANFAR? Reconcile live paths, sizes,
counts, hashes or sampled parity, transfer receipts, and host roles against
`pipeline/machine_inventory.yaml` and the July verification note. Explain h17
growth, the iacobus 244 GB post-transfer quarantine, the missing h23 quarantine,
and every access limitation. Treat CANFAR as explicitly unverified until
[Restore CANFAR read-only verification access](authority-05-restore-canfar-read-access.md)
is resolved; do not mutate any host.

## Answer

Resolved by
[`Research: remote and institutional custody`](../../specs/research/research-authority-remote-custody-2026-07-20.md).

Google Drive remains reachable at 244.815 GiB and 5,438 objects. The former
iacobus staging tree is absent from its old path and retained as a dated 244.36
GiB recovery quarantine with 5,438 files. Size, count, transfer receipts, and a
sentinel MD5 agree, but a current full comparison timed out after exposing a
local provenance file and a duplicate Drive object; present-day full parity is
not established.

h17 holds 73.89 GiB and 13,795 files; its growth is explained by July compute
products and does not make it an authority. The recorded h23 137 GB quarantine
and original codetection paths are absent with no recovered explanation. HPCC's
retired 5.58 GiB quarantine is intact and the old path is only a symlink.
CANFAR remains explicitly unverified because its certificate expired.
