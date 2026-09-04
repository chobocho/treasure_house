# -*- coding: utf-8 -*-
"""포트폴리오 최적화 — 마코위츠 평균–분산 모형.

   최적화 교재의 고전적인 예제이면서, 5부의 등식제약 QP 와 2부의 투영이 그대로
   쓰이는 자리다.

       min  ½ xᵀΣx          (위험)
       s.t. μᵀx = r          (목표 수익률)
            1ᵀx = 1          (예산)
            (선택) x ≥ 0      (공매도 금지)

   공매도를 허용하면 등식 제약만 남아 <닫힌 해>가 나온다(KKT 선형계 한 번).
   금지하면 부등식이 생겨 반복법이 필요하다 — 제약 하나가 문제의 성격을 바꾼다.
"""
import math

from py import constrained as cs
from py import convex as cx
from py import linalg as la


def stats(returns):
    """수익률 표본에서 평균 벡터와 공분산 행렬을 추정한다."""
    n = len(returns)
    d = len(returns[0])
    mu = [math.fsum(r[j] for r in returns) / n for j in range(d)]
    S = la.zeros(d, d)
    for r in returns:
        dev = [r[j] - mu[j] for j in range(d)]
        for a in range(d):
            for b in range(d):
                S[a][b] += dev[a] * dev[b]
    for a in range(d):
        for b in range(d):
            S[a][b] /= float(n - 1)
    return mu, S


def min_variance(S, mu, target, ridge=1e-10):
    """공매도를 허용한 평균–분산 최적화. KKT 선형계 한 번으로 끝난다 (5부 19장)."""
    d = len(mu)
    G = [row[:] for row in S]
    for i in range(d):
        G[i][i] += ridge
    A = [list(mu), [1.0] * d]
    b = [float(target), 1.0]
    x, lam = cs.solve_eq_qp(G, [0.0] * d, A, b)
    return x, lam


def min_variance_long_only(S, mu, target, rounds=6, iters=4000, rho0=1e2):
    """공매도 금지 버전 — 단체 투영 + 수익률 등식 페널티.

       실행가능집합 {x ≥ 0, 1ᵀx = 1} 은 확률 단체이고, 그 위로의 투영은 2부에서
       O(d log d) 로 구현해 두었다. 남은 등식 μᵀx = r 은 페널티로 다루고 ρ 를
       키워 가며 반복한다(5부 22장). 투영이 값싸다는 것이 이 설계의 이유다.

       반환: 가중치 (합이 정확히 1, 모두 ≥ 0)
    """
    d = len(mu)
    x = cx.proj_simplex([1.0 / d] * d)
    vals, _ = la.eigh(S)
    rho = rho0
    for _ in range(rounds):
        L = vals[-1] + rho * la.dot(mu, mu)
        step = 1.0 / L
        for _ in range(iters):
            g = la.matvec(S, x)
            g = la.axpy(rho * (la.dot(mu, x) - target), mu, g)
            x = cx.proj_simplex(la.axpy(-step, g, x))
        rho *= 10.0
    return x


def risk(S, x):
    return math.sqrt(max(0.0, la.dot(x, la.matvec(S, x))))


def frontier(S, mu, n=9, long_only=False):
    """효율적 경계 — 목표 수익률을 바꿔 가며 최소 위험을 구한다."""
    lo, hi = min(mu), max(mu)
    out = []
    for k in range(n):
        r = lo + (hi - lo) * k / float(n - 1)
        if long_only:
            x = min_variance_long_only(S, mu, r)
        else:
            x, _ = min_variance(S, mu, r)
        out.append({'target': r, 'risk': risk(S, x),
                    'actual_return': la.dot(mu, x), 'weights': x,
                    'sum': math.fsum(x), 'min_weight': min(x)})
    return out
