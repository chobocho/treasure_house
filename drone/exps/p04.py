# -*- coding: utf-8 -*-
"""4부 — 기체와 추진. 프레임·모멘텀 이론·반토크·ESC·배터리·진동의 수.

모든 수는 기준 쿼드로터(data/params.tsv — 이 덱의 설계값)에서 나온다.
표에 '가정' 이라고 적힌 값(비에너지, 내부 저항, 불균형 질량, 날개 수)
은 모델의 입력이지 실제 제품의 측정값이 아니다.
"""
import math
import os
import sys

from droneshow import mixer, motor, params
from droneshow import quadrotor as QR
from droneshow import quat as Q

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'ex'))
import dshot_packet as D  # noqa: E402
import frame_mixer as FM  # noqa: E402

LABEL = {'quad_x': 'X 쿼드', 'quad_plus': '+ 쿼드',
         'quad_h': 'H 쿼드', 'hexa_x': '헥사 X (+−+−+−)',
         'hexa_x_ppnnpn': '헥사 X (++−−+−)', 'octo_x': '옥토 X',
         'x8': 'X8 (동축 4쌍)', 'y6': 'Y6 (동축 3쌍)'}


def z(x):
    """−0.000 을 찍지 않게 아주 작은 수는 0 으로."""
    return 0.0 if abs(x) < 1e-9 else x


def captures(ctx):
    ctx.py('p04_hover', 'ex/hover_power.py')
    ctx.py('p04_battery', 'ex/battery_time.py')
    ctx.py('p04_dshot', 'ex/dshot_packet.py')


def frames(ctx):
    p = params.load()
    c, mg = p['kQ'] / p['kT'], p['m'] * p['g']
    rows = []
    for name in FM.NAMES:
        m = FM.matrix(FM.rotors(name, p['L']), c)
        u = FM.equal_split(m, mg)
        rows.append([LABEL[name], str(len(m[0])),
                     '%.1e' % max(abs(x) for x in u[1:]),
                     '%.2f' % FM.cost(m, 1), '%.2f' % FM.cost(m, 2),
                     '%.2f' % FM.cost(m, 3)])
    ctx.table('p04_frames', ['프레임', '로터',
                             '같은 추력의 |토크| 최대',
                             '롤', '피치', '요'], rows,
              num=(1, 2, 3, 4, 5))
    rows = []
    for name in ('quad_x', 'hexa_x', 'hexa_x_ppnnpn'):
        m = FM.matrix(FM.rotors(name, p['L']), c)
        for k in range(len(m[0])):
            g = FM.engine_out(m, k, mg)
            rows.append([LABEL[name], str(k + 1),
                         '평형 없음' if g is None else '%.3f' % z(g)])
    ctx.table('p04_engine', ['프레임', '멈춘 로터', '여유[N]'], rows,
              num=(1, 2))


def radius(ctx):
    p = params.load()
    t = p['m'] * p['g'] / 4
    rows = []
    for r in (0.04, 0.0635, 0.08, 0.1, 0.127, 0.2):
        a = math.pi * r * r
        q = dict(p, r_prop=r)
        rows.append(['%.4f' % r, '%.1f' % (2 * r / 0.0254),
                     '%.1f' % (t / a),
                     '%.2f' % motor.induced_velocity(t, p['rho'], a),
                     '%.2f' % motor.ideal_power(t, p['rho'], a),
                     '%.1f' % motor.hover_power(q),
                     '%.1f' % (motor.flight_time(q) / 60)])
    ctx.table('p04_radius', ['반지름[m]', '지름[인치]', 'T/A[N/m²]',
                             'v[m/s]', '로터 하나 이상 일률[W]',
                             '네 로터 전기[W]', '비행시간[분]'], rows,
              num=(0, 1, 2, 3, 4, 5, 6))


def density(ctx):
    p = params.load()
    t0 = motor.flight_time(p)
    rows = []
    for k in (1.0, 0.95, 0.9, 0.85, 0.8):
        q = dict(p, rho=p['rho'] * k)
        rows.append(['%.2f' % k, '%.4f' % q['rho'],
                     '%.2f' % motor.hover_power(q),
                     '%.3f' % (1 / math.sqrt(k)),
                     '%.2f' % (motor.flight_time(q) / 60),
                     '%.3f' % (motor.flight_time(q) / t0)])
    ctx.table('p04_rho', ['ρ 비율', 'ρ[kg/m³]', '호버 전기[W]',
                          '1/√비율', '비행시간[분]', '시간 비율'], rows,
              num=(0, 1, 2, 3, 4, 5))


