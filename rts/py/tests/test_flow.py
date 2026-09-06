# -*- coding: utf-8 -*-
"""흐름장·클리어런스·브러시파이어 (SPEC §11).

   골든 9절과 대조하고, 정리 11.1 은 완전 탐색으로 직접 확인한다.
"""
from __future__ import print_function

import harness as H
from rts import fixed as F
from rts import flow as FL
from rts import path as P
from rts import tmap as T

H.title('flow')

# tools/gen_prim.py 의 FLOWMAP 과 **글자 단위로 같아야 한다**.
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


def grid(rows):
    m = T.TMap(len(rows[0]), len(rows))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            m.terrain[y * m.w + x] = T.ROCK if ch == '#' else T.DIRT
            m._repass(y * m.w + x)
    m._bump()
    return m


def rows_of(field, m, width):
    return ['  ' + ' '.join(('%%%dd' % width) % field[y * m.w + x]
                            for x in range(m.w)) for y in range(m.h)]


FM = grid(FLOWMAP)

# ── 골든 9절 세 표와 한 줄씩 대조 ───────────────────────────────────────────
g = H.golden('prim.txt').split('\n')
i = g.index('== 9. 흐름장과 클리어런스 ==')
integ = FL.integration(FM, 0, [(4, 4)])
fl = FL.flow_dirs(FM, 0, integ)
cl = FL.clearance(FM, 0)
want = g[i + 2:i + 2 + 12] + g[i + 15:i + 15 + 12] + g[i + 28:i + 28 + 12]
got = rows_of(integ, FM, 5) + rows_of(fl, FM, 3) + rows_of(cl, FM, 2)
bad = 0
for k in range(36):
    if got[k] != want[k]:
        bad += 1
        if bad < 4:
            H.note('%d행 기대 %r', k, want[k])
            H.note('     실제 %r', got[k])
H.check('골든 9절 36줄 (적분장·경사장·클리어런스)', bad, 0)

