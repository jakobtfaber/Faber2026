# Approve retirement of the three provenance-map branches

- Type: `wayfinder:grilling` (HITL)
- Status: open
- Assignee: owner
- Blocked by: —
- Map: [ApJ submission](../map-apj-submission.md)
- Authorization: closure campaign, owner charter 2026-07-26

## Question

May the following three branches be deleted? Each was a DECIDE item on the
2026-07-26 closure roster and is now evidence-resolved as fully absorbed or
superseded (details in
[`receipt-phase2-closures-2026-07-26.md`](../../specs/receipt-phase2-closures-2026-07-26.md),
section 4):

1. Faber2026-analysis `publish/repository-provenance-map` — repository map on
   main via #106; replay-pin move superseded by the `78b448f0` pin; the
   REPRODUCE.md refresh landed via #122.
2. Faber2026 `publish/repository-provenance-map-followup` — README link on
   main; both gitlink targets superseded by main's pins.
3. dsa110-FLITS `publish/repository-provenance-map` — its single path-repair
   commit is on FLITS main verbatim.

These were not part of the consumed 132-name retirement approval, so deletion
needs a separate owner approval naming these exact refs. The fourth DECIDE
item, FLITS `codex/chromatica-cross-band-scintillation`, is excluded — it is
scint material held for the Phase-4 walkthrough.
