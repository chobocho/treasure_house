# -*- coding: utf-8 -*-
"""시야·안개·조명 — SPEC §9.

   브레젠험 직선 하나로 셋을 다 만든다. 시야는 그 선 위에 막는 것이 있는지,
   안개는 본 적 있는지, 조명은 얼마나 먼지.
"""
from . import gamemap as M
from .fixed import oct_dist

EYE = 2
SIGHT_R = 9


def line(x0, y0, x1, y1):
    """브레젠험 정수 직선. 양 끝을 포함한다.

       err 는 '이상적 직선에서 벗어난 양'을 2*dx 배로 확대해 정수로 들고 다니는 값이다.
       그래서 나눗셈도 실수도 없이 어느 축을 밟을지 정할 수 있다.
       길이는 항상 max(|dx|,|dy|) + 1 이고, 걸음마다 x 나 y 가 정확히 1씩 움직인다.
    """
    dx = x1 - x0
    if dx < 0:
        dx = -dx
    dy = y1 - y0
    if dy < 0:
        dy = -dy
    dy = -dy
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    x, y = x0, y0
    out = []
    while True:
        out.append((x, y))
        if x == x1 and y == y1:
            return out
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy


def visible(m, sx, sy, gx, gy):
    """(sx,sy) 에서 (gx,gy) 가 보이는가. 중간 칸만 검사한다.

       높이 규칙은 단순하다 — 양 끝보다 EYE-1 단계 넘게 솟은 칸이 있으면 막힌다.
       진짜 3D 광선을 쏘지 않는 이유는 도스 게임도 그러지 않았기 때문이고,
       타일 눈금에서는 차이가 눈에 띄지 않기 때문이다.
    """
    if sx == gx and sy == gy:
        return True
    if not m.inside(gx, gy):
        return False
    hs = m.height(sx, sy)
    hg = m.height(gx, gy)
    top = (hs if hs > hg else hg) + EYE - 1
    pts = line(sx, sy, gx, gy)
    for i in range(1, len(pts) - 1):
        x, y = pts[i]
        if not m.inside(x, y):
            return False
        if M.OPAQUE[m.terrain(x, y)]:
            return False
        if m.height(x, y) > top:
            return False
    return True


class Fog(object):
    """타일마다 2비트. bit0 = 본 적 있다, bit1 = 지금 보인다."""
    __slots__ = ('w', 'h', 'bits', 'n_seen', 'n_vis')

    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.bits = bytearray(w * h)
        self.n_seen = 0
        self.n_vis = 0

    def is_seen(self, x, y):
        return (self.bits[y * self.w + x] % 2) == 1

    def is_visible(self, x, y):
        return (self.bits[y * self.w + x] // 2) % 2 == 1

    def count_seen(self):
        return self.n_seen

    def count_visible(self):
        return self.n_vis

    def recount(self):
        """비트에서 누적 개수를 다시 센다. 세이브를 되돌린 직후에 부른다.

           개수는 세이브에 넣지 않는다 — 비트에서 유도되는 값이라 넣으면
           두 곳에 같은 사실이 적히고, 둘이 어긋나면 어느 쪽이 옳은지 알 수 없다.
        """
        seen = vis = 0
        for v in self.bits:
            if v % 2:
                seen += 1
            if (v // 2) % 2:
                vis += 1
        self.n_seen = seen
        self.n_vis = vis

    def update(self, m, px, py):
        """지금 보이는 칸을 다시 세운다. 기억(bit0)은 지우지 않는다."""
        bits = self.bits
        w = self.w
        for i in range(len(bits)):
            bits[i] = bits[i] % 2
        x0 = px - SIGHT_R
        x1 = px + SIGHT_R
        y0 = py - SIGHT_R
        y1 = py + SIGHT_R
        if x0 < 0:
            x0 = 0
        if y0 < 0:
            y0 = 0
        if x1 > w - 1:
            x1 = w - 1
        if y1 > self.h - 1:
            y1 = self.h - 1
        seen = self.n_seen
        vis = 0
        rr = SIGHT_R * SIGHT_R
        for y in range(y0, y1 + 1):
            dy = y - py
            row = y * w
            for x in range(x0, x1 + 1):
                dx = x - px
                # 정사각형이 아니라 원 안만 본다 — 사각형 모서리는 반경 밖이다
                if dx * dx + dy * dy > rr:
                    continue
                if visible(m, px, py, x, y):
                    if bits[row + x] == 0:
                        seen += 1
                    bits[row + x] = 3      # 지금 보이면 본 적도 있는 것이다
                    vis += 1
        self.n_seen = seen
        self.n_vis = vis

    def light_of(self, x, y, px, py):
        """조명 단계 0..15. 지금 보이면 거리에 따라, 기억만 있으면 4, 아니면 0."""
        v = self.bits[y * self.w + x]
        if (v // 2) % 2:
            d = oct_dist((x - px) * 256, (y - py) * 256)
            l = 15 - (8 * d) // (SIGHT_R * 256)
            if l < 7:
                return 7
            if l > 15:
                return 15
            return l
        if v % 2:
            return 4
        return 0
