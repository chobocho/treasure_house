# -*- coding: utf-8 -*-
"""화면 구성 — 레이어·스크롤·y 정렬·미니맵·패널 (SPEC §23)."""
from __future__ import print_function

import harness as H
from rts import const as C
from rts import raster as RS
from rts import render as RD
from rts import sim as SIM
from rts import spatial as S
from rts import tmap as T

H.title('render')

PAL = RS.build_palette()
LIGHT = RS.build_light(PAL)


def start_sim():
    m = T.TMap.load_text(H.golden('map_start.txt'))
    s = SIM.Sim(m, 1, 2)
    s.setup_start()
    return s


# ── SPEC §23.2 스크롤 ───────────────────────────────────────────────────────
m = T.TMap.load_text(H.golden('map_start.txt'))
v = RD.View()
H.check('처음 카메라는 (0,0)', [v.cam_x, v.cam_y], [0, 0])
v.move(m, -100, -100)
H.check('왼쪽 위로 넘어가지 않는다', [v.cam_x, v.cam_y], [0, 0])
v.move(m, 10000, 10000)
H.check('오른쪽 아래 한계는 맵 - 뷰포트',
        [v.cam_x, v.cam_y],
        [C.MAP_W * C.TILE - C.VIEW_W, C.MAP_H * C.TILE - C.VIEW_H])
