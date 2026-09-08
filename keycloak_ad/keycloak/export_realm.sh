#!/bin/sh
# export_realm.sh — 만들어 둔 realm 을 파일 하나로 뽑는다.
#
# 콘솔에서 눌러 만든 것을 **되풀이할 수 있는 형태**로 바꾸는 일이다.
# 이 파일 하나면 빈 Keycloak 에 같은 realm 을 다시 세울 수 있다 —
# 6부에서 쿠버네티스에 올릴 때 그렇게 한다.
#
# 서버를 끄고 돌려야 한다. 내보내기는 별도의 실행 모드라
# 돌고 있는 서버와 같은 데이터베이스를 함께 쓸 수 없다.
set -eu
cd "$(dirname "$0")/.."

VER=$(cat keycloak/VERSION)
KC=kc/keycloak-$VER
DIR=out/.kc_export

sh keycloak/stop.sh
rm -rf "$DIR"
mkdir -p "$DIR"

JAVA_OPTS_KC_HEAP="-Xms128m -Xmx640m"
export JAVA_OPTS_KC_HEAP

# --users skip : 사람은 담지 않는다.
#
# AD 에서 온 사람들은 Keycloak 안에 **사본**으로 있을 뿐이고, 원본은
# 디렉터리에 있다. 그 사본을 설정 파일에 담아 커밋하면 이름과 메일이
# 저장소에 들어가고, 게다가 원본이 바뀌면 곧 거짓말이 된다.
# 담을 것은 **설정**이다 — 사람은 뜨는 순간 AD 에서 다시 온다.
"$KC/bin/kc.sh" export --dir "$DIR" --realm campus \
  --users skip >out/kc_export.log 2>&1

[ -f "$DIR/campus-realm.json" ] || {
  echo '내보내기 실패 — out/kc_export.log 를 볼 것' >&2
  tail -20 out/kc_export.log >&2
  exit 1
}

# 사람이 읽을 수 있게 다듬어 저장한다. 키 순서를 고정해야
# 다시 뽑았을 때 쓸데없는 차이가 안 생긴다.
python3 - "$DIR/campus-realm.json" keycloak/realm-campus.json <<'PY'
import json
import sys

src, dst = sys.argv[1], sys.argv[2]
d = json.load(open(src, encoding='utf-8'))
with open(dst, 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2, sort_keys=True)
    f.write('\n')
PY
rm -rf "$DIR"
echo "뽑았다 — keycloak/realm-campus.json ($(wc -l \
  < keycloak/realm-campus.json) 줄)"
