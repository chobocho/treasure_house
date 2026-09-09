#!/bin/sh
# ops_lab.sh — 10부의 실험. 돌아가는 것을 들여다보는 법.
#
# 세션 · 이벤트 · 지표 · 열쇠 회전. 넷 다 관리 API 나 관리 포트로
# 볼 수 있고, 넷 다 "장애가 났을 때 어디를 보나" 의 답이다.
#
# Keycloak 과 가짜 AD 가 이미 떠 있어야 한다.
set -eu
cd "$(dirname "$0")/.."

KC=${KC_URL:-http://localhost:8080}
MGMT=${KC_MGMT:-http://localhost:9000}
REALM=campus
CLIENT=lunch-web
SECRET=lunch-secret-demo
ADMIN=${KC_BOOTSTRAP_ADMIN_USERNAME:-admin}
ADMIN_PW=${KC_BOOTSTRAP_ADMIN_PASSWORD:-admin-demo-1234}
OUT=out
CURL="curl -sS -4"
OC=$KC/realms/$REALM/protocol/openid-connect

TOKEN=$($CURL -X POST \
  "$KC/realms/master/protocol/openid-connect/token" \
  -d client_id=admin-cli -d "username=$ADMIN" \
  -d "password=$ADMIN_PW" -d grant_type=password \
  | python3 -c 'import json,sys
print(json.load(sys.stdin)["access_token"])')
AUTH="Authorization: Bearer $TOKEN"

api() {
  m=$1
  p=$2
  b=${3:-}
  if [ -n "$b" ]; then
    $CURL -X "$m" "$KC/admin/realms$p" -H "$AUTH" \
      -H 'Content-Type: application/json' --data-binary "@$b"
  else
    $CURL -X "$m" "$KC/admin/realms$p" -H "$AUTH"
  fi
}

VERIFIER=lunch-demo-verifier-0123456789-abcdefghijklmnop
CHALLENGE=$(printf %s "$VERIFIER" | openssl dgst -sha256 -binary \
  | openssl base64 -A | tr '+/' '-_' | tr -d '=')

login() {
  jar=$OUT/.ops_jar.txt
  rm -f "$jar"
  q="response_type=code&client_id=$CLIENT"
  q="$q&redirect_uri=http%3A%2F%2Flocalhost%3A9001%2Fcallback"
  q="$q&scope=openid&state=ops&nonce=ops"
  q="$q&code_challenge=$CHALLENGE&code_challenge_method=S256"
  $CURL -c "$jar" -b "$jar" "$OC/auth?$q" >"$OUT/.ops_form.html"
  act=$(sed -n 's/.*action="\([^"]*\)".*/\1/p' "$OUT/.ops_form.html" \
    | head -1 | sed 's/&amp;/\&/g')
  $CURL -c "$jar" -b "$jar" -X POST "$act" \
    -d "username=$1" -d "password=$2" -o /dev/null
  rm -f "$jar" "$OUT/.ops_form.html"
}

# ── 실험 1. 이벤트 켜고 로그인해 보기 ──────────────────────────────
#
# Keycloak 은 기본으로 이벤트를 **저장하지 않는다**. 켜야 남는다.
cat >"$OUT/.events.json" <<'JEOF'
{
  "eventsEnabled": true,
  "eventsExpiration": 604800,
  "adminEventsEnabled": true,
  "adminEventsDetailsEnabled": false,
  "enabledEventTypes": ["LOGIN", "LOGIN_ERROR", "LOGOUT",
    "CODE_TO_TOKEN", "REFRESH_TOKEN", "CLIENT_LOGIN"]
}
JEOF
api PUT "/$REALM/events/config" "$OUT/.events.json" >/dev/null
rm -f "$OUT/.events.json"

login minji 'Passw0rd!-demo'
login minji '틀린비밀번호'
login jisoo.oh 'Passw0rd!-demo'

{
  echo "\$ curl '.../realms/$REALM/events?max=10'"
  api GET "/$REALM/events?max=10" | python3 -c 'import json,sys
rows = json.load(sys.stdin)
print("  %-14s %-12s %s" % ("종류", "사용자", "무슨 일"))
for r in rows:
    d = r.get("details", {})
    who = d.get("username", r.get("userId", "") or "-")
    err = r.get("error", "")
    print("  %-14s %-12s %s" % (r["type"], who, err or "성공"))
print()
print("  모두 %d건" % len(rows))'
  echo
  echo '이벤트는 기본으로 **꺼져 있다**. 켜야 남는다.'
  echo 'LOGIN_ERROR 의 error 칸이 왜 실패했는지 알려 준다.'
} >"$OUT/kc_ops_events.txt" 2>&1

# ── 실험 2. 지금 로그인해 있는 사람 ────────────────────────────────
CID=$(api GET "/$REALM/clients?clientId=$CLIENT" \
  | python3 -c 'import json,sys
rows = json.load(sys.stdin)
print(rows[0]["id"] if rows else "")')
{
  echo "\$ curl '.../clients/<id>/user-sessions'"
  api GET "/$REALM/clients/$CID/user-sessions" \
    | python3 -c 'import json,sys
rows = json.load(sys.stdin)
print("  %-12s %-16s %s" % ("사용자", "시작", "마지막 접근"))
for r in rows:
    print("  %-12s %-16s %s" % (r.get("username"), r.get("start"),
                                r.get("lastAccess")))
print()
print("  모두 %d개" % len(rows))
print()
print("  숫자는 1970년부터 센 밀리초다 —")
print("  4부의 그 NumericDate 와 같은 셈법이다.")'
  echo
  echo '$ 세션 통계 (realm 전체)'
  api GET "/$REALM/client-session-stats" | python3 -m json.tool \
    | sed 's/^/  /'
} >"$OUT/kc_ops_sessions.txt" 2>&1

# ── 실험 3. 지표 ───────────────────────────────────────────────────
# 어떤 지표가 있는지부터 센다. 이름을 짐작해 grep 했다가
# 빈 화면을 얻은 적이 있어서, 있는 것을 세어 보고 고른다.
{
  echo "\$ curl $MGMT/metrics | grep -v '^#' | sed 's/{.*//' | sort -u"
  $CURL "$MGMT/metrics" | grep -v '^#' \
    | sed 's/{.*//;s/ .*//' | sort -u >"$OUT/.names.txt"
  printf '  이름이 모두 %d가지 있다. 그중 눈여겨볼 것:\n\n' \
    "$(wc -l <"$OUT/.names.txt")"
  echo '  # 데이터베이스 연결 풀 — 바닥나면 전부 멈춘다'
  $CURL "$MGMT/metrics" \
    | grep -E '^agroal_(active|available|awaiting)' \
    | sed 's/^/    /'
  echo
  echo '  # 들어온 요청'
  $CURL "$MGMT/metrics" \
    | grep -E '^http_server_(active_requests|active_connections)' \
    | sed 's/^/    /'
  rm -f "$OUT/.names.txt"
  echo
  echo '프로메테우스가 긁어 가는 그 모양이다.'
  echo '관리 포트(9000)에 있고, 바깥에 내걸지 않는다(6부 2장).'
  echo
  echo '⚠ --metrics-enabled 를 따로 켜야 한다. 안 켜면 404 다 —'
  echo '  health 만 켜 놓고 긁으러 갔다가 404 를 받은 적이 있다.'
} >"$OUT/kc_ops_metrics.txt" 2>&1

# ── 실험 4. 서명 열쇠를 하나 더 ────────────────────────────────────
#
# 열쇠를 바꾸는 날 무슨 일이 생기는가. 새 열쇠를 **먼저 얹고**
# 그 다음부터 새 것으로 서명하면, 이미 나간 토큰도 계속 확인된다.
{
  echo '$ 지금 JWKS'
  $CURL "$OC/certs" | python3 -c 'import json,sys
for k in json.load(sys.stdin)["keys"]:
    print("  kid %s  alg %s  use %s"
          % (k["kid"], k.get("alg"), k.get("use")))'
} >"$OUT/kc_ops_keys.txt" 2>&1

cat >"$OUT/.key.json" <<'JEOF'
{
  "name": "rsa-generated-2",
  "providerId": "rsa-generated",
  "providerType": "org.keycloak.keys.KeyProvider",
  "config": {
    "priority": ["200"],
    "algorithm": ["RS256"],
    "keySize": ["2048"]
  }
}
JEOF
api POST "/$REALM/components" "$OUT/.key.json" >/dev/null
rm -f "$OUT/.key.json"

{
  echo
  echo '$ 새 열쇠를 하나 더 얹는다'
  echo '  (priority 를 높여 두면 그쪽으로 서명한다)'
  echo '$ 다시 JWKS'
  $CURL "$OC/certs" | python3 -c 'import json,sys
for k in json.load(sys.stdin)["keys"]:
    print("  kid %s  alg %s  use %s"
          % (k["kid"], k.get("alg"), k.get("use")))'
  echo
  echo '**둘 다 걸려 있다.** 옛 열쇠로 서명된 토큰도 만료될 때까지'
  echo '확인된다 — 그래서 kid 가 있는 것이다(4부 6장).'
  echo '옛 열쇠는 그 토큰들이 다 만료된 뒤에 뺀다.'
} >>"$OUT/kc_ops_keys.txt" 2>&1

echo '운영 실험 완료 — out/kc_ops_*.txt'
