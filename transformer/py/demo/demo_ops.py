# -*- coding: utf-8 -*-
"""2·4부 — 소프트맥스의 넘침, 교차엔트로피의 p − y, 레이어놈, GELU."""
import math

from demo import report
from transformerlib import fmt, ops
from transformerlib import tensor as T


def naive_softmax(z):
    """최댓값을 빼지 않은 판 — 넘치면 nan 이 나온다."""
    try:
        e = [math.exp(v) for v in z]
    except OverflowError:
        return None
    s = sum(e)
    return [v / s for v in e]


def sec_overflow():
    rows = [['로짓', '그냥 exp', '최댓값을 뺀 판']]
    for z in ([1.0, 2.0, 3.0], [100.0, 101.0, 102.0],
              [1000.0, 1001.0, 1002.0]):
        a = naive_softmax(z)
        b = ops.softmax(T.tensor(z)).data
        rows.append([' '.join('%g' % v for v in z),
                     '넘침' if a is None else ' '.join('%.4f' % v
                                                     for v in a),
                     ' '.join('%.4f' % v for v in b)])
    return (fmt.table(rows, align='lll')
            + '\n\nexp(710) 부터 double 이 넘친다. 모든 로짓에서 같은'
            + ' 수를'
            + '\n빼도 소프트맥스는 같으니, 최댓값을 빼고 계산한다.')


def sec_temperature():
    z = [2.0, 1.0, 0.0, -1.0]
    rows = [['온도 τ', 'p(로짓 2)', 'p(1)', 'p(0)', 'p(−1)']]
    for tau in (0.25, 0.5, 1.0, 2.0, 4.0):
        p = ops.softmax(T.tensor([v / tau for v in z])).data
        rows.append(['%.2f' % tau] + ['%.4f' % v for v in p])
    return (fmt.table(rows, align='rrrrr')
            + '\n\n낮은 온도는 가장 큰 칸으로 쏠리고, 높은 온도는'
            + ' 고르게 편다.')


def sec_ce_gradient():
    z = T.tensor([[2.0, 0.5, -1.0, 0.0]], requires_grad=True)
    loss = ops.cross_entropy(z, [1])
    loss.backward()
    p = ops.softmax(T.tensor([[2.0, 0.5, -1.0, 0.0]])).data
    rows = [['칸', '로짓', 'p', 'y', 'p − y', '역전파한 기울기']]
    for j in range(4):
        y = 1.0 if j == 1 else 0.0
        rows.append([str(j), '%.1f' % z.data[j], '%.6f' % p[j],
                     '%.0f' % y, '%+.6f' % (p[j] - y),
                     '%+.6f' % z.grad[j]])
    return (fmt.table(rows, align='rrrrrr')
            + '\n\n손실 = −log p[1] = %.6f' % loss.data[0]
            + '\n기울기 열이 p − y 열과 같다. 행이 하나라 N = 1.')


def sec_initial_loss():
    rows = [['어휘 V', '로짓이 모두 0 일 때 손실', 'ln V']]
    for V in (13, 256, 512, 50257):
        loss = ops.cross_entropy(T.zeros((1, V)), [0]).data[0]
        rows.append([str(V), '%.6f' % loss, '%.6f' % math.log(V)])
    return (fmt.table(rows, align='rrr')
            + '\n\n학습을 시작한 직후의 손실이 ln V 근처가 아니면'
            + ' 초기화를'
            + '\n의심한다.')


def sec_layernorm():
    x = T.tensor([[1.0, 2.0, 3.0, 10.0], [-5.0, -5.0, -5.0, -5.0]])
    g = T.Tensor([1.0] * 4, (4,))
    b = T.zeros((4,))
    y = ops.layernorm(x, g, b).tolist()
    rows = [['입력', '출력', '출력 평균', '출력 분산']]
    for xin, row in zip(x.tolist(), y):
        m = sum(row) / 4
        v = sum((u - m) ** 2 for u in row) / 4
        rows.append([' '.join('%g' % u for u in xin),
                     ' '.join('%+.3f' % u for u in row),
                     '%+.1e' % m, '%.6f' % v])
    return (fmt.table(rows, align='llrr')
            + '\n\n둘째 행은 분산이 0 이다. ε = 1e-5 덕분에 0 으로'
            + ' 나누지'
            + '\n않고 0 을 낸다. 첫 행의 분산이 1 보다 조금 작은 것도 ε'
            + ' 탓.')


def sec_gelu():
    rows = [['x', 'ReLU', 'GELU(erf)', 'GELU(tanh 근사)', '차이']]
    worst = 0.0
    for k in range(-600, 601):
        x = k / 100.0
        a = ops.gelu(T.tensor([x])).data[0]
        worst = max(worst, abs(a - ops.gelu_exact(x)))
    for x in (-3.0, -1.0, -0.5, 0.0, 0.5, 1.0, 3.0):
        a = ops.gelu(T.tensor([x])).data[0]
        e = ops.gelu_exact(x)
        rows.append(['%+.1f' % x, '%.4f' % max(0.0, x), '%.6f' % e,
                     '%.6f' % a, '%.1e' % abs(a - e)])
    return (fmt.table(rows, align='rrrrr')
            + '\n\n[−6, 6] 을 0.01 간격으로 훑은 최대 차이: '
            + '%.2e' % worst)


def main():
    return report.write('ops.txt', [
        ('소프트맥스는 왜 최댓값을 빼나', sec_overflow()),
        ('온도', sec_temperature()),
        ('교차엔트로피의 기울기 = p − y', sec_ce_gradient()),
        ('처음 손실은 ln V', sec_initial_loss()),
        ('레이어놈의 출력', sec_layernorm()),
        ('GELU — 정의와 tanh 근사', sec_gelu()),
    ])


if __name__ == '__main__':
    print(main())
