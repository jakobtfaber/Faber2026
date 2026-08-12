---
name: running-tend
description: Guardrails for the tend bot acting autonomously on Faber2026 pull requests and issues.
---

# Running tend on Faber2026

`CLAUDE.md` and `AGENTS.md` already carry this repository's operating rules
and are loaded alongside this file. This file covers only what is specific
to an autonomous agent with write access acting on pull requests and
issues, without an owner in the loop.

## Hard prohibitions

**Keep manuscript and analysis changes separately scoped.** `analysis/`
is a plain directory of this repository (the former submodule and its pin
were retired in the 2026-08 monorepo consolidation). A manuscript,
workflow, or documentation change must not sweep in `analysis/` edits as
a side effect, and vice versa; a change that genuinely needs both sides
must say so explicitly in its pull-request body.

**Never edit scientific content.** Scientific judgment belongs to the
owner. Do not modify:

- claim wording, numerical values, uncertainties, or units in `main.tex`,
  any `.tex` section file, or the claim ledger;
- figures, figure data, or anything under `analysis/figures/`;
- fit results, derived measurements, or dispersion-measure values;
- `bursts.yaml`, catalogs, or any data product.

When a review finds a problem in scientific content — a claim that no
longer matches its source, a stale number, an inconsistent uncertainty —
report it in a pull-request comment or an issue with the evidence. Do not
"fix" it.

Mechanical work on prose, build tooling, workflows, tests, and
documentation is in scope, subject to the rest of this file.

## Scope discipline

Commit with explicit pathspecs, never `git add -A` or `git add .`. This
repository frequently carries unrelated dirty state; a broad stage sweeps
it into the commit.

One pull request does one thing. Do not bundle an adjacent cleanup,
a lint fix in an untouched file, or a documentation edit into a change
that is about something else.

"One thing" means one defect, not one call site. When the same defect
appears at several call sites, repair them together in one pull request
and name the sites in the body. The manuscript and `analysis/` separation
above forbids sweeping in an *unrelated* edit; it does not require
splitting a single defect across branches, and both this file and
`CLAUDE.md` already provide for a change that genuinely needs both trees
so long as the body says so.

Before opening a pull request, look for a sibling the bot already has
open on the same defect, and push to that branch instead of opening
another:

```bash
BOT_LOGIN=$(gh api user --jq '.login')
gh pr list --state open --author "$BOT_LOGIN" \
  --json number,title,headRefName,files \
  --jq '.[] | "\(.number) \(.title)\n  \([.files[].path] | join(" "))"'
```

Compare by the files the new change would touch, not by title. GitHub's
`mergeable` flag compares a branch against its base and never against
another branch, so two open bot branches that touch the same region of
one file both report `mergeable: true` and then collide when the owner
merges the second. The bot cannot see that collision through the usual
check; the owner absorbs it. When a sibling is on the same defect, or
edits the same region, extend the sibling rather than opening another.

## The daily item budget

Opening an issue or a pull request spends a shared, repository-wide daily
allowance. Every tend workflow starts with a preflight that counts the
issues and pull requests this bot has created so far today in UTC, and
aborts the job when that count exceeds `10 + (items over the previous six
days) / 3`. The abort happens before the model starts and applies to every
workflow, including the ones that create nothing.

Before `gh issue create` or `gh pr create`, check what is left:

```bash
BOT=tend-jakobtfaber
TODAY=$(date -u +%Y-%m-%d)
YESTERDAY=$(date -u -d yesterday +%Y-%m-%d)
SIX_DAYS_AGO=$(date -u -d '6 days ago' +%Y-%m-%d)
count() { gh api "search/issues?q=author:${BOT}+repo:${GITHUB_REPOSITORY}+created:$1" --jq '.total_count'; }
TODAY_POSTS=$(count "$TODAY")
PAST_POSTS=$(count "${SIX_DAYS_AGO}..${YESTERDAY}")
echo "today=${TODAY_POSTS} limit=$((10 + PAST_POSTS / 3))"
```

Those are the two queries the preflight itself runs, so the printed limit
is the one it will apply — it is ten only while the six-day baseline is
under three, and it was fourteen on 2026-08-07. Key the decision off that
number, not off ten: from three below the limit onward, file only what
carries an owner decision or a correctness finding, and put everything
else in an existing open issue, in the pull-request body, or in a comment.
At the limit, file nothing, and say in a comment what would have been
filed and why it was held.

Group findings by theme rather than by instance. One issue that names a
class of defect and enumerates its instances costs one item and reads
better than five issues; splitting a single finding into a parent issue and
a follow-up task issue spends two items on one owner decision.

This is not a tidiness preference. On 2026-08-06 the bot created twelve
items against an allowance of ten, and twelve later runs — nine
`tend-notifications` and three `tend-review` — then failed at the preflight
over the following fifteen hours, until the count reset at midnight UTC.
`tend-review` fires only on pull-request events and never retries, so the
review owed to [#339](https://github.com/jakobtfaber/Faber2026/pull/339)
when it opened that morning was never delivered, and it was still missing
a day later. Two of the twelve items were the `review-runs` workflow's own
tracking issue and pull request, so a housekeeping run can spend the
budget that a review of real work then cannot get.

## Pull request conventions

Title with the lowercase prefix that matches recent history —
`chore:`, `docs:`, `ci:`, `ms:` for manuscript prose, `fix:` — followed
by an imperative summary. Example: `ci: pin the actionlint action digest`.
Where no prefix fits, a plain imperative sentence matches precedent too.

Apply the `tend` label to every pull request and issue comment thread the
bot opens, so the owner can filter the bot's work from their own.

The body states what changed, why, and how it was verified. When a check
was not run, say which and why rather than implying full coverage.

## Merging

Never merge. `main` is admin-gated and the bot's write access is below
the bypass threshold by design. Open the pull request, let CI run, and
leave the merge to the owner.

## Journaling

Do not append to the activity journal
(`analysis/docs/rse/protocols/journal.jsonl`); it is the interactive
sessions' record, and bot writes there would interleave with theirs.
Record what you did in the pull-request body instead — that is the
durable record for bot work in this repository.

Do not run `scripts/deploy-board.sh` or otherwise deploy the readiness
board. That is an outward-facing publish step and belongs to the owner.

## Evidence and honesty

State evidence status plainly, using this repository's labels:
**VERIFIED**, **PRELIMINARY**, **UNKNOWN**, **BLOCKED**, **STALE**. A
passing build is not proof a change is correct — say what you actually
checked. Never present an unverified observation as settled, and never
report a check as passing that you did not run.
