#!/bin/sh
# fork_loop.sh — 바깥 명령을 N번 (실험 5, proot 의 값).
#
#   fork_loop.sh N
#
# 새 프로세스 하나는 fork·execve·wait 와 동적 링커의 일 전부다.
# proot 는 그 시스템 호출마다 끼어들고 execve 때는 경로도 번역한다.
# true 는 셸 내장 명령이라 그냥 쓰면 새 프로세스가 안 생긴다.
# env 를 거쳐 PATH 의 true 실행 파일을 부른다.
n=${1:?사용법: fork_loop.sh N}
i=0
while [ "$i" -lt "$n" ]; do
  env true
  i=$((i + 1))
done
echo "true 를 ${n}번 실행했다"
