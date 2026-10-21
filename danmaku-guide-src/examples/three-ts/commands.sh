#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/../.."
action=build
if [ "$#" -gt 0 ]; then action="$1"; shift; fi
case "$action" in
  build)
    # region three-build
    node examples/three-ts/build.mjs
    # endregion
    ;;
  profile)
    # region three-profile
    if [ "$(node -p process.platform)" = android ]; then
      xvfb-run -a env LIBGL_ALWAYS_SOFTWARE=1 DANMAKU_WEBGL_DRIVER=mesa node examples/three-ts/profile.mjs
    else
      node examples/three-ts/profile.mjs
    fi
    # endregion
    ;;
  version)
    # region three-version
    node -p "require('./node_modules/three/package.json').version"
    node tsc.mjs --version
    # endregion
    ;;
  lv1)
    # region three-lv1
    node examples/three-ts/run.mjs 1
    # endregion
    ;;
  lv2)
    # region three-lv2
    node examples/three-ts/run.mjs 2
    # endregion
    ;;
  lv3)
    # region three-lv3
    node examples/three-ts/run.mjs 3
    # endregion
    ;;
  lv4)
    # region three-lv4
    node examples/three-ts/run.mjs 4
    # endregion
    ;;
  lv5)
    # region three-lv5
    node examples/three-ts/run.mjs 5
    # endregion
    ;;
  lv6)
    # region three-lv6
    node examples/three-ts/run.mjs 6
    # endregion
    ;;
  lv7)
    # region three-lv7
    node examples/three-ts/run.mjs 7
    # endregion
    ;;
  *) echo '알 수 없는 Three 실행 항목입니다' >&2; exit 2 ;;
esac
