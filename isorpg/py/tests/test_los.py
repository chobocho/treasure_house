# -*- coding: utf-8 -*-
"""시야 — 브레젠험, 대칭성, 안개, 조명 단계."""
from __future__ import print_function

import harness as H
from isorpg import gamemap as M
from isorpg import los as L

H.title('los')

# ---- 브레젠험 기본 성질
H.check('한 점', L.line(3, 3, 3, 3), [(3, 3)])
H.check('가로', L.line(0, 0, 4, 0), [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)])
H.check('대각', L.line(0, 0, 3, 3), [(0, 0), (1, 1), (2, 2), (3, 3)])
bad = 0
for x1 in range(-12, 13):
    for y1 in range(-12, 13):
        pts = L.line(0, 0, x1, y1)
        if pts[0] != (0, 0) or pts[-1] != (x1, y1):
            bad += 1
        for i in range(len(pts) - 1):
            dx = abs(pts[i + 1][0] - pts[i][0])
            dy = abs(pts[i + 1][1] - pts[i][1])
            if dx > 1 or dy > 1 or (dx == 0 and dy == 0):
                bad += 1
        if len(pts) != max(abs(x1), abs(y1)) + 1:
            bad += 1
H.check('브레젠험 25x25 성질 (끝점·연결성·길이)', bad, 0)

# ---- 뒤집으면 같은 점 집합인가 (대칭성은 보장되지 않는다 — 실제로 세어 본다)
asym = 0
for x1 in range(-12, 13):
    for y1 in range(-12, 13):
        a = set(L.line(0, 0, x1, y1))
        b = set(L.line(x1, y1, 0, 0))
        if a != b:
            asym += 1
H.note('브레젠험 역방향과 다른 선 %d개 / 625', asym)

m = M.gen_map()

# ---- 벽 너머는 안 보인다
H.check_true('자기 자신은 보인다', L.visible(m, 24, 25, 24, 25))
H.check_true('북문(24,18)은 길이라 그 너머가 보인다', L.visible(m, 24, 25, 24, 17))
H.check_true('벽(22,18) 너머는 안 보인다', not L.visible(m, 22, 25, 22, 16))

# ---- 안개
fog = L.Fog(48, 48)
H.check('처음엔 아무것도 안 봤다', sum(fog.count_seen() for _ in [0]), 0)
fog.update(m, 24, 34)
seen1 = fog.count_seen()
vis1 = fog.count_visible()
H.check_true('갱신하면 주변이 보인다 (%d칸)' % vis1, vis1 > 0)
H.check_true('본 칸 >= 보이는 칸', seen1 >= vis1)
H.check_true('시야 반경 안에만 보인다',
             all(abs(x - 24) <= L.SIGHT_R and abs(y - 34) <= L.SIGHT_R
                 for y in range(48) for x in range(48) if fog.is_visible(x, y)))
fog.update(m, 24, 30)
H.check_true('한 번 본 칸은 기억한다', fog.count_seen() >= seen1)
H.check_true('시야 반경 밖은 보이지 않는다', not fog.is_visible(24, 45))
fog.update(m, 24, 20)
H.check_true('멀어져도 기억은 남는다 (%d칸)' % fog.count_seen(),
             fog.is_seen(24, 34) and not fog.is_visible(24, 34))

# ---- 조명 단계
fog.update(m, 24, 34)
H.check('발밑은 가장 밝다', fog.light_of(24, 34, 24, 34), 15)
H.check_true('멀수록 어둡다',
             fog.light_of(24 + 6, 34, 24, 34) < fog.light_of(24 + 1, 34, 24, 34))
H.check_true('보이는 칸의 조명은 7..15',
             all(7 <= fog.light_of(x, y, 24, 34) <= 15
                 for y in range(48) for x in range(48) if fog.is_visible(x, y)))
H.check('안 본 칸은 0', fog.light_of(0, 0, 24, 34), 0)

H.done()
