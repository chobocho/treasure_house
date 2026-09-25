# -*- coding: utf-8 -*-
"""7부 — 수학 준비. 도구마다 수로 확인한 표와 예제 출력."""
import math

from droneshow import params, quadrotor as QR, rigidbody as RB, rng


def small_angle(ctx):
    """M14 — sin θ ≈ θ 의 오차가 θ³ 에 비례한다는 것을 표로."""
    rows = []
    for deg in (40, 20, 10, 5, 2.5):
        t = math.radians(deg)
        e = t - math.sin(t)
        rows.append(['%g' % deg, '%.5f' % t, '%.3e' % e,
                     '%.5f' % (e / t ** 3), '%.3e' % (math.tan(t) - t),
                     '%.3e' % (1 - math.cos(t))])
    head = ['각(도)', 'θ(rad)', 'θ − sin θ', '(θ − sin θ)/θ³',
            'tan θ − θ', '1 − cos θ']
    ctx.table('p07_small_angle', head, rows, num=(0, 1, 2, 3, 4, 5))


def lag(ctx):
    """M16 — 모터 1차 지연을 모델(RK4)로 적분한 값과 식."""
    p = params.load()
    oh = params.derived(p)['omega_hover']
    s = QR.hover_state(p, [0.0, 0.0, 10.0])
    cmd = [oh * 1.1] * 4
    rows, dt, k = [], 0.002, 0
    for mult in (1, 2, 3, 4, 5):
        while k < round(mult * p['tau_m'] / dt):
            s = QR.step(p, s, cmd, dt)
            k += 1
        got = (QR.motors(s)[0] - oh) / (0.1 * oh)
        want = 1 - math.exp(-mult)
        rows.append(['%dτ' % mult, '%.3f' % (mult * p['tau_m']),
                     '%.6f' % got, '%.6f' % want,
                     '%.1e' % abs(got - want)])
    head = ['시각', 't[s]', '모델(RK4)', '1 − e^(−t/τ)', '차']
    ctx.table('p07_lag', head, rows, num=(1, 2, 3, 4))


def order(ctx):
    """M22 — x' = −x 를 t = 1 까지.

    걸음을 반으로 줄이면 오차가 몇 배로 주는가."""
    rows, prev = [], None
    for dt in (0.2, 0.1, 0.05, 0.025):
        err = []
        for step in (RB.euler, RB.rk4):
            x = [1.0]
            for _ in range(round(1 / dt)):
                x = step(lambda s: [-s[0]], x, dt)
            err.append(abs(x[0] - math.exp(-1)))
        ratio = ['—', '—'] if prev is None else [
            '%.2f' % (prev[i] / err[i]) for i in range(2)]
        rows.append(['%g' % dt, '%.3e' % err[0], ratio[0],
                     '%.3e' % err[1], ratio[1]])
        prev = err
    head = ['dt', '오일러 오차', '비', 'RK4 오차', '비']
    ctx.table('p07_order', head, rows, num=(0, 1, 2, 3, 4))


def roots(ctx):
    """M18·M19 — s² + b s + c 의 근과 해의 모양."""
    rows = []
    for b, c in ((3.0, 2.0), (2.0, 1.0), (2.0, 5.0), (0.0, 4.0),
                 (-1.0, 4.0)):
        d = b * b - 4 * c
        if d > 0:
            q = math.sqrt(d)
            r = '%g, %g' % ((-b + q) / 2, (-b - q) / 2)
            kind = '두 실근'
        elif d == 0:
            r, kind = '%g (중근)' % (-b / 2), '중근'
        else:
            r = '%g ± %gi' % (-b / 2 + 0.0, math.sqrt(-d) / 2)
            kind = '복소 근'
        shape = ('줄어든다' if b > 0 else '진동이 그대로' if b == 0
                 else '커진다')
        rows.append(['%g' % b, '%g' % c, '%g' % d, r, kind, shape])
    ctx.table('p07_roots', ['b', 'c', 'b² − 4c', '근', '갈래', '해는'],
              rows, num=(0, 1, 2))


def normal(ctx):
    """M24 — 표준정규 난수의 표본 평균·분산 (씨앗 7)."""
    rows = []
    for n in (100, 1000, 10000, 100000):
        g = rng.Rng(7)
        xs = [g.normal() for _ in range(n)]
        m = sum(xs) / n
        v = sum((x - m) ** 2 for x in xs) / n
        rows.append(['{:,}'.format(n), '%.4f' % m, '%.4f' % v])
    ctx.table('p07_normal', ['표본 수', '평균', '분산'], rows,
              num=(0, 1, 2))


def run(ctx):
    ctx.py('p07_vectors', 'ex/vectors_demo.py')
    ctx.py('p07_matrix', 'ex/matrix_demo.py')
    ctx.py('p07_exercises', 'ex/exercises7.py')
    small_angle(ctx)
    lag(ctx)
    order(ctx)
    roots(ctx)
    normal(ctx)
