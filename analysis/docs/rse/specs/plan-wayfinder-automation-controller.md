# Implementation Plan: Wayfinder automation controller

---
**Date:** 2026-07-20
**Author:** Codex
**Status:** Approved — In Progress
**Related Documents:**
- [Standing delegation](../wayfinder/standing-delegation-2026-07-20.md)
- [Issue-tracker rules](../../agents/issue-tracker.md)
- [Expanded-catalog repair plan](plan-expanded-foreground-catalog-repair.md)
---

## Overview

Add a standard-library controller that turns a reviewed task manifest into
isolated Codex executions. Each worker owns one branch/worktree and must return a
schema-checked receipt. The controller independently verifies merged outcomes
against GitHub and the ticket on `origin/main`; agent exit code alone is never
completion evidence.

**Goal:** Launch and durably supervise the first safe Wayfinder execution wave,
resumable from disk, while stopping at every recorded scientific or owner gate.

## Current State Analysis

- `docs/agents/issue-tracker.md:23-31` defines claim, blocking, frontier, and
  resolution semantics but has no executor.
- `docs/rse/wayfinder/standing-delegation-2026-07-20.md:15-44` grants bounded
  decision authority and names actions that still require owner review.
- `scripts/deploy-board.sh:6-20` demonstrates isolated temporary worktrees and
  fail-closed preflight.
- `docs/rse/specs/plan-expanded-foreground-catalog-repair.md:74-280` supplies
  executable acceptance gates for the catalog lane.

## Desired End State

- `scripts/wayfinder_controller.py` supports `plan`, `launch`, and `status`.
- `docs/rse/control/wayfinder-automation.toml` is the tracked task graph.
- Runtime state and logs live outside Git under
  `~/.local/state/Faber2026/wayfinder-controller/`.
- Every worker uses subscription-authenticated `codex exec`, closed stdin,
  bounded runtime, an isolated worktree, and a JSON receipt schema.
- `resolved` requires a merged PR plus `Status: resolved` on `origin/main`.

## What We're NOT Doing

- No data movement/deletion, service changes, manuscript submission, Figure 3
  promotion, trust promotion, redshift/budget re-adjudication, or coauthor edits.
- No automatic approval of owner visual or morphology decisions.
- No reliance on normal `codex exec` stdout as structured output.
- No edits in the shared dirty checkout.

## Implementation Approach

Use TOML for the reviewed graph, JSON for atomic runtime state, one detached
supervisor process, and one subprocess per task. The supervisor admits only
dependency-ready tasks up to `max_parallel`; each task process invokes:

```bash
timeout 14400 codex exec -m gpt-5.5 \
  -c 'model_reasoning_effort="medium"' -c 'approval_policy="never"' \
  --sandbox danger-full-access -C <worktree> \
  --output-schema <receipt-schema> -o <receipt.json> <prompt> </dev/null
```

## Implementation Phases

### Phase 1: Manifest and fail-closed core

- [x] Add failing tests in `tests/test_wayfinder_controller.py` for manifest
  validation, dependency planning, forbidden mode/branch values, atomic state,
  and receipt-policy enforcement.
- [x] Run `uv run --project pipeline pytest -q tests/test_wayfinder_controller.py`;
  expect import failure.
- [x] Add `docs/rse/control/wayfinder-automation.toml`,
  `scripts/wayfinder_receipt.schema.json`, and pure parsing/planning functions in
  `scripts/wayfinder_controller.py`.
- [x] Re-run the test; expect pass.

### Phase 2: Durable launch and independent outcome checks

- [x] Extend tests with mocked subprocesses for worktree creation, closed stdin,
  bounded Codex command construction, PID persistence, resume behavior, and the
  rule that an autonomous receipt is not resolved until GitHub and
  `origin/main` agree.
- [x] Implement `plan`, `launch`, `status`, `_supervise`, and `_run-task`.
- [x] Run targeted tests and `python3 scripts/wayfinder_controller.py plan --wave first`.

### Phase 3: Publish and launch first wave

- [ ] Run `make test-science`, `git diff --check`, and `agent-closeout-check`.
- [ ] Commit, push, open a focused PR, wait for all checks, and merge.
- [ ] Verify Codex subscription auth with a live closed-stdin canary.
- [ ] Launch `python3 scripts/wayfinder_controller.py launch --wave first`.
- [ ] Verify a live supervisor PID, task worktrees, state JSON, and logs.

## Success Criteria

### Automated Verification

- `uv run --project pipeline pytest -q tests/test_wayfinder_controller.py`
- `make test-science`
- `python3 scripts/wayfinder_controller.py plan --wave first`
- `python3 scripts/wayfinder_controller.py status --json`
- Merged outcomes require both merged GitHub PR state and resolved ticket state.

### Manual Verification

- Trust-ledger and count-audit tasks stop at review-ready artifacts.
- Any later Figure 3 visual review remains owner-only.

## Testing Strategy

Unit tests mock Git, GitHub, and Codex. The launch smoke test uses one harmless
live Codex handshake before the real wave. Scientific task tests remain owned by
their individual worker PRs.

## Risk Assessment

- Concurrent workers may conflict: each starts from live `origin/main` and must
  update/revalidate before merge.
- A worker may claim success incorrectly: the controller validates its receipt,
  PR state, and ticket state independently.
- A process may die: atomic state, external logs, and stable worktree paths make
  `launch` resumable without guessing.

## References

- `docs/agents/issue-tracker.md`
- `docs/rse/wayfinder/standing-delegation-2026-07-20.md`
- `docs/rse/specs/plan-expanded-foreground-catalog-repair.md`
- `scripts/deploy-board.sh`

## Review History

### Version 1.0 — 2026-07-20
- Approved architecture from the owner conversation; explicit manual gates kept.
