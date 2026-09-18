#!/bin/sh
# serve_once.sh — 폰에 웹 서버를 띄워 한 번 묻고 끈다 (실험 11).
#
#   serve_once.sh PORT DIR FILE    → "상태코드 받은바이트"
#
# 파이썬 표준 라이브러리의 http.server 로 DIR 을 PORT 에 내놓고,
# curl 로 FILE 을 한 번 받은 뒤 서버를 끈다. 127.0.0.1 에만
# 붙이므로 같은 폰 밖에서는 보이지 않는다 — 바깥에 열려면
# --bind 를 바꿔야 하고, 그것은 이 덱이 하지 않는 일이다(14부).
# 1024 미만 포트는 8부에서 본 대로 대개 막혀 있어 8080 같은 높은
# 포트를 쓴다. 서버가 뜰 때까지 기다리는 시간은 최대 5초.
set -u
[ $# -eq 3 ] || { echo '사용법: serve_once.sh PORT DIR FILE' >&2
                  exit 2; }
port=$1 dir=$2 file=$3
python3 -m http.server "$port" --bind 127.0.0.1 -d "$dir" \
  >/dev/null 2>&1 &
pid=$!
trap 'kill "$pid" 2>/dev/null; wait "$pid" 2>/dev/null' EXIT
i=0
until curl -s -o /dev/null "http://127.0.0.1:$port/"; do
  i=$((i + 1))
  [ "$i" -le 50 ] || { echo '서버가 뜨지 않았다' >&2; exit 1; }
  sleep 0.1
done
curl -s -o /dev/null -w '%{http_code} %{size_download}\n' \
  "http://127.0.0.1:$port/$file"
