# -*- coding: utf-8 -*-
"""경로 문제 — TSP 와 그 사촌들.

   같은 문제를 세 가지 방법으로 푼다.
     · 정확 DP (Held–Karp)   O(n² 2ⁿ) — n ≤ 15 정도
     · 탐욕(최근접 이웃)      O(n²)    — 빠르지만 나쁘다
     · 2-opt 국소탐색         반복      — 실무의 기본기

   그리고 세 답을 나란히 놓아 "근사비"가 무엇을 뜻하는지 눈으로 본다.
"""
import itertools
import math
import random


def tour_length(D, tour):
    n = len(tour)
    return math.fsum(D[tour[i]][tour[(i + 1) % n]] for i in range(n))


def random_points(n, seed=0, box=100.0):
    rng = random.Random(seed)
    return [(rng.uniform(0, box), rng.uniform(0, box)) for _ in range(n)]


def distance_matrix(pts):
    n = len(pts)
    return [[math.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1])
             for j in range(n)] for i in range(n)]


def held_karp(D):
    """정확 해 — 부분집합 동적계획.

       dp[S][j] = 0 에서 출발해 S 의 도시를 모두 방문하고 j 에서 끝나는 최단 길이.
       상태가 2ⁿ·n 개, 전이가 n 이라 O(n² 2ⁿ). n=15 면 약 740만 번의 갱신이다.

       배낭의 DP(7부 정리 32.1)와 같은 사고이지만, 여기서는 상태가 <부분집합>이라
       지수적으로 많다. "동적계획이면 다항시간"이 아니라는 것을 보여 주는 예다.
    """
    n = len(D)
    if n <= 1:
        return 0.0, list(range(n))
    size = 1 << (n - 1)                       # 도시 0 은 고정 출발점
    INF = float('inf')
    dp = [[INF] * (n - 1) for _ in range(size)]
    par = [[-1] * (n - 1) for _ in range(size)]
    for j in range(n - 1):
        dp[1 << j][j] = D[0][j + 1]
    for S in range(size):
        for j in range(n - 1):
            if dp[S][j] == INF or not (S >> j) & 1:
                continue
            base = dp[S][j]
            for k in range(n - 1):
                if (S >> k) & 1:
                    continue
                T = S | (1 << k)
                v = base + D[j + 1][k + 1]
                if v < dp[T][k]:
                    dp[T][k] = v
                    par[T][k] = j
    full = size - 1
    best, bj = INF, -1
    for j in range(n - 1):
        v = dp[full][j] + D[j + 1][0]
        if v < best:
            best, bj = v, j
    tour, S, j = [], full, bj
    while j >= 0:
        tour.append(j + 1)
        pj = par[S][j]
        S ^= (1 << j)
        j = pj
    tour.append(0)
    tour.reverse()
    return best, tour


def nearest_neighbor(D, start=0):
    """최근접 이웃 탐욕 — 가장 단순한 구성적 휴리스틱."""
    n = len(D)
    unvisited = set(range(n))
    unvisited.remove(start)
    tour = [start]
    cur = start
    while unvisited:
        nxt = min(unvisited, key=lambda j: D[cur][j])
        unvisited.remove(nxt)
        tour.append(nxt)
        cur = nxt
    return tour_length(D, tour), tour


def two_opt(D, tour, max_pass=200):
    """2-opt 국소탐색 — 교차하는 두 변을 뒤집어 길이를 줄인다.

       개선이 없을 때까지 반복하므로 <국소 최적>에 도달한다. 3부의 경사하강과
       구조가 같다: 이웃 중 더 나은 곳으로 이동하고, 더 나은 이웃이 없으면 멈춘다.
       다만 여기서는 '이웃'이 연속 공간의 방향이 아니라 <조합적 변형>이다.
    """
    n = len(tour)
    t = list(tour)
    best = tour_length(D, t)
    for _ in range(max_pass):
        improved = False
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                a, b = t[i - 1], t[i]
                c, d = t[j], t[(j + 1) % n]
                delta = D[a][c] + D[b][d] - D[a][b] - D[c][d]
                if delta < -1e-12:
                    t[i:j + 1] = reversed(t[i:j + 1])
                    best += delta
                    improved = True
        if not improved:
            break
    return best, t


def mst_lower_bound(D):
    """1-트리 하한의 가장 단순한 형태 — 최소신장나무 길이.

       최적 순회에서 변 하나를 빼면 신장나무가 되므로, MST 길이는 순회 길이의
       하한이다. 분지한정의 하한으로 쓸 수 있고, 근사비를 논할 때 기준이 된다.
    """
    n = len(D)
    if n <= 1:
        return 0.0
    inside = {0}
    total = 0.0
    while len(inside) < n:
        best, bj = float('inf'), None
        for i in inside:
            for j in range(n):
                if j not in inside and D[i][j] < best:
                    best, bj = D[i][j], j
        total += best
        inside.add(bj)
    return total
