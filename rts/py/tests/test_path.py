# -*- coding: utf-8 -*-
"""경로 탐색 I — BFS·다익스트라·A* 와 그 성질 (SPEC §8)."""
from __future__ import print_function

import harness as H
from rts import fixed as F
from rts import path as P
from rts import tmap as T

H.title('path')

MAPS = [T.TMap.load_text(H.golden('map_%d.txt' % i)) for i in range(1, 7)]

# ---- 골든 7절과 전수 대조
rows = H.golden('prim.txt').split('\n')
i = rows.index('== 7. 경로 탐색 ==') + 2
bad = 0
n = 0
while rows[i].strip() and not rows[i].startswith('다익스트라'):
    p = rows[i].replace('(', ' ').replace(')', ' ').replace(',', ' ').replace('->', ' ')
    v = [int(x) for x in p.split()]
    mi, sx, sy, tx, ty, wb, wd, wa, wx = v
    m = MAPS[mi - 1]
    gb = P.bfs(m, 0, (sx, sy), (tx, ty))
    gd = P.dijkstra(m, 0, [sy * m.w + sx], ty * m.w + tx)[ty * m.w + tx]
    gd = -1 if gd >= P.INF else gd
    ga, _tiles, gx = P.astar(m, 0, (sx, sy), (tx, ty))
    if [gb, gd, ga, gx] != [wb, wd, wa, wx]:
        bad += 1
        H.note('맵%d (%d,%d)->(%d,%d) 기대 %s 실제 %s',
               mi, sx, sy, tx, ty, [wb, wd, wa, wx], [gb, gd, ga, gx])
    n += 1
    i += 1
H.check('골든 7절 %d줄 (BFS·다익스트라·A*·연 노드 수)' % n, bad, 0)

# ---- 다익스트라와 A* 의 비용은 언제나 같아야 한다 (정리 8.1)
bad = 0
for m in MAPS:
    for (s, t) in m.pairs:
        d = P.dijkstra(m, 0, [s[1] * m.w + s[0]], t[1] * m.w + t[0])[t[1] * m.w + t[0]]
        a = P.astar(m, 0, s, t)[0]
        if (d if d < P.INF else -1) != a:
            bad += 1
H.check('다익스트라 == A*', bad, 0)

# ---- 휴리스틱의 허용성: h(n) <= 실제 최적 비용 (전수)
m = MAPS[0]
bad = 0
checked = 0
src = (16, 16)
dist = P.dijkstra(m, 0, [src[1] * m.w + src[0]])
for j in range(m.w * m.h):
    if dist[j] >= P.INF:
        continue
    x, y = j % m.w, j // m.w
    if P.h_oct(src[0], src[1], x, y) > dist[j]:
        bad += 1
    checked += 1
H.check('허용성: h <= g* (%d칸 전수)' % checked, bad, 0)

# ---- 일관성: h(n) <= c(n,n') + h(n') (전수)
bad = 0
t = (30, 30)
for y in range(1, 31):
    for x in range(1, 31):
        for d, u, v in P.neighbours(m, x, y, 0):
            if P.h_oct(x, y, t[0], t[1]) > F.DCOST[d] + P.h_oct(u, v, t[0], t[1]):
                bad += 1
H.check('일관성: h(n) <= c + h(n\')', bad, 0)
H.note('일관적이므로 닫힌 노드를 다시 열지 않는다 — 재개방 코드가 아예 없다')

# ---- 경로가 실제로 이어져 있고 비용이 맞는가
bad = 0
for m in MAPS:
    for (s, t) in m.pairs:
        cost, tiles, _n = P.astar(m, 0, s, t)
        if cost < 0:
            continue
        total = 0
        for k in range(len(tiles) - 1):
            ax, ay = tiles[k] % m.w, tiles[k] // m.w
            bx, by = tiles[k + 1] % m.w, tiles[k + 1] // m.w
            dx, dy = bx - ax, by - ay
            if max(abs(dx), abs(dy)) != 1:
                bad += 1
            total += F.D_DIAG if (dx and dy) else F.D_STRAIGHT
        if total != cost:
            bad += 1
H.check('경로가 한 칸씩 이어지고 비용 합이 같다', bad, 0)

# ---- 양동이 큐 (정리 8.3): 15개면 충분한가
H.check('양동이 개수', P.NB, 15)
H.check('최대 간선 비용', F.D_DIAG, 14)
H.check_true('양동이 개수 > 최대 간선 비용', P.NB > F.D_DIAG)

# ---- 코너 컷 허용 (SPEC §8.1)
m2 = T.TMap(3, 3)
for y in range(3):
    for x in range(3):
        m2.set_terrain(x, y, T.DIRT)
m2.set_terrain(1, 0, T.ROCK)
m2.set_terrain(0, 1, T.ROCK)
H.check('바위 두 개 사이 대각을 지나간다', P.astar(m2, 0, (0, 0), (1, 1))[0], 14)
H.note('이것은 선택이다 — 금지하면 JPS 의 가지치기 규칙이 통째로 달라진다')

# ---- 도달 불가 목표 (SPEC §8.6)
m5 = MAPS[4]
H.check('섬 안쪽은 닿지 않는다', P.astar(m5, 0, (1, 1), (25, 25))[0], -1)
alt = P.closest_reachable(m5, 0, (1, 1), (25, 25))
H.check_true('대체 목표를 찾는다 %s' % (alt,), alt is not None)
H.check('대체 목표는 같은 성분',
        m5.labels(0)[alt[1] * m5.w + alt[0]], m5.labels(0)[1 * m5.w + 1])
cost, tiles = P.find(m5, 0, (1, 1), (25, 25))
H.check_true('find 는 대체 목표까지의 경로를 준다', cost > 0)

# ---- 경로 캐시 (SPEC §8.7)
c = P.Cache()
m1 = MAPS[0]
P.find(m1, 0, (1, 1), (30, 30), c)
P.find(m1, 0, (1, 1), (30, 30), c)
H.check('두 번째는 적중', c.hits, 1)
H.check('첫 번째는 실패', c.misses, 1)
m1.set_terrain(15, 15, T.ROCK)
P.find(m1, 0, (1, 1), (30, 30), c)
H.check('지형이 바뀌면 통째로 비운다', c.hits, 1)
m1.set_terrain(15, 15, T.DIRT)

H.done()
