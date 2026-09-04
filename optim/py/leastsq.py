# -*- coding: utf-8 -*-
"""최소제곱 — 최적화에서 가장 자주 나오는 구조.

   목적함수가 ½‖r(x)‖² 꼴이면, 일반적인 최적화 알고리즘보다 훨씬 나은 것을 만들 수 있다.
   이유는 헤세가 거의 공짜로 나오기 때문이다:

       ∇f  = Jᵀr
       ∇²f = JᵀJ + Σ rᵢ ∇²rᵢ
                    ─────────  잔차가 작으면 무시할 수 있다

   야코비 J 만 알면 ∇²f ≈ JᵀJ 를 쓸 수 있고, 이것은 항상 양의 반정부호다.
   가우스–뉴턴과 Levenberg–Marquardt 가 이 관찰 하나 위에 서 있다.
"""
import math

from py import linalg as la


class Result(object):
    def __init__(self, x, cost, nit, converged, msg, history=None):
        self.x = x
        self.cost = cost
        self.nit = nit
        self.converged = converged
        self.msg = msg
        self.history = history or []

    def __repr__(self):
        return ('<LSQ %s nit=%d cost=%.6g>'
                % ('수렴' if self.converged else '미수렴', self.nit, self.cost))


# ---------------------------------------------------------------- 선형 최소제곱

def solve_normal(A, b):
    """정규방정식 AᵀA x = Aᵀb 를 세워 푼다.

       가장 빠르고(대칭 양정부호라 촐레스키가 쓰인다) 가장 위험하다.
       κ(AᵀA) = κ(A)² 이므로 조건수가 제곱된다 — 4부 정리 15.3.
       A 가 잘 조건 지어져 있고 속도가 중요할 때만 쓸 것.
    """
    At = la.transpose(A)
    return la.solve(la.matmul(At, A), la.matvec(At, b))


def solve_qr(A, b):
    """하우스홀더 QR 로 푼다 — 실무의 기본값.

       AᵀA 를 만들지 않으므로 조건수를 제곱하지 않는다. 비용은 O(2mn² − 2n³/3).
    """
    return la.lstsq(A, b)


def solve_svd(A, b, rcond=1e-12):
    """SVD 로 푼다. 랭크가 부족해도 답을 주며, 그 답은 최소노름 해다.

       x = Σ (uᵢᵀb / σᵢ) vᵢ,  단 σᵢ 가 너무 작으면 그 항을 버린다.
       버리는 기준 rcond 가 곧 '이 방향의 정보는 잡음이다'라는 판단이다.
    """
    U, s, V = la.svd(A)
    if not s:
        return [0.0] * len(A[0])
    cut = rcond * s[0]
    ub = la.matvec(la.transpose(U), b)
    coef = [(ub[i] / s[i] if s[i] > cut else 0.0) for i in range(len(s))]
    return la.matvec(V, coef)


def pinv(A, rcond=1e-12):
    """무어–펜로즈 의사역행렬 A⁺ = V Σ⁺ Uᵀ."""
    U, s, V = la.svd(A)
    cut = rcond * (s[0] if s else 0.0)
    Sp = la.zeros(len(s), len(s))
    for i in range(len(s)):
        Sp[i][i] = (1.0 / s[i]) if s[i] > cut else 0.0
    return la.matmul(la.matmul(V, Sp), la.transpose(U))


def residual(A, x, b):
    return la.vsub(la.matvec(A, x), b)


def polyfit(xs, ys, deg):
    """반데르몽드 행렬을 세워 다항식을 맞춘다. 반환은 낮은 차수부터의 계수.

       주의: 반데르몽드 행렬은 차수가 조금만 높아져도 조건수가 폭발한다.
       실무에서는 직교다항식(체비쇼프 등) 기저를 쓴다 — 4부에서 실측한다.
    """
    A = [[x ** k for k in range(deg + 1)] for x in xs]
    return solve_qr(A, list(ys))


def ridge(A, b, lam):
    """릿지 회귀 min ‖Ax−b‖² + λ‖x‖².

       확대 행렬 [A; √λ I] 와 [b; 0] 의 최소제곱과 같다 — 그래서 정규방정식을
       만들지 않고 QR 로 풀 수 있다. λ>0 이면 랭크가 부족해도 유일해가 있다.
    """
    m, n = len(A), len(A[0])
    r = math.sqrt(lam)
    Aa = [row[:] for row in A] + [[r if i == j else 0.0 for j in range(n)]
                                  for i in range(n)]
    ba = list(b) + [0.0] * n
    if lam == 0.0:
        return solve_qr(A, list(b))
    return solve_qr(Aa, ba)


