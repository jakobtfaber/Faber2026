#!/bin/bash
# Cursor postToolUse hook: same 10-min cadence trigger as
# journal-cadence-posttool-hook.sh, but emitting Cursor's output shape
# ({"additional_context": ...}) instead of Claude's hookSpecificOutput.
# (docs/rse/journal-protocol.md)
# Codex streams hook stdin; drain it before early exit to avoid EPIPE.
[ ! -t 0 ] && cat >/dev/null
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
J="$ROOT/docs/rse/journal.jsonl"
[ -f "$J" ] || exit 0
NAG="$ROOT/.git/journal-last-nag"
last=$(tail -1 "$J" | sed -E 's/.*"ts": ?"([^"]+)".*/\1/')
last_s=$(date -j -f "%Y-%m-%dT%H:%M:%S%z" "$last" +%s 2>/dev/null || echo 0)
[ "$last_s" -eq 0 ] && exit 0
now_s=$(date +%s)
age=$(( (now_s - last_s) / 60 ))
[ "$age" -lt 10 ] && exit 0
if [ -f "$NAG" ]; then
  nag_s=$(cat "$NAG" 2>/dev/null || echo 0)
  [ $(( now_s - nag_s )) -lt 180 ] && exit 0
fi
echo "$now_s" > "$NAG"
printf '{"additional_context":"[journal] %sm since last entry — append NOW, mid-turn: scripts/journal-append.sh <agent> <lane> working \\"<what you are working on right now>\\" (10-min cadence, docs/rse/journal-protocol.md)."}\n' "$age"
exit 0
