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
   scripts/deploy-board.sh   # pushes to gh-pages; board/ subdir only
   ```

   Canonical board URL (owner directive 2026-07-12, replaces the claude.ai
   artifact): **<https://jakobtfaber.github.io/Faber2026/board/>**. The
   gh-pages ROOT hosts the CHIME scattering deck — a separate lane; the
   deploy script never touches it. Do not redeploy the board as a
   claude.ai artifact anymore.

   **Owner view (added 2026-07-12; generated since 2026-07-15).** The board's
   top panel is baked from `docs/rse/board/owner-view.json` — the owner-facing
   summary (Needs you / In flight / Up next, ≤3 items each, plus 7 component
   cards). **That JSON is now GENERATED, not hand-edited.** Its canonical
   source is the `[owner_view]` block of `docs/rse/program-state.toml` (the
   hybrid control system, `docs/rse/specs/plan-hybrid-control-system.md`). If
   your turn changed what is in flight, opened or resolved an owner decision,
   or moved a component's status, edit `program-state.toml` and regenerate:

   ```bash
   python3 scripts/sync_state.py           # rewrites owner-view.json + ACTIVE_LANES.md + claims-audit.md
   python3 scripts/render_journal_panel.py # then bakes both board panels
   ```

   Hand-editing `owner-view.json` (or `ACTIVE_LANES.md` / `claims-audit.md`)
   now fails `make check-state` (`scripts/sync_state.py --check --offline`),
   which `make test-science` and `scripts/deploy-board.sh` both enforce. Bump
   `[owner_view].updated` in `program-state.toml` on every owner-view edit.

   **Strand structure (added 2026-07-13).** The owner-facing board groups
   work by science strand (association · budget/census · scattering ·
   scintillation · energies · synthesis · mechanics), each on an
   inputs→method→measured→validated→written lifecycle; owner-view.json
   components are strand-keyed, and a lane-state change must also update
   the matching strand swimlane stage in `readiness.html` (the V…G
   recovery map and lane detail live in its agent fold). Journal `lane`
   values stay the canonical task IDs — strands are presentation only. Plain English only — no lane
   IDs without a gloss. Items are `{"h": headline, "d": detail}`: `h`
   ≤6 words (this is all the owner reads); anything longer goes in `d`
   or gets cut. Component `next` ≤5 words, empty when blocked. A stale
   owner view is worse than none: the `updated` field is displayed, so
   bump it every edit.

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
6. **Non-Claude harnesses** (parity landed 2026-07-06 ~21:30; Cursor
   mechanical layer + honesty pass 2026-07-06 ~21:45). Be clear about
   what each layer guarantees — an instruction file has no clock, so
   only hooks and the watchdog are *mechanical*; `AGENTS.md` is
   *advisory only* and enforces nothing:
   - **Codex** (mechanical, VERIFIED 2026-07-06): both hooks mirrored in
     `.codex/hooks.json` (PostToolUse cadence + UserPromptSubmit
     staleness; scripts resolve the repo root via
     `git rev-parse --show-toplevel`). Verified end-to-end by live
     headless `codex exec` canary tests: gpt-5.5 quoted both injected
     reminders verbatim (Codex's hooks engine is Claude-compatible —
     `ClaudeHooksEngine` in openai/codex). Two operational constraints
     learned from source + testing:
     1. **Trust gate.** Codex runs a project hook only if
        `~/.codex/config.toml` has a matching
        `[hooks.state."<hooks.json path>:<event>:<group>:<index>"]`
        `trusted_hash` entry (machine-local, normally written by
        interactive approval). Both journal hooks are trusted+enabled
        on jakob-mbp. If a hook **command string** in
        `.codex/hooks.json` changes, the hash changes and the hook
        silently stops running until re-trusted — editing the target
        *script's contents* does not affect the hash.
     2. **Output must be JSON-safe.** Codex drops UserPromptSubmit
        stdout that starts with `[` or `{` but isn't valid wire JSON
        (marks the hook Failed). The staleness hook therefore emits
        the `hookSpecificOutput` JSON shape, which both Claude and
        Codex parse.
   - **Cursor** (mechanical): `.cursor/hooks.json` registers
     `scripts/journal-cadence-cursor-hook.sh` (postToolUse — same
     10-min trigger, Cursor's `additional_context` output shape) and
     `scripts/journal-cursor-afteredit-hook.sh` (afterFileEdit —
     self-journaling fallback: if a Cursor session edits a file while
     the journal is ≥10 min stale, the hook itself appends an
     attributed `[auto]` entry; no model cooperation needed).
   - **Antigravity / Gemini / anything else**: no hook surface —
     watchdog detection is the ceiling. Root `AGENTS.md` states the
     protocol for them, but it is a courtesy sign, not a trigger.
   - **Wall-clock backstop, all harnesses**: launchd agent
     `com.jakobfaber.faber2026-journal-watchdog` (plist source:
     `scripts/launchd/`, installed to `~/Library/LaunchAgents/`) runs
     `scripts/journal-watchdog.sh` every 5 min; when repo files changed
     in the last 10 min while the journal is ≥10 min stale, it appends an
     `unattributed activity` entry naming the touched files — the board
     then shows the honest gap even if the writer never self-reports.
     Detection only: it cannot make a session self-report intent.
     Log: `~/logs/faber2026-journal-watchdog.log`.
## Backfill convention

Entries reconstructed after the fact carry a `[backfill]` prefix in
`note` and the best-known timestamp (e.g. the commit time). Unattributable
work is journaled as `agent: "unattributed-writer"` — never guessed.
