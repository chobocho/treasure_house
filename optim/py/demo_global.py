# -*- coding: utf-8 -*-
"""9부 데모 — 전역 최적화: 무엇을 얻고 무엇을 포기하는가."""
import math
import random
import time

from py import fmt
from py import funcs
from py import global_opt as go
from py import linalg as la
from py import unconstrained as uc


def rastrigin(x):
    """전역 최적화의 표준 시험함수 — 격자 모양으로 국소 최소가 촘촘하다."""
    return 10.0 * len(x) + math.fsum(v * v - 10.0 * math.cos(2 * math.pi * v)
                                     for v in x)


def demo_basins():
    print('■ 1. 비볼록에서 "수렴했다"는 "옳다"가 아니다   히멜블라우: 최소점이 4개')
    p = funcs.Himmelblau()
    rng = random.Random(1)
    found = {}
    for _ in range(400):
        x0 = [rng.uniform(-5, 5), rng.uniform(-5, 5)]
        r = uc.minimize(p, x0, method='bfgs', tol=1e-9, maxiter=500)
        if not r.converged:
            found['미수렴'] = found.get('미수렴', 0) + 1
            continue
        key = min(p.ALL_MIN, key=lambda m: (m[0] - r.x[0]) ** 2 + (m[1] - r.x[1]) ** 2)
        if (key[0] - r.x[0]) ** 2 + (key[1] - r.x[1]) ** 2 > 1e-6:
            found['안장점 등'] = found.get('안장점 등', 0) + 1
        else:
            found[key] = found.get(key, 0) + 1
    rows = [['도착한 최소점', '400회 중 몇 번', '비율', 'f 값']]
    for k in sorted(found, key=lambda k: -found[k]):
        label = ('(%.4f, %.4f)' % k) if isinstance(k, tuple) else k
        fv = ('%.2e' % p.f(list(k))) if isinstance(k, tuple) else '-'
        rows.append([label, '%d' % found[k], '%.1f%%' % (100.0 * found[k] / 400), fv])
    print(fmt.table(rows, align='lrrr'))
    print('  네 최소점 모두 f=0 이라 어디에 도착해도 "최적"이지만, 목적값이 다른')
    print('  문제였다면 출발점이 답을 결정했을 것이다. 국소 방법의 근본적 한계다.\n')


def demo_methods():
    print('■ 2. 전역 기법 비교   Rastrigin 2차원 (국소 최소가 수십 개, 전역해는 원점의 0)')
    lo, hi = [-5.12, -5.12], [5.12, 5.12]
    rng = random.Random(2)
    rows = [['방법', '함수 평가 수', '최선 f', '전역해와의 거리', '시간(초)']]

    t0 = time.time()
    best = min((rastrigin([rng.uniform(-5.12, 5.12), rng.uniform(-5.12, 5.12)]),
                None) for _ in range(4000))[0]
    rows.append(['무작위 탐색', '4000', '%.6f' % best, '-', '%.3f' % (time.time() - t0)])

    t0 = time.time()
    r = go.multistart(lambda f, x0: go.nelder_mead(f, x0, maxiter=400),
                      rastrigin, lo, hi, starts=40, seed=3)
    rows.append(['다중출발 Nelder-Mead', '%d' % r.nfev, '%.6f' % r.fx,
                 '%.4f' % la.norm(r.x), '%.3f' % (time.time() - t0)])

    t0 = time.time()
    r = go.simulated_annealing(rastrigin, [4.0, -3.0], lo, hi, iters=4000, seed=5)
    rows.append(['담금질', '4000', '%.6f' % r.fx, '%.4f' % la.norm(r.x),
                 '%.3f' % (time.time() - t0)])

    t0 = time.time()
    r = go.genetic(rastrigin, lo, hi, pop=50, gens=80, seed=7)
    rows.append(['유전 알고리즘', '%d' % r.nfev, '%.6f' % r.fx, '%.4f' % la.norm(r.x),
                 '%.3f' % (time.time() - t0)])

    t0 = time.time()
    r = go.bayes_opt(rastrigin, lo, hi, iters=60, seed=9)
    rows.append(['베이지안 최적화', '%d' % r.nfev, '%.6f' % r.fx, '%.4f' % la.norm(r.x),
                 '%.3f' % (time.time() - t0)])
    print(fmt.table(rows, align='lrrrr'))
    print('  Rastrigin 에서는 다중출발 Nelder-Mead 와 유전 알고리즘이 이긴다.')
    print('  베이지안 최적화는 64번만 평가하고도 무작위 탐색 4000번과 비슷한 값에')
    print('  머물렀지만, 이 문제에서는 좋은 답을 못 찾았다 — RBF 커널의 GP 가')
    print('  진동이 심한 함수를 잘 대변하지 못하기 때문이다. 대리 모형이 문제를')
    print('  닮지 않으면 베이지안 최적화의 장점이 사라진다. 아래에서 GP 가 잘 맞는')
    print('  매끄러운 함수로 다시 비교한다.\n')

    print('  같은 예산(30회 평가)에서, GP 가 잘 맞는 매끄러운 함수라면:')
    f2 = lambda x: (x[0] - 0.32) ** 2 + (x[1] + 0.15) ** 2 + 0.3 * math.sin(4 * x[0])
    rows = [['방법', '함수 평가 수', '최선 f']]
    rng2 = random.Random(21)
    best_r = min(f2([rng2.uniform(-2, 2), rng2.uniform(-2, 2)]) for _ in range(30))
    rows.append(['무작위 탐색 30회', '30', '%.6f' % best_r])
    grid = min(f2([-2 + 4 * i / 4.0, -2 + 4 * j / 4.0])
               for i in range(5) for j in range(5))
    rows.append(['격자 탐색 5x5 = 25회', '25', '%.6f' % grid])
    rb = go.bayes_opt(f2, [-2.0, -2.0], [2.0, 2.0], iters=26, seed=13)
    rows.append(['베이지안 최적화', '%d' % rb.nfev, '%.6f' % rb.fx])
    fine = min(f2([-2 + 4 * i / 400.0, -2 + 4 * j / 400.0])
               for i in range(401) for j in range(401))
    rows.append(['(참값: 401x401 격자)', '160801', '%.6f' % fine])
    print(fmt.table(rows, align='lrr'))
    print('  여기서는 베이지안 최적화가 같은 예산의 무작위·격자 탐색을 앞선다.')
    print('  목적함수가 매끄럽고 평가가 비쌀 때가 이 방법의 자리다.\n')


