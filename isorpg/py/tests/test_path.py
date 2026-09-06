# -*- coding: utf-8 -*-
"""경로 — 허용성·일관성·모서리 자르기·A* == 다익스트라."""
from __future__ import print_function

import harness as H
from isorpg import gamemap as M
from isorpg import path as P

H.title('path')

m = M.gen_map()

# ---- 방향표
H.check('방향 8개', (len(P.DIRX), len(P.DIRY)), (8, 8))
H.check('대각 표시', P.DIAG, [False, True, False, True, False, True, False, True])
H.check('걸음 기본값', P.STEP_BASE, [10, 14, 10, 14, 10, 14, 10, 14])

# ---- 옥타일 골든
H.check('h((0,0),(0,0))', P.octile(0, 0, 0, 0), 0)
H.check('h((0,0),(1,0))', P.octile(0, 0, 1, 0), 8)
H.check('h((0,0),(1,1))', P.octile(0, 0, 1, 1), 11)
H.check('h((0,0),(47,47))', P.octile(0, 0, 47, 47), 526)

# ---- 허용성: 다익스트라 실제 비용 >= h
start = (24, 34)
dist = P.dijkstra(m, start[0], start[1])
bad = worst = 0
for y in range(48):
    for x in range(48):
        d = dist[y * 48 + x]
        if d is None:
            continue
        h = P.octile(start[0], start[1], x, y)
        if h > d:
            bad += 1
            worst = max(worst, h - d)
H.check('허용성 위반 (실제 비용 < h)', bad, 0)

# ---- 일관성: 모든 간선에서 h(a)-h(n) <= cost
goal = (24, 20)
bad = 0
for y in range(48):
    for x in range(48):
        if not P.passable(m, x, y):
            continue
        for d in range(8):
            nx, ny = x + P.DIRX[d], y + P.DIRY[d]
            if not P.step_ok(m, x, y, d):
                continue
            if P.octile(x, y, goal[0], goal[1]) - P.octile(nx, ny, goal[0], goal[1]) \
                    > P.step_cost(m, nx, ny, d):
                bad += 1
H.check('일관성 위반 간선', bad, 0)

# ---- 모서리 자르기 금지
cut = 0
for y in range(1, 47):
    for x in range(1, 47):
        for d in (1, 3, 5, 7):
            if P.step_ok(m, x, y, d):
                if not (P.passable(m, x + P.DIRX[d], y) and P.passable(m, x, y + P.DIRY[d])):
                    cut += 1
H.check('막힌 모서리를 대각으로 통과한 사례', cut, 0)

# ---- 오르막 제한
bad = 0
for y in range(47):
    for x in range(47):
        for d in range(8):
            nx, ny = x + P.DIRX[d], y + P.DIRY[d]
            if not m.inside(nx, ny) or not P.step_ok(m, x, y, d):
                continue
            if abs(M.height_of(m.at(nx, ny)) - M.height_of(m.at(x, y))) > P.CLIMB_MAX:
                bad += 1
H.check('오르막 제한 위반', bad, 0)

# ---- A* 가 다익스트라와 같은 비용을 내는가
targets = [(24, 20), (20, 20), (29, 29), (24, 44), (18, 24), (26, 26), (2, 2)]
same = miss = 0
for gx, gy in targets:
    got = P.astar(m, start[0], start[1], gx, gy)
    want = dist[gy * 48 + gx]
    if want is None:
        miss += 1
        H.check('A* 도 못 감 (%d,%d)' % (gx, gy), got[0], None)
        continue
    H.check('A* 비용 == 다익스트라 (%d,%d)' % (gx, gy), got[1], want)
    same += 1
H.note('도달 가능 %d개 / 도달 불가 %d개', same, miss)

# ---- 경로가 실제로 이어지는가
path, cost, expanded = P.astar(m, start[0], start[1], 24, 20)
H.check('경로 시작', path[0], start)
H.check('경로 끝', path[-1], (24, 20))
bad = 0
tot = 0
for i in range(len(path) - 1):
    (ax, ay), (bx, by) = path[i], path[i + 1]
    dd = [d for d in range(8) if P.DIRX[d] == bx - ax and P.DIRY[d] == by - ay]
    if not dd or not P.step_ok(m, ax, ay, dd[0]):
        bad += 1
    else:
        tot += P.step_cost(m, bx, by, dd[0])
H.check('경로 각 걸음이 합법', bad, 0)
H.check('걸음 비용 합 == A* 비용', tot, cost)
H.note('A* 확장 노드 %d개 (다익스트라 전체 %d칸)', expanded,
       sum(1 for d in dist if d is not None))
H.check_true('A* 가 다익스트라보다 적게 본다',
             expanded < sum(1 for d in dist if d is not None))

# ---- 양동이 큐 경계
H.check_true('최대 간선 비용 < BUCKET_N',
             max(P.step_cost(m, x, y, d) for y in range(48) for x in range(48)
                 for d in range(8) if P.passable(m, x, y)) < P.BUCKET_N)

H.done()
