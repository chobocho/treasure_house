# -*- coding: utf-8 -*-
"""역사 걷기와 merge-base (SPEC.md §10).

git 의 기본 log 차례는 "커미터 날짜가 늦은 것부터" 인데, 날짜가 같을
때의 규칙까지 정해져 있다 — 날짜 차례로 정렬된 목록에 새 커밋을 끼울
때 **같은 날짜들 가운데 맨 뒤에** 끼운다(git 의 commit_list_insert_
by_date). 이 덱의 저장소는 모든 커밋의 날짜가 같게 만들어지므로, 이
한 줄이 차례의 전부를 정한다(golden/dag/equal 이 그것을 확인한다).
"""
import bisect

from mygit import commit, objects

_CACHE = {}


def parents_and_date(gitdir, oid):
    """(부모 목록, 커미터 날짜 초). 한 번 읽은 커밋은 기억한다."""
    key = (gitdir, oid)
    if key not in _CACHE:
        _t, body = objects.read_object(gitdir, oid)
        c = commit.parse_commit(body)
        when = commit.parse_ident(c['committer'])[2]
        _CACHE[key] = (c['parents'], when)
    return _CACHE[key]


def walk_log(gitdir, starts):
    """시작 커밋들에서 닿는 커밋 전부, git log 의 기본 차례로.

    큐는 날짜 내림차순 목록이다. 끼울 자리는 "날짜가 같거나 늦은 것들
    바로 뒤" — 그래서 같은 날짜라면 먼저 들어온 것이 먼저 나간다.
    O(커밋 수 × log(큐 길이)) 비교, 끼우기는 목록이라 O(큐 길이).
    """
    queue, keys, seen, out = [], [], set(), []

    def push(oid):
        if oid in seen:
            return
        seen.add(oid)
        k = -parents_and_date(gitdir, oid)[1]
        at = bisect.bisect_right(keys, k)
        keys.insert(at, k)
        queue.insert(at, oid)
    for s in starts:
        push(s)
    while queue:
        keys.pop(0)
        oid = queue.pop(0)
        out.append(oid)
        for p in parents_and_date(gitdir, oid)[0]:
            push(p)
    return out


def ancestors(gitdir, oid):
    """oid 와 그 조상 전부의 집합. O(커밋 수)."""
    seen, stack = set(), [oid]
    while stack:
        c = stack.pop()
        if c in seen:
            continue
        seen.add(c)
        stack.extend(parents_and_date(gitdir, c)[0])
    return seen


def is_ancestor(gitdir, a, b):
    """a 가 b 이거나 b 의 조상인가."""
    return a in ancestors(gitdir, b)


def merge_bases(gitdir, a, b):
    """가장 좋은 공통 조상들(SPEC.md §10.2), 커미터 날짜 내림차순.

    공통 조상 가운데 다른 공통 조상의 조상이 아닌 것만 남긴다.
    작은 저장소를 위한 곧은 방법이다 — git 은 날짜로 칠하며 내려가는
    더 빠른 길(paint_down_to_common)을 쓴다. O(커밋 수²) 최악.
    """
    common = ancestors(gitdir, a) & ancestors(gitdir, b)
    below = set()
    for c in common:
        for p in parents_and_date(gitdir, c)[0]:
            below |= ancestors(gitdir, p)
    best = [c for c in common if c not in below]
    best.sort(key=lambda c: -parents_and_date(gitdir, c)[1])
    return best
