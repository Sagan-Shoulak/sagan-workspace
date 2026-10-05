#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -ne 5 ]]; then
  echo "Usage: bash scripts/integrated-package-smoke.sh INDEX SAGAN_EXE PHYSICS_DIR RENDER_DIR GAME_DIR" >&2
  exit 2
fi

export SAGAN_PACKAGE_INDEX="$1"
export SAGAN_EXECUTABLE="$2"
physics_dir="$3"
render_dir="$4"
game_dir="$5"

[[ -f "$SAGAN_PACKAGE_INDEX" ]] || { echo "Missing combined package index" >&2; exit 1; }
[[ -f "$SAGAN_EXECUTABLE" ]] || { echo "Missing Sagan executable" >&2; exit 1; }
[[ -d "$physics_dir" && -d "$render_dir" && -d "$game_dir" ]] || {
  echo "Missing candidate checkout" >&2
  exit 1
}

export PATH="/c/msys64/ucrt64/bin:/ucrt64/bin:/usr/bin:/bin:$PATH"

echo "Checking game against the combined physics/render catalog..."
(cd "$game_dir" && "$SAGAN_EXECUTABLE" --run-package .)

echo "Checking headless physics against the combined catalog..."
(cd "$physics_dir" && bash tests/integration/orbit_numeric_test.sh &&
  bash tests/integration/lagrange_numeric_test.sh &&
  bash tests/integration/solar_lagrange_numeric_test.sh)

if [[ "${OS:-}" == "Windows_NT" ]]; then
  echo "Checking native Windows rendering against the combined catalog..."
  (cd "$render_dir" && bash tests/integration/window_bridge_test.sh &&
    bash tests/integration/shape_text_test.sh)
else
  echo "Native rendering check skipped: only the Windows backend is supported."
fi

echo "Integrated package smoke checks passed."
