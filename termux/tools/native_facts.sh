#!/bin/sh
# native_facts.sh — 네이티브 Termux 에서 **사용자가 한 번** 돌린다.
#
#   (Termux 앱을 열고, proot 가 아닌 첫 셸에서)
#   sh ~/github/treasure_house/termux/tools/native_facts.sh \
#      ~/github/treasure_house/termux/data/device.txt
#
# 왜 사람이 돌리나: 이 덱을 만든 세션은 proot 안이다. 거기서는
# getprop 이 막히고, Termux 의 바이너리를 불러도 proot 의 ptrace
# 아래라 id·uname·/proc/self/status 가 proot 가 꾸민 값이다(PLAN.md
# 진행 기록 2단계). 진짜 값은 proot 밖에서만 보인다(§9 결정 8).
#
# 읽기만 한다. 설정을 바꾸는 명령은 하나도 없다. 결과 파일은
# 커밋 전에 tools/scrub.py 가 검사한다.
[ $# -eq 1 ] || { echo '사용법: native_facts.sh 결과파일' >&2; exit 2; }
out=$1
n=0
sec() {
  n=$((n + 1))
  printf '\n== %d. %s ==\n' "$n" "$1" >> "$out"
  sh -c "$1" >> "$out" 2>&1
}
printf '# native_facts %s\n' "$(date +%Y-%m-%d)" > "$out"
sec 'getprop ro.build.version.release'
sec 'getprop ro.build.version.sdk'
sec 'settings get global settings_enable_monitor_phantom_procs'
sec 'getprop ro.product.cpu.abi'
sec 'id'
sec 'uname -a'
sec "grep -E '^(Uid|Gid|Groups|Seccomp|TracerPid)' /proc/self/status"
sec 'termux-info'
echo "적었다: $out"
