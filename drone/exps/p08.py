# -*- coding: utf-8 -*-
"""8부 — 강체와 쿼드로터 모델. 보존량·믹서·선형화·평탄성의 수."""
import math

from droneshow import attitude as A
from droneshow import mixer, params, sim
from droneshow import quadrotor as QR
from droneshow import quat as Q
from droneshow import rigidbody as RB
from droneshow import vec3 as V

J = [1.0, 2.0, 3.0]


def tumble(w0, secs, dt):
    """토크 없는 강체 — (에너지 상대 오차, |h| 상대 오차, 세계 h
    오차)."""
    s = [1.0, 0.0, 0.0, 0.0] + list(w0)
    e0 = RB.rot_energy(J, w0)
    h0 = RB.ang_momentum(J, w0)
    f = lambda x: RB.attitude_deriv(J, x, [0.0, 0.0, 0.0])
    worst = [0.0, 0.0, 0.0]
    for _ in range(round(secs / dt)):
        s = RB.rk4(f, s, dt)
        s[:4] = Q.normalize(s[:4])
        hb = RB.ang_momentum(J, s[4:])
        hw = Q.rotate(s[:4], hb)
        worst[0] = max(worst[0], abs(RB.rot_energy(J, s[4:]) - e0) / e0)
        worst[1] = max(worst[1], abs(V.norm(hb) - V.norm(h0))
                       / V.norm(h0))
        worst[2] = max(worst[2], V.dist(hw, h0))
    return worst, s


def conservation(ctx):
    rows = []
    for dt in (0.02, 0.01, 0.002):
        w, _s = tumble([0.3, 1.0, 0.2], 10.0, dt)
        rows.append(['%g' % dt, '%.2e' % w[0], '%.2e' % w[1],
                     '%.2e' % w[2]])
    head = ['dt[s]', '에너지 상대 오차', '|Jω| 상대 오차',
            '세계 h 벡터 오차']
    ctx.table('p08_tumble', head, rows, num=(0, 1, 2, 3))


def intermediate(ctx):
    rows = []
    for name, w0 in (('x (가장 작은 J)', [2.0, 1e-3, 1e-3]),
                     ('y (가운데 J)', [1e-3, 2.0, 1e-3]),
                     ('z (가장 큰 J)', [1e-3, 1e-3, 2.0])):
        s = [1.0, 0.0, 0.0, 0.0] + w0
        f = lambda x: RB.attitude_deriv(J, x, [0.0, 0.0, 0.0])
        axis = max(range(3), key=lambda k: abs(w0[k]))
        lo, hi = math.inf, 0.0
        for _ in range(10000):
            s = RB.rk4(f, s, 0.002)
            s[:4] = Q.normalize(s[:4])
            off = max(abs(s[4 + k]) for k in range(3) if k != axis)
            hi = max(hi, off)
            lo = min(lo, s[4 + axis])
        rows.append([name, '%.4f' % hi, '%.4f' % lo])
    ctx.table('p08_axes', ['처음 도는 축', '다른 축 각속도의 최대',
                           '그 축 각속도의 최소'], rows, num=(1, 2))


def mixing(ctx):
    p = params.load()
    m, mi = mixer.matrix(p), mixer.inverse(p)
    rows = [[n] + ['%.5f' % x for x in r]
            for n, r in zip(('F', 'τx', 'τy', 'τz'), m)]
    ctx.table('p08_mixer', ['M 의 행', 'T1', 'T2', 'T3', 'T4'], rows,
              num=(1, 2, 3, 4))
    rows = [[n] + ['%.4f' % x for x in r]
            for n, r in zip(('T1', 'T2', 'T3', 'T4'), mi)]
    ctx.table('p08_mixinv', ['M⁻¹ 의 행', 'F', 'τx', 'τy', 'τz'], rows,
              num=(1, 2, 3, 4))
    d = params.derived(p)
    out = []
    for u in ([4.905, 0.0, 0.0, 0.0], [4.905, 0.05, 0.0, 0.0],
              [4.905, 0.0, 0.0, 0.05], [4.905, 0.0, 0.0, 0.2],
              [19.0, 0.3, 0.0, 0.0], [0.5, 0.2, 0.0, 0.0]):
        t, flags = mixer.allocate(p, u, d['T_min'], d['T_max'])
        got = mixer.forward(p, t)
        out.append([' '.join('%g' % x for x in u),
                    ' '.join('%.3f' % x for x in t),
                    ' '.join('%.3f' % x for x in got),
                    ', '.join(flags) or '—'])
    ctx.table('p08_allocate', ['요구 u = (F, τx, τy, τz)',
                               '추력 T1..T4 [N]', '실제 u', '처리'],
              out)


