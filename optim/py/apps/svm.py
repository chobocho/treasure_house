# -*- coding: utf-8 -*-
"""서포트 벡터 머신 — 쌍대성이 알고리즘을 바꾸는 자리.

   원문제 (소프트 마진)
       min ½‖w‖² + C Σ ξᵢ   s.t.  yᵢ(wᵀxᵢ + b) ≥ 1 − ξᵢ,  ξ ≥ 0

   라그랑주 쌍대 (5부 21장의 방식 그대로 유도된다)
       max  Σαᵢ − ½ ΣΣ αᵢαⱼ yᵢyⱼ (xᵢᵀxⱼ)
       s.t. 0 ≤ αᵢ ≤ C,  Σ αᵢ yᵢ = 0

   쌍대로 가면 두 가지가 생긴다.
     · 자료가 <내적으로만> 등장한다 → 커널로 바꿔 끼울 수 있다
     · 제약이 상자 + 초평면 하나라 <투영이 값싸다> → 투영경사법이 바로 쓰인다

   그리고 상보여유(5부 정리 20.3)가 서포트 벡터의 정의를 준다:
       αᵢ = 0        → 마진 밖, 해에 영향 없음
       0 < αᵢ < C    → 마진 위 (경계에 정확히 놓임)
       αᵢ = C        → 마진 안쪽 또는 오분류
"""
import math
import random

from py import linalg as la


def project_box_simplexlike(v, lo, hi, a, b, iters=64):
    """{lo ≤ x ≤ hi, aᵀx = b} 로의 유클리드 투영.

       KKT 를 쓰면 x(θ) = clip(v − θa, lo, hi) 꼴이고, θ 는 aᵀx(θ) = b 를 만족하는
       유일한 수다. aᵀx(θ) 가 θ 에 대해 단조 감소하므로 이분법으로 찾는다.
       2부 명제 5.7(단체 투영)과 완전히 같은 구조다.

       이분법 64회면 초기 구간 2e9 가 1e-9 아래로 좁혀진다 — 배정밀도에서 충분하다.
    """
    def val(th):
        return math.fsum(a[i] * min(hi, max(lo, v[i] - th * a[i]))
                         for i in range(len(v)))

    loθ, hiθ = -1e9, 1e9
    for _ in range(iters):
        mid = 0.5 * (loθ + hiθ)
        if val(mid) > b:
            loθ = mid
        else:
            hiθ = mid
    th = 0.5 * (loθ + hiθ)
    return [min(hi, max(lo, v[i] - th * a[i])) for i in range(len(v))]


def linear_kernel(a, b):
    return la.dot(a, b)


def rbf_kernel(gamma):
    def k(a, b):
        d2 = math.fsum((a[i] - b[i]) ** 2 for i in range(len(a)))
        return math.exp(-gamma * d2)
    return k


def train_dual(X, y, C=1.0, kernel=None, iters=4000, step=None):
    """쌍대 문제를 투영경사법으로 푼다 (5부 22장).

       목적은 최대화이므로 −목적을 최소화한다. 기울기는
           ∇(−D)(α) = Qα − 1,   Q_ij = yᵢyⱼ K(xᵢ, xⱼ)
       보폭은 1/λ_max(Q) 로 잡는다(3부 보조정리 9.1).
    """
    K = kernel or linear_kernel
    n = len(X)
    Q = la.zeros(n, n)
    for i in range(n):
        for j in range(n):
            Q[i][j] = y[i] * y[j] * K(X[i], X[j])
    if step is None:
        vals, _ = la.eigh(Q)
        L = max(vals[-1], 1e-12)
        step = 1.0 / L
    alpha = [0.0] * n
    for _ in range(iters):
        g = [la.dot(Q[i], alpha) - 1.0 for i in range(n)]
        alpha = project_box_simplexlike(la.axpy(-step, g, alpha), 0.0, C, y, 0.0)
    return alpha, Q


def decision_function(X, y, alpha, C, kernel=None):
    """w 와 b 를 복원한다. b 는 0 < αᵢ < C 인 점들(마진 위)에서 평균으로 구한다."""
    K = kernel or linear_kernel
    n = len(X)

    def f_raw(z):
        return math.fsum(alpha[i] * y[i] * K(X[i], z) for i in range(n))

    on_margin = [i for i in range(n) if 1e-6 < alpha[i] < C - 1e-6]
    if on_margin:
        b = math.fsum(y[i] - f_raw(X[i]) for i in on_margin) / len(on_margin)
    else:
        b = 0.0
    return lambda z: f_raw(z) + b, b


def primal_weights(X, y, alpha):
    """선형 커널일 때 w = Σ αᵢ yᵢ xᵢ — 정류조건에서 바로 나온다."""
    d = len(X[0])
    w = [0.0] * d
    for i in range(len(X)):
        if alpha[i] != 0.0:
            w = la.axpy(alpha[i] * y[i], X[i], w)
    return w


def support_vectors(alpha, C, tol=1e-6):
    """상보여유로 세 부류로 나눈다."""
    free, bound = [], []
    for i, a in enumerate(alpha):
        if a > C - tol:
            bound.append(i)
        elif a > tol:
            free.append(i)
    return {'margin': free, 'bound': bound,
            'total': len(free) + len(bound), 'n': len(alpha)}


def separable_data(n=40, seed=0, margin=1.5):
    """선형분리 가능한 2차원 자료 — 정답 경계를 아는 상태에서 실험하기 위해."""
    rng = random.Random(seed)
    X, y = [], []
    for _ in range(n):
        lab = rng.choice([-1.0, 1.0])
        cx = 1.0 * lab * margin
        X.append([cx + rng.gauss(0, 0.6), rng.gauss(0, 1.2)])
        y.append(lab)
    return X, y
