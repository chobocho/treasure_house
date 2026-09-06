# -*- coding: utf-8 -*-
"""래스터 — SPEC §7. 320x200 8비트 인덱스 프레임버퍼.

   모드 13h 를 그대로 흉내 낸다. 색은 0..255 인덱스이고, 실제 RGB 는
   프런트엔드가 팔레트를 통해 정한다. 이 분리 덕분에
     · 팔레트만 돌려 물결 애니메이션을 공짜로 얻고
     · 명암도 표 한 번 조회로 끝나며
     · 세 언어의 결과를 바이트 단위로 비교할 수 있다.
"""
import io
import os

SCR_W = 320
SCR_H = 200
PAL_SIZE = 256
LIGHT_LEVELS = 16
DAC_MAX = 63

WATER_LO = 16
WATER_HI = 31

_HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GOLDEN = os.path.join(_HERE, 'golden')


def load_palette(path=None):
    """golden/palette.txt -> [(r,g,b)] 256개. 값은 6비트 DAC (0..63)."""
    text = io.open(path or os.path.join(GOLDEN, 'palette.txt'),
                   encoding='utf-8').read().strip().split('\n')
    head = text[0].split()
    if head[0] != 'ISORPG-PAL':
        raise ValueError('팔레트 매직이 다르다: %r' % head[0])
    pal = []
    for line in text[1:]:
        p = line.split()
        pal.append((int(p[1]), int(p[2]), int(p[3])))
    if len(pal) != PAL_SIZE:
        raise ValueError('팔레트가 %d색' % len(pal))
    return pal


def build_light(pal):
    """명암표 16 x 256. LIGHT[l*256 + c] = 색 c 를 l/15 로 어둡게 한 것에 가장 가까운 색.

       도스 게임이 쓰던 그대로다. 그릴 때는 표 조회 한 번이면 끝나고,
       팔레트가 램프로 짜여 있으면 결과가 같은 램프 안에서 자연스럽게 내려간다.
       만드는 비용은 16 * 256 * 256 = 1,048,576 번의 거리 계산 — 시작할 때 한 번뿐이다.
    """
    tbl = [0] * (LIGHT_LEVELS * PAL_SIZE)
    for l in range(LIGHT_LEVELS):
        for c in range(PAL_SIZE):
            r, g, b = pal[c]
            tr = (r * l) // (LIGHT_LEVELS - 1)
            tg = (g * l) // (LIGHT_LEVELS - 1)
            tb = (b * l) // (LIGHT_LEVELS - 1)
            best = 0
            bd = 1 << 30
            for k in range(PAL_SIZE):
                pr, pg, pb = pal[k]
                dr = pr - tr
                dg = pg - tg
                db = pb - tb
                d = dr * dr + dg * dg + db * db
                if d < bd:
                    bd = d
                    best = k
                    if d == 0:
                        break
            tbl[l * PAL_SIZE + c] = best
    return tbl


class Sprite(object):
    __slots__ = ('name', 'w', 'h', 'ox', 'oy', 'rows')

    def __init__(self, name, w, h, ox, oy, rows):
        self.name = name
        self.w = w
        self.h = h
        self.ox = ox
        self.oy = oy
        self.rows = rows            # [[(개수, 색), ...], ...]


def load_sprites(path=None):
    """golden/tiles.rle 을 읽는다. 색 0 은 투명."""
    lines = io.open(path or os.path.join(GOLDEN, 'tiles.rle'),
                    encoding='utf-8').read().rstrip('\n').split('\n')
    head = lines[0].split()
    if head[0] != 'ISORPG-TILES':
        raise ValueError('스프라이트 매직이 다르다: %r' % head[0])
    out = []
    i = 1
    while i < len(lines):
        p = lines[i].split()
        name, w, h, ox, oy = p[2], int(p[3]), int(p[4]), int(p[5]), int(p[6])
        i += 1
        rows = []
        for k in range(h):
            runs = []
            total = 0
            for tok in lines[i + k].split():
                a, b = tok.split(':')
                runs.append((int(a), int(b)))
                total += int(a)
            if total != w:
                raise ValueError('%s 의 %d행 런 합이 %d (폭 %d)' % (name, k, total, w))
            rows.append(runs)
        i += h
        out.append(Sprite(name, w, h, ox, oy, rows))
    if len(out) != int(head[2]):
        raise ValueError('스프라이트 개수가 %d 여야 하는데 %d' % (int(head[2]), len(out)))
    return out


_LIGHT_CACHE = []


def get_light():
    """기본 명암표. 만드는 데 1초쯤 걸리므로 한 번만 만들어 둔다."""
    if not _LIGHT_CACHE:
        _LIGHT_CACHE.append(build_light(load_palette()))
    return _LIGHT_CACHE[0]


