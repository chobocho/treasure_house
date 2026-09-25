# -*- coding: utf-8 -*-
"""profile — 속도·가속도 한계 안의 최단 시간 이동 (SPEC §7, T28).

가속 → 등속 → 감속(사다리꼴). 거리가 짧아 최고 속도에 닿기 전에
줄여야 하면 등속 구간이 사라진 삼각형이 된다.
"""
import math

from . import poly


def trapezoid(d, vmax, amax):
    """거리 d 를 멈춤→멈춤으로. {'T', 't_acc', 'v_peak',
    'triangular'}."""
    if d <= vmax * vmax / amax:
        vp = math.sqrt(d * amax)
        ta = vp / amax
        return {'d': d, 'a': amax, 'T': 2 * ta, 't_acc': ta,
                'v_peak': vp,
                'triangular': d < vmax * vmax / amax}
    ta = vmax / amax
    return {'d': d, 'a': amax, 'T': d / vmax + ta, 't_acc': ta,
            'v_peak': vmax, 'triangular': False}


def sample(pr, t):
    """시각 t 의 (이동 거리, 속도, 가속도)."""
    big_t, ta, vp, a = pr['T'], pr['t_acc'], pr['v_peak'], pr['a']
    t = min(max(t, 0.0), big_t)
    if t < ta:
        return 0.5 * a * t * t, a * t, a
    if t <= big_t - ta:
        return 0.5 * a * ta * ta + vp * (t - ta), vp, 0.0
    r = big_t - t
    return pr['d'] - 0.5 * a * r * r, a * r, -a


def beta_trap(u, r):
    """정규화한 사다리꼴 β(u), 가속 비율 r ∈ (0, ½], v̂ = 1/(1−r)."""
    vh = 1.0 / (1.0 - r)
    if u <= r:
        return vh * u * u / (2 * r)
    if u < 1 - r:
        return vh * (u - r / 2)
    return 1.0 - vh * (1 - u) ** 2 / (2 * r)


def beta_trap_limits(r):
    """(β' 의 최대, |β''| 의 최대)."""
    return 1.0 / (1.0 - r), 1.0 / (r * (1.0 - r))


def poly_limits(c, n=10000):
    """다항식 β 의 (max|β'|, max|β''|) — [0,1] 을 n 등분해 잰다."""
    d1, d2 = poly.deriv(c, 1), poly.deriv(c, 2)
    us = [k / n for k in range(n + 1)]
    return (max(abs(poly.val(d1, u)) for u in us),
            max(abs(poly.val(d2, u)) for u in us))


def feasible_time(d, vmax, amax, c):
    """β 로 거리 d 를 갈 때 한계를 지키는 가장 짧은 시간.

    x(t) = d·β(t/T) 이면 속도 최대 d·β'max/T, 가속도 최대
    d·β''max/T²."""
    d1, d2 = poly_limits(c)
    return max(d * d1 / vmax, math.sqrt(d * d2 / amax))
