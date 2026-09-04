# -*- coding: utf-8 -*-
"""6부 데모 — 최적해는 꼭짓점에 있다"""
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


def demo_vertices():
    print('■ 1. 최적해는 꼭짓점에 있다   max 3x + 5y  s.t. x<=4, 2y<=12, 3x+2y<=18, x,y>=0')
    c, A, b = PROB['c'], PROB['A'], PROB['b']
    rows = A + [[-1.0, 0.0], [0.0, -1.0]]           # x>=0, y>=0 을 포함해 전부 5개 반평면
    rhs = b + [0.0, 0.0]
    pts = []
    for i, j in itertools.combinations(range(len(rows)), 2):
        M = [rows[i], rows[j]]
        try:
            p = la.solve(M, [rhs[i], rhs[j]])
        except la.SingularMatrix:
            continue
        if all(la.dot(rows[k], p) <= rhs[k] + 1e-9 for k in range(len(rows))):
            if all(abs(p[0] - q[0]) + abs(p[1] - q[1]) > 1e-9 for q in pts):
                pts.append(p)
    pts.sort(key=lambda p: (la.dot(c, p)))
    trows = [['꼭짓점 (x, y)', '목적값 3x+5y', '활성 제약 수', '비고']]
    for p in pts:
        act = sum(1 for k in range(len(rows)) if abs(la.dot(rows[k], p) - rhs[k]) < 1e-9)
        trows.append(['(%.2f, %.2f)' % (p[0] + 0.0, p[1] + 0.0), '%.2f' % (-la.dot(c, p) + 0.0),
                      '%d' % act, '<- 최적' if p is pts[0] else ''])
    print(fmt.table(trows, align='lrrl'))
    print('  꼭짓점이 %d 개뿐이므로 전부 세어 볼 수도 있다. 그러나 변수가 n 개,' % len(pts))
    print('  제약이 m 개면 꼭짓점 후보는 C(m, n) 개다 — n=20, m=40 이면 1.4e11 개다.')
    print('  심플렉스는 그중 좋아지는 방향으로만 걷는다 — 다음 표가 그 발자국이다.\n')


def main():
    demo_vertices()


if __name__ == '__main__':
    main()
