# -*- coding: utf-8 -*-
"""9부 — 자세·위치 제어. 공식과 측정, 그리고 일부러 망가뜨린 제어."""
import math

from droneshow import attitude as A
from droneshow import params, pid, rng, sim
from droneshow import quat as Q
from droneshow import rigidbody as RB
from droneshow import vec3 as V


def p_first(ctx):
    """1차 계 x' = −x + u 를 P 로 닫으면 정상 오차 1/(1+k)."""
    rows = []
    for k in (1.0, 3.0, 10.0, 30.0):
        f = lambda s, k=k: [-s[0] + k * (1.0 - s[0])]
        s = [0.0]
        for _ in range(5000):
            s = RB.rk4(f, s, 0.002)
        rows.append(['%g' % k, '%.6f' % s[0], '%.6f' % (1 - s[0]),
                     '%.6f' % (1 / (1 + k)), '%.4f' % (1 / (1 + k))])
    ctx.table('p09_pfirst', ['k', '10초 뒤 x', '오차', '1/(1+k)',
                             '시상수 1/(1+k)[s]'], rows, num=(0, 1, 2, 3, 4))


def step2(kp, kd, secs=20.0, dt=1e-3):
    f = lambda s: [s[1], kp * (1 - s[0]) - kd * s[1]]
    s, top, t_top, settle = [0.0, 0.0], 0.0, 0.0, 0.0
    for k in range(round(secs / dt)):
        s = RB.rk4(f, s, dt)
        if s[0] > top:
            top, t_top = s[0], (k + 1) * dt
        if abs(s[0] - 1) > 0.02:
            settle = (k + 1) * dt
    return top, t_top, settle


def pd(ctx):
    """T14 — ζ 를 바꿔 가며 초과량과 정착 시간."""
    rows = []
    kp = 4.0
    for zeta in (0.2, 0.4, 0.6, 0.707, 0.8, 1.0):
        kd = 2 * zeta * math.sqrt(kp)
        top, t_top, settle = step2(kp, kd)
        over = max(0.0, top - 1)
        peak = '%.3f' % t_top if over > 1e-9 else '— (넘치지 않음)'
        rows.append(['%.3f' % zeta, '%.3f' % kd, '%.5f' % over,
                     '%.5f' % pid.overshoot(zeta), peak,
                     '%.2f' % settle])
    ctx.table('p09_pd', ['ζ', 'kd', '초과량(측정)', '초과량(공식)',
                         '최고점 시각[s]', '2% 정착[s]'], rows,
              num=(0, 1, 2, 3, 4, 5))


def integral(ctx):
    """T15 — 외란 d = −0.5 아래 PD 와 PID, 그리고 포화와 적분 누적."""
    rows = []
    for name, ki, umax, clamp in (('PD', 0.0, None, None),
                                  ('PID', 2.0, None, None),
                                  ('PID + 출력 포화', 2.0, 0.8, None),
                                  ('PID + 포화 + 적분 한계', 2.0, 0.8,
                                   0.3)):
        s, top = [0.0, 0.0], 0.0
        c = pid.PID(4.0, ki, 0.0, i_max=clamp or math.inf)
        dt = 1e-3
        for _ in range(40000):
            u = c.update(1.0, s[0], dt) - 3.0 * s[1]
            if umax is not None:
                u = max(-umax, min(umax, u))
            f = lambda x, u=u: [x[1], u - 0.5]
            s = RB.rk4(f, s, dt)
            top = max(top, s[0])
        rows.append([name, '%.5f' % s[0], '%.4f' % max(0.0, top - 1)])
    ctx.table('p09_integral', ['제어', '40초 뒤 x (목표 1)', '초과량'],
              rows, num=(1, 2))


def cascade_poles(ctx):
    """T17 — 안쪽 빠르기 b, 바깥 이득 k = 1: 느린 극과 −k 의 차."""
    rows = []
    for ratio in (4, 10, 30, 100):
        fast, slow = pid.cascade_poles(1.0, float(ratio))
        rows.append(['%d' % ratio, '%.4f' % fast, '%.5f' % slow,
                     '%.2f %%' % (100 * abs(slow + 1))])
    ctx.table('p09_poles', ['b/k', '빠른 극', '느린 극', '−k 와의 차'],
              rows, num=(0, 1, 2, 3))


