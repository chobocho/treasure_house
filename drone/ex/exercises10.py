# -*- coding: utf-8 -*-
"""10부 '손으로 풀어 보기' 의 답.

ex/tests/test_exercises.py 가 정의에서 따로 계산한 값과 대조한다.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'py'))
from droneshow import assign, poly, profile  # noqa: E402


def ch2():
    """최소 저크 β(u) = 10u³ − 15u⁴ + 6u⁵ 의 가운데 속도 β′(½)."""
    return {"β′(½)": poly.val(poly.deriv(poly.rest_to_rest(3), 1), 0.5)}


def ch3():
    """거리 6 m, 최고 속도 3 m/s, 가속도 2 m/s² — 최단 시간."""
    return {'T[s]': profile.trapezoid(6.0, 3.0, 2.0)['T']}


def ch7():
    """비용 [[4,1,3],[2,0,5],[3,2,2]] 의 최소 할당."""
    perm, total, _ops = assign.hungarian([[4, 1, 3], [2, 0, 5],
                                          [3, 2, 2]])
    return {'할당': perm, '합': total}


def ch8():
    """반지름 6 m 원 위 12 대 — 이웃 간격."""
    return {'간격[m]': 2 * 6.0 * math.sin(math.pi / 12)}


def pad(s, w):
    """한글은 두 칸 — 칸 수로 맞춘다."""
    return s + ' ' * (w - sum(2 if ord(c) > 0x1100 else 1 for c in s))


if __name__ == '__main__':
    for k, fn in ((2, ch2), (3, ch3), (7, ch7), (8, ch8)):
        for name, val in fn().items():
            val = str(val) if isinstance(val, list) else '%.4f' % val
            print('[%d장] %s %s' % (k, pad(name, 10), val))
