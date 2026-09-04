# -*- coding: utf-8 -*-
"""7부 데모 — 배낭: 동적계획, LP 상한, 그리고 '의사 다항'의 뜻."""
import random
import time

from py import fmt
from py import milp


def demo_small():
    print('■ 1. 고전적인 배낭 예제  (용량 50)')
    v = [60, 100, 120]
    w = [10, 20, 30]
    rows = [['물건', '가치 v', '무게 w', '단위 가치 v/w']]
    for i in range(3):
        rows.append(['%d' % (i + 1), '%d' % v[i], '%d' % w[i], '%.2f' % (v[i] / w[i])])
    print(fmt.table(rows, align='rrrr'))
    exact, pick = milp.knapsack_dp(v, w, 50)
    bound = milp.knapsack_lp_bound(v, w, 50)
    print('  탐욕(단위 가치 순)  : 물건 1, 2 를 담고 30 남음 -> 3번을 2/3 만 담을 수 있다면 %.1f' % bound)
    print('  분수 배낭(LP 완화)  : %.1f   <- 상한' % bound)
    print('  0/1 배낭(정확한 답) : %d   물건 %s' % (exact, [i + 1 for i in pick]))
    print('  간격 %.1f 는 "쪼갤 수 없다"는 제약이 물리는 비용이다.\n' % (bound - exact))


def demo_bound_quality():
    print('■ 2. LP 상한은 얼마나 좋은가  (무작위 배낭 40개 평균)')
    rows = [['물건 수 n', '용량', '평균 LP 상한', '평균 정확한 값', '평균 상대 간격']]
    for n, cap in ((10, 50), (20, 100), (40, 200), (80, 400)):
        rng = random.Random(7 + n)
        gaps, ub, ex = [], [], []
        for _ in range(40):
            v = [rng.randint(5, 60) for _ in range(n)]
            w = [rng.randint(3, 30) for _ in range(n)]
            e, _ = milp.knapsack_dp(v, w, cap)
            b = milp.knapsack_lp_bound(v, w, cap)
            ub.append(b); ex.append(e)
            gaps.append((b - e) / max(1.0, float(e)))
        rows.append(['%d' % n, '%d' % cap, '%.1f' % (sum(ub) / len(ub)),
                     '%.1f' % (sum(ex) / float(len(ex))),
                     '%.4f%%' % (100 * sum(gaps) / len(gaps))])
    print(fmt.table(rows, align='rrrrr'))
    print('  물건이 많아질수록 상대 간격이 줄어든다 — 쪼개진 물건 하나의 영향이')
    print('  전체에서 차지하는 비중이 작아지기 때문이다. 그래서 큰 배낭일수록')
    print('  분지한정의 가지치기가 잘 든다.\n')


def demo_pseudo_polynomial():
    print('■ 3. "의사 다항" 의 뜻 — 물건 수가 아니라 용량이 비용을 정한다')
    rng = random.Random(3)
    n = 30
    rows = [['용량 cap', 'DP 표 크기 n*cap', '실행 시간(초)', '시간/표크기']]
    for cap in (100, 1000, 10000, 100000):
        v = [rng.randint(5, 60) for _ in range(n)]
        w = [rng.randint(3, 30) * max(1, cap // 100) for _ in range(n)]
        t0 = time.time()
        milp.knapsack_dp(v, w, cap)
        dt = time.time() - t0
        rows.append(['%d' % cap, '%d' % (n * cap), '%.4f' % dt,
                     '%.2e' % (dt / (n * cap))])
    print(fmt.table(rows, align='rrrr'))
    print('  시간이 표 크기에 정비례한다. 입력을 적는 데 필요한 비트 수는 log(cap) 인데')
    print('  비용은 cap 에 비례하므로, 입력 길이 기준으로는 지수다.')
    print('  cap 이 2^40 이면 이 표를 만들 수 없다 — NP-난해가 사라진 것이 아니다.')


def main():
    demo_small()
    demo_bound_quality()
    demo_pseudo_polynomial()


if __name__ == '__main__':
    main()
