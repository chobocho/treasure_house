# -*- coding: utf-8 -*-
"""제약 최적화 — KKT 조건과 그것을 찾는 알고리즘들.

   제약을 다루는 방법은 크게 셋이다.
     · 실행가능집합 안에 머문다        → 투영경사법 (제약이 단순할 때)
     · 제약 위반을 목적함수로 옮긴다   → 페널티법 (단순하지만 병조건화)
     · 승수를 함께 추정한다            → 증강 라그랑주 (페널티의 결함을 고친 것)
   그리고 이 셋 모두가 결국 KKT 조건을 만족하는 점을 찾으려는 시도다.
"""
import math

from py import linalg as la
from py import unconstrained as uc


class Problem(object):
    """제약 문제의 최소 서술 — KKT 잔차를 재기 위한 것.

       min f(x)  s.t.  ineq_i(x) ≤ 0,  eq_j(x) = 0
    """

    def __init__(self, f, grad, ineq=None, ineq_grad=None, eq=None, eq_grad=None):
        self.f = f
        self.grad = grad
        self.ineq = ineq or []
        self.ineq_grad = ineq_grad or []
        self.eq = eq or []
        self.eq_grad = eq_grad or []


class Result(object):
    def __init__(self, x, fx, nit, converged, msg, lam=None, nu=None, mu=None,
                 history=None, inner=0):
        self.x = x
        self.fx = fx
        self.nit = nit
        self.converged = converged
        self.msg = msg
        self.lam = lam or []
        self.nu = nu or []
        self.mu = mu
        self.history = history or []
        self.inner = inner          # 하위 무제약 문제를 푸는 데 든 총 반복 수

    def __repr__(self):
        return ('<CON %s nit=%d f=%.6g>'
                % ('수렴' if self.converged else '미수렴', self.nit, self.fx))


# ---------------------------------------------------------------- 등식제약 QP

def solve_eq_qp(G, c, A, b):
    """min ½xᵀGx + cᵀx  s.t. Ax = b 를 KKT 선형계로 한 번에 푼다.

       정류조건 Gx + c + Aᵀλ = 0 과 제약 Ax = b 를 하나의 대칭 부정부호 계로 묶는다:

           [ G   Aᵀ ] [x]   [−c]
           [ A   0  ] [λ] = [ b]

       이 계는 (G ≻ 0 이고 A 의 행이 독립이면) 정칙이다. 대각에 0 블록이 있어
       양의 정부호가 아니므로 촐레스키를 쓸 수 없다 — LU 로 푼다.
       O((n+m)³).
    """
    n, m = len(G), len(A)
    K = la.zeros(n + m, n + m)
    for i in range(n):
        for j in range(n):
            K[i][j] = G[i][j]
        for j in range(m):
            K[i][n + j] = A[j][i]
    for i in range(m):
        for j in range(n):
            K[n + i][j] = A[i][j]
    rhs = [-v for v in c] + list(b)
    sol = la.solve(K, rhs)
    return sol[:n], sol[n:]


# ---------------------------------------------------------------- KKT 잔차

def kkt_residual(problem, x, lam=None, nu=None):
    """KKT 조건 네 가지를 각각 얼마나 어겼는지 잰다.

       ① 정류성        ∇f + Σλᵢ∇gᵢ + Σνⱼ∇hⱼ = 0
       ② 원문제 실행가능  gᵢ ≤ 0,  hⱼ = 0
       ③ 쌍대 실행가능    λᵢ ≥ 0
       ④ 상보여유        λᵢ gᵢ = 0

       알고리즘이 '수렴했다'고 말할 때 실제로 확인해야 하는 것이 이 네 수다.
    """
    lam = list(lam or [0.0] * len(problem.ineq))
    nu = list(nu or [0.0] * len(problem.eq))
    g = list(problem.grad(x))
    for i, gi in enumerate(problem.ineq_grad):
        g = la.axpy(lam[i], gi(x), g)
    for j, hj in enumerate(problem.eq_grad):
        g = la.axpy(nu[j], hj(x), g)
    gv = [f(x) for f in problem.ineq]
    hv = [f(x) for f in problem.eq]
    return {
        'stationarity': la.norm(g),
        'primal_feasibility': max([0.0] + [max(0.0, v) for v in gv]
                                  + [abs(v) for v in hv]),
        'dual_feasibility': max([0.0] + [max(0.0, -v) for v in lam]),
        'complementarity': max([0.0] + [abs(lam[i] * gv[i]) for i in range(len(gv))]),
    }


