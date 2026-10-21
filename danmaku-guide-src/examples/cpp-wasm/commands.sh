#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/../.."
action=build
if [ "$#" -gt 0 ]; then action="$1"; shift; fi
case "$action" in
  build)
    # region wasm-setup-build
    node examples/cpp-wasm/build.mjs
    # endregion
    ;;
  *)
    echo "사용법: bash examples/cpp-wasm/commands.sh [build]" >&2
    exit 2
    ;;
esac
