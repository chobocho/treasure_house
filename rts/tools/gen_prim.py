# -*- coding: utf-8 -*-
"""프리미티브 보고서의 기준값을 만든다 — golden/prim.txt (그리고 out/analysis.txt)

   여기 있는 것은 **엔진과 독립된 참조 구현**이다. 엔진(py/rts)을 import 하지
   않는다. 그래야 "둘 다 같은 실수를 했다"는 사고가 생기지 않는다.

   golden/prim.txt 는 세 언어의 `main prim` 이 바이트 단위로 재현해야 하는 파일이며,
   따라서 **정수만** 들어간다. 부동소수점이 필요한 분석(오차율·란체스터 폐형해·
   음정 센트)은 out/analysis.txt 에 따로 쓰고, 덱에서만 인용한다.

   실행:  python3 tools/gen_prim.py
"""
import io
import math
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLDEN = os.path.join(BASE, 'golden')
OUT = os.path.join(BASE, 'out')

# ── SPEC §0 상수 ────────────────────────────────────────────────────────────
FP_ONE = 65536
D_STRAIGHT, D_DIAG = 10, 14
PIT_HZ = 1193182
FNV_OFFSET, FNV_PRIME = 2166136261, 16777619
CLUSTER = 8

# SPEC §2.7 의 방향 번호: 0=N 1=NE 2=E 3=SE 4=S 5=SW 6=W 7=NW  (y 는 아래로 증가)
DX = [0, 1, 1, 1, 0, -1, -1, -1]
DY = [-1, -1, 0, 1, 1, 1, 0, -1]
DNAME = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
DCOST = [D_STRAIGHT, D_DIAG, D_STRAIGHT, D_DIAG,
         D_STRAIGHT, D_DIAG, D_STRAIGHT, D_DIAG]


