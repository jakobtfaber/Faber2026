# Owner queue walkthrough (manual trigger — never scheduled)

When the owner says anything like **"walk me through my queue"**, in any
agent session:

1. Run `python3 scripts/owner_queue.py` — regenerates `OWNER_QUEUE.md` from
   the wayfinder frontier (open + unblocked + owner-facing tickets),
   figure-review batches without approval receipts, ✋-marked BOARD.md
   tasks, and open PRs (`gh`, best-effort). Verify heuristics before
   presenting — e.g. confirm a "no receipt" batch is genuinely undecided.
2. Walk the queue **one item at a time**: state the decision plainly, show
   the evidence it needs (figure full-size, diff, ticket body) *before*
   asking, capture the owner's call, and **record it at the source** —
   ticket resolution, `figure_review.py decide`, registry note, PR
   merge/comment — never only in chat.
3. Regenerate between items; stop when the owner says stop or the queue is
   empty. Commit state changes via the normal branch→PR flow before ending.

Standing rule: agents adding work that needs the owner must make it
discoverable by these sources (owner-facing wayfinder ticket, figure-review
batch, ✋ board line, or PR). **A request that isn't in the queue doesn't
exist.**

(This doc is the tracked copy; the machine-local `CLAUDE.md`/`AGENTS.md`
briefs mirror it.)