def tilt(s):
    z = Q.rotate(s[6:10], [0.0, 0.0, 1.0])
    return math.degrees(math.acos(max(-1.0, min(1.0, z[2]))))


def hold(x, y, z, yaw=0.0):
    return lambda t: {'p': [x, y, z], 'yaw': yaw}


def timescale(ctx):
    """T17 — 대역폭(각속도 이득)을 낮추면 무너지고, 주기만 낮추면
    괜찮다."""
    p = params.load()
    rows = []
    for name, cfg in (('기준 (kp_rate 18, 250 Hz)', None),
                      ('주기만 50 Hz', {'rate_hz': 50, 'att_hz': 50}),
                      ('주기만 25 Hz', {'rate_hz': 25, 'att_hz': 25}),
                      ('kp_rate 6', {'kp_rate': 6.0, 'ki_rate': 0.0,
                                     'kd_rate': 0.0}),
                      ('kp_rate 3', {'kp_rate': 3.0, 'ki_rate': 0.0,
                                     'kd_rate': 0.0}),
                      ('kp_rate 2', {'kp_rate': 2.0, 'ki_rate': 0.0,
                                     'kd_rate': 0.0})):
        r = sim.fly(p, hold(1, 0, 5), 4.0, start=[0, 0, 5], cfg=cfg)
        rows.append([name, '%.1f' % max(tilt(o['s']) for o in r),
                     '%.3f' % max(o['s'][0] for o in r),
                     '%.3f' % r[-1]['s'][0]])
    ctx.table('p09_timescale', ['설정', '최대 기울기[°]', 'x 최댓값[m]',
                                '4초 뒤 x[m]'], rows, num=(1, 2, 3))


def attlaw(ctx):
    """T18 — 운동학 모델에서 오차각과 닫힌 해
    tan(θ/4)=tan(θ₀/4)e^(−kt)."""
    k, th0 = 3.0, 2.5
    qd = [1.0, 0.0, 0.0, 0.0]
    q = Q.from_axis_angle([0.3, -0.5, 0.8], th0)
    f = lambda x: Q.qdot(x, A.att_law(x, qd, [k, k, k], 1.0))
    rows, dt = [], 1e-3
    for n in range(1, 2001):
        q = Q.normalize(RB.rk4(f, q, dt))
        if n % 250 == 0:
            _ax, th = Q.to_axis_angle(Q.mul(Q.conj(q), qd))
            want = 4 * math.atan(math.tan(th0 / 4) * math.exp(-k * n * dt))
            rows.append(['%.2f' % (n * dt), '%.6f' % th, '%.6f' % want,
                         '%.1e' % abs(th - want)])
    ctx.table('p09_attlaw', ['t[s]', '오차각 θ', '닫힌 해', '차'], rows,
              num=(0, 1, 2, 3))


def yawweight(ctx):
    """T19 — 요 오차가 클 때 기울기 오차가 먼저 주는가."""
    qd = [1.0, 0.0, 0.0, 0.0]
    rows = []
    for w in (1.0, 0.4):
        q = Q.from_euler(0.5, 0.0, 2.5)
        f = lambda x, w=w: Q.qdot(x, A.att_law(x, qd, [3.0] * 3, w))
        out = []
        for n in range(1, 601):
            q = Q.normalize(RB.rk4(f, q, 1e-3))
            if n in (100, 300, 600):
                out.append(tilt([0] * 6 + q))
                out.append(math.degrees(abs(Q.to_euler(q)[2])))
        rows.append(['%.1f' % w] + ['%.2f' % x for x in out])
    ctx.table('p09_yawweight', ['yaw_w', '기울기 0.1s', '요 0.1s',
                                '기울기 0.3s', '요 0.3s', '기울기 0.6s',
                                '요 0.6s'], rows, num=(0, 1, 2, 3, 4, 5, 6))


