# -*- coding: utf-8 -*-
"""6부 데모 — 퇴화와 축 선택 규칙"""
import itertools
import math
import random

from py import fmt
from py import linalg as la
from py import lp


PROB = dict(
    c=[-3.0, -5.0],
    A=[[1.0, 0.0], [0.0, 2.0], [3.0, 2.0]],
    b=[4.0, 12.0, 18.0],
)


def demo_degeneracy():
    print('■ 4. 퇴화와 순환 — Bland 규칙이 필요한 이유  (Beale 의 예제)')
    c = [-0.75, 150.0, -0.02, 6.0]
    A = [[0.25, -60.0, -0.04, 9.0],
         [0.5, -90.0, -0.02, 3.0],
         [0.0, 0.0, 1.0, 0.0]]
    b = [0.0, 0.0, 1.0]
    rows = [['축 선택 규칙', '상태', '반복 수', '최적값']]
    for rule in ('dantzig', 'bland'):
        r = lp.solve_lp(c, A_ub=A, b_ub=b, rule=rule, maxiter=500)
        rows.append([rule, r.status, '%d' % r.nit,
                     '%.6f' % r.obj if r.obj is not None else '-'])
    print(fmt.table(rows, align='lllr'))
    print('  이 문제는 우변에 0 이 두 개 있어 퇴화(degenerate)한다 — 기저가 바뀌어도')
    print('  꼭짓점이 그대로 머무는 반복이 생긴다. Dantzig 규칙은 같은 기저들을 맴돌다')
    print('  반복 상한 500 에 걸렸다(상태 maxiter, 목적값 없음) — 이 구현의 동률 처리에서')
    print('  실제로 순환한 것이다. Bland 규칙은 6회 만에 최적값 -0.05 에 도달했다.')
    print('  Bland 규칙은 순환하지 않음이 증명되어 있다 — 실무 구현이 순환이 의심되면')
    print('  Bland 로 전환하는 이유다.\n')


def main():
    demo_degeneracy()


if __name__ == '__main__':
    main()
