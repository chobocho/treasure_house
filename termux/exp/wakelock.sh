#!/bin/sh
# wakelock.sh — 웨이크락을 잡고, 무슨 일이 있어도 놓는다 (실험 10).
#
#   wakelock.sh CMD …     CMD 를 도는 동안만 CPU 가 잠들지 않게
#
# termux-wake-lock 은 앱의 서비스에 인텐트를 보내 부분 웨이크락을
# 잡는다. 놓는 것을 잊으면 배터리가 샌다. 그래서 trap 으로 놓는다 —
# CMD 가 실패하거나 Ctrl-C 로 끊겨도 EXIT 에서 풀린다.
set -u
termux-wake-lock
echo "termux-wake-lock 종료 코드 $?"
trap 'termux-wake-unlock; echo "termux-wake-unlock 종료 코드 $?"' EXIT
"$@"
