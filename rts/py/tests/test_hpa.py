# -*- coding: utf-8 -*-
"""계층 경로 탐색 — 최적이 아니라는 것을 숫자로 남긴다 (SPEC §9)."""
from __future__ import print_function

import harness as H
from rts import hpa as A
from rts import path as P
from rts import tmap as T

H.title('hpa')

MAPS = [T.TMap.load_text(H.golden('map_%d.txt' % i)) for i in range(1, 7)]

# ---- 골든 8절의 HPA* 열과 대조
rows = H.golden('prim.txt').split('\n')
i = rows.index('== 8. HPA* 와 JPS ==') + 2
bad = 0
n = 0
ratios = []
while rows[i].strip() and not rows[i].startswith('JPS 비용'):
    p = rows[i].replace('(', ' ').replace(')', ' ').replace(',', ' ').replace('->', ' ')
    v = [int(x) for x in p.split()]
    mi, sx, sy, tx, ty, wa, _wj, _wjx, wh, wr = v
    m = MAPS[mi - 1]
    c, _nodes = A.search(m, 0, (sx, sy), (tx, ty))
    if c != wh:
        bad += 1
        H.note('맵%d (%d,%d)->(%d,%d) 기대 %d 실제 %d', mi, sx, sy, tx, ty, wh, c)
    if wr > 0:
        ratios.append(wr)
    n += 1
    i += 1
H.check('골든 8절 %d줄의 HPA* 비용' % n, bad, 0)
H.note('최적 대비 %d~%d 천분율 (평균 %d) — 논문의 "1%%" 를 옮겨 적지 않는다',
       min(ratios), max(ratios), sum(ratios) // len(ratios))

# ---- HPA* 는 최적 이상이다 (아래로 내려갈 수는 없다)
bad = 0
for m in MAPS:
    for (s, t) in m.pairs:
        a = P.astar(m, 0, s, t)[0]
        c, _ = A.search(m, 0, s, t)
        if a > 0 and 0 < c < a:
            bad += 1
            H.note('HPA* 가 A* 보다 싸다?! %s %s %d < %d', s, t, c, a)
H.check('HPA* 비용 >= A* 비용', bad, 0)

# ---- 클러스터와 전이
m1 = MAPS[0]
H.check('클러스터 한 변', A.CLUSTER, 8)
H.check('32x32 맵의 클러스터 수', (m1.w // 8) * (m1.h // 8), 16)
H.check('cluster_of(0,0)', A.cluster_of(0, 0), (0, 0))
H.check('cluster_of(8,8)', A.cluster_of(8, 8), (1, 1))
ents = A.entrances(m1, 0)
H.check_true('빈 들판에도 전이가 있다 (%d개)' % len(ents), len(ents) > 0)
H.check_true('전이는 이웃한 두 칸을 잇는다',
             all(abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1 for a, b in ents))

# ---- 구간 길이에 따른 전이 개수 (SPEC §9.2)
H.check('길이 1 구간은 전이 1개', len(A._place([5], lambda v: v)), 1)
H.check('길이 5 구간은 전이 1개', len(A._place([1, 2, 3, 4, 5], lambda v: v)), 1)
H.check('길이 5 구간의 위치는 가운데', A._place([1, 2, 3, 4, 5], lambda v: v), [3])
H.check('길이 6 구간은 양 끝 2개', A._place([1, 2, 3, 4, 5, 6], lambda v: v), [1, 6])
H.check('빈 구간은 전이 없음', A._place([], lambda v: v), [])

# ---- 정련 (SPEC §9.4)
m3 = MAPS[3]
s, t = m3.pairs[0]
cost, nodes = A.search(m3, 0, s, t)
tiles = A.refine(m3, 0, nodes)
H.check_true('정련 결과가 출발에서 시작한다', tiles[0] == s[1] * m3.w + s[0])
H.check_true('정련 결과가 도착에서 끝난다', tiles[-1] == t[1] * m3.w + t[0])

# ---- 추상 그래프는 맵 버전마다 다시 짓는다
a1 = A.abstract(m1, 0)
a2 = A.abstract(m1, 0)
H.check('같은 버전이면 같은 그래프 객체', a1 is a2, True)
m1.set_terrain(4, 4, T.ROCK)
a3 = A.abstract(m1, 0)
H.check('버전이 바뀌면 다시 짓는다', a3 is a1, False)
m1.set_terrain(4, 4, T.DIRT)

H.done()
