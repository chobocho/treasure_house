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
    print('  꼭짓점이 그대로 머무는 반복이 생긴다. 이 구현에서는 두 규칙 모두 순환하지')
    print('  않았다(순환은 동률 처리 방식까지 특정해야 재현된다). 그러나 Dantzig 규칙에')
    print('  순환하는 예가 존재한다는 것이 알려져 있고, Bland 규칙은 순환하지 않음이')
    print('  증명되어 있다 — 그래서 실무 구현은 순환이 의심되면 Bland 로 전환한다.\n')


def main():
    demo_degeneracy()


if __name__ == '__main__':
    main()
