# Receipt: Entire rollout closeout for the Faber2026 repositories (2026-09-22)

Objective: close the three open `entire-rollout` tasks in the owner's task
store that concern Faber2026 and its two retired companion repositories.
Scientific phase: none (tooling only). Operational phase: retirement of
Entire checkpoint capture in retired repositories, and a privacy repair in
the live repository.

## Source snapshots (verified 2026-09-22)

| Repository | Path | Branch | Tree | GitHub state |
| --- | --- | --- | --- | --- |
| Faber2026 | `~/Developer/repos/github.com/jakobtfaber/Faber2026` | `method-reassessment-2026-09-11` | untracked `.hydradb-plugin-data/` only | public, active |
| Faber2026-analysis | `~/Developer/repos/github.com/jakobtfaber/Faber2026-analysis` | `main` | clean | public, archived (last push 2026-08-24) |
| dsa110-FLITS | `~/Developer/repos/github.com/jakobtfaber/dsa110-FLITS` | `main` | clean | public, archived (last push 2026-08-24) |

Faber2026-analysis was folded into this repository as `analysis/` and
archived; dsa110-FLITS is retired provenance. Both lanes are quiescent, so
the "once its lane ends" condition on the two disable tasks is met.

## Changes made

1. Faber2026-analysis: `entire disable` wrote `enabled: false` to
   `.entire/settings.local.json` (gitignored). `entire status` reports
   Disabled.
2. dsa110-FLITS: same command, same result.
3. Faber2026: `entire configure --skip-push-sessions --project` set
   `strategy_options.push_sessions: false` in `.entire/settings.json`
   (gitignored via `/.entire/`). Entire stays enabled for local
   checkpoints, but its pre-push step returns before pushing any
   `refs/entire/*` or `entire/checkpoints/v1` data. The task's alternative,
   a private checkpoint repository, was not chosen: there is no private
   destination for this project, and nothing needs the checkpoints
   off-machine.

No git hooks were touched. `entire disable` and `entire configure` without
`--force` only rewrite settings files. The repository hook
`.git/hooks/pre-push` (md5 `52476f4c…`) and the global
`~/.git-hooks-global/pre-push` symlink are byte-identical before and after.
The `entire enable --force` / `entire doctor --force` refresh that
`entire status` suggests was deliberately not run: it reinstalls git hooks
and has previously clobbered the global hook dispatcher.

## Verification

- `entire status` in each repository, after the change (Disabled,
  Disabled, Enabled with push gated).
- Settings files read back as shown above.
- Hook checksums compared before and after.
- Entire source consulted: `cmd/entire/cli/setup.go` (disable and
  configure paths) and `strategy/manual_commit_push.go` (early return when
  `push_sessions` is false).

Not verified: a live `git push` from Faber2026 confirming no checkpoint
refs travel. The gate is read directly from the source; the next ordinary
branch push will show it.

## Remaining items, not done here

Checkpoint refs already on the public remotes before this change:

| Remote | Refs |
| --- | --- |
| Faber2026 `origin` | four `refs/entire/checkpoints/*` (2026-09-11 to 09-13) and `refs/heads/entire/checkpoints/v1` |
| dsa110-FLITS `origin` | `refs/heads/entire/checkpoints/v1` |
| Faber2026-analysis `origin` | none |

Deleting remote refs is a one-way door and needs the owner's named
approval. It has been queued in the task store as a separate item rather
than performed. A third checkpoint (`GF/01M2EX…`) differs between local
and remote, so the local copy would be the one to keep if the remote refs
are removed.

## Task store disposition

Completed with annotation pointing to this receipt:

- `21288bca-771f-5581-b16a-fcc8d8d260c6` (Faber2026-analysis disable)
- `d2789e02-5397-553e-b43f-27c7cd6347de` (dsa110-FLITS disable)
- `f3af14e5-c189-5701-a50d-26291e120c1b` (Faber2026 checkpoint privacy)

Queued: remove already-pushed Entire checkpoint refs from the public
Faber2026 and dsa110-FLITS remotes (owner approval required).
