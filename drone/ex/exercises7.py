# -*- coding: utf-8 -*-
"""7부 '손으로 풀어 보기' 의 답 — 장마다 한 문제.

손으로 푼 뒤 이 출력과 맞춰 본다. 답을 내는 식은 시뮬레이터 모듈을
쓰고, ex/tests/test_exercises.py 가 정의에서 따로 계산한 값과 대조한다.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'py'))
from droneshow import linalg  # noqa: E402
from droneshow import rigidbody as RB  # noqa: E402
from droneshow import vec3 as V  # noqa: E402


def ch1():
    a, b = [1.0, 2.0, 2.0], [2.0, -1.0, 0.0]
    return {'|a|': V.norm(a), 'a·b': V.dot(a, b), 'a×b': V.cross(a, b)}


def ch2():
    m = [[1.0, 2.0, 0.0], [0.0, 1.0, 3.0], [2.0, 0.0, 1.0]]
    return {'det': V.det3(m), 'x': linalg.solve(m, [3.0, 4.0, 3.0])}


def ch3():
    x = 0.1
    return {'sin 0.1': math.sin(x), '근사 0.1': x,
            '오차': x - math.sin(x), '한계 x³/6': x ** 3 / 6}


def ch4():
    tau = 0.03
    return {'95% 시간[s]': -tau * math.log(0.05), '3τ[s]': 3 * tau}


def ch5():
    b, c = 2.0, 5.0
    d = b * b - 4 * c
    return {'근': '%g ± %gi' % (-b / 2, math.sqrt(-d) / 2)}


def ch6():
    r, f = [0.0849, 0.0849, 0.0], [0.0, 0.0, 1.2]
    return {'τ = r×F': V.cross(r, f)}


def ch7():
    f = lambda s: [-s[0]]
    return {'오일러': RB.euler(f, [1.0], 0.5)[0],
            'RK4': RB.rk4(f, [1.0], 0.5)[0], '참값': math.exp(-0.5)}


def ch8():
    return {'k*': 4 / (2 * 2), 'Var((X+Y)/2)': 0.25 * 1 + 0.25 * 1}


def pad(s, w):
    """한글은 두 칸 — 칸 수로 맞춘다."""
    return s + ' ' * (w - sum(2 if ord(c) > 0x1100 else 1 for c in s))


if __name__ == '__main__':
    for k, fn in enumerate([ch1, ch2, ch3, ch4, ch5, ch6, ch7, ch8], 1):
        for name, val in fn().items():
            if isinstance(val, float):
                val = ('%.3e' % val if 0 < abs(val) < 1e-3
                       else '%.6f' % val)
            elif isinstance(val, list):
                val = '(' + ', '.join('%.4f' % v for v in val) + ')'
            print('[%d장] %s %s' % (k, pad(name, 14), val))
