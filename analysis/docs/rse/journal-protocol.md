# Agent journal protocol

---
**Date:** 2026-07-06
**Status:** Active (owner directive: honesty/visibility across concurrent agents)
**Cadence:** every ≤10 minutes of active work (owner may retune)
---

## Why

On 2026-07-06 two writers committed to main interleaved for over an hour
with no mutual visibility, and git authorship (`Jakob Faber`) cannot
distinguish agents from the owner. The journal is the shared activity log;
the readiness board renders it.

## The store

`docs/rse/journal.jsonl` — append-only, tracked, one JSON object per line:

```json
{"ts": "2026-07-06T21:02:24-0700", "agent": "claude-fable-5/session-9f491a6c",
 "lane": "A1", "state": "working", "note": "what is being done, plainly"}
```

- `agent` — model/harness + a stable session tag. Codex: `codex-gpt-5.5/<context>`.
  Owner edits: `owner`.
- `lane` — board ID (`V·P0` … `V·P6`, `A1`–`A4`, `B#`, `C#`, `D#`, `E#`,
  `F#`, `G#`) or `board`, `repo`, `ms` for meta-work.
- `state` — `working` | `done` | `blocked` | `info`.
- Never rewrite or delete lines; corrections are new entries.

## Cadence & mechanics

1. **Every ≤10 min while actively working**, and at every substantive step
   boundary (task start, finish, block, decision, commit), append:

   ```bash
   scripts/journal-append.sh "<agent>" "<lane>" "<state>" "<note>"
   ```

2. **Rebake + redeploy the board** at natural boundaries (turn end, task
   done — batching entries is fine; the JSONL is the record, the panel is
   the view):

   ```bash
   python3 scripts/render_journal_panel.py
   # then redeploy docs/rse/board/readiness.html to the existing artifact
   # URL (Claude: Artifact tool with url=https://claude.ai/code/artifact/fdc8d749-f3a6-4296-bbd2-9f1052fe57f6)
   ```

3. **Commit policy:** the journal rides along with any doc/code commit
   (pathspec-include `docs/rse/journal.jsonl`); it is never the sole
   reason to push.

4. **Delegations:** any subagent or Codex `exec` dispatched to work in
   this repo gets this protocol stated in its prompt (agent tag +
   cadence). The dispatcher journals the dispatch and the landing.

5. **Enforcement — two hooks in `.claude/settings.json`** (verified live
   pickup: settings changes take effect without a session restart):
   - `scripts/journal-staleness-hook.sh` (UserPromptSubmit): reminder on
     each user prompt when the last entry is >10 min old.
   - `scripts/journal-cadence-posttool-hook.sh` (PostToolUse, all tools):
     the every-10-minutes trigger for **active** sessions — fires after
     every tool call, and once the journal is ≥10 min stale it injects a
     mid-turn instruction to append an entry covering what is being
     worked on right now. Throttled to one reminder per 3 min (state:
     `.git/journal-last-nag`, untracked). An active session therefore
     journals every ~10 min even during long autonomous turns; an idle
     session triggers nothing (nothing is being worked on).
6. **Non-Claude harnesses** (parity landed 2026-07-06 ~21:30):
   - **Codex**: both hooks mirrored in `.codex/hooks.json`
     (PostToolUse cadence + UserPromptSubmit staleness; scripts resolve
     the repo root via `git rev-parse --show-toplevel`, no
     Claude-specific env needed).
   - **Cursor / Antigravity / anything reading AGENTS.md**: instruction
     layer in root `AGENTS.md` (no mechanical hook surface — behavioral).
   - **Wall-clock backstop, all harnesses**: launchd agent
     `com.jakobfaber.faber2026-journal-watchdog` (plist source:
     `scripts/launchd/`, installed to `~/Library/LaunchAgents/`) runs
     `scripts/journal-watchdog.sh` every 5 min; when repo files changed
     in the last 10 min while the journal is ≥10 min stale, it appends an
     `unattributed activity` entry naming the touched files — the board
     then shows the honest gap even if the writer never self-reports.
     Log: `~/logs/faber2026-journal-watchdog.log`.
   (A CLAUDE.md pointer to this protocol is still pending: the file was
   held open in the owner's editor when the protocol landed, 2026-07-06
   ~21:00.)

## Backfill convention

Entries reconstructed after the fact carry a `[backfill]` prefix in
`note` and the best-known timestamp (e.g. the commit time). Unattributable
work is journaled as `agent: "unattributed-writer"` — never guessed.
