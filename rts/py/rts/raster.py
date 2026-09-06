# -*- coding: utf-8 -*-
"""래스터 — 프레임버퍼·팔레트·스프라이트·블릿·폰트·PPM (SPEC §22).

   세 언어 모두 프레임버퍼가 **1차원 정수 배열**이다. 이것이 세 구현을 바이트
   단위로 비교 가능하게 만드는 유일한 이유다. 프런트엔드는 이 배열에 팔레트로
   색을 입혀 화면에 올릴 뿐이고, `make parity` 는 192,015바이트짜리 PPM 을
   `cmp` 한다.

   팔레트와 스프라이트는 정수식으로 만든다(§22.2·§22.3). 표를 세 언어에 옮겨
   적는 대신 같은 식을 세 번 쓰고, 결과를 골든과 대조한다.
"""

from . import circle as CI
from . import const as C
from . import fixed as F

PLAYER_BASE = 160
PLAYER_SHADES = 8
SHADOW = 251
WATER_BASE, WATER_N = 232, 8
DRAWN_DIRS = 5                   # §22.7 그린 방향 수 (나머지 셋은 좌우 반전)
UNIT_R = [5, 4, 6, 5, 5]
UNIT_M = [3, 3, 4, 3, 3]
UNIT_NAME = ['INF', 'ARCHER', 'TANK', 'MORTAR', 'HARV']
BLD_NAME = [(C.HQ, 'HQ'), (C.REF, 'REF'), (C.BARR, 'BARR'),
            (C.FACT, 'FACT'), (C.POW, 'POW'), (C.TOWER, 'TOWER')]

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

FONT_HEX = (
    '000000000000000008080808080008000000000000000000143e14143e14000000000000'
    '000000003234081026060000000000000000000000000000000000000408101010080400'
    '100804040408100000000000000000000008083e0808000000000000181810000000003e'
    '00000000000000000018180002020408102020001c22262a32221c000818080808081c00'
    '1c22020408103e003c02021c02023c00040c14243e0404003e203c0202221c000c10203c'
    '22221c003e020408101010001c22221c22221c001c22221e020418000018180018180000'
    '00000000000000000000000000000000000000000000000000000000000000001c220204'
    '0800080000000000000000001c22223e222222003c22223c22223c001c22202020221c00'
    '3c22222222223c003e20203c20203e003e20203c202020001c22202e22221c002222223e'
    '222222001c08080808081c000e0404040424180022242830282422002020202020203e00'
    '22362a2a2222220022322a2a262222001c22222222221c003c22223c202020001c222222'
    '2a241a003c22223c282422001e20201c02023c003e080808080808002222222222221c00'
    '22222222221408002222222a2a362200222214081422220022221408080808003e020408'
    '10203e000000000000000000000000000000000000000000000000000000000000000000'
    '000000000000000000000000000000000000000000000000000000000000000000000000'
    '000000000000000000000000000000000000000000000000000000000000000000000000'
    '000000000000000000000000000000000000000000000000000000000000000000000000'
    '000000000000000000000000000000000000000000000000000000000000000000000000'
    '000000000000000000000000000000000000000000000000000000000000000000000000'
    '000000000000000000000000000000000000000000000000000000000000000000000000'
    '000000000000000000000000000000000000000000000000000000000000000000000000'
    '00000000')
