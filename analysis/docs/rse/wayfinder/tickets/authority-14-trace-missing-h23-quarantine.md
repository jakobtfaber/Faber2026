# Trace the missing h23 quarantine

- Type: `wayfinder:research` (AFK)
- Status: resolved
- Assignee: —
- Blocked by: —
- Map: [Project authority and custody](../map-project-authority-and-custody.md)
- Triage: `ready-for-agent`

## Question

What happened to the recorded 137 GB h23 quarantine after the last verified
observation? Trace first-party migration logs, shell histories where authorized,
handoffs, receipts, destination manifests, and other verified copies. Identify
the last known path/time, any deliberate removal or move, the exact artifact
classes involved, and whether Drive/iacobus or another archive proves their
custody. Read-only; do not reconstruct, transfer, delete, or infer parity from
similar names.

## Answer

Resolved by
[`Research: missing h23 quarantine`](../../specs/research/research-authority-h23-quarantine-2026-07-20.md).

The last positive first-party observation was 2026-07-06 21:52 PDT. By the
2026-07-20 live probe, the parent quarantine, recorded 137 GB tree, and three
original source directories were absent. Repository records, local handoffs,
transfer logs, iacobus metadata, and a targeted non-secret h23 history search
contain no later move, deletion, mount, or disposal receipt. The disappearance
is unexplained.

Transfer logs and downstream manifests prove substantial class-level custody
on iacobus and Google Drive, but not exact parity with the vanished tree.
`burstprop_paper` also moved into a separate iacobus CHIME_Morphologies tree and
was excluded from the later Drive upload. Record the h23 quarantine as missing
and byte-level custody as unproved; do not infer safe disposal or reconstruct
the tree without new evidence.
