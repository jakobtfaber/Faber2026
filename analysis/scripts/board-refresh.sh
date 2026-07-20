#!/usr/bin/env bash
# Rebake the readiness board (journal panel + any task-state sync).
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
python3 scripts/render_journal_panel.py
echo "Board: $ROOT/docs/rse/board/readiness.html"
echo "Open:  open docs/rse/board/readiness.html"
