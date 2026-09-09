#!/bin/sh
# run_dev.sh — Keycloak 을 개발 모드로 띄운다.
#
# **개발 모드는 운영에 쓰면 안 된다.** HTTP 로 열고, 호스트 이름 검사를
# 끄고, 메모리 안에 데이터를 두는 판이다. 6부에서 운영 모드로 바꾼다.
#
# 이 기계는 메모리가 빠듯하다. 그래서 뜨기 전에 남은 양을 세고,
# 모자라면 **뜨지 않고 그 사실을 남긴다**. 억지로 띄우면 세션이 통째로
# OS 에 죽는데, 그러면 여태 한 일이 날아간다.
set -eu
cd "$(dirname "$0")/.."

VER=$(cat keycloak/VERSION)
KC=kc/keycloak-$VER
PORT=${KC_PORT:-8080}
NEED=1800   # MB. 이보다 적으면 안 띄운다
OUT=out
mkdir -p "$OUT"

[ -x "$KC/bin/kc.sh" ] || {
  echo "Keycloak 이 없다 — sh keycloak/fetch.sh 를 먼저 돌릴 것" >&2
  exit 1
}

AVAIL=$(free -m | awk '/^Mem:/ {print $7}')
if [ "$AVAIL" -lt "$NEED" ]; then
  {
    echo "Keycloak 을 띄우지 못했다 — 메모리가 모자란다."
    echo "  필요: ${NEED} MB 이상 / 지금: ${AVAIL} MB"
    echo
    free -m
    echo
    echo '이 덱의 5·7부에서 Keycloak 을 실제로 돌린 화면들은'
    echo '이 기계에서 뜬 것이다. 안 뜨는 날에는 그 사실을 여기 적고'
    echo '해당 슬라이드를 문서 근거(tier C)로 낮춘다 — 지어내지 않는다.'
  } >"$OUT/kc_unavailable.txt"
  cat "$OUT/kc_unavailable.txt" >&2
  exit 2
fi
rm -f "$OUT/kc_unavailable.txt"

# 힙을 못 박는다. 안 박으면 JVM 이 물리 메모리의 1/4 을 잡으려 든다.
JAVA_OPTS_KC_HEAP="-Xms128m -Xmx640m"
export JAVA_OPTS_KC_HEAP

# 첫 관리자. **시연용이다** — 운영에서는 이렇게 만들지 않는다.
KC_BOOTSTRAP_ADMIN_USERNAME=admin
KC_BOOTSTRAP_ADMIN_PASSWORD=admin-demo-1234
export KC_BOOTSTRAP_ADMIN_USERNAME KC_BOOTSTRAP_ADMIN_PASSWORD

IMPORT=
if [ -f keycloak/realm-campus.json ]; then
  mkdir -p "$KC/data/import"
  cp keycloak/realm-campus.json "$KC/data/import/"
  IMPORT=--import-realm
fi

echo "Keycloak $VER 을 띄운다 (남은 메모리 ${AVAIL} MB)"
# --health-enabled 를 켜면 관리 포트(9000)가 열린다.
# 6부에서 쿠버네티스의 readiness/liveness 가 두드릴 그 주소다.
#
# --metrics-enabled 는 따로 켜야 한다. 안 켜면 /metrics 가 404 다 —
# 켠 줄 알고 긁으러 갔다가 404 를 받는 일이 흔하다(10부 4장).
"$KC/bin/kc.sh" start-dev --http-port "$PORT" \
  --health-enabled=true --metrics-enabled=true \
  $IMPORT >"$OUT/kc_server.log" 2>&1 &
echo $! >"$OUT/.kc.pid"

# /health 는 관리 포트(9000)에 있다. 8080 이 아니다 —
# 건강 확인 주소를 바깥에 내걸지 않으려고 포트를 갈라 둔 것이다.
READY=http://localhost:9000/health/ready
i=0
while [ $i -lt 300 ]; do
  if curl -s -o /dev/null -m 2 "$READY"; then
    echo "떴다 — http://localhost:$PORT"
    exit 0
  fi
  i=$((i + 1))
  sleep 1
done
echo 'Keycloak 이 안 뜬다 — out/kc_server.log 를 볼 것' >&2
tail -20 "$OUT/kc_server.log" >&2
exit 1
