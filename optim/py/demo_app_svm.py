# -*- coding: utf-8 -*-
"""13부 데모 — SVM: 쌍대로 가면 무엇이 달라지는가."""
import math

from py import fmt
from py import linalg as la
from py.apps import svm as S


def demo_dual():
    print('■ 1. 쌍대 문제를 투영경사법으로 푼다  (선형분리 가능한 2차원 자료 40개)')
    X, y = S.separable_data(n=40, seed=2, margin=1.5)
    rows = [['C', '반복', 'sum(a_i y_i)', '서포트 벡터 수', '마진 위', '마진 안쪽',
             '오분류 수']]
    for C in (0.1, 1.0, 10.0):
        a, Q = S.train_dual(X, y, C=C, iters=2000)
        f, b = S.decision_function(X, y, a, C)
        sv = S.support_vectors(a, C)
        wrong = sum(1 for i in range(len(X)) if y[i] * f(X[i]) < 0)
        rows.append(['%.1f' % C, '2000',
                     '%.2e' % abs(math.fsum(a[i] * y[i] for i in range(len(a)))),
                     '%d / %d' % (sv['total'], len(X)),
                     '%d' % len(sv['margin']), '%d' % len(sv['bound']),
                     '%d' % wrong])
    print(fmt.table(rows, align='rrrrrrr'))
    print('  제약 sum(a_i y_i) = 0 이 기계정밀도까지 지켜진다 — 투영이 매 걸음')
    print('  실행가능집합 안으로 되돌리기 때문이다(5부 22장). 상자 제약 0 <= a <= C')
    print('  와 초평면 하나뿐이라 투영이 값싸다는 것이 쌍대로 가는 이유 중 하나다.\n')


def demo_support_vectors():
    print('■ 2. 서포트 벡터 — 상보여유가 정의한다')
    X, y = S.separable_data(n=30, seed=5, margin=1.2)
    C = 10.0
    a, _ = S.train_dual(X, y, C=C, iters=3000)
    f, b = S.decision_function(X, y, a, C)
    rows = [['#', 'x1', 'x2', 'y', 'alpha', 'y*f(x)', '분류']]
    idx = sorted(range(len(X)), key=lambda i: -a[i])[:10]
    for i in idx:
        if a[i] > C - 1e-6:
            cat = '마진 안쪽/오분류 (a = C)'
        elif a[i] > 1e-6:
            cat = '마진 위 (0 < a < C)'
        else:
            cat = '마진 밖 (a = 0)'
        rows.append(['%d' % i, '%+.3f' % X[i][0], '%+.3f' % X[i][1],
                     '%+.0f' % y[i], '%.4f' % a[i], '%.4f' % (y[i] * f(X[i])), cat])
    zeros = sum(1 for v in a if v <= 1e-6)
    print(fmt.table(rows, align='rrrrrrl'))
    print('  alpha 가 0 인 점이 %d/%d 개다 — 그 점들은 해에 전혀 영향을 주지 않는다.'
          % (zeros, len(X)))
    print('  상보여유 a_i * (1 - xi_i - y_i f(x_i)) = 0 이 그 사실을 말해 준다(5부).')
    print('  마진 위의 점들은 y*f(x) 가 정확히 1 이다 — 표에서 확인된다.\n')


def demo_primal_dual():
    print('■ 3. 쌍대 해에서 원문제 해를 복원한다')
    X, y = S.separable_data(n=40, seed=7, margin=1.4)
    C = 10.0
    a, _ = S.train_dual(X, y, C=C, iters=3000)
    w = S.primal_weights(X, y, a)
    f, b = S.decision_function(X, y, a, C)
    print('  정류조건에서 w = sum_i a_i y_i x_i 다 (5부 21장의 유도).')
    print('  복원된 w = (%.4f, %.4f), b = %.4f' % (w[0], w[1], b))
    print('  마진 폭 2/||w|| = %.4f' % (2.0 / la.norm(w)))
    err = max(abs(la.dot(w, X[i]) + b - f(X[i])) for i in range(len(X)))
    print('  결정함수를 두 방식으로 계산한 차이: %.2e (같은 함수다)' % err)
    print()
    rows = [['자료 수', '서포트 벡터 수', '비율', '모델을 저장하는 데 필요한 점']]
    for n in (20, 40, 80, 160):
        Xn, yn = S.separable_data(n=n, seed=9, margin=1.4)
        an, _ = S.train_dual(Xn, yn, C=C, iters=1200)
        sv = S.support_vectors(an, C)
        rows.append(['%d' % n, '%d' % sv['total'],
                     '%.1f%%' % (100.0 * sv['total'] / n), '%d' % sv['total']])
    print(fmt.table(rows, align='rrrr'))
    print('  서포트 벡터는 자료의 10% 안팎에 머문다. 예측에 필요한 것은 그 점들뿐이므로')
    print('  모델이 자료보다 훨씬 작아진다 — 쌍대가 준 두 번째 선물이다.')
    print('  (이 자료는 마진이 넓어 서포트가 특히 적다. 겹치는 자료에서는 더 많아진다.)\n')


def demo_kernel():
    print('■ 4. 커널 — 자료가 내적으로만 등장하기 때문에 가능하다')
    X, y = [], []
    import random
    rng = random.Random(11)
    for _ in range(60):                          # 동심원 자료 (선형분리 불가)
        r = rng.choice([1.0, 2.6])
        th = rng.uniform(0, 2 * math.pi)
        X.append([r * math.cos(th) + rng.gauss(0, 0.15),
                  r * math.sin(th) + rng.gauss(0, 0.15)])
        y.append(1.0 if r < 2.0 else -1.0)
    rows = [['커널', '학습 정확도', '서포트 벡터 수', '비고']]
    a, _ = S.train_dual(X, y, C=10.0, iters=1500)
    f, _ = S.decision_function(X, y, a, 10.0)
    acc = sum(1 for i in range(len(X)) if y[i] * f(X[i]) > 0) / float(len(X))
    rows.append(['선형', '%.1f%%' % (100 * acc), '%d' % S.support_vectors(a, 10.0)['total'],
                 '직선으로는 동심원을 못 가른다'])
    for g in (0.5, 2.0):
        k = S.rbf_kernel(g)
        a2, _ = S.train_dual(X, y, C=10.0, kernel=k, iters=1500)
        f2, _ = S.decision_function(X, y, a2, 10.0, kernel=k)
        acc2 = sum(1 for i in range(len(X)) if y[i] * f2(X[i]) > 0) / float(len(X))
        rows.append(['RBF (gamma=%.1f)' % g, '%.1f%%' % (100 * acc2),
                     '%d' % S.support_vectors(a2, 10.0)['total'],
                     '내적을 K(x, z) 로 바꿔 끼운 것뿐'])
    print(fmt.table(rows, align='lrrl'))
    print('  쌍대 목적함수에는 x_i 가 x_i^T x_j 로만 나타난다. 그 자리에 아무 커널이나')
    print('  넣으면 고차원 특징공간에서의 선형 분류가 된다 — 특징을 명시적으로')
    print('  만들지 않고도. 이것이 쌍대성이 알고리즘을 바꾼 가장 유명한 사례다.')


def main():
    demo_dual()
    demo_support_vectors()
    demo_primal_dual()
    demo_kernel()


if __name__ == '__main__':
    main()
