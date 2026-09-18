#!/bin/sh
# native_facts.sh — 네이티브 Termux 에서 **사용자가 한 번** 돌린다.
#
#   (Termux 앱을 열고, proot 가 아닌 첫 셸에서)
#   sh ~/github/treasure_house/termux/tools/native_facts.sh \
#      ~/github/treasure_house/termux/data/device.txt
#
# 왜 사람이 돌리나: 이 덱을 만든 세션은 proot 안이다. 거기서는
# getprop 이 막히고, Termux 의 바이너리를 불러도 proot 의 ptrace
# 아래라 id·uname·/proc/self/status 가 proot 가 꾸민 값이며, 파일
# 시스템도 우분투의 것으로 보인다(PLAN.md 진행 기록 2·5단계).
# 진짜 값은 proot 밖에서만 보인다(§9 결정 8).
#
# 뒤쪽 절은 5단계에서 Termux 의 clang 으로 지어 둔 실험 바이너리
# (scratch/build/bionic/)와 셔뱅 실험, 그리고 proot 에서는 답하지
# 않는 Termux:API 의 읽기 명령(20초 제한)을 네이티브에서 돌린다.
# 읽기만 한다. 설정을 바꾸거나 파일을 지우는 명령은 없다.
# 결과 파일은 커밋 전에 tools/scrub.py 가 검사한다.
[ $# -eq 1 ] || { echo '사용법: native_facts.sh 결과파일' >&2; exit 2; }
out=$1
here=$(cd "$(dirname "$0")/.." && pwd)
b=${NATIVE_BUILD:-$here/scratch/build/bionic}
n=0
sec() {
  n=$((n + 1))
  printf '\n== %d. %s ==\n' "$n" "${2:-$1}" >> "$out"
  sh -c "$1" >> "$out" 2>&1
  printf '(종료 %d)\n' $? >> "$out"
}
exp() {
  if [ -x "$b/$1" ]; then
    sec "\"$b/$1\" $2" "$1 $2"
  else
    n=$((n + 1))
    printf '\n== %d. %s %s ==\n(빌드 없음: %s)\n' "$n" "$1" "$2" \
      "$b/$1" >> "$out"
  fi
}
printf '# native_facts %s\n' "$(date +%Y-%m-%d)" > "$out"
sec 'getprop ro.build.version.release'
sec 'getprop ro.build.version.sdk'
sec 'settings get global settings_enable_monitor_phantom_procs'
sec 'getprop ro.product.cpu.abi'
sec 'id'
sec 'uname -a'
sec "grep -E '^(Uid|Gid|Groups|Seccomp|TracerPid)' /proc/self/status"
sec 'echo "$LD_PRELOAD"'
sec "grep ' /storage/emulated ' /proc/mounts"
sec 'cat /proc/sys/kernel/pid_max'
sec 'ulimit -a'
exp hello ''
exp passwd ''
exp paths '/tmp /bin/sh /usr/bin/env /etc/passwd /system/bin/sh \
  $PREFIX/bin/sh'
exp bind_port '--scan 1 1100'
# 9부의 proot 비용 — proot 안에서 뜬 스냅샷(out/proot_cost.txt)과
# 같은 두 측정을 네이티브에서
sec "cd '$here' && python3 exp/timeit_exp.py -n 3 -- \
  $b/syscall_loop 200000" 'timeit_exp.py -n 3 -- syscall_loop 200000'
sec "cd '$here' && python3 exp/timeit_exp.py -n 3 -- \
  $b/syscall_loop 200000 getcwd" \
  'timeit_exp.py -n 3 -- syscall_loop 200000 getcwd'
sec "cd '$here' && python3 exp/timeit_exp.py -n 3 -- \
  sh exp/fork_loop.sh 100" \
  'timeit_exp.py -n 3 -- sh exp/fork_loop.sh 100'
sec "sh '$here/exp/shebang/run.sh'" 'shebang/run.sh (termux-exec 켬)'
sec "env -u LD_PRELOAD sh '$here/exp/shebang/run.sh'" \
  'shebang/run.sh (LD_PRELOAD 뺌)'
for c in termux-battery-status 'termux-sensor -l' termux-camera-info \
  termux-tts-engines termux-audio-info termux-wifi-connectioninfo; do
  sec "timeout 20 $c"
done
sec 'termux-info'
echo "적었다: $out"
