#!/bin/sh
# authz_lab.sh — AD 그룹 한 줄이 앱의 권한이 되기까지.
#
# 9부의 실험. 같은 사람의 토큰을 **그룹에 넣기 전과 후**로 두 번 떠서
# 무엇이 달라지는지 본다. 그리고 그룹을 역할로 옮기면 토큰이
# 어떻게 바뀌는지도.
#
# Keycloak 과 가짜 AD 가 이미 떠 있어야 한다.
set -eu
cd "$(dirname "$0")/.."

KC=${KC_URL:-http://localhost:8080}
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

# tokens <아이디> — 로그인해서 ID 토큰과 액세스 토큰을 둘 다 받는다.
#
# 둘을 다 받는 이유가 이 부의 배울 거리 하나다 — 역할은 기본으로
# **액세스 토큰**에만 실린다. ID 토큰만 보다가 "역할이 없다" 고
# 헤매는 일이 흔하다.
tokens() {
  jar=$OUT/.authz_jar.txt
  rm -f "$jar"
  q="response_type=code&client_id=$CLIENT"
  q="$q&redirect_uri=http%3A%2F%2Flocalhost%3A9001%2Fcallback"
  q="$q&scope=openid&state=az&nonce=az"
  q="$q&code_challenge=$CHALLENGE&code_challenge_method=S256"
  $CURL -c "$jar" -b "$jar" "$OC/auth?$q" >"$OUT/.authz_form.html"
  act=$(sed -n 's/.*action="\([^"]*\)".*/\1/p' "$OUT/.authz_form.html" \
    | head -1 | sed 's/&amp;/\&/g')
  $CURL -v -c "$jar" -b "$jar" -X POST "$act" \
    -d "username=$1" -d "password=Passw0rd!-demo" \
    >"$OUT/.authz_post.txt" 2>&1
  code=$(sed -n 's/^< [Ll]ocation:.*[?&]code=\([^&]*\).*/\1/p' \
    "$OUT/.authz_post.txt" | tr -d '\r' | head -1)
  [ -n "$code" ] || { echo "로그인 실패: $1" >&2; return 1; }
  $CURL -X POST "$OC/token" \
    -d grant_type=authorization_code -d "code=$code" \
    -d redirect_uri=http://localhost:9001/callback \
    -d "client_id=$CLIENT" -d "client_secret=$SECRET" \
    -d "code_verifier=$VERIFIER" \
    | python3 -c 'import json,sys
d = json.load(sys.stdin)
print(d["id_token"])
print(d["access_token"])'
  rm -f "$jar" "$OUT/.authz_form.html" "$OUT/.authz_post.txt"
}

# 토큰의 크기와 권한 관련 칸만 뽑아 보여 준다.
show() {
  python3 - "$1" "$2" <<'PY'
import base64
import json
import sys

label, tok = sys.argv[1], sys.argv[2]
head, body, sig = tok.split('.')
raw = base64.urlsafe_b64decode(body + '=' * (-len(body) % 4))
c = json.loads(raw)
print('  [%s]' % label)
print('  preferred_username %s' % c.get('preferred_username'))
print('  groups             %s'
      % json.dumps(c.get('groups', []), ensure_ascii=False))
ra = c.get('realm_access', {}).get('roles', [])
print('  realm_access.roles %s' % json.dumps(sorted(ra)))
print('  토큰 길이           %d글자 (내용 %d바이트)'
      % (len(tok), len(raw)))
PY
}

# ── 실험 1. 같은 사람, 그룹에 넣기 전과 후 ─────────────────────────
#
# yuna.choi 는 campus-all 에만 들어 있다(3부의 campus.ldif).
# 그 사람을 lunch-users 에 넣으면 토큰이 어떻게 달라지는가.
#
# AD 를 고칠 수는 없으니(READ_ONLY) Keycloak 쪽 그룹에 넣는다.
# 진짜 운영에서는 AD 에서 넣고 동기화를 기다린다 — 결과는 같다.
uid() {
  api GET "/$REALM/users?username=$1&exact=true" \
    | python3 -c 'import json,sys
rows = json.load(sys.stdin)
print(rows[0]["id"] if rows else "")'
}
gid() {
  api GET "/$REALM/groups?search=$1" | python3 -c 'import json,sys
rows = json.load(sys.stdin)
want = sys.argv[1]
print(next((g["id"] for g in rows if g["name"] == want), ""))' "$1"
}

YU=$(uid yuna.choi)
GL=$(gid lunch-users)
[ -n "$YU" ] && [ -n "$GL" ] || {
  echo '사람이나 그룹을 못 찾았다' >&2
  exit 1
}

# 혹시 들어 있으면 빼 두고 시작한다.
api DELETE "/$REALM/users/$YU/groups/$GL" >/dev/null 2>&1 || true

{
  echo '$ 유나의 토큰 — lunch-users 에 들어가기 **전**'
  tokens yuna.choi >"$OUT/.az.txt"
  show "ID 토큰" "$(sed -n 1p "$OUT/.az.txt")"
  echo
  echo '$ 유나를 lunch-users 그룹에 넣는다'
  api PUT "/$REALM/users/$YU/groups/$GL" >/dev/null
  echo '  (넣었다)'
  echo
  echo '$ 다시 로그인해서 받은 토큰 — **후**'
  tokens yuna.choi >"$OUT/.az.txt"
  show "ID 토큰" "$(sed -n 1p "$OUT/.az.txt")"
  echo
  echo '토큰은 발급 순간의 사진이다. 그룹을 바꿔도'
  echo '이미 나간 토큰은 안 바뀐다 — 다시 로그인해야 한다(4부 8장).'
} >"$OUT/kc_az_before_after.txt" 2>&1

# ── 실험 2. 그룹을 역할로 옮긴다 ───────────────────────────────────
#
# 앱이 "lunch-admins 그룹인가" 를 묻는 대신 "lunch-admin 역할인가" 를
# 묻게 하면, 나중에 그룹 이름이 바뀌어도 앱을 안 고친다.
cat >"$OUT/.role.json" <<'JEOF'
{"name": "lunch-admin", "description": "학식 메뉴를 고칠 수 있다"}
JEOF
api POST "/$REALM/roles" "$OUT/.role.json" >/dev/null 2>&1 || true
ROLE=$(api GET "/$REALM/roles/lunch-admin")

GA=$(gid lunch-admins)
printf '[%s]' "$ROLE" >"$OUT/.rolemap.json"

{
  echo '$ 역할을 하나 만든다: lunch-admin'
  echo "$ROLE" | python3 -c 'import json,sys
d = json.load(sys.stdin)
for k in ["name", "description", "composite", "clientRole"]:
    print("  %-12s %s" % (k, json.dumps(d.get(k), ensure_ascii=False)))'
  echo
  echo '$ 그룹 lunch-admins 에 그 역할을 붙인다'
  api POST "/$REALM/groups/$GA/role-mappings/realm" \
    "$OUT/.rolemap.json" >/dev/null
  echo '  (붙였다 — 이제 그 그룹의 사람은 자동으로 그 역할을 갖는다)'
  echo
  echo '$ 소희 — ID 토큰과 액세스 토큰을 나란히'
  tokens admin.lee >"$OUT/.az.txt"
  show "ID 토큰" "$(sed -n 1p "$OUT/.az.txt")"
  echo
  show "액세스 토큰" "$(sed -n 2p "$OUT/.az.txt")"
  echo
  echo '$ 민지 — 액세스 토큰'
  tokens minji >"$OUT/.az.txt"
  show "액세스 토큰" "$(sed -n 2p "$OUT/.az.txt")"
  echo
  echo '**역할은 ID 토큰에 없다.** 기본 client scope 인 roles 가'
  echo '액세스 토큰에만 싣기 때문이다. ID 토큰에도 넣으려면'
  echo '그 매퍼의 "Add to ID token" 을 켜야 한다.'
} >"$OUT/kc_az_roles.txt" 2>&1

rm -f "$OUT/.role.json" "$OUT/.rolemap.json" "$OUT/.az.txt"
echo '권한 실험 완료 — out/kc_az_*.txt'
