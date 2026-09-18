#!/bin/sh
# build.sh — C 실험 다섯을 같은 플래그로 짓는다.
#
#   sh exp/build.sh CC OUTDIR      (저장소의 termux/ 에서)
#
# 같은 소스를 두 컴파일러로 짓는 것이 실험의 요점이라, 플래그는
# 한 곳에 둔다. -Werror 라 경고 하나도 실패다. -D_DEFAULT_SOURCE 는
# glibc 에서 syscall()·getpwuid() 선언을 드러내려고 둔다 — bionic 은
# 없어도 되지만 두 쪽이 같은 줄로 짓게 한다.
set -eu
cc=${1:?사용법: build.sh CC OUTDIR}
out=${2:?사용법: build.sh CC OUTDIR}
mkdir -p "$out"
for e in hello passwd paths bind_port syscall_loop; do
  "$cc" -std=c99 -Wall -Wextra -Werror -D_DEFAULT_SOURCE \
    "exp/$e.c" -o "$out/$e"
  echo "$out/$e"
done
