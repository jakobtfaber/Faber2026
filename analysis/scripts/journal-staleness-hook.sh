#!/bin/bash
# UserPromptSubmit hook: remind the active agent when the journal cadence
# has lapsed (analysis/docs/rse/protocols/journal-protocol.md; default
# cadence 10 minutes).
# Codex streams hook stdin; drain it before early exit to avoid EPIPE.
[ ! -t 0 ] && cat >/dev/null
# The store lives under analysis/; resolve it from this script's own
# location so the hook does not depend on the harness's project directory.
ANALYSIS="$(cd "$(dirname "$0")/.." && pwd)"
J="$ANALYSIS/docs/rse/protocols/journal.jsonl"
[ -f "$J" ] || exit 0
last=$(tail -1 "$J" | sed -E 's/.*"ts": ?"([^"]+)".*/\1/')
last_s=$(date -j -f "%Y-%m-%dT%H:%M:%S%z" "$last" +%s 2>/dev/null || echo 0)
[ "$last_s" -eq 0 ] && exit 0
age=$(( ($(date +%s) - last_s) / 60 ))
# JSON (not plain text): Codex's parser treats stdout starting with "[" as
# malformed JSON and drops it; the hookSpecificOutput shape parses in both
# Claude and Codex (openai/codex hooks/src/engine/output_parser.rs).
if [ "$age" -ge 10 ]; then
  printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"[journal] Last entry %sm ago — 10-min cadence lapsed. Append: analysis/scripts/journal-append.sh <agent> <lane> <state> \\"<note>\\", then rebake + redeploy the board (analysis/docs/rse/protocols/journal-protocol.md)."}}\n' "$age"
fi
exit 0
