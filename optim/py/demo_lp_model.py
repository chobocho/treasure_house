# -*- coding: utf-8 -*-
"""6부 데모 — LP 로 푸는 l1 회귀"""
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


def demo_l1_vs_l2():
    print('■ 6. LP 로 푸는 l1 회귀 — 이상치에 강하다')
    xs = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    ys = [1.0, 3.0, 5.0, 7.0, 9.0, 11.0, 13.0]        # y = 1 + 2x
    A = [[1.0, x] for x in xs]
    rows = [['자료', 'l2 (최소제곱)', 'l1 (LP)', 'l2 오차', 'l1 오차']]
    from py import leastsq as ls
    for label, yy in (('원본', list(ys)), ('한 점을 +20', [y + (20.0 if i == 3 else 0.0)
                                                          for i, y in enumerate(ys)])):
        x2 = ls.solve_qr(A, yy)
        x1, _ = lp.l1_regression(A, yy)
        rows.append([label, '(%.3f, %.3f)' % (x2[0], x2[1]), '(%.3f, %.3f)' % (x1[0], x1[1]),
                     '%.4f' % math.hypot(x2[0] - 1, x2[1] - 2),
                     '%.4f' % math.hypot(x1[0] - 1, x1[1] - 2)])
    print(fmt.table(rows, align='lllrr'))
    print('  l2 는 이상치 하나에 절편이 1 -> 3.857 로 밀린다. l1 은 꿈쩍하지 않는다.')
    print('  |r| 은 미분 불가능하지만 LP 로 다시 적으면 그 비평활성이 사라진다 —')
    print('  "문제를 다시 적어" 어려움을 없애는 기법의 대표적인 예다.')


def main():
    demo_l1_vs_l2()


if __name__ == '__main__':
    main()
