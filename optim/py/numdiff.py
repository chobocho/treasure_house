# -*- coding: utf-8 -*-
"""수치미분 — 손으로 유도한 기울기를 기계가 채점하게 만드는 장치.

   최적화 코드에서 가장 자주 나오는 버그는 알고리즘이 아니라 '∇f 를 잘못 적은 것'이다.
   증상도 고약하다: 알고리즘은 멀쩡히 돌고, 그저 엉뚱한 점으로 수렴한다.
   그래서 이 교재의 모든 문제는 check_grad 를 통과한 것만 쓴다.

   이론적 배경(1부 3장에서 증명):
     전진차분  (f(x+h)−f(x))/h        = f′(x) + (h/2)f″ + O(h²)   → 절단오차 O(h)
     중심차분  (f(x+h)−f(x−h))/(2h)   = f′(x) + (h²/6)f‴ + O(h⁴)  → 절단오차 O(h²)
   여기에 반올림오차 O(ε/h) 가 더해지므로 최적 스텝은
     전진차분 h* ≈ √ε ≈ 1.5e-8,   중심차분 h* ≈ ε^(1/3) ≈ 6e-6.
"""
import math

EPS = 2.220446049250313e-16          # 배정밀도 기계 엡실론
H_FWD = math.sqrt(EPS)               # ≈ 1.49e-8
H_CEN = EPS ** (1.0 / 3.0)           # ≈ 6.06e-6


def _step(xi, h0):
    """상대 스텝. x=0 에서 h 가 0 이 되지 않도록 절대 하한을 함께 둔다."""
    return h0 * max(1.0, abs(xi))


def grad(f, x, h0=H_CEN):
    """중심차분 기울기. 함수를 2n 번 부른다 — O(n) 호출."""
    g = [0.0] * len(x)
    for i in range(len(x)):
        h = _step(x[i], h0)
        xp, xm = list(x), list(x)
        xp[i] += h
        xm[i] -= h
        h2 = xp[i] - xm[i]           # 실제로 표현된 간격을 쓴다(반올림 보정)
        g[i] = (f(xp) - f(xm)) / h2
    return g


def grad_forward(f, x, h0=H_FWD):
    """전진차분 기울기. 함수를 n+1 번만 부른다 — 값이 비싼 함수에서 쓸모 있다."""
    f0 = f(x)
    g = [0.0] * len(x)
    for i in range(len(x)):
        h = _step(x[i], h0)
        xp = list(x)
        xp[i] += h
        g[i] = (f(xp) - f0) / (xp[i] - x[i])
    return g


def grad_complex(f, x, h=1e-30):
    """복소 스텝 미분:  f′(x) ≈ Im f(x + ih) / h.

       테일러 전개  f(x+ih) = f(x) + ih f′(x) − h²f″/2 − ih³f‴/6 + …
       의 허수부를 h 로 나누면 f′(x) + O(h²) 이고, 뺄셈이 없어 상쇄가 일어나지 않는다.
       그래서 h 를 1e-30 까지 줄여 기계정밀도의 기울기를 얻는다.
       조건: f 가 복소수 인자를 그대로 받아 해석적으로 계산되어야 한다
             (math.exp 대신 cmath.exp, abs()·max() 금지).
    """
    g = [0.0] * len(x)
    for i in range(len(x)):
        xc = [complex(v, 0.0) for v in x]
        xc[i] = complex(x[i], h)
        g[i] = f(xc).imag / h
    return g


def hessian(f, x, h0=None):
    """중심 2차 차분 헤세 행렬. 함수 호출 O(n²) — n 이 크면 쓰지 말 것.

       대각:      (f(x+he) − 2f(x) + f(x−he)) / h²
       비대각:    (f(++) − f(+−) − f(−+) + f(−−)) / (4h²)
       비대각 식은 정의상 대칭이므로 결과도 대칭이 된다.
    """
    n = len(x)
    if h0 is None:
        h0 = EPS ** 0.25             # 2차 차분은 h⁴ 항까지 보므로 스텝을 더 크게
    f0 = f(x)
    h = [_step(x[i], h0) for i in range(n)]
    H = [[0.0] * n for _ in range(n)]
    for i in range(n):
        xp, xm = list(x), list(x)
        xp[i] += h[i]
        xm[i] -= h[i]
        H[i][i] = (f(xp) - 2.0 * f0 + f(xm)) / (h[i] * h[i])
        for j in range(i + 1, n):
            a, b, c, d = list(x), list(x), list(x), list(x)
            a[i] += h[i]; a[j] += h[j]
            b[i] += h[i]; b[j] -= h[j]
            c[i] -= h[i]; c[j] += h[j]
            d[i] -= h[i]; d[j] -= h[j]
            v = (f(a) - f(b) - f(c) + f(d)) / (4.0 * h[i] * h[j])
            H[i][j] = H[j][i] = v
    return H


def jacobian(F, x, h0=H_CEN):
    """벡터함수 F: ℝⁿ→ℝᵐ 의 야코비 행렬 J[i][j] = ∂Fᵢ/∂xⱼ."""
    n = len(x)
    cols = []
    for j in range(n):
        h = _step(x[j], h0)
        xp, xm = list(x), list(x)
        xp[j] += h
        xm[j] -= h
        h2 = xp[j] - xm[j]
        fp, fm = F(xp), F(xm)
        cols.append([(a - b) / h2 for a, b in zip(fp, fm)])
    m = len(cols[0]) if cols else 0
    return [[cols[j][i] for j in range(n)] for i in range(m)]


def _rel_err(a, b):
    """상대 오차 ‖a−b‖ / max(1, ‖a‖, ‖b‖) — 크기가 0 에 가까울 때도 무너지지 않는다."""
    num = math.sqrt(math.fsum((u - v) ** 2 for u, v in zip(a, b)))
    den = max(1.0,
              math.sqrt(math.fsum(u * u for u in a)),
              math.sqrt(math.fsum(v * v for v in b)))
    return num / den


def check_grad(f, gradf, x, h0=H_CEN):
    """해석적 기울기와 중심차분의 상대오차. 1e-6 이하면 통과로 본다."""
    return _rel_err(gradf(x), grad(f, x, h0))


def check_hess(gradf, hessf, x, h0=H_CEN):
    """헤세는 ∇f 의 야코비다 — 그 사실을 그대로 검사로 쓴다."""
    Ha = hessf(x)
    Hn = jacobian(gradf, x, h0)
    flat_a = [v for row in Ha for v in row]
    flat_n = [v for row in Hn for v in row]
    return _rel_err(flat_a, flat_n)
