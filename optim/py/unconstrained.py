# -*- coding: utf-8 -*-
"""무제약 최적화 — 경사하강부터 신뢰영역까지.

   모든 방법이 같은 골격을 공유한다:
       방향 d_k 를 정한다 → 보폭 α_k 를 정한다 → x ← x + α d
   달라지는 것은 오직 '방향을 어떻게 정하는가'와 '보폭을 어떻게 정하는가' 뿐이다.
   그래서 이 파일은 방향 결정부와 보폭 결정부를 분리해 두었다. 새 방법을 붙이려면
   방향 함수 하나만 쓰면 된다.

   기록(history)을 남기는 이유: 수렴 '속도'는 마지막 값이 아니라 궤적에서만 보인다.
   덱의 표들은 전부 이 기록에서 나온다.
"""
import math

from py import linalg as la


class Result(object):
    """최적화 한 번의 결과와 그 과정."""

    def __init__(self, x, fx, gnorm, nit, nfev, ngev, converged, msg, history):
        self.x = x
        self.fx = fx
        self.gnorm = gnorm
        self.nit = nit
        self.nfev = nfev
        self.ngev = ngev
        self.converged = converged
        self.msg = msg
        self.history = history

    def __repr__(self):
        return ('<Result %s nit=%d f=%.6g ‖g‖=%.3g>'
                % ('수렴' if self.converged else '미수렴', self.nit, self.fx, self.gnorm))


class _Counter(object):
    """함수·기울기 호출 횟수를 센다 — 반복 수보다 이쪽이 공정한 비교 기준이다."""

    def __init__(self, problem):
        self.p = problem
        self.nfev = 0
        self.ngev = 0

    def f(self, x):
        self.nfev += 1
        return self.p.f(x)

    def g(self, x):
        self.ngev += 1
        return self.p.grad(x)


# ---------------------------------------------------------------- 라인서치

def backtracking(f, x, fx, g, d, alpha0=1.0, c1=1e-4, rho=0.5, maxiter=60):
    """Armijo 조건을 만족할 때까지 보폭을 반으로 줄인다.

       Armijo:  f(x + αd) ≤ f(x) + c₁ α ∇f(x)ᵀd
       읽는 법: "적어도 예상 감소량의 c₁ 배만큼은 실제로 줄어야 한다."
       c₁ 을 아주 작게(1e-4) 잡는 이유는, 이 조건은 '너무 큰 보폭'만 걸러 내는
       역할이고 '충분히 큰 보폭'은 α 를 1 에서 시작해 줄이는 방식이 담당하기 때문이다.

       O(maxiter) 회의 함수 호출. 반환: (α, 호출 횟수)
    """
    gtd = la.dot(g, d)
    if gtd >= 0:
        raise ValueError('하강 방향이 아니다: ∇fᵀd = %g ≥ 0' % gtd)
    a = alpha0
    for i in range(maxiter):
        if f(la.axpy(a, d, x)) <= fx + c1 * a * gtd:
            return a, i + 1
        a *= rho
    return a, maxiter


def wolfe(f, grad, x, fx, g, d, c1=1e-4, c2=0.9, alpha0=1.0, amax=1e10, maxiter=40):
    """강 Wolfe 조건을 만족하는 보폭을 찾는다 (Nocedal–Wright 3.5–3.6 의 구조).

       Armijo:      f(x+αd) ≤ f(x) + c₁ α φ′(0)
       강 곡률조건:  |φ′(α)| ≤ c₂ |φ′(0)|

       왜 곡률조건이 필요한가: Armijo 만으로는 α 가 0 에 한없이 가까워도 통과한다.
       그러면 한 걸음이 무의미해진다. 곡률조건은 "기울기가 충분히 평평해질 때까지
       나아가라"는 요구이고, BFGS 의 sᵀy > 0 (양의 정부호 유지)을 보장하는 근거다.
    """
    phi0, dphi0 = fx, la.dot(g, d)
    if dphi0 >= 0:
        raise ValueError('하강 방향이 아니다: ∇fᵀd = %g ≥ 0' % dphi0)

    def phi(a):
        return f(la.axpy(a, d, x))

    def dphi(a):
        return la.dot(grad(la.axpy(a, d, x)), d)

    def zoom(lo, hi, philo):
        for _ in range(maxiter):
            a = 0.5 * (lo + hi)                    # 이분 — 보간보다 느리지만 견고하다
            pa = phi(a)
            if pa > phi0 + c1 * a * dphi0 or pa >= philo:
                hi = a
            else:
                da = dphi(a)
                if abs(da) <= -c2 * dphi0:
                    return a
                if da * (hi - lo) >= 0:
                    hi = lo
                lo, philo = a, pa
            if abs(hi - lo) < 1e-16:
                break
        return 0.5 * (lo + hi)

    a_prev, phi_prev, a = 0.0, phi0, alpha0
    for i in range(1, maxiter + 1):
        pa = phi(a)
        if pa > phi0 + c1 * a * dphi0 or (i > 1 and pa >= phi_prev):
            return zoom(a_prev, a, phi_prev), i
        da = dphi(a)
        if abs(da) <= -c2 * dphi0:
            return a, i
        if da >= 0:
            return zoom(a, a_prev, pa), i
        a_prev, phi_prev = a, pa
        a = min(2.0 * a, amax)
    return a, maxiter


