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

## The knowledge base finds nothing in CI

`CLAUDE.md` asks every agent to run
`python3 analysis/scripts/kb search "<topic>"` before exploratory
grepping. The index that command reads lives at `analysis/.kb/kb.sqlite3`
(`analysis/scripts/kb/config.py`), and `analysis/.gitignore` excludes
`/.kb/`, so the directory is never present in a runner's checkout. With no
index the command still exits 0 and prints `no results` for every query.
That is a silent false negative, not evidence of absence.

Verified on `main` at `1ef291a4`: `kb search "dispersion measure"` and
`kb search "catalog" --source code` both print `no results` in a checkout
that contains `analysis/figures/catalog.yaml`.

Read `no results` as "no index built here", never as "no such thing
exists", and search with `grep` instead.

## Scope discipline

Commit with explicit pathspecs, never `git add -A` or `git add .`. This
repository frequently carries unrelated dirty state; a broad stage sweeps
it into the commit.

One pull request does one thing. Do not bundle an adjacent cleanup,
a lint fix in an untouched file, or a documentation edit into a change
that is about something else.

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