def chebyshev_design(xs, deg, lo=None, hi=None):
    """체비쇼프 기저 T₀..T_deg 로 설계행렬을 만든다.

       왜 단항 기저(1, x, x², …)를 쓰지 않는가: 그 기저의 함수들이 구간 위에서
       서로 거의 평행해져 반데르몽드 행렬의 조건수가 지수적으로 커진다.
       체비쇼프 다항식은 [−1,1] 에서 서로 거의 직교라 조건수가 훨씬 낮다.
       점화식 T₀=1, T₁=t, T_{k+1} = 2t·T_k − T_{k−1} 로 O(deg) 에 만든다.
    """
    lo = min(xs) if lo is None else lo
    hi = max(xs) if hi is None else hi
    span = (hi - lo) or 1.0
    A = []
    for x in xs:
        t = 2.0 * (x - lo) / span - 1.0          # [lo,hi] → [−1,1]
        row = [1.0]
        if deg >= 1:
            row.append(t)
        for k in range(2, deg + 1):
            row.append(2.0 * t * row[k - 1] - row[k - 2])
        A.append(row)
    return A


def weighted(A, b, w):
    """가중 최소제곱 min Σ wᵢ(aᵢᵀx − bᵢ)².  √wᵢ 로 행을 스케일하면 보통 문제가 된다.

       측정마다 신뢰도가 다를 때 쓴다. wᵢ = 1/σᵢ² 로 두면 최대가능도 추정과 같다.
    """
    rt = [math.sqrt(v) for v in w]
    Aw = [[rt[i] * v for v in A[i]] for i in range(len(A))]
    bw = [rt[i] * b[i] for i in range(len(b))]
    return solve_qr(Aw, bw)


def huber_irls(A, b, delta=1.0, iters=50, tol=1e-12):
    """후버 손실의 로버스트 회귀 — IRLS(반복 재가중 최소제곱).

       손실:  ρ(r) = ½r²            (|r| ≤ δ)
                    δ|r| − ½δ²      (그 밖)
       작은 잔차에는 제곱, 큰 잔차에는 절댓값처럼 굴어 이상치의 영향을 제한한다.
       ρ 는 볼록이고 C¹ 이지만 C² 가 아니다.

       IRLS 의 착상: ρ′(r)/r 을 가중치로 보면 매 반복이 가중 최소제곱 한 번이다.
       후버는 볼록이므로 이 반복이 전역해로 수렴한다.
    """
    x = solve_qr(A, list(b))
    for _ in range(iters):
        r = residual(A, x, b)
        w = [1.0 if abs(v) <= delta else delta / abs(v) for v in r]
        x_new = weighted(A, b, w)
        if la.norm(la.vsub(x_new, x)) <= tol * max(1.0, la.norm(x)):
            return x_new
        x = x_new
    return x


def solve_cg(A, b, tol=1e-10, maxiter=None):
    """CGLS — AᵀA 를 세우지 않고 최소제곱을 켤레기울기로 푼다.

       쓰는 연산은 A·v 와 Aᵀ·w 두 가지뿐이다. 그래서
         · A 가 희소하거나 (합성곱처럼) 함수로만 주어져도 쓸 수 있고,
         · AᵀA 를 만들 때 생기는 정보 손실(정리 15.3)을 겪지 않는다.
       수렴 속도는 여전히 κ(A)² 가 아니라 κ(A) 에 가깝게 거동한다.

       O(k·(nnz(A))) 시간, O(m+n) 공간.  반환: (x, 반복 수)
    """
    m, n = len(A), len(A[0])
    At = la.transpose(A)
    maxiter = maxiter or 4 * n
    x = [0.0] * n
    r = list(b)                                  # r = b − A·0
    sv = la.matvec(At, r)
    p = list(sv)
    gamma = la.dot(sv, sv)
    g0 = math.sqrt(gamma) or 1.0
    for k in range(maxiter):
        if math.sqrt(gamma) / g0 <= tol:
            return x, k
        q = la.matvec(A, p)
        qq = la.dot(q, q)
        if qq <= 0.0:
            return x, k
        alpha = gamma / qq
        x = la.axpy(alpha, p, x)
        r = la.axpy(-alpha, q, r)
        sv = la.matvec(At, r)
        gamma_new = la.dot(sv, sv)
        p = la.axpy(gamma_new / gamma, p, sv)
        gamma = gamma_new
    return x, maxiter


