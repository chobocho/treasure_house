# -*- coding: utf-8 -*-
"""5부 — 센서와 상태 추정. 센서 모델·자세 표현·상보/칼만 필터의 수.

잡음 크기는 data/params.tsv 의 sigma_* (이 덱의 가정)이고, 표에
'가정' 이라고 적힌 값(자기장 모양, 간섭 계수, 위성 배치)은 모델의
입력이지 실제 제품의 측정값이 아니다. 씨앗은 모두 고정한다.
"""
import math
import os
import sys

from droneshow import estimator as E
from droneshow import linalg, params, rng
from droneshow import quadrotor as QR
from droneshow import quat as Q
from droneshow import sensors as S
from droneshow import vec3 as V

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'ex'))
import gps_trilateration as GT  # noqa: E402
import imu_calib as C  # noqa: E402
import toy_imu as TI  # noqa: E402

DEG = 180.0 / math.pi
FIELD = [1.0, 0.0, -1.5]          # 가정: 수평 1, 아래로 1.5


def quiet(p):
    """잡음과 바이어스를 끈 센서 — 식 자체를 볼 때."""
    z = {k: 0.0 for k in ('sigma_g', 'sigma_bg', 'sigma_a', 'sigma_b',
                          'sigma_p')}
    return S.Sensors(dict(p, **z), rng.Rng(1))


def rms(xs):
    return math.sqrt(sum(x * x for x in xs) / len(xs))


def z0(x, eps=5e-10):
    return 0.0 if abs(x) < eps else x


# ------------------------------------------------ 1장 관성 센서
def accel(ctx):
    """L20 — 네 가지 비행 상황에서 가속도계가 재는 비력."""
    p = params.load()
    sen = quiet(p)
    oh = params.derived(p)['omega_hover']
    cases = []
    s = QR.hover_state(p, [0.0, 0.0, 5.0])
    cases.append(('호버', s, [oh] * 4))
    s = QR.hover_state(p, [0.0, 0.0, 5.0])
    s[13:17] = [0.0] * 4
    cases.append(('자유낙하(모터 0)', s, [0.0] * 4))
    s = QR.hover_state(p, [0.0, 0.0, 5.0])
    s[13:17] = [1.1 * oh] * 4
    cases.append(('상승 가속(회전수 ×1.1)', s, s[13:17]))
    s = QR.hover_state(p, [0.0, 0.0, 5.0])
    s[6:10] = Q.from_euler(math.radians(30), 0.0, 0.0)
    cases.append(('롤 30°, 호버 회전수', s, [oh] * 4))
    rows = []
    for name, s, cmd in cases:
        d = QR.deriv(p, s, cmd)
        a = sen.accel(s, d)
        tilt = math.atan2(math.hypot(a[0], a[1]), a[2]) if any(a) \
            else float('nan')
        true = math.acos(max(-1.0, min(1.0, Q.rotate(
            s[6:10], [0.0, 0.0, 1.0])[2])))
        rows.append([name] + ['%+.3f' % z0(x) for x in d[3:6]]
                    + ['%+.3f' % z0(x) for x in a]
                    + ['%.1f' % (true * DEG),
                       '-' if tilt != tilt else '%.1f' % (tilt * DEG)])
    head = ['상황', 'v̇x', 'v̇y', 'v̇z', '재는 x', '재는 y', '재는 z',
            '참 기울기°', '가속도계로 본 기울기°']
    ctx.table('p05_accel', head, rows, num=tuple(range(1, 9)))


def gyro_drift(ctx):
    """자이로만 적분하면 — 바이어스는 b·t, 잡음은 σ√(t·dt)."""
    p = params.load()
    b, sg, dt = p['sigma_bg'], p['sigma_g'], 0.004
    marks = (1.0, 10.0, 30.0, 100.0)
    runs = 60
    acc = {t: [] for t in marks}
    for seed in range(runs):
        g = rng.Rng(100 + seed)
        th, k = 0.0, 0
        for t in marks:
            while k < round(t / dt):
                th += sg * g.normal() * dt
                k += 1
            acc[t].append(th)
    rows = []
    for t in marks:
        rows.append(['%g' % t, '%.3f' % (b * t * DEG),
                     '%.4f' % (rms(acc[t]) * DEG),
                     '%.4f' % (sg * math.sqrt(t * dt) * DEG)])
    ctx.table('p05_drift', ['t[s]', '바이어스 b·t[°]',
                            '잡음만 — 잰 RMS[°] (60판)',
                            '잡음만 — σ√(t·dt)[°]'], rows,
              num=(0, 1, 2, 3))


def accel_double(ctx):
    """가속도계를 두 번 적분하면 — 영점 오차 b 는 ½bt²,
    기울기 1° 오차는 g·sin 1° 의 가속도."""
    p = params.load()
    b, dt = p['sigma_a'], 0.004
    tilt = p['g'] * math.sin(math.radians(1.0))
    rows = []
    x = v = 0.0
    k = 0
    for t in (1.0, 10.0, 60.0):
        while k < round(t / dt):
            v += b * dt
            x += v * dt
            k += 1
        rows.append(['%g' % t, '%.3f' % (0.5 * b * t * t), '%.3f' % x,
                     '%.2f' % (0.5 * tilt * t * t)])
    ctx.table('p05_double', ['t[s]', '½bt²[m]', '적분(dt 4 ms)[m]',
                             '1° 기울기 오차 ½(g sin1°)t²[m]'], rows,
              num=(0, 1, 2, 3))
    ctx.text('p05_tilt_acc', 'g·sin(1°) = %.4f m/s²  (g = %g)'
             % (tilt, p['g']))


