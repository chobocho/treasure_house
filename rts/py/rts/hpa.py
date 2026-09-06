# -*- coding: utf-8 -*-
"""계층 경로 탐색 — HPA* 2수준 (SPEC §9, Botea–Müller–Schaeffer 2004).

   **HPA* 는 최적이 아니다.** 원 논문이 보고하는 "최적 대비 1 % 안팎"은
   그 논문의 맵과 클러스터 크기에서 나온 값이다. 이 엔진의 값은 골든 맵에서
   직접 재어 out/py_prim.txt 8절에 남기고, 덱은 그 숫자만 쓴다.
"""

from . import fixed as F
from . import path as P

CLUSTER = 8


def cluster_of(x, y):
    return (x // CLUSTER, y // CLUSTER)


def intra(m, kind, a, b):
    """한 클러스터 안에서만 도는 A*. 8×8 이므로 최악 64칸이다."""
    cx, cy = cluster_of(a[0], a[1])
    lo_x, lo_y = cx * CLUSTER, cy * CLUSTER
    hi_x, hi_y = lo_x + CLUSTER - 1, lo_y + CLUSTER - 1
    dist = {a: 0}
    heap = P.Heap()
    order = {a: 0}
    heap.push(P.h_oct(a[0], a[1], b[0], b[1]), 0, 0)
    nodes = [a]
    closed = set()
    while len(heap):
        _f, _h, k = heap.pop()
        p = nodes[k]
        if p in closed:
            continue
        closed.add(p)
        if p == b:
            return dist[p]
        for d, u, v in P.neighbours(m, p[0], p[1], kind):
            if not (lo_x <= u <= hi_x and lo_y <= v <= hi_y):
                continue
            nd = dist[p] + F.DCOST[d]
            if nd < dist.get((u, v), P.INF):
                dist[(u, v)] = nd
                nodes.append((u, v))
                order[(u, v)] = len(nodes) - 1
                heap.push(nd + P.h_oct(u, v, b[0], b[1]), 0, len(nodes) - 1)
    return -1


def _place(run, mk):
    """SPEC §9.2 — 짧은 구간은 가운데 하나, 긴 구간은 양 끝 둘."""
    if not run:
        return []
    if len(run) <= 5:
        return [mk(run[(len(run) - 1) // 2])]
    return [mk(run[0]), mk(run[-1])]


def entrances(m, kind):
    """클러스터 경계에서 양쪽이 모두 통행 가능한 연속 구간을 찾아 전이를 만든다."""
    edges = []
    for cy in range(m.h // CLUSTER):
        for cx in range(m.w // CLUSTER):
            if cx + 1 < m.w // CLUSTER:
                x = cx * CLUSTER + CLUSTER - 1
                run = []
                for y in range(cy * CLUSTER, cy * CLUSTER + CLUSTER):
                    if (m.passable_terrain(x, y, kind)
                            and m.passable_terrain(x + 1, y, kind)):
                        run.append(y)
                    else:
                        edges += _place(run, lambda yy, x=x: ((x, yy), (x + 1, yy)))
                        run = []
                edges += _place(run, lambda yy, x=x: ((x, yy), (x + 1, yy)))
            if cy + 1 < m.h // CLUSTER:
                y = cy * CLUSTER + CLUSTER - 1
                run = []
                for x in range(cx * CLUSTER, cx * CLUSTER + CLUSTER):
                    if (m.passable_terrain(x, y, kind)
                            and m.passable_terrain(x, y + 1, kind)):
                        run.append(x)
                    else:
                        edges += _place(run, lambda xx, y=y: ((xx, y), (xx, y + 1)))
                        run = []
                edges += _place(run, lambda xx, y=y: ((xx, y), (xx, y + 1)))
    return edges


class Abstract(object):
    """추상 그래프. 맵 버전이 바뀌면 다시 짓는다."""

    def __init__(self, m, kind):
        self.version = m.version
        self.kind = kind
        self.graph = {}
        self.by_cluster = {}
        nodes = set()
        for a, b in entrances(m, kind):
            nodes.add(a)
            nodes.add(b)
            self.graph.setdefault(a, []).append((b, F.D_STRAIGHT))
            self.graph.setdefault(b, []).append((a, F.D_STRAIGHT))
        for n in nodes:
            self.by_cluster.setdefault(cluster_of(n[0], n[1]), []).append(n)
        for c in self.by_cluster:
            ns = sorted(self.by_cluster[c])
            self.by_cluster[c] = ns
            for i in range(len(ns)):
                for j in range(i + 1, len(ns)):
                    c1 = intra(m, kind, ns[i], ns[j])
                    if c1 >= 0:
                        self.graph.setdefault(ns[i], []).append((ns[j], c1))
                        self.graph.setdefault(ns[j], []).append((ns[i], c1))


_cache = {}


def abstract(m, kind):
    key = (id(m), kind)
    a = _cache.get(key)
    if a is None or a.version != m.version:
        a = Abstract(m, kind)
        _cache[key] = a
    return a


def search(m, kind, s, t):
    """추상 그래프 위의 A*. 정련 경로의 비용은 추상 비용과 같다."""
    if not (m.passable_terrain(s[0], s[1], kind)
            and m.passable_terrain(t[0], t[1], kind)):
        return -1, []
    ab = abstract(m, kind)
    graph = dict((k, list(v)) for k, v in ab.graph.items())
    for temp in (s, t):                       # 임시 노드 삽입 (질의가 끝나면 버린다)
        for n in ab.by_cluster.get(cluster_of(temp[0], temp[1]), []):
            c1 = intra(m, kind, temp, n)
            if c1 >= 0:
                graph.setdefault(temp, []).append((n, c1))
                graph.setdefault(n, []).append((temp, c1))
    if cluster_of(s[0], s[1]) == cluster_of(t[0], t[1]):
        c1 = intra(m, kind, s, t)
        if c1 >= 0:
            graph.setdefault(s, []).append((t, c1))

    dist = {s: 0}
    prev = {}
    closed = set()
    heap = P.Heap()
    nodes = [s]
    heap.push(P.h_oct(s[0], s[1], t[0], t[1]), 0, 0)
    while len(heap):
        _f, _h, k = heap.pop()
        p = nodes[k]
        if p in closed:
            continue
        closed.add(p)
        if p == t:
            out = [p]
            while out[-1] in prev:
                out.append(prev[out[-1]])
            out.reverse()
            return dist[p], out
        for n, c1 in graph.get(p, []):
            nd = dist[p] + c1
            if nd < dist.get(n, P.INF):
                dist[n] = nd
                prev[n] = p
                nodes.append(n)
                heap.push(nd + P.h_oct(n[0], n[1], t[0], t[1]), 0, len(nodes) - 1)
    return -1, []


def refine(m, kind, absnodes):
    """추상 경로의 인접 노드 쌍을 클러스터 안 A* 로 실제 타일 열로 편다."""
    out = []
    for i in range(len(absnodes) - 1):
        a, b = absnodes[i], absnodes[i + 1]
        if cluster_of(a[0], a[1]) == cluster_of(b[0], b[1]):
            _c, tiles, _n = P.astar(m, kind, a, b)
        else:
            tiles = [a[1] * m.w + a[0], b[1] * m.w + b[0]]
        if out and tiles and out[-1] == tiles[0]:
            tiles = tiles[1:]
        out += tiles
    return out
