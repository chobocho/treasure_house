#!/bin/sh
# app_e2e.sh — 4부에서 만든 앱을 **진짜 Keycloak** 에 붙여 본다.
#
# 이 덱의 약속 하나가 여기서 갚아진다. 4부 6장에서
# "8부에서 바꾸는 것은 -issuer 한 줄뿐" 이라고 적었다.
# 정말 그런지, 코드를 한 글자도 안 고치고 확인한다.
#
# Keycloak 과 가짜 AD 가 이미 떠 있어야 한다.
set -eu
cd "$(dirname "$0")/.."

KC=${KC_URL:-http://localhost:8080}
REALM=campus
PA=${APP_PORT:-9001}
OUT=out
CURL="curl -sS -4"

# 4부의 그 실행 파일이다. 다시 빌드하지도 않는다.
[ -x bin/miniapp ] || {
  echo 'bin/miniapp 이 없다 — make record 를 먼저 돌릴 것' >&2
  exit 1
}

LUNCH_CLIENT_SECRET=lunch-secret-demo
export LUNCH_CLIENT_SECRET

# **바꾸는 것은 -issuer 하나뿐이다.**
bin/miniapp -addr ":$PA" -self "http://localhost:$PA" \
  -issuer "$KC/realms/$REALM" >"$OUT/kc_app.log" 2>&1 &
APP_PID=$!
trap 'kill $APP_PID 2>/dev/null || true' EXIT

i=0
while [ $i -lt 100 ]; do
  if $CURL -o /dev/null -m 1 "http://localhost:$PA/"; then break; fi
  i=$((i + 1))
  sleep 0.2
done

{
  echo '$ bin/miniapp -addr :9001 \'
  echo '    -issuer http://localhost:8080/realms/campus'
  echo
  echo '4부에서 만든 그 실행 파일이다. 다시 빌드하지 않았다.'
  echo '바꾼 것은 -issuer 한 줄뿐이다.'
  echo
  cat "$OUT/kc_app.log"
} >"$OUT/kc_app_start.txt" 2>&1

# ── 브라우저처럼 따라간다 ──
JAR=$OUT/.app_jar.txt
rm -f "$JAR"

$CURL -v -L -c "$JAR" -b "$JAR" "http://localhost:$PA/login" \
  >"$OUT/kc_app_login.txt" 2>&1

# Keycloak 의 로그인 폼을 채워 보낸다.
formaction() {
  sed -n 's/.*action="\([^"]*\)".*/\1/p' "$1" | head -1 \
    | sed 's/&amp;/\&/g'
}
ACTION=$(formaction "$OUT/kc_app_login.txt")
[ -n "$ACTION" ] || { echo '로그인 폼을 못 찾았다' >&2; exit 1; }

$CURL -v -L -c "$JAR" -b "$JAR" -X POST "$ACTION" \
  -d username=minji -d "password=Passw0rd!-demo" \
  >"$OUT/kc_app_callback.txt" 2>&1

$CURL -v -b "$JAR" "http://localhost:$PA/me" \
  >"$OUT/kc_app_me.txt" 2>&1
$CURL -v -b "$JAR" "http://localhost:$PA/admin" \
  >"$OUT/kc_app_admin_denied.txt" 2>&1

# 관리자로 한 번 더 — 갈리는 것은 groups 클레임 하나다.
BJAR=$OUT/.app_bjar.txt
rm -f "$BJAR"
$CURL -sS -4 -L -c "$BJAR" -b "$BJAR" "http://localhost:$PA/login" \
  >"$OUT/.app_blogin.txt" 2>&1
BACTION=$(formaction "$OUT/.app_blogin.txt")
$CURL -sS -4 -L -c "$BJAR" -b "$BJAR" -X POST "$BACTION" \
  -d username=admin.lee -d "password=Passw0rd!-demo" >/dev/null 2>&1
$CURL -v -b "$BJAR" "http://localhost:$PA/admin" \
  >"$OUT/kc_app_admin_ok.txt" 2>&1

rm -f "$JAR" "$BJAR" "$OUT/.app_blogin.txt"
echo '앱 연동 확인 — out/kc_app_*.txt'
