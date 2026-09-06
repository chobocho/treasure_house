# -*- coding: utf-8 -*-
"""경로 탐색 — BFS·다익스트라(양동이 큐)·A*(이진 힙) (SPEC §8).

   코너 컷은 **허용한다**. 대각 이동은 도착 칸만 본다. 선택이며, 그 이유와
   대가는 SPEC §8.1 에 적어 두었다 — 요약하면 JPS 의 가지치기 규칙이
   코너 컷 격자 위에서 정의되어 있기 때문이다.

   경로 탐색은 점유 비트를 보지 않는다(SPEC §4.3). 움직이는 유닛 때문에
   경로가 매 틱 흔들리면 무리 이동이 통째로 무너진다.
"""

from . import fixed as F

INF = 1 << 30
NB = F.D_DIAG + 1                 # 양동이 15개 — 최대 간선 비용보다 커야 한다


def h_oct(ax, ay, bx, by):
    """옥타일 휴리스틱 = 10*max + 4*min. 허용적이고 일관적이다 (SPEC 정리 8.1/8.2)."""
    return F.doct(ax - bx, ay - by)


def neighbours(m, x, y, kind):
    """(방향, u, v) — 코너 컷 허용이므로 도착 칸만 검사한다."""
    for d in range(8):
        u, v = x + F.DX[d], y + F.DY[d]
        if m.passable_terrain(u, v, kind):
            yield d, u, v


# ── BFS ─────────────────────────────────────────────────────────────────────
def bfs(m, kind, s, t):
    """걸음 수(가중치 없음). 대각도 한 걸음이다."""
    if not (m.passable_terrain(s[0], s[1], kind)
            and m.passable_terrain(t[0], t[1], kind)):
        return -1
    w = m.w
    seen = [-1] * (w * m.h)
    si = s[1] * w + s[0]
    seen[si] = 0
    q = [si]
    head = 0
    while head < len(q):
        p = q[head]
        head += 1
        x, y = p % w, p // w
        if (x, y) == t:
            return seen[p]
        for _d, u, v in neighbours(m, x, y, kind):
            j = v * w + u
            if seen[j] < 0:
                seen[j] = seen[p] + 1
                q.append(j)
    return -1


# ── SPEC §8.4 다익스트라 (Dial 양동이 큐) ───────────────────────────────────
def dijkstra(m, kind, starts, goal=None):
    """모든 칸까지의 비용 배열. 간선 비용이 10 과 14 뿐이라 힙이 필요 없다.

       정리 8.3 이 보장한다 — 처리 중인 거리 cur 와 새 거리 nd 는 항상
       cur <= nd < cur + 15 이므로 원형 양동이 15개면 충돌하지 않는다.
    """
    w, h = m.w, m.h
    dist = [INF] * (w * h)
    buckets = [[] for _ in range(NB)]
    pending = 0
    for s in starts:
        if dist[s] > 0:
            dist[s] = 0
            buckets[0].append(s)
            pending += 1
    cur = 0
    while pending:
        b = buckets[cur % NB]
        while not b:
            cur += 1
            b = buckets[cur % NB]
        p = b.pop()
        pending -= 1
        if dist[p] != cur:                 # 낡은 항목 — 감소키를 구현하지 않는다
            continue
        if goal is not None and p == goal:
            return dist
        x, y = p % w, p // w
        for d, u, v in neighbours(m, x, y, kind):
            j = v * w + u
            nd = cur + F.DCOST[d]
            if nd < dist[j]:
                dist[j] = nd
                buckets[nd % NB].append(j)
                pending += 1
    return dist


# ── SPEC §8.5 A* (손으로 쓴 이진 힙) ────────────────────────────────────────
class Heap(object):
    """(f, h, idx) 사전식 최소 힙.

       파이썬 heapq · 루아 table.sort · 자바스크립트 Array.sort 는 서로 다른
       순서를 낼 수 있다. 비교자가 전순서이기만 하면 손으로 쓴 힙이 세 언어에서
       같은 순서로 뽑는다 — 그래서 손으로 쓴다.
    """

    def __init__(self):
        self.a = []

    def __len__(self):
        return len(self.a)

    def push(self, f, hh, idx):
        a = self.a
        a.append((f, hh, idx))
        i = len(a) - 1
        while i > 0:
            p = (i - 1) // 2
            if a[p] <= a[i]:
                break
            a[p], a[i] = a[i], a[p]
            i = p

    def pop(self):
        a = self.a
        top = a[0]
        last = a.pop()
        if a:
            a[0] = last
            i, n = 0, len(a)
            while True:
                l, r = 2 * i + 1, 2 * i + 2
                s = i
                if l < n and a[l] < a[s]:
                    s = l
                if r < n and a[r] < a[s]:
                    s = r
                if s == i:
                    break
                a[s], a[i] = a[i], a[s]
                i = s
        return top


