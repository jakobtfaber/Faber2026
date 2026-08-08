# Plan: hybrid control system — canonical state files, generated views, CI drift gate

---
**Date:** 2026-07-15
**Author:** Claude (Fable 5), synthesizing the 2026-07-14/15 multi-agent review
(diagnosis → verification → draft → Devin critique → owner direction)
**Status:** Draft — awaiting owner approval before implementation
**Related documents:**
- [Plan: loop orchestration](plan-loop-orchestration.md) — the architecture this implements mechanically
- [Journal protocol](../journal-protocol.md) — the activity log this composes with (unchanged)
- [Decision: P1 scope fork](decision-2026-07-15-p1-scope-fork.md) — first entry the evidence ledger must carry
---

## Problem

Status is duplicated across manually maintained surfaces (`ACTIVE_LANES.md`,
`board/owner-view.json`, `board/readiness.html`, plans, handoffs), and they
drift under concurrent work. Evidence from the last 24 hours alone:
`owner-view.json` still requested reviews of FLITS #170/#171 and Faber2026 #17
a day after all three merged; the C1 lane row went stale within hours of the
DOCUMENTED-FAIL verdict; the fixes landed only because a session hand-audited
GitHub. Adding another manually maintained file would reproduce the disease.

## Design principles

1. **Split state by who can know it.**
   - *Fetched live, never stored:* PR state, issue state, branch existence, CI
     status, submodule pin vs FLITS main. The generator queries `gh` at render
     time. A snapshot of any of these is stale by construction.
   - *Stored canonically, because GitHub cannot know it:* scientific trust
     status, gates and prerequisites, stop rules, next actions, owner-input
     flags, claim→artifact→manuscript mappings.
2. **No canonical file without a generated consumer and a CI check from day
   one.** A store nothing reads is another drift surface.
3. **Derived views are never hand-edited after the flag day.** CI fails when a
   regenerated view differs from the committed one.
4. **The journal protocol is unchanged.** The journal stays the append-only
   activity log; this system owns the *status* surfaces the journal panel sits
   next to.

## Data layers

Both files are TOML, read with stdlib `tomllib` (Python ≥3.11) — resolves the
dependency gap in the earlier draft (repo scripts are stdlib-only; PyYAML is
not declared anywhere).

### `docs/rse/program-state.toml` — operational state

```toml
[meta]
updated = "2026-07-15"          # bumped by any edit; shown on the board
wip_limit = 3

[[lane]]
id = "p1-window-upchan"          # canonical task ID (journal `lane` values)
title = "P1 windowed re-upchannelization"
strand = "scintillation"         # association | budget_census | scattering |
                                 # scintillation | energies | synthesis | mechanics
status = "in_progress"           # proposed | in_progress | blocked | needs_owner |
                                 # documented_fail | done
owner = "codex"
issue = 0                        # GitHub issue number (0 = not yet filed)
branch = "codex/p1-window-upchan-plan"
worktree = "~/Developer/scratch/worktrees/Faber2026-p1-window-plan"
pr = 0
gates = ["off-pulse mechanism test", "single-target qualification"]
next_action = "land v1.2 revival-plan revision"
needs_owner = false
```

### `docs/rse/evidence-ledger.toml` — scientific evidence

```toml
[[sightline]]
burst = "freya"

[[sightline.evidence]]
strand = "scintillation_chime"
status = "documented_fail"       # trusted | diagnostic | upper_limit |
                                 # unavailable | blocked | documented_fail
artifact = "pipeline/scintillation/experiments/c1-allpairs-crossgp/RESULT.md"
commit = "80094de"
scope = "retained _cntr_bpc product; estimator class closed by stop rule"
claims = ["retained CHIME product is information-limited for dnu_d at m<=0.17"]
consumers = ["sec:scint_chime", "tab:scint_results"]   # main.tex labels
```

Twelve sightlines × eight strands (association, dm_obs, dm_budget,
foreground_census, scintillation_dsa, scintillation_chime, scattering,
energies), bootstrapped from `CONTEXT.md`'s trust boundaries — not from the
stale boards.

