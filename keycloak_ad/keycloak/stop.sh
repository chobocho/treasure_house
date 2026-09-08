#!/bin/sh
# stop.sh — 띄운 Keycloak 을 끈다.
#
# 반드시 끈다. JVM 하나가 640 MB 를 물고 있으면 다음 작업이 죽는다.
set -eu
cd "$(dirname "$0")/.."

PIDFILE=out/.kc.pid
[ -f "$PIDFILE" ] || { echo '띄운 적이 없다'; exit 0; }

PID=$(cat "$PIDFILE")
if kill "$PID" 2>/dev/null; then
  # 죽을 때까지 기다린다. 안 기다리면 다음 실행이 포트를 못 잡는다.
  i=0
  while [ $i -lt 60 ] && kill -0 "$PID" 2>/dev/null; do
    i=$((i + 1))
    sleep 1
  done
  kill -9 "$PID" 2>/dev/null || true
  echo "껐다 (pid $PID)"
else
  echo "이미 꺼져 있다 (pid $PID)"
fi
rm -f "$PIDFILE"
