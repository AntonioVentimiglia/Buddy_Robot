#!/usr/bin/env bash
set -euo pipefail
if [[ ! -f PROJECT_CONTEXT.md ]]; then
  echo "PROJECT_CONTEXT.md missing" >&2
  exit 1
fi
find . -type d   -not -path './.git*'   -not -path './build*'   -not -path './install*'   -not -path './log*'   -print | while read -r d; do
    if ! ls "$d"/*.md >/dev/null 2>&1; then
      echo "Directory lacks markdown context: $d" >&2
    fi
  done
