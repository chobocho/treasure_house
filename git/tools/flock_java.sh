#!/bin/sh
# JVM 은 한 번에 하나만 — 둘이 겹치면 이 기계는 OOM 으로 죽는다
# (PLAN.md §0.7).
#
#     sh tools/flock_java.sh javac -d build/java @sources.txt
#     sh tools/flock_java.sh java -cp build/java mygit.RunTests
#
# compress/tools/flock_java.sh 에서 물려받았다. 잠금 파일은 덱마다
# 따로 두지 않고 하나를 같이 쓴다 — 다른 덱의 JVM 과 겹쳐도 죽기는
# 마찬가지다.
# flock 이 없는 환경(일부 proot)에서는 잠금 없이 그냥 돌린다 — 그때는
# 병렬 호출을 사람이 막아야 한다.
set -e
LOCK="${TMPDIR:-/tmp}/treasure_house_java.lock"
if command -v flock >/dev/null 2>&1; then
  exec flock "$LOCK" "$@"
fi
echo "  (flock 없음 — 잠금 없이 돈다. JVM 을 동시에 띄우지 말 것)" >&2
exec "$@"