# ── SPEC §3 난수 ────────────────────────────────────────────────────────────
class LCG(object):
    def __init__(self, seed):
        self.s = seed
        self.rejects = 0

    def next15(self):
        self.s = (22695477 * self.s + 1) % 4294967296
        return (self.s // 65536) % 32768

    def roll(self, n):
        if n <= 1:
            return 0
        limit = 32768 - 32768 % n
        while True:
            r = self.next15()
            if r < limit:
                return r % n
            self.rejects += 1


# ── SPEC §2.6 거리 척도 ─────────────────────────────────────────────────────
def metrics(dx, dy):
    ax, ay = abs(dx), abs(dy)
    mx, mn = max(ax, ay), min(ax, ay)
    return dict(
        d1=ax + ay,
        dinf=mx,
        d83=mx + 3 * mn // 8,
        dab=(62943 * mx + 26072 * mn + 32768) // FP_ONE,
        doct=D_STRAIGHT * mx + (D_DIAG - D_STRAIGHT) * mn,
        eu3=math.isqrt((dx * dx + dy * dy) * 1000000),
    )


def atan8(dx, dy):
    """비교만으로 8방향을 고른다 (SPEC §2.7). tan 22.5° ≈ 5/12."""
    if dx == 0 and dy == 0:
        return 2
    ax, ay = abs(dx), abs(dy)
    mx, mn = max(ax, ay), min(ax, ay)
    diag = 12 * mn > 5 * mx
    if ax >= ay:                       # 동서가 주축
        if dx > 0:
            return 1 if (diag and dy < 0) else (3 if (diag and dy > 0) else 2)
        return 7 if (diag and dy < 0) else (5 if (diag and dy > 0) else 6)
    if dy < 0:
        return 1 if (diag and dx > 0) else (7 if (diag and dx < 0) else 0)
    return 3 if (diag and dx > 0) else (5 if (diag and dx < 0) else 4)


# ── SPEC §4.4 오토타일 ──────────────────────────────────────────────────────
CORNERS = ((1, 0, 2), (3, 4, 2), (5, 4, 6), (7, 0, 6))   # (모서리, 변, 변) 방향번호


def canon(m):
    r = m
    for c, a, b in CORNERS:
        if not (m >> a & 1 and m >> b & 1):
            r &= ~(1 << c)
    return r


# ── SPEC §6.2 원 마스크 ─────────────────────────────────────────────────────
def disc_spans(r):
    span = [0] * (r + 1)
    span[0] = r
    x, t = r, 0
    for j in range(1, r + 1):
        t -= 2 * (j - 1) + 1
        while t < 0:
            t += 2 * x - 1
            x -= 1
        span[j] = x
    return span


def disc_offsets(r):
    span = disc_spans(r)
    out = []
    for j in range(-r, r + 1):
        for i in range(-span[abs(j)], span[abs(j)] + 1):
            out.append((i, j))
    out.sort(key=lambda p: (p[1], p[0]))
    return out


# ── 맵 ──────────────────────────────────────────────────────────────────────
class Grid(object):
    def __init__(self, name, rows, pairs):
        self.name, self.rows = name, rows
        self.h, self.w = len(rows), len(rows[0])
        self.pairs = pairs

    def free(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h and self.rows[y][x] == '.'


def load_map(path):
    lines = io.open(path, encoding='utf-8').read().split('\n')
    name, rows, pairs, i = '', [], [], 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith('name '):
            name = ln[5:]
        elif ln.startswith('size '):
            w, h = (int(v) for v in ln[5:].split())
        elif ln == 'map':
            rows = lines[i + 1:i + 1 + h]
            i += h
        elif ln.startswith('pairs '):
            n = int(ln[6:])
            for k in range(n):
                a, b, c, d = (int(v) for v in lines[i + 1 + k].split())
                pairs.append(((a, b), (c, d)))
            i += n
        i += 1
    return Grid(name, rows, pairs)


# ── SPEC §8 경로 탐색 (참조 구현: 느리고 단순하게) ──────────────────────────
def neighbours(g, x, y):
    """코너 컷 허용 — 도착 칸만 본다 (SPEC §8.1)."""
    for d in range(8):
        u, v = x + DX[d], y + DY[d]
        if g.free(u, v):
            yield d, u, v


def bfs_steps(g, s, t):
    from collections import deque
    if not (g.free(*s) and g.free(*t)):
        return -1
    seen = {s: 0}
    q = deque([s])
    while q:
        x, y = q.popleft()
        if (x, y) == t:
            return seen[(x, y)]
        for _d, u, v in neighbours(g, x, y):
            if (u, v) not in seen:
                seen[(u, v)] = seen[(x, y)] + 1
                q.append((u, v))
    return -1


def dijkstra_cost(g, s, t):
    import heapq
    if not (g.free(*s) and g.free(*t)):
        return -1
    dist = {s: 0}
    pq = [(0, s)]
    while pq:
        c, p = heapq.heappop(pq)
        if c > dist.get(p, 1 << 30):
            continue
        if p == t:
            return c
        for d, u, v in neighbours(g, p[0], p[1]):
            nc = c + DCOST[d]
            if nc < dist.get((u, v), 1 << 30):
                dist[(u, v)] = nc
                heapq.heappush(pq, (nc, (u, v)))
    return -1


def h_oct(a, b):
    dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
    return D_STRAIGHT * max(dx, dy) + (D_DIAG - D_STRAIGHT) * min(dx, dy)


def astar(g, s, t):
    """(비용, 연 노드 수). 비교자는 (f, h, idx) 사전식 — SPEC §8.5."""
    import heapq
    if not (g.free(*s) and g.free(*t)):
        return -1, 0
    idx = lambda p: p[1] * g.w + p[0]
    dist = {s: 0}
    pq = [(h_oct(s, t), h_oct(s, t), idx(s), s)]
    closed = set()
    expanded = 0
    while pq:
        f, hh, _i, p = heapq.heappop(pq)
        if p in closed:
            continue
        closed.add(p)
        expanded += 1
        if p == t:
            return dist[p], expanded
        for d, u, v in neighbours(g, p[0], p[1]):
            nc = dist[p] + DCOST[d]
            if nc < dist.get((u, v), 1 << 30):
                dist[(u, v)] = nc
                hn = h_oct((u, v), t)
                heapq.heappush(pq, (nc + hn, hn, idx((u, v)), (u, v)))
    return -1, expanded


# ── SPEC §10 JPS ────────────────────────────────────────────────────────────
def _forced(g, x, y, dx, dy):
    if dx and dy:
        return ((not g.free(x - dx, y) and g.free(x - dx, y + dy)) or
                (not g.free(x, y - dy) and g.free(x + dx, y - dy)))
    if dx:
        return any(not g.free(x, y + t) and g.free(x + dx, y + t) for t in (-1, 1))
    return any(not g.free(x + t, y) and g.free(x + t, y + dy) for t in (-1, 1))


def _jump(g, x, y, dx, dy, t):
    u, v = x + dx, y + dy
    if not g.free(u, v):
        return None
    if (u, v) == t:
        return (u, v)
    if _forced(g, u, v, dx, dy):
        return (u, v)
    if dx and dy:
        if (_jump(g, u, v, dx, 0, t) is not None or
                _jump(g, u, v, 0, dy, t) is not None):
            return (u, v)
    return _jump(g, u, v, dx, dy, t)


def _prune(g, p, parent):
    x, y = p
    if parent is None:
        return [(DX[d], DY[d]) for d in range(8) if g.free(x + DX[d], y + DY[d])]
    dx = (x - parent[0] > 0) - (x - parent[0] < 0)
    dy = (y - parent[1] > 0) - (y - parent[1] < 0)
    out = []
    if dx and dy:
        if g.free(x + dx, y):
            out.append((dx, 0))
        if g.free(x, y + dy):
            out.append((0, dy))
        if g.free(x + dx, y + dy):
            out.append((dx, dy))
        if not g.free(x - dx, y) and g.free(x - dx, y + dy):
            out.append((-dx, dy))
        if not g.free(x, y - dy) and g.free(x + dx, y - dy):
            out.append((dx, -dy))
    elif dx:
        if g.free(x + dx, y):
            out.append((dx, 0))
        for s in (-1, 1):
            if not g.free(x, y + s) and g.free(x + dx, y + s):
                out.append((dx, s))
    else:
        if g.free(x, y + dy):
            out.append((0, dy))
        for s in (-1, 1):
            if not g.free(x + s, y) and g.free(x + s, y + dy):
                out.append((s, dy))
    return out


def jps(g, s, t):
    """(비용, 연 점프점 수). 코너 컷 허용 격자에서 A* 와 같은 비용을 내야 한다."""
    import heapq
    if not (g.free(*s) and g.free(*t)):
        return -1, 0
    idx = lambda p: p[1] * g.w + p[0]
    dist = {s: 0}
    parent = {s: None}
    pq = [(h_oct(s, t), h_oct(s, t), idx(s), s)]
    closed = set()
    expanded = 0
    while pq:
        _f, _h, _i, p = heapq.heappop(pq)
        if p in closed:
            continue
        closed.add(p)
        expanded += 1
        if p == t:
            return dist[p], expanded
        for dx, dy in _prune(g, p, parent[p]):
            n = _jump(g, p[0], p[1], dx, dy, t)
            if n is None:
                continue
            steps = max(abs(n[0] - p[0]), abs(n[1] - p[1]))
            nc = dist[p] + steps * (D_DIAG if (dx and dy) else D_STRAIGHT)
            if nc < dist.get(n, 1 << 30):
                dist[n] = nc
                parent[n] = p
                hn = h_oct(n, t)
                heapq.heappush(pq, (nc + hn, hn, idx(n), n))
    return -1, expanded


# ── SPEC §9 HPA* ────────────────────────────────────────────────────────────
def _cluster_of(x, y):
    return (x // CLUSTER, y // CLUSTER)


def _intra(g, a, b):
    """클러스터 안에서만 도는 A*. 같은 클러스터에 있어야 한다."""
    import heapq
    cx, cy = _cluster_of(*a)
    lo_x, lo_y = cx * CLUSTER, cy * CLUSTER
    hi_x, hi_y = lo_x + CLUSTER - 1, lo_y + CLUSTER - 1
    dist = {a: 0}
    pq = [(h_oct(a, b), a)]
    closed = set()
    while pq:
        _f, p = heapq.heappop(pq)
        if p in closed:
            continue
        closed.add(p)
        if p == b:
            return dist[p]
        for d, u, v in neighbours(g, p[0], p[1]):
            if not (lo_x <= u <= hi_x and lo_y <= v <= hi_y):
                continue
            nc = dist[p] + DCOST[d]
            if nc < dist.get((u, v), 1 << 30):
                dist[(u, v)] = nc
                heapq.heappush(pq, (nc + h_oct((u, v), b), (u, v)))
    return -1


def _entrances(g):
    """SPEC §9.2 — 클러스터 경계의 연속 구간에서 전이를 만든다."""
    edges = []            # ((x,y) 왼쪽/위, (x,y) 오른쪽/아래)
    for cy in range(g.h // CLUSTER):
        for cx in range(g.w // CLUSTER):
            if cx + 1 < g.w // CLUSTER:                 # 세로 경계
                x = cx * CLUSTER + CLUSTER - 1
                run = []
                for y in range(cy * CLUSTER, cy * CLUSTER + CLUSTER):
                    if g.free(x, y) and g.free(x + 1, y):
                        run.append(y)
                    else:
                        edges += _place(run, lambda yy: ((x, yy), (x + 1, yy)))
                        run = []
                edges += _place(run, lambda yy: ((x, yy), (x + 1, yy)))
            if cy + 1 < g.h // CLUSTER:                 # 가로 경계
                y = cy * CLUSTER + CLUSTER - 1
                run = []
                for x in range(cx * CLUSTER, cx * CLUSTER + CLUSTER):
                    if g.free(x, y) and g.free(x, y + 1):
                        run.append(x)
                    else:
                        edges += _place(run, lambda xx: ((xx, y), (xx, y + 1)))
                        run = []
                edges += _place(run, lambda xx: ((xx, y), (xx, y + 1)))
    return edges


def _place(run, mk):
    if not run:
        return []
    if len(run) <= 5:
        return [mk(run[(0 + len(run) - 1) // 2])]
    return [mk(run[0]), mk(run[-1])]


def hpa(g, s, t):
    """추상 그래프 위의 A*. 정련 경로의 비용은 추상 비용과 같다."""
    import heapq
    if not (g.free(*s) and g.free(*t)):
        return -1
    trans = _entrances(g)
    nodes = set()
    graph = {}
    for a, b in trans:
        nodes.add(a)
        nodes.add(b)
        graph.setdefault(a, []).append((b, D_STRAIGHT))
        graph.setdefault(b, []).append((a, D_STRAIGHT))
    by_cluster = {}
    for n in nodes:
        by_cluster.setdefault(_cluster_of(*n), []).append(n)
    for c, ns in by_cluster.items():
        ns.sort()
        for i in range(len(ns)):
            for j in range(i + 1, len(ns)):
                c1 = _intra(g, ns[i], ns[j])
                if c1 >= 0:
                    graph.setdefault(ns[i], []).append((ns[j], c1))
                    graph.setdefault(ns[j], []).append((ns[i], c1))
    for temp in (s, t):                       # 임시 노드 삽입
        for n in by_cluster.get(_cluster_of(*temp), []):
            c1 = _intra(g, temp, n)
            if c1 >= 0:
                graph.setdefault(temp, []).append((n, c1))
                graph.setdefault(n, []).append((temp, c1))
    if _cluster_of(*s) == _cluster_of(*t):
        c1 = _intra(g, s, t)
        if c1 >= 0:
            graph.setdefault(s, []).append((t, c1))
    dist = {s: 0}
    pq = [(h_oct(s, t), s)]
    closed = set()
    while pq:
        _f, p = heapq.heappop(pq)
        if p in closed:
            continue
        closed.add(p)
        if p == t:
            return dist[p]
        for n, c1 in graph.get(p, []):
            nc = dist[p] + c1
            if nc < dist.get(n, 1 << 30):
                dist[n] = nc
                heapq.heappush(pq, (nc + h_oct(n, t), n))
    return -1


# ── SPEC §11 흐름장·클리어런스 ──────────────────────────────────────────────
FLOWMAP = [
    '............',
    '.##########.',
    '.#........#.',
    '.#.######.#.',
    '.#.#....#.#.',
    '.#.#.##.#.#.',
    '.#.#.##.#.#.',
    '.#.#....#.#.',
    '.#.######.#.',
    '.#........#.',
    '.##########.',
    '............',
]


def integration(g, goals):
    import heapq
    INF = 65535
    integ = [[INF] * g.w for _ in range(g.h)]
    pq = []
    for (x, y) in goals:
        integ[y][x] = 0
        heapq.heappush(pq, (0, x, y))
    while pq:
        c, x, y = heapq.heappop(pq)
        if c > integ[y][x]:
            continue
        for d, u, v in neighbours(g, x, y):
            nc = c + DCOST[d]
            if nc < integ[v][u]:
                integ[v][u] = nc
                heapq.heappush(pq, (nc, u, v))
    return integ


def flow_dirs(g, integ):
    INF = 65535
    out = [[255] * g.w for _ in range(g.h)]
    for y in range(g.h):
        for x in range(g.w):
            if not g.free(x, y) or integ[y][x] == INF:
                continue
            best, bd = INF, 255
            for d in range(8):
                u, v = x + DX[d], y + DY[d]
                if g.free(u, v) and integ[v][u] < best:
                    best, bd = integ[v][u], d
            out[y][x] = bd
    return out


def clearance(g):
    c = [[0] * g.w for _ in range(g.h)]
    for y in range(g.h - 1, -1, -1):
        for x in range(g.w - 1, -1, -1):
            if not g.free(x, y):
                c[y][x] = 0
            elif x + 1 >= g.w or y + 1 >= g.h:
                c[y][x] = 1
            else:
                c[y][x] = 1 + min(c[y][x + 1], c[y + 1][x], c[y + 1][x + 1])
    return c


# ── SPEC §20.1 CRC · §18.4 FNV ──────────────────────────────────────────────
def crc16(data):
    c = 0xFFFF
    for b in bytearray(data):
        c ^= b << 8
        for _ in range(8):
            c = ((c << 1) ^ 0x1021) & 0xFFFF if c & 0x8000 else (c << 1) & 0xFFFF
    return c


def fnv1a(data):
    h = FNV_OFFSET
    for b in bytearray(data):
        h = ((h ^ b) * FNV_PRIME) % 4294967296
    return h


# ── 보고서 ──────────────────────────────────────────────────────────────────
PAIRS_M = [(1, 0), (0, 1), (1, 1), (2, 1), (3, 1), (3, 2), (4, 3), (5, 5),
           (8, 3), (10, 0), (10, 10), (-7, 4), (-6, -6), (0, -9), (12, -5), (-3, 11)]
SQ_N = [0, 1, 2, 3, 15, 16, 17, 99, 100, 65535, 65536, 1000000, 2147483647]
ANG_V = [(12, 5), (12, -5), (12, 6), (5, 12), (12, 4), (-12, 5), (-5, -12), (0, 0),
         (1, 0), (0, -1), (7, 3), (3, 7), (-9, -4), (4, -9), (100, 41), (100, 42)]
DMG_CASE = [(6, 3, 0), (6, 3, 2), (6, 3, 5), (6, 3, 9), (9, 1, 0), (9, 1, 4),
            (12, 8, 3), (12, 8, 11), (4, 0, 0), (4, 0, 3), (20, 12, 6), (2, 2, 4)]
LAN_CASE = [(10, 10, 6554, 6554), (20, 10, 6554, 6554), (10, 20, 6554, 6554),
            (30, 20, 3277, 6554), (5, 5, 13107, 13107), (50, 40, 1311, 1311),
            (12, 8, 6554, 9830), (100, 100, 655, 655)]
ECON_CASE = [(0, 6554), (4, 6554), (8, 6554), (16, 6554), (8, 13107), (8, 3277)]
NOTE_NAME = ['C4', 'C#4', 'D4', 'D#4', 'E4', 'F4', 'F#4', 'G4', 'G#4', 'A4', 'A#4', 'B4',
             'C5', 'C#5', 'D5', 'D#5', 'E5', 'F5', 'F#5', 'G5', 'G#5', 'A5', 'A#5', 'B5']
NOTE_HZ = [int(round(440.0 * 2 ** ((k - 9) / 12.0))) for k in range(24)]

LOAD_MAX, MINE_PER_TICK, UNLOAD_TICKS = 100, 5, 12


def sec_metrics(o):
    o.append('== 1. 거리 척도 ==')
    o.append('  dx   dy     d1  dinf   d83   dab   doct     eu3  d83pm  dabpm doctpm')
    for dx, dy in PAIRS_M:
        m = metrics(dx, dy)
        eu = m['eu3']
        o.append('%4d %4d %6d %5d %5d %5d %6d %7d %6d %6d %6d'
                 % (dx, dy, m['d1'], m['dinf'], m['d83'], m['dab'], m['doct'], eu,
                    m['d83'] * 1000000 // eu - 1000,
                    m['dab'] * 1000000 // eu - 1000,
                    m['doct'] * 100000 // eu - 1000))
    o.append('eu3 = floor(sqrt(dx^2+dy^2) * 1000)')
    o.append('d83pm dabpm = 유클리드 대비 천분율 편차')
    o.append('doctpm = 유클리드*10 대비. 옥타일은 유클리드 근사가 아니므로 참고값이며,')
    o.append('참 옥타일과의 비교는 out/analysis.txt 2절에 있다.')


def sec_isqrt(o):
    o.append('== 2. 정수 제곱근 ==')
    o.append('          n     isqrt          isqrt^2      (isqrt+1)^2')
    for n in SQ_N:
        r = math.isqrt(n)
        o.append('%11d %9d %16d %16d' % (n, r, r * r, (r + 1) * (r + 1)))


def sec_atan8(o):
    o.append('== 3. 8방향 판별 ==')
    o.append('  dx   dy  12*mn  5*mx  대각  방향  이름')
    for dx, dy in ANG_V:
        ax, ay = abs(dx), abs(dy)
        mx, mn = max(ax, ay), min(ax, ay)
        d = atan8(dx, dy)
        o.append('%4d %4d %6d %5d %5d %5d  %s'
                 % (dx, dy, 12 * mn, 5 * mx, 1 if 12 * mn > 5 * mx else 0, d, DNAME[d]))


def sec_lcg(o):
    o.append('== 4. LCG ==')
    r = LCG(1)
    o.append('  i           상태   next15')
    for i in range(10):
        v = r.next15()
        o.append('%3d %14d %8d' % (i + 1, r.s, v))
    o.append('하위 비트의 짧은 주기 — 상태의 최하위 1·2비트')
    r2 = LCG(1)
    b1, b2 = [], []
    for _ in range(16):
        r2.next15()
        b1.append(r2.s % 2)
        b2.append(r2.s % 4)
    o.append('  bit0: ' + ' '.join(str(v) for v in b1))
    o.append('  bit10: ' + ' '.join(str(v) for v in b2))
    r3 = LCG(2026)
    vals = [r3.roll(6) for _ in range(20)]
    o.append('roll(6) x20: ' + ' '.join(str(v) for v in vals))
    o.append('기각 횟수 %d' % r3.rejects)
    r4 = LCG(2026)
    hist = [0] * 6
    for _ in range(6000):
        hist[r4.roll(6)] += 1
    o.append('roll(6) x6000 도수: ' + ' '.join(str(v) for v in hist))
    o.append('기각 횟수 %d' % r4.rejects)


def sec_autotile(o):
    o.append('== 5. 오토타일 ==')
    classes = sorted(set(canon(m) for m in range(256)))
    index = dict((m, i) for i, m in enumerate(classes))
    o.append('클래스 %d개' % len(classes))
    o.append('정규화 인덱스 (마스크 0..255, 16개씩)')
    for row in range(16):
        o.append('  ' + ' '.join('%3d' % index[canon(row * 16 + c)] for c in range(16)))
    o.append('클래스별 마스크 개수')
    for row in range(0, len(classes), 8):
        o.append('  ' + ' '.join('%3d:%-3d' % (classes[i],
                                               sum(1 for k in range(256)
                                                   if canon(k) == classes[i]))
                                 for i in range(row, min(row + 8, len(classes)))))


def sec_circle(o):
    o.append('== 6. 원 마스크 ==')
    o.append(' r    개수  span')
    for r in range(1, 9):
        o.append('%2d %7d  %s' % (r, len(disc_offsets(r)),
                                  ' '.join(str(v) for v in disc_spans(r))))


def _maps():
    return [load_map(os.path.join(GOLDEN, 'map_%d.txt' % i)) for i in range(1, 7)]


def sec_path(o, maps):
    o.append('== 7. 경로 탐색 ==')
    o.append('맵 출발      도착      BFS걸음  다익스트라   A*비용  A*연노드')
    for i, g in enumerate(maps):
        for (s, t) in g.pairs:
            b = bfs_steps(g, s, t)
            dj = dijkstra_cost(g, s, t)
            a, ex = astar(g, s, t)
            o.append('%2d (%2d,%2d) -> (%2d,%2d) %8d %11d %8d %9d'
                     % (i + 1, s[0], s[1], t[0], t[1], b, dj, a, ex))
    o.append('다익스트라와 A* 의 비용은 모든 줄에서 같아야 한다 (정리 8.1)')


def sec_hpa_jps(o, maps):
    o.append('== 8. HPA* 와 JPS ==')
    o.append('맵 출발      도착        A*   JPS  JPS연노드   HPA*  HPA*/A*(pm)')
    for i, g in enumerate(maps):
        for (s, t) in g.pairs:
            a, _ = astar(g, s, t)
            j, jx = jps(g, s, t)
            hp = hpa(g, s, t)
            ratio = -1 if (a <= 0 or hp <= 0) else hp * 1000 // a
            o.append('%2d (%2d,%2d) -> (%2d,%2d) %6d %5d %10d %6d %12d'
                     % (i + 1, s[0], s[1], t[0], t[1], a, j, jx, hp, ratio))
    o.append('JPS 비용은 모든 줄에서 A* 와 같아야 한다 (정리 10.1)')


def sec_flow(o):
    o.append('== 9. 흐름장과 클리어런스 ==')
    g = Grid('flow', FLOWMAP, [])
    goal = (4, 4)
    integ = integration(g, [goal])
    fl = flow_dirs(g, integ)
    cl = clearance(g)
    o.append('목표 (%d,%d) · 적분장' % goal)
    for y in range(g.h):
        o.append('  ' + ' '.join('%5d' % integ[y][x] for x in range(g.w)))
    o.append('경사장 (방향 번호, 255=정지)')
    for y in range(g.h):
        o.append('  ' + ' '.join('%3d' % fl[y][x] for x in range(g.w)))
    o.append('클리어런스 (좌상단 기준 정사각 여유)')
    for y in range(g.h):
        o.append('  ' + ' '.join('%2d' % cl[y][x] for x in range(g.w)))


def sec_fog(o):
    o.append('== 10. 안개 참조 카운트 ==')
    W = H = 64
    units = [((10, 10), 3), ((12, 11), 5), ((30, 30), 8)]

    def build(us):
        cnt = {}
        for (x, y), r in us:
            for dx, dy in disc_offsets(r):
                u, v = x + dx, y + dy
                if 0 <= u < W and 0 <= v < H:
                    cnt[(u, v)] = cnt.get((u, v), 0) + 1
        return cnt

    def report(tag, cnt):
        tot = sum(cnt.values())
        vis = len([1 for v in cnt.values() if v > 0])
        mx = max(cnt.values()) if cnt else 0
        hist = [0] * (mx + 1)
        for v in cnt.values():
            hist[v] += 1
        o.append('%s 가시 칸 %d · 카운트 합 %d · 최대 %d' % (tag, vis, tot, mx))
        o.append('  도수: ' + ' '.join('%d:%d' % (k, hist[k])
                                       for k in range(1, mx + 1)))

    report('초기', build(units))
    moved = [((11, 10), 3)] + units[1:]
    report('1번 유닛 (10,10)->(11,10)', build(moved))
    report('3번 유닛 사망', build(moved[:2]))
    o.append('전원 제거 후 카운트 합 %d' % sum(build([]).values()))


def sec_combat(o):
    o.append('== 11. 전투 ==')
    o.append('기본 관통 방어    mx    lo    n   E*100  모의평균*100')
    for basic, pierce, armour in DMG_CASE:
        mx = max(1, basic - armour + pierce)
        lo = (mx + 1) // 2
        n = mx - lo + 1
        e100 = (lo + mx) * 50
        r = LCG(12345)
        tot = sum(lo + r.roll(n) for _ in range(1000))
        o.append('%4d %4d %4d %5d %5d %4d %7d %13d'
                 % (basic, pierce, armour, mx, lo, n, e100, tot * 100 // 1000))
    o.append('란체스터 제곱 법칙 시뮬 (A0 B0 alpha beta -> 틱 A남음 B남음)')
    for a0, b0, al, be in LAN_CASE:
        A, B, t = a0 * FP_ONE, b0 * FP_ONE, 0
        while A >= FP_ONE and B >= FP_ONE and t < 10000:
            dA = be * B // FP_ONE
            dB = al * A // FP_ONE
            A = max(0, A - dA)
            B = max(0, B - dB)
            t += 1
        o.append('%4d %4d %6d %6d %8d %8d %8d'
                 % (a0, b0, al, be, t, A // FP_ONE, B // FP_ONE))


def sec_econ(o):
    o.append('== 12. 경제 ==')
    o.append('왕복타일 속도(fp)   총틱   수입*10000')
    for d, v in ECON_CASE:
        T = 2 * d * FP_ONE // v + LOAD_MAX // MINE_PER_TICK + UNLOAD_TICKS
        o.append('%8d %10d %6d %12d' % (d, v, T, LOAD_MAX * 10000 // T))
    o.append('적재 %d · 틱당 채굴 %d · 반납 %d틱' % (LOAD_MAX, MINE_PER_TICK, UNLOAD_TICKS))


def sec_hash(o):
    o.append('== 13. CRC 와 FNV ==')
    for s in ['123456789', '', 'A', 'RTSM', 'the quick brown fox']:
        o.append('crc16 %-20r %6d 0x%04X' % (s, crc16(s.encode('ascii')),
                                             crc16(s.encode('ascii'))))
    for s in ['', 'a', 'foobar', 'RTSM']:
        o.append('fnv1a %-20r %12d 0x%08X' % (s, fnv1a(s.encode('ascii')),
                                              fnv1a(s.encode('ascii'))))
    b = bytes(bytearray(range(16)))
    o.append('fnv1a bytes(0..15) %12d 0x%08X' % (fnv1a(b), fnv1a(b)))


def sec_pit(o):
    o.append('== 14. PIT 분주값 ==')
    o.append('음   목표Hz  분주값   실제Hz*100   차이*100')
    for name, f in zip(NOTE_NAME, NOTE_HZ):
        div = (PIT_HZ + f // 2) // f
        act = PIT_HZ * 100 // div
        o.append('%-4s %6d %7d %12d %10d' % (name, f, div, act, act - f * 100))


def analysis(maps):
    """부동소수점이 필요한 분석 — 덱에서만 인용한다. 엔진은 이것을 만들지 않는다."""
    o = ['== 1. 정수 출력 그대로의 오차 (%) ==',
         'd83·dab 는 유클리드 거리와, doct 는 참 옥타일 길이(×10)와 견준다.',
         '  dx   dy    유클리드     참옥타일    d83오차%     dab오차%   doct오차%']
    worst = {'d83': 0.0, 'dab': 0.0, 'doct': 0.0}
    for dx, dy in PAIRS_M:
        m = metrics(dx, dy)
        eu = math.hypot(dx, dy)
        mx, mn = max(abs(dx), abs(dy)), min(abs(dx), abs(dy))
        oct_true = (mx - mn) + mn * math.sqrt(2)
        e83 = (m['d83'] - eu) / eu * 100
        eab = (m['dab'] - eu) / eu * 100
        eoc = (m['doct'] / 10.0 - oct_true) / oct_true * 100
        for k, v in (('d83', e83), ('dab', eab), ('doct', eoc)):
            worst[k] = max(worst[k], abs(v))
        o.append('%4d %4d %11.4f %12.4f %11.4f %12.4f %11.4f'
                 % (dx, dy, eu, oct_true, e83, eab, eoc))
    o.append('최대 절대 오차: d83 %.4f%% · dab %.4f%% · doct %.4f%%'
             % (worst['d83'], worst['dab'], worst['doct']))
    o.append('작은 벡터에서 오차가 큰 것은 근사식이 아니라 **정수 출력** 탓이다.')
    o.append('(1,1) 의 참값은 1.4142 인데 정수로는 1 아니면 2 밖에 쓸 수 없다.')

    o.append('')
    o.append('== 2. 근사식 자체의 오차 (입력을 256배 확대해 계산) ==')
    o.append('정수 출력의 양자화를 걷어내면 남는 것이 근사식 고유의 오차다.')
    w = {'d83': 0.0, 'dab': 0.0, 'doct': 0.0}
    arg = {}
    for dy in range(0, 65):
        for dx in range(0, 65):
            if dx == 0 and dy == 0:
                continue
            m = metrics(dx * 256, dy * 256)
            eu = math.hypot(dx, dy) * 256
            mx, mn = max(abs(dx), abs(dy)) * 256, min(abs(dx), abs(dy)) * 256
            oct_true = (mx - mn) + mn * math.sqrt(2)
            for k, v in (('d83', (m['d83'] - eu) / eu * 100),
                         ('dab', (m['dab'] - eu) / eu * 100),
                         ('doct', (m['doct'] / 10.0 - oct_true) / oct_true * 100)):
                if abs(v) > w[k]:
                    w[k] = abs(v)
                    arg[k] = (dx, dy, v)
    for k in ('d83', 'dab', 'doct'):
        dx, dy, v = arg[k]
        o.append('%-5s 최대 %8.4f%%  (dx,dy) = (%d,%d) 에서 %+.4f%%'
                 % (k, w[k], dx, dy, v))

    o.append('')
    o.append('== 3. 란체스터 폐형해와 시뮬의 차이 ==')
    o.append('  A0   B0    alpha     beta   시뮬틱   폐형해틱      차이')
    for a0, b0, al, be in LAN_CASE:
        A, B, t = a0 * FP_ONE, b0 * FP_ONE, 0
        while A >= FP_ONE and B >= FP_ONE and t < 10000:
            dA = be * B // FP_ONE
            dB = al * A // FP_ONE
            A = max(0, A - dA)
            B = max(0, B - dB)
            t += 1
        af, bf = al / float(FP_ONE), be / float(FP_ONE)
        num = math.sqrt(af) * a0 + math.sqrt(bf) * b0
        den = math.sqrt(af) * a0 - math.sqrt(bf) * b0
        if den > 0:
            T = math.log(num / den) / (2 * math.sqrt(af * bf))
            o.append('%4d %4d %8d %8d %8d %10.2f %9.2f'
                     % (a0, b0, al, be, t, T, t - T))
        else:
            o.append('%4d %4d %8d %8d %8d %10s %9s'
                     % (a0, b0, al, be, t, 'A 패배', '-'))

    o.append('')
    o.append('== 4. PIT 반올림의 음정 오차 (센트) ==')
    o.append('음   목표Hz  분주값     실제Hz     센트')
    for name, f in zip(NOTE_NAME, NOTE_HZ):
        div = (PIT_HZ + f // 2) // f
        act = PIT_HZ / float(div)
        o.append('%-4s %6d %7d %10.3f %8.3f'
                 % (name, f, div, act, 1200 * math.log(act / f, 2)))
    o.append('정확한 PIT 클럭 1193181.8182 Hz 로 계산하면')
    for name, f in list(zip(NOTE_NAME, NOTE_HZ))[:4]:
        d1 = (PIT_HZ + f // 2) // f
        d2 = int(round(1193181.8181818181 / f))
        o.append('  %-4s 반올림값 분주 %d · 정확값 분주 %d · %s'
                 % (name, d1, d2, '같다' if d1 == d2 else '다르다'))

    o.append('')
    o.append('== 5. JPS 가 A* 대비 줄인 연 노드 수 ==')
    o.append('맵 출발      도착       A*연노드  JPS연노드   비율%')
    for i, g in enumerate(maps):
        for (s, t) in g.pairs:
            _a, ax = astar(g, s, t)
            _j, jx = jps(g, s, t)
            o.append('%2d (%2d,%2d) -> (%2d,%2d) %10d %10d %8.1f'
                     % (i + 1, s[0], s[1], t[0], t[1], ax, jx,
                        100.0 * jx / ax if ax else 0.0))
    return o


def main():
    for d in (GOLDEN, OUT):
        if not os.path.isdir(d):
            os.makedirs(d)
    maps = _maps()
    o = []
    sec_metrics(o); o.append('')
    sec_isqrt(o); o.append('')
    sec_atan8(o); o.append('')
    sec_lcg(o); o.append('')
    sec_autotile(o); o.append('')
    sec_circle(o); o.append('')
    sec_path(o, maps); o.append('')
    sec_hpa_jps(o, maps); o.append('')
    sec_flow(o); o.append('')
    sec_fog(o); o.append('')
    sec_combat(o); o.append('')
    sec_econ(o); o.append('')
    sec_hash(o); o.append('')
    sec_pit(o)
    io.open(os.path.join(GOLDEN, 'prim.txt'), 'w', encoding='utf-8').write(
        '\n'.join(o) + '\n')
    a = analysis(maps)
    io.open(os.path.join(OUT, 'analysis.txt'), 'w', encoding='utf-8').write(
        '\n'.join(a) + '\n')
    print('prim.txt %d줄 · analysis.txt %d줄' % (len(o), len(a)))


if __name__ == '__main__':
    main()