def accel_tilt(ctx):
    """수평으로 가속하는 동안 가속도계가 보는 '기울기'."""
    p = params.load()
    sen = quiet(p)
    s = QR.hover_state(p, [0.0, 0.0, 5.0])
    rows = []
    for a in (0.0, 0.5, 1.0, 2.0, 5.0):
        d = [0.0] * 17
        d[3] = a
        m = sen.accel(s, d)
        rows.append(['%g' % a, '%+.3f' % m[0], '%+.3f' % m[2],
                     '%.2f' % (math.atan2(m[0], m[2]) * DEG)])
    ctx.table('p05_acctilt', ['수평 가속 a[m/s²]', '재는 x', '재는 z',
                              '가속도계로 본 기울기[°]'], rows,
              num=(0, 1, 2, 3))


# ------------------------------------------------ 2장 자력계·기압계
def mag_tilt(ctx):
    """기울기를 모르고 자력계로 방위를 읽으면 생기는 오차."""
    rows = []
    for inc in (0.5, 1.5):
        f = [1.0, 0.0, -inc]
        for deg in (0, 5, 10, 20, 30):
            r = math.radians(deg)
            m = Q.rotate(Q.conj(Q.from_euler(r, 0.0, 0.5)), f)
            e1 = C.heading(m, 0.0, 0.0) - 0.5
            e2 = C.heading(m, r, 0.0) - 0.5
            rows.append(['%g' % inc, '%d' % deg, '%.2f' % (e1 * DEG),
                         '%.2f' % (z0(e2, 1e-12) * DEG)])
    ctx.table('p05_magtilt', ['수직/수평(가정)', '롤[°]',
                              '기울기 무시 방위 오차[°]',
                              '기울기 보정 후[°]'], rows,
              num=(0, 1, 2, 3))


def spiral(n):
    out = []
    for k in range(n):
        zz = 1 - 2 * (k + 0.5) / n
        r = math.sqrt(1 - zz * zz)
        a = k * math.pi * (3 - math.sqrt(5))
        out.append([r * math.cos(a), r * math.sin(a), zz])
    return out


def mag_fit(ctx):
    """하드·소프트 아이언: 영점 + 축 배율 + 잡음을 넣고 되찾는다."""
    off, scl, sig = [0.3, -0.2, 0.1], [1.1, 0.9, 1.0], 0.01
    bmag = V.norm(FIELD)
    g = rng.Rng(5)
    pts = [[off[i] + scl[i] * bmag * d[i] + sig * g.normal()
            for i in range(3)] for d in spiral(200)]
    c1, r1 = C.fit_sphere(pts)
    c2, r2 = C.fit_axes(pts)
    rows = [['참값(가정)'] + ['%+.3f' % x for x in off]
            + ['%.3f' % (bmag * x) for x in scl],
            ['구 맞춤'] + ['%+.3f' % x for x in c1] + ['%.3f' % r1] * 3,
            ['축 타원체 맞춤'] + ['%+.3f' % x for x in c2]
            + ['%.3f' % x for x in r2]]
    ctx.table('p05_magfit', ['', '중심 x', '중심 y', '중심 z',
                             '반지름 x', '반지름 y', '반지름 z'], rows,
              num=(1, 2, 3, 4, 5, 6))
    worst = [0.0, 0.0, 0.0]
    for k in range(24):
        yaw = math.radians(15 * k)
        t = Q.rotate(Q.conj(Q.from_euler(0.0, 0.0, yaw)), FIELD)
        m = [off[i] + scl[i] * t[i] for i in range(3)]
        fixes = (m, [m[i] - c1[i] for i in range(3)],
                 [(m[i] - c2[i]) / r2[i] for i in range(3)])
        for j, v in enumerate(fixes):
            e = (C.heading(v, 0.0, 0.0) - yaw + math.pi) \
                % (2 * math.pi) - math.pi
            worst[j] = max(worst[j], abs(e))
    ctx.table('p05_magheading',
              ['보정', '방위 오차 최대[°] (15° 간격 24방향)'],
              [['없음', '%.2f' % (worst[0] * DEG)],
               ['중심만(하드 아이언)', '%.2f' % (worst[1] * DEG)],
               ['중심 + 축 배율', '%.2f' % (worst[2] * DEG)]], num=(1,))


