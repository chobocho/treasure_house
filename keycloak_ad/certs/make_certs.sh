#!/bin/sh
# make_certs.sh — 이 덱의 시연용 인증서 세 장을 만든다.
#
#   demo-ca.crt/key   우리가 직접 만든 인증 기관(CA). 회사 내부 CA 를 흉내 낸다.
#   ldap.crt/key      가짜 AD 의 LDAPS(636/10636) 용. 이름은 ldap.ad.campus.example
#   sso.crt/key       Keycloak 의 HTTPS 용. 이름은 sso.campus.example
#
# 왜 자체 CA 인가: 회사·학교의 도메인 컨트롤러는 거의 예외 없이 내부 CA 가 발급한
# 인증서를 쓴다. 그래서 Keycloak 쪽에서 "이 CA 를 믿어라" 라고 알려 주는 일
# (truststore 설정, 7부)이 실무에서 가장 자주 막히는 자리다. 그 상황을 그대로
# 재현하려면 공인 CA 가 아니라 우리 CA 여야 한다.
#
# ⚠ 여기서 나오는 것은 전부 시연용이다. 개인키가 저장소에 그대로 들어 있으므로
#   비밀이 아니다. 실제 환경에 절대 쓰지 말 것. 덱에서는 "예제용" 배지로 표시한다.
#
# 되풀이해 돌려도 같은 결과가 나오도록, 이미 있으면 다시 만들지 않는다.
# 강제로 다시 만들려면:  sh certs/make_certs.sh --force
set -eu
cd "$(dirname "$0")"

[ "${1:-}" = "--force" ] && rm -f demo-ca.crt demo-ca.key demo-ca.srl \
                                 ldap.crt ldap.key ldap.csr sso.crt sso.key sso.csr

# 10년. 시연용이라 유효기간이 길어야 덱이 오래 살아남는다. 실무에서는 서버
# 인증서를 1년 이하로 두는 것이 보통이고, 공인 CA 는 398일을 넘겨 발급하지 않는다.
DAYS=3650
SUBJ_BASE="/C=KR/O=Campus Demo (NOT REAL)/OU=Deck Example"

# ── 1. CA ────────────────────────────────────────────────────────────────
# CA 는 스스로 서명한다. basicConstraints CA:TRUE 가 "나는 남을 서명해도 되는
# 인증서다" 라는 선언이고, 이게 없으면 아무도 이 CA 를 CA 로 인정하지 않는다.
if [ ! -f demo-ca.crt ]; then
  openssl req -x509 -newkey rsa:2048 -nodes -sha256 -days "$DAYS" \
    -keyout demo-ca.key -out demo-ca.crt \
    -subj "$SUBJ_BASE/CN=Campus Demo Root CA" \
    -addext "basicConstraints=critical,CA:TRUE,pathlen:0" \
    -addext "keyUsage=critical,keyCertSign,cRLSign" 2>/dev/null
  echo "  만듦: demo-ca.crt (시연용 루트 CA)"
fi

# ── 2. 서버 인증서 ───────────────────────────────────────────────────────
# 요즘 클라이언트(Go·자바·브라우저 전부)는 CN 을 보지 않고 SAN 만 본다.
# SAN 을 빼먹은 인증서는 "이름이 안 맞는다" 로 거절당한다 — 3부에서 실제로 겪는다.
server_cert() {
  name="$1"; host="$2"; extra="$3"
  [ -f "$name.crt" ] && return 0
  openssl req -newkey rsa:2048 -nodes -sha256 \
    -keyout "$name.key" -out "$name.csr" \
    -subj "$SUBJ_BASE/CN=$host" 2>/dev/null
  openssl x509 -req -in "$name.csr" -CA demo-ca.crt -CAkey demo-ca.key \
    -CAcreateserial -days "$DAYS" -sha256 -out "$name.crt" \
    -extfile /dev/stdin <<EOF 2>/dev/null
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=DNS:$host$extra
EOF
  rm -f "$name.csr"
  echo "  만듦: $name.crt (CN=$host, SAN=$host$extra)"
}

# 가짜 AD 는 컨테이너 밖에서도 안에서도 붙을 수 있어야 해서 localhost 를 함께 넣는다.
server_cert ldap ldap.ad.campus.example ",DNS:localhost,IP:127.0.0.1"
server_cert sso  sso.campus.example      ",DNS:localhost,IP:127.0.0.1"

# 파일 권한: 개인키는 소유자만. 저장소에 들어가긴 하지만 습관은 지킨다.
chmod 600 demo-ca.key ldap.key sso.key
chmod 644 demo-ca.crt ldap.crt sso.crt

echo "완료 — 시연용 인증서 3벌. 검사: sh certs/check_certs.sh"
