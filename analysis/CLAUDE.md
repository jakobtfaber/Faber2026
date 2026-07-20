# CLAUDE.md

Agent brief for the **Faber2026** manuscript repo.

## Response style (required for all responses in this repo)

- Be extremely concise. Sacrifice grammar for the sake of concision;
  telegraphic fragments are fine.
- No shorthand or unnecessary jargon. Write the plain term instead of an
  acronym or project codename; expand any unavoidable acronym at first use.
  Explain domain statistics (e.g. confidence bounds, order statistics) in
  plain English when they appear.

## Owner queue walkthrough (manual trigger — never scheduled)

When the owner says anything like **"walk me through my queue"**:

1. Run `python3 scripts/owner_queue.py` (regenerates `OWNER_QUEUE.md` from
   the wayfinder frontier, figure-review batches, ✋ board tasks, and open
   PRs). Verify its heuristics before presenting — e.g. confirm a
   "no receipt" figure batch is genuinely undecided.
2. Walk the queue **one item at a time**: state the decision plainly, show
   the evidence it needs (figure full-size, diff, ticket body) before asking,
   capture the owner's call, and **record it at the source** (ticket
   resolution, `figure_review.py decide`, registry note, PR merge/comment) —
   never only in chat.
3. Regenerate the queue after each item; stop when the owner says stop or
   the queue is empty. Commit any state changes via the normal branch→PR
   flow before ending.

Agents adding work that needs the owner must make it discoverable by these
sources (an open owner-facing wayfinder ticket, a figure-review batch, a
✋ board line, or a PR) — a request that isn't in the queue doesn't exist. Science/domain context and the
trust-reset state live in [`CONTEXT.md`](CONTEXT.md) (and
[`pipeline/CONTEXT.md`](pipeline/CONTEXT.md)); this file carries operational
standing instructions only.

## Standing authorization — git push / PR (owner grant, 2026-07-08)

The repository owner has granted a **standing, cross-session authorization**: an
agent may **push branches and open/merge pull requests** on this repo (and the
owner's other configured repos) **without asking for per-action approval**.

Scope and guardrails — this authorization is not a licence to be careless:

- **One-way doors stay careful.** Before merging, confirm the branch is
  fast-forwardable (or the merge is intended) and scoped to the correct repo.
  Never force-push a branch that has concurrent writers.
- **Prefer the clean path.** Land figure/section updates via a focused branch +
  PR that mirrors existing precedent (e.g. the `ms/…` jointmodel-panel PRs),
  not a divergent-branch merge that drags in unrelated submodule-pointer bumps.
- **Never delete or rewrite shared history** (`push --force`, branch deletion on
  `main`, `reset --hard` on a shared ref) without an explicit, separate request.
- **The `pipeline/` submodule pin is deliberate** — do not bump the gitlink as a
  side effect of a manuscript change; that is its own reviewed step.

> Note: a repo file records the *preference* so future sessions inherit it. The
> platform's enforced no-approval **gate** is understood to live in the agent's
> Managed-Agent `permission_policy` (should be set to `always_allow`) plus the
> per-session GitHub token — control-plane config, not writable from inside a
> session. These field names are unverified against the live Managed-Agents
> schema (confirm before relying on them). See the handoff in `docs/rse/specs/`
> if the approval prompt reappears.