class Frame(object):
    """프레임버퍼 하나. 파이썬에서는 bytearray 가 곧 모드 13h 의 A000 세그먼트다."""
    __slots__ = ('fb', 'light')

    def __init__(self, light=None):
        self.fb = bytearray(SCR_W * SCR_H)
        self.light = get_light() if light is None else light

    def clear(self, c=0):
        for i in range(SCR_W * SCR_H):
            self.fb[i] = c

    def px(self, x, y):
        return self.fb[y * SCR_W + x]

    def blit_rle(self, spr, x, y, level=15):
        """런 단위로 자르며 그린다. 픽셀마다 조건을 걸지 않는 것이 도스식이다.

           세로는 행 통째로 건너뛰고, 가로는 런 하나를 [a,b) 로 잘라 채운다.
           그래서 화면 밖으로 크게 벗어난 스프라이트도 거의 공짜다.
        """
        light = self.light
        fb = self.fb
        top = y - spr.oy
        left = x - spr.ox
        rows = spr.rows
        for r in range(spr.h):
            py = top + r
            if py < 0 or py >= SCR_H:
                continue
            base = py * SCR_W
            px = left
            for count, color in rows[r]:
                if color:
                    a = px if px > 0 else 0
                    b = px + count
                    if b > SCR_W:
                        b = SCR_W
                    if a < b:
                        v = light[level * PAL_SIZE + color] if light else color
                        for i in range(base + a, base + b):
                            fb[i] = v
                px += count
                if px >= SCR_W:
                    break


class Dirty(object):
    """더티 렉트 — 바뀐 곳만 다시 올리기 위한 사각형 목록."""
    __slots__ = ('rects',)

    def __init__(self):
        self.rects = []

    def add(self, x, y, w, h):
        if x < 0:
            w += x
            x = 0
        if y < 0:
            h += y
            y = 0
        if x + w > SCR_W:
            w = SCR_W - x
        if y + h > SCR_H:
            h = SCR_H - y
        if w > 0 and h > 0:
            self.rects.append((x, y, w, h))

    def merge(self):
        """겹치거나 맞닿은 사각형을 합친다. 낭비가 1.5배를 넘으면 그냥 둔다.

           합치면 갱신 호출이 줄지만 합친 결과가 지나치게 크면 오히려 손해다.
           그 경계를 넓이 비로 잡는 것이 가장 단순하고 잘 듣는 규칙이다.
        """
        changed = True
        while changed:
            changed = False
            out = []
            used = [False] * len(self.rects)
            for i in range(len(self.rects)):
                if used[i]:
                    continue
                x, y, w, h = self.rects[i]
                for j in range(i + 1, len(self.rects)):
                    if used[j]:
                        continue
                    x2, y2, w2, h2 = self.rects[j]
                    if x + w < x2 or x2 + w2 < x or y + h < y2 or y2 + h2 < y:
                        continue
                    nx = x if x < x2 else x2
                    ny = y if y < y2 else y2
                    nr = x + w if x + w > x2 + w2 else x2 + w2
                    nb = y + h if y + h > y2 + h2 else y2 + h2
                    if (nr - nx) * (nb - ny) * 2 <= (w * h + w2 * h2) * 3:
                        x, y, w, h = nx, ny, nr - nx, nb - ny
                        used[j] = True
                        changed = True
                used[i] = True
                out.append((x, y, w, h))
            self.rects = out
        self.rects.sort(key=lambda r: (r[1], r[0]))
        return self.rects


def cycle_palette(pal, n):
    """물 램프 구간만 왼쪽으로 n 칸 돌린다. 프레임버퍼는 건드리지 않는다.

       도스 시절 '공짜 애니메이션'. 그리는 비용이 0이고, DAC 레지스터 몇 개만
       다시 쓰면 물결이 흐른다.
    """
    span = WATER_HI - WATER_LO + 1
    k = n % span
    out = list(pal)
    for i in range(span):
        out[WATER_LO + i] = pal[WATER_LO + (i + k) % span]
    return out


def expand6(v):
    """6비트 DAC -> 8비트. v*4 + v/16 이라 0 -> 0, 63 -> 255 가 정확히 맞는다."""
    return v * 4 + v // 16


def to_ppm(fb, pal):
    """P6 PPM. 머리말 15바이트 + 192,000바이트 = 192,015바이트."""
    lut = bytearray(PAL_SIZE * 3)
    for i in range(PAL_SIZE):
        r, g, b = pal[i]
        lut[i * 3] = expand6(r)
        lut[i * 3 + 1] = expand6(g)
        lut[i * 3 + 2] = expand6(b)
    out = bytearray(b'P6\n320 200\n255\n')
    body = bytearray(SCR_W * SCR_H * 3)
    for i in range(SCR_W * SCR_H):
        c = fb[i] * 3
        j = i * 3
        body[j] = lut[c]
        body[j + 1] = lut[c + 1]
        body[j + 2] = lut[c + 2]
    out.extend(body)
    return bytes(out)
