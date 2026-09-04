# -*- coding: utf-8 -*-
"""이동 범위와 경로 — SPEC §6.

   여기가 헥스 워게임의 심장이다. 도스 시절 이 계산은 한 유닛을 고를 때마다
   즉시 끝나야 했다(286 에서 0.1초 안쪽). 그래서 두 가지를 지켰다.

     1. 비용이 아주 작은 정수다(1..6). 그러면 우선순위 큐가 필요 없다 —
        비용별 양동이(bucket)에 담아 순서대로 비우면 된다. Dial 의 알고리즘.
     2. 방문 표시는 해시가 아니라 맵과 같은 크기의 배열이다. 인덱스 한 번에
        읽고 쓴다.

   A* 는 여러 턴에 걸친 장거리 이동을 미리 그릴 때만 쓴다. 실제로 한 턴에
   갈 수 있는 범위는 언제나 양동이 큐로 구한다.
"""

import heapq

from .hexmap import T_MOVE, TERRAIN_MASK
from .units import NO_UNIT

UNREACHED = 0x7FFFFFFF
MIN_COST = 1          # 도로가 가장 싸다. A* 휴리스틱의 계수가 된다.


def zoc_mask(m, pool, side):
    """상대 유닛에 인접한 칸을 1로 칠한 맵 크기 배열. SPEC §6.2.

       매 이동마다 다시 만든다. 맵이 432칸이라 전부 훑어도 싸고, 증분 갱신은
       유닛이 죽거나 이동할 때마다 틀리기 쉬워 도스 게임들도 대개 다시 칠했다.
    """
    mask = bytearray(m.w * m.h)
    for u in pool.iter_alive():
        if u.side == side:
            continue
        i = m.axial_idx(u.q, u.r)
        if i < 0:
            continue
        for _d, ni in m.neighbors_with_dir(i):
            mask[ni] = 1
    return mask


def step_cost(m, pool, side, frm, to):
    """frm 에서 to 로 한 칸 들어가는 비용. 갈 수 없으면 -1. SPEC §6.1."""
    c = m.cells[to]
    mv = T_MOVE[c & TERRAIN_MASK]
    if mv < 0:
        return -1
    occ = m.occupant[to]
    if occ != NO_UNIT:
        return -1                      # 아군이든 적군이든 겹칠 수 없다
    if (m.cells[frm] & 0x80) and (c & 0x80):
        return 1                       # 도로에서 도로로 — 지형을 무시한다
    return mv


class Reach(object):
    """이동 범위 결과. 세 언어가 같은 모양을 갖도록 자료를 셋으로 나눠 담는다.

       cost[i]  i 칸까지 쓴 이동력
       came[i]  i 칸에 들어온 방향(0..5), 출발 칸은 -1
       list     인덱스 오름차순 목록 — 순회 순서를 언어에 맡기지 않기 위해서다.
                (루아의 pairs 는 순서를 보장하지 않는다. 순서가 결과를 바꾸는
                 자리를 하나라도 남기면 세 구현의 답이 갈린다.)
    """

    __slots__ = ('cost', 'came', 'list')

    def __init__(self, cost, came, lst):
        self.cost = cost
        self.came = came
        self.list = lst

    def has(self, i):
        return i in self.cost


def reachable(m, pool, unit):
    """이번 턴에 갈 수 있는 칸 전부를 Reach 로.

       Dial 의 양동이 큐 — O(V + E + maxMP). 힙이 없으니 비교 함수도, 로그도
       없다. 정점을 꺼내는 순서가 양동이 스캔 순서로 정해져 있어서 결과가
       완전히 결정적이다(골든 벡터에 담을 수 있는 이유).
    """
    start = m.axial_idx(unit.q, unit.r)
    budget = unit.mp
    if start < 0:
        return Reach({}, {}, [])
    if budget <= 0:
        return Reach({start: 0}, {start: -1}, [start])

    n = m.w * m.h
    best = [UNREACHED] * n
    came = [-1] * n
    best[start] = 0
    zoc = zoc_mask(m, pool, unit.side)
    buckets = [[] for _ in range(budget + 1)]
    buckets[0].append(start)

    for c in range(budget + 1):
        b = buckets[c]
        bi = 0
        while bi < len(b):
            cur = b[bi]
            bi += 1
            if best[cur] != c:
                continue                       # 더 싼 길로 이미 갱신됨
            if cur != start and zoc[cur]:
                continue                       # 적 ZOC 에 들어가면 거기서 끝
            for d, ni in m.neighbors_with_dir(cur):
                sc = step_cost(m, pool, unit.side, cur, ni)
                if sc < 0:
                    continue
                nc = c + sc
                if nc <= budget and nc < best[ni]:
                    best[ni] = nc
                    came[ni] = d
                    buckets[nc].append(ni)

    cost, cameo, lst = {}, {}, []
    for i in range(n):
        if best[i] != UNREACHED:
            cost[i] = best[i]
            cameo[i] = came[i]
            lst.append(i)
    return Reach(cost, cameo, lst)


def trace_path(m, reach, target):
    """reachable 결과에서 목표까지의 경로를 인덱스 목록으로 되짚는다.
       came[] 에 '들어온 방향'이 있으니 반대 방향으로 한 칸씩 되돌아가면 된다."""
    from .hexmap import NEIGHBOR_DELTA
    if not reach.has(target):
        return []
    path = [target]
    cur = target
    while True:
        d = reach.came[cur]
        if d < 0:
            break
        row, col = divmod(cur, m.w)
        # d 방향으로 들어왔으니, 되돌아가려면 반대 방향(d+3) 델타를 더한다
        back = NEIGHBOR_DELTA[row & 1][(d + 3) % 6]
        col += back[0]
        row += back[1]
        cur = row * m.w + col
        path.append(cur)
    path.reverse()
    return path


def astar(m, pool, side, start, goal):
    """여러 턴에 걸친 장거리 경로. 인덱스 목록(양 끝 포함), 못 가면 빈 목록.

       휴리스틱 h = 헥스거리 * MIN_COST 는 허용 가능(모든 걸음이 1 이상)하고
       일관적이다(삼각부등식). 그래서 닫힌 정점을 다시 열 필요가 없다.
       동점 처리를 위해 삽입 순번을 키에 넣는다 — 세 언어의 힙 구현이 달라도
       같은 답이 나오게 하는 장치다.
    """
    from . import hexcoord as H
    if start == goal:
        return [start]
    gq, gr = m.idx_axial(goal)
    n = m.w * m.h
    g = [UNREACHED] * n
    came_idx = [-1] * n
    g[start] = 0
    order = 0
    sq, sr = m.idx_axial(start)
    open_heap = [(H.distance(sq, sr, gq, gr) * MIN_COST, 0, start)]
    closed = bytearray(n)

    while open_heap:
        _f, _o, cur = heapq.heappop(open_heap)
        if closed[cur]:
            continue
        closed[cur] = 1
        if cur == goal:
            break
        for _d, ni in m.neighbors_with_dir(cur):
            if closed[ni]:
                continue
            sc = step_cost(m, pool, side, cur, ni)
            if sc < 0 and ni != goal:
                continue
            if sc < 0:
                continue
            ng = g[cur] + sc
            if ng < g[ni]:
                g[ni] = ng
                came_idx[ni] = cur
                nq, nr = m.idx_axial(ni)
                order += 1
                heapq.heappush(open_heap,
                               (ng + H.distance(nq, nr, gq, gr) * MIN_COST, order, ni))

    if g[goal] == UNREACHED:
        return []
    path = [goal]
    while path[-1] != start:
        path.append(came_idx[path[-1]])
    path.reverse()
    return path
