#!/bin/sh
# record.sh — 덱에 실릴 '진짜 출력' 을 전부 다시 남긴다.
#
# 이 덱의 검은 바탕 화면은 하나도 손으로 쓰지 않았다. 전부 여기서 나온다.
# 그래서 이 파일은 덱의 증거 목록이기도 하다 — 무엇을 실제로 돌려 봤는지
# 알고 싶으면 여기를 읽으면 된다.
#
#   sh tools/record.sh          # out/ 를 다시 채운다
#   sh tools/record.sh --check  # 두 번 돌려 결과가 같은지만 본다
#
# 두 번 돌려 같아야 하는 이유는 tools/scrub.py 머리말에 적어 두었다.
set -eu
cd "$(dirname "$0")/.."

OUT=out
mkdir -p "$OUT"

GO=${GO:-go}
GOTOOLCHAIN=local
GOFLAGS=-p=1
export GOTOOLCHAIN GOFLAGS

# 포트는 프로그램 번호와 맞춰 둔다. 겹치면 바꿔서 다시 돌리면 된다.
P1=8081; P2=8082; P3=8083; P4=8443; P4H=8084
PL=10389; PLS=10636
PI=9000; PA=9001

# 4부의 캡처는 시계와 난수를 못 박고 뜬다. 토큰에는 발급 시각과 일련번호가
# 들어가서, 고정하지 않으면 같은 명령이 매번 다른 글자를 내기 때문이다.
# (왜 위험한 깃발인지는 oidc/miniidp/idp.go 의 FixForCapture 에 적었다)
FIXED=2026-09-08T12:00:00Z
LOOK=2026-09-08T12:01:00Z   # 토큰이 살아 있는 시각
LATER=2026-09-08T13:00:00Z  # 기한이 지난 뒤

PIDS=''
stop_all() {
  [ -n "$PIDS" ] || return 0
  kill $PIDS 2>/dev/null || true
  # 죽을 때까지 기다린다. 안 기다리면 다음 서버가 아직 안 놓인 포트를
  # 잡으려다 실패하고, 그 실패가 조용히 지나간다.
  wait $PIDS 2>/dev/null || true
  PIDS=''
}
trap stop_all EXIT INT TERM

# port_busy <포트> — 이미 누가 듣고 있으면 참.
#
# 왜 굳이 확인하나: 지난번 캡처가 남긴 유령이 포트를 물고 있으면, 새 서버는
# 조용히 죽고 curl 은 유령에게서 답을 받아 온다. 그러면 캡처는 '옛날 코드의
# 출력' 인데 아무도 눈치채지 못한다. 실제로 한 번 그렇게 당했다.
port_busy() {
  curl -s -o /dev/null -k --max-time 1 "http://127.0.0.1:$1/" && return 0
  curl -s -o /dev/null -k --max-time 1 "https://127.0.0.1:$1/" && return 0
  return 1
}

require_free() {
  for p in "$@"; do
    if port_busy "$p"; then
      echo "포트 $p 를 이미 누가 쓰고 있다 — 그대로 두면 캡처가" >&2
      echo "옛 프로세스의 출력이 된다. 그 프로세스를 끄고 다시 돌릴 것." >&2
      exit 1
    fi
  done
}

# 먼저 빌드해 두고 그 실행 파일을 직접 띄운다.
#
# `go run` 을 쓰면 안 된다. go run 은 제가 만든 실행 파일을 자식 프로세스로
# 돌리는 껍데기라, 우리가 붙잡은 번호(PID)는 껍데기의 것이다. 껍데기를
# 죽여도 진짜 서버는 살아남아 포트를 물고 있고, 다음 번 캡처는 그 유령이
# 받는다 — 두 번 돌려 결과가 달랐던 원인이 정확히 이것이었다.
BIN=bin
build_all() {
  mkdir -p "$BIN"
  for d in web/01_hello web/02_form_cookie web/03_redirect web/04_tls \
           ldap/fakead/cmd/fakead ldap/ldapcli \
           oidc/miniidp/cmd/miniidp oidc/miniapp oidc/jwtool; do
    $GO build -o "$BIN/$(basename "$d")" "./$d"
  done
}

# start <디렉터리> <로그파일> <인자...> — 서버를 띄우고 뜰 때까지 기다린다.
start() {
  dir=$1; logf=$2; shift 2
  "$BIN/$(basename "$dir")" "$@" >"$logf" 2>&1 &
  PIDS="$PIDS $!"
}

# wait_up <url> — 200 이든 404 든 대답이 올 때까지 기다린다(최대 20초).
wait_up() {
  i=0
  while [ $i -lt 200 ]; do
    if curl -s -o /dev/null -k --max-time 1 "$1"; then return 0; fi
    i=$((i + 1))
    sleep 0.1
  done
  echo "서버가 안 뜬다: $1" >&2
  return 1
}

say() { printf '  %s\n' "$1"; }

# wait_ldap <포트> — 가짜 AD 가 바인드에 답할 때까지 기다린다.
# curl 로는 두드릴 수 없다 — LDAP 은 HTTP 가 아니다.
SVC='CN=svc-keycloak,OU=Service Accounts,DC=ad,DC=campus,DC=example'
PW='Passw0rd!-demo'
wait_ldap() {
  i=0
  while [ $i -lt 100 ]; do
    if bin/ldapcli -h "localhost:$1" -q -D "$SVC" -w "$PW" bind \
         >/dev/null 2>&1; then
      return 0
    fi
    i=$((i + 1))
    sleep 0.1
  done
  echo "가짜 AD 가 안 뜬다: $1" >&2
  return 1
}

# 모든 curl 은 이걸 쓴다.
#   -sS  진행률 막대는 끄고 오류는 보여 준다
#   -4   IPv4 로 못 박는다. localhost 는 ::1 과 127.0.0.1 둘 다로 풀리고,
#        curl 이 그때그때 다른 쪽을 고르는 바람에 캡처가 두 판으로 갈렸다.
CURL="curl -sS -4"