def two_models(ctx):
    """한 로터의 두 모델 — kQ·Ω³ 와 모멘텀 이론 ÷ fm — 이 같은 일률."""
    p = params.load()
    d = params.derived(p)
    rows = []
    for k in (0.8, 1.0, 1.2):
        q = dict(p, m=p['m'] * k)
        dq = params.derived(q)
        w = dq['omega_hover']
        mech = p['kQ'] * w ** 3
        mom = motor.ideal_power(dq['T_hover'], p['rho'], d['area'])
        rows.append(['%.2f' % q['m'], '%.1f' % w, '%.4f' % mech,
                     '%.4f' % (mom / p['fm']), '%.4f' % (mech * p['fm']
                                                         / mom)])
    ctx.table('p04_kq', ['m[kg]', 'Ω_h[rad/s]', 'kQ·Ω³[W]',
                         '이상 일률÷fm[W]', '비율×fm'], rows,
              num=(0, 1, 2, 3, 4))


def yaw(ctx):
    """두 쌍의 회전수를 벌린다 — 총추력은 그대로(T3)."""
    p = params.load()
    oh = params.derived(p)['omega_hover']
    rows = []
    for dl in (0.0, 0.01, 0.02, 0.05, 0.1):
        ccw = oh * (1 + dl)
        cw = math.sqrt(2 * oh * oh - ccw * ccw)
        t = [p['kT'] * w * w for w in (ccw, cw, ccw, cw)]
        u = mixer.forward(p, t)
        rows.append(['%.2f' % dl, '%.1f' % ccw, '%.1f' % cw,
                     '%.4f' % u[0], '%.1e' % max(abs(u[1]), abs(u[2])),
                     '%.5f' % u[3], '%.3f' % (u[3] / p['Jzz'])])
    ctx.table('p04_yaw', ['δ', 'Ω 반시계 쌍', 'Ω 시계 쌍', 'F[N]',
                          '|τx|,|τy|', 'τz[N·m]', 'ṙ[rad/s²]'], rows,
              num=(0, 1, 2, 3, 4, 5, 6))
    # 물리 모델에서 제어 없이: δ = 0.02 를 1 초
    ccw = oh * 1.02
    cw = math.sqrt(2 * oh * oh - ccw * ccw)
    cmd = [ccw, cw, ccw, cw]
    tz = mixer.forward(p, [p['kT'] * w * w for w in cmd])[3]
    s = QR.hover_state(p, [0.0, 0.0, 10.0])
    rows, k = [], 0
    for t in (0.05, 0.1, 0.25, 0.5, 1.0):
        while k < round(t / 0.002):
            s = QR.step(p, s, cmd, 0.002)
            k += 1
        e = Q.to_euler(QR.att(s))
        rows.append(['%.2f' % t, '%.4f' % s[12],
                     '%.4f' % (tz / p['Jzz'] * t),
                     '%.3f' % math.degrees(e[2]),
                     '%.1e' % max(abs(e[0]), abs(e[1])),
                     '%.1e' % (s[2] - 10.0)])
    ctx.table('p04_yawsim', ['t[s]', 'r 모델[rad/s]', 'τz/Jzz·t',
                             '요[°]', '|롤|,|피치|[rad]', 'Δz[m]'],
              rows, num=(0, 1, 2, 3, 4, 5))


def protocols(ctx):
    """신호 하나가 선 위에 머무는 시간 — 문서의 수로 계산."""
    rows = [['PWM (490 Hz)', '1000–2000', '%.0f' % (1e6 / 490)],
            ['OneShot125', '%.0f–%.0f' % (1000 / 8, 2000 / 8), '—']]
    for kb in (150, 300, 600, 1200):
        rows.append(['DShot%d' % kb, '%.2f' % D.frame_us(kb), '—'])
    ctx.table('p04_proto', ['방식', '신호 길이[µs]', '주기[µs]'], rows,
              num=(1, 2))


def payload(ctx):
    """짐을 더 실으면 — 호버 회전수·일률·시간·추력 대 중량비."""
    p = params.load()
    rows = []
    for extra in (0.0, 0.1, 0.2, 0.3, 0.5, 0.8):
        q = dict(p, m=p['m'] + extra)
        d = params.derived(q)
        twr = d['twr']
        rows.append(['%.1f' % extra, '%.1f' % q['m'],
                     '%.0f' % d['omega_hover'],
                     '%.2f' % (d['omega_hover'] / p['omega_max']),
                     '%.1f' % motor.hover_power(q),
                     '%.1f' % (motor.flight_time(q) / 60),
                     '%.2f' % twr,
                     '%.1f' % math.degrees(math.acos(1 / twr)),
                     '%.1f' % ((twr - 1) * p['g'])])
    ctx.table('p04_payload', ['짐[kg]', 'm[kg]', 'Ω_h', 'Ω_h/Ω_max',
                              '호버[W]', '시간[분]', 'T/W',
                              '수평 유지 최대 기울기[°]',
                              '최대 상승 가속[m/s²]'], rows,
              num=(0, 1, 2, 3, 4, 5, 6, 7, 8))


