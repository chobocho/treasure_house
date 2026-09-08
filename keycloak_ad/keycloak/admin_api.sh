#!/bin/sh
# admin_api.sh — 관리 화면의 단추가 실제로 부르는 것들.
#
# Keycloak 의 관리 콘솔은 화면일 뿐이고, 그 밑에는 REST API 가 있다.
# 콘솔에서 누르는 모든 것이 이 API 한 번씩이다. 그래서 이 파일이
# 곧 "콘솔에서 무엇을 했는지" 의 기록이 된다.
#
# 여기서 realm 을 통째로 만든다. 손으로 화면을 눌러 만든 것과
# 결과가 같고, 대신 **다시 만들 수 있다**는 것이 다르다.
set -eu
cd "$(dirname "$0")/.."

KC=${KC_URL:-http://localhost:8080}
REALM=campus
CLIENT=lunch-web
CLIENT_SECRET=lunch-secret-demo
ADMIN=${KC_BOOTSTRAP_ADMIN_USERNAME:-admin}
ADMIN_PW=${KC_BOOTSTRAP_ADMIN_PASSWORD:-admin-demo-1234}
OUT=out
mkdir -p "$OUT"

CURL="curl -sS -4"

# ── 1. 관리자 토큰 ──
#
# 관리 API 도 OIDC 로 지킨다. 4부에서 배운 그 토큰이다 —
# 다만 여기서는 사람이 아니라 스크립트가 쓰므로
# 비밀번호를 직접 내미는 흐름(password grant)을 쓴다.
token() {
  $CURL -X POST \
    "$KC/realms/master/protocol/openid-connect/token" \
    -d "client_id=admin-cli" -d "username=$ADMIN" \
    -d "password=$ADMIN_PW" -d 'grant_type=password' \
    | python3 -c 'import json,sys
print(json.load(sys.stdin)["access_token"])'
}

TOKEN=$(token)
AUTH="Authorization: Bearer $TOKEN"

# api <메서드> <경로> [본문파일] — 관리 API 를 한 번 부른다.
api() {
  m=$1
  path=$2
  body=${3:-}
  if [ -n "$body" ]; then
    $CURL -X "$m" "$KC/admin/realms$path" -H "$AUTH" \
      -H 'Content-Type: application/json' --data-binary "@$body"
  else
    $CURL -X "$m" "$KC/admin/realms$path" -H "$AUTH"
  fi
}

post() {
  # 만들기는 201 을 주고 본문이 없다. 이미 있으면 409 다.
  code=$($CURL -o "$OUT/.api.out" -w '%{http_code}' \
    -X POST "$KC/admin/realms$1" -H "$AUTH" \
    -H 'Content-Type: application/json' --data-binary "@$2")
  case "$code" in
    201|204) echo "  만듦 $1" ;;
    409) echo "  이미 있음 $1" ;;
    *) echo "  실패 $1 → $code"; cat "$OUT/.api.out"; exit 1 ;;
  esac
}

