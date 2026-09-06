# -*- coding: utf-8 -*-
"""스프라이트를 그려 golden/sprites.txt 로 얼린다 (SPEC §22.3).

   gen_palette.py 와 같은 이유로 이것도 **동결기**다. 다만 몸통 원만은
   정의(dx² + dy² <= r²)로 직접 그린다 — 엔진은 §6.2 의 덧셈만 쓰는 행 span
   알고리즘으로 같은 원을 그리므로, 이 파일과의 대조가 그 알고리즘의 검증이
   된다.

   실행:  python3 tools/gen_sprites.py
"""
import io
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLDEN = os.path.join(BASE, 'golden')

PLAYER_BASE = 160
SHADOW = 251
DX = [0, 1, 1, 1, 0, -1, -1, -1]
DY = [-1, -1, 0, 1, 1, 1, 0, -1]
R = [5, 4, 6, 5, 5]
M = [3, 3, 4, 3, 3]
UNIT_NAME = ['INF', 'ARCHER', 'TANK', 'MORTAR', 'HARV']
BLD = [(10, 'HQ', 3), (11, 'REF', 2), (12, 'BARR', 2), (13, 'FACT', 3),
       (14, 'POW', 2), (15, 'TOWER', 1)]

FNV_OFFSET, FNV_PRIME = 2166136261, 16777619


def fnv1a(data):
    h = FNV_OFFSET
    for b in bytearray(data):
        h = ((h ^ b) * FNV_PRIME) % 4294967296
    return h


def unit_sprite(k, d):
    w = h = 16
    px = [0] * (w * h)
    r = R[k]
    for y in range(h):
        for x in range(w):
            dx, dy = x - 8, y - 9
            q = dx * dx + dy * dy
            if q <= r * r:
                px[y * w + x] = (PLAYER_BASE + 1 if q > (r - 1) * (r - 1)
                                 else PLAYER_BASE + 3)
    for y in range(h):                       # 그림자는 몸통 아래 절반만
        for x in range(w):
            dx, dy = x - 8, y - 14
            if dy >= 0 and dx * dx + dy * dy <= 9 and px[y * w + x] == 0:
                px[y * w + x] = SHADOW
    mx, my = 8 + DX[d] * M[k], 9 + DY[d] * M[k]
    for y in range(my, my + 2):
        for x in range(mx, mx + 2):
            if 0 <= x < w and 0 <= y < h:
                px[y * w + x] = PLAYER_BASE + 6
    return w, h, 8, 14, px


def bld_sprite(foot):
    w = h = 16 * foot
    px = [0] * (w * h)
    for y in range(4, h - 2):
        for x in range(2, w - 2):
            edge = (x == 2 or x == w - 3 or y == 4 or y == h - 3)
            px[y * w + x] = PLAYER_BASE + (5 if edge else 2)
    for y in range(4, 7):
        for x in range(2, w - 2):
            px[y * w + x] = PLAYER_BASE + 6
    for y in range(h - 6, h - 2):
        for x in range(w // 2 - 2, w // 2 + 2):
            px[y * w + x] = PLAYER_BASE
    return w, h, w // 2, h - 2, px


def rle(px):
    out = bytearray()
    i = 0
    while i < len(px):
        v = px[i]
        run = 1
        while i + run < len(px) and px[i + run] == v and run < 255:
            run += 1
        out.append(run)
        out.append(v)
        i += run
    return bytes(out)


def main():
    o = ['# SPEC §22.3 스프라이트 — 이름 w h ox oy RLE바이트 FNV']
    total = 0
    for k in range(5):
        for d in range(5):
            w, h, ox, oy, px = unit_sprite(k, d)
            b = rle(px)
            total += len(b)
            o.append('%-10s %2d %2d %2d %2d %5d 0x%08X'
                     % ('%s_%d' % (UNIT_NAME[k], d), w, h, ox, oy,
                        len(b), fnv1a(b)))
    for (_kind, name, foot) in BLD:
        w, h, ox, oy, px = bld_sprite(foot)
        b = rle(px)
        total += len(b)
        o.append('%-10s %2d %2d %2d %2d %5d 0x%08X'
                 % (name, w, h, ox, oy, len(b), fnv1a(b)))
    o.append('# 합계 RLE 바이트 %d' % total)
    io.open(os.path.join(GOLDEN, 'sprites.txt'), 'w',
            encoding='utf-8').write('\n'.join(o) + '\n')
    print('golden/sprites.txt — 유닛 25 · 건물 6 · RLE %d바이트' % total)


main()
