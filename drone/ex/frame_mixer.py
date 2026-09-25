# -*- coding: utf-8 -*-
"""프레임 기하 → 믹서 행렬, 그리고 로터 하나가 멈추면 (4부 1장).

로터 i 는 몸체 좌표 (x, y) 에 있고 s = +1(위에서 보아 반시계) 또는
−1(시계)로 돈다. 추력 T 하나가 몸체에 주는 것은 8부 믹서와 같다:
총추력 T, 롤 y·T, 피치 −x·T, 요 −s·c·T (c = kQ/kT, 정리 T3).
"""
import itertools
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'py'))
from droneshow import linalg, params  # noqa: E402

# 고리 모양 프레임: (로터 수, 첫 로터 각도[도], 도는 방향들).
# 각도는 몸체 x 축(앞)에서 반시계. quad_x 는 8부 mixer.py 의 배치.
RING = {'quad_x': (4, 45.0, (1, -1, 1, -1)),
        'quad_plus': (4, 0.0, (1, -1, 1, -1)),
        'hexa_x': (6, 30.0, (1, -1, 1, -1, 1, -1)),
        'hexa_x_ppnnpn': (6, 30.0, (1, 1, -1, -1, 1, -1)),
        'octo_x': (8, 22.5, (1, -1, 1, -1, 1, -1, 1, -1))}
NAMES = ('quad_x', 'quad_plus', 'quad_h', 'hexa_x', 'hexa_x_ppnnpn',
         'octo_x', 'x8', 'y6')


def rotors(name, L):
    """[(x, y, s), …]. H 는 옆으로 넓은 직사각형(0.6L × 0.8L) 예,
    X8·Y6 은 한 팔에 위아래로 반대로 도는 두 로터(동축)."""
    if name in RING:
        n, a0, spins = RING[name]
        out = []
        for k in range(n):
            a = math.radians(a0 + 360.0 * k / n)
            out.append((L * math.cos(a), L * math.sin(a), spins[k]))
        return out
    if name == 'quad_h':
        xy = ((0.6, 0.8), (-0.6, 0.8), (-0.6, -0.8), (0.6, -0.8))
        return [(L * x, L * y, s) for (x, y), s in zip(xy, (1, -1) * 2)]
    if name == 'x8':
        arms = rotors('quad_x', L)
    elif name == 'y6':
        arms = [(L * math.cos(math.radians(a)),
                 L * math.sin(math.radians(a)), 0)
                for a in (60.0, 180.0, 300.0)]
    else:
        raise KeyError(name)
    return [(x, y, s) for x, y, _ in arms for s in (1, -1)]


def matrix(rs, c):
    """4×n: 총추력·롤·피치·요 줄."""
    return [[1.0] * len(rs), [y for _x, y, _s in rs],
            [-x for x, _y, _s in rs], [-s * c for _x, _y, s in rs]]


def apply(m, t):
    return [math.fsum(r[k] * t[k] for k in range(len(t))) for r in m]


def equal_split(m, mg):
    """로터마다 mg/n 일 때의 (F, τx, τy, τz)."""
    n = len(m[0])
    return apply(m, [mg / n] * n)


def min_norm(m, u):
    """M t = u 의 해 가운데 |t| 가 가장 작은 것: t = Mᵀ(MMᵀ)⁻¹u.

    O(n) 곱셈으로 4×4 를 만들고 소거 한 번(linalg.solve)."""
    a = [[math.fsum(x * y for x, y in zip(ri, rj)) for rj in m]
         for ri in m]
    lam = linalg.solve(a, u)
    return [math.fsum(m[i][k] * lam[i] for i in range(4))
            for k in range(len(m[0]))]


def cost(m, axis):
    """축 하나에 토크 1 N·m 를 내려고 가장 바쁜 로터가 바꿔야 하는
    추력[N] (나머지 셋은 그대로 두는 최소 노름 해)."""
    u = [0.0] * 4
    u[axis] = 1.0
    return max(abs(x) for x in min_norm(m, u))


def null_vector(sub):
    """4×5 행렬(계수 4)의 M n = 0 인 n. 한 칸을 1 로 두고 나머지
    넷을 푼다 — 그 넷의 열이 특이하면 다른 칸을 1 로 둔다."""
    for free in range(4, -1, -1):
        cols = [k for k in range(5) if k != free]
        try:
            x = linalg.solve([[r[k] for k in cols] for r in sub],
                             [-r[free] for r in sub])
        except ValueError:
            continue
        x.insert(free, 1.0)
        return x
    raise ValueError('계수가 4 보다 작다')


def engine_out(m, drop, mg, full=False):
    """로터 drop 이 멈췄을 때 F = mg, 토크 0 을 지키면서 남은 로터의
    가장 작은 추력을 가장 크게 한 값(여유). 평형이 없으면 None.

    남은 로터가 5개면 해는 t0 + λ·n 한 줄이다. 여유 g(λ) =
    min_i(t0_i + λ n_i) 는 오목한 꺾은선이라 꼭짓점(두 직선의 교점)
    가운데 하나에서 가장 크다 — 교점 O(n²)개를 다 본다."""
    keep = [k for k in range(len(m[0])) if k != drop]
    sub = [[r[k] for k in keep] for r in m]
    if linalg.rank(sub) < 4 or len(keep) not in (4, 5):
        return None
    u = [mg, 0.0, 0.0, 0.0]
    t0 = min_norm(sub, u)
    if len(keep) == 4:
        lams, nv = [0.0], [0.0] * 4
    else:
        nv = null_vector(sub)
        lams = [(t0[j] - t0[i]) / (nv[i] - nv[j])
                for i, j in itertools.combinations(range(5), 2)
                if abs(nv[i] - nv[j]) > 1e-12]
    best = max(lams, key=lambda l: min(a + l * b
                                       for a, b in zip(t0, nv)))
    t = [a + best * b for a, b in zip(t0, nv)]
    g = min(t)
    if g < -1e-9:
        return None
    if not full:
        return g
    out = [0.0] * len(m[0])
    for k, x in zip(keep, t):
        out[k] = x
    return g, out
