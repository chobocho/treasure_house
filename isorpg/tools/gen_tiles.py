# -*- coding: utf-8 -*-
"""golden/tiles.rle 생성 — 스프라이트 뱅크.

   지형 마름모와 큐브는 절차적으로 그리고(베이어 디더 + 모서리 강조),
   캐릭터·상자·나무 같은 물체는 아스키 아트로 찍는다.
   아스키 쪽이 손으로 다듬기 훨씬 쉽고, 색은 팔레트 램프 이름으로 가리킨다.

   실행:  python3 tools/gen_tiles.py
"""
import io
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, 'tools'))
import gen_palette as P                                        # noqa: E402

RAMP = {name: P.RAMP_LO + k * P.RAMP_LEN for k, (name, _, _) in enumerate(P.RAMPS)}


def shade(ramp, level):
    """램프 안에서 0..15 단계를 고른다. 범위를 벗어나면 자른다."""
    return RAMP[ramp] + max(0, min(15, level))


# 지형 id -> (램프, 어두운 단계, 밝은 단계, 디더 문턱 0..16)
# 문턱이 클수록 밝은 픽셀이 많다. 0이면 전부 어두운 색.
TERRAIN_ART = [
    ('water',  6, 9, 8),      # 0 DEEP
    ('water',  9, 12, 8),     # 1 WATER
    ('sand',   9, 12, 6),     # 2 SAND
    ('grass',  7, 11, 5),     # 3 GRASS
    ('dirt',   7, 10, 6),     # 4 DIRT
    ('rock',   7, 10, 7),     # 5 ROCK
    ('forest', 5, 9, 9),      # 6 FOREST
    ('rock',   10, 14, 5),    # 7 MOUNTAIN
    ('road',   8, 11, 4),     # 8 ROAD
    ('floor',  9, 12, 3),     # 9 FLOOR
    ('wall',   8, 12, 4),     # 10 WALL
    ('wood',   8, 12, 7),     # 11 BRIDGE
    ('snow',   11, 15, 4),    # 12 SNOW
    ('swamp',  5, 8, 10),     # 13 SWAMP
    ('lava',   7, 14, 9),     # 14 LAVA
    ('rock',   2, 4, 4),      # 15 VOID
]

# 4x4 베이어 행렬 — 도스 시절 디더링의 표준. 값 0..15
BAYER = [0, 8, 2, 10,
         12, 4, 14, 6,
         3, 11, 1, 9,
         15, 7, 13, 5]

TW, TH, TZ = 32, 16, 8


