# -*- coding: utf-8 -*-
"""통합 — 프레임 렌더, 정렬, 카메라, 화면이 실제로 그려지는가."""
from __future__ import print_function

import harness as H
from isorpg import camera as C
from isorpg import game as G
from isorpg import raster as R

H.title('engine')

# ---- 카메라 클램프
H.check('클램프 왼쪽', C.clamp_cam(-99999, 0)[0], C.WORLD_X0)
H.check('클램프 오른쪽', C.clamp_cam(99999, 0)[0], C.WORLD_X1 - R.SCR_W)
H.check('클램프 위', C.clamp_cam(0, -99999)[1], C.WORLD_Y0)
H.check('클램프 아래', C.clamp_cam(0, 99999)[1], C.WORLD_Y1 - R.SCR_H)
H.check_true('데드존 안에서는 안 움직인다',
             C.follow(0, 0, R.SCR_W // 2 + 10, R.SCR_H // 2 + 5)
             == C.clamp_cam(0, 0))
H.check_true('데드존 밖이면 따라간다',
             C.follow(0, 0, R.SCR_W // 2 + 200, R.SCR_H // 2)[0] != C.clamp_cam(0, 0)[0])

# ---- 한 프레임 렌더
g = G.Game()
# render() 는 내부 버퍼를 그대로 돌려준다(복사하지 않는다). 비교하려면 스냅샷을 떠야 한다.
fb = bytes(g.render())
H.check('프레임버퍼 크기', len(fb), 320 * 200)
H.check_true('화면이 비어 있지 않다', len(set(fb)) > 8)
H.check_true('그린 픽셀이 절반 넘는다', sum(1 for v in fb if v) > 320 * 200 // 2)

# ---- 같은 상태면 같은 그림
H.check('렌더는 순수하다 (같은 상태를 두 번 그리면 같다)', bytes(g.render()), fb)

# ---- 진행하면 그림이 바뀐다
for _ in range(40):
    g.tick()
H.check_true('40틱 뒤 화면이 달라진다', bytes(g.render()) != fb)

# ---- 정렬 순환 절단이 폭주하지 않는가
H.check_true('순환 절단 누적이 적다 (%d회)' % g.cycle_breaks, g.cycle_breaks < 50)

# ---- 팔레트 사이클링은 프레임버퍼를 건드리지 않는다
before = bytes(g.render())
g.pal_phase += 3
H.check('사이클링은 인덱스를 바꾸지 않는다', bytes(g.render()), before)
H.check_true('그런데 PPM 색은 바뀐다',
             g.render_ppm() != R.to_ppm(g.render(), R.load_palette()))

# ---- PPM 저장
ppm = g.render_ppm()
H.check('PPM 크기', len(ppm), 192015)

H.done()