H.check('그 값은 768', v.cam_x, 768)
v2 = RD.View()
v2.center_on(m, 32, 32)
H.check('가운데 정렬', [v2.cam_x, v2.cam_y],
        [32 * 16 - C.VIEW_W // 2, 32 * 16 - C.VIEW_H // 2])
v2.center_on(m, 0, 0)
H.check('가장자리에서는 클램프', [v2.cam_x, v2.cam_y], [0, 0])
H.check('카메라는 정수 픽셀', isinstance(v2.cam_x, int), True)

v3 = RD.View()
v3.cam_x, v3.cam_y = 100, 50
H.check('첫 타일과 오프셋', v3.first_tile(), (6, 3, 4, 2))
H.check('그릴 타일 수는 17열', RD.TILES_X, C.VIEW_W // C.TILE + 1)
H.check('가장자리 스크롤 — 왼쪽 8px 안', RD.edge_scroll(3, 100), (-RD.EDGE_SPEED, 0))
H.check('오른쪽', RD.edge_scroll(C.VIEW_W - 2, 100), (RD.EDGE_SPEED, 0))
H.check('위', RD.edge_scroll(100, 2), (0, -RD.EDGE_SPEED))
H.check('가운데는 안 움직인다', RD.edge_scroll(100, 100), (0, 0))
H.check('패널 위에서는 안 움직인다', RD.edge_scroll(300, 100), (0, 0))

# ── SPEC §23.3 y 정렬 ───────────────────────────────────────────────────────
s = start_sim()
order = RD.y_order(s.w)
keys = [RD.sort_key(s.w, i) for i in order]
H.check('발밑 y · x · 핸들 순', keys, sorted(keys))
H.check('살아 있는 것만', len(order),
        len([1 for i in range(1, C.MAX_ENT) if s.w.alive[i]]))
H.check('삽입 정렬이 표준 정렬과 같은 답을 낸다', order,
        sorted(order, key=lambda i: RD.sort_key(s.w, i)))
H.check('키는 전순서 — 같은 키가 둘일 수 없다', len(set(keys)), len(keys))

# ── SPEC §23.4 미니맵 ───────────────────────────────────────────────────────
H.check('64 맵을 64 픽셀에 — 한 타일이 한 픽셀', RD.minimap_nearest(m, 10, 20),
        m.terrain[20 * m.w + 10])
H.check('축소 코드도 있다 (128 맵을 대비)',
        RD.minimap_nearest(m, 0, 0), m.terrain[0])
maj = RD.minimap_majority(m, 5, 5)
H.check_true('다수결도 같은 크기에서는 같은 답', maj == RD.minimap_nearest(m, 5, 5))
H.check('미니맵 클릭의 역변환', RD.minimap_to_tile(32, 48), (32, 48))
vv = RD.View()
vv.center_on(m, *RD.minimap_to_tile(32, 32))
H.check('클릭한 타일이 뷰포트 중앙에 온다',
        [vv.cam_x + C.VIEW_W // 2, vv.cam_y + C.VIEW_H // 2],
        [32 * 16, 32 * 16])

# ── SPEC §23.1 레이어 ───────────────────────────────────────────────────────
fb = RS.Frame()
RD.draw(fb.fb, s, RD.View(), 0, PAL, LIGHT, 0, [], '')
H.check('프레임버퍼를 다 채운다', len([1 for v in fb.fb if v == 0]) < 320 * 200,
        True)
H.check('패널 영역에도 그린다',
        max(fb.fb[10 * 320 + C.PANEL_X:10 * 320 + 320]) > 0, True)
H.check('하단 바에도 그린다',
        max(fb.fb[(C.BAR_Y + 10) * 320:(C.BAR_Y + 10) * 320 + 256]) > 0, True)

fb2 = RS.Frame()
RD.draw(fb2.fb, s, RD.View(), 0, PAL, LIGHT, 0, [], '')
H.check('같은 상태면 같은 그림', fb.fb, fb2.fb)
ppm = RS.to_ppm(fb.fb, PAL)
H.check('PPM 192,015바이트', len(ppm), 192015)

# ── 안개 ────────────────────────────────────────────────────────────────────
view = RD.View()
view.center_on(m, 8, 8)                      # 0번 기지
lit = RS.Frame()
RD.draw(lit.fb, s, view, 0, PAL, LIGHT, 0, [], '')
dark = RS.Frame()
RD.draw(dark.fb, s, view, 0, PAL, LIGHT, 1, [], '')   # 1번 시야로 같은 곳
H.check_true('남의 시야로 보면 어둡다',
             len([1 for v in dark.fb[:C.VIEW_H * 320] if v == 0])
             > len([1 for v in lit.fb[:C.VIEW_H * 320] if v == 0]))
H.check('미탐험은 완전한 검정', dark.fb[10 * 320 + 10], 0)

enemy_visible = RD.visible_entities(s, 1)
H.check('1번 플레이어는 0번 유닛을 못 본다',
        [i for i in enemy_visible if s.w.owner[i] == 0], [])
own = RD.visible_entities(s, 0)
H.check_true('제 유닛은 본다', len(own) > 0)
H.note('명암표는 어둡게 만들 뿐이라 유닛 숨기기는 2단계에서 걸러야 한다')

# ── 선택 표시와 체력바 ──────────────────────────────────────────────────────
hq = [i for i in range(1, C.MAX_ENT)
      if s.w.alive[i] and s.w.owner[i] == 0 and s.w.kind[i] == C.HQ][0]
fb3 = RS.Frame()
RD.draw(fb3.fb, s, view, 0, PAL, LIGHT, 0, [s.w.handle(hq)], '')
H.check_true('선택하면 그림이 달라진다', fb3.fb != lit.fb)
s.w.hp[hq] = C.HP[C.HQ] // 2
fb4 = RS.Frame()
RD.draw(fb4.fb, s, view, 0, PAL, LIGHT, 0, [s.w.handle(hq)], '')
H.check_true('체력이 줄면 체력바도 달라진다', fb4.fb != fb3.fb)

# ── 하단 바 ─────────────────────────────────────────────────────────────────
fb5 = RS.Frame()
RD.draw(fb5.fb, s, view, 0, PAL, LIGHT, 0, [], 'BASE UNDER ATTACK')
H.check_true('메시지를 쓰면 하단 바가 달라진다',
             fb5.fb[(C.BAR_Y):] != fb.fb[(C.BAR_Y):])
H.check('자릿수는 고정 폭', RD.credits_text(50), '   50')
H.check('큰 수도 다섯 자리', RD.credits_text(12345), '12345')
H.check('넘치면 잘라 붙인다', RD.credits_text(1234567), '99999')

# ── 팔레트 사이클은 그림을 바꾸지 않는다 (팔레트만 바뀐다) ──────────────────
fb6 = RS.Frame()
fb7 = RS.Frame()
RD.draw(fb6.fb, s, view, 0, PAL, LIGHT, 0, [], '')
RD.draw(fb7.fb, s, view, 3, PAL, LIGHT, 0, [], '')
H.check('사이클 위상은 프레임버퍼를 바꾸지 않는다', fb7.fb, fb6.fb)
H.note('물 애니메이션은 팔레트만 돌린다 — 그래서 공짜다')

H.done()
