#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
for candidate in python3 python py; do
  if command -v "$candidate" >/dev/null 2>&1; then
    exec "$candidate" scripts/workspace.py update "$@"
  fi
done
echo "Python 3.11 or newer is required for workspace.toml." >&2
exit 1
