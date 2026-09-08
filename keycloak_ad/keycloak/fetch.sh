#!/bin/sh
# fetch.sh — Keycloak 배포판을 내려받아 kc/ 에 푼다.
#
# 판번호는 VERSION 파일 하나에만 적혀 있다. 덱의 모든 화면이 그 판의
# 것이므로, 판을 올리려면 그 파일을 고치고 캡처를 전부 다시 떠야 한다.
#
# 받은 것의 sha256 은 deck/claims.md 에 적혀 있다. 여기서도 다시 세어
# 견준다 — 내려받은 것이 그때 그것인지 확인하지 않으면
# "출처가 있다" 는 말이 아무 뜻이 없기 때문이다.
#
# kc/ 는 .gitignore 에 있다. 500 MB 가 넘고, 언제든 다시 받을 수 있다.
set -eu
cd "$(dirname "$0")/.."

VER=$(cat keycloak/VERSION)
ZIP=kc/keycloak-$VER.zip
BASE=https://github.com/keycloak/keycloak/releases/download
URL=$BASE/$VER/keycloak-$VER.zip

mkdir -p kc

if [ -x "kc/keycloak-$VER/bin/kc.sh" ]; then
  echo "이미 있다: kc/keycloak-$VER"
  exit 0
fi

if [ ! -f "$ZIP" ]; then
  echo "내려받는 중 ($VER, 200 MB 쯤)"
  curl -sSL -o "$ZIP" "$URL"
fi

echo "sha256 $(sha256sum "$ZIP" | cut -d' ' -f1)"

# -q 로 조용히 푼다. 파일이 만 개가 넘어 목록을 찍으면 화면이 넘친다.
unzip -q -o "$ZIP" -d kc
[ -x "kc/keycloak-$VER/bin/kc.sh" ] || {
  echo "kc.sh 가 없다 — 압축이 깨졌다" >&2
  exit 1
}
rm -f "$ZIP"
echo "풀었다: kc/keycloak-$VER"
