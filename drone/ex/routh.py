# -*- coding: utf-8 -*-
"""라우스 판정 — 3차 특성다항식 s³ + a2 s² + a1 s + a0 (T16, 9부).

모든 계수가 양수이고 a2·a1 > a0 이면 근이 모두 왼쪽 반평면에 있다.
경계 너머로 이득을 올리면 흔들림이 커진다 — 적분으로 확인한다.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'py'))
from droneshow import pid  # noqa: E402
from droneshow import rigidbody as RB  # noqa: E402


def swing(kp, kd, ki, secs=60.0, dt=0.002):
    """이중 적분기 + PID 의 마지막 5초 동안 |x| 의 최댓값."""
    f = lambda s: [s[1], -kp * s[0] - kd * s[1] - ki * s[2], s[0]]
    s, top = [1.0, 0.0, 0.0], 0.0
    n = round(secs / dt)
    for k in range(n):
        s = RB.rk4(f, s, dt)
        if k * dt > secs - 5:
            top = max(top, abs(s[0]))
    return top


if __name__ == '__main__':
    kp, kd = 3.0, 2.0
    print('s³ + %.0f s² + %.0f s + ki — 경계 ki = %.0f'
          % (kd, kp, kd * kp))
    print('   ki   라우스   마지막 5초 |x| 최대')
    for ki in (2.0, 4.0, 5.5, 5.9, 6.1, 6.5, 8.0):
        ok = '안정' if pid.routh3(kd, kp, ki) else '불안정'
        print('%5.1f   %-5s  %10.4f' % (ki, ok, swing(kp, kd, ki)))
