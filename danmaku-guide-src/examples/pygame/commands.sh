#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/../.."
action="${1:-setup}"
if [ "$#" -gt 0 ]; then shift; fi
# region python-choice
python=python3
if [ -x .cache/pygame-venv/bin/python ]; then
  python=.cache/pygame-venv/bin/python
fi
# endregion
case "$action" in
  install)
    # region pygame-install
    python3 -m venv .cache/pygame-venv
    .cache/pygame-venv/bin/python -m pip install --disable-pip-version-check -r examples/pygame/requirements.txt
    # endregion
    ;;
  setup)
    # region pygame-setup
    "$python" examples/pygame/setup.py "$@"
    # endregion
    ;;
  lv1)
    # region pygame-lv1
    python="${PYTHON:-.cache/pygame-venv/bin/python}"
    "$python" examples/pygame/lv1/main.py "$@"
    # endregion
    ;;
  lv2)
    # region pygame-lv2
    python="${PYTHON:-.cache/pygame-venv/bin/python}"
    "$python" examples/pygame/lv2/main.py "$@"
    # endregion
    ;;
  lv3)
    # region pygame-lv3
    python="${PYTHON:-.cache/pygame-venv/bin/python}"
    "$python" examples/pygame/lv3/main.py "$@"
    # endregion
    ;;
  lv4)
    # region pygame-lv4
    python="${PYTHON:-.cache/pygame-venv/bin/python}"
    "$python" examples/pygame/lv4/main.py "$@"
    # endregion
    ;;
  lv5)
    # region pygame-lv5
    python="${PYTHON:-.cache/pygame-venv/bin/python}"
    "$python" examples/pygame/lv5/main.py "$@"
    # endregion
    ;;
  lv6)
    # region pygame-lv6
    python="${PYTHON:-.cache/pygame-venv/bin/python}"
    "$python" examples/pygame/lv6/main.py "$@"
    # endregion
    ;;
  lv7)
    # region pygame-lv7
    python="${PYTHON:-.cache/pygame-venv/bin/python}"
    "$python" examples/pygame/lv7/main.py "$@"
    # endregion
    ;;
  package)
    # region pygame-package
    "$python" examples/pygame/tools.py package
    # endregion
    ;;
  profile)
    # region pygame-profile
    "$python" examples/pygame/tools.py profile
    # endregion
    ;;
  diagnose)
    # region pygame-diagnose
    "$python" examples/pygame/tools.py diagnose
    # endregion
    ;;
  *) echo '알 수 없는 pygame 실행 항목입니다' >&2; exit 2 ;;
esac
