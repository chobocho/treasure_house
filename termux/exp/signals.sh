#!/bin/sh
# signals.sh — "[Process completed (signal 9)]" 의 정체 (실험 9).
#
# 팬텀 프로세스 킬러는 SIGKILL(9)을 보낸다. 셸은 시그널로 죽은
# 자식의 종료 상태를 128 + 시그널 번호로 적는다 — 그래서 137 이다.
# 킬러를 일부러 부르지 않는다(PLAN.md §3.3). 우리 자식에게 우리가
# kill -9 를 보내 같은 모양을 만든다.
sleep 30 &
child=$!
kill -9 "$child"
status=0
wait "$child" || status=$?
echo "자식 $child 에 SIGKILL 을 보냈다"
echo "종료 상태 $status = 128 + $((status - 128))(SIGKILL)"