## Generator: `scripts/sync_state.py` (stdlib only)

- **Inputs:** both TOML files; live GitHub via `gh` subprocess (`--offline`
  skips live queries and validates structure only, for environments without a
  token).
- **Outputs (each with a `GENERATED — do not hand-edit` banner):**
  1. `docs/rse/ACTIVE_LANES.md` — lane table from `program-state.toml`, with
     live PR/issue/branch columns fetched at render time.
  2. `docs/rse/board/owner-view.json` — Needs-you / Now / Next and strand
     component cards derived from lanes + ledger rollups; then the existing
     `scripts/render_journal_panel.py` bakes `readiness.html` unchanged.
  3. `docs/rse/board/claims-audit.md` — the ledger's consumer: every claim
     with its status, artifact, commit, and manuscript consumers, plus a
     cross-check against `main.tex` labels. A manuscript label consuming
     evidence whose status is not `trusted`/`upper_limit`/`documented_fail`
     is an error.
- **`--check` mode (CI):** regenerate to a temp dir and diff against the
  committed views (drift gate); flag stored↔live contradictions (a lane whose
  PR is merged but whose status is non-terminal); police the operating rules
  (lane without an issue once `issue` adoption lands, WIP above `wip_limit`,
  worktree paths that no longer exist).
- **Determinism:** sorted keys, stable ordering, byte-identical output for
  identical inputs; golden-file tests under `tests/`.

## Makefile / CI wiring

- `make check-state` → `python3 scripts/sync_state.py --check --offline` in
  CI (live mode is advisory, run locally); appended to the `test-science`
  target so the existing workflows enforce it with no new workflow files.
- `scripts/deploy-board.sh` gains a pre-step: refuse to deploy when
  `--check` fails, so a stale board can never publish.

## Migration (single flag-day PR)

1. Bootstrap both TOML files: lanes from live GitHub + the current worktree
   inventory; evidence from `CONTEXT.md` trust boundaries + the C1/P1 decision
   records. The stale `ACTIVE_LANES.md`/`owner-view.json` are hints only.
2. Land in one PR: state files + generator + tests + regenerated views +
   Makefile wiring + a journal-protocol note that the owner-view is now
   generated (its "update that JSON in the same pass" instruction becomes
   "update `program-state.toml` and rerun the generator").
3. After merge, any hand-edit to a generated view fails CI.

## Workspace preconditions (before implementation starts)

- Exactly **one** implementation worktree. Two clean, empty Antigravity
  worktrees exist for this effort (`centralize-operational-state-logic`,
  `implement-hybrid-control-system`, both at `3e59e9a`, now behind main);
  delete one, rebase the survivor. Owner/Antigravity to prune since the
  worktrees are Antigravity-managed.
- The P1 lane's in-flight v1.2 revision (separate codex worktree) may also
  touch `ACTIVE_LANES.md`; land it (or at least its board edits) before the
  flag day, or rebase the flag-day PR over it. Never edit that worktree.
- GitHub issue adoption is part of bootstrap: file one issue per active lane
  so the `issue` field is real from day one (repo currently has zero issues).

## Timebox

One working day. If it slips: ship `program-state.toml` + generator +
`--check` + the two operational views, and defer the ledger *with its
claims-audit consumer* to an immediate follow-up — never the ledger alone.

## Verification

1. `python3 scripts/sync_state.py` — generates all three views; visual review.
2. `python3 scripts/sync_state.py --check` — passes on a clean tree; fails
   when a view is hand-edited or a stored status contradicts live GitHub.
3. Golden-file tests + `make test-science` green.
4. Board deploys and renders; owner-view panel matches `program-state.toml`.

## Open questions (owner)

1. TOML/stdlib (this plan) vs YAML + a declared PyYAML dependency — TOML
   assumed unless overridden.
2. Implementer: Antigravity (holds the worktrees) vs Devin (requested this
   spec before implementing) vs Claude. One implementer, one worktree.
3. Should bootstrap file GitHub issues for currently active lanes immediately,
   or defer issue adoption to a second pass?