FONT = bytes(bytearray(int(FONT_HEX[k * 2:k * 2 + 2], 16)
                       for k in range(len(FONT_HEX) // 2)))
FONT_W, FONT_H, FONT_ADV = 6, 8, 6
FONT_FIRST = 32


# ── SPEC §22.2 팔레트 ───────────────────────────────────────────────────────
def ramp(c0, c1, i):
    """두 끝색 사이의 정수 보간. 나눗셈은 내림이다."""
    return (c0[0] + F.floordiv((c1[0] - c0[0]) * i, 7),
            c0[1] + F.floordiv((c1[1] - c0[1]) * i, 7),
            c0[2] + F.floordiv((c1[2] - c0[2]) * i, 7))


def build_palette():
    pal = [(0, 0, 0)] * 256
    for k in range(15):
        pal[1 + k] = EGA[k]
    for i in range(16):
        g = F.floordiv(i * 63, 15)
        pal[16 + i] = (g, g, g)
    for p in range(4):
        c0, c1 = PLAYER_RAMP[p]
        for i in range(PLAYER_SHADES):
            pal[PLAYER_BASE + p * PLAYER_SHADES + i] = ramp(c0, c1, i)
    for i in range(16):
        pal[192 + i] = UI[i]
    for r in range(6):
        c0, c1 = TERRAIN_RAMP[r]
        for i in range(8):
            pal[208 + r * 8 + i] = ramp(c0, c1, i)
    return pal


def build_light(pal):
    """명암 단계 l 에서 색 c 에 가장 가까운 항목. 동점이면 인덱스 최소.

       256 × 256 × 4 = 262,144회 비교이며 **시작할 때 한 번**이다. 안개(§14.4)가
       이 표를 쓴다 — 안개 때문에 색 계산을 하지 않으려고 표로 미리 굳힌다.
    """
    out = []
    for l in range(4):
        row = [0] * 256
        for c in range(256):
            wr = F.floordiv(pal[c][0] * l, 3)
            wg = F.floordiv(pal[c][1] * l, 3)
            wb = F.floordiv(pal[c][2] * l, 3)
            best, bd = 0, -1
            for j in range(256):
                dr = pal[j][0] - wr
                dg = pal[j][1] - wg
                db = pal[j][2] - wb
                d = dr * dr + dg * dg + db * db
                if bd < 0 or d < bd:
                    bd, best = d, j
            row[c] = best
        out.append(row)
    return out


# ── SPEC §22.6 팔레트 사이클링 ──────────────────────────────────────────────
def cycle_water(pal, phase):
    """물 색 8칸을 한 칸씩 돌린다. **프레임버퍼는 건드리지 않는다** —
       팔레트 모드의 가장 큰 장점이었던 공짜 애니메이션이다."""
    out = list(pal)
    for i in range(WATER_N):
        out[WATER_BASE + i] = pal[WATER_BASE + (i + phase) % WATER_N]
    return out


# ── SPEC §22.3 스프라이트 ───────────────────────────────────────────────────
class Sprite(object):
    def __init__(self, w, h, ox, oy, data):
        self.w = w
        self.h = h
        self.ox = ox
        self.oy = oy
        self.data = data

    def pixels(self):
        out = []
        d = bytearray(self.data)
        i = 0
        while i < len(d):
            for _k in range(d[i]):
                out.append(d[i + 1])
            i += 2
        return out


def _rle(px):
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


def _disc(px, w, cx, cy, r, colour, only_below=False, only_empty=False):
    """§6.2 의 행 span 으로 원을 채운다 — 곱셈도 제곱근도 쓰지 않는다."""
    sp = CI.spans(r)
    for dy in range(-r, r + 1):
        if only_below and dy < 0:
            continue
        wdt = sp[dy if dy >= 0 else -dy]
        y = cy + dy
        for dx in range(-wdt, wdt + 1):
            x = cx + dx
            if 0 <= x < w and 0 <= y < len(px) // w:
                if only_empty and px[y * w + x] != 0:
                    continue
                px[y * w + x] = colour


def unit_sprite(k, d):
    w = h = C.TILE
    px = [0] * (w * h)
    r = UNIT_R[k]
    _disc(px, w, 8, 9, r, PLAYER_BASE + 1)          # 테두리
    _disc(px, w, 8, 9, r - 1, PLAYER_BASE + 3)      # 속
    _disc(px, w, 8, 14, 3, SHADOW, True, True)      # 그림자 (아래 절반, 빈 곳만)
    mx, my = 8 + F.DX[d] * UNIT_M[k], 9 + F.DY[d] * UNIT_M[k]
    for y in range(my, my + 2):
        for x in range(mx, mx + 2):
            if 0 <= x < w and 0 <= y < h:
                px[y * w + x] = PLAYER_BASE + 6      # 방향 표시
    return Sprite(w, h, 8, 14, _rle(px))


def building_sprite(foot):
    w = h = C.TILE * foot
    px = [0] * (w * h)
    for y in range(4, h - 2):
        for x in range(2, w - 2):
            edge = (x == 2 or x == w - 3 or y == 4 or y == h - 3)
            px[y * w + x] = PLAYER_BASE + (5 if edge else 2)
    for y in range(4, 7):
        for x in range(2, w - 2):
            px[y * w + x] = PLAYER_BASE + 6          # 지붕
    for y in range(h - 6, h - 2):
        for x in range(w // 2 - 2, w // 2 + 2):
            px[y * w + x] = PLAYER_BASE              # 문
    return Sprite(w, h, w // 2, h - 2, _rle(px))


def _build_sprites():
    out = {}
    for k in range(5):
        for d in range(DRAWN_DIRS):
            out['%s_%d' % (UNIT_NAME[k], d)] = unit_sprite(k, d)
    for (kind, name) in BLD_NAME:
        out[name] = building_sprite(C.FOOT[kind])
    return out


SPRITES = _build_sprites()


def sprite_for(kind, d):
    """§22.7 — 그린 것은 5방향뿐이다. (스프라이트, 반전 여부)."""
    if C.IS_BUILDING[kind]:
        for (k, name) in BLD_NAME:
            if k == kind:
                return SPRITES[name], False
        return None, False
    if d <= 4:
        return SPRITES['%s_%d' % (UNIT_NAME[kind], d)], False
    return SPRITES['%s_%d' % (UNIT_NAME[kind], 8 - d)], True


# ── SPEC §22.1 프레임버퍼 ───────────────────────────────────────────────────
class Frame(object):
    def __init__(self, w=C.SCR_W, h=C.SCR_H):
        self.w = w
        self.h = h
        self.fb = [0] * (w * h)

    def clear(self, v=0):
        for i in range(len(self.fb)):
            self.fb[i] = v

    def rect(self, x, y, w, h, v):
        for j in range(max(0, y), min(self.h, y + h)):
            row = j * self.w
            for i in range(max(0, x), min(self.w, x + w)):
                self.fb[row + i] = v


# ── SPEC §22.4 클리핑 블릿 ──────────────────────────────────────────────────
def blit(fb, spr, x, y, owner=0, flip=False, light=None, level=3):
    """런 단위로 자른다 — 픽셀마다 경계를 검사하지 않는다 (정리 22.1).

       완전히 화면 밖이면 런을 하나도 훑지 않고 돌아간다.
    """
    # 반전해도 상자 자체는 그대로 두고 상자 **안에서** 뒤집는다. 기준점은
    # (w - 1 - 2*ox) 픽셀만큼 옮겨지는데(폭 16·ox 8 이면 1px), 세 언어가
    # 같은 자리에 그리는 것이 그 1px 보다 중요하다.
    x0 = x - spr.ox
    y0 = y - spr.oy
    if (x0 + spr.w <= 0 or x0 >= C.SCR_W
            or y0 + spr.h <= 0 or y0 >= C.SCR_H):
        return
    add = owner * PLAYER_SHADES
    d = bytearray(spr.data)
    i = 0
    pos = 0
    while i < len(d):
        run, val = d[i], d[i + 1]
        i += 2
        if val == 0:                                  # 컬러키 — 통째로 건너뛴다
            pos += run
            continue
        colour = val + add if PLAYER_BASE <= val < PLAYER_BASE + PLAYER_SHADES \
            else val
        if light is not None and level < 3:
            colour = light[level][colour]
        p = pos
        end = pos + run
        while p < end:
            sy = p // spr.w
            sx = p % spr.w
            n = end - p
            if n > spr.w - sx:
                n = spr.w - sx                        # 이 줄에 걸치는 만큼만
            fy = y0 + sy
            if 0 <= fy < C.SCR_H:
                if flip:
                    fx = x0 + (spr.w - 1 - (sx + n - 1))
                else:
                    fx = x0 + sx
                a = fx if fx > 0 else 0
                b = fx + n
                if b > C.SCR_W:
                    b = C.SCR_W
                row = fy * C.SCR_W
                for q in range(a, b):
                    fb[row + q] = colour
            p += n
        pos = end


# ── SPEC §22.8 폰트 ─────────────────────────────────────────────────────────
def text(fb, s, x, y, colour):
    """6×8 칸에 5×7 획. 소문자는 빈 글자다(§22.8)."""
    for ch in s:
        code = ord(ch)
        if FONT_FIRST <= code < FONT_FIRST + 95:
            base = (code - FONT_FIRST) * FONT_H
            for j in range(FONT_H):
                v = FONT[base + j] if isinstance(FONT[base + j], int) \
                    else ord(FONT[base + j])
                fy = y + j
                if not (0 <= fy < C.SCR_H):
                    continue
                for k in range(FONT_W):
                    if (v // (1 << (5 - k))) % 2 == 1:
                        fx = x + k
                        if 0 <= fx < C.SCR_W:
                            fb[fy * C.SCR_W + fx] = colour
        x += FONT_ADV


# ── SPEC §22.9 더티 렉트 ────────────────────────────────────────────────────
class Dirty(object):
    """8개를 넘으면 전체를 다시 그린다 — 합치는 비용이 이득을 넘는 지점이다."""

    MAX = 8

    def __init__(self):
        self._r = []

    def add(self, x, y, w, h):
        self._r.append((x, y, w, h))

    def rects(self):
        if len(self._r) > self.MAX:
            return [(0, 0, C.SCR_W, C.SCR_H)]
        return list(self._r)

    def clear(self):
        self._r = []


# ── SPEC §22.10 PPM ─────────────────────────────────────────────────────────
def expand(v):
    """0…63 을 0…255 로. v*255/63 이 아니라 곱셈·나눗셈 하나씩이다."""
    return v * 4 + F.floordiv(v, 16)


def to_ppm(fb, pal):
    head = b'P6\n%d %d\n255\n' % (C.SCR_W, C.SCR_H)
    lut = bytearray()
    for c in pal:
        lut.append(expand(c[0]))
        lut.append(expand(c[1]))
        lut.append(expand(c[2]))
    out = bytearray()
    for v in fb:
        j = v * 3
        out.append(lut[j])
        out.append(lut[j + 1])
        out.append(lut[j + 2])
    return head + bytes(out)
