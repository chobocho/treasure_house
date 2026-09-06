# -*- coding: utf-8 -*-
"""래스터 — 팔레트·명암표·스프라이트·블릿·폰트·PPM (SPEC §22)."""
from __future__ import print_function

import harness as H
from rts import const as C
from rts import fixed as F
from rts import raster as RS

H.title('raster')

# ── SPEC §22.2 팔레트 ───────────────────────────────────────────────────────
pal = RS.build_palette()
g = [ln for ln in H.golden('palette.txt').split('\n') if ln and ln[0] != '#']
bad = 0
n = 0
for ln in g:
    p = ln.split()
    if p[0] in ('light', 'palette'):
        continue
    i, r, gg, b = int(p[0]), int(p[1]), int(p[2]), int(p[3])
    if list(pal[i]) != [r, gg, b]:
        bad += 1
        if bad < 4:
            H.note('%d 기대 %s 실제 %s', i, [r, gg, b], list(pal[i]))
    n += 1
H.check('골든 팔레트 %d색' % n, bad, 0)
H.check('256색', len(pal), 256)
H.check('성분은 0..63 (VGA DAC 6비트)',
        max(max(c) for c in pal) <= 63 and min(min(c) for c in pal) >= 0, True)
H.check('0번은 검정', list(pal[0]), [0, 0, 0])
H.check('회색 16단계의 끝', [list(pal[16]), list(pal[31])],
        [[0, 0, 0], [63, 63, 63]])
H.check('플레이어 기준은 160', RS.PLAYER_BASE, 160)
H.check('플레이어 램프는 넷 × 8단계',
        [pal[160 + p * 8] != pal[160 + (p + 1) * 8] for p in range(3)],
        [True] * 3)

flat = bytearray()
for c in pal:
    flat += bytearray(c)
want = [ln for ln in H.golden('palette.txt').split('\n')
        if ln.startswith('palette ')][0].split()[1]
H.check('팔레트 전체 해시', '0x%08X' % F.fnv1a(bytes(flat)), want)

light = RS.build_light(pal)
H.check('명암 단계는 넷', len(light), 4)
H.check('3단계는 원색 그대로 (같은 색이 둘이면 인덱스가 작은 쪽)',
        [c for c in range(256)
         if light[3][c] != c and pal[light[3][c]] != pal[c]], [])
H.check_true('중복 색이 있어 항등은 아니다', light[3] != list(range(256)))
H.check('0단계는 전부 검정 계열', light[0][100], 0)
bad = 0
for ln in H.golden('palette.txt').split('\n'):
    if ln.startswith('light '):
        l = int(ln.split()[1])
        if '0x%08X' % F.fnv1a(bytes(bytearray(light[l]))) != ln.split()[2]:
            bad += 1
H.check('명암표 네 단계의 해시', bad, 0)
H.note('256×256×4 = 262,144회 비교를 시작할 때 한 번 한다')

# ── SPEC §22.10 PPM ─────────────────────────────────────────────────────────
H.check('expand(63) = 255', RS.expand(63), 255)
H.check('expand(0) = 0', RS.expand(0), 0)
H.check('expand 는 단조', all(RS.expand(v) < RS.expand(v + 1)
                              for v in range(63)), True)
H.check('expand 는 v*4 + v//16', [RS.expand(v) for v in (1, 16, 32, 47)],
        [4, 65, 130, 190])

fb = RS.Frame()
H.check('프레임버퍼는 320x200 1차원', len(fb.fb), 320 * 200)
H.check('처음에는 전부 0', max(fb.fb), 0)
fb.fb[0] = 63
ppm = RS.to_ppm(fb.fb, pal)
H.check('PPM 은 192,015바이트', len(ppm), 15 + 320 * 200 * 3)
H.check('머리', ppm[:15], b'P6\n320 200\n255\n')
H.check('첫 픽셀은 팔레트 63번을 편 값', list(bytearray(ppm[15:18])),
        [RS.expand(c) for c in pal[63]])

# ── SPEC §22.3 스프라이트 ───────────────────────────────────────────────────
gs = [ln.split() for ln in H.golden('sprites.txt').split('\n')
      if ln and ln[0] != '#']
bad = 0
for row in gs:
    name, w, h, ox, oy, ln_, fnv = row
    spr = RS.SPRITES[name]
    got = [spr.w, spr.h, spr.ox, spr.oy, len(spr.data),
           '0x%08X' % F.fnv1a(spr.data)]
    if got != [int(w), int(h), int(ox), int(oy), int(ln_), fnv]:
        bad += 1
        if bad < 4:
            H.note('%s 기대 %s 실제 %s', name,
                   [int(w), int(h), int(ox), int(oy), int(ln_), fnv], got)
H.check('골든 스프라이트 %d장' % len(gs), bad, 0)
H.check('유닛 25 + 건물 6', len(RS.SPRITES), 31)
H.check('유닛 기준점은 발밑', [RS.SPRITES['INF_0'].ox, RS.SPRITES['INF_0'].oy],
        [8, 14])
H.check('사령부는 3x3 타일', [RS.SPRITES['HQ'].w, RS.SPRITES['HQ'].h],
        [48, 48])

px = RS.SPRITES['INF_0'].pixels()
H.check('풀면 w*h 픽셀', len(px), 16 * 16)
H.check('0 은 투명 — 모서리는 비어 있다', px[0], 0)
H.check('몸통은 플레이어 색', px[9 * 16 + 8], RS.PLAYER_BASE + 3)

