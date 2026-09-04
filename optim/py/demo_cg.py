# -*- coding: utf-8 -*-
"""3부 데모 — 켤레기울기의 유한 종료"""
import math

from py import fmt
from py import funcs
from py import linalg as la
from py import unconstrained as uc


def demo_cg_exact():
    print('■ 5. 켤레기울기는 n 차원 이차문제를 n 번 안에 정확히 푼다')
    rows = [['n', 'CG 반복', '잔차 ||Ax-b||', 'LU 해와의 차이', 'kappa(A)']]
    for n in (3, 5, 8, 12):
        A = [[1.0 / (i + j + 1) for j in range(n)] for i in range(n)]
        for i in range(n):
            A[i][i] += 1.0
        b = [1.0] * n
        x, k = uc.cg_solve(A, b, tol=1e-14, maxiter=n)
        y = la.solve(A, b)
        rows.append(['%d' % n, '%d' % k,
                     '%.2e' % la.norm(la.vsub(la.matvec(A, x), b)),
                     '%.2e' % la.norm(la.vsub(x, y)),
                     '%.1f' % la.cond(A)])
    print(fmt.table(rows, align='rrrrr'))
    print('  행렬을 분해하지 않고 곱셈만 썼는데 직접 해와 같은 답이 나온다.\n')


def main():
    demo_cg_exact()


if __name__ == '__main__':
    main()
