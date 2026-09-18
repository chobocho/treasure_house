#!/bin/sh
# fetch_src.sh — upstream 저장소를 data/repos.tsv 의 핀 커밋으로 받는다.
#
#   sh tools/fetch_src.sh              # 표의 저장소 전부
#   sh tools/fetch_src.sh --only REPO  # 하나만
#   sh tools/fetch_src.sh --head       # 원격 HEAD (핀 고르기)
#
# sources/ 는 커밋하지 않는 캐시다. 이 스크립트 하나로 언제든 다시
# 만든다. 덱이 인용하는 것은 작업 트리가 아니라 핀 커밋이므로
# (deck/srcpin.py), 여기서 할 일은 "그 커밋이 로컬에 있게" 하는
# 것뿐이다.
#
# 표의 history 칸이 받는 양을 정한다 — 이 폰의 메모리와 저장소 크기
# 때문이다(PLAN.md §0.6).
#   full    : 커밋 기록 전부, 나무·파일은 필요할 때(--filter=tree:0).
#             첫 커밋·태그 날짜와 태그마다의 minSdk 를 git 으로
#             읽는다 — GitHub API 는 시간당 60번뿐이다.
#   shallow : 핀 커밋 하나만(--depth 1 --filter=blob:none).
# paths 칸(쉼표로 가른 디렉터리, 없으면 -)은 희소 체크아웃이다.
# termux-packages 처럼 큰 저장소에서 필요한 패키지만 푼다.
#
# 시간 O(받는 양). 한 번에 한 저장소씩, 차례로.
set -u
BASE=${FETCH_BASE:-$(cd "$(dirname "$0")/.." && pwd)}
TSV=$BASE/data/repos.tsv
only=
head=0
while [ $# -gt 0 ]; do
  case $1 in
    --only) only=$2; shift ;;
    --head) head=1 ;;
  esac
  shift
done

# 칸 이름으로 칸 번호를 찾는다 — 칸을 더해도 스크립트가 안 깨진다.
col() {
  head -n 50 "$TSV" | grep -v '^#' | head -n 1 | tr '\t' '\n' \
    | grep -nx "$1" | cut -d: -f1
}
C_REPO=$(col repo); C_URL=$(col url); C_SHA=$(col pinned-sha)
C_HIST=$(col history); C_PATHS=$(col paths)

rows() {
  grep -v '^#' "$TSV" | tail -n +2 | grep -v '^[[:space:]]*$'
}

fail=0
tab=$(printf '\t')
rows | while IFS= read -r line; do
  f() { printf '%s\n' "$line" | cut -d"$tab" -f"$1"; }
  repo=$(f "$C_REPO"); url=$(f "$C_URL"); sha=$(f "$C_SHA")
  hist=$(f "$C_HIST"); paths=$(f "$C_PATHS")
  [ -n "$only" ] && [ "$only" != "$repo" ] && continue
  if [ $head -eq 1 ]; then
    printf '%s\t%s\n' "$repo" \
      "$(git ls-remote "$url" HEAD | cut -f1)"
    continue
  fi
  dir=$BASE/sources/$repo
  if [ ! -d "$dir/.git" ]; then
    git init -q "$dir" && git -C "$dir" remote add origin "$url"
    if [ "$paths" != '-' ] && [ -n "$paths" ]; then
      git -C "$dir" sparse-checkout set $(echo "$paths" | tr ',' ' ')
    fi
  fi
  if ! git -C "$dir" cat-file -e "$sha^{commit}" 2>/dev/null; then
    if [ "$hist" = full ]; then
      git -C "$dir" fetch -q --filter=tree:0 --tags origin \
        '+refs/heads/*:refs/remotes/origin/*'
    fi
    git -C "$dir" cat-file -e "$sha^{commit}" 2>/dev/null \
      || git -C "$dir" fetch -q --depth 1 --filter=blob:none \
           origin "$sha"
  fi
  if ! git -C "$dir" -c advice.detachedHead=false checkout -q \
       --detach "$sha" 2>/dev/null; then
    echo "  ✗ $repo: 핀 커밋 $sha 에 설 수 없다" >&2
    exit 1
  fi
  size=$(du -sh "$dir" | cut -f1)
  echo "  $repo @ $(echo "$sha" | cut -c1-7) · $size"
done || fail=1
exit $fail