def compassmot(ctx):
    """전류에 비례하는 간섭 — 전류를 올리며 재고 직선을 맞춘다."""
    k_true = [0.02, -0.01, 0.015]          # 가정: A 당 간섭
    g = rng.Rng(8)
    cur = [2.0 * i for i in range(16)]
    base = Q.rotate(Q.conj(Q.from_euler(0.0, 0.0, 0.5)), FIELD)
    k_fit = []
    for ax in range(3):
        ys = [base[ax] + k_true[ax] * i + 0.01 * g.normal()
              for i in cur]
        k_fit.append(C.fit_line(cur, ys)[0])
    rows = []
    for amp in (0.0, 10.0, 20.0, 30.0):
        m = [base[i] + k_true[i] * amp for i in range(3)]
        fixed = [m[i] - k_fit[i] * amp for i in range(3)]
        rows.append(['%g' % amp,
                     '%.2f' % ((C.heading(m, 0, 0) - 0.5) * DEG),
                     '%.3f' % ((C.heading(fixed, 0, 0) - 0.5) * DEG)])
    ctx.table('p05_compassmot', ['전류[A]', '보상 전 방위 오차[°]',
                                 '보상 후[°]'], rows, num=(0, 1, 2))
    ctx.text('p05_compassmot_k', '참 k = %s\n맞춘 k = %s' % (
        ' '.join('%+.4f' % x for x in k_true),
        ' '.join('%+.4f' % x for x in k_fit)))


def baro(ctx):
    """정수압 dp = −ρ g dh — 압력 차와 높이 차를 잇는 한 줄."""
    p = params.load()
    rg = p['rho'] * p['g']
    rows = [['높이 1 m', '%.2f' % rg, '1'],
            ['0.12 hPa = 12 Pa', '12', '%.3f' % (12 / rg)],
            ['1 hPa = 100 Pa', '100', '%.2f' % (100 / rg)],
            ['1.5 Pa (1 K 당 온도 계수)', '1.5', '%.3f' % (1.5 / rg)]]
    ctx.table('p05_baro', ['항목', '압력 차[Pa]', '높이 차[m]'], rows,
              num=(1, 2))


# ------------------------------------------------ 3장 GNSS
def sky(pairs):
    """(고도각°, 방위각°) → 궤도 반지름 위의 위성 위치 (합성 예제)."""
    out = []
    for el, az in pairs:
        e, a = math.radians(el), math.radians(az)
        out.append([GT.R * math.cos(e) * math.cos(a),
                    GT.R * math.cos(e) * math.sin(a),
                    GT.R * math.sin(e)])
    return out


GEOMS = [('천정 하나 + 낮은 셋', [(90, 0), (15, 0), (15, 120),
                                 (15, 240)]),
         ('예제의 여섯', [(60, 0), (35, 70), (30, 150), (45, 220),
                        (25, 290), (70, 180)]),
         ('예제의 앞 넷', [(60, 0), (35, 70), (30, 150), (45, 220)]),
         ('한데 몰린 넷', [(60, 0), (70, 20), (65, 40), (55, 25)]),
         ('같은 고도각 넷', [(30, 0), (30, 90), (30, 180), (30, 270)]),
         ('셋', [(60, 0), (35, 70), (30, 150)])]


def jac(sv, x):
    """의사거리 식의 야코비 행 — (단위 벡터, 1)."""
    rows = []
    for s in sv:
        d = math.dist(s, x[:3])
        rows.append([(x[i] - s[i]) / d for i in range(3)] + [1.0])
    return rows


def pdop(rows):
    """√(AᵀA)⁻¹ 의 위치 대각합 — 잡음 1 이 위치 오차 몇이 되나."""
    ata = [[sum(r[i] * r[j] for r in rows) for j in range(4)]
           for i in range(4)]
    tr = 0.0
    for i in range(3):
        e = [0.0] * 4
        e[i] = 1.0
        tr += linalg.solve(ata, e)[i]
    return math.sqrt(tr)


def gnss_geometry(ctx):
    """L15·T26 — 위성 배치가 계수와 오차 증폭(PDOP)을 정한다.

    수신기는 원점, 시계 오차 45 km, 의사거리 잡음 σ = 1 m."""
    truth, bias, sig = [0.0, 0.0, 0.0], 45_000.0, 1.0
    rows = []
    for name, pairs in GEOMS:
        sv = sky(pairs)
        a = jac(sv, truth + [bias])
        rk = linalg.rank(a + [[0.0] * 4] * max(0, 4 - len(a)))
        try:
            dop = '%.2f' % pdop(a)
            g = rng.Rng(21)
            err = []
            for _ in range(300):
                rho = [math.dist(s, truth) + bias + sig * g.normal()
                       for s in sv]
                x, _h = GT.solve(sv, rho)
                err.append(math.dist(x[:3], truth))
            rows.append([name, '%d' % len(sv), '%d' % rk, dop,
                         '%.2f' % (rms(err) / sig)])
        except ValueError:
            rows.append([name, '%d' % len(sv), '%d' % rk, '-',
                         '풀 수 없음(특이)'])
    ctx.table('p05_geometry', ['배치(고도각·방위각)', '위성',
                               '야코비 계수', 'PDOP',
                               'RMS 위치 오차 ÷ σ (300판)'], rows,
              num=(1, 2, 3, 4))


