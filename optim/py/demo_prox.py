# -*- coding: utf-8 -*-
"""8부 데모 — 근접경사, 가속, 좌표하강, ADMM: 라쏘를 네 가지로 푼다."""
import math
import random

from py import fmt
from py import linalg as la
from py import stochastic as st


def sparse_data(n=60, d=10, seed=3, noise=0.05, nnz=3):
    rng = random.Random(seed)
    w = [0.0] * d
    for j in range(nnz):
        w[j * 3 % d] = rng.choice([-2.0, -1.5, 1.5, 2.0])
    X = [[rng.gauss(0, 1) for _ in range(d)] for _ in range(n)]
    y = [sum(a * b for a, b in zip(w, X[i])) + rng.gauss(0, noise) for i in range(n)]
    return X, y, w


def demo_sparsity_path():
    print('■ 1. 정칙화 경로 — lambda 를 키우면 계수가 하나씩 정확히 0 이 된다')
    X, y, w = sparse_data()
    true_nz = [j for j, v in enumerate(w) if v != 0.0]
    rows = [['lambda', '0 이 아닌 계수 수', '어느 계수가 살아 있나', '잔차제곱합']]
    for lam in (0.0, 0.5, 2.0, 5.0, 10.0, 20.0, 50.0):
        r = st.ista(X, y, lam=lam, iters=8000)
        nz = [j for j, v in enumerate(r.x) if abs(v) > 1e-8]
        rss = math.fsum((la.dot(X[i], r.x) - y[i]) ** 2 for i in range(len(X)))
        rows.append(['%.1f' % lam, '%d' % len(nz),
                     ', '.join(str(j) for j in nz) if nz else '(전부 0)',
                     '%.4f' % rss])
    print(fmt.table(rows, align='rrlr'))
    print('  진짜 0 이 아닌 계수는 %s 다.' % true_nz)
    print('  lambda 가 적당하면 정확히 그 셋만 살아남는다 — 라쏘가 변수 선택을 한다.')
    print('  lambda 를 더 키우면 살아남은 계수도 0 쪽으로 눌려 잔차가 커진다.\n')


def demo_four_solvers():
    print('■ 2. 같은 라쏘 문제, 네 가지 알고리즘  (lambda = 2.0)')
    X, y, w = sparse_data()
    lam = 2.0
    ref = st.lasso_coordinate(X, y, lam=lam, iters=2000)
    rows = [['알고리즘', '반복', '목적값', '기준해와의 거리', '한 반복의 비용']]
    specs = [
        ('ISTA (근접경사)', lambda: st.ista(X, y, lam=lam, iters=2000), 2000, 'O(nd)'),
        ('FISTA (가속)', lambda: st.fista(X, y, lam=lam, iters=2000), 2000, 'O(nd)'),
        ('좌표하강', lambda: st.lasso_coordinate(X, y, lam=lam, iters=200), 200, 'O(nd) / 전체 훑기'),
        ('ADMM', lambda: st.lasso_admm(X, y, lam=lam, rho=1.0, iters=300), 300,
         'O(d^2) + 미리 분해'),
    ]
    for name, fn, it, cost in specs:
        r = fn()
        rows.append([name, '%d' % it, '%.10f' % r.fx,
                     '%.2e' % la.norm(la.vsub(r.x, ref.x)), cost])
    print(fmt.table(rows, align='lrrrl'))
    print('  네 방법이 같은 해로 모인다 — 라쏘는 볼록이므로 최적해가 유일하다')
    print('  (설계행렬의 열이 독립이면). 다른 것은 "가는 길"과 비용 구조뿐이다.\n')


def demo_convergence_speed():
    print('■ 3. ISTA vs FISTA — 조건수가 나쁜 문제에서의 수렴 곡선')
    rng = random.Random(5)
    d, n = 8, 40
    base = [[rng.gauss(0, 1) for _ in range(2)] for _ in range(n)]
    X = [[(base[i][0] if j < 4 else base[i][1]) + 0.02 * rng.gauss(0, 1)
          for j in range(d)] for i in range(n)]
    wt = [1.0, 0, 0, 0, -1.5, 0, 0, 0]
    y = [sum(a * b for a, b in zip(wt, X[i])) + rng.gauss(0, 0.05) for i in range(n)]
    print('  설계행렬 조건수 kappa(X) = %.1f' % la.cond(X))
    a = st.ista(X, y, lam=0.3, iters=4000, keep_history=True)
    b = st.fista(X, y, lam=0.3, iters=4000, keep_history=True)
    best = min(min(a.history), min(b.history))
    rows = [['반복 k', 'ISTA 목적값 - 최적', 'FISTA 목적값 - 최적', 'ISTA/FISTA']]
    for k in (10, 50, 100, 500, 1000, 2000, 4000):
        ea = a.history[k - 1] - best
        eb = b.history[k - 1] - best
        rows.append(['%d' % k, '%.3e' % ea, '%.3e' % eb,
                     '%.1f' % (ea / eb) if eb > 0 else '-'])
    print(fmt.table(rows, align='rrrr'))
    print('  FISTA 는 같은 반복 수에서 훨씬 낮은 목적값에 도달한다. 비용은 같다 —')
    print('  둘 다 한 반복에 기울기 한 번과 prox 한 번이다. 차이는 "어디서 기울기를')
    print('  재는가" 뿐이다. 가속은 공짜에 가깝다.')


def main():
    demo_sparsity_path()
    demo_four_solvers()
    demo_convergence_speed()


if __name__ == '__main__':
    main()
