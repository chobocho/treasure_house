# -*- coding: utf-8 -*-
"""9부 '손으로 풀어 보기' 의 답.

ex/tests/test_exercises.py 가 정의에서 따로 계산한 값과 대조한다.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'py'))
from droneshow import pid  # noqa: E402


def ch2():
    """시상수 0.03 s 인 1차 계를 P 이득 k = 4 로 닫으면."""
    tau, k = 0.03, 4.0
    return {'닫힌 시상수[s]': tau / (1 + k), '정상 오차': 1 / (1 + k)}


def ch3():
    """kp = 9, kd = 1.8 인 PD — ζ, ωn, 초과량."""
    z, wn = pid.second_order(9.0, 1.8)
    return {'ζ': z, 'ωn': wn, '초과량': pid.overshoot(z)}


def ch4():
    """외란 −0.5, kp = 4 인 PD 의 정상 오차."""
    return {'정상 오차': 0.5 / 4.0}


def ch5():
    """s³ + 2s² + 3s + ki 가 안정한 ki 의 범위."""
    return {'ki 상한': 2.0 * 3.0, 'ki=5 안정': pid.routh3(2, 3, 5),
            'ki=7 안정': pid.routh3(2, 3, 7)}


def ch6():
    """안쪽 b = 20, 바깥 k = 2 — 느린 극."""
    return {'느린 극': pid.cascade_poles(2.0, 20.0)[1]}


def ch7():
    """k = 3 인 자세 P 법칙, 오차 120° 가 30° 로 줄 때까지."""
    k, a, b = 3.0, math.radians(120), math.radians(30)
    t = math.log(math.tan(a / 4) / math.tan(b / 4)) / k
    return {'걸린 시간[s]': t}


def ch9():
    """τ = 0.01 s 필터가 100 rad/s 잡음을 얼마로 줄이나."""
    return {'진폭비': pid.lowpass_gain(100.0, 0.01)}


def pad(s, w):
    """한글은 두 칸 — 칸 수로 맞춘다."""
    return s + ' ' * (w - sum(2 if ord(c) > 0x1100 else 1 for c in s))


if __name__ == '__main__':
    for k, fn in ((2, ch2), (3, ch3), (4, ch4), (5, ch5), (6, ch6),
                  (7, ch7), (9, ch9)):
        for name, val in fn().items():
            val = str(val) if isinstance(val, bool) else '%.4f' % val
            print('[%d장] %s %s' % (k, pad(name, 16), val))