def gnss_blunder(ctx):
    """위성 하나의 의사거리가 10 m 틀리면 — 넷과 여섯의 차이."""
    truth, bias = [1200.0, -800.0, 300.0], 45_000.0
    rows = []
    for name, pairs in (GEOMS[0], GEOMS[1]):
        sv = sky(pairs)
        for bad in range(len(sv)):
            rho = [math.dist(s, truth) + bias for s in sv]
            rho[bad] += 10.0
            x, h = GT.solve(sv, rho)
            res = [r - (math.dist(s, x[:3]) + x[3])
                   for s, r in zip(sv, rho)]
            rows.append([name, '%d' % (bad + 1),
                         '%.2f' % math.dist(x[:3], truth),
                         '%.2f' % (x[3] - bias), '%.2f' % rms(res)])
    ctx.table('p05_blunder', ['배치', '틀린 위성', '위치 오차[m]',
                              '시계 오차 추정의 어긋남[m]',
                              '남은 잔차 RMS[m]'], rows,
              num=(1, 2, 3, 4))


def swarm(ctx):
    """드론마다 위치가 σ 만큼 흔들리면 10×10 격자의 최소 거리는."""
    rows = []
    for sig, label in ((0.3, 'σ 0.3 m (params sigma_p)'),
                       (0.02, 'σ 0.02 m (가정: RTK 급)')):
        g = rng.Rng(31)
        mins = []
        for _ in range(30):
            pts = [[1.5 * i + sig * g.normal(),
                    1.5 * j + sig * g.normal(),
                    20.0 + sig * g.normal()]
                   for i in range(10) for j in range(10)]
            best = 1e9
            for a in range(len(pts)):
                for b in range(a + 1, len(pts)):
                    d = V.dist(pts[a], pts[b])
                    if d < best:
                        best = d
            mins.append(best)
        rows.append([label, '%.3f' % min(mins),
                     '%.3f' % (sum(mins) / len(mins)),
                     '%d' % sum(1 for m in mins if m < 1.0)])
    ctx.table('p05_swarm', ['위치 흔들림', '최소 거리의 최솟값[m]',
                            '최소 거리의 평균[m]',
                            '1 m 미만인 판(30판)'],
              rows, num=(1, 2, 3))


# ------------------------------------------------ 5장 자세 표현
def lock(ctx):
    """T5·L18 — 피치가 90° 에 가까워지면 E 가 풀리지 않는다."""
    rows = []
    for deg in (0.0, 45.0, 80.0, 89.0, 89.9, 90.0):
        th = math.radians(deg)
        e = Q.euler_rate_matrix(0.3, th)
        dt = V.det3(e)
        if abs(dt) < 1e-12:
            rows.append(['%g' % deg, '%.4f' % z0(dt, 1e-12), '-', '-',
                         '-', '풀 수 없음'])
            continue
        r = linalg.solve(e, [0.0, 0.0, 1.0])
        rows.append(['%g' % deg, '%.4f' % dt, '%.3f' % r[0],
                     '%.3f' % r[1], '%.3f' % r[2], '풀림'])
    ctx.table('p05_lock', ['피치[°]', 'det E', 'φ̇', 'θ̇', 'ψ̇', ''],
              rows, num=(0, 1, 2, 3, 4))
    lines = []
    for deg in (90.0, 80.0):
        th = math.radians(deg)
        a = Q.to_matrix(Q.from_euler(0.2, th, 0.5))
        b = Q.to_matrix(Q.from_euler(0.5, th, 0.8))
        d = max(abs(a[i][j] - b[i][j])
                for i in range(3) for j in range(3))
        lines.append('피치 %g°: (0.2, 0.5) 와 (0.5, 0.8) 의 '
                     '행렬 차 최대 %.2e' % (deg, d))
    q = Q.from_euler(0.2, math.pi / 2, 0.5)
    back = Q.to_euler(q)
    lines.append('to_euler(from_euler(0.2, 90°, 0.5)) = '
                 '(%.4f, %.4f°, %.4f)'
                 % (back[0], back[1] * DEG, back[2]))
    b2 = Q.to_matrix(Q.from_euler(*back))
    d = max(abs(Q.to_matrix(q)[i][j] - b2[i][j])
            for i in range(3) for j in range(3))
    lines.append('되돌린 각으로 만든 행렬과의 차 최대 %.2e' % d)
    ctx.text('p05_lock_same', '\n'.join(lines))


def qnorm(ctx):
    """T7 — 오일러 한 걸음마다 |q| 가 √(1+(dt|ω|/2)²) 배."""
    w = [1.0, -2.0, 0.5]
    wn = V.norm(w)
    q0 = Q.from_axis_angle([0.0, 0.6, 0.8], 0.4)
    rows = []
    for dt in (0.01, 0.004, 0.001):
        for secs in (1.0, 10.0):
            n = round(secs / dt)
            q, qn = list(q0), list(q0)
            for _ in range(n):
                q = Q.step_euler(q, w, dt)
                qn = Q.normalize(Q.step_euler(qn, w, dt))
            want = (1 + (dt * wn / 2) ** 2) ** (n / 2)
            ex = Q.mul(q0, Q.from_axis_angle(w, wn * secs))
            ang = Q.to_axis_angle(Q.mul(Q.conj(ex), qn))[1]
            rows.append(['%g' % dt, '%g' % secs, '%d' % n,
                         '%.6f' % Q.norm(q), '%.6f' % want,
                         '%.2e' % ang])
    ctx.table('p05_qnorm', ['dt[s]', 't[s]', '걸음', '|q| 잰 값',
                            '(1+(dt|ω|/2)²)^(n/2)',
                            '정규화한 오일러의 각 오차[rad]'], rows,
              num=(0, 1, 2, 3, 4, 5))