# ---------------------------------------------------------------- 투영경사법

def projected_gradient(f, grad, proj, x0, step=None, tol=1e-10, maxiter=2000,
                       keep_history=False):
    """x ← P_C(x − α∇f(x)).

       '자유롭게 한 걸음 간 뒤 실행가능집합으로 되돌린다.' 되돌리는 연산이
       비확장(정리 5.6)이라 무제약 경사하강의 수렴 증명이 거의 그대로 옮겨진다.

       종료 판정은 ‖∇f‖ 가 아니라 <b>사상의 이동량</b> ‖x − P(x−α∇f)‖/α 로 한다.
       제약 위에서는 ∇f 가 0 이 아닌 것이 정상이기 때문이다(정리 7.4).
    """
    x = proj([float(v) for v in x0])
    a = step or 1.0
    hist = []
    for k in range(maxiter):
        g = grad(x)
        x_new = proj(la.axpy(-a, g, x))
        gap = la.norm(la.vsub(x_new, x)) / a
        if keep_history:
            hist.append({'k': k, 'f': f(x), 'gap': gap})
        if gap <= tol:
            return Result(x, f(x), k, True, '투영경사 사상의 고정점', history=hist)
        x = x_new
    return Result(x, f(x), maxiter, False, '최대 반복 도달', history=hist)


# ---------------------------------------------------------------- 페널티법

class _Sub(object):
    """무제약 하위 문제를 minimize 에 넘기기 위한 최소 어댑터."""

    def __init__(self, f, g):
        self.f = f
        self.grad = g

    hess = None


def penalty_method(f, grad, h, hjac, x0, mu0=1.0, growth=10.0, outer=8,
                   tol=1e-10, maxiter=2000, method='bfgs'):
    """이차 페널티:  min f(x) + (μ/2)‖h(x)‖².

       제약을 목적함수로 흡수해 무제약 문제로 바꾼다. 단순하지만 두 가지 결함이 있다.
         · μ 가 유한하면 해가 <b>정확히 실행가능해지지 않는다</b>(항상 조금 위반).
         · μ 를 키우면 헤세의 조건수가 μ 에 비례해 커져 하위 문제가 병조건화된다.
       증강 라그랑주가 이 둘을 모두 고친다.
    """
    x = [float(v) for v in x0]
    mu = mu0
    inner = 0
    for it in range(outer):
        def F(z, mu=mu):
            hv = h(z)
            return f(z) + 0.5 * mu * math.fsum(v * v for v in hv)

        def G(z, mu=mu):
            hv = h(z)
            J = hjac(z)
            g = list(grad(z))
            for j in range(len(hv)):
                g = la.axpy(mu * hv[j], J[j], g)
            return g

        r = uc.minimize(_Sub(F, G), x, method=method,
                        line_search='armijo' if method == 'gd' else None,
                        tol=tol, maxiter=maxiter)
        x = r.x
        inner += r.nit
        if it < outer - 1:
            mu *= growth
    return Result(x, f(x), outer, True, '페널티 반복 종료', mu=mu, inner=inner)


