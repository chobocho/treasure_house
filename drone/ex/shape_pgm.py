# -*- coding: utf-8 -*-
"""13부 — 모양을 흑백 그림(글자 PGM, P2)으로. 이미지 → 점의 입력.

    python3 ex/shape_pgm.py heart 40 > scratch/heart.pgm

현장에서는 로고나 사진을 받는다. 여기서는 식으로 그린 하트와 별을
n×n 칸에 칠해 같은 꼴(P2: 머리줄 + 0/255 값)의 파일을 만든다. 칸의
가운데가 모양 안이면 255, 밖이면 0 이다. 좌표는 가로 x, 세로 y 가
모두 −1…1 이고 y 가 위쪽이다(PGM 의 첫 줄이 그림의 맨 위).
"""
import math
import sys

HEART_SCALE = 1.3        # 하트 식은 x ±1.14, y −1…1.25 — 칸에 들이려고


def inside_heart(x, y):
    """(X² + Y² − 1)³ − X²Y³ ≤ 0 인 고전 하트 곡선의 안쪽."""
    hx, hy = HEART_SCALE * x, HEART_SCALE * y + 0.1
    return (hx * hx + hy * hy - 1) ** 3 - hx * hx * hy ** 3 <= 0.0


def _star(r_out=0.95, r_in=0.38):
    """꼭짓점이 위를 향한 오각별의 꼭짓점 10 개."""
    pts = []
    for k in range(10):
        a = math.pi / 2 + k * math.pi / 5
        r = r_out if k % 2 == 0 else r_in
        pts.append((r * math.cos(a), r * math.sin(a) - 0.05))
    return pts


STAR = _star()


def inside_star(x, y):
    """반직선 교차 수 세기 — 오른쪽으로 쏜 반직선이 변을 홀수 번 넘으면
    안. O(꼭짓점 수)."""
    inside = False
    for (x1, y1), (x2, y2) in zip(STAR, STAR[1:] + STAR[:1]):
        if (y1 > y) != (y2 > y):
            xc = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < xc:
                inside = not inside
    return inside


def heart_area_fraction(m=600):
    """−1…1 네모 중 하트가 차지하는 비율 — m×m 가운데점 규칙."""
    hit = 0
    for i in range(m):
        y = -1 + (i + 0.5) * 2 / m
        for j in range(m):
            if inside_heart(-1 + (j + 0.5) * 2 / m, y):
                hit += 1
    return hit / (m * m)


def pgm(inside, n):
    """n×n 칸의 P2 글. 칸이 셋보다 적으면 모양이 안 나오므로 거절."""
    if n < 3:
        raise ValueError('칸이 너무 적다: %d' % n)
    rows = []
    for r in range(n):
        y = 1 - (r + 0.5) * 2 / n
        rows.append(' '.join('255' if inside(-1 + (c + 0.5) * 2 / n, y)
                             else '0' for c in range(n)))
    return 'P2\n%d %d\n255\n%s\n' % (n, n, '\n'.join(rows))


if __name__ == '__main__':
    shape = {'heart': inside_heart, 'star': inside_star}[sys.argv[1]]
    sys.stdout.write(pgm(shape, int(sys.argv[2])))
