#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/../.."
action=build
if [ "$#" -gt 0 ]; then action="$1"; shift; fi
case "$action" in
  version)
    # region canvas-version
    node --version
    node tsc.mjs --version
    # endregion
    ;;
  build)
    # region canvas-build
    node examples/canvas-ts/build.mjs
    # endregion
    ;;
  lv1)
    # region canvas-lv1
    node examples/canvas-ts/run.mjs 1
    # endregion
    ;;
  lv2)
    # region canvas-lv2
    node examples/canvas-ts/run.mjs 2
    # endregion
    ;;
  lv3)
    # region canvas-lv3
    node examples/canvas-ts/run.mjs 3
    # endregion
    ;;
  lv4)
    # region canvas-lv4
    node examples/canvas-ts/run.mjs 4
    # endregion
    ;;
  lv5)
    # region canvas-lv5
    node examples/canvas-ts/run.mjs 5
    # endregion
    ;;
  lv6)
    # region canvas-lv6
    node examples/canvas-ts/run.mjs 6
    # endregion
    ;;
  lv7)
    # region canvas-lv7
    node examples/canvas-ts/run.mjs 7
    # endregion
    ;;
  deploy)
    # region canvas-deploy
    node examples/canvas-ts/tools.mjs deploy
    # endregion
    ;;
  profile)
    # region canvas-profile
    node examples/canvas-ts/tools.mjs profile
    # endregion
    ;;
  serve)
    # region canvas-serve
    exec node examples/canvas-ts/tools.mjs serve "$@"
    # endregion
    ;;
  *) echo '알 수 없는 Canvas 실행 항목입니다' >&2; exit 2 ;;
esac
