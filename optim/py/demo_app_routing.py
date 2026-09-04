# -*- coding: utf-8 -*-
"""13부 데모 — TSP: 정확해·휴리스틱·하한을 나란히 놓는다."""
import math
import time

from py import fmt
from py.apps import routing as R


def demo_compare():
    print('■ 1. 같은 문제, 세 가지 답  (무작위 도시, 유클리드 거리)')
    rows = [['도시 수', '정확해 (Held-Karp)', '시간(초)', '최근접 이웃', '초과율',
             '2-opt', '초과율', 'MST 하한']]
    for n in (6, 8, 10, 12):
        D = R.distance_matrix(R.random_points(n, seed=11))
        t0 = time.time()
        exact, _ = R.held_karp(D)
        te = time.time() - t0
        nn, tour = R.nearest_neighbor(D)
        imp, _ = R.two_opt(D, tour)
        lb = R.mst_lower_bound(D)
        rows.append(['%d' % n, '%.2f' % exact, '%.3f' % te, '%.2f' % nn,
                     '%.1f%%' % (100 * (nn / exact - 1)), '%.2f' % imp,
                     '%.1f%%' % (100 * (imp / exact - 1)), '%.2f' % lb])
    print(fmt.table(rows, align='rrrrrrrr'))
    print('  최근접 이웃은 최적보다 10~30% 나쁘고, 2-opt 로 다듬으면 대개 몇 % 안으로')
    print('  들어온다. MST 하한은 최적값 아래에 있으면서도 그리 멀지 않다 —')
    print('  분지한정의 가지치기에 쓸 만하다는 뜻이다(7부).\n')


def demo_scaling():
    print('■ 2. 정확해는 어디까지 가능한가')
    rows = [['도시 수 n', 'DP 상태 수 n*2^n', '측정 시간(초)', '직전 대비',
             '이 속도로 본 n=25']]
    prev = None
    last_rate = None
    for n in (10, 12, 14, 16, 18):
        D = R.distance_matrix(R.random_points(n, seed=3))
        t0 = time.time()
        R.held_karp(D)
        dt = time.time() - t0
        states = n * (1 << n)
        last_rate = dt / states
        rows.append(['%d' % n, '%d' % states, '%.3f' % dt,
                     '%.1f배' % (dt / prev) if prev else '-',
                     '%.0f분' % (last_rate * 25 * (1 << 25) / 60.0)])
        prev = dt
    print(fmt.table(rows, align='rrrrr'))
    est25 = last_rate * 25 * (1 << 25)
    est30 = last_rate * 30 * (1 << 30)
    print('  n 이 2 늘 때마다 시간이 대략 4~8배가 된다(작은 n 에서는 측정 잡음이 크다).')
    print('  마지막 줄의 속도로 외삽하면')
    print('  n=25 는 약 %.0f분, n=30 은 약 %.1f시간이다. 정확해의 벽은 아주 가깝다.'
          % (est25 / 60.0, est30 / 3600.0))
    print('  (실무의 Concorde 솔버는 절단면과 분지한정으로 수만 도시를 푼다 —')
    print('   같은 DP 를 빠르게 만든 것이 아니라 "다른 정식화"를 쓴 것이다.)\n')


def demo_2opt_local():
    print('■ 3. 2-opt 는 국소탐색이다 — 경사하강과 같은 구조')
    D = R.distance_matrix(R.random_points(30, seed=5))
    nn, tour = R.nearest_neighbor(D)
    rows = [['출발점 (시작 도시)', '최근접 이웃', '2-opt 후', '개선율']]
    best_overall = None
    for start in range(0, 30, 5):
        s, t = R.nearest_neighbor(D, start=start)
        v, _ = R.two_opt(D, t)
        best_overall = v if best_overall is None else min(best_overall, v)
        rows.append(['%d' % start, '%.2f' % s, '%.2f' % v,
                     '%.1f%%' % (100 * (1 - v / s))])
    print(fmt.table(rows, align='rrrr'))
    print('  출발점이 다르면 도착하는 국소 최적도 다르다 — 9부에서 본 다중출발과')
    print('  정확히 같은 상황이다. 여러 출발점 중 최선: %.2f' % best_overall)
    print('  연속 최적화의 "이웃"이 방향이었다면, 여기서는 두 변을 뒤집는 것이다.')
    print('  더 나은 이웃이 없으면 멈춘다는 규칙은 똑같다.')


def main():
    demo_compare()
    demo_scaling()
    demo_2opt_local()


if __name__ == '__main__':
    main()
