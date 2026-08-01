#!/usr/bin/env bash
# Publish the open discovery index to GitHub Pages.
#
# PREREQUISITE (one-time, needs YOUR GitHub account — Hermes cannot do this):
#   install gh:   (already handled — uv/apt)
#   authenticate: gh auth login        # opens browser, uses your account
#   (or set a token: gh auth login --with-token < token.txt)
#
# This script is FREE and reversible. It:
#   1. builds gh-pages/ from seed data (python scripts/build_site.py)
#   2. creates repo <name> on your account (if missing)
#   3. pushes gh-pages/ to the gh-pages branch and enables Pages
#
# Nothing here bills. No paid calls.
set -euo pipefail

REPO_NAME="${1:-misfit-music-discovery}"
export PATH="$HOME/.local/bin:$PATH"

echo "==> building site"
python scripts/build_site.py

if ! gh auth status >/dev/null 2>&1; then
  echo "ERROR: gh not authenticated. Run: gh auth login" >&2
  exit 1
fi

echo "==> ensuring repo $REPO_NAME exists"
gh repo create "$REPO_NAME" --public --description "Misfit Music Project — open, non-tiered artist discovery index" 2>/dev/null || \
  echo "(repo may already exist — continuing)"

echo "==> publishing gh-pages branch"
git init -q gh-pages-tmp 2>/dev/null || true
TMP="gh-pages-tmp"
rm -rf "$TMP" && mkdir -p "$TMP" && cp -r gh-pages/. "$TMP/"
cd "$TMP"
git init -q
git add -A
git -c user.name="Hermes" -c user.email="hermes@local" \
  commit -q -m "publish open discovery index"
git branch -M gh-pages
git push "git@github.com:$(gh api user --jq .login)/$REPO_NAME.git" gh-pages --force
cd ..
rm -rf "$TMP"

echo "==> enabling GitHub Pages"
gh api -X POST "repos/$(gh api user --jq .login)/$REPO_NAME/pages" \
  -f source.branch=gh-pages -f source.path=/ 2>/dev/null || \
  echo "(Pages may need manual enable at: https://github.com/$(gh api user --jq .login)/$REPO_NAME/settings/pages)"

echo "DONE. Live at: https://$(gh api user --jq .login).github.io/$REPO_NAME/"