# ── 0. 시험과 정적 검사 ───────────────────────────────────────────
say '0. 포트 확인 · 빌드 · go test · go vet'
require_free $P1 $P2 $P3 $P4 $P4H $PL $PLS $PI $PA
build_all
# -count=1 로 캐시를 끈다. 캐시가 걸리면 "(cached)" 가 찍히고, 안 걸리면
# 걸린 시간이 찍혀서 같은 명령이 두 판을 낸다. 그보다 중요한 이유는
# 따로 있다 — 이 덱은 "실제로 돌려 봤다" 고 말한다. 그러면 캡처도
# 실제로 돌린 결과여야 한다.
$GO test -count=1 ./... >"$OUT/web_test.txt" 2>&1 || true
$GO vet ./... >"$OUT/web_vet.txt" 2>&1 || true

# ── 1. 가장 작은 서버 ─────────────────────────────────────────────
say '1. web/01_hello'
start web/01_hello "$OUT/web01_server.txt" -addr ":$P1"
wait_up "http://localhost:$P1/"

$CURL -v "http://localhost:$P1/" >"$OUT/web01_root.txt" 2>&1
# --trace-ascii 는 오간 바이트를 그대로 보여 준다. "HTTP 는 글자다" 의 증거.
$CURL --trace-ascii "$OUT/web01_trace.txt" -o /dev/null \
  "http://localhost:$P1/echo"
$CURL "http://localhost:$P1/echo" >"$OUT/web01_echo.txt" 2>&1
$CURL "http://localhost:$P1/echo" \
  -H 'X-Try: one' -H 'X-Try: two' -H 'Accept-Language: ko-KR' \
  >"$OUT/web01_echo_headers.txt" 2>&1
$CURL -v "http://localhost:$P1/없는주소" >"$OUT/web01_404.txt" 2>&1
stop_all

# ── 2. 폼 · 쿠키 · 세션 ───────────────────────────────────────────
say '2. web/02_form_cookie'
start web/02_form_cookie "$OUT/web02_server.txt" -addr ":$P2"
wait_up "http://localhost:$P2/"

JAR=$OUT/web02_jar.txt
rm -f "$JAR"
$CURL "http://localhost:$P2/" >"$OUT/web02_form.txt" 2>&1
$CURL -v -c "$JAR" \
  -d 'user=minji' -d 'pass=Passw0rd!-demo' \
  "http://localhost:$P2/login" >"$OUT/web02_login_ok.txt" 2>&1
$CURL -v -d 'user=minji' -d 'pass=틀린것' \
  "http://localhost:$P2/login" >"$OUT/web02_login_bad.txt" 2>&1
$CURL -v "http://localhost:$P2/login?user=minji" \
  >"$OUT/web02_login_get.txt" 2>&1
$CURL -v "http://localhost:$P2/me" >"$OUT/web02_me_nocookie.txt" 2>&1
$CURL -v -b "$JAR" "http://localhost:$P2/me" >"$OUT/web02_me_ok.txt" 2>&1
$CURL -v -b 'lunch_session=aaaabbbbccccdddd' \
  "http://localhost:$P2/me" >"$OUT/web02_me_forged.txt" 2>&1
# 로그아웃이 항아리를 덮어쓰기 전에 '로그인된 상태의 항아리' 를 남겨 둔다.
cp "$JAR" "$OUT/web02_jar_loggedin.txt"
$CURL -v -b "$JAR" -c "$JAR" -X POST \
  "http://localhost:$P2/logout" >"$OUT/web02_logout.txt" 2>&1
$CURL -v -b "$JAR" "http://localhost:$P2/me" \
  >"$OUT/web02_after_logout.txt" 2>&1
stop_all

# ── 3. 리다이렉트 ─────────────────────────────────────────────────
say '3. web/03_redirect'
start web/03_redirect "$OUT/web03_server.txt" -addr ":$P3"
wait_up "http://localhost:$P3/start"

$CURL -v "http://localhost:$P3/start" >"$OUT/web03_nofollow.txt" 2>&1
$CURL -v -L "http://localhost:$P3/start" >"$OUT/web03_chain.txt" 2>&1
$CURL -v -L -d 'a=1' \
  "http://localhost:$P3/method?code=303" >"$OUT/web03_post_303.txt" 2>&1
$CURL -v -L -d 'a=1' \
  "http://localhost:$P3/method?code=307" >"$OUT/web03_post_307.txt" 2>&1
$CURL -v "http://localhost:$P3/method?code=200" \
  >"$OUT/web03_badcode.txt" 2>&1
$CURL -v -L --max-redirs 3 "http://localhost:$P3/loop?n=0" \
  >"$OUT/web03_loop.txt" 2>&1 || true
stop_all

# ── 4. TLS ────────────────────────────────────────────────────────
#
# 알아 둘 것: web04_insecure.txt 의 맨 끝 한 줄(`{ [5 bytes data]` 과
# `} [5 bytes data]`)은 두 번 돌리면 가끔 바뀐다. TLS 1.3 의 세션 티켓이
# 오는 것과 curl 이 연결을 닫는 것이 경주를 하기 때문이다. 둘 다 맞는
# 출력이라 손대지 않았다 — 덱은 이 파일의 9번째 줄만 인용한다.
say '4. web/04_tls'
sh certs/make_certs.sh >/dev/null
start web/04_tls "$OUT/web04_server.txt" \
  -addr ":$P4" -http ":$P4H" -cert certs/sso.crt -key certs/sso.key
wait_up "https://localhost:$P4/tls"

RES="--resolve sso.campus.example:$P4:127.0.0.1"
# 우리 CA 를 안 알려 주면 악수가 깨진다 — curl 이 내는 그 오류 그대로.
$CURL -v $RES "https://sso.campus.example:$P4/tls" \
  >"$OUT/web04_notrust.txt" 2>&1 || true
$CURL -v $RES --cacert certs/demo-ca.crt \
  "https://sso.campus.example:$P4/tls" >"$OUT/web04_trust.txt" 2>&1
