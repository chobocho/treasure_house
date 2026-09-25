# -*- coding: utf-8 -*-
"""assign — 드론 n 대를 목표 n 자리에 (SPEC §8, T29–T31).

비용의 합이 가장 작은 짝짓기를 찾는다. 경우의 수는 n! 이지만,
헝가리안 방법은 O(n³) 에 끝난다(쿤-먼크레스, 잠재값 판).
"""
import itertools
import math

from . import vec3 as V


def cost_matrix(a, b, squared=True):
    """c[i][j] = |aᵢ − bⱼ|² (squared) 또는 |aᵢ − bⱼ|."""
    if squared:
        return [[V.dot(V.sub(p, q), V.sub(p, q)) for q in b] for p in a]
    return [[V.dist(p, q) for q in b] for p in a]


def total(c, perm):
    return V.total(c[i][perm[i]] for i in range(len(perm)))


def brute(c):
    """n! 개를 다 본다 — n ≤ 7 에서 헝가리안을 검산하는 데만."""
    best, bp = math.inf, None
    for p in itertools.permutations(range(len(c))):
        t = total(c, p)
        if t < best:
            best, bp = t, list(p)
    return bp, best


def hungarian(c):
    """(perm, 합, ops). perm[i] = 행 i 가 받은 열.

    행을 하나씩 더하며, 잠재값 u(행)·v(열)로 줄인 비용 c−u−v 가 0 인
    칸만 따라 증가 경로를 찾는다. 잠재값을 고치는 한 번이 O(n), 한
    행을 더하는 데 최대 n 번 — 합 O(n³). ops 는 안쪽 완화 횟수를 센
    것이다(시간이 아니라 연산 수로 차수를 보인다)."""
    n = len(c)
    inf = math.inf
    u, v = [0.0] * (n + 1), [0.0] * (n + 1)
    p, way = [0] * (n + 1), [0] * (n + 1)       # p[열] = 그 열의 행
    ops = 0
    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minv = [inf] * (n + 1)
        used = [False] * (n + 1)
        while True:
            used[j0] = True
            i0, delta, j1 = p[j0], inf, 0
            for j in range(1, n + 1):
                if not used[j]:
                    ops += 1
                    cur = c[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j], way[j] = cur, j0
                    if minv[j] < delta:
                        delta, j1 = minv[j], j
            for j in range(n + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while j0:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
    perm = [0] * n
    for j in range(1, n + 1):
        perm[p[j] - 1] = j - 1
    return perm, total(c, perm), ops
