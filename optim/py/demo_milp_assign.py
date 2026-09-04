# -*- coding: utf-8 -*-
"""7부 데모 — 할당 문제: 헝가리안 알고리즘과 LP 쌍대성."""
import itertools
import random
import time

from py import fmt
from py import lp
from py import milp


def demo_small():
    print('■ 1. 작은 할당 문제 — 사람 3명, 작업 3개 (비용 최소)')
    C = [[4, 1, 3], [2, 0, 5], [3, 2, 2]]
    rows = [['', '작업 A', '작업 B', '작업 C']]
    for i in range(3):
        rows.append(['사람 %d' % (i + 1)] + ['%d' % v for v in C[i]])
    print(fmt.table(rows, align='lrrr'))
    cost, assign = milp.hungarian(C)
    print('  헝가리안 결과: ' + ', '.join('사람 %d -> %s' % (i + 1, 'ABC'[assign[i]])
                                          for i in range(3)))
    print('  총비용 %d' % cost)
    best = min((sum(C[i][p[i]] for i in range(3)), p)
               for p in itertools.permutations(range(3)))
    print('  전수 조사(3! = 6가지) 최적: %d — 일치' % best[0])
    print('  탐욕(각 사람이 가장 싼 작업을 고름)은 충돌한다: 1->B, 2->B 로 겹친다.')
    print('  "각자 최선"이 "전체 최선"이 아니라는 것이 할당 문제의 핵심이다.\n')


def demo_scaling():
    print('■ 2. 전수 조사 vs 헝가리안 — n! 과 n^3 의 차이')
    rng = random.Random(4)
    rows = [['n', 'n! (순열 수)', '전수 조사(초)', '헝가리안(초)', '두 답이 같은가']]
    for n in (5, 6, 7, 8, 9):
        C = [[rng.randint(1, 50) for _ in range(n)] for _ in range(n)]
        t0 = time.time()
        best = min(sum(C[i][p[i]] for i in range(n))
                   for p in itertools.permutations(range(n)))
        t_brute = time.time() - t0
        t0 = time.time()
        got, _ = milp.hungarian(C)
        t_hung = time.time() - t0
        fact = 1
        for k in range(2, n + 1):
            fact *= k
        rows.append(['%d' % n, '%d' % fact, '%.4f' % t_brute, '%.5f' % t_hung,
                     '예' if got == best else '아니오'])
    print(fmt.table(rows, align='rrrrl'))
    print('  n=12 면 순열이 4.8억 개다. 헝가리안은 n^3 = 1728 번의 일로 끝낸다.\n')


def demo_lp_connection():
    print('■ 3. 할당 문제는 LP 로도 풀린다 — 그리고 답이 자동으로 0/1 이다')
    rng = random.Random(9)
    n = 5
    C = [[rng.randint(1, 30) for _ in range(n)] for _ in range(n)]
    A_eq, b_eq = [], []
    for i in range(n):
        row = [0.0] * (n * n)
        for j in range(n):
            row[i * n + j] = 1.0
        A_eq.append(row); b_eq.append(1.0)
    for j in range(n):
        row = [0.0] * (n * n)
        for i in range(n):
            row[i * n + j] = 1.0
        A_eq.append(row); b_eq.append(1.0)
    c = [float(C[i][j]) for i in range(n) for j in range(n)]
    r = lp.solve_lp(c, A_eq=A_eq, b_eq=b_eq)
    hc, ha = milp.hungarian(C)
    frac = sum(1 for v in r.x if 1e-7 < v < 1 - 1e-7)
    print('  LP 완화 최적값 %.4f,  헝가리안 %d  -> 같다: %s'
          % (r.obj, hc, '예' if abs(r.obj - hc) < 1e-6 else '아니오'))
    print('  LP 해에서 0 도 1 도 아닌 성분의 수: %d 개' % frac)
    print('  정수 제약을 아예 걸지 않았는데도 정수해가 나왔다. 우연이 아니라')
    print('  할당 문제의 제약행렬이 완전단모듈(totally unimodular)이기 때문이다.')
    print('  이것이 "어떤 정수 문제는 사실 쉽다"의 정확한 이유다 — 다음 데모에서 확인한다.\n')

    print('  헝가리안이 유지하는 잠재값 u, v 를 꺼내 쌍대 실행가능성을 확인한다:')
    _, asg, du, dv = milp.hungarian(C, return_dual=True)
    worst = max(du[i] + dv[j] - C[i][j] for i in range(n) for j in range(n))
    tight = [(i, asg[i], abs(du[i] + dv[asg[i]] - C[i][asg[i]])) for i in range(n)]
    trows = [['i', '배정된 j', 'c[i][j]', 'u[i] + v[j]', '차이']]
    for i, j2, gap in tight:
        trows.append(['%d' % i, '%d' % j2, '%d' % C[i][j2],
                      '%.4f' % (du[i] + dv[j2]), '%.2e' % gap])
    print(fmt.table(trows, align='rrrrr'))
    print('  모든 (i, j) 에서 u_i + v_j - c_ij 의 최댓값 = %.2e  (0 이하여야 한다)' % worst)
    print('  즉 u, v 는 쌍대 실행가능하고, 매칭된 간선에서만 등호가 성립한다.')
    print('  sum(u) + sum(v) = %.4f = 원문제 최적값 %d — 강쌍대성이다.'
          % (sum(du) + sum(dv), hc))
    print('  헝가리안 알고리즘은 LP 쌍대성을 조합적으로 구현한 것이다.')


def main():
    demo_small()
    demo_scaling()
    demo_lp_connection()


if __name__ == '__main__':
    main()
