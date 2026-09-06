# -*- coding: utf-8 -*-
"""점프 포인트 탐색 — A* 와 비용이 같은가를 전수로 확인한다 (SPEC §10)."""
from __future__ import print_function

import harness as H
from rts import jps as J
from rts import path as P
from rts import rng as R
from rts import tmap as T

H.title('jps')

MAPS = [T.TMap.load_text(H.golden('map_%d.txt' % i)) for i in range(1, 7)]

# ---- 골든 8절의 JPS 열과 대조
rows = H.golden('prim.txt').split('\n')
i = rows.index('== 8. HPA* 와 JPS ==') + 2
bad = 0
n = 0
while rows[i].strip() and not rows[i].startswith('JPS 비용'):
    p = rows[i].replace('(', ' ').replace(')', ' ').replace(',', ' ').replace('->', ' ')
    v = [int(x) for x in p.split()]
    mi, sx, sy, tx, ty, wa, wj, wjx = v[:8]
    m = MAPS[mi - 1]
    c, _tiles, ex = J.search(m, 0, (sx, sy), (tx, ty))
    if [c, ex] != [wj, wjx]:
        bad += 1
        H.note('맵%d (%d,%d)->(%d,%d) 기대 %s 실제 %s', mi, sx, sy, tx, ty,
               [wj, wjx], [c, ex])
    n += 1
    i += 1
H.check('골든 8절 %d줄의 JPS 비용·연 노드 수' % n, bad, 0)

# ---- 전수 검사: 정리 10.1 을 옮겨 적는 대신 직접 확인한다
bad = 0
total = 0
for mi, m in enumerate(MAPS):
    free = [j for j in range(m.w * m.h) if m.passable_terrain(j % m.w, j // m.w, 0)]
    rand = R.LCG(1000 + mi)
    for _ in range(120):
        a = free[rand.roll(len(free))]
        b = free[rand.roll(len(free))]
        s = (a % m.w, a // m.w)
        t = (b % m.w, b // m.w)
        ca = P.astar(m, 0, s, t)[0]
        cj = J.search(m, 0, s, t)[0]
        total += 1
        if ca != cj:
            bad += 1
            if bad < 4:
                H.note('맵%d (%d,%d)->(%d,%d) A*=%d JPS=%d',
                       mi + 1, s[0], s[1], t[0], t[1], ca, cj)
H.check('무작위 %d쌍에서 JPS 비용 == A* 비용' % total, bad, 0)

# ---- 경로가 실제로 이어지는가 (점프점 사이는 직선이어야 한다)
bad = 0
for m in MAPS:
    for (s, t) in m.pairs:
        cost, tiles, _n = J.search(m, 0, s, t)
        if cost < 0:
            continue
        for k in range(len(tiles) - 1):
            ax, ay = tiles[k] % m.w, tiles[k] // m.w
            bx, by = tiles[k + 1] % m.w, tiles[k + 1] // m.w
            dx, dy = bx - ax, by - ay
            if dx and dy and abs(dx) != abs(dy):
                bad += 1                       # 대각 구간은 45도여야 한다
            if not dx and not dy:
                bad += 1
H.check('점프점 사이가 직선 또는 45도', bad, 0)

# ---- JPS 가 여는 노드 수는 A* 이하인가
worse = 0
same = 0
for m in MAPS:
    for (s, t) in m.pairs:
        ax = P.astar(m, 0, s, t)[2]
        jx = J.search(m, 0, s, t)[2]
        if jx > ax:
            worse += 1
        elif jx == ax:
            same += 1
H.check('JPS 의 연 노드 수가 A* 보다 많은 경우', worse, 0)
H.note('연 노드 수가 같은 경우 %d건 — 줄어드는 것은 연 노드지 훑는 칸이 아니다', same)

# ---- 강제 이웃 규칙 (SPEC §10.1)
m2 = T.TMap(5, 5)
for y in range(5):
    for x in range(5):
        m2.set_terrain(x, y, T.DIRT)
m2.set_terrain(2, 1, T.ROCK)
H.check_true('(2,2) 로 동쪽으로 들어오면 (3,1) 이 강제 이웃',
             J._forced(m2, 2, 2, 1, 0, 0))
m2.set_terrain(2, 1, T.DIRT)
H.check_true('막힌 칸이 없으면 강제 이웃도 없다',
             not J._forced(m2, 2, 2, 1, 0, 0))

H.done()
