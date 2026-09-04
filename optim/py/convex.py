# -*- coding: utf-8 -*-
"""볼록성 — 수치 검사와 투영 연산.

   이 파일은 두 가지 일을 한다.
     1. "이 함수가 볼록한가"를 기계로 의심해 보는 도구 (증명은 못 하지만 반례는 잘 찾는다).
     2. 볼록집합 위로의 투영 — 5부(투영경사)와 8부(근접경사)가 그대로 쓴다.

   투영이 왜 그렇게 중요한가: 제약이 있는 문제를 "일단 자유롭게 한 걸음 간 뒤
   실행가능집합으로 되돌린다"로 풀 수 있게 해 주기 때문이다. 그 되돌리는 연산이
   비확장(nonexpansive)이라는 성질(정리 2부 1장) 덕분에 수렴 증명이 그대로 산다.
"""
import math
import random

from py import linalg as la
from py import numdiff as nd


# ---------------------------------------------------------------- 젠센 검사

def jensen_gap(f, x, y, t):
    """볼록성의 정의가 남기는 여유:  t·f(x) + (1−t)·f(y) − f(t·x + (1−t)·y).

       볼록이면 항상 ≥ 0. 음수가 나오면 그 (x, y, t) 가 곧 반례다.
    """
    z = [t * a + (1.0 - t) * b for a, b in zip(x, y)]
    return t * f(x) + (1.0 - t) * f(y) - f(z)


def looks_convex(f, n, trials=500, seed=0, scale=2.0, tol=1e-9):
    """무작위 현(弦)을 그어 젠센 부등식을 어기는 곳이 있는지 본다.

       통과했다고 볼록임이 증명되는 것은 아니다 — 반례를 못 찾았을 뿐이다.
       그래도 실무에서 "볼록한 줄 알았던 손실함수"의 오류를 대단히 잘 잡아낸다.
       O(trials) 회의 함수 호출.
    """
    rng = random.Random(seed)
    for _ in range(trials):
        x = [rng.uniform(-scale, scale) for _ in range(n)]
        y = [rng.uniform(-scale, scale) for _ in range(n)]
        t = rng.random()
        if jensen_gap(f, x, y, t) < -tol:
            return False
    return True


def worst_jensen(f, n, trials=2000, seed=0, scale=2.0):
    """가장 크게 어긋난 현을 돌려준다 — 반례를 보여 주기 위한 도구."""
    rng = random.Random(seed)
    worst = (0.0, None, None, None)
    for _ in range(trials):
        x = [rng.uniform(-scale, scale) for _ in range(n)]
        y = [rng.uniform(-scale, scale) for _ in range(n)]
        t = rng.random()
        g = jensen_gap(f, x, y, t)
        if g < worst[0]:
            worst = (g, x, y, t)
    return worst


def curvature_range(problem, points):
    """표본점들에서 헤세의 최소·최대 고윳값 — 강볼록 상수 μ 와 평활 상수 L 의 추정.

       μ = min λ_min,  L = max λ_max.  μ > 0 이면 그 표본 위에서 강볼록해 보인다는 뜻.
       전 구간의 보장이 아니라 표본의 관찰이라는 점을 잊지 말 것.
    """
    mu, L = float('inf'), float('-inf')
    for x in points:
        H = problem.hess(x) if problem.hess is not None else nd.hessian(problem.f, x)
        vals, _ = la.eigh(H)
        mu = min(mu, vals[0])
        L = max(L, vals[-1])
    return mu, L


# ---------------------------------------------------------------- 투영

def proj_box(x, lo, hi):
    """상자 {x : lo ≤ xᵢ ≤ hi} 로의 투영 — 성분마다 자르면 끝이다.

       왜 성분별로 나뉘는가: 목적 ‖x−z‖² = Σ(xᵢ−zᵢ)² 이 성분별로 분리되고
       제약도 성분별로 분리되기 때문이다. 분리 가능한 문제는 따로 풀어도 된다.
    """
    return [min(hi, max(lo, v)) for v in x]


def proj_ball(x, r=1.0, center=None):
    """공 {z : ‖z−c‖ ≤ r} 로의 투영. 밖이면 반지름으로 줄이고, 안이면 그대로."""
    c = [0.0] * len(x) if center is None else center
    d = la.vsub(x, c)
    n = la.norm(d)
    if n <= r:
        return list(x)
    s = r / n
    return [ci + s * di for ci, di in zip(c, d)]


def proj_simplex(x, a=1.0):
    """확률 단체 {z : zᵢ ≥ 0, Σzᵢ = a} 로의 유클리드 투영.

       해의 꼴은 z = max(x − θ, 0) 이고, θ 는 Σ max(xᵢ−θ, 0) = a 를 만족하는 유일한 수다.
       (KKT 조건에서 나온다 — 5부에서 이 유도를 정식으로 한다.)
       θ 를 이분법으로 찾을 수도 있지만, 정렬하면 정확히 한 번에 찾을 수 있다.

       O(n log n) 시간, O(n) 공간.
    """
    n = len(x)
    if n == 0:
        return []
    u = sorted(x, reverse=True)
    css = 0.0
    rho, theta = 0, (u[0] - a)
    for j in range(n):
        css += u[j]
        t = (css - a) / (j + 1)
        # u[j] > t 인 가장 큰 j 가 활성 집합의 크기다.
        if u[j] - t > 0.0:
            rho, theta = j + 1, t
    return [max(v - theta, 0.0) for v in x]


def proj_halfspace(x, a, b):
    """반공간 {z : aᵀz ≤ b} 로의 투영.  aᵀx ≤ b 면 그대로, 아니면 법선 방향으로 되돌린다."""
    ax = la.dot(a, x)
    if ax <= b:
        return list(x)
    na = la.dot(a, a)
    if na == 0.0:
        return list(x)
    s = (ax - b) / na
    return [xi - s * ai for xi, ai in zip(x, a)]


def proj_affine(x, A, b):
    """아핀 부분공간 {z : Az = b} 로의 투영:  z = x − Aᵀ(AAᵀ)⁻¹(Ax − b)."""
    r = la.vsub(la.matvec(A, x), b)
    AAt = la.matmul(A, la.transpose(A))
    lam = la.solve(AAt, r)
    corr = la.matvec(la.transpose(A), lam)
    return la.vsub(x, corr)


# ---------------------------------------------------------------- 열경사

def subgrad_abs(x, pick=0.0):
    """f(x) = ‖x‖₁ 의 열경사 하나.

       xᵢ ≠ 0 이면 sign(xᵢ) 로 결정되지만, xᵢ = 0 에서는 [−1, 1] 의 아무 값이나 된다.
       그 자유도가 9부에서 열경사법이 왜 단조 감소하지 않는지를 설명한다.
    """
    out = []
    for v in x:
        if v > 0.0:
            out.append(1.0)
        elif v < 0.0:
            out.append(-1.0)
        else:
            out.append(pick)
    return out


def soft_threshold(x, t):
    """‖·‖₁ 의 근접연산자:  prox_{t‖·‖₁}(x) = sign(x)·max(|x|−t, 0).

       8부의 ISTA/FISTA 와 라쏘가 계수를 정확히 0 으로 보내는 장치가 바로 이 한 줄이다.
    """
    # +0.0 을 더해 −0.0 을 없앤다. 부호 있는 0 은 출력에서 "-0.00" 으로 보여
    # "이 계수는 0 이 되었다"는 사실을 도리어 흐린다.
    return [math.copysign(max(abs(v) - t, 0.0), v) + 0.0 for v in x]
