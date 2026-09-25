# -*- coding: utf-8 -*-
"""8부 '손으로 풀어 보기' 의 답 — 장마다 한 문제.

손으로 푼 뒤 이 출력과 맞춰 본다. ex/tests/test_exercises.py 가
정의에서 따로 계산한 값과 대조한다.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'py'))
from droneshow import mixer, params  # noqa: E402
from droneshow import quat as Q  # noqa: E402
from droneshow import rigidbody as RB  # noqa: E402
from droneshow import vec3 as V  # noqa: E402

P = params.load()


def ch1():
    """ENU 의 (동 3, 북 4, 위 5) 를 NED 로."""
    return {'NED': V.matvec(V.ENU_TO_NED, [3.0, 4.0, 5.0])}


def ch2():
    """J = (1, 2, 3), ω = (1, 1, 0) 일 때 자이로 항과 에너지."""
    j, w = [1.0, 2.0, 3.0], [1.0, 1.0, 0.0]
    return {'ω×Jω': V.cross(w, RB.ang_momentum(j, w)),
            '에너지': RB.rot_energy(j, w)}


def ch3():
    """기준 쿼드로터의 호버 회전수 [rpm]."""
    om = params.derived(P)['omega_hover']
    return {'호버 rpm': om * 60 / (2 * math.pi)}


def ch4():
    """추력 (1.3, 1.2, 1.1, 1.2) N 이 내는 u = (F, τx, τy, τz)."""
    return {'u': mixer.forward(P, [1.3, 1.2, 1.1, 1.2])}


def ch5():
    """피치 10° 로 기운 채 추력 mg — 수평 가속도."""
    q = Q.from_euler(0.0, math.radians(10), 0.0)
    z = Q.rotate(q, [0.0, 0.0, 1.0])
    return {'x 가속도': P['g'] * z[0], 'gθ': P['g'] * math.radians(10)}


def ch6():
    """원 운동(반지름 2 m, 0.8 rad/s)에 필요한 기울기 [°]."""
    a = 2.0 * 0.8 ** 2
    tilt = math.degrees(math.atan(a / P['g']))
    return {'구심 가속도': a, '기울기[°]': tilt}


def pad(s, w):
    """한글은 두 칸 — 칸 수로 맞춘다."""
    return s + ' ' * (w - sum(2 if ord(c) > 0x1100 else 1 for c in s))


if __name__ == '__main__':
    for k, fn in enumerate([ch1, ch2, ch3, ch4, ch5, ch6], 1):
        for name, val in fn().items():
            if isinstance(val, list):
                val = '(' + ', '.join('%.4f' % (v if abs(v) > 5e-5
                                                else 0.0)
                                      for v in val) + ')'
            else:
                val = '%.4f' % val
            print('[%d장] %s %s' % (k, pad(name, 12), val))