# 이름이 다르면 CA 를 믿어도 거절한다.
$CURL -v --resolve "lunch.campus.example:$P4:127.0.0.1" \
  --cacert certs/demo-ca.crt \
  "https://lunch.campus.example:$P4/tls" \
  >"$OUT/web04_wrongname.txt" 2>&1 || true
# 검증을 끄면(-k) 붙기는 한다. 무엇을 포기한 것인지 화면에 남긴다.
$CURL -v -k "https://localhost:$P4/tls" >"$OUT/web04_insecure.txt" 2>&1
# 본문만 따로 남긴다.
#
# TLS 1.3 의 세션 티켓은 악수가 끝난 **뒤에** 따로 온다. 몇 장이 오는지,
# curl 이 끊기 전에 몇 장을 받아 적는지가 그때그때 다르다 — 그래서 -v
# 출력의 줄 번호가 밀린다. 덱이 줄 번호로 인용하므로, 흔들리지 않는
# 조각은 따로 떠 둔다.
$CURL -s -k "https://localhost:$P4/tls" >"$OUT/web04_insecure_body.txt" 2>&1
$CURL -s $RES --cacert certs/demo-ca.crt \
  "https://sso.campus.example:$P4/tls" >"$OUT/web04_trust_body.txt" 2>&1
$CURL -v "http://localhost:$P4H/tls" >"$OUT/web04_redirect.txt" 2>&1

# 인증서 자체를 사람이 읽는 글로. SAN·EKU·유효기간이 여기 다 있다.
openssl x509 -in certs/sso.crt -noout -subject -issuer -dates \
  -ext subjectAltName,extendedKeyUsage,basicConstraints \
  >"$OUT/web04_cert_text.txt" 2>&1
stop_all

# ── 5. 가짜 AD (3부) ──────────────────────────────────────────────
say '5. ldap/fakead + ldapcli'
MINJI='CN=Kim Minji,OU=Students,DC=ad,DC=campus,DC=example'
JISOO='CN=Oh Jisoo,OU=Staff,DC=ad,DC=campus,DC=example'
HANA='CN=Park Hana,OU=Students,DC=ad,DC=campus,DC=example'
BASE='DC=ad,DC=campus,DC=example'

start ldap/fakead/cmd/fakead "$OUT/ad_server_start.txt" \
  -addr ":$PL" -ldaps ":$PLS" -log "$OUT/ad_fakead.log" \
  -cert certs/ldap.crt -key certs/ldap.key
wait_ldap "$PL"

CLI="bin/ldapcli -h localhost:$PL"

# 바인드 한 번을 바이트까지 통째로. 3부에서 가장 여러 번 인용할 화면이다.
$CLI -D "$SVC" -w "$PW" bind >"$OUT/ad_bind_ok.txt" 2>&1

# 실패 셋 — AD 의 data 코드를 눈으로 보는 자리
$CLI -q -D "$MINJI" -w '틀린비밀번호' bind \
  >"$OUT/ad_bind_52e.txt" 2>&1 || true
$CLI -q -D "$JISOO" -w "$PW" bind >"$OUT/ad_bind_533.txt" 2>&1 || true
$CLI -q -D '' -w '' bind >"$OUT/ad_bind_anon.txt" 2>&1 || true

# 다섯 번 틀려 잠그고, 그다음 맞는 비밀번호로 눌러 본다
for i in 1 2 3 4 5; do
  $CLI -q -D "$HANA" -w '틀린비밀번호' bind >/dev/null 2>&1 || true
done
$CLI -q -D "$HANA" -w "$PW" bind >"$OUT/ad_bind_775.txt" 2>&1 || true

# 검색 한 번을 바이트까지
$CLI -D "$SVC" -w "$PW" search '(sAMAccountName=minji)' \
  cn mail objectGUID memberOf >"$OUT/ad_search_bytes.txt" 2>&1

# 결과만 — 필터를 바꿔 가며
{
  for f in '(sAMAccountName=minji)' '(objectClass=group)' \
           '(&(objectClass=user)(mail=*))' '(cn=Kim*)' \
           '(!(mail=*))' '(userAccountControl=514)'; do
    printf '$ ldapcli search %s cn\n' "'$f'"
    $CLI -q -D "$SVC" -w "$PW" search "$f" cn 2>&1
    echo
  done
} >"$OUT/ad_search_filters.txt" 2>&1

# 범위 셋을 나란히
{
  for sc in base one sub; do
    printf '$ ldapcli -s %s search "(objectClass=*)"\n' "$sc"
    $CLI -q -s "$sc" -b "$BASE" -D "$SVC" -w "$PW" \
      search '(objectClass=*)' 2>&1 | tail -2
    echo
  done
} >"$OUT/ad_search_scopes.txt" 2>&1

# 그룹으로 사람 찾기 — 9부 인가 이야기의 씨앗
$CLI -q -D "$SVC" -w "$PW" \
  search "(memberOf=CN=lunch-admins,OU=Groups,$BASE)" \
  cn sAMAccountName >"$OUT/ad_search_memberof.txt" 2>&1

# 바인드 없이 검색하면 거절당한다
$CLI -q -D '' -w '' search '(objectClass=*)' \
  >"$OUT/ad_search_nobind.txt" 2>&1 || true

# LDAPS — 우리 CA 를 알려 줄 때와 아닐 때
bin/ldapcli -h "localhost:$PLS" -ldaps -name ldap.ad.campus.example \
  -cacert certs/demo-ca.crt -q -D "$SVC" -w "$PW" \
  search '(sAMAccountName=minji)' cn >"$OUT/ad_ldaps_ok.txt" 2>&1
bin/ldapcli -h "localhost:$PLS" -ldaps -name ldap.ad.campus.example \
  -q -D "$SVC" -w "$PW" bind >"$OUT/ad_ldaps_notrust.txt" 2>&1 || true

stop_all

