# -*- coding: utf-8 -*-
"""formation — 편대 모양을 점 n 개로 (SPEC §8, T32).

모든 생성기는 [x, y, z] 목록을 돌려준다(ENU, 미터). 2차원 모양은
관객이 있는 −y 쪽을 바라보는 x–z 평면에 세우고, x 는 가운데 0,
맨 아래는 z0 이다. 약속은 하나 — **어느 두 점도 d 보다 가깝지 않다.**
"""
import math

from . import collide
from .font5x7 import GLYPHS

GOLDEN = math.pi * (3.0 - math.sqrt(5.0))      # 황금각 (라디안)


def _place(pts, z0):
    """x 를 가운데로, 맨 아래 z 를 z0 로 옮긴다."""
    xs = [p[0] for p in pts]
    cx = (min(xs) + max(xs)) / 2
    zb = min(p[2] for p in pts)
    return [[p[0] - cx, p[1], p[2] - zb + z0] for p in pts]


def _fit(pts, d):
    """최소 간격이 정확히 d 가 되게 통째로 늘린다(닮음 — 모양은
    그대로)."""
    m = collide.min_distance(pts)[0]
    return [[c * d / m for c in p] for p in pts]


def grid(n, d, plane='xz', z0=0.0):
    cols = math.ceil(math.sqrt(n))
    pts = []
    for k in range(n):
        r, c = divmod(k, cols)
        pts.append([c * d, r * d, 0.0] if plane == 'xy'
                   else [c * d, 0.0, r * d])
    if plane == 'xy':
        ys = [p[1] for p in pts]
        cy = (min(ys) + max(ys)) / 2
        pts = [[p[0], p[1] - cy, 0.0] for p in pts]
    return _place(pts, z0)


def circle(n, d, z0=0.0):
    """반지름 R = d / (2 sin(π/n)) — 이웃한 두 점의 현이 정확히 d."""
    r = d / (2 * math.sin(math.pi / n))
    return _place([[r * math.cos(2 * math.pi * k / n), 0.0,
                    r * math.sin(2 * math.pi * k / n)]
                   for k in range(n)], z0)


def rings(n, d, layers=3, z0=0.0):
    """수평 원을 층층이 — 층 사이는 d, 층마다 거의 같은 수."""
    pts = []
    for L in range(layers):
        m = n // layers + (1 if L < n % layers else 0)
        r = d / (2 * math.sin(math.pi / max(m, 3)))
        for k in range(m):
            a = 2 * math.pi * k / m + L * 0.5
            pts.append([r * math.cos(a), r * math.sin(a), L * d])
    return _place(pts, z0)


def fibonacci_unit(n):
    """단위 구 위의 피보나치 격자 — 위도는 고르게, 경도는 황금각씩."""
    out = []
    for i in range(n):
        z = 1.0 - 2.0 * (i + 0.5) / n
        r = math.sqrt(1.0 - z * z)
        a = GOLDEN * i
        out.append([r * math.cos(a), r * math.sin(a), z])
    return out


def fibonacci_unit_min(n):
    return collide.min_distance(fibonacci_unit(n))[0]


def sphere(n, d, z0=0.0):
    """피보나치 격자를 R = d / (단위 구의 최소 간격) 배로 (T32)."""
    return _place(_fit(fibonacci_unit(n), d), z0)


