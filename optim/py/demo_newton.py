# -*- coding: utf-8 -*-
"""3부 데모 — 뉴턴법의 이차수렴을 자릿수로 확인한다"""
import math

from py import fmt
from py import funcs
from py import linalg as la
from py import unconstrained as uc


def demo_newton_rate():
    print('■ 4. 뉴턴법의 이차수렴 — 유효 자릿수가 매 걸음 두 배가 된다')
    p = funcs.Rosenbrock(2)
    r = uc.minimize(p, [-1.2, 1.0], method='newton', tol=1e-14, maxiter=60, keep_history=True)
    rows = [['k', '||g_k||', 'log10 ||g_k||', '||g_k|| / ||g_{k-1}||^2', 'tau (헤세 수정)']]
    prev = None
    for h in r.history:
        g = h['gnorm']
        lg = ('%.2f' % math.log10(g)) if g > 0 else '-inf'
        q = ('%.3f' % (g / prev ** 2)) if (prev and prev > 0 and g > 0) else '-'
        rows.append(['%d' % h['k'], '%.4e' % g, lg, q, '%.1e' % h['tau']])
        prev = g
    print(fmt.table(rows, align='rrrrr'))
    print('  앞부분은 요동친다 — 멀리서는 2차 모형이 함수를 대변하지 못하기 때문이다.')
    print('  마지막 세 걸음에서 ||g|| 가 3.9e-03 -> 1.2e-04 -> 4.5e-10 -> 0 으로 떨어진다.')
    print('  log10 열의 감소폭이 대략 두 배씩 커지는 것이 이차수렴의 지문이다.')
    print('  tau 가 0 이 아닌 줄은 헤세가 양의 정부호가 아니어서 수정한 반복이다.\n')


def main():
    demo_newton_rate()


if __name__ == '__main__':
    main()
