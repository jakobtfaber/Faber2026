#!/bin/bash
# Append an entry to the repo agent journal (docs/rse/protocols/journal-protocol.md).
# Usage: scripts/journal-append.sh <agent> <lane> <state> <note...>
#   state: working | done | blocked | info
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
J="$ROOT/docs/rse/protocols/journal.jsonl"
agent="$1"; lane="$2"; state="$3"; shift 3; note="$*"
case "$state" in
  working|done|blocked|info) ;;
  *)
    echo "journal-append: invalid state '$state' (expected: working, done, blocked, info)" >&2
    exit 2
    ;;
esac
ts="$(date +%Y-%m-%dT%H:%M:%S%z)"
python3 - "$J" "$ts" "$agent" "$lane" "$state" "$note" <<'EOF'
import json, sys
path, ts, agent, lane, state, note = sys.argv[1:7]
with open(path, "a") as fh:
    fh.write(json.dumps({"ts": ts, "agent": agent, "lane": lane,
                         "state": state, "note": note}) + "\n")
EOF
echo "journaled: [$lane/$state] $note"
