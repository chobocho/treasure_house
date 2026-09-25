# -*- coding: utf-8 -*-
"""벡터 계산 한 판 — 7부 1장의 예를 손 대신 기계로 (droneshow.vec3).

두 벡터 a = (3, 0, 4), b = (1, 2, 2) 로 크기·내적·사이각·외적을 구하고,
라그랑주 항등식 |a×b|² + (a·b)² = |a|²|b|² 을 수로 확인한다.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'py'))
from droneshow import vec3 as V  # noqa: E402

a, b = [3.0, 0.0, 4.0], [1.0, 2.0, 2.0]
c = V.cross(a, b)
theta = math.degrees(math.acos(V.dot(a, b) / (V.norm(a) * V.norm(b))))

if __name__ == '__main__':
    print('a + b      =', V.add(a, b))
    print('|a|, |b|   =', V.norm(a), V.norm(b))
    print('a · b      =', V.dot(a, b))
    print('사이각     = %.4f 도' % theta)
    print('a × b      =', c)
    print('(a×b)·a    =', V.dot(c, a), ' (a×b)·b =', V.dot(c, b))
    print('b × a      =', V.cross(b, a))
    lhs = V.dot(c, c) + V.dot(a, b) ** 2
    print('|a×b|²+(a·b)² =', lhs, ' |a|²|b|² =',
          V.dot(a, a) * V.dot(b, b))
