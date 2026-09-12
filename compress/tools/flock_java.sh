#!/bin/sh
# JVM 은 한 번에 하나만 — 이 기계에서 둘이 겹치면 세션째 OOM 으로 죽는다.
#
#     sh tools/flock_java.sh javac -d build @sources.txt
#     sh tools/flock_java.sh java -cp build compresslib.RunTests
#
# flock 이 없는 환경(일부 proot)에서는 잠금 없이 그냥 돌린다 — 그때는
# 병렬 호출을 사람이 막아야 한다. 잠금이 걸렸는지 첫 줄에 찍어 둔다.
set -e
LOCK="${TMPDIR:-/tmp}/compress_java.lock"
if command -v flock >/dev/null 2>&1; then
  exec flock "$LOCK" "$@"
fi
echo "  (flock 없음 — 잠금 없이 돈다. JVM 을 동시에 띄우지 말 것)" >&2
exec "$@"
