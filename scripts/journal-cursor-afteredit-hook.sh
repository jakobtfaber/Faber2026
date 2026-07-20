#!/bin/bash
# Cursor afterFileEdit hook: self-journaling fallback. If a Cursor session
# edits a file while the journal is >=10 min stale, the hook itself appends
# an attributed auto-entry — no model cooperation required. Appending
# resets staleness, so this self-throttles to one entry per lapse.
# (docs/rse/protocols/journal-protocol.md)
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
J="$ROOT/docs/rse/protocols/journal.jsonl"
[ -f "$J" ] || exit 0
last=$(tail -1 "$J" | sed -E 's/.*"ts": ?"([^"]+)".*/\1/')
last_s=$(date -j -f "%Y-%m-%dT%H:%M:%S%z" "$last" +%s 2>/dev/null || echo 0)
[ "$last_s" -eq 0 ] && exit 0
age=$(( ($(date +%s) - last_s) / 60 ))
[ "$age" -lt 10 ] && exit 0
IN=$(cat)
FILE=$(printf '%s' "$IN" | python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("file_path",""))
except Exception: print("")' 2>/dev/null)
CONV=$(printf '%s' "$IN" | python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("conversation_id","")[:8])
except Exception: print("")' 2>/dev/null)
REL="${FILE#"$ROOT"/}"
"$ROOT/scripts/journal-append.sh" "cursor/auto-hook${CONV:+-$CONV}" "repo" "info" \
  "[auto] Cursor session edited ${REL:-a file} while journal ${age}m stale — hook-generated entry, session did not self-report." >/dev/null 2>&1
exit 0
