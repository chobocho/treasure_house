# -*- coding: utf-8 -*-
"""mixer — 추력 넷 ↔ (총추력, 롤·피치·요 토크).

SPEC §4.1–4.2, 정리 T3·T9·T10.

로터 i 는 몸체 x 축에서 반시계로 45° + 90°(i−1) 자리에 있고, 회전
방향은 (+1, −1, +1, −1) 이다(+1 = 위에서 보아 반시계).
"""
from . import params as P
from . import vec3 as V

SPIN = (1, -1, 1, -1)


def matrix(p):
    """M: u = M·T. 네 행이 서로 수직이다 — 그래서 역행렬이 쉽다(T9)."""
    d = P.derived(p)
    a, c = d['a'], d['c']
    return [[1.0, 1.0, 1.0, 1.0],
            [a, a, -a, -a],
            [-a, a, a, -a],
            [-c, c, -c, c]]


def inverse(p):
    """M⁻¹ = Mᵀ · diag(1/4, 1/(4a²), 1/(4a²), 1/(4c²))."""
    m = matrix(p)
    d = [V.total(x * x for x in row) for row in m]  # 4, 4a², 4a², 4c²
    return [[m[j][i] / d[j] for j in range(4)] for i in range(4)]


def forward(p, t):
    """추력 넷 → [F, τx, τy, τz]."""
    return [V.total(r[k] * t[k] for k in range(4)) for r in matrix(p)]


def wrench_map(p):
    """추력 넷 → 힘 셋·토크 셋 (6×4).

    옆으로 미는 힘의 두 행은 0 이다(T10)."""
    m = matrix(p)
    return [[0.0] * 4, [0.0] * 4, list(m[0]), m[1], m[2], m[3]]


def _apply(mi, u):
    return [V.total(mi[i][k] * u[k] for k in range(4))
            for i in range(4)]


def _inside(t, lo, hi):
    return all(lo - 1e-12 <= x <= hi + 1e-12 for x in t)


def allocate(p, u, lo, hi):
    """u → 추력 넷, 한계 [lo, hi] 안으로.

    우선순위는 롤·피치 > 총추력 > 요.

    1) 그대로 풀어 한계 안이면 끝. 2) 요 토크를 가장 크게 남기는 배율
    k ∈ [0,1] 을 이분법으로(30번). 3) 그래도 넘치면 넷을 같은 δ 만큼
    옮긴다(총추력을 희생). 4) 마지막으로 하나씩 자른다.
    PX4·ArduPilot 이 문서에 적은 순서를 단순하게 옮긴 것이다(9부)."""
    mi = inverse(p)
    flags = []
    t = _apply(mi, u)
    if _inside(t, lo, hi):
        return t, flags
    if u[3] != 0.0:
        flags.append('yaw_scaled')
        base = _apply(mi, [u[0], u[1], u[2], 0.0])
        if _inside(base, lo, hi):
            k0, k1 = 0.0, 1.0
            for _ in range(30):
                k = 0.5 * (k0 + k1)
                if _inside(_apply(mi, [u[0], u[1], u[2], k * u[3]]),
                           lo, hi):
                    k0 = k
                else:
                    k1 = k
            return _apply(mi, [u[0], u[1], u[2], k0 * u[3]]), flags
        t = base
    flags.append('shifted')
    delta = lo - min(t) if min(t) < lo else hi - max(t)
    t = [x + delta for x in t]
    if not _inside(t, lo, hi):
        flags.append('clamped')
        t = [min(hi, max(lo, x)) for x in t]
    return t, flags
