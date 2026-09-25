# -*- coding: utf-8 -*-
"""collide — 가장 가까운 두 대, 경로 교차, 전환 중 최소 간격 (SPEC §8).

쇼의 안전은 숫자 하나로 요약된다: 전 구간에서 두 드론 사이의 가장
짧은 거리. 수백 대를 모든 쌍으로 재면 O(n²) 이라 느리다 — x 로 줄
세워 훑으며 지금까지의 최솟값보다 x 차가 크면 멈춘다.
"""
import math

from . import vec3 as V


def min_distance(pts):
    """(거리, i, j), i < j. 같은 거리면 먼저 찾은 쌍.

    x 순으로 정렬해 앞에서부터, x 차가 지금 최솟값보다 커지면 안쪽
    고리를 끊는다. 고르게 퍼진 점이면 거의 O(n log n)."""
    order = sorted(range(len(pts)), key=lambda k: (pts[k][0], k))
    best, bi, bj = math.inf, -1, -1
    for a in range(len(order)):
        i = order[a]
        pi = pts[i]
        for b in range(a + 1, len(order)):
            j = order[b]
            pj = pts[j]
            if pj[0] - pi[0] >= best:
                break
            d = V.dist(pi, pj)
            if d < best:
                best, bi, bj = d, min(i, j), max(i, j)
    return best, bi, bj


def _cell(p, d):
    return (math.floor(p[0] / d), math.floor(p[1] / d),
            math.floor(p[2] / d))


def far_enough(grid, p, d):
    """격자(칸 = d)의 이웃 27칸에 d 보다 가까운 점이 없나."""
    cx, cy, cz = _cell(p, d)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for q in grid.get((cx + dx, cy + dy, cz + dz), ()):
                    if V.dist(p, q) < d:
                        return False
    return True


def grid_add(grid, p, d, _idx=None):
    grid.setdefault(_cell(p, d), []).append(p)


def _orient(a, b, c):
    """x–z 평면의 방향: 양수면 반시계."""
    return ((b[0] - a[0]) * (c[2] - a[2])
            - (b[2] - a[2]) * (c[0] - a[0]))


def _cross(p1, p2, q1, q2):
    """두 선분이 안쪽에서 엄밀히 엇갈리나 (끝점 닿음은 제외)."""
    d1, d2 = _orient(q1, q2, p1), _orient(q1, q2, p2)
    d3, d4 = _orient(p1, p2, q1), _orient(p1, p2, q2)
    return d1 * d2 < 0 and d3 * d4 < 0


def crossings(a, b, perm):
    """편대 평면(x–z)에서 서로 엇갈리는 경로 쌍의 수 (T30)."""
    n = 0
    for i in range(len(a)):
        for j in range(i + 1, len(a)):
            if _cross(a[i], b[perm[i]], a[j], b[perm[j]]):
                n += 1
    return n


def check_transition(a, b, perm, beta, samples):
    """동기 직선 이동 xᵢ(u) = aᵢ + β(u)(b_perm(i) − aᵢ) 의 최소 간격.

    u 를 samples 등분해 잰다. (거리, u, i, j) 를 돌려준다."""
    best = (math.inf, 0.0, -1, -1)
    for k in range(samples + 1):
        u = k / samples
        s = beta(u)
        x = [[a[i][c] + s * (b[perm[i]][c] - a[i][c]) for c in range(3)]
             for i in range(len(a))]
        d, i, j = min_distance(x)
        if d < best[0]:
            best = (d, u, i, j)
    return best
