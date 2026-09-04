# -*- coding: utf-8 -*-
"""3부 데모 — 같은 문제를 여섯 가지 방법으로 푼다"""
import math

from py import fmt
from py import funcs
from py import linalg as la
from py import unconstrained as uc


def demo_methods():
    print('■ 3. 같은 문제, 다른 방법  (로젠브록 2차원, 출발 (-1.2, 1), tol = 1e-8)')
    p = funcs.Rosenbrock(2)
    rows = [['방법', '반복', 'f 호출', 'grad 호출', '최종 f', '최종 ||g||', '수렴']]
    specs = [('경사하강 + Armijo', dict(method='gd', line_search='armijo', maxiter=200000)),
             ('비선형 CG (PR+)', dict(method='cg', maxiter=20000)),
             ('BFGS', dict(method='bfgs', maxiter=2000)),
             ('L-BFGS (m=5)', dict(method='lbfgs', memory=5, maxiter=2000)),
             ('수정 뉴턴', dict(method='newton', maxiter=2000)),
             ('신뢰영역 (Steihaug)', dict(method='tr', maxiter=2000))]
    for name, kw in specs:
        r = uc.minimize(p, p.x0, tol=1e-8, **kw)
        rows.append([name, '%d' % r.nit, '%d' % r.nfev, '%d' % r.ngev,
                     '%.3e' % r.fx, '%.2e' % r.gnorm, '예' if r.converged else '아니오'])
    print(fmt.table(rows, align='lrrrrrl'))
    print('  반복 수만 보면 뉴턴이 압도적이지만, 한 반복의 비용이 다르다 —')
    print('  뉴턴은 헤세 n^2 개와 O(n^3) 분해가 필요하고 BFGS 는 기울기만 쓴다.\n')


def main():
    demo_methods()


if __name__ == '__main__':
    main()
