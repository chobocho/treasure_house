# -*- coding: utf-8 -*-
"""래스터 — 클리핑, 광원표, 더티 렉트, PPM."""
from __future__ import print_function

import harness as H
from isorpg import raster as R

H.title('raster')

pal = R.load_palette()
H.check('팔레트 256색', len(pal), 256)
H.check_true('DAC 는 6비트', all(0 <= c <= 63 for rgb in pal for c in rgb))
H.check('0번은 검정', pal[0], (0, 0, 0))

light = R.build_light(pal)
H.check('광원표 크기', len(light), 16 * 256)
H.check_true('15단계는 항등', all(light[15 * 256 + c] == c for c in range(256)))
H.check_true('0단계는 전부 검정에 가장 가까운 색',
             len(set(light[0 * 256 + c] for c in range(256))) <= 4)
H.check_true('단계가 낮을수록 밝기 합이 줄어든다',
             all(sum(sum(pal[light[l * 256 + c]]) for c in range(256))
                 <= sum(sum(pal[light[(l + 1) * 256 + c]]) for c in range(256))
                 for l in range(15)))

spr = R.load_sprites()
H.check('스프라이트 48개', len(spr), 48)
H.check('0번은 tile_0', (spr[0].name, spr[0].w, spr[0].h, spr[0].ox, spr[0].oy),
        ('tile_0', 32, 16, 16, 0))
H.check_true('모든 런의 합이 폭과 같다',
             all(sum(c for c, _ in row) == s.w for s in spr for row in s.rows))
H.check('마름모 픽셀 수 256',
        sum(c for row in spr[0].rows for c, v in row if v), 256)

# ---- 클리핑: 화면 밖, 걸침, 완전히 안
f = R.Frame()
f.clear(0)
f.blit_rle(spr[0], -1000, -1000, 15)
H.check('완전히 밖 (왼위)', sum(f.fb), 0)
f.blit_rle(spr[0], 1000, 1000, 15)
H.check('완전히 밖 (오른아래)', sum(f.fb), 0)
f.blit_rle(spr[0], 16, 0, 15)
H.check('안쪽 블릿 픽셀 수', sum(1 for v in f.fb if v), 256)
f.clear(0)
f.blit_rle(spr[0], 0, 0, 15)
H.check_true('왼쪽으로 걸치면 잘린다', 0 < sum(1 for v in f.fb if v) < 256)
f.clear(0)
f.blit_rle(spr[0], 16, R.SCR_H - 4, 15)
H.check_true('아래로 걸치면 잘린다', 0 < sum(1 for v in f.fb if v) < 256)
bad = 0
for x in range(-40, R.SCR_W + 40, 7):
    for y in range(-20, R.SCR_H + 20, 5):
        f.clear(0)
        f.blit_rle(spr[0], x, y, 15)
        if len(f.fb) != R.SCR_W * R.SCR_H:
            bad += 1
H.check('클리핑 중 버퍼 크기 불변', bad, 0)

# ---- 색 0 은 투명
f.clear(7)
f.blit_rle(spr[0], 16, 0, 15)
H.check_true('투명 픽셀은 배경이 남는다', f.px(0, 0) == 7)

# ---- 명암
f.clear(0)
f.blit_rle(spr[3], 16, 0, 15)
bright = sum(f.fb)
f.clear(0)
f.blit_rle(spr[3], 16, 0, 4)
H.check_true('어두운 단계가 더 어둡다', sum(f.fb) != bright)

# ---- 더티 렉트
d = R.Dirty()
d.add(10, 10, 20, 20)
d.add(15, 15, 20, 20)
d.merge()
H.check('겹치는 둘은 하나로', len(d.rects), 1)
d = R.Dirty()
d.add(0, 0, 10, 10)
d.add(300, 190, 40, 40)
d.merge()
H.check('먼 둘은 그대로', len(d.rects), 2)
H.check('화면 밖은 잘린다', d.rects[1], (300, 190, 20, 10))
d = R.Dirty()
d.add(-50, -50, 10, 10)
d.merge()
H.check('완전히 밖이면 버린다', len(d.rects), 0)

# ---- 팔레트 사이클링
p2 = R.cycle_palette(pal, 1)
H.check('물 구간이 한 칸 돈다', p2[R.WATER_LO], pal[R.WATER_LO + 1])
H.check('물 구간 끝이 앞으로', p2[R.WATER_HI], pal[R.WATER_LO])
H.check('물 밖은 그대로', p2[0:R.WATER_LO], pal[0:R.WATER_LO])
H.check('한 바퀴 돌면 원래대로', R.cycle_palette(pal, 16), pal)

# ---- PPM
f.clear(15)
ppm = R.to_ppm(f.fb, pal)
H.check('PPM 크기', len(ppm), 192015)
H.check('PPM 머리말', ppm[:15], b'P6\n320 200\n255\n')
H.check('흰색은 255,255,255', ppm[15:18], b'\xff\xff\xff')
f.clear(0)
H.check('검정은 0,0,0', R.to_ppm(f.fb, pal)[15:18], b'\x00\x00\x00')

H.done()
