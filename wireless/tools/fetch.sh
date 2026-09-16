#!/bin/sh
# 3gpp.org 는 TLS 핸드셰이크에서 중간 인증서(Sectigo Public Server Authentication
# CA OV R36)를 보내지 않는다. 브라우저는 AIA 로 알아서 받아 채우지만 curl 과
# WebFetch 는 "unable to verify the first certificate" 로 실패한다.
# 그래서 시스템 번들에 그 중간 인증서 하나를 덧붙인 임시 번들로 받는다.
# 봇 차단 때문에 브라우저형 User-Agent 도 필요하다(없으면 403).
#
# 사용: tools/fetch.sh <URL> [출력파일]   (출력파일 생략 시 표준 출력)
#
# 제한 시간은 600초다. 규격 zip 은 10 MB 가 넘는 것이 있는데 이 회선에서
# 초당 50 KB 남짓 나와서, 120초로는 38.101-1 같은 문서를 못 받는다.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
BUNDLE="${TMPDIR:-/tmp}/treasure_house_ca_bundle.pem"
if [ ! -s "$BUNDLE" ] || [ "$HERE/sectigo_ov_r36.pem" -nt "$BUNDLE" ]; then
  cat /etc/ssl/certs/ca-certificates.crt "$HERE/sectigo_ov_r36.pem" > "$BUNDLE"
fi
UA="Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 Chrome/128 Safari/537.36 treasure_house-deck-builder"
if [ -n "$2" ]; then
  exec curl -sS -L -m 600 --retry 2 --cacert "$BUNDLE" -A "$UA" -o "$2" "$1"
else
  exec curl -sS -L -m 600 --retry 2 --cacert "$BUNDLE" -A "$UA" "$1"
fi
