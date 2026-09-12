#!/bin/sh
# record.sh — 덱에 실릴 '진짜 출력' 을 전부 다시 남긴다.
#
# 이 덱의 검은 바탕 화면은 하나도 손으로 쓰지 않았다. 전부 여기서
# 나온다. 그래서 이 파일은 덱의 증거 목록이기도 하다 — 무엇을 실제로
# 돌려 봤는지 알고 싶으면 여기를 읽으면 된다.
#
#   sh tools/record.sh          # out/ 를 다시 채운다
#   sh tools/record.sh --check  # 두 번 더 떠서 md5 가 같은지 본다
#
# **두 번 떠서 같아야 한다** 는 규칙의 값어치는 이것이다: 캡처가 그
# 실행의 우연(시각·난수·해시 순서)에 기대고 있으면 여기서 걸린다.
# 걸린 것을 그대로 덱에 실으면, 독자가 같은 명령을 쳤을 때 다른 답이
# 나온다. 그러면 그 장은 증거가 아니라 그림이다.
#
# 시간을 재는 캡처는 그럴 수 없다. 그 사실은 out/reproducible.txt 에
# 적어 두고, 검사에서 뺀다 — 숨기지 않고 적어 두는 쪽을 택한다.
set -eu
cd "$(dirname "$0")/.."

OUT=out
mkdir -p "$OUT"

PY=${PY:-python3}
GOTOOLCHAIN=local
GOFLAGS=-p=1
export GOTOOLCHAIN GOFLAGS

# 두 번 떠서 같아야 하는 것들. 여기 없는 것은 시간이 들어간 캡처다.
REPRO="parity_*.txt decoders_*.txt interop_*.txt bench_ratio.txt"

record_all() {
  # 1. 다섯 언어가 같은 바이트를 내는가 (골든 + 5×5 교차 복호).
  $PY bench/run_parity.py
  # 2. 복호기만 있는 모듈 — 진짜 bzip2·xz 가 만든 파일을 푼다.
  $PY bench/run_decoders.py
  # 3. 진짜 gzip·zlib·lz4 와 양방향으로 주고받는다.
  $PY interop/run_interop.py
  # 4. 비율(골든에서)·속도(실제 측정)·manifest.
  $PY bench/run_bench.py
}

# md5sum <- 재현 가능한 캡처만 한 줄로.
repro_md5() {
  # shellcheck disable=SC2086
  (cd "$OUT" && ls $REPRO 2>/dev/null | sort | while read -r f; do
    md5sum "$f"
  done)
}

if [ "${1:-}" = '--check' ]; then
  first=$(repro_md5)
  echo "  1회차 — 지금 out/ 에 있는 것"
  n=2
  while [ "$n" -le 3 ]; do
    echo "  ${n}회차 — 다시 뜬다"
    record_all >/dev/null
    later=$(repro_md5)
    if [ "$first" != "$later" ]; then
      echo '  ✗ 두 번 뜬 결과가 다르다:'
      printf '%s\n' "$first" >"$OUT/.md5_1"
      printf '%s\n' "$later" >"$OUT/.md5_$n"
      diff "$OUT/.md5_1" "$OUT/.md5_$n" || true
      exit 1
    fi
    n=$((n + 1))
  done
  echo "  ✓ 재현 가능한 캡처 $(repro_md5 | wc -l)개가 3회차까지 같다"
  exit 0
fi

record_all

# 무엇이 두 번 떠도 같고 무엇이 아닌지, 그리고 왜인지.
{
  echo '이 덱의 캡처는 두 번 떠서 md5 가 같아야 실린다.'
  echo '아래는 그럴 수 있다 — 다섯 언어가 같은 바이트를 내는 것이'
  echo '이 책의 주장이므로, 여기가 흔들리면 주장이 흔들린다.'
  echo
  # shellcheck disable=SC2086
  (cd "$OUT" && ls $REPRO 2>/dev/null | sort | sed 's/^/  /')
  echo
  echo '아래는 그럴 수 없다 — 시간을 재기 때문이다:'
  echo
  echo '  bench_speed.txt   모듈 × 언어의 처리량'
  echo '  bench_lang.txt    언어별 합계'
  echo '  manifest.json     위 두 파일의 SHA-256 을 담는다'
  echo
  echo '시간을 고정하는 길이 없지는 않다 — 명령 수를 세는 것이다.'
  echo '하지만 그러면 "C++ 가 파이썬보다 20배" 같은 말을 못 한다.'
  echo '이 책이 하려는 말이 바로 그것이라, 시간 쪽을 택하고 그'
  echo '대신 재현 불가를 적어 둔다.'
} >"$OUT/reproducible.txt"

echo "  out/ 를 다시 채웠다 — 재현 검사는 sh tools/record.sh --check"