def dnoise(ctx):
    """T22 — 잡음 섞인 측정의 D 출력: 필터 시상수마다의 흔들림."""
    def spread(tau, noise):
        g = rng.Rng(7)
        c = pid.PID(0.0, 0.0, 1.0, tau_d=tau)
        out = []
        for k in range(5000):
            t = k * 0.004
            y = math.sin(2 * math.pi * 0.5 * t) + noise * g.normal()
            out.append(c.update(0.0, y, 0.004))
        tail = out[500:]
        m = sum(tail) / len(tail)
        return math.sqrt(sum((x - m) ** 2 for x in tail) / len(tail))
    rows = []
    for tau in (0.0, 0.005, 0.02, 0.05):
        sig, tot = spread(tau, 0.0), spread(tau, 0.01)
        rows.append(['%g' % tau, '%.3f' % sig, '%.3f' % tot,
                     '%.3f' % math.sqrt(max(0.0, tot * tot - sig * sig))])
    ctx.table('p09_dnoise', ['τ_d[s]', '신호만', '신호+잡음',
                             '잡음의 몫'], rows, num=(0, 1, 2, 3))
    rows = []
    for w in (10.0, 50.0, 200.0, 1000.0):
        rows.append(['%g' % w, '%.4f' % pid.lowpass_gain(w, 0.005),
                     '%.2f' % (w * pid.lowpass_gain(w, 0.005))])
    ctx.table('p09_lowpass', ['ω[rad/s]', '1/√(1+(ωτ)²)', 'D×필터 이득'],
              rows, num=(0, 1, 2))


def flights(ctx):
    """캐스케이드 한 바퀴 — 1 m 계단, 요 90°, 바람, 큰 걸음."""
    p = params.load()
    r = sim.fly(p, hold(1, 0, 5), 6.0, start=[0, 0, 5])
    rows = [['%.1f' % o['t'], '%.4f' % o['s'][0], '%.4f' % o['s'][3],
             '%.2f' % tilt(o['s'])] for o in r if round(o['t'] * 50) % 25 == 0]
    ctx.table('p09_step', ['t[s]', 'x[m]', 'vx[m/s]', '기울기[°]'], rows,
              num=(0, 1, 2, 3))
    r = sim.fly(p, hold(0, 0, 5, math.pi / 2), 4.0, start=[0, 0, 5])
    rows = [['%.1f' % o['t'],
             '%.2f' % math.degrees(Q.to_euler(o['s'][6:10])[2]),
             '%.4f' % V.dist(o['s'][0:3], [0, 0, 5])]
            for o in r if round(o['t'] * 50) % 25 == 0]
    ctx.table('p09_yaw', ['t[s]', '요[°]', '제자리에서 벗어난 거리[m]'],
              rows, num=(0, 1, 2))
    rows = []
    for name, cfg in (('I 있음', None), ('I 없음', {'ki_vel': 0.0})):
        r = sim.fly(p, hold(0, 0, 5), 20.0, start=[0, 0, 5],
                    wind=lambda t: [0.3, 0.0, 0.0], cfg=cfg)
        rows.append([name] + ['%.4f' % r[k]['s'][0]
                              for k in (99, 249, 499, 999)])
    ctx.table('p09_wind', ['속도 루프', 'x@2s', 'x@5s', 'x@10s', 'x@20s'],
              rows, num=(1, 2, 3, 4))
    r = sim.fly(p, hold(10, 0, 5), 8.0, start=[0, 0, 5])
    rows = [['%.1f' % o['t'], '%.3f' % o['s'][0], '%.3f' % o['s'][3],
             '%.2f' % tilt(o['s'])] for o in r if round(o['t'] * 50) % 50 == 0]
    ctx.table('p09_bigstep', ['t[s]', 'x[m]', 'vx[m/s]', '기울기[°]'], rows,
              num=(0, 1, 2, 3))


def run(ctx):
    ctx.py('p09_exercises', 'ex/exercises9.py')
    ctx.py('p09_routh', 'ex/routh.py')
    p_first(ctx)
    pd(ctx)
    integral(ctx)
    cascade_poles(ctx)
    timescale(ctx)
    attlaw(ctx)
    yawweight(ctx)
    dnoise(ctx)
    flights(ctx)