# ── 5. 도구 상자 ──────────────────────────────────────────────────
say '6. 도구 상자 (base64 · 해시 · 서명 · JSON)'
{
  echo '$ printf %s "minji:Passw0rd!-demo" | base64'
  printf %s 'minji:Passw0rd!-demo' | base64
  echo
  echo '$ printf %s "minji" | base64'
  printf %s 'minji' | base64
  echo '  (= 이 붙은 이유: base64 는 3바이트를 4글자로 바꾼다.'
  echo '   5바이트는 3으로 안 나눠떨어져 남은 자리를 = 로 채운다)'
  echo
  echo '$ echo -n "?~>" | base64          # + 와 / 가 나오는 값'
  printf %s '?~>' | base64
  echo '  base64url 은 여기서 + 를 - 로, / 를 _ 로 바꾸고 = 를 뗀다.'
  echo '  주소(URL)에 그대로 실으려면 그래야 하기 때문이다 — 4부의 토큰이 그 꼴이다.'
} >"$OUT/tool_base64.txt" 2>&1

{
  echo '$ printf %s "minji" | sha256sum'
  printf %s 'minji' | sha256sum
  echo
  echo '$ printf %s "minjj" | sha256sum     # 마지막 글자 하나만 다르다'
  printf %s 'minjj' | sha256sum
  echo
  echo '같은 입력은 언제나 같은 값이 나오고, 한 글자만 달라도 전부 달라진다.'
  echo '거꾸로 되돌릴 수는 없다. 그래서 비밀번호를 이렇게 저장한다.'
} >"$OUT/tool_hash.txt" 2>&1

{
  echo '$ printf %s "lunch" > /tmp/msg'
  echo '$ openssl dgst -sha256 -sign certs/demo-ca.key -out /tmp/sig /tmp/msg'
  echo '$ openssl dgst -sha256 -verify <(공개키) -signature /tmp/sig /tmp/msg'
  printf %s 'lunch' >"$OUT/.msg.tmp"
  openssl dgst -sha256 -sign certs/demo-ca.key \
    -out "$OUT/.sig.tmp" "$OUT/.msg.tmp"
  openssl pkey -in certs/demo-ca.key -pubout -out "$OUT/.pub.tmp" 2>/dev/null
  openssl dgst -sha256 -verify "$OUT/.pub.tmp" \
    -signature "$OUT/.sig.tmp" "$OUT/.msg.tmp"
  echo
  echo '$ printf %s "lunchX" > /tmp/msg    # 글자를 하나 바꾼 뒤 같은 서명으로'
  printf %s 'lunchX' >"$OUT/.msg.tmp"
  openssl dgst -sha256 -verify "$OUT/.pub.tmp" \
    -signature "$OUT/.sig.tmp" "$OUT/.msg.tmp" || true
  echo
  echo '개인키를 가진 쪽만 서명할 수 있고, 공개키를 가진 누구나 확인할 수 있다.'
  echo '4부의 ID 토큰이 정확히 이 방식으로 서명된다.'
  rm -f "$OUT/.msg.tmp" "$OUT/.sig.tmp" "$OUT/.pub.tmp"
} >"$OUT/tool_sign.txt" 2>&1

{
  echo '$ echo "{\"sub\":\"minji\",\"groups\":[\"lunch-users\"]}" \'
  echo '    | python3 -m json.tool'
  printf '%s' '{"sub":"minji","groups":["lunch-users"],"exp":1789000000}' \
    | python3 -m json.tool
  echo
  echo '$ echo "{\"sub\":\"minji\",}" | python3 -m json.tool   # 쉼표 하나 더'
  printf '%s' '{"sub":"minji",}' | python3 -m json.tool 2>&1 || true
} >"$OUT/tool_json.txt" 2>&1

# ── 7. OIDC — miniidp · miniapp · jwtool (4부) ────────────────────
say '7. oidc/miniidp + miniapp + jwtool'
IDP="http://localhost:$PI/realms/campus"
OC="$IDP/protocol/openid-connect"
BACK="http://localhost:$PA/callback"

start ldap/fakead/cmd/fakead "$OUT/.fakead.raw" -addr ":$PL"
wait_ldap $PL
start oidc/miniidp/cmd/miniidp "$OUT/oidc_idp.log" -addr ":$PI" \
  -issuer "$IDP" -key certs/idp-signing.key -ldap "localhost:$PL" \
  -redirect "$BACK" -fixed-now "$FIXED"
wait_up "$OC/certs"

# PKCE 는 이 두 줄이 전부다. verifier 를 만들고, 그 해시를 challenge 로.
VERIFIER='lunch-demo-verifier-0123456789-abcdefghijklmnop'
CHALLENGE=$(printf %s "$VERIFIER" | openssl dgst -sha256 -binary \
  | openssl base64 -A | tr '+/' '-_' | tr -d '=')
{
  echo '$ VERIFIER=lunch-demo-verifier-0123456789-abcdefghijklmnop'
  echo '$ printf %s "$VERIFIER" | openssl dgst -sha256 -binary \'
  echo '    | openssl base64 -A | tr "+/" "-_" | tr -d "="'
  echo "$CHALLENGE"
  echo
  echo 'challenge 는 verifier 의 해시다. 해시는 되돌릴 수 없으므로,'
  echo '앞의 요청을 훔쳐본 쪽은 challenge 만 보고 verifier 를 못 만든다.'
} >"$OUT/oidc_pkce.txt" 2>&1

# ── 안내문과 공개키 ──
$CURL "$IDP/.well-known/openid-configuration" \
  >"$OUT/oidc_discovery.txt" 2>&1
$CURL "$OC/certs" >"$OUT/oidc_certs.txt" 2>&1

# 공개키의 n 은 342글자라 한 줄에 안 들어간다. 가운데를 줄여 한 벌 더 뜬다.
python3 - "$OUT/oidc_certs.txt" >"$OUT/oidc_certs_short.txt" <<'PYEOF'
import json
import sys

