#!/bin/bash
# Wall-clock journal watchdog (launchd com.jakobfaber.faber2026-journal-
# watchdog, every 5 min): the cadence backstop for harnesses that run no
# hooks (Cursor, Antigravity, unattributed writers). If repo files changed
# in the last 10 min while the journal is >=10 min stale, append an
# unattributed-activity entry so the board shows honest gaps. The entry
# resets staleness, so the watchdog self-throttles to one entry per lapse.
# (analysis/docs/rse/protocols/journal-protocol.md)
# Resolve both roots from this script's own location rather than hard-coding
# one checkout: launchd invokes it by absolute path, so $0 is always usable.
ANALYSIS="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$ANALYSIS/.." && pwd)"
J="$ANALYSIS/docs/rse/protocols/journal.jsonl"
[ -f "$J" ] || exit 0
last=$(tail -1 "$J" | sed -E 's/.*"ts": ?"([^"]+)".*/\1/')
last_s=$(date -j -f "%Y-%m-%dT%H:%M:%S%z" "$last" +%s 2>/dev/null || echo 0)
[ "$last_s" -eq 0 ] && exit 0
age=$(( ($(date +%s) - last_s) / 60 ))
[ "$age" -lt 10 ] && exit 0
recent=$(find "$REPO" -type f -mmin -10 \
  -not -path "$REPO/.git/*" \
  -not -path "$ANALYSIS/docs/rse/control/board/*" \
  -not -name "journal.jsonl" -not -name "*.swp" -not -name ".DS_Store" \
  2>/dev/null | head -6)
[ -z "$recent" ] && exit 0
n=$(printf '%s\n' "$recent" | wc -l | tr -d ' ')
top=$(printf '%s\n' "$recent" | head -3 | sed "s|$REPO/||" | paste -sd ", " -)
"$ANALYSIS/scripts/journal-append.sh" "watchdog/launchd" "repo" "info" \
  "unattributed activity: ${n}+ file(s) touched in last 10m ($top) while journal stale ${age}m - active agent must self-report (analysis/docs/rse/protocols/journal-protocol.md)"
