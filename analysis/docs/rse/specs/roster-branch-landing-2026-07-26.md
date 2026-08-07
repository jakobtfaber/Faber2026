# Roster: development-branch landing onto origin/main (2026-07-26)

**Objective/phase:** discovery packet for landing development-branch work
onto `origin/main` across Faber2026, Faber2026-analysis, and dsa110-FLITS
(reconciliation Phase 4; excludes Overleaf history bundles and receipt
estates per the owner's instruction).

**Method:** all three remotes fetched with `--prune`; every non-main,
non-gh-pages, non-`overleaf-*` branch (65 total) triaged by (1) ahead
count vs `origin/main`, (2) associated pull-request state via `gh`,
(3) a stable patch-id absorption screen — each ahead-commit's patch-id
compared against every `origin/main` commit since the merge base. Squash
merges and rebases can defeat patch-id matching, so "unabsorbed" is an
upper bound on unlanded work, and "absorbed" is proof of landing.

## Class 1 — Provably absorbed (no landing needed)

`docs/authority-roles-proof-20260720`,
`research/foreground-redshift-verdicts` (parent);
`codex/visual-science-review` (analysis);
`codex/auto-freeze-candidate-redshifts`,
`rescue/pr174-parent-work-pipeline-20260726` (FLITS); all merged-PR
branches (~40, including every `docs/receipt-*` branch).

## Class 2 — Never-merge (preservation, pins, checkpoints)

- `entire/checkpoints/v1` (all repos) — checkpoint lineages.
- FLITS `pin/faber2026`, `agent/dm-phase-v2`,
  `codex/provenance-dm-associations-9175b925` — pre-rewrite or pin
  lineages (633–671 "ahead" = different history, not pending work).
- `rescue/science-gates-*` (parent + 3 FLITS), and standalone submodule
  pin commits ("chore: pin …") inside otherwise-live branches — the
  deliberate-pin rule keeps pointer moves separately scoped.
- `docs/special-ref-maintenance-20260724` — preservation record push.

## Class 3 — Open pull requests (live lanes, land via PR flow)

| PR | Repo | Branch | Subject |
|---|---|---|---|
| #216 | Faber2026 | `codex/final-author-block` | final collaboration author block (owner-facing) |
| #74 | Faber2026-analysis | `codex/rfi-validation-contract-20260723` | remaining CHIME RFI acceptance contract |
| #231 | dsa110-FLITS | `codex/foreground-six-row-identities` | freeze six missing source identities |

## Class 4 — Unabsorbed work needing owner adjudication, by family

Closed-unmerged PRs and PR-less branches with surviving unique commits.
A closed PR often means rejected or superseded — each family needs its
closure reasons read before landing anything.

1. **CHIME RFI preservation/validation:** parent
   `codex/prototype-chime-rfi-preservation-gates` (12),
   `codex/chime-rfi-preservation-gates-successor-20260722` (6); analysis
   `codex/auto-review-rfi-preservation-limits` (1); plus open PR #74.
2. **Host-DM repair/trust:** parent `codex/host-dm-repair-v2` (8);
   analysis `codex/host-dm-repair-v2` (17),
   `codex/host-dm-trust-ratification` (1 — note a commit records the
   owner *rejecting* the trust promotion; likely do-not-land).
3. **Expanded foreground / Figure 3:** parent
   `codex/expanded-foreground-phase-two-review` (4),
   `codex/figure3-source-replay-pins` (1); analysis
   `codex/auto-set-expanded-independent-validation` (4),
   `codex/figure3-source-replay-final` (1),
   `codex/auto-resolve-expanded-crossmatch-contract` (1),
   `codex/close-expanded-foreground-tickets-02-03` (1); FLITS
   `codex/b4-figure-review-20260720` (3); plus open PR #231.
4. **Trust registry / convergence:** analysis
   `codex/resolve-trust-assessment` (7),
   `codex/auto-review-trust-ledger` (1),
   `codex/convergence-wave-20260722` (14, includes owner-checkpoint and
   controller-manifest changes).
5. **Scintillation:** FLITS `codex/chromatica-cross-band-scintillation`
   (4) — likely superseded by the two-component `window_campaign_2L`
   products (PR #192 lane); verify supersession rather than land.
6. **Queue/board/provenance infrastructure:** parent `infra/owner-board`
   (2), `publish/repository-provenance-map-followup` (2),
   `ms/fig1-dm-drift-closure-20260717` (1),
   `codex/pin-analysis-owner-queue-fix-20260724` (1); analysis
   `publish/repository-provenance-map` (3),
   `codex/phase0-queue-accounting` (2),
   `codex/fix-owner-queue-resolved-redshift` (1),
   `codex/auto-review-count-audit` (2),
   `codex/wayfinder-18-law-host-redshifts` (1 — check against the
   Verdi-draft redshift authority before landing); FLITS
   `publish/repository-provenance-map` (1).

Nine-sightline branches are excluded: their content supersession is
already proven in `decision-nine-sightline-divergence-2026-07.md`; the
surviving "unabsorbed" commits are submodule pin moves only.

## Protocol for landing (per family)

1. Read the family's PR closure reasons and any owner decisions on
   record; classify each branch land / supersede / reject.
2. For "land": rebase or cherry-pick the surviving commits onto a fresh
   branch from `origin/main`, resolve conflicts with owner adjudication
   where scientific, open a focused PR, verify, merge.
3. For "supersede"/"reject": record the verdict in a receipt; the branch
   becomes retirement-eligible under the Tier-2 gate (separate step).
4. One family at a time; a verified checkpoint between families;
   submodule pin bumps remain separately scoped.