k = json.load(open(sys.argv[1]))['keys'][0]
print('$ curl .../certs | python3 -m json.tool')
print('  (n 은 342글자라 가운데를 줄였다)')
print('{')
print('  "keys": [')
print('    {')
fields = ['kty', 'use', 'alg', 'kid', 'n', 'e']
for n, f in enumerate(fields):
    v = k[f]
    if len(v) > 40:
        v = '%s…(%d자 줄임)…%s' % (v[:16], len(v) - 32, v[-16:])
    print('      "%s": "%s"%s' % (f, v, ',' if n < len(fields) - 1 else ''))
print('    }')
print('  ]')
print('}')
PYEOF

# ── 로그인 화면 ──
AQ="response_type=code&client_id=lunch-web"
AQ="$AQ&redirect_uri=http%3A%2F%2Flocalhost%3A$PA%2Fcallback"
AQ="$AQ&scope=openid+profile+email&state=st-demo-123&nonce=no-demo-456"
AQ="$AQ&code_challenge=$CHALLENGE&code_challenge_method=S256"

{
  echo '$ showurl "$AUTH_URL"'
  python3 tools/showurl.py "$OC/auth?$AQ"
  echo
  echo '앱이 브라우저를 이 주소로 보낸다. 칸 하나하나가 4부 2·3장의 주제다.'
} >"$OUT/oidc_authorize_url.txt" 2>&1
$CURL -v "$OC/auth?$AQ" >"$OUT/oidc_authorize.txt" 2>&1
$CURL -v "$OC/auth?$(echo "$AQ" | sed 's/client_id=lunch-web/client_id=남의앱/')" \
  >"$OUT/oidc_authorize_badclient.txt" 2>&1
$CURL -v "$OC/auth?$(echo "$AQ" | sed "s/&code_challenge=$CHALLENGE//")" \
  >"$OUT/oidc_authorize_nopkce.txt" 2>&1

# ── 비밀번호를 IdP 에 낸다. 앱은 이 화면을 못 본다 ──
FORM="-d client_id=lunch-web -d redirect_uri=$BACK"
FORM="$FORM -d scope=openid+profile+email -d state=st-demo-123"
FORM="$FORM -d nonce=no-demo-456 -d code_challenge=$CHALLENGE"

$CURL -v $FORM -d user=minji -d 'pass=틀린비밀번호' "$OC/auth" \
  >"$OUT/oidc_login_bad.txt" 2>&1
$CURL -v $FORM -d user=minji -d "pass=$PW" "$OC/auth" \
  >"$OUT/oidc_login.txt" 2>&1

# 인가 코드는 Location 헤더의 주소에 실려 온다.
CODE=$(sed -n 's/^< [Ll]ocation:.*[?&]code=\([^&]*\).*/\1/p' \
  "$OUT/oidc_login.txt" | tr -d '\r')
[ -n "$CODE" ] || { echo '인가 코드를 못 받았다' >&2; exit 1; }

# 돌아온 주소를 펼쳐 본다. 코드가 **주소에** 실려 온다는 것이 요점이다.
loc() {
  sed -n 's/^< [Ll]ocation: //p' "$1" | tr -d '\r' | head -1
}
{
  echo '$ showurl "$(돌아온 Location)"'
  python3 tools/showurl.py "$(loc "$OUT/oidc_login.txt")"
  echo
  echo '코드는 브라우저의 주소창을 지나간다. 그래서 짧고, 한 번만 쓴다.'
} >"$OUT/oidc_code_url.txt" 2>&1
{
  echo '$ showurl "$(PKCE 없이 보냈을 때 돌아온 Location)"'
  python3 tools/showurl.py "$(loc "$OUT/oidc_authorize_nopkce.txt")"
  echo
  echo '오류도 앱으로 돌려보낸다. state 를 함께 돌려주는 것이 중요하다 —'
  echo '앱이 "내가 시작한 그 로그인" 임을 알아볼 수 있어야 하기 때문이다.'
} >"$OUT/oidc_err_url.txt" 2>&1

# ── 코드를 토큰으로 ──
TF="-d grant_type=authorization_code -d code=$CODE"
TF="$TF -d redirect_uri=$BACK -d client_id=lunch-web"
TF="$TF -d client_secret=lunch-secret-demo"
$CURL -v $TF -d "code_verifier=$VERIFIER" "$OC/token" \
  -o "$OUT/.tok.json" 2>"$OUT/.tok.hdr"
{ cat "$OUT/.tok.hdr"; echo; cat "$OUT/.tok.json"; } \
  >"$OUT/oidc_token.txt"

# 토큰 세 장이 한 줄에 다 안 들어간다. 가운데를 줄여 응답의 모양만 보인다.
python3 - "$OUT/.tok.json" >"$OUT/oidc_token_short.txt" <<'PYEOF'
import json
import sys

d = json.load(open(sys.argv[1]))
print('$ curl ... /token | python3 -m json.tool')
print('  (토큰은 너무 길어 가운데를 줄였다)')
print('{')
keys = ['access_token', 'id_token', 'refresh_token',
        'token_type', 'expires_in', 'scope']
for n, k in enumerate(keys):
    v = d[k]
    if isinstance(v, str) and len(v) > 64:
        v = '%s…(%d자 줄임)…%s' % (v[:28], len(v) - 56, v[-28:])
    if isinstance(v, str):
        v = '"%s"' % v
    else:
        v = str(v)
    print('  "%s": %s%s' % (k, v, ',' if n < len(keys) - 1 else ''))
print('}')
PYEOF

# 같은 코드를 한 번 더. 코드는 한 번만 쓴다.
$CURL -v $TF -d "code_verifier=$VERIFIER" "$OC/token" \
  >"$OUT/oidc_token_replay.txt" 2>&1

jget() { python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))[sys.argv[2]])' "$1" "$2"; }
IDTOK=$(jget "$OUT/.tok.json" id_token)
ACCTOK=$(jget "$OUT/.tok.json" access_token)
REFTOK=$(jget "$OUT/.tok.json" refresh_token)

