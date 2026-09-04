# -*- coding: utf-8 -*-
"""3부 데모 — L-BFGS 의 기억 용량이 하는 일"""
import math

from py import fmt
from py import funcs
from py import linalg as la
from py import unconstrained as uc


def demo_lbfgs_memory():
    print('■ 6. L-BFGS 의 기억 용량 m 이 하는 일  (로젠브록 20차원)')
    p = funcs.Rosenbrock(20)
    rows = [['방법', '반복', 'grad 호출', '최종 f', '최종 ||g||', '방향 계산 비용']]
    r = uc.minimize(p, p.x0, method='bfgs', tol=1e-6, maxiter=5000)
    rows.append(['BFGS (n x n 행렬)', '%d' % r.nit, '%d' % r.ngev,
                 '%.4e' % r.fx, '%.1e' % r.gnorm, 'O(n^2) = 400'])
    for m in (1, 3, 5, 10, 20):
        r = uc.minimize(p, p.x0, method='lbfgs', memory=m, tol=1e-6, maxiter=5000)
        rows.append(['L-BFGS m=%d' % m, '%d' % r.nit, '%d' % r.ngev,
                     '%.4e' % r.fx, '%.1e' % r.gnorm, 'O(mn) = %d' % (m * 20)])
    print(fmt.table(rows, align='lrrrrl'))
    print('  m 을 키우면 반복 수가 BFGS 에 가까워지지만 한 반복의 비용과 메모리가 늘어난다.')
    print('  n 이 10^6 이면 BFGS 의 O(n^2) = 10^12 개 원소는 아예 담을 수 없다 —')
    print('  L-BFGS 가 대규모 학습의 표준이 된 이유다. 실무에서는 m = 5~20 을 쓴다.\n')


def main():
    demo_lbfgs_memory()


if __name__ == '__main__':
    main()
