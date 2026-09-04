# -*- coding: utf-8 -*-
"""9부 데모 — 비평활 문제에서 열경사법이 치르는 대가."""
import math
import random

from py import convex as cx
from py import fmt
from py import global_opt as go
from py import linalg as la
from py import stochastic as st


def demo_rate():
    print('■ 1. 열경사법의 수렴률은 O(1/sqrt(k)) 다   f(x) = |x1| + 2|x2|')
    f = lambda x: abs(x[0]) + 2.0 * abs(x[1])
    sg = lambda x: [1.0 if x[0] > 0 else (-1.0 if x[0] < 0 else 0.0),
                    2.0 if x[1] > 0 else (-2.0 if x[1] < 0 else 0.0)]
    rows = [['반복 k', '최선 f(x)', '이론 상한 RG/sqrt(k)', '비율']]
    R = la.norm([1.0, 1.0])
    G = math.sqrt(1.0 + 4.0)
    for k in (10, 100, 1000, 10000, 100000):
        r = go.subgradient(f, sg, [1.0, 1.0],
                           step=lambda t, k=k: R / (G * math.sqrt(k)), iters=k)
        bound = R * G / math.sqrt(k)
        rows.append(['%d' % k, '%.6f' % r.fx, '%.6f' % bound,
                     '%.3f' % (r.fx / bound)])
    print(fmt.table(rows, align='rrrr'))
    print('  최선값이 이론 상한 아래에서 1/sqrt(k) 를 따라 줄어든다. 반복을 100배')
    print('  늘려야 오차가 10배 준다 — 경사하강의 O(1/k) 보다 확연히 느리다.')
    print('  이것이 비평활성의 대가이고, 근접경사법이 존재하는 이유다.\n')


def demo_nonmonotone():
    print('■ 2. 열경사법은 단조 감소하지 않는다 — 하강 방향이 아닐 수 있다')
    f = lambda x: abs(x[0]) + 0.1 * x[0] ** 2
    sg = lambda x: [(1.0 if x[0] > 0 else -1.0) + 0.2 * x[0]]
    r = go.subgradient(f, sg, [1.0], step=lambda k: 0.3, iters=30, keep_history=True)
    rows = [['k', 'f(x)', '지금까지의 최선', '직전보다 늘었나']]
    prev = None
    for h in r.history[:16]:
        rows.append(['%d' % h['k'], '%.6f' % h['f'], '%.6f' % h['best'],
                     '예' if prev is not None and h['f'] > prev else ''])
        prev = h['f']
    print(fmt.table(rows, align='rrrl'))
    ups = sum(1 for i in range(len(r.history) - 1)
              if r.history[i + 1]['f'] > r.history[i]['f'])
    print('  30번 중 %d번이 직전보다 커졌다. 고정 보폭이면 0 주위를 계속 넘나든다.' % ups)
    print('  그래서 열경사법은 "지금까지의 최선"을 따로 들고 다녀야 하고,')
    print('  라인서치를 쓸 수도 없다 — 어느 방향이 좋은지 국소 정보로는 모른다.\n')


def demo_prox_vs_subgrad():
    print('■ 3. 같은 라쏘 문제: 열경사법 vs 근접경사법')
    rng = random.Random(3)
    n, d = 50, 8
    w = [1.5, 0.0, -2.0, 0.0, 0.0, 0.0, 0.8, 0.0]
    X = [[rng.gauss(0, 1) for _ in range(d)] for _ in range(n)]
    y = [sum(a * b for a, b in zip(w, X[i])) + rng.gauss(0, 0.05) for i in range(n)]
    lam = 2.0

    def F(x):
        r = [la.dot(X[i], x) - y[i] for i in range(n)]
        return 0.5 * math.fsum(v * v for v in r) + lam * math.fsum(abs(v) for v in x)

    def SG(x):
        r = [la.dot(X[i], x) - y[i] for i in range(n)]
        g = la.matvec(la.transpose(X), r)
        return [g[j] + lam * (1.0 if x[j] > 0 else (-1.0 if x[j] < 0 else 0.0))
                for j in range(d)]

    L = 1.0
    XtX = la.matmul(la.transpose(X), X)
    vals, _ = la.eigh(XtX)
    L = vals[-1]
    rows = [['반복', '열경사 목적값', '열경사 0인 계수', 'ISTA 목적값', 'ISTA 0인 계수']]
    for it in (100, 1000, 10000):
        sgr = go.subgradient(F, SG, [0.0] * d,
                             step=lambda k: 1.0 / (L * math.sqrt(k + 1)), iters=it)
        isr = st.ista(X, y, lam=lam, iters=it)
        rows.append(['%d' % it, '%.8f' % sgr.fx,
                     '%d' % sum(1 for v in sgr.x if abs(v) < 1e-8),
                     '%.8f' % isr.fx,
                     '%d' % sum(1 for v in isr.x if abs(v) < 1e-8)])
    print(fmt.table(rows, align='rrrrr'))
    print('  열경사법은 계수를 정확히 0 으로 만들지 못한다 — 0 을 지나쳐 넘나들 뿐이다.')
    print('  근접경사법은 연성 문턱이 |v| <= t 구간을 통째로 0 으로 보내므로 정확히 0 이 된다.')
    print('  목적값도 근접경사 쪽이 훨씬 빨리 내려간다. 비평활 항을 근사하지 않고')
    print('  그대로 다루는 것이 핵심이다.')


def main():
    demo_rate()
    demo_nonmonotone()
    demo_prox_vs_subgrad()


if __name__ == '__main__':
    main()
