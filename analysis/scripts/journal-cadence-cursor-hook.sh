#!/bin/bash
# Cursor postToolUse hook: same 10-min cadence trigger as
# journal-cadence-posttool-hook.sh, but emitting Cursor's output shape
# ({"additional_context": ...}) instead of Claude's hookSpecificOutput.
# (analysis/docs/rse/protocols/journal-protocol.md)
# Codex streams hook stdin; drain it before early exit to avoid EPIPE.
[ ! -t 0 ] && cat >/dev/null
# The store and the throttle stamp both belong to this script's own
# checkout; resolve them from $0 rather than from the harness's project
# directory, which may be a subdirectory or a different tree entirely.
# --absolute-git-dir is a real directory in a linked worktree too, where
# .git is a file and writing "$toplevel/.git/..." fails.
ANALYSIS="$(cd "$(dirname "$0")/.." && pwd)"
J="$ANALYSIS/docs/rse/protocols/journal.jsonl"
[ -f "$J" ] || exit 0
NAG="$(git -C "$ANALYSIS" rev-parse --absolute-git-dir 2>/dev/null || echo "${TMPDIR:-/tmp}")/journal-last-nag"
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
printf '{"additional_context":"[journal] %sm since last entry — append NOW, mid-turn: analysis/scripts/journal-append.sh <agent> <lane> working \\"<what you are working on right now>\\" (10-min cadence, analysis/docs/rse/protocols/journal-protocol.md)."}\n' "$age"
exit 0
