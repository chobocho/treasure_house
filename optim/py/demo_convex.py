# -*- coding: utf-8 -*-
"""2부 데모 — 볼록성을 기계로 의심해 보고, 투영이 실제로 최단 거리임을 확인한다."""
import math
import random

from py import convex as cx
from py import fmt
from py import funcs
from py import linalg as la


def demo_jensen():
    print('■ 1. 젠센 부등식으로 볼록성을 의심해 본다  (무작위 현 2000개)')
    cases = [
        ('x^2 + y^2', 2, lambda v: v[0] ** 2 + v[1] ** 2, '볼록'),
        ('max(x, y)', 2, lambda v: max(v[0], v[1]), '볼록'),
        ('|x| + |y|', 2, lambda v: abs(v[0]) + abs(v[1]), '볼록(미분 불가)'),
        ('exp(x) + exp(-y)', 2, lambda v: math.exp(v[0]) + math.exp(-v[1]), '볼록'),
        ('log-sum-exp', 3, lambda v: math.log(sum(math.exp(t) for t in v)), '볼록'),
        ('x*y', 2, lambda v: v[0] * v[1], '볼록 아님'),
        ('sin(3x) + y^2/10', 2, lambda v: math.sin(3 * v[0]) + 0.1 * v[1] ** 2, '볼록 아님'),
        ('rosenbrock', 2, funcs.Rosenbrock(2).f, '볼록 아님'),
        ('sqrt(|x|)', 1, lambda v: math.sqrt(abs(v[0])), '볼록 아님'),
    ]
    rows = [['함수', '차원', '최악의 젠센 간격', '판정', '참값']]
    for name, n, f, truth in cases:
        g, x, y, t = cx.worst_jensen(f, n, trials=2000, seed=17, scale=2.0)
        rows.append([name, str(n), '%.4e' % g,
                     '볼록으로 보임' if g >= -1e-9 else '반례 발견', truth])
    print(fmt.table(rows, align='llrll'))
    print('  간격이 음수면 그 자리에 반례가 있다는 뜻이다. 통과는 증명이 아니라')
    print('  "반례를 못 찾았다"일 뿐이라는 점을 잊지 말 것.\n')

    g, x, y, t = cx.worst_jensen(lambda v: v[0] * v[1], 2, trials=2000, seed=17)
    print('  찾아낸 반례 (f = xy):')
    print('    x = [%.4f, %.4f],  y = [%.4f, %.4f],  t = %.4f' % (x[0], x[1], y[0], y[1], t))
    z = [t * a + (1 - t) * b for a, b in zip(x, y)]
    print('    t f(x) + (1-t) f(y) = %.6f   <   f(tx+(1-t)y) = %.6f'
          % (t * x[0] * x[1] + (1 - t) * y[0] * y[1], z[0] * z[1]))
    print()


def demo_curvature():
    print('■ 2. 헤세의 고윳값으로 본 강볼록 상수 mu 와 평활 상수 L')
    rng = random.Random(0)
    rows = [['문제', '표본', 'mu = min lam_min', 'L = max lam_max', 'kappa = L/mu', '해석']]
    lg = funcs.LogisticRegression.toy(seed=7, n=200, d=4, lam=1e-2)
    items = [
        ('quadratic diag(3,7)', funcs.Quadratic([[3.0, 0.0], [0.0, 7.0]]), 2),
        ('logistic (lam=1e-2)', lg, 4),
        ('rosenbrock(2)', funcs.Rosenbrock(2), 2),
        ('himmelblau', funcs.Himmelblau(), 2),
    ]
    for name, p, n in items:
        pts = [[rng.uniform(-2, 2) for _ in range(n)] for _ in range(60)]
        mu, L = cx.curvature_range(p, pts)
        k = (L / mu) if mu > 0 else float('inf')
        rows.append([name, '60점',
                     '%.4f' % mu, '%.4f' % L,
                     ('%.1f' % k) if mu > 0 else '-',
                     '강볼록' if mu > 1e-12 else ('볼록' if mu >= -1e-12 else '볼록 아님')])
    print(fmt.table(rows, align='llrrrl'))
    print('  로지스틱 회귀의 mu 가 정칙화 계수 lam 에 가까운 것에 주목. 데이터 항의')
    print('  헤세는 양의 반정부호일 뿐이라, 강볼록성은 전적으로 (lam/2)||w||^2 이 만든다.\n')


def demo_projection():
    print('■ 3. 투영 — 정말로 가장 가까운 점인가')
    x = [0.8, -0.3, 0.9, 0.1]
    p = cx.proj_simplex(x)
    print('  x        = [%s]' % ', '.join('%7.4f' % v for v in x))
    print('  P(x)     = [%s]   sum = %.12f' % (', '.join('%7.4f' % v for v in p), sum(p)))
    rng = random.Random(1)
    dp = la.norm(la.vsub(x, p))
    best = float('inf')
    for _ in range(200000):
        w = [rng.random() for _ in range(4)]
        s = sum(w)
        q = [v / s for v in w]
        best = min(best, la.norm(la.vsub(x, q)))
    print('  ||x - P(x)||                    = %.12f' % dp)
    print('  단체 위 무작위 20만 점 중 최단   = %.12f  (투영보다 가까운 점은 없다)' % best)
    print()

    print('  변분 부등식 (x - P(x))^T (q - P(x)) <= 0 을 무작위 20만 점에서 확인:')
    worst = -1e300
    for _ in range(200000):
        w = [rng.random() for _ in range(4)]
        s = sum(w)
        q = [v / s for v in w]
        worst = max(worst, la.dot(la.vsub(x, p), la.vsub(q, p)))
    print('    최댓값 = %.3e   (0 이하여야 한다 — 이것이 투영의 정의다)' % worst)
    print()

    print('  비확장성 ||P(x) - P(y)|| <= ||x - y|| 를 무작위 5만 쌍에서 확인:')
    ratio = 0.0
    for _ in range(50000):
        a = [rng.uniform(-3, 3) for _ in range(4)]
        b = [rng.uniform(-3, 3) for _ in range(4)]
        ratio = max(ratio, la.norm(la.vsub(cx.proj_simplex(a), cx.proj_simplex(b)))
                    / max(1e-300, la.norm(la.vsub(a, b))))
    print('    최대 비율 = %.12f  (1 이하여야 한다)' % ratio)
    print()


def demo_soft_threshold():
    print('■ 4. 연성 문턱 함수 — l1 이 계수를 정확히 0 으로 보내는 장치')
    xs = [-1.5, -0.4, -0.05, 0.0, 0.05, 0.4, 1.5]
    rows = [['x'] + ['%.2f' % v for v in xs]]
    for t in (0.0, 0.1, 0.5):
        rows.append(['prox t=%.1f' % t] + ['%.2f' % v for v in cx.soft_threshold(xs, t)])
    print(fmt.table(rows, align='l' + 'r' * len(xs)))
    print('  |x| <= t 인 성분은 정확히 0 이 된다. 이것이 라쏘의 희소성이다 (8부).')


def main():
    demo_jensen()
    demo_curvature()
    demo_projection()
    demo_soft_threshold()


if __name__ == '__main__':
    main()
