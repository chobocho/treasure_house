#!/bin/sh
# missing_lib.sh — 공유 라이브러리가 사라지면 링커는 무엇이라 하나
# (실험 12).
#
#   sh exp/missing_lib.sh CC DIR
#
# DIR 에 libgone.so 와 그것을 부르는 use_gone 을 짓고, 한 번 돌린 뒤
# 라이브러리를 지우고 다시 돌린다. 둘째 실행은 main 에 닿기도 전에
# 동적 링커가 멈춘다 — bionic 의 linker64 는 "CANNOT LINK
# EXECUTABLE", glibc 의 ld.so 는 "error while loading shared
# libraries". 15부의 문제 해결 사전이 이 한 줄을 읽는 법을 다룬다.
# 실행 파일은 ./use_gone 으로 부른다 — 메시지의 경로가 DIR 의 절대
# 경로에 흔들리지 않게.
set -u
[ $# -eq 2 ] || { echo '사용법: missing_lib.sh CC DIR' >&2; exit 2; }
cc=$1 dir=$2
mkdir -p "$dir"
cd "$dir" || exit 1
printf '#include <stdio.h>\n%s\n' \
  'void gone(void) { puts("gone 이 불렸다"); }' > gone.c
printf 'void gone(void);\nint main(void) { gone(); return 0; }\n' \
  > use.c
"$cc" -shared -fPIC gone.c -o libgone.so || exit 1
"$cc" use.c -L. -lgone -Wl,-rpath,"$PWD" -o use_gone || exit 1
printf '있을 때: '
./use_gone
rm -f libgone.so gone.c use.c
./use_gone 2>&1 | head -n 1
./use_gone >/dev/null 2>&1
echo "종료 $?"