# postComp — 컴포넌트(연동·매퍼)를 만든다.
#
# 컴포넌트는 이름이 같아도 **409 를 안 준다**. 같은 이름으로 여러 벌을
# 둘 수 있게 돼 있기 때문이다. 그래서 그냥 POST 하면 두 번 돌릴 때마다
# 겹친다 — 실제로 한 번 겹쳐 봤고, 매퍼가 스무 개가 됐다.
# 여기서는 이름으로 먼저 찾아보고 있으면 건너뛴다.
postComp() {
  want=$(python3 -c 'import json,sys
print(json.load(open(sys.argv[1]))["name"])' "$2")
  found=$(api GET "/$REALM/components?parent=$3" \
    | python3 -c 'import json,sys
rows = json.load(sys.stdin)
print(next((r["id"] for r in rows if r["name"] == sys.argv[1]), ""))' \
      "$want")
  if [ -n "$found" ]; then
    echo "  이미 있음 $want"
    return 0
  fi
  post "$1" "$2"
}

# ── 2. realm ──
echo 'realm'
post "" keycloak/json/realm.json

# ── 3. 클라이언트 ──
#
# **비밀이 있는(confidential) 클라이언트**다. 그리고 PKCE 를 S256 으로
# 못 박았다 — 4부 3장에서 만든 그 장치가 여기 설정 한 줄이 된다.
echo '클라이언트'
post "/$REALM/clients" keycloak/json/client.json

# ── 4. 그룹을 토큰에 싣는 매퍼 ──
#
# 기본 토큰에는 그룹이 안 실린다. 4부에서 우리 miniidp 는 groups 를
# 그냥 실었지만, Keycloak 은 **실을 것을 골라서** 매퍼로 붙인다.
echo '매퍼'
CID=$(api GET "/$REALM/clients?clientId=$CLIENT" \
  | python3 -c 'import json,sys
rows = json.load(sys.stdin)
print(rows[0]["id"] if rows else "")')
[ -n "$CID" ] || { echo '클라이언트를 못 찾았다' >&2; exit 1; }
post "/$REALM/clients/$CID/protocol-mappers/models" \
  keycloak/json/mapper-groups.json

# ── 5. AD 연동 (User Federation) ──
#
# 7부의 주제를 여기서 미리 한 번 붙인다. 값들이 3부에서 만든
# 가짜 AD 를 가리킨다 — Keycloak 은 이것을 진짜 AD 로 알고 붙는다.
echo 'AD 연동'
postComp "/$REALM/components" keycloak/json/ldap.json ""

PROVIDER=org.keycloak.storage.UserStorageProvider
LDAP_ID=$(api GET "/$REALM/components?type=$PROVIDER" \
  | python3 -c 'import json,sys
rows = json.load(sys.stdin)
print(next((r["id"] for r in rows if r["name"] == "ad-campus"), ""))')
[ -n "$LDAP_ID" ] || { echo 'AD 연동을 못 찾았다' >&2; exit 1; }

# LDAP 매퍼 — AD 의 어느 칸을 Keycloak 의 어느 칸으로 옮길 것인가.
#
# 여기서 만드는 것은 **하나뿐**이다. vendor 를 ad 로 골라 두면
# Keycloak 이 username·email·이름·MSAD 매퍼를 **알아서** 만든다.
# 안 만들어 주는 것이 그룹이라, 그것만 우리가 더한다.
ldapmap() {
  sed "s/PARENT_ID/$LDAP_ID/" "keycloak/json/ldapmap-$1.json" \
    >"$OUT/.ldapmap.json"
  postComp "/$REALM/components" "$OUT/.ldapmap.json" "$LDAP_ID"
}
ldapmap groups

# ── 이름이 뒤집혀 나오는 문제 ──
#
# AD 를 고르면 Keycloak 이 "full name" 매퍼를 붙인다. 그 매퍼는
# cn 을 **"이름 성"** 으로 보고 빈칸에서 가른다. 그런데 우리 AD 의
# cn 은 "Kim Minji" — 성이 앞이다. 그대로 두면 이름이 "Kim Kim" 이 된다.
#
# 그래서 full name 매퍼를 빼고, givenName 을 이름으로 옮기는 매퍼를
# 대신 둔다. 실제 AD 연동에서 가장 자주 겪는 손질이다(7부).
FULL_ID=$(api GET "/$REALM/components?parent=$LDAP_ID" \
  | python3 -c 'import json,sys
rows = json.load(sys.stdin)
print(next((r["id"] for r in rows if r["name"] == "full name"), ""))')
if [ -n "$FULL_ID" ]; then
  api DELETE "/$REALM/components/$FULL_ID" >/dev/null
  echo '  뺌 full name 매퍼 (cn 을 이름+성으로 가른다)'
fi
ldapmap firstname

rm -f "$OUT/.ldapmap.json" "$OUT/.api.out"

# ── 6. 화면 대신 남기는 것들 ──
#
# 여기서부터는 만들지 않고 **읽는다**. 관리 콘솔의 각 화면이
# 무엇을 부르는지가 그대로 드러난다.
echo '캡처'

{
  echo '$ curl -X POST .../protocol/openid-connect/token \\'
  echo '    -d client_id=admin-cli -d grant_type=password ...'
  echo
  echo '관리 API 도 OIDC 로 지킨다. 받은 토큰을 뜯어보면:'
  bin/jwtool decode "$TOKEN" | sed -n '/^내용/,/^$/p'
} >"$OUT/kc_admin_token.txt" 2>&1

{
  echo "\$ curl .../admin/realms/$REALM  -H 'Authorization: Bearer ...'"
  api GET "/$REALM" | python3 -c 'import json,sys
d = json.load(sys.stdin)
keys = ["realm", "enabled", "sslRequired", "bruteForceProtected",
        "failureFactor", "accessTokenLifespan", "ssoSessionIdleTimeout",
        "ssoSessionMaxLifespan", "defaultLocale"]
for k in keys:
    print("  %-24s %s" % (k, json.dumps(d.get(k), ensure_ascii=False)))
print()
print("  (칸이 모두 %d개다 — 위는 이 덱이 건드린 것들)" % len(d))'
} >"$OUT/kc_admin_realm.txt" 2>&1

{
  echo "\$ curl '.../realms/$REALM/components?type=...Provider'"
  api GET "/$REALM/components?type=$PROVIDER" \
    | python3 -c 'import json,sys
rows = json.load(sys.stdin)
for r in rows:
    print("  name       %s" % r["name"])
    print("  providerId %s" % r["providerId"])
    cfg = r["config"]
    for k in sorted(cfg):
        v = cfg[k][0] if cfg[k] else ""
        if k == "bindCredential":
            v = "********"
        print("    %-24s %s" % (k, v))'
} >"$OUT/kc_admin_ldap.txt" 2>&1

{
  echo "\$ curl -X POST '.../user-storage/<id>/sync'"
  api POST "/$REALM/user-storage/$LDAP_ID/sync?action=triggerFullSync" \
    | python3 -m json.tool
  echo
  echo '관리 콘솔의 "Sync all users" 단추가 부르는 것이 이것이다.'
} >"$OUT/kc_admin_sync.txt" 2>&1

{
  echo "\$ curl '.../realms/$REALM/users?brief=true'"
  api GET "/$REALM/users?briefRepresentation=true&max=20" \
    | python3 -c 'import json,sys
rows = json.load(sys.stdin)
print("  %-14s %-22s %s" % ("username", "email", "enabled"))
for r in sorted(rows, key=lambda r: r["username"]):
    print("  %-14s %-22s %s" % (r["username"], r.get("email", ""),
                                r["enabled"]))
print()
print("  모두 %d명 — AD 에서 온 사람들이다" % len(rows))'
} >"$OUT/kc_admin_users.txt" 2>&1

{
  echo "\$ curl '.../admin/realms/$REALM/users?username=minji'"
  api GET "/$REALM/users?username=minji&exact=true" \
    | python3 -c 'import json,sys
r = json.load(sys.stdin)[0]
for k in ["username", "firstName", "lastName", "email", "enabled",
          "origin"]:
    print("  %-14s %s" % (k, r.get(k)))
for k, v in sorted(r.get("attributes", {}).items()):
    print("  %-14s %s" % (k, v[0]))
print()
print("  LDAP_ENTRY_DN 이 3부에서 만든 그 DN 이다.")'
} >"$OUT/kc_admin_user_minji.txt" 2>&1

rm -f "$OUT/.api.out"
echo "준비됨 — $KC/realms/$REALM"
