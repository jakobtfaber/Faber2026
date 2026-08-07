# Receipt: Phase 3 — Side-Checkout Integration (2026-07-25)

**Objective/phase:** Phase 3 of
`plan-scattered-work-integration-and-retirement.md` — put every
backup-drive side-checkout's unique committed work on an origin branch.
**Preconditions honored:** drive mounted throughout; no unlock, prune,
remove, or pointer realignment performed; no submodule pointer committed.

## Actions and verification

All four target branches confirmed absent on their remotes before pushing
(`ls-remote` clash check, empty). Post-push `ls-remote --exit-code`
full-hash verification:

| Source (under `/Volumes/ArtifexBackupDrive/Faber2026-worktrees/`) | Remote (repo → branch) | Pushed tip (verified) |
|---|---|---|
| `parent/Faber2026-foreground-redshift-verdicts` (locked, clean) | Faber2026 → `research/foreground-redshift-verdicts` | `6e6a986b78bc46d9d3dbb23415dac5252543cdef` |
| `parent/Faber2026-rfi-route-validation` (detached `94052932`) | Faber2026 → `research/rfi-route-validation` (branch created at that commit; no switch, checkout stays detached) | `94052932dce402551cb124a465e3f1ff6c779ad2` |
| `parent/.codex-expanded-foreground-map-closure-20260722` | Faber2026 → `codex/expanded-foreground-map-closure` | `9ea975de30549ff996bc93ab6692c67a7eb74fb0` |
| `analysis/set-expanded-independent-validation` | Faber2026-analysis → `codex/auto-set-expanded-independent-validation` | `8415f1eea3b92aa384b3b37ffff04cffc810ed45` |

## Dirty-state disposition

- `Faber2026-rfi-route-validation`: 1 dirty entry = `analysis` submodule
  pointer move, **uncommitted by rule**. Receipted:
  `91ea72a42f7b4f95aa8cdc51aa7be5d71b8c2b67` →
  `9a33f78cec5f41f9d556f1509b8e6d0964c7c3b3`.
- `.codex-expanded-foreground-map-closure-20260722`: 2 dirty entries =
  submodule pointer moves, uncommitted. Receipted: `analysis`
  `8337c2327313f9318ef3b481c1b4f0115e567551` →
  `304a177a931003d41b03fb0925b9d993c77d6373`; `pipeline`
  `b69dea16636fc9944c0083040c09b5a57d66db34` →
  `f3c8d22a9088914e0179cfecf1ee4086777dc927`.
- `set-expanded-independent-validation`: 2 untracked review-evidence docs
  (`ADVERSARIAL_REVIEW_BLOCKERS.md`,
  `logs/independent-release-gate-adversarial-review.md` — adversarial
  findings on the release-gate validator, including a pass-transition
  bypass) committed on the checkout's own branch as
  "review: preserve independent release-gate adversarial findings"
  (`8415f1ee…` tip includes it).
- `Faber2026-foreground-redshift-verdicts`: clean; nothing to disposition.

Pointer realignment (working trees back to pinned gitlinks) is **not
done** — it is named in the Phase 5 Track A owner approval per checkout,
per the plan.

## Outstanding

No PRs opened for these branches (landing into `main` is reconciliation
work, out of this plan). Locks untouched (live registration shows the
drive worktrees locked; Codex's live count during the Phase 3 gate was
four locked worktrees, superseding the handoff's "three locked
parent-side" — re-verify at Phase 5).
