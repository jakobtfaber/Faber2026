# Complete Drive-to-iacobus parity and duplicate adjudication

- Type: `wayfinder:task` (AFK)
- Status: resolved
- Assignee: —
- Blocked by: —
- Map: [Project authority and custody](../map-project-authority-and-custody.md)
- Triage: `ready-for-agent`

## Question

Run a bounded, logged, read-only full comparison between the dated iacobus
recovery quarantine and Google Drive, allowing enough time to finish. Explain
the local-only provenance receipt and the duplicate Drive object without
changing either side. Produce a manifest of matches, one-sided paths, size/hash
differences where available, command/version/timestamps, and an explicit parity
verdict suitable for the data-authority decision.

## Answer

Resolved by
[`Research: Drive-to-iacobus parity`](../../specs/research/research-drive-iacobus-parity-2026-07-20.md).

All 5,437 project-data paths match by MD5. There are no size/hash differences
and no unexplained one-sided paths. The sole local-only path is the deliberate
iacobus recovery receipt. Drive's extra object is a second same-name filterbank
with a distinct object ID but the same size, timestamp, and MD5 as both the
first Drive object and the iacobus file.

Content parity therefore passes; strict one-to-one object parity fails. Neither
side was changed. Retaining the iacobus quarantine and any Drive deduplication
remain owner decisions.
