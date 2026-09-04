# -*- coding: utf-8 -*-
"""9부 데모 — 가우스 과정과 기대 개선량이 실제로 무엇을 계산하는가."""
import math

from py import fmt
from py import global_opt as go


def target(x):
    return (x[0] - 0.32) ** 2 + 0.3 * math.sin(9.0 * x[0])


def demo_posterior():
    print('■ 1. 가우스 과정의 사후분포 — 아는 곳과 모르는 곳')
    X = [[0.05], [0.35], [0.62], [0.95]]
    y = [target(p) for p in X]
    gp = go.GP(X, y, length=0.15, sigma=0.4, noise=1e-8)
    rows = [['x', '참값 f(x)', 'GP 평균', 'GP 표준편차', '가장 가까운 관측점까지']]
    for i in range(0, 21):
        x = i / 20.0
        m, s = gp.predict([x])
        d = min(abs(x - p[0]) for p in X)
        mark = '  <- 관측점' if d < 1e-9 else ''
        rows.append(['%.2f' % x, '%.4f' % target([x]), '%.4f' % m, '%.4f' % s,
                     '%.3f%s' % (d, mark)])
    print(fmt.table(rows, align='rrrrl'))
    print('  관측점에서는 평균이 참값과 같고 표준편차가 0 이다 — 잡음이 없다고 두었으므로.')
    print('  관측점에서 멀어질수록 표준편차가 커진다. 이 "모른다"는 정보가')
    print('  다음에 어디를 볼지 정하는 데 쓰인다.\n')


def demo_ei():
    print('■ 2. 기대 개선량(EI) — 탐색과 활용을 하나의 수로')
    X = [[0.05], [0.35], [0.62], [0.95]]
    y = [target(p) for p in X]
    gp = go.GP(X, y, length=0.15, sigma=0.4, noise=1e-8)
    best = min(y)
    rows = [['x', 'GP 평균 mu', '표준편차 s', '개선 여지 best-mu', 'EI', '해석']]
    for i in range(0, 21):
        x = i / 20.0
        m, s = gp.predict([x])
        ei = go.expected_improvement(gp, [x], best)
        if s < 1e-6:
            note = '관측점 — EI = 0'
        elif m < best:
            note = '평균이 이미 낫다 (활용)'
        elif s > 0.25:
            note = '모르는 영역 (탐색)'
        else:
            note = ''
        rows.append(['%.2f' % x, '%.4f' % m, '%.4f' % s, '%.4f' % (best - m),
                     '%.6f' % ei, note])
    print(fmt.table(rows, align='rrrrrl'))
    print('  현재 최선값은 %.4f 다. EI 는 "평균이 낮은 곳"과 "불확실한 곳" 양쪽에서' % best)
    print('  커진다. 관측점에서는 정확히 0 이므로 같은 점을 두 번 보지 않는다.\n')


def demo_progress():
    print('■ 3. 베이지안 최적화의 진행 — 매 반복 어디를 보는가')
    r = go.bayes_opt(target, [0.0], [1.0], iters=15, init=3, seed=5,
                     length=0.15, keep_history=True)
    fine = min((target([i / 2000.0]), i / 2000.0) for i in range(2001))
    rows = [['반복', '고른 x', 'f(x)', '지금까지 최선', 'EI 값']]
    for h in r.history:
        rows.append(['%d' % (h['t'] + 1), '%.4f' % h['x'][0],
                     '%.6f' % target(h['x']), '%.6f' % h['best'],
                     '%.6f' % h['ei']])
    print(fmt.table(rows, align='rrrrr'))
    print('  총 함수 평가 %d회로 최선값 %.6f 에 도달했다.' % (r.nfev, r.fx))
    print('  촘촘한 격자(2001점)로 구한 참 최솟값은 %.6f (x = %.4f) 다.'
          % (fine[0], fine[1]))
    print('  EI 가 반복이 진행될수록 작아진다 — "더 볼 가치가 있는 곳"이 줄어든다는 뜻이고,')
    print('  그 자체가 종료 판정 기준이 된다.')


def main():
    demo_posterior()
    demo_ei()
    demo_progress()


if __name__ == '__main__':
    main()
