# Approve retirement of the three provenance-map branches

- Type: `wayfinder:grilling` (HITL)
- Status: resolved — owner approved 2026-07-26; all three branches deleted
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

## Resolution — 2026-07-26

Owner approved in session ("closure-01 approved"). All three branches deleted
and confirmed gone by `ls-remote`; sha at deletion:

| Repository | Branch | Tip at deletion |
|---|---|---|
| Faber2026-analysis | `publish/repository-provenance-map` | `e753fa9cd43632e7edf3ef4be2760ff622212d2b` |
| Faber2026 | `publish/repository-provenance-map-followup` | `46aa13165c079892381a8533c6a38e5ebe0993ac` |
| dsa110-FLITS | `publish/repository-provenance-map` | `1d5633c1a118b47b7b0ae5b4b27a682a751f1b2b` |

Parent PR #216 was merged the same session (squash `ac004ece`, head verified
`1daecd625a18`), closing the campaign's last open parent pull request.
