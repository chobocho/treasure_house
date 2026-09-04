# -*- coding: utf-8 -*-
"""3부 데모 — 보폭과 조건수가 수렴을 어떻게 지배하는가"""
import math

from py import fmt
from py import funcs
from py import linalg as la
from py import unconstrained as uc


def demo_stepsize():
    print('■ 1. 보폭 alpha 와 발산의 경계  (f = 1/2 (4x^2 + y^2), L = 4, mu = 1)')
    Q = [[4.0, 0.0], [0.0, 1.0]]
    p = funcs.Quadratic(Q)
    rows = [['alpha', 'alpha*L', '이론상 증폭 |1-alpha*L|', '200회 뒤 ||x||', '결과']]
    for a in (0.1, 0.25, 0.4, 0.49, 0.5, 0.51, 0.6):
        r = uc.minimize(p, [1.0, 1.0], method='gd', step=a, tol=0.0, maxiter=200)
        amp = abs(1.0 - a * 4.0)
        nx = la.norm(r.x)
        rows.append(['%.2f' % a, '%.2f' % (a * 4), '%.3f' % amp,
                     ('%.3e' % nx) if math.isfinite(nx) else 'inf',
                     '수렴' if amp < 1 else ('진동' if amp == 1 else '발산')])
    print(fmt.table(rows, align='rrrrl'))
    print('  경계는 정확히 alpha = 2/L = 0.5 다. 그 위로는 가장 가파른 좌표가 증폭된다.')
    print('  정리 3부-2.2 가 요구하는 alpha <= 1/L 은 안전판이고, 실제 경계는 2/L 이다.\n')


def demo_rate_vs_kappa():
    print('■ 2. 조건수와 수렴 속도  (최적 고정보폭 alpha = 2/(L+mu))')
    rows = [['kappa', '실측 수렴 인자', '이론 (k-1)/(k+1)', '상대 오차', '1e-6 까지 반복 수']]
    for kappa in (2.0, 5.0, 20.0, 100.0, 1000.0):
        Q = [[1.0, 0.0], [0.0, kappa]]
        p = funcs.Quadratic(Q)
        r = uc.minimize(p, [1.0, 1.0], method='gd', step=2.0 / (1.0 + kappa),
                        tol=0.0, maxiter=80, keep_history=True)
        e0 = la.norm(r.history[0]['x'])
        e1 = la.norm(r.history[-1]['x'])
        k = len(r.history) - 1
        obs = (e1 / e0) ** (1.0 / k)
        th = (kappa - 1) / (kappa + 1)
        need = uc.minimize(p, [1.0, 1.0], method='gd', step=2.0 / (1.0 + kappa),
                           tol=1e-6, maxiter=200000)
        rows.append(['%.0f' % kappa, '%.8f' % obs, '%.8f' % th,
                     '%.1e' % (abs(obs - th) / th), '%d' % need.nit])
    print(fmt.table(rows, align='rrrrr'))
    print('  실측이 이론과 소수점 여덟 자리까지 같다. 반복 수가 kappa 에 비례해 늘어난다.\n')


def main():
    demo_stepsize()
    demo_rate_vs_kappa()


if __name__ == '__main__':
    main()
