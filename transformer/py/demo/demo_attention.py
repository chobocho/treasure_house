# -*- coding: utf-8 -*-
"""6부 — √d 로 나누는 까닭과 인과 마스크를 숫자로."""
import math

from demo import report
from transformerlib import attention as A
from transformerlib import fmt
from transformerlib import tensor as T
from transformerlib.rng import Rng


def sec_variance():
    rows = [['d', 'Var(q·k)', 'Var(q·k)/d', 'Var(q·k/√d)']]
    for d in (4, 16, 64, 256):
        raw, scaled = A.dot_variance(d, 10000, Rng(d))
        rows.append([str(d), '%.2f' % raw, '%.3f' % (raw / d),
                     '%.3f' % scaled])
    return (fmt.table(rows, align='rrrr')
            + '\n\n성분이 독립·평균 0·분산 1 인 q, k 를 1만 쌍씩'
            + ' 뽑았다.'
            + '\n나누지 않으면 분산이 d 를 따라 자라고, √d 로 나누면 1'
            + ' 근처다.')


def sec_saturation():
    rows = [['d', '키 8개 중 최대 가중치 평균 (나눔 없음)',
             '(√d 로 나눔)']]
    for d in (4, 16, 64, 256):
        raw = A.max_weight_mean(d, 8, 100, Rng(d + 1), scale=False)
        ok = A.max_weight_mean(d, 8, 100, Rng(d + 1), scale=True)
        rows.append([str(d), '%.3f' % raw, '%.3f' % ok])
    return (fmt.table(rows, align='rrr')
            + '\n\n1 에 가까우면 소프트맥스가 argmax 가 된 것이다. 그'
            + ' 자리의'
            + '\n기울기는 거의 0 이라 학습이 멈춘다.')


def sec_mask():
    q = T.tensor([[[1.0, 0.0], [0.0, 1.0], [1.0, 1.0], [0.5, -0.5]]])
    k = T.tensor([[[1.0, 0.0], [0.0, 1.0], [1.0, 1.0], [0.5, -0.5]]])
    _, w = A.scaled_dot_product(q, k, k, causal=True)
    rows = [['질의 \\ 키', '0', '1', '2', '3']]
    for i, row in enumerate(w.tolist()[0]):
        rows.append([str(i)] + ['%.3f' % v for v in row])
    return (fmt.table(rows, align='rrrrr')
            + '\n\n위 삼각형은 정확히 0 이다. 행마다 합은 1.')


def sec_cost():
    rows = [['n', 'd', '점수 n²·d', '사영 n·d²', '점수 / 사영']]
    for n, d in ((64, 768), (512, 768), (1024, 768), (4096, 768),
                 (1024, 4096)):
        s, p = n * n * d, n * d * d
        rows.append([str(n), str(d), '{:,}'.format(s), '{:,}'.format(p),
                     '%.2f' % (float(s) / p)])
    return (fmt.table(rows, align='rrrrr')
            + '\n\n곱셈 수의 비는 n/d 다. 문맥이 폭보다 길어지면 어텐션'
            + ' 점수가'
            + '\n사영보다 비싸진다.')


def main():
    return report.write('attention.txt', [
        ('q·k 의 분산은 d', sec_variance()),
        ('나누지 않으면 소프트맥스가 쏠린다', sec_saturation()),
        ('인과 마스크를 지난 가중치', sec_mask()),
        ('비용 — 점수 대 사영', sec_cost()),
    ])


if __name__ == '__main__':
    print(main())
