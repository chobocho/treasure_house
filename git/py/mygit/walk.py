# -*- coding: utf-8 -*-
"""역사 걷기와 merge-base (SPEC.md §10).

git 의 기본 log 차례는 "커미터 날짜가 늦은 것부터" 인데, 날짜가 같을
때의 규칙까지 정해져 있다 — 날짜 차례로 정렬된 목록에 새 커밋을 끼울
때 **같은 날짜들 가운데 맨 뒤에** 끼운다(git 의 commit_list_insert_
by_date). 이 덱의 저장소는 모든 커밋의 날짜가 같게 만들어지므로, 이
한 줄이 차례의 전부를 정한다(golden/dag/equal 이 그것을 확인한다).
"""
import bisect
import heapq
import itertools

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


def _paint(gitdir, a, b):
    """git 의 paint_down_to_common(commit-reach.c)이 공통 조상 후보를
    찾는 차례 — SPEC.md §10.2 의 1~4.

    큐는 (날짜 내림차순, 넣은 차례) 의 우선순위 큐다 — 같은 날짜면 먼저
    넣은 것이 먼저 나온다. 표시는 P1(a 에서 닿음)·P2(b 에서 닿음)·
    STALE(이미 찾은 후보의 조상). "넣을 때 STALE 이 아니었던" 커밋이
    큐에 남아 있는 동안 돈다(git 의 max_nonstale 과 같은 조건).
    O(커밋 수 × log 커밋 수) 시간, O(커밋 수) 공간.
    """
    p1, p2, stale = 1, 2, 4
    flags, queued, heap, found = {}, {}, [], []
    ctr = itertools.count()
    live = [0]                 # 넣을 때 STALE 이 아니었던 것의 수

    def put(c):
        if c in queued:        # 이미 큐에 있으면 자리는 그대로
            return
        queued[c] = not flags[c] & stale
        live[0] += queued[c]
        heapq.heappush(heap, (-parents_and_date(gitdir, c)[1],
                              next(ctr), c))
    flags[a] = p1
    put(a)
    flags[b] = flags.get(b, 0) | p2
    put(b)
    while live[0]:
        _, _, c = heapq.heappop(heap)
        live[0] -= queued.pop(c)
        f = flags[c] & (p1 | p2 | stale)
        if f == p1 | p2:
            if c not in found:
                found.append(c)
            f |= stale
        for p in parents_and_date(gitdir, c)[0]:
            if flags.get(p, 0) & f == f:
                continue
            flags[p] = flags.get(p, 0) | f
            put(p)
    return [c for c in found if not flags[c] & stale]


def merge_bases(gitdir, a, b):
    """가장 좋은 공통 조상들(SPEC.md §10.2) — git 과 같은 차례로.

    후보는 _paint 가 찾은 차례 그대로 두고, 다른 후보의 조상인 것을 뺀
    뒤(git 의 remove_redundant — 차례를 바꾸지 않는다) 커미터 날짜
    내림차순으로 안정 정렬한다. 날짜가 같으면 찾은 차례가 남으므로
    인자 순서에 따라 답의 차례가 바뀐다 — git 도 그렇다.
    후보가 몇 안 되므로 조상 검사는 곧은 방법으로. O(커밋 수 × 후보 수).
    """
    cands = _paint(gitdir, a, b)
    best = [c for c in cands
            if not any(o != c and is_ancestor(gitdir, c, o)
                       for o in cands)]
    best.sort(key=lambda c: -parents_and_date(gitdir, c)[1])
    return best