# ── verifier 가 틀리면? 새 코드를 하나 더 받아 시험한다 ──
$CURL -v $FORM -d user=minji -d "pass=$PW" "$OC/auth" \
  >"$OUT/.login2.txt" 2>&1
CODE2=$(sed -n 's/^< [Ll]ocation:.*[?&]code=\([^&]*\).*/\1/p' \
  "$OUT/.login2.txt" | tr -d '\r')
$CURL -v -d grant_type=authorization_code -d "code=$CODE2" \
  -d "redirect_uri=$BACK" -d client_id=lunch-web \
  -d client_secret=lunch-secret-demo -d 'code_verifier=엉뚱한-값' \
  "$OC/token" >"$OUT/oidc_token_badverifier.txt" 2>&1

# ── 토큰을 눈으로 본다 ──
echo "$IDTOK" >"$OUT/.idtok.txt"
{
  echo '$ jwtool decode "$ID_TOKEN"'
  bin/jwtool decode -now "$LOOK" "$IDTOK"
} >"$OUT/oidc_decode_id.txt" 2>&1
{
  echo '$ jwtool decode "$ACCESS_TOKEN"'
  bin/jwtool decode -now "$LOOK" "$ACCTOK"
} >"$OUT/oidc_decode_at.txt" 2>&1

# 토큰의 생김새 — 점 두 개로 나뉜 세 조각. 60칸씩 접어서 보인다.
{
  printf '%s\n' '$ echo "$ID_TOKEN" | tr "." "\n" | fold -w 60'
  echo
  printf '%s\n' "$IDTOK" | tr '.' '\n' | (
    n=1
    while IFS= read -r part; do
      case $n in
        1) echo '── 1. 머리 (header) ──' ;;
        2) echo '── 2. 내용 (payload) ──' ;;
        3) echo '── 3. 서명 (signature) ──' ;;
      esac
      printf '%s\n' "$part" | fold -w 60
      echo
      n=$((n + 1))
    done
  )
  echo '앞의 두 조각은 누구나 되돌려 읽는다. 셋째 조각만이 열쇠를 요구한다.'
} >"$OUT/oidc_token_shape.txt" 2>&1
{
  echo '$ jwtool verify -jwks .../certs -iss ... -aud lunch-web "$ID_TOKEN"'
  bin/jwtool verify -jwks "$OC/certs" -iss "$IDP" -aud lunch-web \
    -now "$LOOK" "$IDTOK"
} >"$OUT/oidc_verify_ok.txt" 2>&1
{
  echo '$ jwtool verify ... -now (한 시간 뒤) "$ID_TOKEN"'
  bin/jwtool verify -jwks "$OC/certs" -iss "$IDP" -aud lunch-web \
    -now "$LATER" "$IDTOK" || echo "(끝난 값: $?)"
} >"$OUT/oidc_verify_expired.txt" 2>&1

# 내용을 한 글자 고친 토큰. 서명이 곧바로 어긋난다.
TAMPERED=$(python3 tools/tamper_jwt.py "$IDTOK")
{
  echo '$ # 내용의 preferred_username 을 admin.lee 로 고쳐 봤다'
  echo '$ jwtool verify ... "$TAMPERED"'
  bin/jwtool verify -jwks "$OC/certs" -iss "$IDP" -aud lunch-web \
    -now "$LOOK" "$TAMPERED" || echo "(끝난 값: $?)"
  echo
  echo '$ jwtool decode "$TAMPERED"   # 읽히기는 읽힌다'
  bin/jwtool decode -now "$LOOK" "$TAMPERED" | sed -n '/^내용/,/^$/p'
} >"$OUT/oidc_verify_tampered.txt" 2>&1

# alg=none — 서명을 아예 뗀 토큰.
NONE=$(python3 tools/tamper_jwt.py --alg-none "$IDTOK")
{
  echo '$ jwtool verify ... "$ALG_NONE_TOKEN"'
  bin/jwtool verify -jwks "$OC/certs" -iss "$IDP" -aud lunch-web \
    -now "$LOOK" "$NONE" || echo "(끝난 값: $?)"
} >"$OUT/oidc_verify_algnone.txt" 2>&1

# ── userinfo ──
$CURL -v -H "Authorization: Bearer $ACCTOK" "$OC/userinfo" \
  >"$OUT/oidc_userinfo.txt" 2>&1
$CURL -v -H "Authorization: Bearer $IDTOK" "$OC/userinfo" \
  >"$OUT/oidc_userinfo_idtoken.txt" 2>&1
$CURL -v "$OC/userinfo" >"$OUT/oidc_userinfo_notoken.txt" 2>&1

# ── 갱신과 회전 ──
$CURL -v -d grant_type=refresh_token -d "refresh_token=$REFTOK" \
  -d client_id=lunch-web -d client_secret=lunch-secret-demo \
  "$OC/token" >"$OUT/oidc_refresh.txt" 2>&1
$CURL -v -d grant_type=refresh_token -d "refresh_token=$REFTOK" \
  -d client_id=lunch-web -d client_secret=lunch-secret-demo \
  "$OC/token" >"$OUT/oidc_refresh_replay.txt" 2>&1

# ── 앱 쪽에서 본 같은 흐름 ──
# 비밀은 환경 변수로 준다. 명령줄에 적으면 ps 에 그대로 뜬다(2부).
LUNCH_CLIENT_SECRET=lunch-secret-demo
export LUNCH_CLIENT_SECRET
start oidc/miniapp "$OUT/oidc_app.log" -addr ":$PA" \
  -self "http://localhost:$PA" -issuer "$IDP" -fixed-now "$FIXED"
wait_up "http://localhost:$PA/"

AJAR=$OUT/.appjar.txt
rm -f "$AJAR"
$CURL -v -L -c "$AJAR" -b "$AJAR" "http://localhost:$PA/login" \
  >"$OUT/oidc_app_login.txt" 2>&1
