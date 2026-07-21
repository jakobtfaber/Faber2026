# Wayfinder automation controller

The controller runs only tasks declared in
`docs/rse/control/wayfinder-automation.toml`. The manifest is reviewed Git
state; runtime state and logs are outside the repository at
`~/.local/state/Faber2026/wayfinder-controller/`.

## Commands

```bash
python3 scripts/wayfinder_controller.py plan --wave first
python3 scripts/wayfinder_controller.py launch --wave first
python3 scripts/wayfinder_controller.py status
python3 scripts/wayfinder_controller.py status --json
```

`launch` refuses to run until the controller, schema, and manifest match
`origin/main`. It starts a detached supervisor. Each task gets an isolated
worktree below `~/Developer/scratch/worktrees/Faber2026-wayfinder-auto/`, a
`codex/auto-*` branch, bounded `codex exec`, closed stdin, and a schema-checked
receipt.

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