# ---------------------------------------------------------------- 켤레기울기 (선형)

def cg_solve(A, b, x0=None, tol=1e-10, maxiter=None):
    """Ax = b (A ≻ 0) 를 켤레기울기로 푼다.

       정확 산술이라면 n 번 안에 정확한 해를 준다 — 매 반복이 새로운 켤레방향으로
       그 방향의 최적을 완전히 소진하기 때문이다(3부에서 증명).
       행렬을 분해하지 않고 곱셈만 쓰므로, A 가 크고 희소할 때 유일한 선택지다.

       O(maxiter · nnz(A)) 시간, O(n) 추가 공간.
    """
    n = len(b)
    maxiter = n if maxiter is None else maxiter
    x = [0.0] * n if x0 is None else list(x0)
    r = la.vsub(b, la.matvec(A, x))
    p = list(r)
    rs = la.dot(r, r)
    b_norm = max(1e-300, la.norm(b))
    for k in range(maxiter):
        if math.sqrt(rs) / b_norm <= tol:
            return x, k
        Ap = la.matvec(A, p)
        pAp = la.dot(p, Ap)
        if pAp <= 0:
            return x, k                    # A 가 양의 정부호가 아니다 — 여기서 멈춘다
        alpha = rs / pAp
        x = la.axpy(alpha, p, x)
        r = la.axpy(-alpha, Ap, r)
        rs_new = la.dot(r, r)
        p = la.axpy(rs_new / rs, p, r)
        rs = rs_new
    return x, maxiter


# ---------------------------------------------------------------- 방향 계산기

def _gd_dir(g):
    """경사하강의 방향 — 정리 3.4 가 말하는 '가장 가파른 하강 방향'.

       단위벡터로 정규화하지 않는다는 점에 주의. 크기까지 그대로 쓰면 기울기가
       작은 곳에서 자동으로 보폭이 줄어드는 효과가 생긴다. 이것이 고정 보폭
       경사하강이 최소점 근처에서 얌전해지는 이유다.
    """
    return [-v for v in g]


def _modified_newton_dir(H, g, base=1e-8):
    """뉴턴 방향 −H⁻¹g. H 가 양의 정부호가 아니면 τI 를 더해 고친다.

       왜 고쳐야 하는가: H 가 부정부호면 −H⁻¹g 가 <b>오르막</b>일 수 있다.
       그러면 라인서치가 실패하고 알고리즘이 멈춘다. τ 를 키우면 방향이 점점
       −g (경사하강) 쪽으로 돌아가므로, 최악의 경우에도 하강은 보장된다.
    """
    n = len(g)
    tau = 0.0
    diag = max(abs(H[i][i]) for i in range(n)) if n else 1.0
    for _ in range(60):
        M = [row[:] for row in H]
        for i in range(n):
            M[i][i] += tau
        try:
            L = la.cholesky(M)
            d = [-v for v in la.chol_solve(L, g)]
            if la.dot(g, d) < 0:
                return d, tau
        except la.NotPositiveDefinite:
            pass
        tau = base if tau == 0.0 else tau * 10.0
        if tau < 1e-12:
            tau = max(1e-8, 1e-3 * diag)
    return [-v for v in g], tau            # 끝내 실패하면 경사하강으로 물러선다


def _bfgs_update(H, s, y):
    """역헤세 근사의 BFGS 갱신 (제자리 수정).

       H ← (I − ρ s yᵀ) H (I − ρ y sᵀ) + ρ s sᵀ,   ρ = 1/sᵀy

       곱을 전개해 랭크-2 보정으로 정리하면 아래 한 줄이 된다. 행렬 세 개를
       곱하지 않으므로 O(n²) 에 끝난다 — 전개하지 않으면 O(n³) 이 된다.
       호출 전에 sᵀy > 0 을 확인해야 한다(정리 12.5).
    """
    n = len(s)
    r = 1.0 / la.dot(s, y)
    Hy = la.matvec(H, y)
    yHy = la.dot(y, Hy)
    for i in range(n):
        for j in range(n):
            H[i][j] += (r * r * (1.0 / r + yHy) * s[i] * s[j]
                        - r * (Hy[i] * s[j] + s[i] * Hy[j]))
    return H


