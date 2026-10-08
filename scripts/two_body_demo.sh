#!/usr/bin/env bash
set -euo pipefail

export PATH="/c/msys64/ucrt64/bin:/ucrt64/bin:/usr/bin:/bin:$PATH"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

mkdir -p build/two-body-demo build/tmp

sagan_executable="${SAGAN_EXECUTABLE:-$repo_root/checkouts/sagan/bin/sagan}"
render_root="${SAGAN_RENDER_ROOT:-$repo_root/checkouts/sagan-render}"
: "${SAGAN_PACKAGE_INDEX:?Set SAGAN_PACKAGE_INDEX to the reviewed combined workspace catalog}"
[[ -x "$sagan_executable" ]] || { echo "Missing Sagan executable: $sagan_executable" >&2; exit 1; }
[[ -f "$render_root/libraries/render/native/window_bridge.hpp" &&
   -f "$render_root/libraries/render/native/window_bridge.cpp" ]] || {
  echo "Missing sagan-render native bridge under $render_root" >&2
  exit 1
}

action="${1:-build-and-run}"
native_output="build/two-body-demo/two-body-demo.exe"

build_demo() {
  "$sagan_executable" --emit-cpp-package examples/two_body_demo \
    build/two-body-demo/program.cpp
  native_tmp="$repo_root/build/tmp"
  if command -v cygpath >/dev/null 2>&1; then
    native_tmp="$(cygpath -w "$native_tmp")"
  fi
  TMPDIR="$native_tmp" TMP="$native_tmp" TEMP="$native_tmp" \
    g++ -std=c++23 -Wall -Wextra -Wpedantic -Werror -Wno-error=switch \
    -include "$render_root/libraries/render/native/window_bridge.hpp" \
    build/two-body-demo/program.cpp "$render_root/libraries/render/native/window_bridge.cpp" \
    "$("$sagan_executable" --application-icon windows)" \
    -o "$native_output" -static -static-libgcc -static-libstdc++ -lgdi32 -luser32
  echo "Built $native_output"
}

run_demo() {
  if [[ ! -x "$native_output" ]]; then
    echo "Missing $native_output; build it first." >&2
    exit 1
  fi
  "$native_output"
}

case "$action" in
  build) build_demo ;;
  run) run_demo ;;
  build-and-run) build_demo; run_demo ;;
  *) echo "Usage: $0 [build|run|build-and-run]" >&2; exit 2 ;;
esac
