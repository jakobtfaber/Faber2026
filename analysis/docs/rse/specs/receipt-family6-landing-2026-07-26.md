# Receipt: family 6 pilot — queue/board/provenance branch landing (2026-07-26)

**Objective/phase:** pilot family of the branch-landing roster
(`roster-branch-landing-2026-07-26.md`), owner-chartered ("Proceed with
family 6 as the pilot"). Verdicts below follow the roster protocol: read
closure reasons, classify land / superseded / reject, land survivors via
focused PR.

## Landed

- **`docs/rse/ops/repository-map.md` + README link** (analysis repo) —
  the one surviving artifact of the family. Cherry-picked commit
  `17aca27` from `publish/repository-provenance-map` onto a fresh branch
  from main; map file byte-identical to source; PR #106 squash-merged;
  presence on `origin/main` confirmed. Its Overleaf description was
  checked against the current browser-sync route and is accurate.

## Superseded / absorbed (verified, not landed)

| Branch | Evidence |
|---|---|
| parent `infra/owner-board` | PR #2 closed "Superseded by merged board redesign PR #3"; unique artifact already deployed to gh-pages |
| parent `codex/pin-analysis-owner-queue-fix-20260724` | PR #218 closed fail-closed (seven governance failures; pin unsafe); sole commit is a gitlink move — pin rule |
| parent `publish/repository-provenance-map-followup` | README "Start here" section and boundary-note removal already on main verbatim; remaining commits are gitlink moves — pin rule |
| parent `ms/fig1-dm-drift-closure-20260717` | companion PR #121 merged; the branch's extra candidate ACF PDFs are pre-refit renders superseded by the model-TOA closeout (FLITS #194/#197, parent #106), which rejected the fig1 batch wholesale — regeneration at pin parity is the fig1 lane's open work, not a landing |
| analysis `codex/phase0-queue-accounting` | PR #67 closed "stale queue bookkeeping … replaying would regress current state" |
| analysis `codex/fix-owner-queue-resolved-redshift` | PR #22 closed as duplicate of merged #21 |
| analysis `codex/auto-review-count-audit` | PR #30 closed "Superseded by merged PR #29" |
| analysis `codex/wayfinder-18-law-host-redshifts` | PR #40 closed "Superseded by #41"; #41 is MERGED |
| analysis `publish/repository-provenance-map` commits `e753fa9`, `0bdec1a` | dated REPRODUCE/repro-manifest and OWNER_QUEUE/replay churn; replaying would regress queue state (same class as #67) |
| FLITS `publish/repository-provenance-map` | its 2-line `DATA_LOCATIONS.md` fix is on main verbatim (lines 137–138) |

## Family status

Family 6 is closed: one artifact landed, all other content proven
superseded or absorbed. No branch was deleted (retirement is a separate
Tier-2-gated step). Next families per roster remain unpiloted; the three
open PRs (#216 parent, #74 analysis, #231 FLITS) are untouched live
lanes.