# 로그인 화면의 숨은 칸을 그대로 되돌려 보낸다 — 브라우저가 하는 일이다.
APPQ=$(sed -n 's/.*<input type="hidden" name="\([^"]*\)" value="\([^"]*\)">.*/-d \1=\2/p' \
  "$OUT/oidc_app_login.txt" | tr '\n' ' ')
# shellcheck disable=SC2086
$CURL -v -L -c "$AJAR" -b "$AJAR" $APPQ -d user=minji -d "pass=$PW" \
  "$OC/auth" >"$OUT/oidc_app_callback.txt" 2>&1
{
  echo '$ showurl "$(앱의 /login 이 보낸 곳)"'
  python3 tools/showurl.py "$(loc "$OUT/oidc_app_login.txt")"
  echo
  echo '2장에서 손으로 만든 그 주소다. 이번에는 앱이 만들었다.'
} >"$OUT/oidc_app_url.txt" 2>&1
$CURL -v -b "$AJAR" "http://localhost:$PA/me" >"$OUT/oidc_app_me.txt" 2>&1
$CURL -v -b "$AJAR" "http://localhost:$PA/admin" \
  >"$OUT/oidc_app_admin_denied.txt" 2>&1
$CURL -v -L -b "$AJAR" -c "$AJAR" \
  -X POST "http://localhost:$PA/logout" \
  >"$OUT/oidc_app_logout.txt" 2>&1
$CURL -v -b "$AJAR" "http://localhost:$PA/me" \
  >"$OUT/oidc_app_me_after.txt" 2>&1
{
  echo '$ showurl "$(로그아웃 단추가 보낸 곳)"'
  python3 tools/showurl.py "$(loc "$OUT/oidc_app_logout.txt")"
  echo
  echo 'id_token_hint 는 "누구의 세션을 끊는지" 를 알려 준다.'
  echo '이게 없으면 IdP 가 사용자에게 "정말 로그아웃할까요" 를 물어야 한다.'
} >"$OUT/oidc_logout_url.txt" 2>&1

# 관리자는 같은 화면을 볼 수 있다. 갈리는 것은 groups 클레임 하나다.
BJAR=$OUT/.adminjar.txt
rm -f "$BJAR"
$CURL -sS -4 -L -c "$BJAR" -b "$BJAR" "http://localhost:$PA/login" \
  >"$OUT/.adminlogin.txt" 2>&1
ADMINQ=$(sed -n 's/.*<input type="hidden" name="\([^"]*\)" value="\([^"]*\)">.*/-d \1=\2/p' \
  "$OUT/.adminlogin.txt" | tr '\n' ' ')
# shellcheck disable=SC2086
$CURL -sS -4 -L -c "$BJAR" -b "$BJAR" $ADMINQ -d user=admin.lee \
  -d "pass=$PW" "$OC/auth" >/dev/null 2>&1
$CURL -v -b "$BJAR" "http://localhost:$PA/admin" \
  >"$OUT/oidc_app_admin_ok.txt" 2>&1

stop_all

# 가짜 AD 의 로그에서 '끊김' 줄은 뺀다.
#
# 연결이 닫히는 것은 서버의 다른 고루틴이 알아채는 일이라, 두 연결이
# 거의 동시에 닫히면 두 줄의 앞뒤가 그때그때 바뀐다. 두 판 다 맞는
# 출력이지만 md5 가 달라져 재현 검사를 통과할 수 없다. 뺀 사실을
# 파일 안에 적어 둔다 — 원래 모양은 3부의 ad_fakead.log 에 그대로 있다.
{
  echo '# (연결이 끊긴 줄은 두 연결이 동시에 닫힐 때 순서가 바뀌어 뺐다.'
  echo '#  원래 모양은 3부의 로그에 그대로 있다.)'
  grep -v '끊김' "$OUT/.fakead.raw"
} >"$OUT/oidc_fakead.log"

rm -f "$OUT/.tok.json" "$OUT/.tok.hdr" "$OUT/.login2.txt" \
  "$OUT/.idtok.txt" "$OUT/.adminlogin.txt" "$OUT/.fakead.raw" \
  "$AJAR" "$BJAR"

# ── 8. 쿠버네티스 (2부) ───────────────────────────────────────────
#
# 클러스터는 없다. 그래서 여기서 뜨는 것은 전부 **읽고 검증한** 결과다.
#   kubectl kustomize   조각을 합친 최종 YAML (오프라인)
#   kubeconform         쿠버네티스 JSON 스키마와 맞춰 보기
#   tools/kexplain.py   필드 설명을 스키마에서 직접 읽기
#
# kubectl explain 과 kubectl create --dry-run=client 는 **서버를 부른다**.
# 클러스터 없이는 못 쓴다 — 실제로 해 보고 확인했다(아래 캡처).
say '8. k8s 매니페스트 (kustomize · kubeconform)'
K8S_OK=1
for t in bin/kubectl bin/kubeconform; do
  [ -x "$t" ] || K8S_OK=0
done
[ -f bin/schemas/deployment-apps-v1.json ] || K8S_OK=0

if [ "$K8S_OK" = 0 ]; then
  echo '  k8s 도구가 없다 — sh tools/fetch_k8s_tools.sh 를 먼저 돌릴 것' >&2
  exit 1
fi

KC=bin/kubeconform
KVER=1.37.0
conform() {
  $KC -strict -summary -kubernetes-version "$KVER" -cache bin/.kccache -
}

{
  echo '$ bin/kubectl version --client'
  bin/kubectl version --client
  echo
  echo '$ bin/kubeconform -v'
  bin/kubeconform -v
  echo
  echo '스키마: kubernetes-json-schema 의 master-standalone-strict'
  ls bin/schemas | sed 's/^/  /'
} >"$OUT/k8s_tools.txt" 2>&1

