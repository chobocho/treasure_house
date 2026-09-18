#!/bin/sh
# patch_stats.sh — termux-packages 의 패치를 센다 (8부).
#
#   sh tools/patch_stats.sh REPO [REV] [TOP]
#
# REPO 의 커밋 REV(기본 HEAD)에서 packages/ 트리를 읽어
#   packages N          — 패키지 디렉터리 수
#   patches N           — 이름이 .patch 로 끝나는 파일 수
#   patched-packages N  — 그런 파일이 하나라도 있는 패키지 수
# 를 적고, 패치가 많은 패키지 TOP 개(기본 8)를 센 수와 함께 적는다.
#
# 작업 트리가 아니라 **커밋의 트리**를 센다. sources/ 는 필요한
# 디렉터리만 꺼내 둔 스파스 체크아웃이라 작업 트리로는 셀 수 없다.
# .patch32 처럼 끝이 다른 이름은 세지 않는다. 트리 전체를 한 번
# 훑으므로 시간 O(파일 수), 추가 공간은 패키지 수만큼.
set -eu
[ $# -ge 1 ] || { echo '사용법: patch_stats.sh REPO [REV] [TOP]' >&2
                  exit 2; }
repo=$1 rev=${2:-HEAD} top=${3:-8}
tree=$(git -C "$repo" ls-tree -r --name-only "$rev:packages")
echo "packages $(git -C "$repo" ls-tree --name-only "$rev:packages" |
  wc -l)"
p=$(printf '%s\n' "$tree" | awk -F/ '/\.patch$/ {print $1}')
echo "patches $(printf '%s\n' "$p" | grep -c . || true)"
echo "patched-packages $(printf '%s\n' "$p" | grep . | sort -u | wc -l)"
printf '%s\n' "$p" | grep . | sort | uniq -c | sort -k1,1rn -k2 |
  head -n "$top"
