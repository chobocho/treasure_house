# -*- coding: utf-8 -*-
"""선형계획 — 심플렉스법과 원-쌍대 내부점법.

   모든 것이 선형이면 세 가지가 참이 된다.
     · 실행가능집합은 다면체이고, 최적해가 있으면 꼭짓점에 있다.
     · 꼭짓점은 기저해와 일대일 대응한다 → 유한 탐색이 가능하다(심플렉스).
     · 쌍대성이 완벽히 대칭이고 간격이 0 이다(강쌍대성이 언제나 성립).

   여기서는 교재용으로 전체 타블로 심플렉스를 쓴다. 실무 구현은 기저 역행렬을
   갱신하는 개정 심플렉스(revised simplex)를 쓰지만, 타블로 쪽이 매 단계에서 무슨
   일이 일어나는지 눈에 보인다. 큰 문제에서는 O(m·n) 메모리가 문제가 된다.
"""
import math

from py import linalg as la

INF = float('inf')
TOL = 1e-9


class LPResult(object):
    def __init__(self, status, x=None, obj=None, dual=None, nit=0, msg='',
                 basis=None, history=None):
        self.status = status          # 'optimal' | 'unbounded' | 'infeasible' | 'maxiter'
        self.x = x or []
        self.obj = obj
        self.dual = dual or []
        self.nit = nit
        self.msg = msg
        self.basis = basis or []
        self.history = history or []

    def __repr__(self):
        return '<LP %s obj=%s nit=%d>' % (self.status, self.obj, self.nit)


# ---------------------------------------------------------------- 타블로 심플렉스

def _pivot(T, basis, row, col):
    """(row, col) 을 축으로 가우스 소거. O(m·n)."""
    m = len(T)
    piv = T[row][col]
    T[row] = [v / piv for v in T[row]]
    for i in range(m):
        if i != row and T[i][col] != 0.0:
            f = T[i][col]
            Ti, Tr = T[i], T[row]
            for j in range(len(Tr)):
                Ti[j] -= f * Tr[j]
    basis[row] = col


def _choose_entering(T, cols, rule):
    """들어올 열을 고른다. 축소비용이 음수인 열만 후보다.

       Dantzig: 가장 음수인 것 — 보통 빠르지만 순환할 수 있다.
       Bland  : 첨자가 가장 작은 것 — 느리지만 순환하지 않음이 증명된다.
    """
    obj = T[-1]
    best, bestv = -1, -TOL
    for j in cols:
        if obj[j] < -TOL:
            if rule == 'bland':
                return j
            if obj[j] < bestv:
                best, bestv = j, obj[j]
    return best


def _ratio_test(T, col, rule):
    """나갈 행을 고른다 — 최소 비율. 동률이면 Bland 규칙으로 첨자가 작은 기저를 뺀다."""
    m = len(T) - 1
    best, bestr = -1, INF
    for i in range(m):
        if T[i][col] > TOL:
            r = T[i][-1] / T[i][col]
            if r < bestr - 1e-12:
                best, bestr = i, r
            elif abs(r - bestr) <= 1e-12 and best >= 0 and rule == 'bland':
                best = i if T[i][col] > 0 else best
    return best, bestr


def _simplex(T, basis, cols, rule='dantzig', maxiter=10000, trace=None):
    """축소비용이 모두 0 이상이 될 때까지 축을 옮긴다.

       반환: ('optimal'|'unbounded'|'maxiter', 반복 수)
    """
    for k in range(maxiter):
        col = _choose_entering(T, cols, rule)
        if col < 0:
            if trace is not None:
                trace.append({'k': k, 'basis': list(basis), 'obj': -T[-1][-1],
                              'enter': None, 'leave': None,
                              'rc': [T[-1][j] for j in cols]})
            return 'optimal', k
        row, ratio = _ratio_test(T, col, rule)
        if trace is not None:
            trace.append({'k': k, 'basis': list(basis), 'obj': -T[-1][-1],
                          'enter': col, 'leave': (basis[row] if row >= 0 else None),
                          'ratio': ratio, 'rc': [T[-1][j] for j in cols]})
        if row < 0:
            return 'unbounded', k          # 그 방향으로 무한히 개선된다
        _pivot(T, basis, row, col)
    return 'maxiter', maxiter


