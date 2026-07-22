# Wayfinder automation controller

The controller runs only tasks declared in
`docs/rse/control/wayfinder-automation.toml`. The manifest is reviewed Git
state; runtime state and logs are outside the repository at
`~/.local/state/Faber2026-analysis/wayfinder-controller/`. The pre-split
`~/.local/state/Faber2026/wayfinder-controller/` tree is legacy history. The
controller neither migrates nor deletes it.

The manifest exactly covers the expanded-foreground ticket family. Open
tickets are `[[task]]` entries; resolved tickets remain as `[[history]]` so
dependency chains stay explicit. `execution = "afk"` marks runnable agent work.
`execution = "hitl"` marks human-in-the-loop work: visible to the owner, never
spawned by the controller. `mode` separately states the endpoint (`resolve` or
`review`).

## Commands

```bash
python3 scripts/wayfinder_controller.py plan --wave first
python3 scripts/wayfinder_controller.py launch --wave first
python3 scripts/wayfinder_controller.py status
python3 scripts/wayfinder_controller.py status --json
```

`launch` refuses to run until the controller, schema, and manifest match
`origin/main`. Manifest loading also rejects missing or extra scoped tickets,
ticket-blocker drift, AFK/HITL drift, cross-repository tasks, and state identity
drift. Launch and worktree setup verify the repository root, `origin`, and
shared Git directory. Cross-repository work must be decomposed into one task per
repository.

Launch starts a detached supervisor. Each AFK task gets an isolated
worktree below `~/Developer/scratch/worktrees/Faber2026-analysis-wayfinder-auto/`, a
`codex/auto-*` branch, bounded `codex exec`, closed stdin, and a schema-checked
receipt. HITL entries remain queued for the owner and cannot be run directly or
by the supervisor.

After repairing an external or evidence blocker:

```bash
python3 scripts/wayfinder_controller.py retry --task <task-id>
python3 scripts/wayfinder_controller.py launch --wave <wave>
```

Retry refuses running and resolved tasks. Logs and receipts are retained under
the state directory. Do not edit `state.json` manually.

## Completion semantics

- `resolved`: controller verified a merged PR and `Status: resolved` in the
  ticket on `origin/main`.
- `review_ready`: a complete owner-review artifact exists; no protected
  scientific action was taken.
- `blocked`: a named evidence, owner, or external-state gate stopped the task.
- `needs_attention`: the agent receipt and remote state disagree.
- `failed`: execution or validation failed.

The controller never waives owner visual review, independent validation, or the
exceptions in the standing delegation.
