#!/bin/bash
# UserPromptSubmit hook: remind the active agent when the journal cadence
# has lapsed (docs/rse/protocols/journal-protocol.md; default cadence 10 minutes).
# Codex streams hook stdin; drain it before early exit to avoid EPIPE.
[ ! -t 0 ] && cat >/dev/null
J="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}/docs/rse/protocols/journal.jsonl"
[ -f "$J" ] || exit 0
last=$(tail -1 "$J" | sed -E 's/.*"ts": ?"([^"]+)".*/\1/')
last_s=$(date -j -f "%Y-%m-%dT%H:%M:%S%z" "$last" +%s 2>/dev/null || echo 0)
[ "$last_s" -eq 0 ] && exit 0
age=$(( ($(date +%s) - last_s) / 60 ))
# JSON (not plain text): Codex's parser treats stdout starting with "[" as
# malformed JSON and drops it; the hookSpecificOutput shape parses in both
# Claude and Codex (openai/codex hooks/src/engine/output_parser.rs).
if [ "$age" -ge 10 ]; then
  printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"[journal] Last entry %sm ago — 10-min cadence lapsed. Append: scripts/journal-append.sh <agent> <lane> <state> \\"<note>\\", then rebake + redeploy the board (docs/rse/protocols/journal-protocol.md)."}}\n' "$age"
fi
exit 0