# ---------------------------------------------------------------- 비선형 최소제곱

def _cost(r):
    return 0.5 * math.fsum(v * v for v in r)


def gauss_newton(resid, jac, x0, tol=1e-10, maxiter=200, damping=True):
    """가우스–뉴턴법:  (JᵀJ) p = −Jᵀr  를 풀어 한 걸음.

       헤세의 2차 항 Σrᵢ∇²rᵢ 을 버린다. 잔차가 작거나 모형이 거의 선형이면
       그 항이 작아서 근사가 좋고, 뉴턴법에 가까운 속도가 나온다.
       잔차가 크면 수렴이 느려지거나 발산한다 — 그때가 LM 을 쓸 때다.

       damping=True 면 Armijo 되추적을 붙여 전역화한다.
    """
    x = [float(v) for v in x0]
    hist = []
    for k in range(maxiter):
        r = resid(x)
        J = jac(x)
        g = la.matvec(la.transpose(J), r)               # ∇f = Jᵀr
        gn = la.norm(g)
        hist.append({'k': k, 'cost': _cost(r), 'gnorm': gn, 'lam': 0.0})
        if gn <= tol:
            return Result(x, _cost(r), k, True, '기울기 노름이 허용오차 이하', hist)
        JtJ = la.matmul(la.transpose(J), J)
        try:
            p = [-v for v in la.solve(JtJ, g)]
        except la.SingularMatrix:
            return Result(x, _cost(r), k, False, 'JᵀJ 가 특이하다 — LM 을 쓸 것', hist)
        a, f0 = 1.0, _cost(r)
        if damping:
            gtd = la.dot(g, p)
            for _ in range(40):
                if _cost(resid(la.axpy(a, p, x))) <= f0 + 1e-4 * a * gtd:
                    break
                a *= 0.5
        x = la.axpy(a, p, x)
    return Result(x, _cost(resid(x)), maxiter, False, '최대 반복 도달', hist)


def levenberg_marquardt(resid, jac, x0, tol=1e-10, maxiter=300,
                        lam0=1e-3, up=10.0, down=10.0):
    """Levenberg–Marquardt:  (JᵀJ + λ diag(JᵀJ)) p = −Jᵀr

       λ 를 키우면 걸음이 짧아지고 방향이 −∇f (경사하강) 쪽으로 돈다.
       λ→0 이면 가우스–뉴턴이 된다. 즉 신뢰영역을 감쇠 매개변수로 표현한 것이다
       (3부 13장의 τ 와 같은 절충).

       대각으로 스케일하는 이유: 변수마다 단위가 다르면 λI 는 스케일에 의존한다.
       diag(JᵀJ) 를 쓰면 각 변수의 곡률에 비례해 감쇠가 걸린다.
    """
    x = [float(v) for v in x0]
    lam = lam0
    r = resid(x)
    f = _cost(r)
    hist = []
    for k in range(maxiter):
        J = jac(x)
        Jt = la.transpose(J)
        g = la.matvec(Jt, r)
        gn = la.norm(g)
        hist.append({'k': k, 'cost': f, 'gnorm': gn, 'lam': lam})
        if gn <= tol:
            return Result(x, f, k, True, '기울기 노름이 허용오차 이하', hist)
        JtJ = la.matmul(Jt, J)
        n = len(x)
        solved = False
        for _ in range(60):                              # λ 를 키우며 풀릴 때까지
            M = [row[:] for row in JtJ]
            for i in range(n):
                M[i][i] += lam * max(JtJ[i][i], 1e-12)
            try:
                p = [-v for v in la.solve(M, g)]
            except la.SingularMatrix:
                lam *= up
                continue
            x_new = la.vadd(x, p)
            r_new = resid(x_new)
            f_new = _cost(r_new)
            if f_new < f:                                # 받아들인다 — λ 를 줄인다
                x, r, f = x_new, r_new, f_new
                lam = max(lam / down, 1e-12)
                solved = True
                break
            lam *= up                                     # 실패 — 더 조심스럽게
            if lam > 1e14:
                break
        if not solved:
            return Result(x, f, k, gn <= tol * 10,
                          '감쇠를 키워도 개선되지 않는다(국소 최소일 수 있다)', hist)
    return Result(x, f, maxiter, False, '최대 반복 도달', hist)