def rot(ctx):
    """T4·T6 — 무작위 쿼터니언 200개로 성질을 잰다(가장 나쁜 값)."""
    g = rng.Rng(41)
    worst = [0.0] * 6
    for _ in range(200):
        q = Q.normalize([g.normal() for _ in range(4)])
        p2 = Q.normalize([g.normal() for _ in range(4)])
        a = [g.normal() for _ in range(3)]
        b = [g.normal() for _ in range(3)]
        r = Q.to_matrix(q)
        rtr = V.matmul(V.transpose(r), r)
        i3 = V.eye3()
        m1 = Q.to_matrix(Q.mul(q, p2))
        m2 = V.matmul(r, Q.to_matrix(p2))
        mq = Q.to_matrix([-c for c in q])
        vals = [max(abs(rtr[i][j] - i3[i][j]) for i in range(3)
                    for j in range(3)),
                abs(V.det3(r) - 1),
                max(abs(m1[i][j] - m2[i][j]) for i in range(3)
                    for j in range(3)),
                abs(V.norm(Q.rotate(q, a)) - V.norm(a)),
                abs(V.dot(Q.rotate(q, a), Q.rotate(q, b))
                    - V.dot(a, b)),
                max(abs(r[i][j] - mq[i][j]) for i in range(3)
                    for j in range(3))]
        worst = [max(x, y) for x, y in zip(worst, vals)]
    names = ['|RᵀR − I| 최대', '|det R − 1|',
             '|R(q⊗p) − R(q)R(p)| 최대', '||qvq*| − |v||',
             '|(Ra)·(Rb) − a·b|', '|R(q) − R(−q)| 최대']
    ctx.table('p05_rot', ['성질', '200개 중 가장 나쁜 값'],
              [[n, '%.1e' % w] for n, w in zip(names, worst)], num=(1,))


# ------------------------------------------------ 6장 상보 필터
def comp_run(alpha, secs=60.0, dt=0.004, bias=0.02, sg=0.01, sa=0.05,
             seed=7):
    """test_estimator 의 한 축 실험 — 참 각 sin(0.5t)."""
    g = rng.Rng(seed)
    est = gy = 0.0
    ec, eg, ea = [], [], []
    for k in range(round(secs / dt)):
        t = k * dt
        th = math.sin(0.5 * (t + dt))
        gyro = 0.5 * math.cos(0.5 * t) + bias + sg * g.normal()
        acc = th + sa * g.normal()
        est = E.complementary_1d(est, gyro, acc, alpha, dt)
        gy += gyro * dt
        if t >= 10.0:
            ec.append(est - th)
            eg.append(gy - th)
            ea.append(acc - th)
    return rms(ec), rms(eg), rms(ea)


def comp_sweep(ctx):
    """α 를 바꾸면 — 바이어스 몫은 커지고 잡음 몫은 준다."""
    dt, b, sa = 0.004, 0.02, 0.05
    rows = []
    for a in (0.9, 0.95, 0.98, 0.99, 0.995, 0.999):
        c, gy, ac = comp_run(a)
        eb = a * b * dt / (1 - a)
        en = sa * math.sqrt((1 - a) / (1 + a))
        rows.append(['%g' % a, '%.3f' % (a * dt / (1 - a)),
                     '%.5f' % eb, '%.5f' % en,
                     '%.5f' % math.hypot(eb, en), '%.5f' % c])
    ctx.table('p05_alpha', ['α', 'τ = α·dt/(1−α)[s]',
                            '바이어스 몫 αb·dt/(1−α)',
                            '가속도계 잡음 몫 σ√((1−α)/(1+α))',
                            '두 몫의 제곱합 √', '잰 RMS 오차(10–60 s)'],
              rows, num=(0, 1, 2, 3, 4, 5))
    c, gy, ac = comp_run(0.98)
    ctx.text('p05_alpha_ref', 'α = 0.98: 상보 %.5f · 자이로만 %.5f · '
             '가속도계만 %.5f  (RMS, rad, 10–60 s)' % (c, gy, ac))


def comp_quat(ctx):
    """쿼터니언 상보 필터 — k_c 가 기울기를 붙잡고, 요는 못 잡는다."""
    truth = Q.from_euler(0.2, -0.1, 0.7)
    acc = Q.rotate(Q.conj(truth), [0.0, 0.0, 9.81])
    gyro = [0.02, -0.01, 0.015]                 # 바이어스만
    # 기울기 오차 = 몸체 좌표로 본 '위' 방향의 어긋남(요와 무관)
    up_t = Q.rotate(Q.conj(truth), [0.0, 0.0, 1.0])
    rows = []
    for kc in (0.0, 0.1, 1.0, 5.0):
        f = E.Complementary(k_c=kc, q0=truth)
        for _ in range(5000):
            f.update(gyro, acc, 0.004)
        up = Q.rotate(Q.conj(f.q), [0.0, 0.0, 1.0])
        tilt = math.acos(min(1.0, V.dot(up, up_t)))
        yaw = Q.to_euler(f.q)[2] - Q.to_euler(truth)[2]
        rows.append(['%g' % kc, '%.3f' % (tilt * DEG),
                     '%.3f' % (yaw * DEG)])
    ctx.table('p05_compq', ['k_c', '기울기 오차[°] (20 s)',
                            '요 오차[°] (20 s)'], rows, num=(0, 1, 2))