def derived(ctx):
    ctx.py('p08_derived', '-c', 'import sys; sys.path.insert(0, "py")\n'
           'from droneshow import params\n'
           'for k, v in params.derived(params.load()).items():\n'
           '    print("%-12s %.6g" % (k, v))')


def openloop(ctx):
    """호버 회전수에서 모터 하나만 1 % 세게 — 제어가 없으면."""
    p = params.load()
    oh = params.derived(p)['omega_hover']
    s = QR.hover_state(p, [0.0, 0.0, 10.0])
    cmd = [oh * 1.01, oh, oh, oh]
    rows, k = [], 0
    for t in (0.5, 1.0, 1.5, 2.0):
        while k < round(t / 0.002):
            s = QR.step(p, s, cmd, 0.002)
            k += 1
        e = [math.degrees(a) for a in Q.to_euler(s[6:10])]
        rows.append(['%.1f' % t, '%.2f' % e[0], '%.2f' % e[1],
                     '%.3f' % s[0], '%.3f' % s[1],
                     '%.3f' % (s[2] - 10)])
    head = ['t[s]', '롤[°]', '피치[°]', 'x[m]', 'y[m]', 'Δz[m]']
    ctx.table('p08_openloop', head, rows, num=(0, 1, 2, 3, 4, 5))


def linearise(ctx):
    p = params.load()
    rows = []
    for deg in (20, 10, 5, 2.5):
        th = math.radians(deg)
        ex = QR.accel_tilted(p, 0.0, th)
        li = QR.accel_small_angle(p, 0.0, th)
        rows.append(['%g' % deg, '%.5f' % ex[0], '%.5f' % li[0],
                     '%.2e' % (abs(ex[0] - li[0]) / li[0]),
                     '%.5f' % ex[2]])
    ctx.table('p08_linear', ['피치[°]', 'ẍ 정확', 'ẍ ≈ gθ', '상대 오차',
                             'z̈ 정확'], rows, num=(0, 1, 2, 3, 4))


def flatness(ctx):
    rows = []
    for t in (0.0, 1.0, 2.5, 4.0):
        w, r = 0.8, 2.0
        c, s = math.cos(w * t), math.sin(w * t)
        a = [-r * w * w * c, -r * w * w * s, 0.0]
        j = [r * w ** 3 * s, -r * w ** 3 * c, 0.0]
        rates = A.flat_rates(a, j, 0.3 * t, 0.3, 9.81)
        h = 1e-5
        qs = []
        for tt in (t - h, t + h):
            cc, ss = math.cos(w * tt), math.sin(w * tt)
            aa = [-r * w * w * cc, -r * w * w * ss, 9.81]
            qs.append(A.desired_attitude(aa, 0.3 * tt))
        dq = Q.canonical(Q.mul(Q.conj(qs[0]), qs[1]))
        num = [x / h for x in dq[1:]]
        diff = max(abs(x - y) for x, y in zip(rates, num))
        rows.append(['%.1f' % t] + ['%.6f' % x for x in rates]
                    + ['%.1e' % diff])
    head = ['t[s]', 'p', 'q', 'r', '수치 미분과의 차']
    ctx.table('p08_flat', head, rows, num=(0, 1, 2, 3, 4))


def feedforward(ctx):
    p = params.load()
    rows = []
    for drag in (p['c_drag'], 0.0):
        for lv, name in enumerate(('없음', '+ 속도', '+ 가속도',
                                   '+ 가가속도→각속도')):
            def ref(t, lv=lv):
                w, r = 0.8, 2.0
                c, s = math.cos(w * t), math.sin(w * t)
                o = {'p': [r * c, r * s, 5.0], 'yaw': 0.0}
                if lv >= 1:
                    o['v'] = [-r * w * s, r * w * c, 0.0]
                if lv >= 2:
                    o['a'] = [-r * w * w * c, -r * w * w * s, 0.0]
                if lv >= 3:
                    o['j'] = [r * w ** 3 * s, -r * w ** 3 * c, 0.0]
                return o
            out = sim.fly(p, ref, 12.0, start=[2.0, 0.0, 5.0],
                          cfg={'c_drag': drag})
            err = max(V.dist(o['s'][0:3], ref(o['t'])['p'])
                      for o in out if o['t'] > 4.0)
            rows.append(['%g' % drag, name, '%.3f' % err])
    head = ['항력 c[N/(m/s)]', '앞먹임', '최대 오차[m]']
    ctx.table('p08_ff', head, rows, num=(0, 2))


def run(ctx):
    ctx.py('p08_exercises', 'ex/exercises8.py')
    conservation(ctx)
    intermediate(ctx)
    mixing(ctx)
    derived(ctx)
    openloop(ctx)
    linearise(ctx)
    flatness(ctx)
    feedforward(ctx)