def _standard_form(c, A_ub, b_ub, A_eq, b_eq):
    """min cᵀx  s.t. A_ub x ≤ b_ub, A_eq x = b_eq, x ≥ 0
       을  min c̄ᵀz  s.t. Āz = b̄, z ≥ 0, b̄ ≥ 0  으로 바꾼다.

       부등식마다 슬랙 변수를 하나씩 붙이고, 우변이 음수인 행은 −1 을 곱한다.
       (그러면 슬랙 계수가 −1 이 되어 그 행에는 인공변수가 필요해진다.)
    """
    n = len(c)
    A_ub = A_ub or []
    b_ub = list(b_ub or [])
    A_eq = A_eq or []
    b_eq = list(b_eq or [])
    m1, m2 = len(A_ub), len(A_eq)
    m = m1 + m2
    ntot = n + m1
    A = la.zeros(m, ntot)
    b = [0.0] * m
    for i in range(m1):
        for j in range(n):
            A[i][j] = float(A_ub[i][j])
        A[i][n + i] = 1.0
        b[i] = float(b_ub[i])
    for i in range(m2):
        for j in range(n):
            A[m1 + i][j] = float(A_eq[i][j])
        b[m1 + i] = float(b_eq[i])
    for i in range(m):                      # 우변을 음이 아니게
        if b[i] < 0:
            A[i] = [-v for v in A[i]]
            b[i] = -b[i]
    cc = [float(v) for v in c] + [0.0] * m1
    return A, b, cc, n, m1


def _find_unit_columns(A, b):
    """이미 기저가 되어 있는 열을 찾는다 — 슬랙 열이 대개 여기 해당한다.

       인공변수를 필요한 행에만 붙이기 위한 준비다. 모든 행에 인공변수를
       붙여도 답은 같지만, 1단계가 실제 최적화를 대신 해 버려서 2단계에서 아무
       일도 일어나지 않는다 — 배울 것이 사라진다. 실무 구현도 이렇게 한다.
    """
    m, n = len(A), len(A[0])
    basis = [-1] * m
    used = set()
    for j in range(n):
        rows = [i for i in range(m) if abs(A[i][j]) > TOL]
        if len(rows) != 1:
            continue
        i = rows[0]
        if basis[i] >= 0 or j in used:
            continue
        if abs(A[i][j] - 1.0) < TOL and b[i] >= -TOL:
            basis[i] = j
            used.add(j)
    return basis


def _two_phase(A, b, c, rule='dantzig', maxiter=20000, trace=None):
    """실행가능 기저를 만든 뒤(필요하면 1단계) 2단계로 최적화한다.

       1단계: 기저가 없는 행에만 인공변수 aᵢ 를 붙이고 min Σaᵢ 를 푼다. 최적값이
              0 이면 원래 문제가 실행가능하고 그때의 기저가 출발점이 된다.
       왜 필요한가: 등식 제약이나 우변이 음수라 부호를 뒤집은 행에는 실행가능한
              기저 열이 없기 때문이다.
    """
    m, n = len(A), len(A[0])
    basis = _find_unit_columns(A, b)
    need = [i for i in range(m) if basis[i] < 0]
    k1 = 0

    if need:
        na = len(need)
        T = [[0.0] * (n + na + 1) for _ in range(m + 1)]
        for i in range(m):
            for j in range(n):
                T[i][j] = A[i][j]
            T[i][-1] = b[i]
        for t, i in enumerate(need):
            T[i][n + t] = 1.0
            basis[i] = n + t
        for j in range(n):                  # 1단계 목적행 = −Σ(인공변수 행)
            T[-1][j] = -math.fsum(T[i][j] for i in need)
        T[-1][-1] = -math.fsum(b[i] for i in need)
        st, k1 = _simplex(T, basis, range(n), rule, maxiter)
        if -T[-1][-1] > 1e-7:
            return 'infeasible', None, None, k1
        for i in range(m):                  # 기저에 남은 인공변수를 밀어낸다
            if basis[i] >= n:
                for j in range(n):
                    if abs(T[i][j]) > TOL:
                        _pivot(T, basis, i, j)
                        break
        T2 = [row[:n] + [row[-1]] for row in T[:m]]
    else:
        T2 = [[A[i][j] for j in range(n)] + [b[i]] for i in range(m)]

    # ── 2단계 ─────────────────────────────────────────────
    T2.append([c[j] for j in range(n)] + [0.0])
    for i in range(m):                      # 기저 변수의 축소비용을 0 으로 만든다
        j = basis[i]
        if j < n and abs(T2[-1][j]) > 0.0:
            f = T2[-1][j]
            for t in range(n + 1):
                T2[-1][t] -= f * T2[i][t]
    st2, k2 = _simplex(T2, basis, range(n), rule, maxiter, trace=trace)
    return st2, T2, basis, k1 + k2