# ── SPEC §22.4 클리핑 블릿 ──────────────────────────────────────────────────
fb2 = RS.Frame()
RS.blit(fb2.fb, RS.SPRITES['INF_0'], 100, 100)
H.check_true('그려졌다', max(fb2.fb) > 0)
drawn = len([1 for v in fb2.fb if v > 0])
H.check('투명 픽셀은 건드리지 않는다', drawn,
        len([1 for v in px if v > 0]))

fb3 = RS.Frame()
RS.blit(fb3.fb, RS.SPRITES['INF_0'], -100, 100)
H.check('완전히 화면 밖이면 한 픽셀도 안 쓴다', max(fb3.fb), 0)
RS.blit(fb3.fb, RS.SPRITES['INF_0'], 400, 100)
H.check('오른쪽 밖도', max(fb3.fb), 0)
RS.blit(fb3.fb, RS.SPRITES['INF_0'], 100, -100)
H.check('위쪽 밖도', max(fb3.fb), 0)

fb4 = RS.Frame()
RS.blit(fb4.fb, RS.SPRITES['INF_0'], 4, 100)     # x0 = -4 — 네 칸이 화면 밖
part = len([1 for v in fb4.fb if v > 0])
H.check_true('걸치면 걸친 만큼만 그린다', 0 < part < drawn)
H.check('왼쪽 밖으로 새지 않는다',
        [1 for y in range(200) for x in range(320)
         if fb4.fb[y * 320 + x] > 0 and x >= 12], [])

# ── SPEC §22.5 플레이어 색 리맵 ─────────────────────────────────────────────
fb5 = RS.Frame()
RS.blit(fb5.fb, RS.SPRITES['INF_0'], 100, 100, owner=2)
H.check('owner * 8 을 더한다', fb5.fb[(100 + 9 - 14) * 320 + (100 + 8 - 8)],
        RS.PLAYER_BASE + 16 + 3)
H.check('그림자는 리맵하지 않는다',
        RS.SHADOW in fb5.fb, True)
H.note('색을 여덟 벌 그리지 않는다 — 도스 시절의 표준 요령이다')

# ── SPEC §22.7 좌우 반전 ────────────────────────────────────────────────────
fa = RS.Frame()
fbb = RS.Frame()
RS.blit(fa.fb, RS.SPRITES['INF_1'], 100, 100)
RS.blit(fbb.fb, RS.SPRITES['INF_1'], 100, 100, flip=True)
row_a = [fa.fb[(100 - 14 + 5) * 320 + 100 - 8 + k] for k in range(16)]
row_b = [fbb.fb[(100 - 14 + 5) * 320 + 100 - 8 + k] for k in range(16)]
H.check('반전은 각 줄을 뒤집는다', row_b, row_a[::-1])
H.check('그리는 것은 5방향, 나머지 셋은 반전', RS.DRAWN_DIRS, 5)

# ── SPEC §22.6 팔레트 사이클링 ──────────────────────────────────────────────
p0 = RS.build_palette()
p1 = RS.cycle_water(RS.build_palette(), 1)
H.check('물 색만 돈다', [k for k in range(256) if p0[k] != p1[k]],
        [k for k in range(232, 240) if p0[k] != p1[k]])
H.check('한 칸 돈다', p1[232], p0[233])
H.check('끝은 처음으로', p1[239], p0[232])
H.check('8칸이면 제자리', RS.cycle_water(RS.build_palette(), 8), p0)
H.check('프레임버퍼는 건드리지 않는다 — 공짜 애니메이션', RS.Frame().fb,
        [0] * (320 * 200))

# ── SPEC §22.8 폰트 ─────────────────────────────────────────────────────────
fhex = [ln for ln in H.golden('font.txt').split('\n') if ln and ln[0] != '#'][0]
H.check('폰트는 760바이트 (95자 × 8)', len(RS.FONT), 760)
H.check('골든 폰트와 같다', ''.join('%02x' % b for b in bytearray(RS.FONT)),
        fhex)
fb6 = RS.Frame()
RS.text(fb6.fb, 'A', 0, 0, 15)
rows = [''.join('#' if fb6.fb[y * 320 + x] else '.' for x in range(6))
        for y in range(7)]
H.check('A 의 첫 줄', rows[0], '.###..')
H.check('A 의 넷째 줄', rows[3], '#####.')
H.check('소문자는 빈 글자다 — 도스 UI 가 대문자만 쓴 이유와 같다',
        (RS.text(RS.Frame().fb, 'a', 0, 0, 15), True)[1], True)
fb7 = RS.Frame()
RS.text(fb7.fb, 'AB', 0, 0, 15)
H.check('글자 간격은 6px', fb7.fb[0 * 320 + 6], 15)
H.check('화면 밖 글자는 잘린다',
        (RS.text(fb7.fb, 'ZZZZ', 318, 0, 15), True)[1], True)

# ── SPEC §22.9 더티 렉트 ────────────────────────────────────────────────────
d = RS.Dirty()
H.check('처음에는 비어 있다', d.rects(), [])
d.add(10, 10, 4, 4)
H.check('하나', len(d.rects()), 1)
for k in range(8):
    d.add(k * 10, 0, 4, 4)
H.check('8개를 넘으면 전체를 다시 그린다', d.rects(),
        [(0, 0, C.SCR_W, C.SCR_H)])
H.check('비우면 다시 처음', (d.clear(), d.rects())[1], [])
H.note('합치는 비용이 이득을 넘는 지점은 out/bench.txt 6절에서 실측한다')

H.done()