def demo_annealing_temperature():
    print('■ 3. 담금질의 온도가 하는 일   Rastrigin 2차원, 제안 폭을 좁게(구간의 2%)')
    lo, hi = [-5.12, -5.12], [5.12, 5.12]
    starts = [[4.0, -3.0], [-4.5, 4.5], [2.5, 2.5], [-1.5, 3.5], [3.5, -4.0], [0.9, 0.9]]
    rows = [['초기 온도 T0', '평균 최선 f', '가장 나쁜 결과', '나쁜 이동 수락률', '판정']]
    for t0 in (1e-12, 0.5, 2.0, 10.0, 50.0):
        res, ups = [], []
        for s2, x0 in enumerate(starts):
            r = go.simulated_annealing(rastrigin, x0, lo, hi, iters=4000, t0=t0,
                                       seed=100 + s2, scale=0.02, keep_history=True)
            res.append(r.fx)
            ups.append(sum(1 for i in range(len(r.history) - 1)
                           if r.history[i + 1]['f'] > r.history[i]['f']) / 4000.0)
        mean = sum(res) / len(res)
        verdict = ('출발점 근처에 갇힘' if mean > 10 else
                   ('전역해에 근접' if mean < 2 else '중간'))
        rows.append(['%.0e' % t0 if t0 < 0.1 else '%.1f' % t0,
                     '%.3f' % mean, '%.3f' % max(res),
                     '%.1f%%' % (100.0 * sum(ups) / len(ups)), verdict])
    print(fmt.table(rows, align='rrrrl'))
    print('  T0 이 거의 0 이면 순수 탐욕이라 출발점 근처의 국소 최소에 갇힌다')
    print('  (평균 21, 최악 41 — 전역해는 0 이다). T0 을 키우면 나쁜 이동을 받아들여')
    print('  분지를 건너뛰고 평균 1.4 까지 내려간다.')
    print('  주의: 제안 분포의 폭도 함께 봐야 한다. 폭이 넓으면 온도가 0 이어도')
    print('  분지를 건너뛰므로 온도의 효과가 보이지 않는다. 담금질을 이해한다는 것은')
    print('  냉각 일정과 제안 분포를 함께 이해한다는 뜻이다.')
    print('  그리고 어느 쪽도 원리적으로 정하는 방법은 없다 — 이 방법의 정직한 성격이다.')


def main():
    demo_basins()
    demo_methods()
    demo_annealing_temperature()


if __name__ == '__main__':
    main()