def solve_lp(c, A_ub=None, b_ub=None, A_eq=None, b_eq=None,
             method='simplex', rule='dantzig', maxiter=20000, keep_history=False,
             return_tableau=False):
    """min cᵀx  s.t.  A_ub x ≤ b_ub,  A_eq x = b_eq,  x ≥ 0.

       return_tableau=True 이면 결과에 최종 타블로와 기저를 붙여 준다 —
       고모리 절단(7부 31장)이 그 타블로의 한 행에서 만들어지기 때문이다.
    """
    A, b, cc, n, m1 = _standard_form(c, A_ub, b_ub, A_eq, b_eq)
    if method == 'interior':
        return _interior_point(A, b, cc, n, m1, keep_history=keep_history)

    trace = [] if keep_history else None
    st, T, basis, nit = _two_phase(A, b, cc, rule=rule, maxiter=maxiter, trace=trace)
    if st == 'infeasible':
        return LPResult('infeasible', nit=nit, msg='1단계 최적값이 0 이 아니다',
                        history=trace)
    if st == 'unbounded':
        return LPResult('unbounded', nit=nit, msg='개선 방향이 유계가 아니다',
                        history=trace)
    ntot = len(A[0])
    z = [0.0] * ntot
    for i in range(len(basis)):
        if basis[i] < ntot:
            z[basis[i]] = T[i][-1]
    x = z[:n]
    obj = math.fsum(cc[j] * z[j] for j in range(ntot))
    dual = _dual_from_tableau(T, basis, cc, ntot, m1)
    res = LPResult('optimal', x=x, obj=obj, dual=dual, nit=nit, basis=list(basis),
                   history=trace)
    if return_tableau:
        res.tableau = T
        res.nvars = ntot
        res.nx = n
    return res


def _dual_from_tableau(T, basis, c, ntot, m1):
    """슬랙 열의 축소비용에서 쌍대변수를 읽는다.

       슬랙 sᵢ 의 축소비용은 c_sᵢ − c_Bᵀ B⁻¹ eᵢ = −πᵢ 다(c_sᵢ = 0).
       여기서는 y = −π ≥ 0 규약을 쓴다 — 그래야 obj = −bᵀy 가 되고
       yᵢ 가 "제약을 한 단위 조였을 때의 손해"라는 그림자 가격이 된다(정리 19.8).
    """
    n = ntot - m1
    out = []
    for i in range(m1):
        out.append(T[-1][n + i])
    return out


# ---------------------------------------------------------------- 내부점법

