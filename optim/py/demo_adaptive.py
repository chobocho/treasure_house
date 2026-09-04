# -*- coding: utf-8 -*-
"""8부 데모 — 적응 보폭(AdaGrad·Adam)과 분산 감소(SVRG)."""
import math
import random

from py import fmt
from py import funcs
from py import linalg as la
from py import stochastic as st


def demo_scale():
    print('■ 1. 좌표마다 스케일이 다를 때 — AdaGrad 가 하는 일')
    print('  f = 1/2 (x1-1)^2 + 200 (x2-1)^2  : 두 좌표의 곡률이 400배 다르다')
    Q = [[1.0, 0.0], [0.0, 400.0]]
    p = funcs.Quadratic(Q, [1.0, 400.0])
    star = [1.0, 1.0]
    rows = [['방법', '반복', '최종 x', '거리 ||x-x*||', '비고']]
    x = [0.0, 0.0]
    for _ in range(500):
        x = la.axpy(-2.0 / (1.0 + 400.0), p.grad(x), x)     # 최적 고정 보폭
    rows.append(['경사하강 (최적 고정보폭)', '500', '(%.4f, %.4f)' % tuple(x),
                 '%.3e' % la.norm(la.vsub(x, star)), 'alpha = 2/(L+mu)'])
    for step in (0.1, 1.0, 5.0):
        r = st.adagrad_full(p, [0.0, 0.0], step=step, iters=500)
        rows.append(['AdaGrad (step=%.1f)' % step, '500', '(%.4f, %.4f)' % tuple(r.x),
                     '%.3e' % la.norm(la.vsub(r.x, star)), '좌표별 보폭'])
    print(fmt.table(rows, align='lrlrl'))
    print('  AdaGrad 는 곡률이 큰 좌표의 보폭을 자동으로 줄인다 — 기울기 제곱합이')
    print('  빨리 쌓이기 때문이다. 스케일 조정을 손으로 하지 않아도 되는 것이 장점이고,')
    print('  분모가 단조 증가해 보폭이 영원히 줄어드는 것이 단점이다.\n')


def demo_adam():
    print('■ 2. Adam 의 편향 보정이 하는 일')
    rng = random.Random(4)
    n, d = 200, 5
    w = [1.0, -2.0, 0.5, 0.3, -1.0]
    X = [[rng.gauss(0, 1) for _ in range(d)] for _ in range(n)]
    y = [sum(a * b for a, b in zip(w, X[i])) + rng.gauss(0, 0.1) for i in range(n)]
    p = st.LeastSquaresBatch(X, y)
    rows = [['에폭', '보정 있음: ||x||', '보정 있음: f', '보정 없음: ||x||', '보정 없음: f']]
    for ep in (1, 2, 3, 5, 10, 30, 100):
        a = st.adam(p, [0.0] * d, step=0.05, epochs=ep, seed=1, bias_correct=True)
        b = st.adam(p, [0.0] * d, step=0.05, epochs=ep, seed=1, bias_correct=False)
        rows.append(['%d' % ep, '%.4f' % la.norm(a.x), '%.6f' % a.fx,
                     '%.4f' % la.norm(b.x), '%.6f' % b.fx])
    print(fmt.table(rows, align='rrrrr'))
    print('  초기 몇 에폭에서 보정 있는 쪽의 손실이 절반 수준이다 — m, v 가 0 에서')
    print('  출발한 탓에 보정이 없으면 첫 걸음들의 추정이 0 쪽으로 치우치기 때문이다.')
    print('  (1 - beta^k) 로 나누면 그 치우침이 정확히 상쇄된다.')
    print('  에폭 10 을 넘으면 beta^k -> 0 이라 두 방식이 사실상 같아진다.\n')


def demo_svrg():
    print('■ 3. 분산 감소 — SVRG 는 고정 보폭으로도 수렴한다')
    rng = random.Random(15)
    n, d = 200, 5
    w = [1.0, -2.0, 0.5, 0.3, -1.0]
    X = [[rng.gauss(0, 1) for _ in range(d)] for _ in range(n)]
    y = [sum(a * b for a, b in zip(w, X[i])) + rng.gauss(0, 0.3) for i in range(n)]
    p = st.LeastSquaresBatch(X, y)
    star = p.exact_solution()
    rows = [['방법', '기울기 계산 횟수', '거리 ||x-x*||', '보폭']]
    for ep in (10, 40, 100):
        s = st.sgd(p, [0.0] * d, step=lambda k: 0.02, epochs=ep, seed=1)
        v = st.svrg(p, [0.0] * d, step=0.02, epochs=ep // 2, seed=1)
        rows.append(['SGD (고정 0.02), %d에폭' % ep, '%d' % (ep * n),
                     '%.6f' % la.norm(la.vsub(s.x, star)), '고정'])
        rows.append(['SVRG (고정 0.02), %d에폭' % (ep // 2), '%d' % (ep // 2 * n * 2),
                     '%.6f' % la.norm(la.vsub(v.x, star)), '고정'])
    print(fmt.table(rows, align='lrrl'))
    print('  SGD 는 고정 보폭에서 어느 지점부터 더 나아가지 못한다 — 잡음이 만든 공이다.')
    print('  SVRG 는 같은 보폭으로 계속 줄여 나간다. 주기마다 전체 기울기를 한 번 더')
    print('  계산하는 대가로 분산이 0 으로 줄기 때문이다(정리 35.4).')


def main():
    demo_scale()
    demo_adam()
    demo_svrg()


if __name__ == '__main__':
    main()
