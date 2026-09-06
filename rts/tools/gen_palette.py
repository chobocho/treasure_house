# -*- coding: utf-8 -*-
"""팔레트와 명암표를 얼려 golden/palette.txt 로 남긴다 (SPEC §22.2).

   다른 gen_*.py 와 달리 이것은 **독립 구현이 아니라 동결기**다. 팔레트는
   알고리즘이 아니라 데이터이고, 같은 표를 두 번 구현해 봐야 같은 실수를
   두 번 하거나 서로 다른 표를 갖게 될 뿐이다. SPEC §22.2 의 표가 기준이고,
   이 파일은 그것을 바이트로 굳혀 세 언어가 대조할 대상을 만든다.

   실행:  python3 tools/gen_palette.py
"""
import io
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLDEN = os.path.join(BASE, 'golden')

EGA = [(0, 0, 42), (0, 42, 0), (0, 42, 42), (42, 0, 0), (42, 0, 42),
       (42, 21, 0), (42, 42, 42), (21, 21, 21), (21, 21, 63), (21, 63, 21),
       (21, 63, 63), (63, 21, 21), (63, 21, 63), (63, 63, 21), (63, 63, 63)]
PLAYER_RAMP = [((16, 4, 4), (63, 26, 26)), ((4, 8, 20), (26, 38, 63)),
               ((4, 18, 6), (26, 56, 26)), ((20, 16, 4), (63, 58, 20))]
TERRAIN_RAMP = [((24, 14, 6), (46, 34, 18)), ((44, 40, 26), (18, 18, 20)),
                ((20, 20, 22), (40, 40, 42)), ((6, 10, 30), (22, 34, 54)),
                ((40, 32, 4), (63, 58, 26)), ((0, 0, 0), (30, 30, 30))]
UI = [(0, 0, 0), (10, 10, 12), (20, 20, 24), (30, 30, 34), (42, 42, 46),
      (52, 52, 56), (63, 63, 63), (63, 52, 20), (52, 20, 20), (20, 52, 20),
      (20, 20, 52), (40, 40, 10), (30, 8, 8), (8, 30, 8), (8, 8, 30),
      (32, 32, 32)]

FNV_OFFSET, FNV_PRIME = 2166136261, 16777619


def fnv1a(data):
    h = FNV_OFFSET
    for b in bytearray(data):
        h = ((h ^ b) * FNV_PRIME) % 4294967296
    return h


def ramp(c0, c1, i):
    return tuple(c0[k] + (c1[k] - c0[k]) * i // 7 for k in range(3))


def build_palette():
    pal = [(0, 0, 0)] * 256
    for k in range(15):
        pal[1 + k] = EGA[k]
    for i in range(16):
        g = i * 63 // 15
        pal[16 + i] = (g, g, g)
    for p in range(4):
        c0, c1 = PLAYER_RAMP[p]
        for i in range(8):
            pal[160 + p * 8 + i] = ramp(c0, c1, i)
    for i in range(16):
        pal[192 + i] = UI[i]
    for r in range(6):
        c0, c1 = TERRAIN_RAMP[r]
        for i in range(8):
            pal[208 + r * 8 + i] = ramp(c0, c1, i)
    return pal


def build_light(pal):
    """명암 단계 l 에서 색 c 에 가장 가까운 팔레트 항목. 동점이면 인덱스 최소."""
    out = []
    for l in range(4):
        row = []
        for c in range(256):
            want = tuple(pal[c][k] * l // 3 for k in range(3))
            best, bd = 0, None
            for j in range(256):
                d = sum((pal[j][k] - want[k]) ** 2 for k in range(3))
                if bd is None or d < bd:
                    bd, best = d, j
            row.append(best)
        out.append(row)
    return out


def main():
    pal = build_palette()
    light = build_light(pal)
    o = ['# SPEC §22.2 팔레트 (성분 0..63) — 인덱스 r g b']
    for i in range(256):
        o.append('%3d %2d %2d %2d' % ((i,) + tuple(pal[i])))
    o.append('# 명암표 각 단계의 FNV-1a')
    for l in range(4):
        blob = bytes(bytearray(light[l]))
        o.append('light %d 0x%08X' % (l, fnv1a(blob)))
    o.append('# 팔레트 전체의 FNV-1a')
    flat = bytearray()
    for i in range(256):
        flat += bytearray(pal[i])
    o.append('palette 0x%08X' % fnv1a(bytes(flat)))
    io.open(os.path.join(GOLDEN, 'palette.txt'), 'w',
            encoding='utf-8').write('\n'.join(o) + '\n')
    print('golden/palette.txt — 256색 · 명암표 4단계')


main()
