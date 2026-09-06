# -*- coding: utf-8 -*-
"""점프 포인트 탐색 — Harabor & Grastien 2011 (SPEC §10).

   격자의 대칭 경로를 가지치기해 A* 가 여는 노드 수를 줄인다. 비용은 A* 와
   **정확히 같다**. 그 등가성을 정리로 옮겨 적는 대신 전수 검사로 증명한다
   (py/tests/test_jps.py).

   여기 있는 가지치기 규칙은 **코너 컷을 허용하는 격자**의 것이다. 금지하면
   강제 이웃 조건이 통째로 달라진다 — 그것이 SPEC §8.1 에서 코너 컷을
   허용하기로 한 첫 번째 이유다.
"""

from . import fixed as F
from . import path as P


def _forced(m, x, y, dx, dy, kind):
    """(x,y) 에 방향 (dx,dy) 로 들어왔을 때 강제 이웃이 있는가 (SPEC §10.1)."""
    ok = m.passable_terrain
    if dx and dy:
        return ((not ok(x - dx, y, kind) and ok(x - dx, y + dy, kind)) or
                (not ok(x, y - dy, kind) and ok(x + dx, y - dy, kind)))
    if dx:
        for s in (-1, 1):
            if not ok(x, y + s, kind) and ok(x + dx, y + s, kind):
                return True
        return False
    for s in (-1, 1):
        if not ok(x + s, y, kind) and ok(x + s, y + dy, kind):
            return True
    return False


def jump(m, x, y, dx, dy, t, kind):
    """방향 (dx,dy) 로 계속 나아가다 점프점을 만나면 그 칸을 돌려준다.

       대각 점프가 먼저 두 성분 방향을 재귀로 훑는 것이 핵심이다. 그 방향에서
       점프점이 나오면 지금 서 있는 대각 칸 자체가 점프점이 된다.
    """
    u, v = x + dx, y + dy
    if not m.passable_terrain(u, v, kind):
        return None
    if (u, v) == t:
        return (u, v)
    if _forced(m, u, v, dx, dy, kind):
        return (u, v)
    if dx and dy:
        if (jump(m, u, v, dx, 0, t, kind) is not None or
                jump(m, u, v, 0, dy, t, kind) is not None):
            return (u, v)
    return jump(m, u, v, dx, dy, t, kind)


def _prune(m, x, y, parent, kind):
    """부모에서 온 방향에 따라 살아남는 이웃 방향들 (SPEC §10.1)."""
    ok = m.passable_terrain
    if parent is None:
        return [(F.DX[d], F.DY[d]) for d in range(8)
                if ok(x + F.DX[d], y + F.DY[d], kind)]
    px, py = parent
    dx = (x - px > 0) - (x - px < 0)
    dy = (y - py > 0) - (y - py < 0)
    out = []
    if dx and dy:
        if ok(x + dx, y, kind):
            out.append((dx, 0))
        if ok(x, y + dy, kind):
            out.append((0, dy))
        if ok(x + dx, y + dy, kind):
            out.append((dx, dy))
        if not ok(x - dx, y, kind) and ok(x - dx, y + dy, kind):
            out.append((-dx, dy))
        if not ok(x, y - dy, kind) and ok(x + dx, y - dy, kind):
            out.append((dx, -dy))
    elif dx:
        if ok(x + dx, y, kind):
            out.append((dx, 0))
        for s in (-1, 1):
            if not ok(x, y + s, kind) and ok(x + dx, y + s, kind):
                out.append((dx, s))
    else:
        if ok(x, y + dy, kind):
            out.append((0, dy))
        for s in (-1, 1):
            if not ok(x + s, y, kind) and ok(x + s, y + dy, kind):
                out.append((s, dy))
    return out


def search(m, kind, s, t):
    """(비용, 점프점 목록, 연 노드 수). A* 와 같은 비교자·같은 힙을 쓴다."""
    w = m.w
    if not (m.passable_terrain(s[0], s[1], kind)
            and m.passable_terrain(t[0], t[1], kind)):
        return -1, [], 0
    si, ti = s[1] * w + s[0], t[1] * w + t[0]
    dist = {si: 0}
    parent = {si: None}
    closed = set()
    heap = P.Heap()
    h0 = P.h_oct(s[0], s[1], t[0], t[1])
    heap.push(h0, h0, si)
    expanded = 0
    while len(heap):
        _f, _hh, p = heap.pop()
        if p in closed:
            continue
        closed.add(p)
        expanded += 1
        x, y = p % w, p // w
        if p == ti:
            out = [p]
            while parent[out[-1]] is not None:
                q = parent[out[-1]]
                out.append(q[1] * w + q[0])
            out.reverse()
            return dist[p], out, expanded
        par = parent[p]
        for dx, dy in _prune(m, x, y, par, kind):
            n = jump(m, x, y, dx, dy, t, kind)
            if n is None:
                continue
            steps = max(abs(n[0] - x), abs(n[1] - y))
            nd = dist[p] + steps * (F.D_DIAG if (dx and dy) else F.D_STRAIGHT)
            j = n[1] * w + n[0]
            if nd < dist.get(j, P.INF):
                dist[j] = nd
                parent[j] = (x, y)
                hn = P.h_oct(n[0], n[1], t[0], t[1])
                heap.push(nd + hn, hn, j)
    return -1, [], expanded