def astar(m, kind, s, t):
    """(비용, 경로 타일 목록, 연 노드 수). 도달 불가면 (-1, [], n)."""
    w = m.w
    if not (m.passable_terrain(s[0], s[1], kind)
            and m.passable_terrain(t[0], t[1], kind)):
        return -1, [], 0
    si, ti = s[1] * w + s[0], t[1] * w + t[0]
    dist = {si: 0}
    prev = {}
    closed = set()
    heap = Heap()
    h0 = h_oct(s[0], s[1], t[0], t[1])
    heap.push(h0, h0, si)
    expanded = 0
    while len(heap):
        _f, _hh, p = heap.pop()
        if p in closed:
            continue
        closed.add(p)                      # 일관적이므로 재개방하지 않는다
        expanded += 1
        if p == ti:
            out = [p]
            while out[-1] != si:
                out.append(prev[out[-1]])
            out.reverse()
            return dist[p], out, expanded
        x, y = p % w, p // w
        for d, u, v in neighbours(m, x, y, kind):
            j = v * w + u
            nd = dist[p] + F.DCOST[d]
            if nd < dist.get(j, INF):
                dist[j] = nd
                prev[j] = p
                hn = h_oct(u, v, t[0], t[1])
                heap.push(nd + hn, hn, j)
    return -1, [], expanded


# ── SPEC §8.6 도달 불가 목표 ────────────────────────────────────────────────
def closest_reachable(m, kind, s, t):
    """목표가 다른 성분이면 같은 성분에서 목표에 가장 가까운 칸으로 바꾼다.

       이 한 줄이 없으면 '섬 건너편 클릭' 한 번이 A* 에게 맵 전체를 펴게 한다.
    """
    lab = m.labels(kind)
    si = s[1] * m.w + s[0]
    ti = t[1] * m.w + t[0]
    if lab[si] < 0:
        return None
    if lab[ti] == lab[si]:
        return t
    best, bd, bi = None, INF, INF
    for i in range(m.w * m.h):
        if lab[i] != lab[si]:
            continue
        x, y = i % m.w, i // m.w
        d = F.d83(x - t[0], y - t[1])
        if d < bd or (d == bd and i < bi):
            best, bd, bi = (x, y), d, i
    return best


# ── SPEC §8.7 경로 캐시 ─────────────────────────────────────────────────────
class Cache(object):
    """64칸 LRU. 지형이 바뀌면 통째로 비운다 — 낡은 경로는 곧 디싱크다.

       LRU 순서는 상태가 아니다(해시에 넣지 않는다). 캐시는 같은 답을 더 빨리
       줄 뿐이고, 다른 답을 주면 그것은 버그다.
    """

    LIMIT = 64

    def __init__(self):
        self.map_version = -1
        self.data = {}
        self.order = []
        self.hits = 0
        self.misses = 0

    def get(self, m, key):
        if m.version != self.map_version:
            self.map_version = m.version
            self.data = {}
            self.order = []
        if key in self.data:
            self.hits += 1
            self.order.remove(key)
            self.order.append(key)
            return self.data[key]
        self.misses += 1
        return None

    def put(self, key, value):
        if key in self.data:
            self.order.remove(key)
        elif len(self.order) >= self.LIMIT:
            del self.data[self.order.pop(0)]
        self.data[key] = value
        self.order.append(key)


def find(m, kind, s, t, cache=None):
    """캐시를 거치는 표준 경로 질의. 목표가 닿지 않으면 대체 목표로 바꾼다."""
    goal = closest_reachable(m, kind, s, t)
    if goal is None:
        return -1, []
    key = (s[1] * m.w + s[0], goal[1] * m.w + goal[0], kind)
    if cache is not None:
        hit = cache.get(m, key)
        if hit is not None:
            return hit
    cost, tiles, _n = astar(m, kind, s, goal)
    if cache is not None:
        cache.put(key, (cost, tiles))
    return cost, tiles
