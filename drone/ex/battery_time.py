# -*- coding: utf-8 -*-
"""비행시간 = 에너지 / 일률 (T2) — 식 하나와 시뮬레이터 적분 하나.

1) 식: t = C·V·η_사용 / (P_호버 + P_LED)
2) 적분: 물리 모델로 60초 떠 있으며 모터의 기계 일률 Σ kQ·Ω³
   (반토크 × 회전 속도)을 더한다.
3) 무게를 바꾸면 비행시간이 어떻게 바뀌나 — 반으로 줄여도 두 배가
   아니다(호버 일률 ∝ m^(3/2), 그리고 LED 는 그대로).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'py'))
from droneshow import motor, params  # noqa: E402
from droneshow import quadrotor as QR  # noqa: E402


def mech_power_hover(p, secs=60.0, dt=0.002):
    """호버 비행의 평균 기계 일률 [W] — Σ kQ Ω³ 를 시간 평균."""
    oh = params.derived(p)['omega_hover']
    s = QR.hover_state(p, [0.0, 0.0, 10.0])
    e = 0.0
    for _ in range(round(secs / dt)):
        s = QR.step(p, s, [oh] * 4, dt)
        e += sum(p['kQ'] * w ** 3 for w in QR.motors(s)) * dt
    return e / secs


if __name__ == '__main__':
    p = params.load()
    print('식: 비행시간 %.1f 분 (호버 %.1f W + LED %.1f W)'
          % (motor.flight_time(p) / 60, motor.hover_power(p),
             p['led_W']))
    pm = mech_power_hover(p)
    print('적분: 기계 일률 %.2f W → 전기 %.2f W (효율 %.1f)'
          % (pm, pm / p['eta_e'], p['eta_e']))
    print('무게[kg]  비행시간[분]  비율')
    t0 = motor.flight_time(p)
    for k in (0.5, 0.75, 1.0, 1.25):
        q = dict(p, m=p['m'] * k)
        t = motor.flight_time(q)
        print('%7.3f  %11.2f  %5.2f' % (q['m'], t / 60, t / t0))