def _interior_point(A, b, c, n, m1, tol=1e-10, maxiter=200, sigma=0.1,
                    keep_history=False):
    """원-쌍대 내부점법 (infeasible start, 고정 중심화 계수).

       KKT 조건
           Ax = b,   Aᵀy + s = c,   x ≥ 0, s ≥ 0,   xᵢsᵢ = 0
       에서 마지막 상보여유를 xᵢsᵢ = σμ 로 완화하고 뉴턴법을 한 걸음 적용한다.
       μ = xᵀs/n 을 줄여 가면 해에 다가간다 — 5부 정리 22.4 의 중심 경로다.

       각 반복의 비용은 정규방정식 (A X S⁻¹ Aᵀ)Δy = r 한 번, 즉 O(m²n + m³).
       심플렉스와 달리 반복 수가 문제 크기에 거의 무관하다(대개 20~50회).
    """
    m, ntot = len(A), len(A[0])
    x = [1.0] * ntot
    s = [1.0] * ntot
    y = [0.0] * m
    hist = []
    for k in range(maxiter):
        rp = la.vsub(b, la.matvec(A, x))                       # 원문제 잔차
        rd = la.vsub(la.vsub(c, la.matvec(la.transpose(A), y)), s)   # 쌍대 잔차
        mu = math.fsum(x[i] * s[i] for i in range(ntot)) / ntot
        if keep_history:
            hist.append({'k': k, 'mu': mu, 'x': list(x[:n]),
                         'rp': la.norm(rp), 'rd': la.norm(rd)})
        if mu < tol and la.norm(rp) < tol and la.norm(rd) < tol:
            break
        # 정규방정식: (A D Aᵀ) Δy = rp + A D (rd − X⁻¹ rc),  D = X S⁻¹
        d = [x[i] / s[i] for i in range(ntot)]
        rc = [sigma * mu - x[i] * s[i] for i in range(ntot)]
        ADAt = la.zeros(m, m)
        for i in range(m):
            for j in range(i, m):
                v = math.fsum(A[i][t] * d[t] * A[j][t] for t in range(ntot))
                ADAt[i][j] = ADAt[j][i] = v
        for i in range(m):
            ADAt[i][i] += 1e-12                                # 수치 안정용 미세 정칙화
        w = [d[t] * rd[t] - rc[t] / s[t] for t in range(ntot)]
        rhs = la.vadd(rp, la.matvec(A, w))
        try:
            dy = la.solve(ADAt, rhs)
        except la.SingularMatrix:
            return LPResult('infeasible', nit=k, msg='정규방정식이 특이하다',
                            history=hist)
        ds = la.vsub(rd, la.matvec(la.transpose(A), dy))
        dx = [(rc[t] - x[t] * ds[t]) / s[t] for t in range(ntot)]
        ap = _max_step(x, dx)
        ad = _max_step(s, ds)
        a = 0.99 * min(ap, ad, 1.0)
        x = la.axpy(a, dx, x)
        s = la.axpy(a, ds, s)
        y = la.axpy(a, dy, y)
        if a < 1e-12:
            break
    obj = math.fsum(c[j] * x[j] for j in range(ntot))
    dual = [-v for v in y[:m1]]
    status = 'optimal' if mu < 1e-6 else 'maxiter'
    return LPResult(status, x=x[:n], obj=obj, dual=dual, nit=k, history=hist)


def _max_step(v, dv):
    """v + α·dv > 0 을 유지하는 최대 α."""
    a = INF
    for i in range(len(v)):
        if dv[i] < 0:
            a = min(a, -v[i] / dv[i])
    return a if a < INF else 1.0


# ---------------------------------------------------------------- 모형화 예제

def l1_regression(A, b):
    """min ‖Ax − b‖₁ 을 LP 로 푼다.

       |rᵢ| ≤ tᵢ 를 두 개의 선형 부등식으로 쪼개고 Σtᵢ 를 최소화한다.
       부호 제한 없는 x 는 x = u − v (u,v ≥ 0) 로 나눈다.
       변수 2n+m 개, 제약 2m 개짜리 LP 가 된다.

       왜 쓸모 있나: ℓ₁ 회귀는 이상치에 강하지만 미분 불가능하다. LP 로 바꾸면
       그 비평활성이 사라진다 — "문제를 다시 적어" 어려움을 없애는 전형적인 예다.
    """
    m, n = len(A), len(A[0])
    nv = 2 * n + m
    rows, rhs = [], []
    for i in range(m):
        r1 = [0.0] * nv
        r2 = [0.0] * nv
        for j in range(n):
            r1[j] = A[i][j]
            r1[n + j] = -A[i][j]
            r2[j] = -A[i][j]
            r2[n + j] = A[i][j]
        r1[2 * n + i] = -1.0
        r2[2 * n + i] = -1.0
        rows += [r1, r2]
        rhs += [b[i], -b[i]]
    c = [0.0] * (2 * n) + [1.0] * m
    r = solve_lp(c, A_ub=rows, b_ub=rhs)
    if r.status != 'optimal':
        raise ValueError('LP 가 풀리지 않았다: %s' % r.status)
    x = [r.x[j] - r.x[n + j] for j in range(n)]
    return x, r.obj