# ------------------------------------------------ 7장 칼만 필터
def gain(ctx):
    """T24 — 섞는 비율 K 에 따른 분산: 식과 2만 번 뽑은 표본."""
    p, r = 1.0, 0.25
    g = rng.Rng(51)
    draws = [(math.sqrt(p) * g.normal(), math.sqrt(r) * g.normal())
             for _ in range(20000)]
    ks = [0.0, 0.2, 0.4, 0.6, E.kalman_1d_gain(p, r), 0.9, 1.0]
    rows = []
    for k in ks:
        emp = sum(((1 - k) * a + k * b) ** 2 for a, b in draws) \
            / len(draws)
        rows.append(['%.2f' % k, '%.4f' % E.posterior_var(p, r, k),
                     '%.4f' % emp])
    ctx.table('p05_gain', ['K', '(1−K)²P + K²R', '표본 분산(2만 개)'],
              rows, num=(0, 1, 2))


def seq(ctx):
    """같은 양을 거듭 재면 — P 가 R/n 꼴로 준다."""
    p, r = 100.0, 1.0
    rows = []
    for n in range(1, 11):
        k = E.kalman_1d_gain(p, r)
        p = E.posterior_var(p, r, k)
        if n in (1, 2, 3, 5, 10):
            rows.append(['%d' % n, '%.4f' % k, '%.5f' % p,
                         '%.5f' % (1 / (1 / 100.0 + n / r)),
                         '%.5f' % (r / n)])
    ctx.table('p05_seq', ['n', 'K', 'P (갱신 뒤)', '1/(1/P₀ + n/R)',
                          'R/n'], rows, num=(0, 1, 2, 3, 4))


def qr(ctx):
    """상수 속도 모델의 정상 이득 — q/r 이 클수록 측정을 믿는다."""
    r, dt = 0.09, 0.1
    rows = []
    for q in (1e-4, 1e-3, 1e-2, 1e-1, 1.0):
        kf = E.Kalman1D(q, r)
        prev, settle = None, None
        for k in range(1, 2001):
            kf.predict(dt)
            s = kf.p[0][0] + r
            kk = (kf.p[0][0] / s, kf.p[1][0] / s)
            kf.update(0.0)
            if prev and settle is None and \
                    abs(kk[0] - prev[0]) < 1e-9:
                settle = k
            prev = kk
        rows.append(['%g' % q, '%.4f' % kk[0], '%.4f' % kk[1],
                     '%.4f' % math.sqrt(kf.p[0][0]), '%d' % settle])
    ctx.table('p05_qr', ['q (r = 0.09)', 'K 위치', 'K 속도[1/s]',
                         '√P 위치[m]', '이득이 멈춘 걸음'], rows,
              num=(0, 1, 2, 3, 4))


def track(q_f, r_f, q=0.05, r=0.09, n=3000, dt=0.1, seed=61,
          glitch=None, gate=None):
    """참 운동(가속이 흰 잡음) + GNSS 같은 위치 측정 → Kalman1D."""
    g = rng.Rng(seed)
    kf = E.Kalman1D(q_f, r_f)
    x, v = 0.0, 1.0
    out = {'raw': [], 'pos': [], 'vel': [], 'nis': [], 'inn': [],
           'rej': 0, 'rej_glitch': 0}
    for k in range(n):
        v += math.sqrt(q * dt) * g.normal()
        x += v * dt
        z = x + math.sqrt(r) * g.normal()
        if glitch and glitch[0] <= k < glitch[1]:
            z += 5.0
        kf.predict(dt)
        if gate and not gated(kf, z, gate):
            out['rej'] += 1
            if glitch and glitch[0] <= k < glitch[1]:
                out['rej_glitch'] += 1
        else:
            y, s = kf.update(z)
            out['nis'].append(y * y / s)
            out['inn'].append(y)
        out['raw'].append(z - x)
        out['pos'].append(kf.x[0] - x)
        out['vel'].append(kf.x[1] - v)
    return out


def gated(kf, z, limit):
    """혁신 검사: y²/S 가 limit 를 넘는 측정은 버린다(갱신하지 않음).

    PX4 EKF2 의 '혁신 일관성 검사' 와 같은 생각 — 모델이 맞으면
    y²/S 는 평균 1 이고, 9(3σ) 를 넘는 일은 드물다."""
    y = z - kf.x[0]
    s = kf.p[0][0] + kf.r
    return y * y / s <= limit


def lag1(xs):
    m = sum(xs) / len(xs)
    c0 = sum((a - m) ** 2 for a in xs)
    return sum((a - m) * (b - m) for a, b in zip(xs, xs[1:])) / c0


