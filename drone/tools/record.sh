#!/bin/sh
# record.sh — 덱에 실릴 '진짜 출력' 을 다시 남기고, 재현되는지 본다.
#
#   sh tools/record.sh          # out/ 를 다시 채운다
#   sh tools/record.sh --check  # 세 번 돌려 sha256 이 같은지 본다
#
# **세 번 돌려 같아야 한다** 는 규칙의 값어치는 이것이다: 캡처가 그
# 실행의 우연(시각·난수·딕셔너리 차례)에 기대고 있으면 여기서 걸린다.
# 걸린 것을 그대로 덱에 실으면, 독자가 같은 코드를 돌렸을 때 다른
# 답이 나온다. 그러면 그 장은 증거가 아니라 그림이다.
#
# 이 덱에는 시간을 재는 캡처가 없다(PLAN.md §0.10 — 벤치마크의 ns/op 는
# 가리고 allocs/op·B/op 만 싣는다). 그래서 out/ 의 캡처(*.txt)와 생성
# 표(*.html) 전부가 세 번 돌려 바이트까지 같아야 한다. go 출력에 섞이는
# 경로·고루틴 번호·주소·임시 이름은 tools/gover.py 가 정규화하며 그
# 사실을 캡션에 적는다.
set -eu
cd "$(dirname "$0")/.."

PY=${PY:-python3}

sums_all() {
  (ls out/*.txt out/*.html 2>/dev/null \
     | sort | while read -r f; do
    sha256sum "$f"
  done)
}

if [ "${1:-}" = '--check' ]; then
  first=$(sums_all)
  echo "  1회차 — 지금 out/ 에 있는 것"
  n=2
  while [ "$n" -le 3 ]; do
    echo "  ${n}회차 — 실험 디렉터리를 비우고 다시 돌린다"
    # 앞 실행이 남긴 작업 디렉터리가 있으면 "처음 돌리는 사람" 과 다른
    # 결과가 나와도 세 번 모두 같아 보인다 — git 덱에서 2026-09-18 에
    # worktree·pre-push 캡처가 그렇게 숨었다. 그래서 재실행은 늘 빈
    # scratch/work 에서 시작한다. GOCACHE 는 남긴다 — 빌드 캐시는
    # 출력을 바꾸지 않고, 지우면 세 번 모두 처음부터 컴파일해 이
    # 기계에서 너무 길다.
    rm -rf scratch/work
    $PY run_all.py >/dev/null
    later=$(sums_all)
    if [ "$first" != "$later" ]; then
      echo '  ✗ 두 번 돌린 결과가 다르다:'
      printf '%s\n' "$first" > out/.sha_1
      printf '%s\n' "$later" > "out/.sha_$n"
      diff out/.sha_1 "out/.sha_$n" || true
      exit 1
    fi
    n=$((n + 1))
  done
  echo "  ✓ 캡처 $(sums_all | wc -l)개가 3회차까지 같다"
  exit 0
fi

$PY run_all.py
