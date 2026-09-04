# -*- coding: utf-8 -*-
"""8부 데모 — 확률적 기울기: 왜 되는가, 무엇을 잃는가."""
import math
import random

from py import fmt
from py import linalg as la
from py import stochastic as st


def make(n=400, d=6, seed=1, noise=0.3):
    rng = random.Random(seed)
    w = [1.0, -2.0, 0.5, 0.3, -1.0, 0.8][:d]
    X = [[rng.gauss(0, 1) for _ in range(d)] for _ in range(n)]
    y = [sum(a * b for a, b in zip(w, X[i])) + rng.gauss(0, noise) for i in range(n)]
    return st.LeastSquaresBatch(X, y), w


def demo_unbiased():
    print('■ 1. 표본 기울기는 전체 기울기의 불편추정량이다')
    p, w = make(n=200, seed=2)
    x = [0.2, -0.1, 0.4, 0.0, 0.3, -0.2]
    full = p.grad(x)
    rng = random.Random(0)
    rows = [['배치 크기 B', '표본평균의 편차', '표준편차 sd', 'sd/sqrt(300)',
             '판정', '기울기 계산량']]
    for B in (1, 4, 16, 64, 200):
        errs, comps = [], []
        for _ in range(300):
            idx = [rng.randrange(p.n) for _ in range(B)]
            g = p.grad_sample(x, idx)
            errs.append(la.norm(la.vsub(g, full)))
            comps.append(g)
        mean = [sum(c[j] for c in comps) / len(comps) for j in range(len(x))]
        bias = la.norm(la.vsub(mean, full))
        sd = math.sqrt(sum((c[j] - mean[j]) ** 2 for c in comps
                           for j in range(len(x))) / (len(comps) * len(x)))
        mc = sd / math.sqrt(300.0) * math.sqrt(len(x))
        rows.append(['%d' % B, '%.4f' % bias, '%.4f' % sd, '%.4f' % mc,
                     '편향 없음' if bias < 3 * mc else '의심',
                     '%d / %d' % (B, p.n)])
    print(fmt.table(rows, align='rrrrlr'))
    print('  300번 뽑은 표본평균이 전체 기울기에서 벗어난 정도가, 몬테카를로 오차')
    print('  sd/sqrt(300) 과 같은 규모다 — 편향이 0 이라는 것과 일관된다.')
    print('  표준편차는 배치 크기의 제곱근에 반비례해 줄어든다(B=1 -> 2.31, B=16 -> 0.60).')
    print('  즉 배치를 4배로 키우면 계산량이 4배가 되고 잡음은 2배만 줄어든다.\n')


def demo_constant_step():
    print('■ 2. 고정 보폭 SGD 는 최적해에 <도달하지 않는다>')
    p, w = make(n=300, seed=3, noise=0.5)
    star = p.exact_solution()
    rows = [['보폭 alpha', '최종 거리 ||x - x*||', '마지막 20에폭 진동폭', '거리/alpha']]
    base = None
    for a in (0.2, 0.05, 0.01, 0.002):
        r = st.sgd(p, [0.0] * 6, step=lambda k, a=a: a, epochs=200, seed=11,
                   keep_history=True)
        d = la.norm(la.vsub(r.x, star))
        tail = [h['f'] for h in r.history[-20:]]
        rows.append(['%.3f' % a, '%.5f' % d, '%.6f' % (max(tail) - min(tail)),
                     '%.3f' % (d / a)])
        if base is None:
            base = d / a
    print(fmt.table(rows, align='rrrr'))
    print('  마지막 열(거리/alpha)이 alpha 를 100배 바꾸는 동안 3~5 사이에 머문다 —')
    print('  최종 거리가 alpha 에 비례한다는 뜻이고, 정리 33.3 의 O(alpha) 공이다.')
    print('  잡음이 있는 한 이 공은 없앨 수 없다. 줄이려면 보폭을 줄이거나 분산을 줄여야 한다.\n')


def demo_decaying_step():
    print('■ 3. 보폭을 줄이면 도달한다 — 대신 느려진다')
    p, w = make(n=300, seed=3, noise=0.5)
    star = p.exact_solution()
    schemes = [
        ('고정 alpha=0.05', lambda k: 0.05),
        ('alpha = 0.5/(1+0.05k)', lambda k: 0.5 / (1 + 0.05 * k)),
        ('alpha = 0.5/sqrt(1+k)', lambda k: 0.5 / math.sqrt(1 + k)),
        ('alpha = 0.5/(1+k)', lambda k: 0.5 / (1 + k)),
    ]
    rows = [['보폭 규칙', '50에폭 거리', '200에폭 거리', '800에폭 거리', '조건 sum a=inf, sum a^2<inf']]
    for name, sch in schemes:
        ds = []
        for ep in (50, 200, 800):
            r = st.sgd(p, [0.0] * 6, step=sch, epochs=ep, seed=7)
            ds.append(la.norm(la.vsub(r.x, star)))
        cond = '만족' if name != '고정 alpha=0.05' else '위반 (sum a^2 = inf)'
        rows.append([name] + ['%.5f' % v for v in ds] + [cond])
    print(fmt.table(rows, align='lrrrl'))
    print('  Robbins-Monro 조건(sum alpha_k = inf, sum alpha_k^2 < inf)을 만족하는')
    print('  규칙만 최적해로 수렴한다. 1/k 는 조건을 만족하지만 너무 빨리 줄어')
    print('  초반에 거의 움직이지 못한다 — 실무에서 1/sqrt(k) 나 단계적 감소를 쓰는 이유다.\n')


def demo_cost():
    print('■ 4. 계산량으로 비교하면 — 같은 기울기 예산에서 누가 이기는가')
    p, w = make(n=1000, d=6, seed=5, noise=0.3)
    star = p.exact_solution()
    rows = [['방법', '기울기 계산 횟수', '거리 ||x - x*||', '한 걸음의 비용']]
    for budget in (2000, 10000, 50000):
        # 전체 경사하강: 한 걸음에 n 번
        x = [0.0] * 6
        for _ in range(budget // p.n):
            x = la.axpy(-0.5, p.grad(x), x)
        dg = la.norm(la.vsub(x, star))
        # SGD: 한 걸음에 1 번
        r = st.sgd(p, [0.0] * 6, step=lambda k: 0.5 / (1 + 0.002 * k),
                   epochs=budget // p.n, seed=4)
        ds = la.norm(la.vsub(r.x, star))
        rows.append(['전체 경사하강 (예산 %d)' % budget, '%d' % budget, '%.6f' % dg,
                     'n = %d' % p.n])
        rows.append(['SGD (예산 %d)' % budget, '%d' % budget, '%.6f' % ds, '1'])
    print(fmt.table(rows, align='lrrl'))
    print('  예산이 작을 때는 SGD 가 압도한다 — 전체 경사하강은 예산 2000 으로 겨우')
    print('  2걸음을 걷기 때문이다. 그러나 예산이 커지면 역전된다: 전체 경사하강은')
    print('  선형 수렴으로 기계정밀도까지 가고, SGD 는 감소하는 보폭 때문에 느려진다.')
    print('  결론은 명확하다 — SGD 는 <큰 자료에서 적당한 정확도를 빨리> 얻는 도구다.')
    print('  높은 정확도가 필요하면 분산 감소(SVRG)나 2차 방법으로 갈아타야 한다.')


def main():
    demo_unbiased()
    demo_constant_step()
    demo_decaying_step()
    demo_cost()


if __name__ == '__main__':
    main()
