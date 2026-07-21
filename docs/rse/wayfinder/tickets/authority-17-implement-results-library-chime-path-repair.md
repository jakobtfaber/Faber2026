# Implement the results-library and CHIME-path repair batch

- Type: `wayfinder:task` (AFK)
- Status: resolved
- Assignee: Codex
- Blocked by: [Choose the results-library and CHIME-path repair batch](authority-13-choose-link-and-chime-path-repair.md)
- Map: [Project authority and custody](../map-project-authority-and-custody.md)
- Triage: `ready-for-agent`

## Question

Execute the exact phased repair accepted in
[Choose the results-library and CHIME-path repair batch](authority-13-choose-link-and-chime-path-repair.md).
Freeze the action packet first; update only its approved current authorities;
repair only the approved links after their gates pass; regenerate the inventory
and receipts; validate the parent and pipeline repositories separately. Stop on
drift, incomplete input evidence, either both-real conflict, JointTF material,
historical records, byte movement or deletion, trust promotion, manuscript
claim changes, or service changes.

## Progress

Completed under the owner-approved bounded scope correction. The pipeline
change landed through [dsa110-FLITS #212](https://github.com/jakobtfaber/dsa110-FLITS/pull/212)
and the parent pins merged commit `ded8d195`.

Eight broken library links were replaced, two missing library links created,
and three repository links restored. All 13 resolve to their frozen targets;
the full inventory contains 18 catalog entries. Six excluded-tree manifests
and both rollback preimages remain unchanged. No real bytes moved or deleted.

The two both-real conflicts remain fail-closed for `authority-16`. Fifteen
incomplete input lineages are explicit exceptions; no identity was fabricated.
Parent tests passed 67/67 and pipeline tests passed 34/34. See the
[implementation](../../specs/implement-results-library-chime-path-repair.md),
[validation](../../specs/validation-results-library-chime-path-repair.md), and
[receipts](../../certificates/results-library-repair-2026-07-20/action-packet.json).
