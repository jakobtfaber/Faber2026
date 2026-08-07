# Owner queue walkthrough (manual trigger — never scheduled)

When the owner says **"walk me through my queue"**:

1. Run `python3 scripts/owner_queue.py --check`, then
   `python3 scripts/owner_queue.py`.
2. Show one generated decision card at a time. Open its evidence before asking.
3. Record the selected choice at the card's recorder path. Never leave the
   decision only in chat.
4. Regenerate after each choice. Stop when asked or when the queue is empty.

Wayfinder tickets and figure-review manifests are the only queue authorities.
Board lines link to them; technical pull-request review is not owner-queue work.
A pending figure receipt counts only when its candidate hash matches exactly.

Every card must contain one decision, two or three choices, one recommendation,
at most three context facts, one to three evidence links, the effect, and the
recording destination. Cards carry one of three kinds: `scientific`, `visual`,
or `operational` (an authority or admission decision over an operational
surface, such as ratifying the Jupyter surface — owner-only, but not a
manuscript judgment). No kind auto-resolves. Silence leaves promotion and
claims blocked.

Outside a requested walkthrough, report only: **"N decisions queued."**
Do not repeat decision requests in chat.

Assignment does not remove a human-review ticket. Resolved tickets, exact-hash
approval receipts, and explicit batch dispositions remove items on regeneration.

(This doc is the tracked copy; the machine-local `CLAUDE.md`/`AGENTS.md`
briefs mirror it.)