def _lbfgs_dir(g, S, Y, rho):
    """L-BFGS 두 루프 재귀 — 행렬을 만들지 않고 H_k∇f 를 계산한다.

       메모리 m 개의 (s, y) 쌍만으로 O(mn) 시간에 방향을 얻는다. n 이 10⁶ 이어도
       n×n 행렬(10¹² 개)을 만들 필요가 없다는 것이 이 방법의 존재 이유다.
    """
    q = list(g)
    m = len(S)
    alpha = [0.0] * m
    for i in range(m - 1, -1, -1):
        alpha[i] = rho[i] * la.dot(S[i], q)
        q = la.axpy(-alpha[i], Y[i], q)
    if m:
        gamma = la.dot(S[-1], Y[-1]) / la.dot(Y[-1], Y[-1])
        q = la.vscale(gamma, q)
    for i in range(m):
        beta = rho[i] * la.dot(Y[i], q)
        q = la.axpy(alpha[i] - beta, S[i], q)
    return [-v for v in q]


def _steihaug(g, Hv, delta, tol=1e-10, maxiter=200):
    """신뢰영역 부분문제를 Steihaug–CG 로 근사한다.

       min mᵢ(p) = gᵀp + ½pᵀHp   s.t. ‖p‖ ≤ Δ
       CG 를 돌리다가 (a) 경계에 닿거나 (b) 음의 곡률을 만나면 경계까지 나아가고 멈춘다.
       음의 곡률을 '문제'가 아니라 '기회'로 쓴다는 것이 이 방법의 요령이다.
    """
    n = len(g)
    z = [0.0] * n
    r = list(g)
    d = [-v for v in g]
    gn = la.norm(g)
    if gn < tol:
        return z
    for _ in range(maxiter):
        Hd = Hv(d)
        dHd = la.dot(d, Hd)
        if dHd <= 0:                              # 음의 곡률 — 경계까지 간다
            return _to_boundary(z, d, delta)
        alpha = la.dot(r, r) / dHd
        z_next = la.axpy(alpha, d, z)
        if la.norm(z_next) >= delta:
            return _to_boundary(z, d, delta)
        r_next = la.axpy(alpha, Hd, r)
        if la.norm(r_next) < tol * gn:
            return z_next
        beta = la.dot(r_next, r_next) / la.dot(r, r)
        d = la.axpy(beta, d, [-v for v in r_next])
        z, r = z_next, r_next
    return z


def _to_boundary(z, d, delta):
    """z + τd 가 반지름 Δ 의 구면에 닿는 τ > 0 을 구한다 (이차방정식의 양근)."""
    a = la.dot(d, d)
    b = 2.0 * la.dot(z, d)
    c = la.dot(z, z) - delta * delta
    disc = max(0.0, b * b - 4 * a * c)
    tau = (-b + math.sqrt(disc)) / (2 * a) if a > 0 else 0.0
    return la.axpy(tau, d, z)


# ---------------------------------------------------------------- 주 드라이버

