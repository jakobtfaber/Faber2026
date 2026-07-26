# Closure roster — all open work lanes across the three repositories (2026-07-26)

**Objective/phase:** Phase 1 (inventory and classification) of the owner-chartered
closure campaign: "close all open WIP lanes across Faber2026, dsa110-FLITS, and
Faber2026-analysis so that we can begin new work and structure it more cleanly."
Read-only inventory; nothing was landed, retired, or modified in this phase.

**Snapshot:** remote state fetched 2026-07-26 (after the owner's merge of FLITS
PR #231 and the analysis-pin-bump work on parent PR #253). 153 remote branches
examined: 23 parent, 112 analysis, 18 FLITS. Every branch was joined against
its pull-request history; branches without a pull request were checked by
commit-content presence on main. Evidence trail: the six family receipts
(`receipt-family{1..6}-*.md`), `roster-branch-landing-2026-07-26.md`, and the
per-branch checks recorded in this session.

Dispositions used below:

- **KEEP** — infrastructure or archive that must exist for something else to work.
- **RETIRE** — safe to delete once the owner approves the list by name; content
  is on main (merged pull request), strictly behind main, or recorded as
  superseded/rejected in a closed pull request adjudicated by a family receipt.
- **CARRY** — unfinished work worth folding into the manuscript-finalization
  effort, restructured under a plain name.
- **DECIDE** — real unmerged content whose value is an owner call.

## Faber2026 (parent, 23 branches)

**KEEP (5)**

| Branch | Why |
|---|---|
| `gh-pages` | the deployed readiness board |
| `overleaf-2026-07-11-2125` | raw Overleaf sync branch — deleting breaks the Overleaf GitHub link (standing rule) |
| `entire/checkpoints/v1` | session-checkpoint archive; never merges, holds history |
| `rescue/science-gates-parent-20260722` | preservation estate from the July-22 rescue |
| `codex/analysis-pin-bump-20260726` | PR #253, landing now; branch auto-deletes at merge |

**Open pull request (1):** `codex/final-author-block` (PR #216) — owner merge
call once checks pass against the fixed pin.

**RETIRE (14)** — each with recorded proof:
`infra/owner-board` (PR #2 closed; board superseded by the in-repo deployed
board), `ms/fig1-dm-drift-closure-20260717` (fig1 model-TOA batch rejected
wholesale 2026-07-17), `docs/authority-roles-proof-20260720` (its authority
maps, tickets, and parity evidence are all on main; only a parent-side
CONTEXT.md draft never landed — the authority content lives in the analysis
CONTEXT.md), `research/foreground-redshift-verdicts` (its single audit document
is on main), `codex/expanded-foreground-phase-two-review` (family-3 receipt:
retired wayfinder tree + excluded pin move), `codex/expanded-foreground-map-closure`
(strictly behind main), `codex/figure3-source-replay-pins` (PR #199 closed as
superseded), `codex/nine-sightline-search-contract` and
`codex/nine-sightline-search-contract-successor-20260722` (PR #200 closed;
contract revision landed through the analysis-side lane, family-6),
`codex/chime-rfi-preservation-gates-successor-20260722` (PR #201 closed) and
`codex/prototype-chime-rfi-preservation-gates` (family-1: superseded, and the
owner's 2026-07-26 no-cleaner verdict moots the lane),
`codex/wayfinder-07-pin-host-redshift-evidence` (PR #193 closed; Verdi
redshift authority superseded it), `codex/host-dm-repair-v2` (PR #204 closed;
host-DM lane owner-rejected, family-2), `codex/pin-analysis-owner-queue-fix-20260724`
(PR #218 closed; superseded by PR #253), `docs/special-ref-maintenance-20260724`
(PR #245 merged).

**DECIDE (1):** `publish/repository-provenance-map-followup` — 3 unlanded
commits ("refresh reproducibility provenance", "align analysis replay with docs
pin", "link repository provenance map"). Parent-side companion of the analysis
DECIDE item below; land together or supersede together.

## Faber2026-analysis (112 branches)

**RETIRE (108)**

- 95 branches whose pull requests are MERGED (squash workflow leaves the branch
  behind after every landing — this is the bulk of the pile; includes all
  `docs/receipt-*` and this week's RFI branches).
- 13 branches whose pull requests were CLOSED with recorded supersession or
  rejection, adjudicated in the family receipts: PR #20, #22, #30, #31, #32,
  #33, #34, #35, #36, #40, #48, #56, #67.
- `codex/visual-science-review` (no PR; its one commit's figure-review workflow
  files are all on main via the v2 lane, PR #44 merged).
- `codex/nine-sightline-cherrypick-resolution-20260725` (its divergence decision
  was recorded and landed via PR #96; the five draft commits predate that
  resolution).

**CARRY (1):** `codex/auto-set-expanded-independent-validation` — ticket-05,
the Figure 3 independent audit. Owner direction 2026-07-26: this is an agent
task. Fold into manuscript finalization as a plainly-named lane ("independently
re-verify the Figure 3 foreground catalog before submission"); the branch holds
the gate implementation and `ADVERSARIAL_REVIEW_BLOCKERS.md` checklist an agent
must discharge. Keep the branch until that lane completes, then retire it.

**DECIDE (1):** `publish/repository-provenance-map` — 3 commits, tip `e753fa9c`
(the parent's pre-bump submodule pin — the parent pinned this branch, not main).
The repository-map commit landed via PR #106; the other two ("refresh
reproducibility provenance", "advance replay evidence for docs pin") are
unlanded. If the reproducibility-provenance refresh is wanted for the
manuscript, land it through a focused PR; otherwise record it superseded and
retire all three provenance-map branches together.

## dsa110-FLITS (18 branches)

**KEEP (9)**

| Branch | Why |
|---|---|
| `entire/checkpoints/v1`, `agent/dm-phase-v2`, `pin/faber2026`, `codex/provenance-dm-associations-9175b925` | pre-rewrite history lineages (the July-13 fork rewrite); sole remaining reachability for pre-rewrite objects |
| `archive/foreground-source-freeze-pr231` | created 2026-07-26: durable ref for provenance commit `c913175e567d`, which analysis tests replay (the #231 squash orphaned it and broke CI) |
| `rescue/science-gates-{codex,claude,pipeline}-20260722`, `rescue/pr174-parent-work-pipeline-20260726` | preservation estates; re-examine only after the captured-WIP reconciliation below |

**CARRY (1):** `rescue/wip-crossmatch-scint-20260726` — the captured dirty
working tree (crossmatching + scintillation edits from July 17). Reconciling it
is Phase 2 of this campaign, and its scintillation half belongs to the owner's
scint walkthrough.

**RETIRE (6):** `joint/tf-fit-window-resolution` (PR #193 merged),
`codex/figure3-deterministic-pdf` (PR #223 merged),
`codex/model-grid-exact-support-20260722` (PR #228 merged; strictly behind),
`codex/auto-freeze-candidate-redshifts` (its three files are on main) and
`codex/auto-freeze-candidate-redshifts-mainpin` (strictly behind),
`codex/b4-figure-review-20260720` (family-3: superseded by the deterministic
catalog rebuild on main).

**DECIDE (2):** `publish/repository-provenance-map` (1 commit "repair results
library paths" — part of the provenance-map trio decision), and
`codex/chromatica-cross-band-scintillation` (PR #200 closed, but it is scint
material — hold for the scint walkthrough rather than retiring now).

## Non-branch WIP lanes

1. **FLITS canonical clone**: working tree carries the 11 modified files
   captured in `rescue/wip-crossmatch-scint-20260726`; local `main` is ~155
   behind origin; 3 local stashes sit on pre-rewrite history. Phase 2 closes
   this: fast-forward main, reconcile or discard the working-tree copy against
   the capture, triage the stashes.
2. **Parent canonical clone**: modified `AGENTS.md`, `CLAUDE.md`, `README.md`,
   a `pipeline` gitlink drift, and untracked notes (`update-072326-1535.md`,
   `worktree-reconciliation.md`, `graphify-out/`, `figures/.receipts/`,
   `figures/prototypes/`, `.claude-science/`, `docs/rse/{ops,specs}/`). Local
   only; needs a tidy pass (commit-or-discard per file) in Phase 2.
3. **Wayfinder tickets**: the open frontier beyond ticket-05 is not classified
   here; plain-language restructuring of surviving tickets is Phase 2 work.
4. **Scint campaign** (window_campaign_2L ratification, pin bump, steep-α
   physicality, chromatica cross-band branch): deliberately excluded — owner
   walkthrough, Phase 4.

## Counts

| | KEEP | open PR | RETIRE | CARRY | DECIDE |
|---|---|---|---|---|---|
| Faber2026 | 5 | 1 | 14 | 0 | 1 |
| Faber2026-analysis | 0 | 0 | 108 | 1 | 1 |
| dsa110-FLITS | 9 | 0 | 6 | 1 | 2 |
| **total** | **14** | **1** | **128** | **2** | **4** |

## What Phase 3 (retirement) will and will not do

Will: delete exactly the 128 RETIRE branches above, after the owner approves
this roster by name; deletions run agent-side where the push gate allows,
batched for the owner's terminal otherwise; a deletion receipt records every
ref and its final commit hash.

Will not: touch KEEP/CARRY/DECIDE branches, any `overleaf-*`, `rescue/*`,
`archive/*`, `entire/*`, or pre-rewrite lineage, the Overleaf link, tags, or
any local working tree.
