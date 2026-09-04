# -*- coding: utf-8 -*-
"""6부 데모 — 쌍대성과 그림자 가격"""
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


def demo_duality():
    print('■ 3. 쌍대성과 그림자 가격')
    c, A, b = PROB['c'], PROB['A'], PROB['b']
    r = lp.solve_lp(c, A_ub=A, b_ub=b)
    slack = la.vsub(b, la.matvec(A, r.x))
    rows = [['제약', '우변 b', '여유 slack', '쌍대변수 y', 'y*slack', 'b 를 +1 했을 때 실제 변화']]
    for i in range(len(b)):
        bb = list(b)
        bb[i] += 1.0
        r2 = lp.solve_lp(c, A_ub=A, b_ub=bb)
        rows.append(['%d' % (i + 1), '%.1f' % b[i], '%.4f' % slack[i],
                     '%.4f' % r.dual[i], '%.2e' % abs(r.dual[i] * slack[i]),
                     '%.4f' % (-(r2.obj - r.obj))])
    print(fmt.table(rows, align='rrrrrr'))
    print('  여유가 있는 제약의 쌍대변수는 0 이다 — 상보여유(5부 정리 20.3 (4)).')
    print('  쌍대변수가 양수인 제약이 병목이고, 그 값이 "한 단위 늘렸을 때의 이득"이다.')
    print('  마지막 열이 실제로 b 를 1 늘려 다시 푼 결과인데, 쌍대변수와 정확히 같다.')
    print('  원문제 최적값 %.4f = -b^T y = %.4f — 강쌍대성.\n'
          % (-r.obj, la.dot(b, r.dual)))


def main():
    demo_duality()


if __name__ == '__main__':
    main()
