# -*- coding: utf-8 -*-
"""poly — 다항식 궤적: 최소 저크·최소 스냅 (SPEC §7, T27).

다항식은 오름차순 계수 리스트다: [c0, c1, c2, …] = c0 + c1 t + ….
스냅(위치의 4계 도함수)의 제곱을 적분한 값을 가장 작게 하는 곡선은
오일러-라그랑주 식 x⁽⁸⁾ = 0 을 만족한다 — 곧 7차 다항식이다(T27).
"""
import math

from . import linalg
from . import vec3 as V


def val(c, t):
    """호너 법으로 c(t). O(차수)."""
    s = 0.0
    for a in reversed(c):
        s = s * t + a
    return s


def deriv(c, k=1):
    """k 계 도함수의 계수. 차수보다 많이 미분하면 [0.0]."""
    for _ in range(k):
        c = [i * c[i] for i in range(1, len(c))] or [0.0]
    return [float(x) for x in c]


def add(a, b):
    n = max(len(a), len(b))
    a = list(a) + [0.0] * (n - len(a))
    b = list(b) + [0.0] * (n - len(b))
    return [a[i] + b[i] for i in range(n)]


def mul(a, b):
    out = [0.0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i + j] += x * y
    return out


def int_prod(a, b, big_t):
    """∫₀ᵀ a(t)·b(t) dt — 곱을 전개해 항마다 적분한다(정확)."""
    c = mul(a, b)
    return V.total(x * big_t ** (i + 1) / (i + 1)
                   for i, x in enumerate(c))


def snap_cost(c, big_t):
    """J = ∫₀ᵀ (x⁗)² dt."""
    d4 = deriv(c, 4)
    return int_prod(d4, d4, big_t)


def bump_poly(big_t, cubic):
    """(t(T−t))⁴ · (3차식) — 양 끝에서 값과 1~3계 도함수가 0 인 섭동."""
    base = [0.0, big_t, -1.0]                 # t(T − t)
    b4 = mul(mul(base, base), mul(base, base))
    return mul(b4, list(cubic))


def _row(deg, t, d):
    """d 계 도함수를 t 에서 잰 값의, 계수에 대한 행 (계수 0..deg)."""
    row = []
    for i in range(deg + 1):
        if i < d:
            row.append(0.0)
        else:
            row.append(math.factorial(i) / math.factorial(i - d)
                       * t ** (i - d))
    return row


def rest_to_rest(n):
    """β(0)=0, β(1)=1, 1..n−1 계 도함수가 양 끝에서 0 인 2n−1 차식.

    n = 3 이 최소 저크(5차), n = 4 가 최소 스냅(7차). 식을 외우지 않고
    2n 개의 조건을 연립해 푼다 — 그 연립이 곧 증명의 마지막 단계다."""
    deg = 2 * n - 1
    rows, rhs = [], []
    for d in range(n):
        rows.append(_row(deg, 0.0, d))
        rhs.append(0.0)
        rows.append(_row(deg, 1.0, d))
        rhs.append(1.0 if d == 0 else 0.0)
    return linalg.solve(rows, rhs)


def min_snap(wp, times):
    """한 축의 경유점 N+1 개, 구간 시간 N 개 → 구간마다 7차식 N 개.

    미지수 8N. 조건: 처음·끝의 위치와 1~3계 도함수 0 (8개), 가운데
    경유점마다 양쪽 위치(2개)와 1~6계 도함수 연속(6개). 합 8N 개라
    정사각 연립방정식 하나로 풀린다. O((8N)³)."""
    n = len(times)
    size = 8 * n
    rows, rhs = [], []

    def put(seg, r):
        full = [0.0] * size
        full[8 * seg:8 * seg + 8] = r
        return full

    for d in range(4):
        rows.append(put(0, _row(7, 0.0, d)))
        rhs.append(wp[0] if d == 0 else 0.0)
        rows.append(put(n - 1, _row(7, times[-1], d)))
        rhs.append(wp[-1] if d == 0 else 0.0)
    for k in range(1, n):
        rows.append(put(k - 1, _row(7, times[k - 1], 0)))
        rhs.append(wp[k])
        rows.append(put(k, _row(7, 0.0, 0)))
        rhs.append(wp[k])
        for d in range(1, 7):
            a = put(k - 1, _row(7, times[k - 1], d))
            b = put(k, _row(7, 0.0, d))
            rows.append([x - y for x, y in zip(a, b)])
            rhs.append(0.0)
    x = linalg.solve(rows, rhs)
    return [x[8 * k:8 * k + 8] for k in range(n)]
