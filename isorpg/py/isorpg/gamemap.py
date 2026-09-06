# -*- coding: utf-8 -*-
"""지형 맵 — SPEC §5. 한 칸 1바이트, 다이아몬드-스퀘어 생성, RLE 저장.

   모듈 이름이 map 이 아닌 것은 파이썬 내장 map 과 겹치지 않게 하려는 것이다.
   루아·타입스크립트 쪽도 같은 이름을 쓴다.
"""
from .rng import Rng

MAP_W = 48
MAP_H = 48
MAXH = 15

# 지형 id — 셀 바이트의 하위 4비트
(T_DEEP, T_WATER, T_SAND, T_GRASS, T_DIRT, T_ROCK, T_FOREST, T_MOUNTAIN,
 T_ROAD, T_FLOOR, T_WALL, T_BRIDGE, T_SNOW, T_SWAMP, T_LAVA, T_VOID) = range(16)

# (이름, 이동비용 0=불가, 시야차단)
TERRAIN = [
    ('DEEP', 0, False), ('WATER', 0, False), ('SAND', 12, False),
    ('GRASS', 10, False), ('DIRT', 10, False), ('ROCK', 14, False),
    ('FOREST', 16, True), ('MOUNTAIN', 0, True), ('ROAD', 8, False),
    ('FLOOR', 10, False), ('WALL', 0, True), ('BRIDGE', 10, False),
    ('SNOW', 13, False), ('SWAMP', 20, False), ('LAVA', 0, False),
    ('VOID', 0, True),
]
MOVE = [t[1] for t in TERRAIN]
OPAQUE = [t[2] for t in TERRAIN]
MIN_MOVE = min(v for v in MOVE if v > 0)          # ROAD 의 8


def make_cell(t, h):
    return t + h * 16


def terrain_of(cell):
    return cell % 16


def height_of(cell):
    return cell // 16


