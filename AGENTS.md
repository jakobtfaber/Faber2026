# AGENTS.md — Faber2026

Instructions for ALL agents working in this repo (Codex, Cursor,
Antigravity/Gemini, and any other harness). Claude Code reads CLAUDE.md;
the rules below bind everyone.

## Journal protocol (mandatory)

Full protocol: `docs/rse/journal-protocol.md`. Summary:

- While actively working here, append a journal entry **every ≤10 minutes**
  and at every substantive step boundary (start, finish, block, decision,
  commit):

  ```bash
  scripts/journal-append.sh "<agent>" "<lane>" "<state>" "<note>"
  # agent: harness/model + session tag, e.g. codex-gpt-5.5/exec-2026-07-06
  # lane:  board task ID (V·P0…P6, A1–A4, B#, C#, D#, E#, F#, G#) or repo/ms/board
  # state: working | done | blocked | info
  ```

- The journal (`docs/rse/journal.jsonl`) is append-only; corrections are
  new entries. It rides along in every doc/code commit.
- Codex sessions get hook reminders via `.codex/hooks.json`; a launchd
  watchdog (`scripts/journal-watchdog.sh`) logs unattributed activity for
  anything else. Do not rely on the watchdog — self-report.
- git authorship does not identify agents here; the journal `agent` field
  is the only attribution. Unattributed work gets flagged on the shared
  readiness board.

## Repo ground rules (mirror of CLAUDE.md non-negotiables)

- `pipeline/` is a pinned submodule (detached HEAD intentional) — never
  check out a branch inside it or bump the pin casually.
- Never hand-edit `figures/` or root `*_table.tex` (pipeline exports).
- A tex change is done only when `make` exits 0 with no new warnings.
- Trust reset in force (CONTEXT.md): no fit-, census-, budget-,
  association-, or DM-derived number is citable until its §V ladder passes
  (docs/rse/specs/plan-trust-reset-revalidation.md).
- Read `CONTEXT.md` before editing any prose — its "Avoid" lines are hard
  constraints.
