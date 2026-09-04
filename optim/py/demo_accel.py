# -*- coding: utf-8 -*-
"""8부 데모 — 모멘텀과 네스테로프 가속: 정말 빠른가, 얼마나 빠른가."""
import math

from py import fmt
from py import funcs
from py import linalg as la
from py import stochastic as st


def demo_iterations():
    print('■ 1. 조건수가 커질수록 가속의 이득이 커진다  (f = 1/2 x^T Q x, Q = diag(1, kappa))')
    rows = [['kappa', '경사하강 반복', '모멘텀 반복', '비율', '이론 sqrt(kappa) 배']]
    for kappa in (10.0, 100.0, 1000.0, 10000.0):
        Q = [[1.0, 0.0], [0.0, kappa]]
        p = funcs.Quadratic(Q)
        x0 = [1.0, 1.0]
        ng = st.count_iters(p, x0, method='gd', tol=1e-8, maxiter=200000)
        nm = st.count_iters(p, x0, method='momentum', tol=1e-8, maxiter=200000)
        rows.append(['%.0f' % kappa, '%d' % ng, '%d' % nm, '%.1f' % (ng / float(nm)),
                     '%.1f' % math.sqrt(kappa)])
    print(fmt.table(rows, align='rrrrr'))
    print("  반복 수의 비율이 sqrt(kappa) 를 대체로 따라간다 — 수렴 인자가 (kappa-1)/(kappa+1)")
    print('  에서 (sqrt(kappa)-1)/(sqrt(kappa)+1) 로 바뀌었기 때문이다(정리 34.1).')
    print('  kappa = 10000 이면 100배 빨라진다.\n')


def demo_bound():
    print('■ 2. 네스테로프의 O(1/k^2) 한계를 실측으로 확인')
    Q = [[1.0, 0.0], [0.0, 100.0]]
    p = funcs.Quadratic(Q, [1.0, 100.0])
    star, L = [1.0, 1.0], 100.0
    fstar = p.f(star)
    R2 = la.dot(star, star)
    acc = st.accelerated(p, [0.0, 0.0], L=L, iters=310, tol=0.0, keep_history=True)
    x = [0.0, 0.0]
    gd = []
    for _ in range(301):
        gd.append(p.f(x) - fstar)
        x = la.axpy(-1.0 / L, p.grad(x), x)
    rows = [['k', '가속법 f-f*', '이론 상한 2LR^2/(k+1)^2', '경사하강 f-f*',
             '이론 상한 LR^2/2k', '가속/경사하강']]
    for k in (5, 10, 25, 50, 100, 200, 300):
        a = acc.history[k]['f'] - fstar
        g = gd[k]
        rows.append(['%d' % k, '%.3e' % a, '%.3e' % (2 * L * R2 / (k + 1) ** 2),
                     '%.3e' % g, '%.3e' % (L * R2 / (2.0 * k)),
                     '%.2e' % (a / g)])
    print(fmt.table(rows, align='rrrrrr'))
    print('  두 방법 모두 각자의 이론 상한 아래에 있다. 마지막 열을 보면 k=100 에서')
    print('  가속법의 오차가 경사하강의 3e-07 배다. 이 문제는 사실 강볼록이라')
    print('  가속법이 O(1/k^2) 를 넘어 선형 수렴으로 들어갔기 때문이다.')
    print('  k=200, 300 에서 오차가 오르내리는 것은 가속법이 단조가 아니기 때문이다.\n')


def demo_nonmonotone():
    print('■ 3. 가속법은 단조 감소하지 않는다')
    Q = [[1.0, 0.0], [0.0, 100.0]]
    p = funcs.Quadratic(Q, [1.0, 100.0])
    fstar = p.f([1.0, 1.0])
    r = st.accelerated(p, [0.0, 0.0], L=100.0, iters=60, tol=0.0, keep_history=True)
    fs = [h['f'] - fstar for h in r.history]
    ups = [k for k in range(len(fs) - 1) if fs[k + 1] > fs[k]]
    rows = [['k', 'f(x_k) - f*', '직전보다 늘었는가']]
    for k in range(0, 40, 2):
        rows.append(['%d' % k, '%.6e' % fs[k],
                     '예' if k > 0 and fs[k] > fs[k - 1] else ''])
    print(fmt.table(rows, align='rrl'))
    print('  60번 반복 중 %d번이 직전보다 커졌다. 모멘텀이 관성으로 최소점을' % len(ups))
    print('  지나쳤다가 되돌아오기 때문이다. "목적값이 줄지 않으면 버그"라는 직관이')
    print('  가속법에서는 틀린다 — 실무에서 이것 때문에 재시작(restart) 기법을 쓴다.')


def main():
    demo_iterations()
    demo_bound()
    demo_nonmonotone()


if __name__ == '__main__':
    main()