def tracking(ctx):
    """T25 — 조율이 맞으면 NIS 평균 1, 혁신은 흰 잡음."""
    q, r = 0.05, 0.09
    rows = []
    for label, qf, rf in (('맞음 (q, r)', q, r), ('q ÷ 10', q / 10, r),
                          ('q × 10', q * 10, r), ('r ÷ 4', q, r / 4),
                          ('r × 4', q, r * 4)):
        o = track(qf, rf)
        t = slice(200, None)
        rows.append([label, '%.3f' % rms(o['raw'][t]),
                     '%.3f' % rms(o['pos'][t]),
                     '%.3f' % rms(o['vel'][t]),
                     '%.2f' % (sum(o['nis'][t]) / len(o['nis'][t])),
                     '%+.3f' % lag1(o['inn'][t])])
    ctx.table('p05_track', ['필터 설정', '측정 RMS[m]', '위치 RMS[m]',
                            '속도 RMS[m/s]', 'NIS 평균',
                            '혁신 자기상관(1)'],
              rows, num=(1, 2, 3, 4, 5))


def glitch(ctx):
    """1000–1009 걸음에 측정이 5 m 튄다 — 검사 없음 대 NIS ≤ 9."""
    rows = []
    for label, gate in (('검사 없음', None), ('y²/S ≤ 9', 9.0)):
        o = track(0.05, 0.09, glitch=(1000, 1010), gate=gate)
        w = o['pos'][995:1040]
        rows.append([label, '%.3f' % max(abs(e) for e in w),
                     '%d' % o['rej'], '%d' % o['rej_glitch'],
                     '%.3f' % rms(o['pos'][200:])])
    ctx.table('p05_glitch', ['', '튀는 동안·뒤 최대 위치 오차[m]',
                             '버린 측정', '그 가운데 튄 구간',
                             '전체 위치 RMS[m]'], rows,
              num=(1, 2, 3, 4))


def baro_fuse(ctx):
    """가속도계(250 Hz)로 예측, 기압계(50 Hz)로 갱신하는 고도 필터."""
    p = params.load()
    sa, sb, dt = p['sigma_a'], p['sigma_b'], 0.004
    g = rng.Rng(71)
    kf = E.Kalman1D(sa * sa * dt, sb * sb, p0=(1.0, 1.0))
    raw, fz, fv, nis = [], [], [], []
    for k in range(round(60.0 / dt)):
        t = (k + 1) * dt
        z = 2 * math.sin(0.3 * t)
        vz = 0.6 * math.cos(0.3 * t)
        az = -0.18 * math.sin(0.3 * (t - dt))
        kf.predict(dt, az + sa * g.normal())
        if k % 5 == 4:
            m = z + sb * g.normal()
            y, s = kf.update(m)
            if t > 5.0:
                raw.append(m - z)
                nis.append(y * y / s)
        if t > 5.0:
            fz.append(kf.x[0] - z)
            fv.append(kf.x[1] - vz)
    ctx.table('p05_barofuse', ['', '값'],
              [['기압계 그대로 RMS[m]', '%.4f' % rms(raw)],
               ['필터 고도 RMS[m]', '%.4f' % rms(fz)],
               ['필터 상승률 RMS[m/s]', '%.4f' % rms(fv)],
               ['NIS 평균', '%.2f' % (sum(nis) / len(nis))]], num=(1,))


# ------------------------------------------------ 8장 캘리브레이션
def gyro_cal(ctx):
    """가만히 두고 평균 — 바이어스 추정 오차는 σ/√N."""
    p = params.load()
    rows = []
    for secs in (0.2, 1.0, 5.0, 30.0):
        n = round(secs / 0.004)
        errs = []
        for seed in range(10):
            sen = S.Sensors(p, rng.Rng(200 + seed))
            s = QR.hover_state(p, [0.0, 0.0, 0.0])
            b = C.gyro_bias([sen.gyro(s) for _ in range(n)])
            errs.extend(b[i] - sen.bias[i] for i in range(3))
        rows.append(['%g' % secs, '%d' % n, '%.2e' % rms(errs),
                     '%.2e' % (p['sigma_g'] / math.sqrt(n))])
    ctx.table('p05_gyrocal', ['가만히 둔 시간[s]', '표본 N (250 Hz)',
                              '추정 오차 RMS[rad/s] (10판×3축)',
                              'σ_g/√N'], rows, num=(0, 1, 2, 3))


def accel_cal(ctx):
    """6면 보정 — 한 면마다 N 개를 평균하면 영점 오차가 σ/√N 로."""
    p = params.load()
    ofs, scl, g0 = [0.12, -0.3, 0.05], [1.02, 0.97, 1.01], p['g']
    rows = []
    for n in (1, 25, 250, 2500):
        g = rng.Rng(81)
        e_o, e_s = [], []
        for _ in range(10):
            up, down = [], []
            for i in range(3):
                for sign, bag in ((1.0, up), (-1.0, down)):
                    tv = [0.0, 0.0, 0.0]
                    tv[i] = sign * g0
                    rd = [[scl[j] * tv[j] + ofs[j]
                           + p['sigma_a'] * g.normal()
                           for j in range(3)] for _ in range(n)]
                    bag.append(C.gyro_bias(rd))
            o, s = C.accel_six(up, down, g0)
            e_o.extend(o[i] - ofs[i] for i in range(3))
            e_s.extend(s[i] - scl[i] for i in range(3))
        rows.append(['%d' % n, '%.2e' % rms(e_o),
                     '%.2e' % (p['sigma_a'] / math.sqrt(2 * n)),
                     '%.2e' % rms(e_s)])
    ctx.table('p05_accelcal', ['한 면의 표본 N', '영점 오차 RMS[m/s²]',
                               'σ_a/√(2N)', '배율 오차 RMS'], rows,
              num=(0, 1, 2, 3))


