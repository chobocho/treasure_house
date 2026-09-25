# -*- coding: utf-8 -*-
"""기준 쿼드로터의 호버 추력·유도 속도·일률 (모멘텀 이론, T1, 4부).

손으로 계산한 식과 시뮬레이터(droneshow.motor)의 값을 나란히 찍는다.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'py'))
from droneshow import motor, params  # noqa: E402

p = params.load()
T = p['m'] * p['g'] / 4                        # 로터 하나의 추력 [N]
A = math.pi * p['r_prop'] ** 2                 # 원판 넓이 [m²]
v = math.sqrt(T / (2 * p['rho'] * A))          # 유도 속도 [m/s]
P1 = T * v                                     # 이상 일률 = 추력 × 속도

if __name__ == '__main__':
    print('로터 하나 추력 T      %8.4f N' % T)
    print('원판 넓이 A           %8.5f m^2' % A)
    print('유도 속도 v           %8.4f m/s' % v)
    print('이상 일률 T·v         %8.4f W' % P1)
    print('  motor.ideal_power   %8.4f W'
          % motor.ideal_power(T, p['rho'], A))
    print('네 로터, 성능지수 %.1f·효율 %.1f' % (p['fm'], p['eta_e']))
    print('  전기 일률           %8.2f W' % motor.hover_power(p))
