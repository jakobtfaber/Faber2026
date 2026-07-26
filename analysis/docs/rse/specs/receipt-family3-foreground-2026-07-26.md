# Receipt: family 3 — expanded foreground / Figure 3 (2026-07-26)

**Objective/phase:** fifth family of the branch-landing roster,
owner-chartered ("proceed with families 3 and 4 automatically").

## Superseded (verified, not landed)

| Branch | Evidence |
|---|---|
| parent `codex/figure3-source-replay-pins` (PR #199) | closed "Superseded by the final Figure 3 review and source-replay gate work … checks were already failing" |
| analysis `codex/figure3-source-replay-final` (PR #20) | closed: staged PDF proven non-byte-deterministic; FLITS PR #223 (MERGED, verified) repaired the generator; "this candidate must not receive owner approval" |
| analysis `codex/auto-resolve-expanded-crossmatch-contract` (PR #32) | closed "Superseded by #37 … and #39" — both verified MERGED |
| analysis `codex/close-expanded-foreground-tickets-02-03` (PR #36) | same supersession, both targets MERGED |
| parent `codex/expanded-foreground-phase-two-review` (4 commits, no PR) | its ticket edits target the parent-side wayfinder tree, which is retired (authority: `analysis/docs/rse/wayfinder/`); the authoritative analysis-side tickets 02/03 are "Status: resolved" on analysis main; its pin move is excluded by the pin rule; its staged catalog docs predate the merged validation chain |
| FLITS `codex/b4-figure-review-20260720` (3 commits, no PR) | its hand-exported cross-references CSV and config catalog registrations are superseded by main's deterministic `build_expanded_catalog.py` rebuild (commit `f1bc2230` + PR #221), whose CSV carries richer per-match provenance (status, separations, timestamps, hashes); the B4 `figures.review.json` on main is owned by the merged consolidation lane (PR #174) |

## Blocked — open frontier, deliberately not landed

analysis `codex/auto-set-expanded-independent-validation` (release-gate
implementation + `ADVERSARIAL_REVIEW_BLOCKERS.md`). Its own adversarial
review (2026-07-24) forbids opening or merging the release-gate PR until
seven checks pass (52/52 replay with zero discrepancies, independently
computed SHA-256 pins, independent recomputation, byte-compares, empty
blocker list, commit binding). Wayfinder ticket
`…repair-05-set-independent-validation-gate` is still "Status: open" on
analysis main. Landing under standing authorization is prohibited while
review findings are unresolved; the branch is the recorded frontier for
ticket 05.

## Open PR #231 (FLITS) — verified, awaiting owner (draft)

"foreground: freeze six missing source identities." Independent
verification performed this session: simulated merge via
`merge-tree` is conflict-free; the 10 touched provenance tests pass on
the simulated merge result in an ephemeral worktree (removed after use);
head `c913175e` unchanged. The PR is a **draft** — the author's
not-ready marker — so marking it ready and merging is an owner decision,
not covered by standing authorization.

## Separate lane preserved (dsa110-FLITS canonical clone)

The clone's working tree carries an uncommitted separate-active lane:
11 modified files (~1,400 inserted lines) across `crossmatching/`
(association + TOA crossmatch code and reports),
`flits/batch/codetection_data.py`, `scintillation/scint_analysis/`, and
paired tests, plus three older stashes. Not authored by this task;
inventoried read-only and left untouched. Local `main` sits at
`fed4a02c` (152 behind origin) — not advanced, to avoid disturbing the
lane. Family-3 verification used `merge-tree` and an ephemeral worktree
instead of this tree.

## Family status

Family 3 closed. Owner items now queue-visible: (1) mark-ready + merge
decision on draft PR #231; (2) ticket 05 release-gate frontier (blocked
on the adversarial checklist). No branches deleted.