# 배터리 표의 가정: 기준 기체의 배터리(14.8 V × 1.5 Ah = 22.2 Wh)가
# 150 Wh/kg 이라고 보고 나머지를 '빈 기체' 로 둔다. 185 Wh/kg 은
# PX4 문서가 LiPo 로는 매우 높은 쪽이라고 든 예다.
E_SPEC = 150.0
E_HIGH = 185.0


def battery(ctx):
    p = params.load()
    wh0 = p['batt_V'] * p['batt_Ah']
    dry = p['m'] - wh0 / E_SPEC
    rows = []
    for ah in (0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0):
        wh = p['batt_V'] * ah
        out = ['%.1f' % ah, '%.1f' % wh]
        for e in (E_SPEC, E_HIGH):
            q = dict(p, m=dry + wh / e, batt_Ah=ah)
            out += ['%.3f' % q['m'],
                    '%.1f' % (motor.flight_time(q) / 60)]
        q = dict(p, m=dry + wh / E_SPEC)
        out.append('%.2f' % params.derived(q)['twr'])
        rows.append(out)
    ctx.table('p04_batt', ['Ah', 'Wh', 'm@150[kg]', '시간@150[분]',
                           'm@185[kg]', '시간@185[분]', 'T/W@150'],
              rows, num=(0, 1, 2, 3, 4, 5, 6))
    ctx.text('p04_dry', '빈 기체 = %.3f kg (가정 %d Wh/kg 에서)'
             % (dry, E_SPEC))


def current(ctx):
    """호버·최대 추력에서 전류, C율, 내부 저항 전압 강하(모델)."""
    p = params.load()
    d = params.derived(p)
    r_int = 4 * 0.005                      # 셀마다 5 mΩ × 4셀 (가정)
    rows = []
    for name, t in (('호버', d['T_hover']), ('최대 추력', d['T_max'])):
        pw = 4 * motor.ideal_power(t, p['rho'], d['area']) / (
            p['fm'] * p['eta_e'])
        i = pw / p['batt_V']
        rows.append([name, '%.3f' % t, '%.1f' % pw, '%.2f' % i,
                     '%.1f' % (i / p['batt_Ah']), '%.3f' % (i * r_int),
                     '%.3f' % ((p['batt_V'] - i * r_int) / 4)])
    ctx.table('p04_current', ['상태', '로터 추력[N]', '전기 일률[W]',
                              '전류[A]', 'C율', '강하[V]',
                              '셀 전압[V]'], rows,
              num=(1, 2, 3, 4, 5, 6))


def vibration(ctx):
    """회전 주파수와 불균형 원심력(가정한 불균형 질량)."""
    p = params.load()
    d = params.derived(p)
    rows = []
    for name, w in (('호버', d['omega_hover']),
                    ('최대', p['omega_max'])):
        f = w / (2 * math.pi)
        rpm = w * 60 / (2 * math.pi)
        rows.append([name, '%.0f' % w, '%.0f' % rpm, '%.1f' % f,
                     '%.1f' % (2 * f), '%.0f' % (rpm * 7)])
    ctx.table('p04_freq', ['상태', 'Ω[rad/s]', 'rpm', '회전[Hz]',
                           '날개 지남(2날)[Hz]', 'eRPM(14극)'], rows,
              num=(1, 2, 3, 4, 5))
    w = d['omega_hover']
    rows = []
    for mg_ in (1, 5, 10, 50):
        f = mg_ * 1e-6 * 0.03 * w * w
        rows.append(['%d' % mg_, '%.3f' % f,
                     '%.0f' % (100 * f / d['T_hover'])])
    ctx.table('p04_imbal', ['불균형 질량[mg]', '원심력[N]',
                            '로터 추력 대비[%]'], rows, num=(0, 1, 2))


def kv(ctx):
    """Ω_max 를 무부하로라도 내려면 KV 가 적어도 Ω_max / V.

    전압 셋: 4셀 공칭(params), PX4 문서의 셀당 '가득' 4.05 V 와
    '비행 중 실제 최소' 3.5 V 에 4셀을 곱한 것."""
    p = params.load()
    rows = []
    for name, v in (('가득(4.05 V × 4)', 4.05 * 4),
                    ('공칭(params)', p['batt_V']),
                    ('비행 중 최소(3.5 V × 4)', 3.5 * 4)):
        k = p['omega_max'] / v
        rows.append([name, '%.2f' % v, '%.1f' % k,
                     '%.0f' % (k * 60 / (2 * math.pi))])
    ctx.table('p04_kv', ['배터리 전압', 'V', 'KV 하한[rad/s/V]',
                         'KV 하한[rpm/V]'], rows, num=(1, 2, 3))


def run(ctx):
    captures(ctx)
    frames(ctx)
    radius(ctx)
    density(ctx)
    two_models(ctx)
    yaw(ctx)
    protocols(ctx)
    kv(ctx)
    payload(ctx)
    battery(ctx)
    current(ctx)
    vibration(ctx)