def up_error(s, est):
    """참 '위'(Rᵀe₃)와 추정한 '위' 사이의 각 [°]."""
    up = Q.rotate(Q.conj(s[6:10]), [0.0, 0.0, 1.0])
    n = math.sqrt(sum(x * x for x in est))
    c = sum(u * e for u, e in zip(up, est)) / n
    return math.acos(max(-1.0, min(1.0, c))) * DEG


def toy_fly(p, filtertime, secs=20.0, seed=31):
    """6자유도 비행(옆으로 20 m 돌진 뒤 제자리)에 완구 필터를 250 Hz 로
    붙인다. (최대 오차, 그 시각, 8 초 오차, 20 초 오차, 최대 참 기울기)
    — 각은 [°], 시각은 [s]."""
    from droneshow import cascade
    ctl = cascade.Controller(p)
    st = QR.hover_state(p, [0.0, 0.0, 5.0])
    sen = S.Sensors(p, rng.Rng(seed))
    f = TI.ToyIMU(filtertime, g=p['g'])
    dt = 1.0 / cascade.PHYS_HZ
    ref = {'p': [20.0, 0.0, 5.0]}
    worst, t_w, tilt, at8 = 0.0, 0.0, 0.0, 0.0
    for k in range(round(secs / dt)):
        cmd = ctl.update(k, st, ref)
        if k % 2 == 0:
            d = QR.deriv(p, st, cmd)
            f.update(sen.gyro(st), sen.accel(st, d), 2 * dt)
            err = up_error(st, f.est)
            if err > worst:
                worst, t_w = err, k * dt
            tilt = max(tilt, up_error(st, [0.0, 0.0, 1.0]))
            if k == round(8.0 / dt):
                at8 = err
        st = QR.step(p, st, cmd, dt)
    return worst, t_w, at8, err, tilt


def toy(ctx):
    """5부 9장 — 완구 드론의 6축 상보 필터를 실제 비행 모델에서."""
    p = params.load()
    rows = []
    sen = S.Sensors(p, rng.Rng(31))            # toy_fly 와 같은 씨앗
    bxy = math.hypot(sen.bias[0], sen.bias[1])
    for name, T in (('가속도계만(T → 0)', 1e-9), ('T = 0.5 s', 0.5),
                    ('T = 2 s(펌웨어 기본)', 2.0), ('T = 4 s', 4.0),
                    ('자이로만(T → ∞)', 1e9)):
        w, t, e8, e20, tilt = toy_fly(p, T)
        bound = '%.2f' % (bxy * T * DEG) if T < 100 else '—'
        rows.append([name, '%.2f' % w, '%.2f' % t, '%.2f' % e8,
                     '%.2f' % e20, bound])
    head = ['필터', '최대 오차[°]', '그 시각[s]', '8 초[°]', '20 초[°]',
            'b·T[°]']
    ctx.table('p05_toy_dash', head, rows, num=(1, 2, 3, 4, 5))
    ctx.text('p05_toy_tilt', '옆으로 20 m 돌진하는 동안 참 기울기의 '
             '최댓값: %.1f° · 수평 자이로 바이어스 %.4f rad/s(씨앗 31)'
             % (tilt, bxy))
    rows = []
    g = rng.Rng(41)
    for b in (0.002, 0.005, 0.01, 0.02):
        sen = S.Sensors(p, g)
        sen.bias = [0.0, 0.0, b]
        h = TI.Headless()
        still = [0.0] * 10 + [0.0, 0.0, 0.0] + [0.0] * 4
        out, t = [], 0.0
        for k in range(1, 30001):                  # 250 Hz, 120 초
            h.update(sen.gyro(still)[2], 0.004)
            if k in (2500, 7500, 15000, 30000):
                out.append('%.1f' % (h.yaw * DEG))
        rows.append(['%.3f' % b, '%.2f' % (b * DEG)] + out)
    ctx.table('p05_toy_headless', ['바이어스[rad/s]', '[°/s]', '10 초',
                                   '30 초', '60 초', '120 초'], rows,
              num=(0, 1, 2, 3, 4, 5))


def run(ctx):
    toy(ctx)
    ctx.py('p05_gps', 'ex/gps_trilateration.py')
    ctx.py('p05_calib', 'ex/imu_calib.py')
    accel(ctx)
    gyro_drift(ctx)
    accel_double(ctx)
    accel_tilt(ctx)
    mag_tilt(ctx)
    mag_fit(ctx)
    compassmot(ctx)
    baro(ctx)
    gnss_geometry(ctx)
    gnss_blunder(ctx)
    swarm(ctx)
    lock(ctx)
    qnorm(ctx)
    rot(ctx)
    comp_sweep(ctx)
    comp_quat(ctx)
    gain(ctx)
    seq(ctx)
    qr(ctx)
    tracking(ctx)
    glitch(ctx)
    baro_fuse(ctx)
    gyro_cal(ctx)
    accel_cal(ctx)
