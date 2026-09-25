# -*- coding: utf-8 -*-
"""지오펜스 판정 — 집을 중심으로 한 원기둥과 다각형 (6부).

PX4·ArduPilot 문서의 두 모양을 그대로 옮긴 판정일 뿐, 두 펌웨어의
코드가 아니다. 울타리는 '밖으로 나간 뒤에야' 동작하므로(PX4 안전
문서), 멈춤 거리 v²/(2a) 만큼 안쪽에 여유를 두라는 문서의 식도
함께 둔다.
"""
import math


def in_cylinder(p, home, r, alt):
    """수평 거리 ≤ r 이고 집보다 alt 이하로 높으면 안."""
    dx, dy = p[0] - home[0], p[1] - home[1]
    return math.hypot(dx, dy) <= r and p[2] - home[2] <= alt


def in_polygon(pt, poly):
    """짝홀 규칙 — 점에서 +x 로 쏜 광선이 변을 홀수 번 건너면 안.

    변 (a, b) 는 반열린 구간 [min y, max y) 에서만 센다 — 광선이
    꼭짓점을 스칠 때 두 번 세지 않으려는 약속. O(꼭짓점 수)."""
    x, y = pt
    inside = False
    n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xc = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if xc > x:
                inside = not inside
    return inside


def stop_distance(v, a):
    """속도 v 에서 감속 a 로 멈출 때까지 가는 거리."""
    return v * v / (2 * a)


def first_breach(track, ok):
    """[(t, p)] 에서 처음으로 ok(p) 가 거짓인 시각, 없으면 None."""
    for t, p in track:
        if not ok(p):
            return t
    return None


if __name__ == '__main__':
    ell = [(0, 0), (10, 0), (10, 4), (4, 4), (4, 10), (0, 10)]
    for pt in ((2, 8), (8, 2), (7, 7)):
        print('ㄱ 자 울타리', pt, '안' if in_polygon(pt, ell) else '밖')
    for v in (2.0, 5.0, 10.0):
        print('%4.1f m/s, 2.5 m/s² → 멈춤 거리 %.1f m'
              % (v, stop_distance(v, 2.5)))