def _on_curves(curves, n, d):
    """여러 곡선 위에 간격 d 로 점을 n 개 — 교차점 근처도 d 를 지킨다.

    배율 S 를 정하면 곡선을 따라 d 마다 점을 제안하고, 이미 받은 점과
    d 보다 가까우면 버린다(탐욕). 받은 수가 n 이상이 되는 가장 작은
    S 를 이분법으로 찾고, 곡선 순서대로 고르게 n 개를 골라 낸다.
    고른 부분집합의 간격은 원래 집합의 간격 이상이다."""
    def accept(s):
        got, grid = [], {}
        for poly in curves:
            carry = 0.0
            for a, b in zip(poly, poly[1:]):
                a, b = [c * s for c in a], [c * s for c in b]
                seg = math.dist(a, b)
                t = carry
                while t <= seg:
                    f = t / seg
                    p = [a[k] + (b[k] - a[k]) * f for k in range(3)]
                    if collide.far_enough(grid, p, d):
                        collide.grid_add(grid, p, d, len(got))
                        got.append(p)
                    t += d
                carry = t - seg
        return got
    lo, hi = 1e-3, 1.0
    while len(accept(hi)) < n:
        hi *= 2
    for _ in range(40):
        mid = (lo + hi) / 2
        if len(accept(mid)) >= n:
            hi = mid
        else:
            lo = mid
    pts = accept(hi)
    m = len(pts)
    return [pts[(k * m) // n] for k in range(n)]


def heart(n, d, z0=0.0):
    """x = 16 sin³t, z = 13 cos t − 5 cos 2t − 2 cos 3t − cos 4t."""
    curve = []
    for k in range(2001):
        t = 2 * math.pi * k / 2000
        curve.append([16 * math.sin(t) ** 3, 0.0,
                      13 * math.cos(t) - 5 * math.cos(2 * t)
                      - 2 * math.cos(3 * t) - math.cos(4 * t)])
    return _place(_on_curves([curve], n, d), z0)


def globe(n, d, meridians=6, parallels=(-45, 0, 45), z0=0.0):
    """경선과 위선으로 그린 지구본. 경선은 반원 둘씩, 위선은 원."""
    curves = []
    for k in range(meridians):
        a = math.pi * k / meridians
        curves.append([[math.cos(a) * math.sin(t), math.sin(a) *
                        math.sin(t), math.cos(t)]
                       for t in [2 * math.pi * j / 400
                                 for j in range(401)]])
    for lat in parallels:
        r, z = math.cos(math.radians(lat)), math.sin(math.radians(lat))
        curves.append([[r * math.cos(t), r * math.sin(t), z]
                       for t in [2 * math.pi * j / 400
                                 for j in range(401)]])
    return _place(_on_curves(curves, n, d), z0)


def glyph_count(ch):
    return GLYPHS[ch].count('#')


def text(s, d, z0=0.0):
    """글자마다 5×7 칸, 글자 사이 한 칸. 한 칸의 너비가 d."""
    pts = []
    for i, ch in enumerate(s):
        rows = GLYPHS[ch].split()
        for r, row in enumerate(rows):
            for c, cell in enumerate(row):
                if cell == '#':
                    pts.append([(6 * i + c) * d, 0.0, (6 - r) * d])
    return _place(pts, z0)


def digit(k, d, z0=0.0):
    return text(str(k), d, z0)


def poisson_disk(inside, w, h, r, g, tries=2000):
    """다트 던지기 — r 보다 가까운 후보는 버린다. 그래서 간격 ≥ r (T32).

    증명은 한 줄이다: 받아들인 점마다 앞서 받은 모든 점과 r 이상
    떨어져 있음을 확인했으니, 어느 두 점도 r 보다 가깝지 않다."""
    got, grid = [], {}
    for _ in range(tries):
        x, z = (g.uniform() - 0.5) * w, g.uniform() * h
        p = [x, 0.0, z]
        if inside(x, z) and collide.far_enough(grid, p, r):
            collide.grid_add(grid, p, r, len(got))
            got.append(p)
    return [(p[0], p[2]) for p in got]


def _pgm(text_):
    tok = [t for line in text_.split('\n') if not line.startswith('#')
           for t in line.split()]
    if tok[0] != 'P2':
        raise ValueError('P2(글자 PGM)만 읽는다')
    w, h, mx = int(tok[1]), int(tok[2]), int(tok[3])
    v = [int(t) for t in tok[4:4 + w * h]]
    px = [[v[r * w + c] / mx for c in range(w)] for r in range(h)]
    return w, h, px


def image(pgm, n, d, g, lloyd=10):
    """그림 → 점 n 개: 밝은 칸 → 포아송 원판 → 로이드 완화 → 크기 맞춤.

    로이드 완화: 밝은 칸마다 가장 가까운 점을 찾고, 점을 자기 몫의
    칸들의 무게중심으로 옮긴다. 열 번 되풀이하면 점이 고르게 퍼진다.
    O(lloyd · n · 밝은 칸 수)."""
    w, h, px = _pgm(pgm)
    cells = [(c + 0.5 - w / 2, h - r - 0.5) for r in range(h)
             for c in range(w) if px[r][c] > 0.5]
    inside = lambda x, z: px[min(h - 1, max(0, int(h - z)))][
        min(w - 1, max(0, int(x + w / 2)))] > 0.5
    rad = math.sqrt(len(cells) / n)
    pts = []
    while len(pts) < n:
        pts = poisson_disk(inside, w, h, rad, g, tries=40 * n)
        rad *= 0.9
    pts = pts[:n]
    for _ in range(lloyd):
        acc = [[0.0, 0.0, 0] for _ in pts]
        for cx, cz in cells:
            k = min(range(len(pts)), key=lambda i: (pts[i][0] - cx) ** 2
                    + (pts[i][1] - cz) ** 2)
            acc[k][0] += cx
            acc[k][1] += cz
            acc[k][2] += 1
        pts = [(a[0] / a[2], a[1] / a[2]) if a[2] else p
               for a, p in zip(acc, pts)]
    return _place(_fit([[x, 0.0, z] for x, z in pts], d), 0.0)
