# -*- coding: utf-8 -*-
"""4부 데모 — 기저 선택·가중·로버스트·행렬 없는 해법."""
import math
import random

from py import fmt
from py import leastsq as ls
from py import linalg as la


def demo_basis():
    print('■ 1. 같은 모형, 다른 기저 — 단항 vs 체비쇼프  (구간 [0,1] 균등 30점)')
    xs = [i / 29.0 for i in range(30)]
    ys = [math.sin(3.0 * x) + 0.5 * x for x in xs]
    rows = [['차수', 'cond(단항)', 'cond(체비쇼프)', '비율', '단항 잔차', '체비쇼프 잔차']]
    for deg in (4, 8, 12, 16, 20):
        M = [[x ** k for k in range(deg + 1)] for x in xs]
        C = ls.chebyshev_design(xs, deg)
        cm = ls.solve_qr(M, ys)
        cc = ls.solve_qr(C, ys)
        rows.append(['%d' % deg, '%.2e' % la.cond(M), '%.2e' % la.cond(C),
                     '%.0f배' % (la.cond(M) / la.cond(C)),
                     '%.2e' % la.norm(ls.residual(M, cm, ys)),
                     '%.2e' % la.norm(ls.residual(C, cc, ys))])
    print(fmt.table(rows, align='rrrrrr'))
    print('  두 기저는 같은 함수공간을 표현하므로 잔차는 사실상 같다. 그런데 조건수는')
    print('  차수 20 에서 10^13 배 넘게 벌어진다. 단항 기저의 3.3e15 는 배정밀도의')
    print('  한계(1/eps ~ 4.5e15)에 닿은 값이라, 계수를 신뢰할 수 없다는 뜻이다.\n')


def demo_weighted():
    print('■ 2. 가중 최소제곱 — 신뢰도가 다른 측정 섞기')
    xs = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
    true = [1.0, 2.0]                               # y = 1 + 2x
    ys = [true[0] + true[1] * x for x in xs]
    ys[4] += 3.0                                    # 5번째 측정만 크게 틀렸다
    A = [[1.0, x] for x in xs]
    rows = [['가중', '절편', '기울기', '틀린 점의 잔차']]
    for name, w in (('전부 1 (보통 최소제곱)', [1.0] * 6),
                    ('틀린 점만 1/100', [1, 1, 1, 1, 0.01, 1]),
                    ('틀린 점만 1/10000', [1, 1, 1, 1, 1e-4, 1])):
        x = ls.weighted(A, ys, [float(v) for v in w])
        r = ls.residual(A, x, ys)
        rows.append([name, '%.4f' % x[0], '%.4f' % x[1], '%.4f' % r[4]])
    rows.append(['참값', '1.0000', '2.0000', '-'])
    print(fmt.table(rows, align='lrrr'))
    print('  가중치를 낮추면 그 점이 해를 끌어당기지 못한다. 다만 어떤 점이 못 믿을')
    print('  점인지 미리 알아야 한다 — 모를 때 쓰는 것이 다음의 로버스트 회귀다.\n')


def demo_huber():
    print('■ 3. 이상치가 있을 때 — 최소제곱 vs 후버(IRLS)')
    rng = random.Random(9)
    xs = [i * 0.5 for i in range(20)]
    ys = [1.0 + 2.0 * x + rng.gauss(0, 0.15) for x in xs]
    A = [[1.0, x] for x in xs]
    rows = [['이상치 수', '최소제곱 (절편, 기울기)', '후버 (절편, 기울기)',
             '최소제곱 오차', '후버 오차']]
    for nout in (0, 1, 2, 4):
        yy = list(ys)
        for i in range(nout):
            yy[3 + 5 * i] += 25.0
        xo = ls.solve_qr(A, yy)
        xh = ls.huber_irls(A, yy, delta=0.5)
        eo = math.hypot(xo[0] - 1.0, xo[1] - 2.0)
        eh = math.hypot(xh[0] - 1.0, xh[1] - 2.0)
        rows.append(['%d' % nout, '(%.3f, %.3f)' % (xo[0], xo[1]),
                     '(%.3f, %.3f)' % (xh[0], xh[1]), '%.4f' % eo, '%.4f' % eh])
    print(fmt.table(rows, align='rllrr'))
    print('  이상치 하나만으로 최소제곱은 크게 흔들린다. 제곱 손실이 큰 잔차에')
    print('  제곱으로 반응하기 때문이다. 후버는 |r| > delta 부터 절댓값처럼 굴어')
    print('  영향을 선형으로 제한한다 — 볼록성은 그대로 유지된다.\n')


def demo_cgls():
    print('■ 4. 행렬을 만들지 않는 해법 — CGLS')
    rows = [['문제', 'cond(A)', 'QR 오차', 'CGLS 반복', 'CGLS 오차', '정규방정식']]
    e = 1e-9
    A1 = [[1.0, 1.0], [e, 0.0], [0.0, e]]
    b1 = [2.0, 0.0, 0.0]
    ex1 = 2.0 / (2.0 + e * e)
    xq = ls.solve_qr(A1, b1)[0]
    xc, k = ls.solve_cg(A1, b1, tol=1e-14, maxiter=50)
    try:
        ls.solve_normal(A1, b1)
        ne = '풀림'
    except la.SingularMatrix:
        ne = '특이'
    rows.append(['Lauchli eps=1e-9', '%.1e' % la.cond(A1), '%.2e' % abs(xq - ex1),
                 '%d' % k, '%.2e' % abs(xc[0] - ex1), ne])

    rng = random.Random(2)
    n = 12
    xs = [i / 39.0 for i in range(40)]
    A2 = ls.chebyshev_design(xs, n - 1)
    xt = [rng.gauss(0, 1) for _ in range(n)]
    b2 = la.matvec(A2, xt)
    xq2 = ls.solve_qr(A2, b2)
    xc2, k2 = ls.solve_cg(A2, b2, tol=1e-14)
    rows.append(['체비쇼프 40x12', '%.1e' % la.cond(A2),
                 '%.2e' % la.norm(la.vsub(xq2, xt)), '%d' % k2,
                 '%.2e' % la.norm(la.vsub(xc2, xt)), '풀림'])
    print(fmt.table(rows, align='lrrrrl'))
    print('  CGLS 는 A·v 와 A^T·w 두 곱만 쓴다. A 를 명시적으로 갖고 있지 않아도')
    print('  (희소행렬이거나 합성곱 같은 연산자여도) 최소제곱을 풀 수 있다는 뜻이다.')


def main():
    demo_basis()
    demo_weighted()
    demo_huber()
    demo_cgls()


if __name__ == '__main__':
    main()
