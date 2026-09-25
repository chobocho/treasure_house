# -*- coding: utf-8 -*-
"""도해용 수치 — deck/gen_figs.py 는 data/ 와 out/ 만 읽는다 (PLAN §3.6).

그림에 쓰는 곡선을 여기서 시뮬레이터로 계산해 out/fig_*.tsv 로 남긴다.
그림이 코드와 어긋나면 run-check(해시)와 figs-check 가 같이 잡는다.
"""
import math

from droneshow import estimator as E
from droneshow import params, poly, profile, rng, sim
from droneshow import rigidbody as RB


def tsv(ctx, name, head, rows):
    ctx.save('fig_%s.tsv' % name, '\n'.join(
        ['\t'.join(head)] + ['\t'.join(r) for r in rows]) + '\n')


def step(ctx):
    """T14 — kp = 4, ζ 세 가지의 계단 응답 x(t), 0…6 s 를 20 ms 간격."""
    kp, dt = 4.0, 1e-3
    zetas = (0.2, 0.707, 1.0)
    cols = []
    for z in zetas:
        kd = 2 * z * math.sqrt(kp)
        f = lambda s, kd=kd: [s[1], kp * (1 - s[0]) - kd * s[1]]
        s, xs = [0.0, 0.0], [0.0]
        for k in range(1, 6001):
            s = RB.rk4(f, s, dt)
            if k % 20 == 0:
                xs.append(s[0])
        cols.append(xs)
    rows = [['%.2f' % (i * 0.02)] + ['%.5f' % c[i] for c in cols]
            for i in range(len(cols[0]))]
    tsv(ctx, 'step', ['t'] + ['zeta=%g' % z for z in zetas], rows)


def cascade(ctx):
    """9부 — 제자리 비행 중 x 목표를 1 m 옮긴 전체 모형의 x(t)·기울기."""
    p = params.load()
    ref = lambda t: {'p': [1.0, 0.0, 5.0]}
    r = sim.fly(p, ref, 5.0, start=[0, 0, 5], every=5)
    rows = [['0.00', '0.00000', '0.00000']]
    for row in r:
        s = row['s']
        w, x, y, z = s[6:10]
        # 기울기 = 몸 z 축과 세계 z 축의 사이각 (자세 사원수에서)
        cz = 1 - 2 * (x * x + y * y)
        rows.append(['%.2f' % row['t'], '%.5f' % s[0],
                     '%.5f' % math.degrees(math.acos(max(-1, min(1, cz))))])
    tsv(ctx, 'cascade', ['t', 'x', 'tilt_deg'], rows)


def comp(ctx):
    """T23 — 참 각 θ(t) = 0.3 sin t, 자이로 바이어스 0.05 rad/s·잡음,
    가속도계 각 잡음 0.08 rad. 자이로 적분·가속도계·상보 필터
    (α 0.98)."""
    g = rng.Rng(7)
    dt, alpha = 0.01, 0.98
    th_g = th_c = 0.0
    rows = []
    for k in range(1001):
        t = k * dt
        truth = 0.3 * math.sin(t)
        gyro = 0.3 * math.cos(t) + 0.05 + 0.02 * g.normal()
        acc = truth + 0.08 * g.normal()
        if k:
            th_g += gyro * dt
            th_c = E.complementary_1d(th_c, gyro, acc, alpha, dt)
        if k % 5 == 0:
            rows.append(['%.2f' % t, '%.5f' % truth, '%.5f' % th_g,
                         '%.5f' % acc, '%.5f' % th_c])
    tsv(ctx, 'comp', ['t', 'truth', 'gyro_int', 'acc', 'comp'], rows)


def snap(ctx):
    """10부 — 10 m 를 사다리꼴(v 4, a 2)과 같은 시간의 최소 스냅으로."""
    d = 10.0
    tr = profile.trapezoid(d, 4.0, 2.0)
    big_t = tr['T']
    c = poly.rest_to_rest(4)
    c1 = poly.deriv(c, 1)
    rows = []
    for i in range(101):
        t = big_t * i / 100
        x, v, _a = profile.sample(tr, t)
        u = t / big_t
        rows.append(['%.3f' % t, '%.5f' % x, '%.5f' % v,
                     '%.5f' % (d * poly.val(c, u)),
                     '%.5f' % (d / big_t * poly.val(c1, u) + 0.0)])
    tsv(ctx, 'snap', ['t', 'trap_x', 'trap_v', 'snap_x', 'snap_v'], rows)


def run(ctx):
    step(ctx)
    cascade(ctx)
    comp(ctx)
    snap(ctx)
