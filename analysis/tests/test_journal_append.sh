#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$TMP/scripts" "$TMP/docs/rse"
cp "$ROOT/scripts/journal-append.sh" "$TMP/scripts/journal-append.sh"
: > "$TMP/docs/rse/journal.jsonl"

if "$TMP/scripts/journal-append.sh" "test-agent" "repo" "finish" "bad state" >/tmp/journal-invalid.out 2>/tmp/journal-invalid.err; then
  echo "expected invalid state to fail" >&2
  exit 1
fi

if [[ -s "$TMP/docs/rse/journal.jsonl" ]]; then
  echo "invalid state should not append to journal" >&2
  exit 1
fi

"$TMP/scripts/journal-append.sh" "test-agent" "repo" "done" "valid state" >/tmp/journal-valid.out

python3 - "$TMP/docs/rse/journal.jsonl" <<'PY'
import json
import sys

entries = [json.loads(line) for line in open(sys.argv[1])]
assert len(entries) == 1, entries
entry = entries[0]
assert entry["agent"] == "test-agent", entry
assert entry["lane"] == "repo", entry
assert entry["state"] == "done", entry
assert entry["note"] == "valid state", entry
PY
