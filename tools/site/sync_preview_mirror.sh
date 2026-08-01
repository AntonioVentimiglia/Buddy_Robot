#!/usr/bin/env bash
# Refresh the out-of-tree preview mirror that .claude/launch.json serves.
#
#   tools/site/sync_preview_mirror.sh
#
# Needed only on this Mac, and only because the repo sits under ~/Desktop, which
# macOS TCC hides from the preview-server process — it cannot read any file in
# the repo, so the preview serves a copy from ~/.buddy_preview instead. See the
# _comment block in .claude/launch.json for the durable fixes (grant Desktop
# access, or move the repo out of ~/Desktop).
#
# Run after `python3 tools/build.py`, or the served pages go stale.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
MIRROR="${BUDDY_PREVIEW_DIR:-$HOME/.buddy_preview}"

mkdir -p "$MIRROR"
cp "$REPO/tools/site/serve.py" "$MIRROR/serve.py"
rsync -a --delete "$REPO/site/" "$MIRROR/site/"
rsync -a --delete "$REPO/assets/figures/" "$MIRROR/figures/"
echo "mirror refreshed: $MIRROR  ($(find "$MIRROR/site" -type f | wc -l | tr -d ' ') site files)"
