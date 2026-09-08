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
           ldap/fakead/cmd/fakead ldap/ldapcli; do
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
require_free $P1 $P2 $P3 $P4 $P4H $PL $PLS
build_all
$GO test ./... >"$OUT/web_test.txt" 2>&1 || true
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

# ── 6. 정리 ───────────────────────────────────────────────────────
say '7. 매번 달라지는 값 고정 (tools/scrub.py)'
python3 tools/scrub.py "$OUT"/web*.txt "$OUT"/tool_*.txt \
  "$OUT"/ad_*.txt "$OUT"/ad_fakead.log

echo '캡처 완료 — out/ 아래'
ls -1 "$OUT" | sed 's/^/  /'
