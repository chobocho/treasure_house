# -*- coding: utf-8 -*-
"""3부 데모 — Armijo 와 Wolfe 는 무엇이 다른가"""
import math

from py import fmt
from py import funcs
from py import linalg as la
from py import unconstrained as uc


def demo_linesearch():
    print('■ 7. Armijo 와 Wolfe 는 무엇이 다른가')
    Q = [[4.0, 0.0], [0.0, 1.0]]
    q = funcs.Quadratic(Q)
    x = [1.0, 1.0]
    fx, g = q.f(x), q.grad(x)
    d = [-v for v in g]
    gtd = la.dot(g, d)
    exact = -gtd / la.dot(d, la.matvec(Q, d))
    a_arm, n_arm = uc.backtracking(q.f, x, fx, g, d)
    a_wol, n_wol = uc.wolfe(q.f, q.grad, x, fx, g, d)
    rows = [['라인서치', 'alpha', '호출', 'f(x+ad)', '|phi\'(a)| / |phi\'(0)|', 'Armijo', '곡률']]
    for name, a, ncall in (('Armijo (backtracking)', a_arm, n_arm),
                           ('강 Wolfe (c2=0.9)', a_wol, n_wol),
                           ('정확한 라인서치', exact, 0)):
        xn = la.axpy(a, d, x)
        arm = q.f(xn) <= fx + 1e-4 * a * gtd
        ratio = abs(la.dot(q.grad(xn), d)) / abs(gtd)
        rows.append([name, '%.6f' % a, '%d' % ncall, '%.6f' % q.f(xn), '%.4f' % ratio,
                     '예' if arm else '아니오', '예' if ratio <= 0.9 else '아니오'])
    print(fmt.table(rows, align='lrrrrll'))
    print('  이차함수의 정확한 해는 alpha* = -g^T d / d^T Q d = %.6f 다.' % exact)
    print('  Armijo 는 값만 보므로 alpha=1 에서 반씩 줄이다 처음 통과한 곳에서 멈춘다.')
    print('  Wolfe 는 기울기까지 보고 정확한 최소점 쪽으로 더 다가간다.\n')

    print('  알고리즘 전체에서의 차이 (로젠브록 2차원, BFGS, tol = 1e-8):')
    p = funcs.Rosenbrock(2)
    rows = [['라인서치', '반복', 'f 호출', 'grad 호출', '최종 ||g||', '수렴']]
    for name, ls in (('Armijo', 'armijo'), ('강 Wolfe', 'wolfe')):
        r = uc.minimize(p, p.x0, method='bfgs', line_search=ls, tol=1e-8, maxiter=5000)
        rows.append([name, '%d' % r.nit, '%d' % r.nfev, '%d' % r.ngev,
                     '%.2e' % r.gnorm, '예' if r.converged else '아니오'])
    print(fmt.table(rows, align='lrrrrl'))
    print('  이 문제에서는 반복 수가 같고 기울기 호출만 두 배가 됐다 — Wolfe 가 언제나')
    print('  이기는 것은 아니다. 그럼에도 Wolfe 를 쓰는 이유는 곡률조건이 s^T y > 0 을')
    print('  보장하고, 그것이 BFGS 근사의 양의 정부호(따라서 하강 방향)를 지키기 때문이다.')


def main():
    demo_linesearch()


if __name__ == '__main__':
    main()
