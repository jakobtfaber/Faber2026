#!/usr/bin/env bash
# Publish docs/rse/board/readiness.html to the board/ path on GitHub Pages.
# Usage: scripts/deploy-board.sh
set -euo pipefail

ROOT=$(git rev-parse --show-toplevel)
BOARD="$ROOT/docs/rse/board/readiness.html"
REMOTE=origin
BRANCH=gh-pages
TMP=$(mktemp -d /tmp/faber2026-ghpages.XXXXXX)

cleanup() {
  git -C "$ROOT" worktree remove --force "$TMP" 2>/dev/null || rm -rf "$TMP"
}
trap cleanup EXIT

[[ -f "$BOARD" ]] || { echo "missing $BOARD" >&2; exit 1; }

# Refuse to publish a board built from a drifted/contradicted control state.
# --offline keeps deploy usable without a gh token; drop it for live checks.
if ! python3 "$ROOT/scripts/sync_state.py" --check --offline; then
  echo "deploy-board: sync_state --check failed; regenerate views before deploying" >&2
  exit 1
fi

git -C "$ROOT" fetch "$REMOTE" "$BRANCH"
git -C "$ROOT" worktree add --detach "$TMP" "$REMOTE/$BRANCH"

# The page is self-contained. Preserve every other gh-pages artifact and replace
# only the board entry point; .nojekyll keeps GitHub Pages from invoking Jekyll.
mkdir -p "$TMP/board"
cp "$BOARD" "$TMP/board/index.html"
touch "$TMP/.nojekyll"
git -C "$TMP" add board/index.html .nojekyll

if git -C "$TMP" diff --cached --quiet; then
  echo "board unchanged; nothing to deploy"
  exit 0
fi

git -C "$TMP" commit -q -m "board: $(date '+%Y-%m-%d %H:%M %Z')"
git -C "$TMP" push -q "$REMOTE" "HEAD:$BRANCH"
echo "deployed -> https://jakobtfaber.github.io/Faber2026/board/"
