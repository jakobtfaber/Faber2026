#!/bin/bash
# UserPromptSubmit hook: remind the active agent when the journal cadence
# has lapsed (docs/rse/journal-protocol.md; default cadence 10 minutes).
J="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}/docs/rse/journal.jsonl"
[ -f "$J" ] || exit 0
last=$(tail -1 "$J" | sed -E 's/.*"ts": ?"([^"]+)".*/\1/')
last_s=$(date -j -f "%Y-%m-%dT%H:%M:%S%z" "$last" +%s 2>/dev/null || echo 0)
[ "$last_s" -eq 0 ] && exit 0
age=$(( ($(date +%s) - last_s) / 60 ))
if [ "$age" -ge 10 ]; then
  echo "[journal] Last entry ${age}m ago — 10-min cadence lapsed. Append: scripts/journal-append.sh <agent> <lane> <state> \"<note>\", then rebake + redeploy the board (docs/rse/journal-protocol.md)."
fi
exit 0
