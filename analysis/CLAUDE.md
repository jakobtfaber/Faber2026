# CLAUDE.md

Agent brief for the **Faber2026** manuscript repo.

## Response style (required for all responses in this repo)

- Be extremely concise. Sacrifice grammar for the sake of concision;
  telegraphic fragments are fine.
- No shorthand or unnecessary jargon. Write the plain term instead of an
  acronym or project codename; expand any unavoidable acronym at first use.
  Explain domain statistics (e.g. confidence bounds, order statistics) in
  plain English when they appear.

## Orient with the knowledge base before grepping

Before exploratory `grep`/`glob`/file-reading to reconstruct context, run
`python3 scripts/kb search "<topic>"` — hybrid keyword+semantic search over
manuscript docs, wayfinder tickets, parent and analysis git history, analysis
code, configs, and cited references, with ranked
cross-source results. Filter with `--source tickets|docs|git|code|config|refs`.
Refresh after changes with `make kb-index` (incremental, seconds when
embeddings are current). See [`docs/rse/knowledge-base.md`](docs/rse/knowledge-base.md).
Fall back to grep for exhaustive sweeps (every call site, every match).

## Agent skills

### Issue tracker

Local Markdown maps and tickets live under `docs/rse/wayfinder/`. See
`docs/agents/issue-tracker.md`.

### Triage labels

Use the default Matt Pocock skill labels. See
`docs/agents/triage-labels.md`.

### Domain docs

Use the manuscript and fitting context at `CONTEXT.md`. See
`docs/agents/domain.md`.

## Owner queue walkthrough (manual trigger — never scheduled)

When the owner says anything like **"walk me through my queue"**:

1. Run `python3 scripts/owner_queue.py --check`, then regenerate
   `OWNER_QUEUE.md` from Wayfinder tickets and figure-review manifests.
2. Walk the queue **one item at a time**: state the decision plainly, show
   the evidence it needs (figure full-size, diff, ticket body) before asking,
   capture the owner's call, and **record it at the source** (ticket
   resolution, `figure_review.py decide`, registry note, PR merge/comment) —
   never only in chat.
3. Regenerate the queue after each item; stop when the owner says stop or
   the queue is empty. Commit any state changes via the normal branch→PR
   flow before ending.

Agents adding work that needs the owner must place one decision card in an
owner-facing Wayfinder ticket or figure-review manifest. Boards and pull
requests link to that authority; they are not queue sources. Science context
lives in [`CONTEXT.md`](CONTEXT.md).

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
- **The parent `analysis/` pin is deliberate** — update it only as a focused,
  reviewed manuscript integration step.

> Note: a repo file records the *preference* so future sessions inherit it. The
> platform's enforced no-approval **gate** is understood to live in the agent's
> Managed-Agent `permission_policy` (should be set to `always_allow`) plus the
> per-session GitHub token — control-plane config, not writable from inside a
> session. These field names are unverified against the live Managed-Agents
> schema (confirm before relying on them). See the handoff in `docs/rse/specs/`
> if the approval prompt reappears.
