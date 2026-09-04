# -*- coding: utf-8 -*-
"""6부 데모 — 심플렉스 vs 내부점"""
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


def demo_simplex_vs_interior():
    print('■ 5. 심플렉스 vs 내부점 — 반복 수가 어떻게 늘어나는가')
    rng = random.Random(7)
    rows = [['변수 n', '제약 m', '심플렉스 반복', '내부점 반복', '목적값 차이']]
    for n, m in ((5, 5), (10, 10), (20, 20), (30, 30), (40, 40)):
        A = [[rng.uniform(0.2, 2.0) for _ in range(n)] for _ in range(m)]
        b = [rng.uniform(5.0, 20.0) for _ in range(m)]
        c = [-rng.uniform(0.5, 3.0) for _ in range(n)]
        rs = lp.solve_lp(c, A_ub=A, b_ub=b)
        ri = lp.solve_lp(c, A_ub=A, b_ub=b, method='interior')
        diff = abs(rs.obj - ri.obj) if (rs.obj is not None and ri.obj is not None) else float('nan')
        rows.append(['%d' % n, '%d' % m, '%d' % rs.nit, '%d' % ri.nit, '%.2e' % diff])
    print(fmt.table(rows, align='rrrrr'))
    print('  심플렉스의 반복 수는 문제 크기에 따라 늘어난다(실무에서는 대략 2m~3m).')
    print('  내부점은 거의 일정하다 — 이론 상한이 O(sqrt(n) log(1/eps)) 이고 실측은')
    print('  대개 20~50회다. 대신 한 반복이 훨씬 비싸다(정규방정식 m x m 을 푼다).\n')


def main():
    demo_simplex_vs_interior()


if __name__ == '__main__':
    main()
