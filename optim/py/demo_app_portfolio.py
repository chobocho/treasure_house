# -*- coding: utf-8 -*-
"""13부 데모 — 포트폴리오: 등식 제약 QP 와 부등식이 붙었을 때의 차이."""
import math
import random

from py import fmt
from py import linalg as la
from py.apps import portfolio as P


def data(seed=3, n=600, d=5):
    rng = random.Random(seed)
    name = ['성장주', '가치주', '채권', '리츠', '원자재'][:d]
    base = [0.12, 0.08, 0.03, 0.07, 0.05][:d]
    vol = [0.30, 0.16, 0.04, 0.18, 0.25][:d]
    rets = []
    for _ in range(n):
        market = rng.gauss(0, 1.0)
        rets.append([base[j] + vol[j] * (0.55 * market + rng.gauss(0, 0.85))
                     for j in range(d)])
    mu, S = P.stats(rets)
    return name, mu, S


def demo_inputs():
    print('■ 1. 입력 — 로그가 아니라 수익률 표본에서 추정한다')
    name, mu, S = data()
    rows = [['자산', '기대수익 mu', '변동성 sqrt(sigma_ii)'] + name]
    for i, nm in enumerate(name):
        rows.append([nm, '%.4f' % mu[i], '%.4f' % math.sqrt(S[i][i])] +
                    ['%.4f' % (S[i][j] / math.sqrt(S[i][i] * S[j][j]))
                     for j in range(len(name))])
    print(fmt.table(rows, align='l' + 'r' * (2 + len(name))))
    print('  오른쪽 블록은 상관계수다. 모두 양(+)인 것은 공통 시장 요인 때문이며,')
    print('  그래서 분산투자로 위험을 0 으로 만들 수는 없다.\n')


def demo_frontier():
    print('■ 2. 효율적 경계 — 목표 수익률마다 최소 위험을 구한다 (공매도 허용)')
    name, mu, S = data()
    fr = P.frontier(S, mu, n=9)
    rows = [['목표수익', '위험(표준편차)', '합계'] + name]
    for f in fr:
        rows.append(['%.4f' % f['target'], '%.4f' % f['risk'], '%.3f' % f['sum']] +
                    ['%+.3f' % w for w in f['weights']])
    print(fmt.table(rows, align='rr' + 'r' * (1 + len(name))))
    k = min(range(len(fr)), key=lambda i: fr[i]['risk'])
    print('  최소 위험 지점은 목표수익 %.4f, 위험 %.4f 다.'
          % (fr[k]['target'], fr[k]['risk']))
    print('  왼쪽으로 가도 위험이 늘어나는 것에 주목 — 수익을 낮추는 것도 비용이다.')
    print('  그 아래쪽 가지는 "비효율적"이라 부르며, 실제로 고를 이유가 없다.')
    print('  음수 가중치는 공매도다. 각 해는 KKT 선형계 한 번으로 나온다(5부 19장).\n')


def demo_long_only():
    print('■ 3. 공매도를 금지하면 — 부등식 하나가 문제를 바꾼다')
    name, mu, S = data()
    rows = [['목표수익', '자유(공매도 허용) 위험', '공매도 금지 위험', '증가율',
             '자유 해의 최소 가중치', '실제 달성 수익']]
    for target in (0.04, 0.05, 0.06, 0.07, 0.09, 0.11):
        xf, _ = P.min_variance(S, mu, target)
        xl = P.min_variance_long_only(S, mu, target)
        rf, rl = P.risk(S, xf), P.risk(S, xl)
        rows.append(['%.3f' % target, '%.4f' % rf, '%.4f' % rl,
                     '%.1f%%' % (100 * (rl / rf - 1)), '%+.3f' % min(xf),
                     '%.4f' % la.dot(mu, xl)])
    print(fmt.table(rows, align='rrrrrr'))
    print('  자유 해가 살짝만 공매도하는 구간(-0.03)에서는 두 답이 거의 같다 —')
    print('  제약이 겨우 물리기 때문이다. 공매도가 커지는 구간(-0.49)에서는 위험이')
    print('  20% 넘게 올라간다. 제약의 <값>이 그만큼이라는 뜻이고, 그것이 곧')
    print('  라그랑주 승수의 크기다(5부 정리 19.8).')
    print('  계산 방식도 달라진다: 등식만 있으면 선형계 한 번, 부등식이 붙으면')
    print('  투영경사법 반복이다(5부 22장).\n')


def demo_estimation_risk():
    print('■ 4. 최적화의 답은 입력만큼만 좋다')
    name, mu_true, S_true = data(seed=3, n=20000)
    rows = [['표본 크기', '추정 mu 오차', '해의 가중치 차이', '실제 위험 증가']]
    for n in (60, 120, 500, 2000):
        _, mu_hat, S_hat = data(seed=99, n=n)
        x_hat, _ = P.min_variance(S_hat, mu_hat, 0.07)
        x_true, _ = P.min_variance(S_true, mu_true, 0.07)
        err = la.norm(la.vsub(mu_hat, mu_true))
        wdiff = la.norm(la.vsub(x_hat, x_true))
        r_hat = P.risk(S_true, x_hat)          # 추정으로 만든 해를 진짜 세계에서 평가
        r_true = P.risk(S_true, x_true)
        rows.append(['%d' % n, '%.4f' % err, '%.4f' % wdiff,
                     '%.1f%%' % (100 * (r_hat / r_true - 1))])
    print(fmt.table(rows, align='rrrr'))
    print('  표본이 적으면 추정 오차가 해를 크게 흔든다. 마코위츠 모형이 실무에서')
    print('  "추정 오차 증폭기"라 불리는 이유다 — 최적화가 추정의 잡음까지 성실하게')
    print('  이용하기 때문이다. 대응은 정칙화(4부): 공분산을 대각 쪽으로 수축시키거나')
    print('  가중치에 상한을 두거나, 아예 균등 가중을 쓴다.')


def main():
    demo_inputs()
    demo_frontier()
    demo_long_only()
    demo_estimation_risk()


if __name__ == '__main__':
    main()