# ── 적분장 = 목표에서 거꾸로 돌린 다익스트라 ────────────────────────────────
d = P.dijkstra(FM, 0, [4 * FM.w + 4])
bad = 0
for j in range(FM.w * FM.h):
    want_v = FL.INF if d[j] >= FL.INF else d[j]
    if not FM.passable_terrain(j % FM.w, j // FM.w, 0):
        want_v = FL.INF
    if integ[j] != want_v:
        bad += 1
H.check('적분장 == path.dijkstra (INF 는 65535 로 자름)', bad, 0)

# ── 다중 목표는 목표별 장의 최솟값이다 ──────────────────────────────────────
a = FL.integration(FM, 0, [(2, 2)])
b = FL.integration(FM, 0, [(9, 9)])
ab = FL.integration(FM, 0, [(2, 2), (9, 9)])
H.check('다중 목표 == 목표별 최솟값',
        ab, [min(a[j], b[j]) for j in range(FM.w * FM.h)])

# ── 경계 조건 ───────────────────────────────────────────────────────────────
H.check('목표가 없으면 전부 INF',
        set(FL.integration(FM, 0, [])), set([FL.INF]))
H.check('막힌 목표는 무시한다 (SPEC §11.1)',
        FL.integration(FM, 0, [(1, 1)]), FL.integration(FM, 0, []))
H.check('막힌 목표 + 성한 목표 = 성한 목표만',
        FL.integration(FM, 0, [(1, 1), (4, 4)]), integ)
one = grid(['.'])
H.check('1x1 맵', FL.integration(one, 0, [(0, 0)]), [0])
H.check('1x1 맵의 경사장', FL.flow_dirs(one, 0, [0]), [255])
H.check('1x1 맵의 클리어런스', FL.clearance(one, 0), [1])
solid = grid(['##', '##'])
H.check('전부 막힌 맵의 클리어런스', FL.clearance(solid, 0), [0, 0, 0, 0])
H.check('전부 막힌 맵의 브러시파이어', FL.brushfire(solid, 0), [0, 0, 0, 0])

# ── 경사장: 막힌 칸과 INF 칸은 255, 나머지는 내리막이다 ─────────────────────
bad = 0
stops = 0
for j in range(FM.w * FM.h):
    x, y = j % FM.w, j // FM.w
    if integ[j] == FL.INF:
        if fl[j] != 255:
            bad += 1
        continue
    if fl[j] == 255:
        stops += 1
        continue
    u, v = x + F.DX[fl[j]], y + F.DY[fl[j]]
    if integ[j] == 0:                      # 목표 칸은 예외 — 오르막을 가리킨다
        continue
    if not FM.passable_terrain(u, v, 0) or integ[v * FM.w + u] >= integ[j]:
        bad += 1
H.check('INF·막힌 칸의 경사는 255', bad, 0)
H.check('정지 칸은 없다 (모든 도달 가능 칸에 후보가 있다)', stops, 0)

# ── 경사장 동점 규칙: 대칭 맵에서 항상 작은 방향 번호 ───────────────────────
open3 = grid(['...', '...', '...'])
of = FL.flow_dirs(open3, 0, FL.integration(open3, 0, [(1, 1)]))
H.check('(0,0) 은 목표를 향한 대각 3(SE)', of[0], 3)
H.check('목표 칸도 255 가 아니다 — 가장 싼 이웃(오르막)을 가리킨다', of[4], 0)
tie = FL.flow_dirs(open3, 0, FL.integration(open3, 0, [(0, 0), (2, 0)]))
H.check('동점이면 작은 방향 번호 — (1,1) 은 1(NE), 7(NW) 이 아니다', tie[4], 1)

# ── 정리 11.1 을 완전 탐색으로 확인 ─────────────────────────────────────────
def max_square(m, kind, x, y):
    k = 0
    while True:
        s = k + 1
        if x + s > m.w or y + s > m.h:
            return k
        for v in range(y, y + s):
            for u in range(x, x + s):
                if not m.passable_terrain(u, v, kind):
                    return k
        k = s


MAPS = [FM] + [T.TMap.load_text(H.golden('map_%d.txt' % n)) for n in range(1, 7)]
bad = 0
cells = 0
for m in MAPS:
    c = FL.clearance(m, 0)
    for y in range(m.h):
        for x in range(m.w):
            cells += 1
            if c[y * m.w + x] != max_square(m, 0, x, y):
                bad += 1
H.check('정리 11.1 — %d칸에서 clear == 최대 정사각 변' % cells, bad, 0)

# ── 크기 s 유닛의 통행 판정 ─────────────────────────────────────────────────
c1 = FL.clearance(MAPS[1], 0)
H.check_true('크기 1 통행 칸 수 == 지형 통행 칸 수',
             len([1 for v in c1 if v >= 1])
             == len([1 for j in range(MAPS[1].w * MAPS[1].h)
                     if MAPS[1].passable_terrain(j % MAPS[1].w,
                                                 j // MAPS[1].w, 0)]))
H.check_true('크기 2 통행 칸은 크기 1 통행 칸의 부분집합',
             all(v >= 1 for v in c1 if v >= 2))
H.check('size_passable 는 clear >= s 와 같다',
        [FL.size_passable(c1, MAPS[1], j % MAPS[1].w, j // MAPS[1].w, 2)
         for j in range(20)],
        [c1[j] >= 2 for j in range(20)])
H.check('맵 밖은 어떤 크기로도 통행 불가',
        FL.size_passable(c1, MAPS[1], -1, 0, 1), False)

# ── 브러시파이어: 벨만-포드로 다시 풀어 비교 ────────────────────────────────
def brushfire_ref(m, kind):
    """같은 답을 아주 느리게 구하는 참조 구현 — 완화가 멈출 때까지 돈다."""
    n = m.w * m.h
    dist = [FL.INF] * n
    for y in range(m.h):
        for x in range(m.w):
            if not m.passable_terrain(x, y, kind):
                dist[y * m.w + x] = 0
            else:
                for d in range(8):
                    if not m.in_map(x + F.DX[d], y + F.DY[d]):
                        dist[y * m.w + x] = min(dist[y * m.w + x], F.DCOST[d])
    changed = True
    while changed:
        changed = False
        for y in range(m.h):
            for x in range(m.w):
                if not m.passable_terrain(x, y, kind):
                    continue
                j = y * m.w + x
                for d in range(8):
                    u, v = x + F.DX[d], y + F.DY[d]
                    if not m.in_map(u, v):
                        continue
                    nd = dist[v * m.w + u] + F.DCOST[d]
                    if nd < dist[j]:
                        dist[j] = nd
                        changed = True
    return dist


bad = 0
for m in MAPS[:4]:
    if FL.brushfire(m, 0) != brushfire_ref(m, 0):
        bad += 1
H.check('브러시파이어 == 참조 구현 (맵 4장)', bad, 0)

fire = FL.brushfire(FM, 0)
H.check('막힌 칸의 fire 는 0', fire[1 * FM.w + 1], 0)
H.check('가장자리 자유 칸의 fire 는 10 (맵 밖 = 막힌 칸)', fire[0], 10)
H.check_true('바위 덩어리 반대편으로 0 이 새지 않는다',
             fire[0 * FM.w + 6] > 0 and fire[2 * FM.w + 5] > 0)

# ── 한 번 계산하면 유닛 수와 무관하다 (§11.1 의 손익분기) ───────────────────
free = [j for j in range(FM.w * FM.h) if FM.passable_terrain(j % FM.w, j // FM.w, 0)]
bad = 0
for j in free[:40]:
    s = (j % FM.w, j // FM.w)
    if integ[j] >= FL.INF:
        continue
    if P.astar(FM, 0, s, (4, 4))[0] != integ[j]:
        bad += 1
H.check('적분장 값 == 그 칸에서 목표까지의 A* 비용 (%d칸)' % len(free[:40]), bad, 0)

H.done()