def augmented_lagrangian(f, grad, h, hjac, x0, mu0=1.0, outer=20,
                         tol=1e-10, maxiter=2000, growth=2.0, eta=0.25,
                         ctol=1e-9, mu_max=1e6):
    """증강 라그랑주:  L_A(x,ν;μ) = f(x) + νᵀh(x) + (μ/2)‖h(x)‖².

       페널티 항에 <b>승수 추정 ν</b>를 더한 것이다. 하위 문제를 푼 뒤
           ν ← ν + μ h(x)
       로 갱신하면, μ 를 무한대로 보내지 않아도 h(x) → 0 이 된다.

       왜 되는가: 최적점에서 ∇f + Jᵀν⋆ = 0 이어야 하는데, 페널티만 쓰면 그 ν⋆ 역할을
       μh(x) 가 대신해야 하므로 h(x) ≈ ν⋆/μ 만큼 위반이 남는다. ν 를 따로 들고
       있으면 그 짐을 페널티가 질 필요가 없다 — 5부 22장에서 정식으로 증명한다.
    """
    x = [float(v) for v in x0]
    nu = [0.0] * len(h(x))
    mu = mu0
    inner = 0
    prev = None
    for it in range(outer):
        def F(z, nu=list(nu), mu=mu):
            hv = h(z)
            return (f(z) + math.fsum(nu[j] * hv[j] for j in range(len(hv)))
                    + 0.5 * mu * math.fsum(v * v for v in hv))

        def G(z, nu=list(nu), mu=mu):
            hv = h(z)
            J = hjac(z)
            g = list(grad(z))
            for j in range(len(hv)):
                g = la.axpy(nu[j] + mu * hv[j], J[j], g)
            return g

        r = uc.minimize(_Sub(F, G), x, method='bfgs', tol=tol, maxiter=maxiter)
        x = r.x
        inner += r.nit
        hv = h(x)
        viol = max(abs(v) for v in hv) if hv else 0.0
        nu = [nu[j] + mu * hv[j] for j in range(len(hv))]
        if viol <= ctol:
            break                              # 이미 실행가능하다 — μ 를 더 키우지 않는다
        if prev is not None and viol > eta * prev:
            # 위반이 충분히 줄지 않았다면 벌을 키운다. 다만 viol 이 이미 수치 바닥에
            # 닿은 뒤에는 비율이 늘 1 근처가 되므로, ctol 위에서만 이 규칙을 적용한다.
            # 그러지 않으면 μ 가 무한정 커져 하위 문제가 병조건화되고, 승수 갱신
            # ν += μh 에서 μ 가 h 의 반올림 오차를 증폭한다.
            mu = min(mu * growth, mu_max)
        prev = viol
    return Result(x, f(x), it + 1, True, '증강 라그랑주 종료', nu=nu, lam=nu,
                  mu=mu, inner=inner)


# ---------------------------------------------------------------- 로그 배리어

def log_barrier(f, grad, gs, gjac, x0, t0=1.0, mu=10.0, outer=30,
                tol=1e-9, maxiter=2000):
    """로그 배리어(내부점의 원형):  min t·f(x) − Σ log(−gᵢ(x)).

       실행가능 영역 <b>안쪽</b>에서만 정의되고 경계에 다가가면 +∞ 로 튄다.
       t 를 키우면 배리어의 영향이 줄어 원문제에 가까워진다.
       중심 경로 x⋆(t) 의 최적성 간격은 정확히 m/t 이다(6부 정리 26.4).
    """
    x = [float(v) for v in x0]
    t = t0
    m = len(gs)
    for it in range(outer):
        def F(z, t=t):
            v = [g(z) for g in gs]
            if any(u >= 0 for u in v):
                return float('inf')
            return t * f(z) - math.fsum(math.log(-u) for u in v)

        def G(z, t=t):
            v = [g(z) for g in gs]
            J = [j(z) for j in gjac]
            out = [t * u for u in grad(z)]
            for i in range(m):
                out = la.axpy(-1.0 / v[i], J[i], out)
            return out

        r = uc.minimize(_Sub(F, G), x, method='bfgs', tol=tol, maxiter=maxiter)
        x = r.x
        if m / float(t) < tol:
            break
        t *= mu
    return Result(x, f(x), it + 1, True, '배리어 종료 (간격 ≤ m/t)', mu=t)