def minimize(problem, x0, method='bfgs', step=None, line_search=None,
             tol=1e-8, maxiter=1000, memory=10, keep_history=False,
             delta0=1.0, delta_max=1e3, cg_restart=None):
    """무제약 최소화. method 로 방향 결정 방식을 고른다.

       method: 'gd' 경사하강 · 'newton' 수정 뉴턴 · 'bfgs' · 'lbfgs' ·
               'cg' 비선형 켤레기울기(Polak–Ribière+) · 'tr' 신뢰영역
       line_search: None(방법별 기본) · 'armijo' · 'wolfe' · 'fixed'
       step: 'fixed' 일 때의 보폭. 경사하강의 기본값은 라인서치.
    """
    cnt = _Counter(problem)
    x = [float(v) for v in x0]
    n = len(x)
    fx = cnt.f(x)
    g = cnt.g(x)
    gnorm = la.norm(g)
    history = []
    B = la.identity(n)                  # BFGS 의 역헤세 근사 H
    S, Y, rho = [], [], []              # L-BFGS 메모리
    d_prev, g_prev = None, None
    delta = delta0
    converged = gnorm <= tol
    msg = '초기점이 이미 정류점' if converged else ''
    cg_restart = cg_restart or max(2, n)

    if line_search is None:
        line_search = 'fixed' if (method == 'gd' and step is not None) else (
            'armijo' if method in ('gd', 'newton') else 'wolfe')

    k = 0
    while k < maxiter and not converged:
        # ── 방향 ──────────────────────────────────────────────
        tau = 0.0
        if method == 'gd':
            d = _gd_dir(g)
        elif method == 'newton':
            d, tau = _modified_newton_dir(problem.hess(x), g)
        elif method == 'bfgs':
            d = [-v for v in la.matvec(B, g)]
            if la.dot(g, d) >= 0:                     # 수치 오차로 무너지면 초기화
                B = la.identity(n)
                d = _gd_dir(g)
        elif method == 'lbfgs':
            d = _lbfgs_dir(g, S, Y, rho)
            if la.dot(g, d) >= 0:
                S, Y, rho = [], [], []
                d = _gd_dir(g)
        elif method == 'cg':
            if d_prev is None or k % cg_restart == 0:
                d = _gd_dir(g)
            else:
                yk = la.vsub(g, g_prev)
                beta = max(0.0, la.dot(g, yk) / max(1e-300, la.dot(g_prev, g_prev)))
                d = la.axpy(beta, d_prev, _gd_dir(g))
                if la.dot(g, d) >= 0:                 # 하강이 아니면 재시작
                    d = _gd_dir(g)
        elif method == 'tr':
            d = None
        else:
            raise ValueError('모르는 방법: %s' % method)

        if keep_history:
            history.append({'k': k, 'x': list(x), 'f': fx, 'gnorm': gnorm,
                            'gtd': (la.dot(g, d) if d is not None else 0.0),
                            'alpha': None, 'tau': tau, 'delta': delta})

        # ── 신뢰영역은 보폭 개념이 다르다 ───────────────────────
        if method == 'tr':
            H = problem.hess(x)
            p = _steihaug(g, lambda v: la.matvec(H, v), delta)
            pred = -(la.dot(g, p) + 0.5 * la.dot(p, la.matvec(H, p)))
            f_new = cnt.f(la.vadd(x, p))
            ared = fx - f_new
            ratio = ared / pred if pred > 1e-300 else -1.0
            if ratio < 0.25:
                delta *= 0.25
            elif ratio > 0.75 and abs(la.norm(p) - delta) < 1e-10 * max(1.0, delta):
                delta = min(2.0 * delta, delta_max)
            if ratio > 0.1:                           # 받아들인다
                x = la.vadd(x, p)
                fx = f_new
                g = cnt.g(x)
                gnorm = la.norm(g)
            if keep_history:
                history[-1]['alpha'] = ratio
            k += 1
            if gnorm <= tol:
                converged, msg = True, '기울기 노름이 허용오차 이하'
            if delta < 1e-14:
                msg = '신뢰영역이 너무 작아졌다'
                break
            continue

        # ── 보폭 ──────────────────────────────────────────────
        try:
            if line_search == 'fixed':
                a = step
            elif line_search == 'armijo':
                a, _ = backtracking(cnt.f, x, fx, g, d,
                                    alpha0=(1.0 if method != 'gd' else 1.0))
            else:
                a, _ = wolfe(cnt.f, cnt.g, x, fx, g, d, c2=(0.1 if method == 'cg' else 0.9))
                if a <= 0.0:
                    # zoom 이 0 으로 수축했다 — 최소점 근처에서 f 의 차이가 반올림에
                    # 묻히면 실제로 일어난다. Armijo 로 한 번 더 시도해 본다.
                    a, _ = backtracking(cnt.f, x, fx, g, d)
        except ValueError:
            msg = '하강 방향을 만들지 못했다'
            break

        x_new = la.axpy(a, d, x)
        f_new = cnt.f(x_new)
        g_new = cnt.g(x_new)

        # ── 준뉴턴 갱신 ────────────────────────────────────────
        s = la.vsub(x_new, x)
        y = la.vsub(g_new, g)
        sy = la.dot(s, y)
        if method == 'bfgs' and sy > 1e-12 * max(1.0, la.norm(s) * la.norm(y)):
            _bfgs_update(B, s, y)
        elif method == 'lbfgs' and sy > 1e-12 * max(1.0, la.norm(s) * la.norm(y)):
            S.append(s); Y.append(y); rho.append(1.0 / sy)
            if len(S) > memory:
                S.pop(0); Y.pop(0); rho.pop(0)

        if keep_history:
            history[-1]['alpha'] = a
        d_prev, g_prev = d, g
        x, fx, g = x_new, f_new, g_new
        gnorm = la.norm(g)
        k += 1

        if gnorm <= tol:
            converged, msg = True, '기울기 노름이 허용오차 이하'
        elif not all(math.isfinite(v) for v in x) or not math.isfinite(fx):
            msg = '발산했다'
            break
        elif la.norm(s) < 1e-18 and line_search != 'fixed':
            msg = '더 이상 움직이지 않는다'
            break

    if keep_history:
        history.append({'k': k, 'x': list(x), 'f': fx, 'gnorm': gnorm,
                        'gtd': 0.0, 'alpha': None, 'tau': 0.0, 'delta': delta})
    if not converged and not msg:
        msg = '최대 반복 도달'
    return Result(x, fx, gnorm, k, cnt.nfev, cnt.ngev, converged, msg, history)
