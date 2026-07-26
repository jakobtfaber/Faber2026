# Decision Packet: `codex/nine-sightline-search-contract` Divergence

---
**Date:** 2026-07-25
**Phase:** Plan → Phase 1 of
`plan-scattered-work-integration-and-retirement.md` (landed in this repo)
**Status:** AWAITING OWNER DECISION
---

## Pinned evidence snapshot (2026-07-25, post-fetch)

| Ref | Hash |
|---|---|
| merge-base (`$BASE`) | `11b716cabb7183d2e30f2bfffad4ef720b87397a` |
| local `codex/nine-sightline-search-contract` (`$LOCAL`) | `6c0e9b3640061ba95df54cc457898fb24824a3e2` |
| `origin/codex/nine-sightline-search-contract` (`$REMOTE`) | `33a61ad894c6e41b7d3f91664fe3edf2a1f5fa8d` |
| `origin/main` at packet time | `7c1a595` (tip; moved during this session by docs PRs #94/#95) |

Local tip is also preserved at
`origin/codex/nine-sightline-cherrypick-resolution-20260725` (pushed
2026-07-25; nothing is at risk whatever is decided).

## Finding 1 — the "4 behind" is already merged work

Every remote-side commit is an ancestor of `origin/main`
(`git merge-base --is-ancestor` verified per commit): `78d04ed` (archive
superseded analysis material), `e5d624e` (wayfinder: revise nine-sightline
search contract), `33a61ad` (wayfinder: make search contract executable),
merge `ce6a516` (PR #5). PR #4 for this branch is **MERGED**. The remote
branch is a fully-landed, dead line; there is nothing to "catch up" to
except `main` itself.

## Finding 2 — the local side holds exactly 4 unique commits

`git range-diff $BASE..$REMOTE $BASE..$LOCAL`:

- `a8a5d83` = remote `e5d624e` (patch-equivalent; already on main — drops
  out on rebase).
- Unique: `27b51b3` (docs: resolve trust assessment registry),
  `97b3e89` (figures: support data-only morphology subsets),
  `d44ca73` (figures: require shared displayed time support),
  `6c0e9b3` (review: record owner morphology roster).

These are the resolved cherry-pick queue from the 2026-07-25 rescue.

## Finding 3 — conflict surface is total, and science-adjacent

All 10 files touched by the 4 unique commits have also changed on
`origin/main` since the merge-base. `git merge-tree --write-tree
origin/main 6c0e9b3` (no-touch simulation) reports **8 conflicted files**:

- content conflicts: `docs/rse/control/results-registry.toml`,
  `docs/rse/wayfinder/map-apj-submission.md`,
  `docs/rse/wayfinder/map-expanded-foreground-catalog-repair.md`,
  `docs/rse/wayfinder/tickets/13-overhaul-trust-assessment.md`,
  `docs/rse/wayfinder/tickets/expanded-foreground-catalog-repair-13-set-nine-sightline-search-contract.md`
- add/add (both sides recreated the file independently): `RESULTS.md`,
  `scripts/render_results_registry.py`, `tests/test_results_registry.py`

The add/add trio means main's archive-and-overhaul line and the local
cherry-pick line rebuilt the results-registry surface divergently.
Resolving them decides **which trust-assessment and results-registry
content is authoritative** — scientific adjudication, not mechanics.

## Options

**A (recommended): re-apply the 4 commits onto `origin/main` on a focused
branch, one commit at a time, owner adjudicating registry/trust
conflicts.** Start from `origin/main`, `git cherry-pick` each of
`27b51b3`, `97b3e89`, `d44ca73`, `6c0e9b3`; at each conflict the owner
(or an owner-approved rule per file) picks the surviving content; PR to
`main`. Preserves per-commit provenance; the dead remote branch is left
alone (no deletion under the plan).

**B: merge `origin/main` into the local branch and PR the branch.** One
big conflict resolution instead of four scoped ones; history keeps both
lines. Harder to review; same adjudication burden in one lump.

**C: park.** Leave `codex/nine-sightline-cherrypick-resolution-20260725`
on the remote as preservation and defer adjudication to the trust /
results-registry reconciliation family
(`worktree-reconciliation.md` proposed order item 1). Zero risk, but the
four commits stay un-integrated and the local clone stays divergent.

Note for A/B: the adjudication overlaps the reconciliation's "Trust"
family. If the owner prefers, choose **C now** and fold this packet into
that family's decision packet — that is the cleanest read of
"authority reconciliation governs".

## Verification contract (per plan Phase 1 step 4)

With `$BASE`, `$LOCAL` pinned above and `TIP` = surviving branch head:
`git range-diff $BASE..$LOCAL $BASE..$TIP` must show every accepted
commit as `=` or documented-modified; if squash-merged, `git diff $TIP
$LOCAL -- <accepted paths>` must be empty per accepted path.

## Owner decision

- **Decision:** **Option A** — cherry-pick the 4 commits onto a branch from
  `main`; owner adjudicates each conflict, staged one commit at a time;
  focused PR to `main`.
- **Date:** 2026-07-25
- **Recorded by:** session agent, owner instruction verbatim in chat; PR #96
  is the queue record.

## Execution outcome (2026-07-25)

Option A executed in a session-scratch worktree from `origin/main`
(`7c1a595`). **All four commits proved content-superseded by main; zero
commits were produced and no PR is needed.** Per-commit evidence:

- `27b51b3` (trust registry): owner-adjudicated skip. Incoming registry is
  `schema_version = 2` / "pass 3"; main carries `schema_version = 6` /
  "pass 7" of the same overhaul with the same pins (`9175b92`, `23fbd295`,
  `6c87890`) at full hashes; ticket 13 resolved with the richer 62-row
  authority text; renderer/test 88/93 and 33/35 line-subsumed.
- `97b3e89` (data-only morphology subsets): one docstring context conflict;
  after union resolution git reported the pick **empty** — main already
  contains `select_rows`, `grid_shape`, `--burst`, and a test file 22 lines
  newer than the incoming one. Skipped.
- `d44ca73` (shared displayed time support): pick empty with no conflicts.
  Skipped.
- `6c0e9b3` (owner morphology roster): pick empty;
  `figure_review/owner-morphology.yaml` and `tests/test_owner_morphology.py`
  byte-identical on main (`git diff --quiet` both). Skipped.

Verification contract satisfied in its squash form: for every touched path,
`git diff origin/main <commit> -- <path>` is empty or main is strictly
newer. The four commits remain preserved verbatim at
`origin/codex/nine-sightline-cherrypick-resolution-20260725` (`6c0e9b36…`).
The local clone's divergent branch `codex/nine-sightline-search-contract`
now qualifies as separate-stale (no unique delta); its retirement is a
Phase 5 Track A item, not executed here.
