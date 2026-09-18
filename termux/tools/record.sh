#!/bin/sh
# record.sh — 덱에 실릴 '진짜 출력' 을 다시 남기고, 재현되는지 본다.
#
#   sh tools/record.sh          # out/ 를 다시 채운다
#   sh tools/record.sh --check  # 세 번 돌려 md5 가 같은지 본다
#
# **세 번 돌려 같아야 한다** 는 규칙의 값어치는 이것이다: 캡처가 그
# 실행의 우연(시각·난수·딕셔너리 차례)에 기대고 있으면 여기서 걸린다.
# 걸린 것을 그대로 덱에 실으면, 독자가 같은 코드를 돌렸을 때 다른
# 답이 나온다. 그러면 그 장은 증거가 아니라 그림이다.
#
# 시간을 재는 캡처는 out/bench.txt 하나뿐이다(9부 벤치 표). 그 파일만
# 대조에서 빼고, 나머지 out/*.txt 와 C 가 학습한 체크포인트
# ckpt/c_*.ckpt 는 세 번 돌려 바이트까지 같아야 한다.
set -eu
cd "$(dirname "$0")/.."

PY=${PY:-python3}

md5_all() {
  (ls out/*.txt ckpt/c_*.ckpt 2>/dev/null | grep -v '^out/bench.txt$' \
     | sort | while read -r f; do
    md5sum "$f"
  done)
}

if [ "${1:-}" = '--check' ]; then
  first=$(md5_all)
  echo "  1회차 — 지금 out/ 에 있는 것"
  n=2
  while [ "$n" -le 3 ]; do
    echo "  ${n}회차 — 다시 돌린다"
    $PY run_all.py >/dev/null
    later=$(md5_all)
    if [ "$first" != "$later" ]; then
      echo '  ✗ 두 번 돌린 결과가 다르다:'
      printf '%s\n' "$first" > out/.md5_1
      printf '%s\n' "$later" > "out/.md5_$n"
      diff out/.md5_1 "out/.md5_$n" || true
      exit 1
    fi
    n=$((n + 1))
  done
  echo "  ✓ 캡처 $(md5_all | wc -l)개가 3회차까지 같다"
  exit 0
fi

$PY run_all.py