class Map(object):
    __slots__ = ('w', 'h', 'cells')

    def __init__(self, w, h, cells=None):
        self.w = w
        self.h = h
        self.cells = cells if cells is not None else bytearray(w * h)

    def inside(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def at(self, x, y):
        return self.cells[y * self.w + x]

    def put(self, x, y, cell):
        self.cells[y * self.w + x] = cell

    def terrain(self, x, y):
        return self.cells[y * self.w + x] % 16

    def height(self, x, y):
        return self.cells[y * self.w + x] // 16


# ---------------------------------------------------------------- 다이아몬드-스퀘어
DS_N = 64
DS_SEED = 1
DS_CORNER = [520, 300, 700, 420]
DS_SCALE = 560
DS_ROUGH_NUM = 58
DS_ROUGH_DEN = 100
DS_OFF = (DS_N + 1 - MAP_W) // 2                  # 65x65 에서 가운데 48x48 을 오려 쓴다


def gen_height(n, corners, scale, seed, rough_num=DS_ROUGH_NUM,
               rough_den=DS_ROUGH_DEN):
    """프랙탈 중점 변위. 반복 순서가 난수 소비 순서를 정하므로 명세의 일부다.

       O(n^2) 시간, O(n^2) 공간. 격자는 (2^k + 1) 이어야 한다 —
       중점을 계속 반으로 접으려면 양 끝이 모두 격자점이어야 하기 때문이다.
    """
    size = n + 1
    h = [[0] * size for _ in range(size)]
    h[0][0] = corners[0]
    h[0][n] = corners[1]
    h[n][0] = corners[2]
    h[n][n] = corners[3]
    r = Rng(seed)
    step = n
    while step > 1:
        half = step // 2
        # 다이아몬드: 정사각형 네 꼭짓점의 평균 + 흔들림
        y = half
        while y < size:
            x = half
            while x < size:
                s = (h[y - half][x - half] + h[y - half][x + half]
                     + h[y + half][x - half] + h[y + half][x + half])
                h[y][x] = s // 4 + (r.next() % (2 * scale + 1) - scale)
                x += step
            y += step
        # 스퀘어: 마름모 네 꼭짓점(격자 밖은 뺀다)의 평균 + 흔들림.
        # 행 간격은 half, 열 간격은 step 이고 홀짝 행마다 시작 열이 어긋난다 —
        # 그래야 아직 값이 없는 변의 중점만 정확히 한 번씩 채운다.
        y = 0
        while y < size:
            x = half if (y // half) % 2 == 0 else 0
            while x < size:
                s = 0
                cnt = 0
                if x - half >= 0:
                    s += h[y][x - half]
                    cnt += 1
                if x + half < size:
                    s += h[y][x + half]
                    cnt += 1
                if y - half >= 0:
                    s += h[y - half][x]
                    cnt += 1
                if y + half < size:
                    s += h[y + half][x]
                    cnt += 1
                h[y][x] = s // cnt + (r.next() % (2 * scale + 1) - scale)
                x += step
            y += half
        step = half
        scale = scale * rough_num // rough_den
    for row in h:
        for i in range(size):
            v = row[i]
            row[i] = 0 if v < 0 else (1023 if v > 1023 else v)
    return h


DS_BLUR = 2


def smooth(h):
    """3x3 상자 흐리기. 프랙탈 그대로는 타일 눈금에서 잡음처럼 보인다.

       한 번 돌릴 때마다 고주파가 깎여 같은 지형이 넓게 뭉친다.
       도스 시절 맵 편집기가 마지막에 평활 버튼을 두었던 이유이기도 하고,
       RLE 가 실제로 압축되게 만드는 유일한 장치이기도 하다.
       O(9 * n^2) 시간. 가장자리는 격자 안의 이웃만 평균한다.
    """
    n = len(h)
    for _ in range(DS_BLUR):
        g = [[0] * n for _ in range(n)]
        for y in range(n):
            for x in range(n):
                s = 0
                c = 0
                for dy in (-1, 0, 1):
                    yy = y + dy
                    if yy < 0 or yy >= n:
                        continue
                    row = h[yy]
                    for dx in (-1, 0, 1):
                        xx = x + dx
                        if 0 <= xx < n:
                            s += row[xx]
                            c += 1
                g[y][x] = s // c
        h = g
    return h


def terrain_of_value(v):
    """높이값 -> 지형. 문턱은 SPEC §5.4 가 정한다."""
    if v < 100:
        return T_DEEP
    if v < 205:
        return T_WATER
    if v < 240:
        return T_SAND
    if v < 460:
        return T_GRASS
    if v < 630:
        return T_FOREST
    if v < 800:
        return T_ROCK
    return T_MOUNTAIN


def height_of_value(v):
    if v < 205:
        return 0
    hh = (v - 205) // 90
    return 12 if hh > 12 else hh


TOWN_X0, TOWN_Y0, TOWN_X1, TOWN_Y1 = 18, 18, 30, 30
TOWN_MID = 24
TOWN_H = 2


def stamp_town(m):
    """마을을 찍는다. 순서가 중요하다 — 벽을 먼저 두르고 문을 나중에 뚫는다."""
    for ty in range(TOWN_Y0, TOWN_Y1):
        for tx in range(TOWN_X0, TOWN_X1):
            if tx in (TOWN_X0, TOWN_X1 - 1) or ty in (TOWN_Y0, TOWN_Y1 - 1):
                t = T_WALL
            elif tx == TOWN_MID or ty == TOWN_MID:
                t = T_ROAD
            else:
                t = T_FLOOR
            m.put(tx, ty, make_cell(t, TOWN_H))
    for tx, ty in ((TOWN_MID, TOWN_Y0), (TOWN_MID, TOWN_Y1 - 1),
                   (TOWN_X0, TOWN_MID), (TOWN_X1 - 1, TOWN_MID)):
        m.put(tx, ty, make_cell(T_ROAD, TOWN_H))
    for ty in range(0, TOWN_Y0):
        m.put(TOWN_MID, ty, make_cell(T_ROAD, TOWN_H))
    for ty in range(TOWN_Y1, MAP_H):
        m.put(TOWN_MID, ty, make_cell(T_ROAD, TOWN_H))


def gen_map():
    """맵 한 장. 같은 씨앗이면 언제나 같은 맵이다."""
    hg = smooth(gen_height(DS_N, DS_CORNER, DS_SCALE, DS_SEED))
    m = Map(MAP_W, MAP_H)
    for ty in range(MAP_H):
        row = hg[ty + DS_OFF]
        for tx in range(MAP_W):
            v = row[tx + DS_OFF]
            m.put(tx, ty, make_cell(terrain_of_value(v), height_of_value(v)))
    stamp_town(m)
    return m


# ---------------------------------------------------------------- RLE
def save_rle(m):
    """행 우선으로 훑어 같은 값을 묶는다. 런 하나는 최대 255칸.

       도스 시절 맵 파일이 이랬다. 지형은 넓게 뭉쳐 있어서 압축이 잘 든다.
    """
    runs = []
    i = 0
    n = len(m.cells)
    while i < n:
        v = m.cells[i]
        j = i
        while j < n and m.cells[j] == v and j - i < 255:
            j += 1
        runs.append('%d:%d' % (j - i, v))
        i = j
    lines = ['ISORPG-MAP 1 %d %d' % (m.w, m.h)]
    for k in range(0, len(runs), 16):
        lines.append(' '.join(runs[k:k + 16]))
    return '\n'.join(lines) + '\n'


def load_rle(text):
    lines = text.strip().split('\n')
    head = lines[0].split()
    if head[0] != 'ISORPG-MAP':
        raise ValueError('맵 매직이 다르다: %r' % head[0])
    w, h = int(head[2]), int(head[3])
    cells = bytearray()
    for line in lines[1:]:
        for run in line.split():
            c, v = run.split(':')
            cells.extend([int(v)] * int(c))
    if len(cells) != w * h:
        raise ValueError('칸 수가 %d 여야 하는데 %d' % (w * h, len(cells)))
    return Map(w, h, cells)
