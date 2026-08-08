# Receipt: Phase 5 Track A — Batch 1 (2026-07-26)

**Objective/phase:** Phase 5 Track A of
`plan-scattered-work-integration-and-retirement.md`. Five retirements —
the per-session cap.
**Owner approvals (verbatim, this session):** batch of five exact paths
approved ("Approved, all five"); gate item 1 (reconciliation authority
status) **waived by owner instruction** ("Let's proceed with Phase 5
track A now"); `worktree remove --force` for the three parent worktrees
separately approved ("Approved") after the halt-and-resurface below.

## Gate evidence (pre-approval, all read-only)

- Branches pushed & full-hash verified (Phase 3 receipt); zero open PRs on
  all four branches (`gh pr list --head`).
- Trees clean (pointer drifts receipted in the Phase 3 receipt; drifted
  commits `9a33f78c`, `304a177a`, `f3c8d22a` and deinit-cleared `c6111390`
  all confirmed present in the parent's `.git/modules` stores).
- No open files (`lsof +D` = 0 on every path); `lane-liveness` quiescent
  or uncertain-with-unresolved-owner only (no live signals).
- Overleaf clone: clean; all 5 branches + both stashes ancestor-covered by
  the terminal-home bundle (149 refs, sha256 `ae6fa3a0…e376`) except
  `entire/checkpoints/v1` (`39784fe1`, one metadata commit) — gap closed
  before approval with `entire-checkpoints-v1-supplement.bundle`
  (sha256 `eb0208ee…b076`, verified).

## Actions

| # | Path | Action | Result |
|---|---|---|---|
| 1 | `…/Faber2026-worktrees/analysis/set-expanded-independent-validation` | unlock → `worktree remove` | removed, deregistered |
| 2 | `…/Faber2026-worktrees/parent/Faber2026-foreground-redshift-verdicts` | deinit → unlock → `worktree remove --force` | removed |
| 3 | `…/Faber2026-worktrees/parent/Faber2026-rfi-route-validation` | deinit → unlock → `worktree remove --force` | removed |
| 4 | `…/Faber2026-worktrees/parent/.codex-expanded-foreground-map-closure-20260722` | deinit → unlock → `worktree remove --force` | removed |
| 5 | `~/Developer/overleaf/Faber2026` (1.7 GB) | move → `~/Documents/_trash/Faber2026-overleaf-clone/` + `PROVENANCE.md` | staged; deletion needs separate instruction |

HEAD re-verified against the expected full hash immediately before each
removal (freshness check at the door).

## The `--force` carve-out (halt-and-resurface record)

git 2.55 `worktree remove` refuses **any** worktree whose index carries a
submodule gitlink, even fully deinited (pipeline dir empty, no `.git`,
clean tree — all verified). The plan's "never `--force`" rationale
("refusal means a gate item was wrong") is inapplicable to this
structural refusal in submodule-carrying parents. Execution halted,
the forced variant was re-surfaced with this evidence, and the owner
approved it explicitly. Precedent for future Track A batches on parent
worktrees: deinit → verify clean/preserved → `remove --force` under
named approval remains the required pattern.

## Post-state (verified)

- Parent `Faber2026`: exactly one registered worktree (canonical root,
  `8d492fea`). Analysis submodule: root only. `…/Faber2026-worktrees/`
  drive dirs `parent/` and `analysis/` are empty.
- `~/Developer/overleaf/` no longer contains `Faber2026`.
- Nothing deleted outright: worktree removals destroyed only
  gate-verified-redundant checkouts; the Overleaf clone is intact in
  `_trash/` staging.

## Remaining Track A queue (untouched, next batches)

Local `Faber2026-worktrees/special-refs-20260724` (786 MB), stale
`codex/nine-sightline-search-contract` local branch, 25+ analysis ticket
worktrees under scratch — each still needs its own gate run and named
approval; the authority-status waiver above covered only this batch.
