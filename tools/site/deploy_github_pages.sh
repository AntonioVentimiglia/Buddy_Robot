#!/usr/bin/env bash
# Publish site/ to a public GitHub Pages repo. One-time setup:
#   1. Create an EMPTY public repo on GitHub (e.g. buddy-portfolio)
#   2. ./tools/site/deploy_github_pages.sh git@github.com:AntonioVentimiglia/buddy-portfolio.git
# Re-run the same command to publish updates. Enable Pages: repo Settings ->
# Pages -> deploy from branch 'main', folder '/ (root)'.
set -euo pipefail
REMOTE="${1:?usage: deploy_github_pages.sh <git-remote-url>}"
cd "$(dirname "$0")/../../site"
touch .nojekyll
rm -rf .git && git init -q -b main && git add -A
git commit -q -m "Publish Buddy portfolio site $(date +%F)"
git push -f "$REMOTE" main
rm -rf .git
echo "Published to $REMOTE (Pages serves it within ~1 min once enabled)"
