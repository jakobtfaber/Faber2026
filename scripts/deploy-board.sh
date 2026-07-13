#!/usr/bin/env bash
# Publish docs/rse/board/readiness.html to GitHub Pages (gh-pages branch).
# Usage: scripts/deploy-board.sh
# Board URL: https://jakobtfaber.github.io/Faber2026/board/
# The gh-pages ROOT hosts the CHIME scattering deck (separate lane) — the
# board lives under board/ and this script touches nothing else.
# Rebake first: python3 scripts/render_journal_panel.py
set -euo pipefail

ROOT=$(git rev-parse --show-toplevel)
BOARD="$ROOT/docs/rse/board/readiness.html"
BRANCH=gh-pages
TMP=$(mktemp -d /tmp/faber2026-ghpages.XXXXXX)
trap 'git -C "$ROOT" worktree remove --force "$TMP" 2>/dev/null || rm -rf "$TMP"' EXIT

[ -f "$BOARD" ] || { echo "missing $BOARD" >&2; exit 1; }

git -C "$ROOT" fetch origin "$BRANCH" 2>/dev/null || true
if git -C "$ROOT" rev-parse --verify --quiet "origin/$BRANCH" >/dev/null; then
  git -C "$ROOT" worktree add --force -B "$BRANCH" "$TMP" "origin/$BRANCH"
else
  git -C "$ROOT" worktree add --detach "$TMP"
  git -C "$TMP" checkout --orphan "$BRANCH"
  git -C "$TMP" rm -rfq . 2>/dev/null || true
fi

# The page is fully self-contained (inline CSS, no runtime fetch), so the
# deploy is a single-file copy; .nojekyll skips the Jekyll build.
mkdir -p "$TMP/board"
cp "$BOARD" "$TMP/board/index.html"
touch "$TMP/.nojekyll"
git -C "$TMP" add board/index.html .nojekyll

if git -C "$TMP" diff --cached --quiet; then
  echo "board unchanged; nothing to deploy"
  exit 0
fi

git -C "$TMP" commit -q -m "board: $(date '+%Y-%m-%d %H:%M %Z')"
git -C "$TMP" push -q origin "$BRANCH"
echo "deployed -> https://jakobtfaber.github.io/Faber2026/board/ (Pages rebuild ~1 min)"