def diamond_rows():
    """마름모가 차지하는 픽셀을 screen_to_tile 규칙에서 그대로 뽑는다.

       손으로 그린 마름모를 쓰면 픽킹 결과와 한 픽셀씩 어긋난다. 그리는 모양과
       고르는 모양이 같아야 한다는 것이 이 함수의 존재 이유다.
    """
    rows = []
    for y in range(TH):
        xs = [x for x in range(TW)
              if (x - 16 + 2 * y) // 32 == 0 and (2 * y - x + 16) // 32 == 0]
        rows.append((min(xs), max(xs)) if xs else None)
    return rows


DIA = diamond_rows()


def tile_pixels(tid):
    """지형 마름모 32x16. 색 0은 투명."""
    ramp, lo, hi, thr = TERRAIN_ART[tid]
    px = [[0] * TW for _ in range(TH)]
    for y in range(TH):
        if DIA[y] is None:
            continue
        a, b = DIA[y]
        for x in range(a, b + 1):
            lv = hi if BAYER[(y % 4) * 4 + (x % 4)] < thr else lo
            # 위쪽 모서리는 한 단계 밝게, 아래쪽 모서리는 한 단계 어둡게 —
            # 마름모 하나가 평면이 아니라 면으로 보이게 하는 최소한의 장치다.
            if y < TH // 2 and (x == a or x == b):
                lv += 2
            elif y >= TH // 2 and (x == a or x == b):
                lv -= 2
            px[y][x] = shade(ramp, lv)
    return px


def cube_pixels(tid):
    """높이 한 단계짜리 큐브 32x24 — 윗면(마름모) + 옆면 8픽셀."""
    ramp, lo, hi, thr = TERRAIN_ART[tid]
    top = tile_pixels(tid)
    px = [[0] * TW for _ in range(TH + TZ)]
    for y in range(TH):
        px[y] = list(top[y])
    # 열마다 마름모의 마지막 행을 찾아 그 아래로 TZ 픽셀을 옆면으로 채운다
    for x in range(TW):
        last = -1
        for y in range(TH):
            if top[y][x]:
                last = y
        if last < 0:
            continue
        for k in range(1, TZ + 1):
            # 왼쪽 면은 더 어둡게, 오른쪽 면은 조금 어둡게 — 광원이 왼쪽 위에 있다고 본다
            lv = (lo - 4) if x < TW // 2 else (lo - 2)
            if k == TZ:
                lv -= 1                       # 바닥선 한 줄은 더 어둡게
            px[last + k][x] = shade(ramp, lv)
    return px


def art_pixels(art, palette_map):
    """아스키 아트 -> 픽셀. '.' 은 투명."""
    h = len(art)
    w = max(len(r) for r in art)
    px = [[0] * w for _ in range(h)]
    for y, row in enumerate(art):
        for x, ch in enumerate(row):
            if ch != '.':
                if ch not in palette_map:
                    raise KeyError('알 수 없는 아트 문자 %r' % ch)
                px[y][x] = palette_map[ch]
    return px


def mirror(px):
    return [list(reversed(row)) for row in px]


def rle_rows(px):
    """행마다 (개수, 색) 런으로 압축. 개수는 1..255."""
    out = []
    for row in px:
        runs = []
        i = 0
        while i < len(row):
            j = i
            while j < len(row) and row[j] == row[i] and j - i < 255:
                j += 1
            runs.append('%d:%d' % (j - i, row[i]))
            i = j
        out.append(' '.join(runs))
    return out


# ---------------------------------------------------------------- 아스키 아트
# h 머리 s 살 c 옷 d 옷그늘 b 신발 e 눈 m 금속 w 나무 g 잎 k 바위 y 금
ART_PAL = {
    'h': shade('dirt', 2),   's': shade('skin', 11), 'c': shade('cloth', 9),
    'd': shade('cloth', 4),  'b': shade('wood', 4),  'e': shade('rock', 1),
    'm': shade('rock', 12),  'w': shade('wood', 7),  'g': shade('forest', 9),
    'k': shade('rock', 8),   'y': shade('sand', 14), 'r': shade('lava', 12),
    'G': shade('grass', 10), 'W': shade('wood', 11), 'K': shade('rock', 12),
}

HERO_FRONT = [
    '................',
    '.....hhhhhh.....',
    '....hhhhhhhh....',
    '....hssssssh....',
    '....hssssssh....',
    '....ssessesss...',
    '....ssssssss....',
    '.....ssmmss.....',
    '......ssss......',
    '...cccccccccc...',
    '..cccccccccccc..',
    '..sccccccccccs..',
    '..scccccccccss..',
    '...cccccccccc...',
    '...cccccccccc...',
    '...dddddddddd...',
    '....dddddddd....',
    '....dd....dd....',
    '....dd....dd....',
    '....dd....dd....',
    '....bbb..bbb....',
    '....bbb..bbb....',
]
HERO_BACK = [
    '................',
    '.....hhhhhh.....',
    '....hhhhhhhh....',
    '....hhhhhhhh....',
    '....hhhhhhhh....',
    '....hhhhhhhh....',
    '....hhhhhhhh....',
    '.....hhhhhh.....',
    '......ssss......',
    '...cccccccccc...',
    '..cccccccccccc..',
    '..sccccccccccs..',
    '..sscccccccccs..',
    '...cccccccccc...',
    '...cccccccccc...',
    '...dddddddddd...',
    '....dddddddd....',
    '....dd....dd....',
    '....dd....dd....',
    '....dd....dd....',
    '....bbb..bbb....',
    '....bbb..bbb....',
]
MONSTER = [
    '................',
    '...kk......kk...',
    '...kkk....kkk...',
    '....kkkkkkkk....',
    '...kkkkkkkkkk...',
    '..kkrkkkkkkrkk..',
    '..kkkkkkkkkkkk..',
    '..kkkKKKKKKkkk..',
    '...kkkkkkkkkk...',
    '..kkkkkkkkkkkk..',
    '..kkkkkkkkkkkk..',
    '..kkkkkkkkkkkk..',
    '...kkkkkkkkkk...',
    '....kkkkkkkk....',
    '....kk....kk....',
    '....kk....kk....',
    '...kkk....kkk...',
    '...kkk....kkk...',
]
CHEST_C = [
    '................',
    '..wwwwwwwwwwww..',
    '.wWWWWWWWWWWWWw.',
    '.wWmmmmmmmmmmWw.',
    '.wWWWWWWWWWWWWw.',
    '.wwwwwwwwwwwwww.',
    '.wWWWWyyyyWWWWw.',
    '.wWWWWymmyWWWWw.',
    '.wWWWWyyyyWWWWw.',
    '.wWWWWWWWWWWWWw.',
    '.wWWWWWWWWWWWWw.',
    '.wwwwwwwwwwwwww.',
    '..wwwwwwwwwwww..',
    '................',
]
CHEST_O = [
    '..wwwwwwwwwwww..',
    '.wWWWWWWWWWWWWw.',
    '.wWmmmmmmmmmmWw.',
    '.wwwwwwwwwwwwww.',
    '................',
    '..yyyyyyyyyyyy..',
    '.wyyyyyyyyyyyyw.',
    '.wWyyyyyyyyyyWw.',
    '.wWWWWWWWWWWWWw.',
    '.wWWWWWWWWWWWWw.',
    '.wWWWWWWWWWWWWw.',
    '.wwwwwwwwwwwwww.',
    '..wwwwwwwwwwww..',
    '................',
]
NPC_FRONT = [r.replace('c', 'y').replace('d', 'w') for r in HERO_FRONT]
NPC_BACK = [r.replace('c', 'y').replace('d', 'w') for r in HERO_BACK]
TREE = [
    '........gggg........',
    '......gggggggg......',
    '.....gggggggggg.....',
    '....gggggggggggg....',
    '...gggggggggggggg...',
    '...gggggggggggggg...',
    '..gggggggggggggggg..',
    '..gggggggggggggggg..',
    '..gggggggggggggggg..',
    '...gggggggggggggg...',
    '....gggggggggggg....',
    '.....gggggggggg.....',
    '......gggggggg......',
    '........wwww........',
    '........wwww........',
    '........wwww........',
    '.......wwwwww.......',
    '.......wwwwww.......',
]
ROCK = [
    '......kkkkkk......',
    '....kkKKKKKKkk....',
    '...kKKKKKKKKKKk...',
    '..kKKKKKKKKKKKKk..',
    '..kKKKKKKKKKKKKk..',
    '.kkKKKKKKKKKKKKkk.',
    '.kkkKKKKKKKKKKkkk.',
    '..kkkkkkkkkkkkkk..',
]


def build_bank():
    """(name, w, h, ox, oy, 픽셀) 목록. 순서가 곧 스프라이트 id 다."""
    bank = []
    for t in range(16):
        bank.append(('tile_%d' % t, 16, 0, tile_pixels(t)))
    for t in range(16):
        bank.append(('cube_%d' % t, 16, 0, cube_pixels(t)))
    front = art_pixels(HERO_FRONT, ART_PAL)
    back = art_pixels(HERO_BACK, ART_PAL)

    def walk(px, frame):
        """프레임 1은 아랫부분 여섯 줄에서 두 다리를 바깥으로 한 픽셀씩 벌린다.

           행 전체를 밀면 몸통까지 어긋나 줄무늬가 생긴다. 좌우 반쪽을
           각각 바깥으로 미는 것이 가장 적은 손질로 걷는 느낌을 낸다.
        """
        if frame == 0:
            return px
        out = [list(r) for r in px]
        w = len(out[0])
        for y in range(len(out) - 6, len(out)):
            row = out[y]
            left = row[1:w // 2] + [0]
            right = [0] + row[w // 2:w - 1]
            out[y] = left + right
        return out

    for d, base in enumerate((front, mirror(front), back, mirror(back))):
        for f in range(2):
            bank.append(('hero_%d_%d' % (d, f), 8, 21, walk(base, f)))
    mon = art_pixels(MONSTER, ART_PAL)
    for f in range(2):
        bank.append(('mon_%d' % f, 8, 17, walk(mon, f)))
    bank.append(('chest_0', 8, 11, art_pixels(CHEST_C, ART_PAL)))
    bank.append(('chest_1', 8, 11, art_pixels(CHEST_O, ART_PAL)))
    npf = art_pixels(NPC_FRONT, ART_PAL)
    npb = art_pixels(NPC_BACK, ART_PAL)
    bank.append(('npc_0', 8, 21, npf))
    bank.append(('npc_1', 8, 21, mirror(npb)))
    bank.append(('tree', 10, 17, art_pixels(TREE, ART_PAL)))
    bank.append(('rock', 9, 7, art_pixels(ROCK, ART_PAL)))
    return bank


def main():
    bank = build_bank()
    out = ['ISORPG-TILES 1 %d' % len(bank)]
    for i, (name, ox, oy, px) in enumerate(bank):
        h = len(px)
        w = len(px[0])
        out.append('SPRITE %d %s %d %d %d %d' % (i, name, w, h, ox, oy))
        out.extend(rle_rows(px))
    text = '\n'.join(out) + '\n'
    io.open(os.path.join(BASE, 'golden', 'tiles.rle'), 'w',
            encoding='utf-8').write(text)
    npix = sum(len(p) * len(p[0]) for _, _, _, p in bank)
    print('golden/tiles.rle  스프라이트 %d개  %d픽셀  %d바이트'
          % (len(bank), npix, len(text.encode('utf-8'))))


if __name__ == '__main__':
    main()
