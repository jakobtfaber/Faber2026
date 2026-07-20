# Issue tracker: Local Markdown

Planning maps and decision tickets for this repo live under
`docs/rse/wayfinder/`. Existing maps and tickets retain their current names.

## Conventions

- Map: `docs/rse/wayfinder/map-<effort>.md`
- Child ticket: `docs/rse/wayfinder/tickets/<effort>-<NN>-<slug>.md`
- Existing ApJ submission tickets keep their unprefixed names.
- Ticket headers record `Type`, `Status`, `Assignee`, `Blocked by`, `Map`, and
  `Triage` when triage applies.
- Comments and supporting evidence are appended to the ticket, not duplicated
  in the map.

## When a skill says "publish to the issue tracker"

Create or update the appropriate map or ticket under `docs/rse/wayfinder/`.

## When a skill says "fetch the relevant ticket"

Read the referenced map or ticket file. Resolve relative links from the file
that contains them.

## Wayfinding operations

- **Map:** `docs/rse/wayfinder/map-<effort>.md`, with the destination, notes,
  linked decision gists, fog, and out-of-scope sections.
- **Child ticket:** one file under `docs/rse/wayfinder/tickets/`, with the
  decision question and tracker headers.
- **Blocking:** `Blocked by` links point to ticket files. A ticket is unblocked
  when every linked blocker has `Status: resolved`.
- **Frontier:** open, unblocked, unassigned child tickets, in map order.
- **Claim:** set `Assignee` before work. Do not claim owner-facing tickets on
  the owner's behalf.
- **Resolve:** record the answer in the ticket, set `Status: resolved`, clear
  the assignee when appropriate, then add one linked gist under the map's
  `Decisions so far` section.
- **Concurrency:** re-read the map and ticket headers immediately before every
  claim or resolution because other sessions may update them.
