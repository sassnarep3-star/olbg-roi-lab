#!/usr/bin/env bash
# One-shot helper to create the GitHub remote and push the repo.
# Requires the GitHub CLI (https://cli.github.com) or a manual remote URL.
set -euo pipefail

REPO_NAME="olbg-roi-lab"

if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  echo "==> Creating GitHub repo via gh CLI"
  gh repo create "$REPO_NAME" --public --source . --push
  echo "==> Done: https://github.com/$(gh api user -q .login)/$REPO_NAME"
else
  echo "gh CLI not authenticated. Either:"
  echo "  1)  gh auth login   &&  gh repo create $REPO_NAME --public --source . --push"
  echo "  2) or push manually:"
  echo "     git remote add origin https://github.com/<YOUR_USERNAME>/$REPO_NAME.git"
  echo "     git push -u origin main"
fi
