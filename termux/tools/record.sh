#!/bin/sh
# record.sh — 덱에 실릴 캡처를 다시 뜨고, stable 이 재현되는지 본다.
#
#   sh tools/record.sh          # run_all.py 한 번
#   sh tools/record.sh --check  # 두 번 더 돌려 stable 의 md5 를 대조
#
# **세 번 떠서 같아야 한다** 는 규칙의 값어치: 캡처가 그 실행의
# 우연(pid·시각·순서)에 기대면 여기서 걸린다. 걸린 것을 그대로
# 실으면 독자가 같은 명령을 쳤을 때 다른 답이 나온다.
# 배터리·시간처럼 원래 흔들리는 것은 매니페스트에 snapshot 으로
# 적혀 있고 대조에서 빠진다(PLAN.md §0.9). 1회차는 지금 out/ 에
# 있는 것이다. RECORD_BASE 로 다른 디렉터리를 가리킬 수 있다(시험용).
set -eu
cd "${RECORD_BASE:-$(dirname "$0")/..}"
PY=${PY:-python3}

# 매니페스트에서 stable 인 파일만, 이름 차례로
md5_stable() {
  $PY -c 'import json
m = json.load(open("out/manifest.json"))
print("\n".join(sorted(k for k, v in m.items()
                       if v.get("kind") == "stable")))' |
  while read -r f; do md5sum "out/$f"; done
}

if [ "${1:-}" = '--check' ]; then
  first=$(md5_stable)
  echo "  1회차 — 지금 out/ 에 있는 것"
  n=2
  while [ "$n" -le 3 ]; do
    echo "  ${n}회차 — 다시 돌린다"
    $PY run_all.py > /dev/null
    later=$(md5_stable)
    if [ "$first" != "$later" ]; then
      echo "  ✗ ${n}회차가 1회차와 다르다:"
      printf '%s\n' "$first" > out/.md5_1
      printf '%s\n' "$later" > "out/.md5_$n"
      diff out/.md5_1 "out/.md5_$n" | grep '^[<>]' || true
      exit 1
    fi
    n=$((n + 1))
  done
  rm -f out/.md5_*
  echo "  ✓ stable 캡처 $(md5_stable | wc -l)개가 3회차까지 같다"
  exit 0
fi

$PY run_all.py
