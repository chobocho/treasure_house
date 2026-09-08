#!/bin/sh
# e2e_login.sh — 진짜 Keycloak 으로 로그인 전 과정을 훑는다.
#
# 4부에서 miniidp 를 상대로 한 그 흐름을, 이번에는 **진짜 제품**을
# 상대로 똑같이 한다. 주소도 칸 이름도 같다 — 그게 표준의 값어치다.
#
# 브라우저가 하는 일을 curl 이 대신한다. 쿠키 항아리를 들고 다니고,
# 리다이렉트를 따라가고, 폼을 채워 보낸다.
set -eu
cd "$(dirname "$0")/.."

KC=${KC_URL:-http://localhost:8080}
REALM=campus
CLIENT=lunch-web
SECRET=lunch-secret-demo
BACK=http://localhost:9001/callback
USER=${KC_USER:-minji}
PASS=${KC_PASS:-Passw0rd!-demo}
OUT=out
mkdir -p "$OUT"

OC=$KC/realms/$REALM/protocol/openid-connect
JAR=$OUT/.kc_jar.txt
rm -f "$JAR"
CURL="curl -sS -4"

# ── 1. 안내문 ──
# Keycloak 은 안내문을 한 줄로 준다. 6,500칸이라 그대로는 못 읽는다.
{
  echo "\$ curl $KC/realms/$REALM/.well-known/openid-configuration"
  echo '    | python3 -m json.tool'
  $CURL "$KC/realms/$REALM/.well-known/openid-configuration" \
    | python3 -c 'import json,sys
d = json.load(sys.stdin)
# 이 덱이 4부에서 다룬 칸들만 먼저, 나머지는 개수만 센다.
keys = ["issuer", "authorization_endpoint", "token_endpoint",
        "jwks_uri", "userinfo_endpoint", "end_session_endpoint",
        "grant_types_supported", "response_types_supported",
        "id_token_signing_alg_values_supported",
        "code_challenge_methods_supported",
        "token_endpoint_auth_methods_supported"]
for k in keys:
    v = d.get(k)
    if isinstance(v, list):
        print("  %s" % k)
        line = "   "
        for x in v:
            if len(line) + len(x) > 68:
                print(line)
                line = "   "
            line += " " + str(x)
        print(line)
        continue
    print("  %-24s %s" % (k, v))
print()
print("  (칸이 모두 %d개다 — 우리 miniidp 는 11개였다)" % len(d))'
} >"$OUT/kc_e2e_01_discovery.txt" 2>&1

# ── 2. PKCE ──
VERIFIER=lunch-demo-verifier-0123456789-abcdefghijklmnop
CHALLENGE=$(printf %s "$VERIFIER" | openssl dgst -sha256 -binary \
  | openssl base64 -A | tr '+/' '-_' | tr -d '=')

AQ="response_type=code&client_id=$CLIENT"
AQ="$AQ&redirect_uri=http%3A%2F%2Flocalhost%3A9001%2Fcallback"
AQ="$AQ&scope=openid+profile+email&state=st-demo-123&nonce=no-demo-456"
AQ="$AQ&code_challenge=$CHALLENGE&code_challenge_method=S256"

{
  echo '$ showurl "$AUTH_URL"'
  python3 tools/showurl.py "$OC/auth?$AQ"
} >"$OUT/kc_e2e_02_authorize_url.txt" 2>&1

# ── 3. 로그인 화면 ──
#
# Keycloak 이 내려 주는 폼에는 **한 번만 쓰는 주소**가 들어 있다.
# 그 주소에 세션 코드가 박혀 있어서, 폼을 그대로 다시 쓸 수 없다.
$CURL -c "$JAR" -b "$JAR" "$OC/auth?$AQ" >"$OUT/.kc_login.html" 2>&1
ACTION=$(sed -n 's/.*action="\([^"]*\)".*/\1/p' "$OUT/.kc_login.html" \
  | head -1 | sed 's/&amp;/\&/g')
[ -n "$ACTION" ] || { echo '로그인 폼을 못 찾았다' >&2; exit 1; }
{
  echo '$ curl .../auth?... | grep -i "form action"'
  echo
  echo '폼이 가리키는 곳 (세션 코드가 박혀 있다):'
  python3 tools/showurl.py "$ACTION"
} >"$OUT/kc_e2e_03_loginform.txt" 2>&1

# ── 4. 아이디와 비밀번호를 낸다 ──
#
# 여기서 Keycloak 이 AD 에 묻는다. 그 흔적은 가짜 AD 의 로그에 남는다.
$CURL -v -c "$JAR" -b "$JAR" -X POST "$ACTION" \
  -d "username=$USER" -d "password=$PASS" \
  >"$OUT/kc_e2e_04_login_post.txt" 2>&1

CODE=$(sed -n 's/^< [Ll]ocation:.*[?&]code=\([^&]*\).*/\1/p' \
  "$OUT/kc_e2e_04_login_post.txt" | tr -d '\r' | head -1)
[ -n "$CODE" ] || { echo '인가 코드를 못 받았다' >&2; exit 1; }

LOC=$(sed -n 's/^< [Ll]ocation: //p' "$OUT/kc_e2e_04_login_post.txt" \
  | tr -d '\r' | head -1)
{
  echo '$ showurl "$(돌아온 Location)"'
  python3 tools/showurl.py "$LOC"
} >"$OUT/kc_e2e_05_code_url.txt" 2>&1

# ── 5. 코드를 토큰으로 ──
$CURL -v -X POST "$OC/token" \
  -d grant_type=authorization_code -d "code=$CODE" \
  -d "redirect_uri=$BACK" -d "client_id=$CLIENT" \
  -d "client_secret=$SECRET" -d "code_verifier=$VERIFIER" \
  -o "$OUT/.kc_tok.json" 2>"$OUT/.kc_tok.hdr"
{ cat "$OUT/.kc_tok.hdr"; echo; cat "$OUT/.kc_tok.json"; } \
  >"$OUT/kc_e2e_06_token.txt"

jget() {
  python3 -c 'import json,sys
print(json.load(open(sys.argv[1]))[sys.argv[2]])' "$1" "$2"
}
IDTOK=$(jget "$OUT/.kc_tok.json" id_token)
ACCTOK=$(jget "$OUT/.kc_tok.json" access_token)

# ── 6. 우리 도구로 진짜 토큰을 뜯어본다 ──
{
  echo '$ jwtool decode "$ID_TOKEN"'
  bin/jwtool decode "$IDTOK"
} >"$OUT/kc_e2e_07_decode.txt" 2>&1
{
  echo '$ jwtool verify -jwks .../certs -iss ... -aud lunch-web'
  bin/jwtool verify -jwks "$OC/certs" \
    -iss "$KC/realms/$REALM" -aud "$CLIENT" "$IDTOK"
} >"$OUT/kc_e2e_08_verify.txt" 2>&1

# ── 7. userinfo ──
$CURL -v -H "Authorization: Bearer $ACCTOK" "$OC/userinfo" \
  >"$OUT/kc_e2e_09_userinfo.txt" 2>&1

# ── 8. 로그아웃 ──
HOME_ENC=http%3A%2F%2Flocalhost%3A9001%2F
LQ="id_token_hint=$IDTOK&post_logout_redirect_uri=$HOME_ENC"
$CURL -v -c "$JAR" -b "$JAR" "$OC/logout?$LQ" \
  >"$OUT/kc_e2e_10_logout.txt" 2>&1

rm -f "$OUT/.kc_login.html" "$OUT/.kc_tok.json" \
  "$OUT/.kc_tok.hdr" "$JAR"
echo '전 과정 통과 — out/kc_e2e_*.txt'
