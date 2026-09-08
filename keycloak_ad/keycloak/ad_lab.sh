#!/bin/sh
# ad_lab.sh — AD 연동을 건드려 보고 그때마다 무엇이 달라지는지 남긴다.
#
# 7부는 설정 칸 이야기다. 칸을 설명하는 가장 좋은 방법은 **바꿔 보고
# 로그를 보는 것**이라, 여기서 그 실험들을 한 번에 돌린다.
#
# 앞의 것이 뒤에 영향을 준다 — 순서가 있다.
# Keycloak 은 이미 떠 있어야 한다.
set -eu
cd "$(dirname "$0")/.."

KC=${KC_URL:-http://localhost:8080}
REALM=campus
ADMIN=${KC_BOOTSTRAP_ADMIN_USERNAME:-admin}
ADMIN_PW=${KC_BOOTSTRAP_ADMIN_PASSWORD:-admin-demo-1234}
OUT=out
AD_LOG=$OUT/kc_fakead.log
CURL="curl -sS -4"

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

PROVIDER=org.keycloak.storage.UserStorageProvider
LDAP_ID=$(api GET "/$REALM/components?type=$PROVIDER" \
  | python3 -c 'import json,sys
rows = json.load(sys.stdin)
print(next((r["id"] for r in rows if r["name"] == "ad-campus"), ""))')
[ -n "$LDAP_ID" ] || { echo 'AD 연동을 못 찾았다' >&2; exit 1; }

# mark <파일> — 지금까지의 AD 로그 길이를 재 둔다.
# 그 뒤 벌어진 일만 잘라 내려는 것이다.
MARK=0
mark() { MARK=$(wc -l <"$AD_LOG"); }
since() { tail -n +$((MARK + 1)) "$AD_LOG"; }

# login <아이디> <비밀번호> — 로그인 한 번을 끝까지 해 본다.
# 결과(성공이면 코드, 실패면 화면의 말)를 표준 출력으로.
login() {
  jar=$OUT/.lab_jar.txt
  rm -f "$jar"
  oc=$KC/realms/$REALM/protocol/openid-connect
  q="response_type=code&client_id=lunch-web"
  q="$q&redirect_uri=http%3A%2F%2Flocalhost%3A9001%2Fcallback"
  q="$q&scope=openid&state=lab&nonce=lab"
  q="$q&code_challenge=$CHALLENGE&code_challenge_method=S256"
  $CURL -c "$jar" -b "$jar" "$oc/auth?$q" >"$OUT/.lab_form.html"
  form=$OUT/.lab_form.html
  action=$(sed -n 's/.*action="\([^"]*\)".*/\1/p' "$form" \
    | head -1 | sed 's/&amp;/\&/g')
  $CURL -v -c "$jar" -b "$jar" -X POST "$action" \
    -d "username=$1" -d "password=$2" >"$OUT/.lab_post.txt" 2>&1
  if grep -q '^< [Ll]ocation:.*code=' "$OUT/.lab_post.txt"; then
    echo '  → 성공: 인가 코드를 받았다'
  else
    echo '  → 실패. 화면에 뜬 말:'
    # 오류 문구는 여러 줄에 걸쳐 있어 한 줄짜리 sed 로는 못 잡는다.
    python3 - "$OUT/.lab_post.txt" <<'PY'
import re
import sys

html = open(sys.argv[1], encoding='utf-8', errors='replace').read()
m = re.search(r'kc-feedback-text[^>]*>\s*(.*?)\s*</span>', html, re.S)
print('    ' + (m.group(1) if m else '(문구를 못 찾았다)'))
PY
  fi
  rm -f "$jar" "$OUT/.lab_form.html" "$OUT/.lab_post.txt"
}

cfgset() {
  api GET "/$REALM/components/$LDAP_ID" >"$OUT/.lab_cfg.json"
  python3 - "$OUT/.lab_cfg.json" "$1" "$2" <<'PY'
import json
import sys

path, key, val = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(path, encoding='utf-8'))
# 키를 빼는 것만으로는 안 지워진다 — PUT 이 합치기 때문이다.
# 빈 값으로 덮어써야 실제로 없어진다. 한 번 이것 때문에 앞 실험의
# 필터가 뒤 실험까지 따라가 답을 바꿔 놓았다.
d['config'][key] = [val]
json.dump(d, open(path, 'w', encoding='utf-8'), ensure_ascii=False)
PY
  api PUT "/$REALM/components/$LDAP_ID" "$OUT/.lab_cfg.json" >/dev/null
  rm -f "$OUT/.lab_cfg.json"
}

# reset — 실험을 깨끗한 자리에서 시작한다.
#
# 앞 실험이 남긴 것이 뒤 실험의 답을 바꾼다. 실제로 한 번 그렇게 돼서
# "sAMAccountName 으로는 못 들어간다" 고 적어 둔 화면에 성공이 찍혔다.
# 그래서 실험마다 설정을 되돌리고, **가져온 사본을 지운다**.
# 사본을 안 지우면 옛 아이디로 만들어진 사람이 그대로 남는다.
reset() {
  cfgset customUserSearchFilter ''
  cfgset usernameLDAPAttribute sAMAccountName
  api POST "/$REALM/user-storage/$LDAP_ID/remove-imported-users" \
    >/dev/null
}

users() {
  api GET "/$REALM/users?briefRepresentation=true&max=50" \
    | python3 -c 'import json,sys
rows = json.load(sys.stdin)
print("    " + " ".join(sorted(r["username"] for r in rows)))
print("    모두 %d명" % len(rows))'
}

groups_of() {
  api GET "/$REALM/users?username=$1&exact=true" \
    | python3 -c 'import json,sys
rows = json.load(sys.stdin)
print(rows[0]["id"] if rows else "")'
}

VERIFIER=lunch-demo-verifier-0123456789-abcdefghijklmnop
CHALLENGE=$(printf %s "$VERIFIER" | openssl dgst -sha256 -binary \
  | openssl base64 -A | tr '+/' '-_' | tr -d '=')
# ── 실험 1. 로그인 세 가지 ──────────────────────────────────────────
#
# 맞는 비밀번호 · 틀린 비밀번호 · 꺼진 계정.
# 셋이 AD 에게는 어떻게 보이고, 사용자에게는 어떻게 보이는가.
reset
{
  echo '$ 로그인: minji / 맞는 비밀번호'
  mark
  login minji 'Passw0rd!-demo'
  echo
  echo '  가짜 AD 가 받은 것:'
  since | sed 's/^/    /'
} >"$OUT/kc_ad_login_ok.txt" 2>&1

{
  echo '$ 로그인: minji / 틀린 비밀번호'
  mark
  login minji '틀린비밀번호'
  echo
  echo '  가짜 AD 가 받은 것:'
  since | sed 's/^/    /'
} >"$OUT/kc_ad_login_badpw.txt" 2>&1

{
  echo '$ 로그인: jisoo.oh (AD 에서 꺼진 계정)'
  mark
  login jisoo.oh 'Passw0rd!-demo'
  echo
  echo '  가짜 AD 가 받은 것:'
  since | sed 's/^/    /'
} >"$OUT/kc_ad_login_disabled.txt" 2>&1

{
  echo '$ 로그인: 없는 사람'
  mark
  login 없는사람 'Passw0rd!-demo'
  echo
  echo '  가짜 AD 가 받은 것:'
  since | sed 's/^/    /'
} >"$OUT/kc_ad_login_nouser.txt" 2>&1

# ── 실험 2. 사람마다 다른 그룹 ──────────────────────────────────────
reset
{
  echo '$ 두 사람의 그룹을 견준다 (AD 의 member 속성에서 온다)'
  for u in minji admin.lee; do
    id=$(groups_of "$u")
    printf '  %-10s ' "$u"
    api GET "/$REALM/users/$id/groups" \
      | python3 -c 'import json,sys
print(", ".join(g["name"] for g in json.load(sys.stdin)))'
  done
  echo
  echo '  9부에서 이 차이가 "메뉴를 고칠 수 있는가" 로 이어진다.'
} >"$OUT/kc_ad_groups.txt" 2>&1

# ── 실험 3. 서비스 계정을 사람 목록에서 뺀다 ────────────────────────
reset
api POST "/$REALM/user-storage/$LDAP_ID/sync?action=triggerFullSync" \
  >/dev/null
{
  echo '$ 지금 사람 목록'
  users
  echo
  echo '$ customUserSearchFilter 로 서비스 계정을 뺀다'
  echo '  (&(!(sAMAccountName=svc-*)))'
  cfgset customUserSearchFilter '(&(!(sAMAccountName=svc-*)))'
  api POST "/$REALM/user-storage/$LDAP_ID/sync?action=triggerFullSync" \
    >/dev/null
  echo
  echo '  다시 보면:'
  users
  echo
  echo '  바로 줄었다. 사람 목록은 캐시가 아니라 그때그때 AD 에'
  echo '  물어보기 때문이다 — 필터가 곧바로 먹는다.'
  echo
  echo '  다만 데이터베이스 안의 **사본**은 남아 있을 수 있다.'
  echo '  그것까지 치우는 것이 remove-imported-users 다.'
  cfgset customUserSearchFilter ''
} >"$OUT/kc_ad_filter.txt" 2>&1

# ── 실험 4. 로그인 아이디를 UPN 으로 바꾼다 ─────────────────────────
#
# 회사마다 "직원 번호로 로그인" "메일 주소로 로그인" 이 다르다.
# 그것을 정하는 칸이 usernameLDAPAttribute 하나다.
# 이 실험은 사본의 아이디를 바꿔 놓으므로 **맨 뒤에** 둔다.
reset
{
  echo '$ usernameLDAPAttribute 를 userPrincipalName 으로 바꾼다'
  cfgset usernameLDAPAttribute userPrincipalName
  echo
  echo '  이제 sAMAccountName 으로는 못 들어간다:'
  mark
  login minji 'Passw0rd!-demo'
  echo
  echo '  UPN 으로는 들어간다:'
  login 'minji@ad.campus.example' 'Passw0rd!-demo'
  echo
  echo '  가짜 AD 가 받은 것 (필터의 속성 이름을 볼 것):'
  since | grep filter= | sed 's/^/    /'
  cfgset usernameLDAPAttribute sAMAccountName
  echo
  echo '  (되돌렸다)'
} >"$OUT/kc_ad_upn.txt" 2>&1

rm -f "$OUT/.lab_cfg.json"
echo 'AD 실험 완료 — out/kc_ad_*.txt'
