# !/bin/sh check_certs.sh — make_certs.sh 가 만든 인증서가 실제로 쓸 수
# 있는 물건인지 검사한다.
#
# 왜 검사하나: 이 인증서들은 덱의 "자체 CA 를 신뢰시키는 법"(3부 LDAPS,
# 6부 Ingress, 7부 truststore) 장을 통째로 떠받친다. 만들어만 놓고
# 체인이 안 맞으면, 독자가 그대로 따라 했을 때 우리는 못 봤던 오류를
# 그쪽에서 처음 보게 된다.
#
# 검사 넷:
#   1) CA 로 서버 인증서 두 장이 검증되는가 (openssl verify)
#   2) SAN(주체 대체 이름)에 우리가 쓰는 호스트 이름이 들어 있는가
#      — 요즘 클라이언트는 CN 을 안 본다. SAN 이 없으면 실패한다.
#   3) 확장 키 용도가 serverAuth 인가
#   4) 개인키와 인증서의 공개키가 같은 짝인가
set -eu
cd "$(dirname "$0")"

fail=0
say()  { printf '  %s %s\n' "$1" "$2"; }
ok()   { say '✓' "$1"; }
bad()  { say '✗' "$1"; fail=$((fail + 1)); }

for f in demo-ca.crt demo-ca.key ldap.crt ldap.key sso.crt sso.key; do
  [ -f "$f" ] || { bad "$f 가 없다 — sh certs/make_certs.sh 를 먼저"; }
done
[ "$fail" -eq 0 ] || { printf '\n오류 %d건\n' "$fail"; exit 1; }

check_one() {
  crt="$1"; key="$2"; host="$3"

  if openssl verify -CAfile demo-ca.crt "$crt" >/dev/null 2>&1; then
    ok "$crt — demo CA 로 검증됨"
  else
    bad "$crt — demo CA 로 검증되지 않는다"
  fi

  san=$(openssl x509 -in "$crt" -noout -ext subjectAltName 2>/dev/null)
  if printf '%s' "$san" | grep -q "DNS:$host"; then
    ok "$crt — SAN 에 $host 있음"
  else
    bad "$crt — SAN 에 $host 가 없다 (CN 만으로는 거부당한다)"
  fi

  eku=$(openssl x509 -in "$crt" -noout \
          -ext extendedKeyUsage 2>/dev/null)
  if printf '%s' "$eku" | grep -q 'TLS Web Server Authentication'; then
    ok "$crt — 확장 키 용도 serverAuth"
  else
    bad "$crt — serverAuth 가 아니다"
  fi

  # 인증서의 공개키와 개인키가 같은 짝인지: 둘에서 뽑은 공개키가
  # 글자까지 같아야 한다
  a=$(openssl x509 -in "$crt" -noout -pubkey 2>/dev/null)
  b=$(openssl pkey -in "$key" -pubout 2>/dev/null)
  if [ -n "$a" ] && [ "$a" = "$b" ]; then
    ok "$crt — $key 와 같은 짝"
  else
    bad "$crt — $key 와 짝이 맞지 않는다"
  fi
}

bc=$(openssl x509 -in demo-ca.crt -noout \
       -ext basicConstraints 2>/dev/null)
if printf '%s' "$bc" | grep -q 'CA:TRUE'; then
  ok 'demo-ca.crt — basicConstraints CA:TRUE'
else
  bad 'demo-ca.crt — CA 인증서가 아니다'
fi

check_one ldap.crt ldap.key ldap.ad.campus.example
check_one sso.crt  sso.key  sso.campus.example

if [ "$fail" -eq 0 ]; then
  printf '\n오류 0건\n'
else
  printf '\n오류 %d건\n' "$fail"
  exit 1
fi
