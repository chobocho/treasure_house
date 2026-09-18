#!/bin/sh
# run.sh — 셔뱅 세 가지를 직접 실행해 본다 (실험 8).
#
# 커널은 #! 줄의 경로를 **그대로** 연다. 네이티브 Termux 에는 /bin/sh
# 도 /usr/bin/env 도 없으니 앞의 둘은 "No such file" 로 실패해야
# 한다 — termux-exec 가 LD_PRELOAD 로 execve 를 가로채 경로를
# $PREFIX 아래로 바꿔 주지 않는 한(5부). 세 번째는 어디서든 된다.
# 이 기기의 proot 안에서는 /bin/sh 가 우분투의 것이라 셋 다 된다.
# 스크립트는 임시 디렉터리에 복사해 실행 비트를 준 뒤 부른다.
here=$(cd "$(dirname "$0")" && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
for s in bin_sh.sh env_sh.sh prefix_sh.sh; do
  cp "$here/$s" "$tmp/$s"
  chmod 755 "$tmp/$s"
  out=$("$tmp/$s" 2>&1)
  rc=$?
  first=$(printf '%s\n' "$out" | head -n 1 | sed "s|$tmp/||")
  echo "$s: 종료 $rc · $first"
done