# 클러스터가 없으면 안 되는 것 둘. 말로 하지 않고 직접 해 본다.
{
  echo '$ bin/kubectl explain deployment.spec.replicas'
  bin/kubectl explain deployment.spec.replicas 2>&1 | tail -1
  echo
  echo '$ bin/kubectl create --dry-run=client -f k8s/base/namespace.yaml'
  echo '    2>&1 | fold -s -w 96      # 한 줄이 길어서 접었다'
  bin/kubectl create --dry-run=client -f k8s/base/namespace.yaml 2>&1 \
    | tail -1 | fold -s -w 96
  echo
  echo '둘 다 클러스터에 물어본다. 그래서 이 덱에서는 못 쓴다 —'
  echo 'kubectl kustomize 와 kubeconform 은 오프라인으로 된다.'
} >"$OUT/k8s_needs_server.txt" 2>&1

# 필드 설명 — 스키마에서 직접 읽는다.
for spec in "deployment " "deployment spec.replicas" \
            "deployment spec.selector" "deployment spec.strategy" \
            "service spec.type" "service spec.ports" \
            "ingress spec.rules" "pod spec.containers"; do
  set -- $spec
  kind=$1
  field=${2:-}
  name=$(echo "k8s_explain_${kind}_${field}" | tr '.' '_' | sed 's/_$//')
  {
    echo "\$ kexplain.py $kind $field"
    python3 tools/kexplain.py "$kind" "$field"
  } >"$OUT/$name.txt" 2>&1
done

# 조각을 합친 최종 YAML.
for o in dev prod; do
  {
    echo "\$ bin/kubectl kustomize k8s/overlays/$o"
    bin/kubectl kustomize "k8s/overlays/$o"
  } >"$OUT/k8s_kustomize_$o.txt" 2>&1
done

# dev 와 prod 는 무엇이 다른가 — 합친 결과끼리 견준다.
{
  echo '$ diff <(kubectl kustomize overlays/dev) \'
  echo '       <(kubectl kustomize overlays/prod)'
  bin/kubectl kustomize k8s/overlays/dev >"$OUT/.dev.yaml"
  bin/kubectl kustomize k8s/overlays/prod >"$OUT/.prod.yaml"
  diff "$OUT/.dev.yaml" "$OUT/.prod.yaml" || true
  rm -f "$OUT/.dev.yaml" "$OUT/.prod.yaml"
} >"$OUT/k8s_diff.txt" 2>&1

# 검증.
{
  echo '$ sh k8s/validate.sh'
  sh k8s/validate.sh
} >"$OUT/k8s_validate.txt" 2>&1

# 일부러 틀린 매니페스트 — 검사기가 무엇을 잡고 무엇을 못 잡는가.
{
  echo '$ kubeconform -strict -output json k8s/examples/typo.yaml'
  $KC -strict -output json -kubernetes-version "$KVER" \
    -cache bin/.kccache k8s/examples/typo.yaml || true
} >"$OUT/k8s_invalid.txt" 2>&1
# -strict 가 있고 없고의 차이를 또렷하게 보이려고, **오타 하나만** 있는
# 매니페스트를 따로 만들어 두 번 검사한다. typo.yaml 은 타입 오류도 함께
# 들어 있어서, 그것만으로는 "그냥 넘어간다" 가 눈에 안 보인다.
ONLYTYPO=$OUT/.onlytypo.yaml
cat >"$ONLYTYPO" <<'YEOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lunch-web
spec:
  replica: 3          # replicas 를 replica 로 적었다. 이것 하나뿐이다.
  selector:
    matchLabels: {app: lunch-web}
  template:
    metadata:
      labels: {app: lunch-web}
    spec:
      containers:
        - name: web
          image: registry.campus.example/lunch/lunch-web:1.4.2
YEOF
{
  echo '$ cat 오타-하나만.yaml'
  sed -n '5,7p' "$ONLYTYPO"
  echo
  echo '$ kubeconform 오타-하나만.yaml            # -strict 없이'
  $KC -summary -kubernetes-version "$KVER" \
    -cache bin/.kccache "$ONLYTYPO" 2>&1 | sed "s|$ONLYTYPO|오타-하나만.yaml|"
  echo
  echo '$ kubeconform -strict 오타-하나만.yaml'
  $KC -strict -summary -kubernetes-version "$KVER" \
    -cache bin/.kccache "$ONLYTYPO" 2>&1 \
    | sed "s|$ONLYTYPO|오타-하나만.yaml|" | fold -s -w 96
} >"$OUT/k8s_invalid_nostrict.txt" 2>&1
rm -f "$ONLYTYPO"

# YAML 자체의 함정 — 따옴표 없는 값이 무엇이 되는가.
#
# 짐작으로 적지 않는다. 진짜 파서(kubectl 안의 것)에 넣었다가
# 도로 꺼내 **무엇으로 바뀌어 나오는지** 본다.
TRAP=$OUT/.trap
mkdir -p "$TRAP"
cat >"$TRAP/cm.yaml" <<'YEOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: traps
data:
  enabled: yes
  country: NO
  version: 1.20
  build: 010
  time: 12:30
YEOF
cat >"$TRAP/kustomization.yaml" <<'YEOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - cm.yaml
YEOF
{
  echo '$ cat cm.yaml        # 따옴표를 하나도 안 씌우고 적었다'
  sed -n '5,11p' "$TRAP/cm.yaml"
  echo
  echo '$ bin/kubectl kustomize .    # 파서에 넣었다가 도로 꺼낸다'
  bin/kubectl kustomize "$TRAP" | sed -n '/^data:/,/^kind:/p' \
    | sed '$d'
} >"$OUT/k8s_yaml_traps.txt" 2>&1
rm -rf "$TRAP"

# ── 9. 정리 ───────────────────────────────────────────────────────
say '9. 매번 달라지는 값 고정 (tools/scrub.py)'
python3 tools/scrub.py "$OUT"/web*.txt "$OUT"/tool_*.txt \
  "$OUT"/ad_*.txt "$OUT"/ad_fakead.log "$OUT"/oidc_*.txt "$OUT"/oidc_*.log \
  "$OUT"/k8s_*.txt

echo '캡처 완료 — out/ 아래'
ls -1 "$OUT" | sed 's/^/  /'
